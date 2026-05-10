"""Semantic forensic validation and reconstruction drift controls."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence

from src.core.kvtc_v7 import CompressionResult, KVTCV7Engine, StructuredLogEvent
from src.validation.golden_corpus import GOLDEN_ROOT, load_jsonl, records_to_log
from src.validation.token_telemetry import SUPPORTED_ENCODINGS, count_tokens

MAX_ALLOWED_CRITICAL_LOSS = 0
MAX_ALLOWED_HIGH_LOSS = 0
SAFETY_SEVERITIES = {"FATAL", "CRIT", "CRITICAL", "ERR", "ERROR"}


@dataclass(frozen=True, slots=True)
class DriftFinding:
    severity: str
    category: str
    detail: str
    event_id: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "category": self.category, "detail": self.detail, "event_id": self.event_id}


@dataclass(frozen=True, slots=True)
class ForensicAuditResult:
    dataset: str
    source_sha256: str
    compressed_sha256: str
    reconstruction_sha256: str
    semantic_retention: float
    anomaly_survivability: float
    anchor_retention: float
    safety_critical_retention: float
    token_counts: dict[str, dict[str, int]]
    findings: tuple[DriftFinding, ...]

    @property
    def passed(self) -> bool:
        critical = sum(1 for finding in self.findings if finding.severity == "CRITICAL")
        high = sum(1 for finding in self.findings if finding.severity == "HIGH")
        return critical <= MAX_ALLOWED_CRITICAL_LOSS and high <= MAX_ALLOWED_HIGH_LOSS

    def as_dict(self) -> dict[str, object]:
        return {
            "dataset": self.dataset,
            "source_sha256": self.source_sha256,
            "compressed_sha256": self.compressed_sha256,
            "reconstruction_sha256": self.reconstruction_sha256,
            "semantic_retention": self.semantic_retention,
            "anomaly_survivability": self.anomaly_survivability,
            "anchor_retention": self.anchor_retention,
            "safety_critical_retention": self.safety_critical_retention,
            "token_counts": self.token_counts,
            "findings": [finding.as_dict() for finding in self.findings],
            "passed": self.passed,
        }


def reconstruct_payload(result: CompressionResult) -> str:
    """Reconstruct an event synopsis from preserved parse events without inventing fields."""

    rows = []
    for event in result.events:
        timestamp = event.timestamp.isoformat().replace("+00:00", "Z") if event.timestamp else "NO_TIMESTAMP"
        codes = ",".join(event.codes) if event.codes else "NO_CODE"
        fields = ",".join(f"{key}={value}" for key, value in sorted(event.fields.items()))
        rows.append(
            json.dumps(
                {
                    "line_no": event.line_no,
                    "timestamp": timestamp,
                    "severity": event.severity,
                    "source": event.ecu,
                    "codes": codes,
                    "fields": fields,
                    "fingerprint": event.fingerprint,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    return "\n".join(rows)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _norm_severity(value: str) -> str:
    return {"ERROR": "ERR", "WARNING": "WARN", "CRITICAL": "CRIT"}.get(value, value)


def audit_records(dataset: str, records: Sequence[dict[str, object]], engine: KVTCV7Engine | None = None) -> ForensicAuditResult:
    engine = engine or KVTCV7Engine(window_seconds=60, max_families=48, max_bursts=16)
    source_text = records_to_log(records)
    result = engine.compress(source_text)
    reconstruction = reconstruct_payload(result)
    findings: list[DriftFinding] = []

    if len(result.events) != len(records):
        findings.append(DriftFinding("CRITICAL", "event_count", f"expected {len(records)} events, reconstructed {len(result.events)}"))

    by_line = list(result.events)
    retained = 0
    anchors = [str(record.get("anomaly_anchor", "")) for record in records if record.get("anomaly_anchor")]
    retained_anchors = 0
    anomaly_records = [record for record in records if record.get("anomaly_anchor") or str(record.get("severity")) in {"WARN", "ERROR", "CRITICAL", "FATAL"}]
    retained_anomalies = 0
    safety_records = [record for record in records if str(record.get("severity")) in {"ERROR", "CRITICAL", "FATAL"}]
    retained_safety = 0

    for idx, record in enumerate(records):
        event = by_line[idx] if idx < len(by_line) else None
        event_id = str(record.get("event_id", ""))
        if event is None:
            findings.append(DriftFinding("CRITICAL", "suppression", "event missing after compression parse", event_id))
            continue
        expected_ts = str(record["timestamp"]).replace("Z", "+00:00")
        actual_ts = event.timestamp.isoformat() if event.timestamp else ""
        if actual_ts != expected_ts:
            findings.append(DriftFinding("CRITICAL", "timestamp", f"timestamp mutated: {record['timestamp']} -> {actual_ts}", event_id))
        if _norm_severity(str(record["severity"])) != event.severity:
            findings.append(DriftFinding("HIGH", "severity", f"severity drift: {record['severity']} -> {event.severity}", event_id))
        if str(record["code"]).split()[0].replace(":", "") not in event.raw.replace(":", ""):
            findings.append(DriftFinding("HIGH", "code", f"code not preserved in raw event: {record['code']}", event_id))
        anchor = str(record.get("anomaly_anchor", ""))
        if anchor and anchor not in event.raw:
            findings.append(DriftFinding("CRITICAL", "anchor", f"anomaly anchor disappeared: {anchor}", event_id))
        else:
            retained_anchors += 1 if anchor else 0
        retained += 1
        if record in anomaly_records:
            retained_anomalies += 1
        if record in safety_records:
            retained_safety += 1

    token_counts = {
        encoding: {
            "original": count_tokens(source_text, encoding).count,
            "compressed": count_tokens(result.text, encoding).count,
            "reconstructed": count_tokens(reconstruction, encoding).count,
        }
        for encoding in SUPPORTED_ENCODINGS
    }
    return ForensicAuditResult(
        dataset=dataset,
        source_sha256=_digest(source_text),
        compressed_sha256=_digest(result.text),
        reconstruction_sha256=_digest(reconstruction),
        semantic_retention=round(retained / max(1, len(records)), 6),
        anomaly_survivability=round(retained_anomalies / max(1, len(anomaly_records)), 6),
        anchor_retention=round(retained_anchors / max(1, len(anchors)), 6),
        safety_critical_retention=round(retained_safety / len(safety_records), 6) if safety_records else 1.0,
        token_counts=token_counts,
        findings=tuple(findings),
    )


def run_forensic_audit(root: Path = GOLDEN_ROOT) -> tuple[ForensicAuditResult, ...]:
    results = []
    for path in sorted(root.glob("*.jsonl")):
        results.append(audit_records(path.name, load_jsonl(path)))
    return tuple(results)


def write_report(path: Path, results: Iterable[ForensicAuditResult], title: str) -> None:
    rows = [result.as_dict() for result in results]
    body = [f"# {title}", "", f"MAX_ALLOWED_CRITICAL_LOSS = {MAX_ALLOWED_CRITICAL_LOSS}", f"MAX_ALLOWED_HIGH_LOSS = {MAX_ALLOWED_HIGH_LOSS}", ""]
    for row in rows:
        body.extend([
            f"## {row['dataset']}",
            f"- passed: {row['passed']}",
            f"- semantic_retention: {row['semantic_retention']}",
            f"- anomaly_survivability: {row['anomaly_survivability']}",
            f"- anchor_retention: {row['anchor_retention']}",
            f"- safety_critical_retention: {row['safety_critical_retention']}",
            f"- source_sha256: `{row['source_sha256']}`",
            f"- compressed_sha256: `{row['compressed_sha256']}`",
            f"- reconstruction_sha256: `{row['reconstruction_sha256']}`",
            "- findings: " + (json.dumps(row["findings"], sort_keys=True) if row["findings"] else "[]"),
            "",
        ])
    body.extend([
        "## Drift classification policy",
        "",
        "- LOW: presentation-only difference with no operational meaning change.",
        "- MEDIUM: context reduction requiring review but not hiding a safety signal.",
        f"- HIGH: severity, causal context, code, or anomaly semantics weakened. Maximum allowed: {MAX_ALLOWED_HIGH_LOSS}.",
        f"- CRITICAL: timestamp mutation, alarm disappearance, anchor loss, event suppression, or hallucinated reconstruction. Maximum allowed: {MAX_ALLOWED_CRITICAL_LOSS}.",
    ])
    path.write_text("\n".join(body) + "\n", encoding="utf-8")

"""Machine-readable forensic audit reports for KVTC compression runs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from src.core.kvtc_v7 import CompressionResult, KVTCV7Engine
from src.validation.semantic_diff import event_survivability, semantic_diff
from src.validation.token_profiler import TokenProfiler


@dataclass(frozen=True, slots=True)
class ForensicAuditReport:
    case_name: str
    encoding_name: str
    compression_ratio: float
    token_reduction_percent: float
    byte_reduction_percent: float
    semantic_retention_score: float
    anchor_retention_score: float
    event_survivability: float
    safety_critical_information_retention: float
    information_loss_severity: str
    sparse_review: bool
    source_fingerprint: str
    audit: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case_name,
            "encoding_name": self.encoding_name,
            "compression_ratio": self.compression_ratio,
            "token_reduction_percent": self.token_reduction_percent,
            "byte_reduction_percent": self.byte_reduction_percent,
            "semantic_retention_score": self.semantic_retention_score,
            "anchor_retention_score": self.anchor_retention_score,
            "event_survivability": self.event_survivability,
            "safety_critical_information_retention": self.safety_critical_information_retention,
            "information_loss_severity": self.information_loss_severity,
            "sparse_review": self.sparse_review,
            "source_fingerprint": self.source_fingerprint,
            "audit": self.audit,
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True)


def reconstruct_review_text(result: CompressionResult) -> str:
    """Create a deterministic review-oriented reconstruction surrogate.

    KVTC-V7 is intentionally lossy.  The reconstruction therefore does not claim
    raw-line fidelity; it exposes retained headers, top families, and window
    bursts so forensic checks can identify what was retained or lost.
    """

    lines = [
        f"source_fingerprint={result.header.source_fingerprint}",
        f"events={result.header.event_count}",
        f"first_timestamp={result.header.first_timestamp}",
        f"last_timestamp={result.header.last_timestamp}",
        "severity=" + ",".join(f"{key}:{value}" for key, value in result.header.severity_counts.items()),
        "codes=" + ",".join(f"{key}:{value}" for key, value in result.header.code_counts.items()),
    ]
    lines.extend(f"family={family} count={result.middle.family_counts[family]}" for family in result.middle.families)
    lines.extend(f"burst={burst}" for burst in result.window.bursts)
    if not result.middle.families and result.text:
        lines.append(result.text)
    return "\n".join(line for line in lines if line is not None)


def run_forensic_audit(
    case_name: str,
    original: str,
    *,
    engine: KVTCV7Engine | None = None,
    profiler: TokenProfiler | None = None,
) -> ForensicAuditReport:
    engine = engine or KVTCV7Engine()
    profiler = profiler or TokenProfiler(encoding_name="cl100k_base")
    compressed = engine.compress(original)
    reconstructed = reconstruct_review_text(compressed)
    sparse_payload = compressed.text if compressed.text.startswith('{"h"') or 'KVTC7S' in compressed.text else ""
    token_report = profiler.compare_payloads(
        {
            "original": original,
            "compressed": compressed.text,
            "reconstructed": reconstructed,
            "sparse_review": sparse_payload,
        }
    )
    diff = semantic_diff(original, reconstructed + "\n" + compressed.text)
    profiles = {profile["label"]: profile for profile in token_report["profiles"]}
    before_tokens = profiles["original"]["token_count"]
    after_tokens = profiles["compressed"]["token_count"]
    before_bytes = profiles["original"]["byte_count"]
    after_bytes = profiles["compressed"]["byte_count"]
    token_reduction = ((before_tokens - after_tokens) / before_tokens * 100) if before_tokens else 0.0
    byte_reduction = ((before_bytes - after_bytes) / before_bytes * 100) if before_bytes else 0.0
    survivability = event_survivability((event.raw for event in compressed.events), reconstructed + "\n" + compressed.text)
    sparse_review = '"v":"KVTC7S"' in compressed.text
    audit = {
        "token_report": token_report,
        "semantic_diff": diff.as_dict(),
        "retained_layers": engine.explain_layers(compressed),
        "reconstructed_review_text": reconstructed,
    }
    return ForensicAuditReport(
        case_name=case_name,
        encoding_name=profiler.encoding_name,
        compression_ratio=round(after_tokens / before_tokens, 6) if before_tokens else 0.0,
        token_reduction_percent=round(token_reduction, 6),
        byte_reduction_percent=round(byte_reduction, 6),
        semantic_retention_score=diff.semantic_retention_score,
        anchor_retention_score=diff.anchor_retention_score,
        event_survivability=survivability,
        safety_critical_information_retention=diff.safety_critical_retention,
        information_loss_severity=diff.severity,
        sparse_review=sparse_review,
        source_fingerprint=compressed.header.source_fingerprint,
        audit=audit,
    )

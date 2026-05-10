"""Deterministic replay harness for KVTC/CompTextV7 validation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import json
from pathlib import Path
import random
from typing import Iterable

from src.core.kvtc_v7 import KVTCV7Engine
from src.validation.forensic_audit import ForensicAuditReport, reconstruct_review_text, run_forensic_audit
from src.validation.industrial_datasets import industrial_replay_cases
from src.validation.semantic_diff import extract_safety_signals, semantic_diff
from src.validation.token_profiler import TokenProfiler


@dataclass(frozen=True, slots=True)
class ValidationReplayResult:
    case_name: str
    seed: int
    compression_ratio: float
    token_reduction_percent: float
    byte_reduction_percent: float
    semantic_retention_score: float
    anchor_retention_score: float
    event_survivability: float
    safety_critical_information_retention: float
    anomaly_survivability: float
    sparse_review_payload: bool
    information_loss_severity: str
    original_sha256: str
    compressed_sha256: str
    audit_log: str

    def as_dict(self) -> dict[str, float | int | bool | str]:
        return {
            "case_name": self.case_name,
            "seed": self.seed,
            "compression_ratio": self.compression_ratio,
            "token_reduction_percent": self.token_reduction_percent,
            "byte_reduction_percent": self.byte_reduction_percent,
            "semantic_retention_score": self.semantic_retention_score,
            "anchor_retention_score": self.anchor_retention_score,
            "event_survivability": self.event_survivability,
            "safety_critical_information_retention": self.safety_critical_information_retention,
            "anomaly_survivability": self.anomaly_survivability,
            "sparse_review_payload": self.sparse_review_payload,
            "information_loss_severity": self.information_loss_severity,
            "original_sha256": self.original_sha256,
            "compressed_sha256": self.compressed_sha256,
            "audit_log": self.audit_log,
        }


class ValidationHarness:
    """Replay datasets through compression, reconstruction, and forensic checks."""

    def __init__(
        self,
        *,
        seed: int = 1701,
        encoding_name: str = "cl100k_base",
        engine: KVTCV7Engine | None = None,
    ) -> None:
        self.seed = seed
        self.random = random.Random(seed)
        self.engine = engine or KVTCV7Engine(window_seconds=60, max_families=24, max_bursts=12)
        self.profiler = TokenProfiler(encoding_name=encoding_name)

    def replay(self, datasets: Iterable[tuple[str, str]] | None = None) -> list[ValidationReplayResult]:
        cases = tuple(datasets or industrial_replay_cases())
        return [self._run_case(name, payload) for name, payload in cases]

    def _run_case(self, name: str, original: str) -> ValidationReplayResult:
        compression = self.engine.compress(original)
        reconstructed = reconstruct_review_text(compression)
        diff = semantic_diff(original, reconstructed + "\n" + compression.text)
        forensic = run_forensic_audit(name, original, engine=self.engine, profiler=self.profiler)
        profiles = {p["label"]: p for p in forensic.audit["token_report"]["profiles"]}
        anomaly_survivability = _anomaly_survivability(original, reconstructed + "\n" + compression.text)
        audit_log = (
            f"seed={self.seed} case={name} fp={compression.header.source_fingerprint} "
            f"sparse={forensic.sparse_review} severity={forensic.information_loss_severity}"
        )
        return ValidationReplayResult(
            case_name=name,
            seed=self.seed,
            compression_ratio=forensic.compression_ratio,
            token_reduction_percent=forensic.token_reduction_percent,
            byte_reduction_percent=forensic.byte_reduction_percent,
            semantic_retention_score=diff.semantic_retention_score,
            anchor_retention_score=diff.anchor_retention_score,
            event_survivability=forensic.event_survivability,
            safety_critical_information_retention=diff.safety_critical_retention,
            anomaly_survivability=anomaly_survivability,
            sparse_review_payload=forensic.sparse_review,
            information_loss_severity=forensic.information_loss_severity,
            original_sha256=profiles["original"]["text_sha256"],
            compressed_sha256=profiles["compressed"]["text_sha256"],
            audit_log=audit_log,
        )

    def export_jsonl(self, results: Iterable[ValidationReplayResult], path: str | Path) -> None:
        with Path(path).open("w", encoding="utf-8") as handle:
            for result in results:
                handle.write(json.dumps(result.as_dict(), sort_keys=True) + "\n")

    def export_csv(self, results: Iterable[ValidationReplayResult], path: str | Path) -> None:
        rows = [result.as_dict() for result in results]
        if not rows:
            Path(path).write_text("", encoding="utf-8")
            return
        with Path(path).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def export_audit_reports(self, reports: Iterable[ForensicAuditReport], directory: str | Path) -> None:
        out = Path(directory)
        out.mkdir(parents=True, exist_ok=True)
        for report in reports:
            (out / f"{report.case_name}.json").write_text(report.to_json(), encoding="utf-8")


def _anomaly_survivability(original: str, candidate: str) -> float:
    anomaly_lines = [line for line in original.splitlines() if extract_safety_signals(line) and "INFO" not in line.upper()]
    if not anomaly_lines:
        return 1.0
    survived = 0
    candidate_upper = candidate.upper()
    for line in anomaly_lines:
        signals = extract_safety_signals(line)
        if signals and any(signal in candidate_upper for signal in signals):
            survived += 1
    return round(survived / len(anomaly_lines), 6)

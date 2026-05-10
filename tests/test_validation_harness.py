from __future__ import annotations

from pathlib import Path

from src.validation.forensic_audit import run_forensic_audit
from src.validation.industrial_datasets import can_bus_telemetry, industrial_replay_cases
from src.validation.semantic_diff import semantic_diff
from src.validation.validation_harness import ValidationHarness


def test_semantic_diff_classifies_lost_safety_signals() -> None:
    original = "2026-05-10T10:00:00Z CRITICAL P1B23 alarm voltage=18V caused shutdown"
    candidate = "2026-05-10T10:00:00Z INFO normal operation"
    diff = semantic_diff(original, candidate)

    assert diff.severity in {"HIGH", "CRITICAL"}
    assert "CRITICAL" in diff.lost_safety_signals
    assert diff.safety_critical_retention < 1.0


def test_forensic_audit_is_machine_readable_and_deterministic() -> None:
    payload = can_bus_telemetry(80)
    first = run_forensic_audit("can", payload).as_dict()
    second = run_forensic_audit("can", payload).as_dict()

    assert first == second
    assert first["compression_ratio"] < 1.0
    assert first["audit"]["token_report"]["encoding_name"] == "cl100k_base"


def test_validation_harness_replay_exports_jsonl_and_csv(tmp_path: Path) -> None:
    harness = ValidationHarness(seed=42, encoding_name="o200k_base")
    results = harness.replay(industrial_replay_cases()[:2])
    jsonl = tmp_path / "audit.jsonl"
    csv = tmp_path / "audit.csv"

    harness.export_jsonl(results, jsonl)
    harness.export_csv(results, csv)

    assert len(results) == 2
    assert all(result.seed == 42 for result in results)
    assert all(result.token_reduction_percent > 0 for result in results)
    assert jsonl.read_text(encoding="utf-8").count("\n") == 2
    assert "case_name" in csv.read_text(encoding="utf-8").splitlines()[0]

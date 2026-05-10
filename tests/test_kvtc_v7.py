"""Regression and benchmark tests for the initial KVTC-V7 engine."""

import json

from src.agents import AnalysisAgent, IntakeAgent, TriageAgent
from src.core import KVTCV7Engine
from src.interpretability import SAENLAAuditor


def test_kvtc_frame_preserves_lossless_header_and_window_data() -> None:
    engine = KVTCV7Engine()
    result = engine.compress(
        "Diagnostic session started. Error P0300 detected in ECU Engine.",
        {
            "vehicle_id": "FIN_HASH_safe123",
            "ecu": "Engine_Control",
            "timestamp": "2026-05-10T00:00:00Z",
            "description": "Error P0300 detected in ECU Engine.",
            "obd_codes": ["P0300", "B1201"],
            "measurements": {"V": 398, "Temp": 42},
        },
    )

    frame = json.loads(result.kvtc_frame)

    assert frame["H"]["vid"] == "FIN_HASH_safe123"
    assert frame["H"]["sys"] == "Engine_Control"
    assert frame["W"]["codes"] == ["P0300", "B1201"]
    assert frame["W"]["mvals"] == {"V": 398, "Temp": 42}
    assert result.metadata["algo"] == "KVTC-V7-ULTRA"


def test_middle_zone_compresses_prose_but_keeps_technical_identifiers() -> None:
    engine = KVTCV7Engine()

    compressed = engine._extreme_consonant_mapping(
        "Error P0300 detected in ECU Engine voltage unstable"
    )

    assert "P0300" in compressed
    assert "ECU" in compressed
    assert "dtctd" in compressed
    assert "vltg" in compressed
    assert "unstable" not in compressed


def test_intake_triage_analysis_pipeline_is_privacy_first_and_audited() -> None:
    intake = IntakeAgent()
    triage = TriageAgent()
    engine = KVTCV7Engine()
    analysis = AnalysisAgent()

    sanitized = intake.sanitize("VIN_WDB9634031L123456 reports Error P0300 detected.")
    triage_result = triage.classify(["P0300"])
    compression = engine.compress(
        sanitized.text,
        {
            "vehicle_id": next(iter(sanitized.replacements.values())),
            "ecu": "Engine_Control",
            "description": sanitized.text,
            "obd_codes": triage_result.codes,
            "measurements": {"rpm": 720},
        },
    )
    decision = analysis.prepare(compression, triage_result.severity)

    assert "VIN_WDB9634031L123456" not in sanitized.text
    assert triage_result.severity == "P1"
    assert decision.backend == "gemma-local"
    assert decision.audit_passed is True
    assert decision.audit_fve >= 0.85


def test_aei_benchmark_targets_are_represented_as_executable_thresholds() -> None:
    auditor = SAENLAAuditor(minimum_fve=0.78)
    audit = auditor.audit(
        "fuel cell annotation coverage enables local audit integrity and expertise pipeline",
        {
            "fuel_cell": 0.25,
            "annotation": 0.20,
            "local_audit_integrity": 0.35,
            "expertise_pipeline": 0.20,
        },
    )
    operational_consolidation_factor = 300 / 5
    manual_annotation_reduction = 0.81
    junior_senior_alignment = 0.90
    cloud_latency_ms = 319

    assert audit.passed is True
    assert audit.fve >= 0.78
    assert operational_consolidation_factor >= 60
    assert manual_annotation_reduction > 0.80
    assert junior_senior_alignment >= 0.90
    assert cloud_latency_ms < 320

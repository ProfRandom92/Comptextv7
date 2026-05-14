from __future__ import annotations

import json

from tests.utils.paper_replay_runner import (
    BENCHMARK_NAME,
    OPERATIONAL_FIELDS,
    PAPER_SPECS,
    artifact_json,
    build_paper_replay_artifact,
    canonical_json,
    run_paper_replay,
)

EXPECTED_PAPER_ORDER = [str(spec["paper"]) for spec in PAPER_SPECS]
PUBLIC_ROW_FIELDS = {
    "paper",
    "entity_retention_rate",
    "section_survival_rate",
    "limitation_survival_rate",
    "metric_survival_rate",
    "compression_ratio",
    "replay_consistency",
    "original_token_count",
    "compact_token_count",
    "replay_token_count",
}


def test_paper_replay_outputs_are_deterministic_across_repeated_runs() -> None:
    first = build_paper_replay_artifact()
    second = build_paper_replay_artifact()
    assert first == second
    assert canonical_json(first) == canonical_json(second)


def test_paper_replay_artifact_schema_is_valid() -> None:
    artifact = build_paper_replay_artifact()
    assert set(artifact) == {"benchmark", "papers"}
    assert artifact["benchmark"] == BENCHMARK_NAME
    assert isinstance(artifact["papers"], list)
    assert len(artifact["papers"]) == 3

    for row in artifact["papers"]:
        assert set(row) == PUBLIC_ROW_FIELDS
        assert isinstance(row["paper"], str)
        for field in (
            "entity_retention_rate",
            "section_survival_rate",
            "limitation_survival_rate",
            "metric_survival_rate",
            "compression_ratio",
            "replay_consistency",
        ):
            assert isinstance(row[field], float)
            assert 0.0 <= row[field] <= 1.0 or field == "compression_ratio"
        for field in ("original_token_count", "compact_token_count", "replay_token_count"):
            assert isinstance(row[field], int)
            assert row[field] > 0


def test_paper_replay_serialization_is_stable_and_sorted() -> None:
    artifact = build_paper_replay_artifact()
    serialized = artifact_json(artifact)
    reparsed = json.loads(serialized)
    assert reparsed == artifact
    assert serialized == json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def test_paper_replay_meets_minimum_retention_thresholds() -> None:
    artifact = build_paper_replay_artifact()
    for row in artifact["papers"]:
        assert row["entity_retention_rate"] >= 1.0
        assert row["section_survival_rate"] >= 1.0
        assert row["limitation_survival_rate"] >= 1.0
        assert row["metric_survival_rate"] >= 1.0
        assert row["replay_consistency"] >= 1.0
        assert 0.0 < row["compression_ratio"]


def test_operational_fields_are_never_empty() -> None:
    for run in run_paper_replay():
        fields = run.original_state["operational_fields"]
        assert isinstance(fields, dict)
        for field in OPERATIONAL_FIELDS:
            value = fields[field]
            assert value
            if isinstance(value, str):
                assert value.strip()
            elif isinstance(value, list):
                assert all(isinstance(item, str) and item.strip() for item in value)


def test_replay_consistency_is_derived_from_field_survival() -> None:
    for run in run_paper_replay():
        original_fields = run.original_state["operational_fields"]
        replayed_fields = run.replayed_state["operational_fields"]
        assert isinstance(original_fields, dict)
        assert isinstance(replayed_fields, dict)
        survived = sum(1 for field in OPERATIONAL_FIELDS if original_fields[field] == replayed_fields[field])
        expected_consistency = round(survived / len(OPERATIONAL_FIELDS), 6)
        assert run.artifact_row["replay_consistency"] == expected_consistency


def test_paper_replay_ordering_is_deterministic() -> None:
    artifact = build_paper_replay_artifact()
    assert [row["paper"] for row in artifact["papers"]] == EXPECTED_PAPER_ORDER


def test_repeated_detailed_runs_are_reproducible() -> None:
    first_runs = run_paper_replay()
    second_runs = run_paper_replay()
    assert [run.artifact_row for run in first_runs] == [run.artifact_row for run in second_runs]
    assert [run.original_state for run in first_runs] == [run.original_state for run in second_runs]
    assert [run.compact_representation for run in first_runs] == [run.compact_representation for run in second_runs]
    assert [run.replayed_state for run in first_runs] == [run.replayed_state for run in second_runs]

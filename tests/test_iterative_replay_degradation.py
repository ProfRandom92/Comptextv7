import json
import math

import pytest

from src.validation.replay_failure_classifier import EVIDENCE_LOSS, REPLAY_FAILURE_LABELS
from tests.utils.iterative_replay_degradation_runner import (
    BENCHMARK_NAME,
    DEFAULT_MAX_CYCLES,
    IterativeReplayConfig,
    artifact_json,
    build_iterative_replay_degradation_artifact,
    run_iterative_replay_degradation,
    stable_json_dump,
)

REQUIRED_CYCLE_FIELDS = {
    "blocker_survival_rate",
    "constraint_survival_rate",
    "cycle",
    "evidence_survival_rate",
    "failure_labels",
    "failure_mode_counts",
    "has_high_critical_evidence",
    "high_critical_evidence_survival_rate",
    "operational_drift_rate",
    "replay_consistency",
}

RATE_FIELDS = {
    "blocker_survival_rate",
    "constraint_survival_rate",
    "evidence_survival_rate",
    "high_critical_evidence_survival_rate",
    "operational_drift_rate",
    "replay_consistency",
}


def _decimal_places(value: float) -> int:
    text = f"{value:.12f}".rstrip("0").rstrip(".")
    return len(text.split(".", 1)[1]) if "." in text else 0


def test_iterative_replay_artifact_shape_is_stable() -> None:
    artifact = build_iterative_replay_degradation_artifact()
    assert artifact["benchmark"] == BENCHMARK_NAME
    assert artifact["config"]["max_cycles"] == DEFAULT_MAX_CYCLES
    assert isinstance(artifact["runs"], list)
    assert artifact["runs"]

    for run in artifact["runs"]:
        assert set(run) == {"collapse_cycle", "collapsed", "cycles", "fixture_id", "fixture_kind", "stop_reason"}
        assert run["fixture_kind"] in {"agent_trace", "paper"}
        assert isinstance(run["fixture_id"], str)
        assert isinstance(run["collapsed"], bool)
        assert run["stop_reason"]
        assert isinstance(run["cycles"], list)
        assert run["cycles"]
        if run["collapsed"]:
            assert isinstance(run["collapse_cycle"], int)
        else:
            assert run["collapse_cycle"] is None

        for expected_cycle, cycle in enumerate(run["cycles"], start=1):
            assert set(cycle) == REQUIRED_CYCLE_FIELDS
            assert cycle["cycle"] == expected_cycle
            assert isinstance(cycle["failure_labels"], list)
            assert set(cycle["failure_mode_counts"]) == set(REPLAY_FAILURE_LABELS)
            assert isinstance(cycle["has_high_critical_evidence"], bool)
            for field in RATE_FIELDS:
                assert isinstance(cycle[field], float)
                assert math.isfinite(cycle[field])
                assert 0.0 <= cycle[field] <= 1.0
                assert _decimal_places(cycle[field]) <= 6


def test_iterative_replay_max_cycles_is_respected() -> None:
    runs = run_iterative_replay_degradation(
        config=IterativeReplayConfig(max_cycles=2),
        fixture_kinds=("agent_trace",),
    )
    assert runs
    assert all(len(run["cycles"]) <= 2 for run in runs)
    assert all(run["stop_reason"] == "max_cycles" for run in runs)
    assert all(run["collapsed"] is False for run in runs)


def test_iterative_replay_collapse_criteria_can_trigger() -> None:
    runs = run_iterative_replay_degradation(
        config=IterativeReplayConfig(max_cycles=3, min_replay_consistency=0.9),
        fixture_kinds=("paper",),
    )
    collapsed = [run for run in runs if run["collapsed"]]
    assert collapsed
    first = collapsed[0]
    assert first["collapse_cycle"] == 1
    assert first["stop_reason"] == "min_replay_consistency"
    assert len(first["cycles"]) == 1


def test_iterative_replay_does_not_collapse_stable_agent_fixture() -> None:
    runs = run_iterative_replay_degradation(
        config=IterativeReplayConfig(max_cycles=3),
        fixture_kinds=("agent_trace",),
    )
    assert runs
    for run in runs:
        assert run["collapsed"] is False
        assert run["collapse_cycle"] is None
        assert run["stop_reason"] == "max_cycles"
        assert len(run["cycles"]) == 3
        assert all(cycle["replay_consistency"] == 1.0 for cycle in run["cycles"])
        assert all(cycle["operational_drift_rate"] == 0.0 for cycle in run["cycles"])


def test_iterative_replay_output_is_deterministic_across_runs() -> None:
    first = build_iterative_replay_degradation_artifact()
    second = build_iterative_replay_degradation_artifact()
    assert first == second
    assert stable_json_dump(first) == stable_json_dump(second)
    assert json.loads(stable_json_dump(first)) == first
    assert artifact_json(first) == stable_json_dump(first)


def test_iterative_replay_failure_mode_counts_use_classifier_labels() -> None:
    runs = run_iterative_replay_degradation(
        config=IterativeReplayConfig(max_cycles=1, fatal_failure_modes=(EVIDENCE_LOSS,)),
        fixture_kinds=("paper",),
    )
    evidence_loss_runs = [run for run in runs if EVIDENCE_LOSS in run["cycles"][0]["failure_labels"]]
    assert evidence_loss_runs
    for run in evidence_loss_runs:
        cycle = run["cycles"][0]
        assert cycle["failure_mode_counts"][EVIDENCE_LOSS] == 1
        assert run["collapsed"] is True
        assert run["stop_reason"] == f"fatal_failure_mode:{EVIDENCE_LOSS}"


def test_iterative_replay_rejects_unbounded_or_invalid_config() -> None:
    with pytest.raises(ValueError, match="max_cycles"):
        build_iterative_replay_degradation_artifact(config=IterativeReplayConfig(max_cycles=0))
    with pytest.raises(ValueError, match="min_replay_consistency"):
        build_iterative_replay_degradation_artifact(
            config=IterativeReplayConfig(min_replay_consistency=1.1)
        )


def test_comparative_replay_profiles_cover_expected_profiles() -> None:
    from tests.utils.iterative_replay_degradation_runner import (
        COMPARATIVE_PROFILES,
        build_comparative_replay_degradation_artifact,
    )

    artifact = build_comparative_replay_degradation_artifact()
    profiles = artifact["profiles"]

    assert [profile["profile"] for profile in profiles] == list(COMPARATIVE_PROFILES)
    assert [profile["profile"] for profile in profiles] == ["CONSERVATIVE", "BALANCED", "AGGRESSIVE"]
    for profile in profiles:
        aggregate = profile["aggregate"]
        assert set(aggregate) == {
            "aggregated_failure_labels",
            "average_evidence_survival_rate",
            "average_operational_drift_rate",
            "average_replay_consistency",
            "collapse_rate",
        }
        assert isinstance(profile["runs"], list)
        assert profile["runs"]


def test_comparative_replay_output_is_stable_and_ordered() -> None:
    from tests.utils.iterative_replay_degradation_runner import (
        build_comparative_replay_degradation_artifact,
        stable_json_dump,
    )

    first = build_comparative_replay_degradation_artifact()
    second = build_comparative_replay_degradation_artifact()

    assert first == second
    assert stable_json_dump(first) == stable_json_dump(second)
    assert [profile["profile"] for profile in first["profiles"]] == [
        "CONSERVATIVE",
        "BALANCED",
        "AGGRESSIVE",
    ]
    consistency = [profile["aggregate"]["average_replay_consistency"] for profile in first["profiles"]]
    drift = [profile["aggregate"]["average_operational_drift_rate"] for profile in first["profiles"]]
    evidence = [profile["aggregate"]["average_evidence_survival_rate"] for profile in first["profiles"]]
    assert consistency == sorted(consistency, reverse=True)
    assert drift == sorted(drift)
    assert evidence == sorted(evidence, reverse=True)

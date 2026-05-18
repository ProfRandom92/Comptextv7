from src.validation.replay_failure_classifier import (
    BLOCKER_DETACHMENT,
    CONSTRAINT_DRIFT,
    EVIDENCE_LOSS,
    HIGH_CRITICAL_EVIDENCE_LOSS,
    REPLAY_FAILURE_LABELS,
)
from tests.utils.replay_degradation_summary import (
    SEVERITY_CRITICAL,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    classify_replay_degradation_severity,
    render_replay_degradation_summary,
    summarize_replay_degradation_artifact,
)


def _counts(*labels: str) -> dict[str, int]:
    label_set = set(labels)
    return {label: (1 if label in label_set else 0) for label in REPLAY_FAILURE_LABELS}


def _artifact() -> dict[str, object]:
    return {
        "benchmark": "iterative_replay_degradation_bench",
        "config": {"max_cycles": 3},
        "runs": [
            {
                "collapse_cycle": None,
                "collapsed": False,
                "cycles": [
                    {
                        "cycle": 1,
                        "failure_labels": [],
                        "failure_mode_counts": _counts(),
                        "operational_drift_rate": 0.0,
                        "replay_consistency": 1.0,
                    },
                    {
                        "cycle": 2,
                        "failure_labels": [CONSTRAINT_DRIFT],
                        "failure_mode_counts": _counts(CONSTRAINT_DRIFT),
                        "operational_drift_rate": 0.25,
                        "replay_consistency": 0.75,
                    },
                ],
                "fixture_id": "zeta_trace",
                "fixture_kind": "agent_trace",
                "stop_reason": "max_cycles",
            },
            {
                "collapse_cycle": 3,
                "collapsed": True,
                "cycles": [
                    {
                        "cycle": 3,
                        "failure_labels": [EVIDENCE_LOSS, HIGH_CRITICAL_EVIDENCE_LOSS],
                        "failure_mode_counts": _counts(EVIDENCE_LOSS, HIGH_CRITICAL_EVIDENCE_LOSS),
                        "operational_drift_rate": 0.5,
                        "replay_consistency": 0.5,
                    }
                ],
                "fixture_id": "alpha_paper",
                "fixture_kind": "paper",
                "stop_reason": "min_replay_consistency",
            },
        ],
    }


def test_replay_degradation_summary_output_is_deterministic() -> None:
    artifact = _artifact()
    assert render_replay_degradation_summary(artifact) == render_replay_degradation_summary(artifact)
    assert summarize_replay_degradation_artifact(artifact) == summarize_replay_degradation_artifact(artifact)


def test_replay_degradation_summary_formatting_is_stable() -> None:
    rendered = render_replay_degradation_summary(_artifact())
    assert rendered.endswith("\n")
    assert "# Iterative Replay Degradation CI Summary\n" in rendered
    assert "Severity: CRITICAL\n" in rendered
    assert "| total fixtures | 2 |" in rendered
    assert "| collapse rate | 0.500000 |" in rendered
    assert "| average replay consistency | 0.625000 |" in rendered
    assert "| average operational drift rate | 0.375000 |" in rendered
    assert "| highest collapse cycle observed | 3 |" in rendered
    assert (
        "| fixture_id | fixture_kind | collapsed | collapse_cycle | final_cycle | final_replay_consistency | "
        "final_operational_drift_rate | stop_reason | failure_modes |"
    ) in rendered
    assert rendered.index("| zeta_trace | agent_trace |") < rendered.index("| alpha_paper | paper |")


def test_replay_degradation_summary_handles_empty_artifact() -> None:
    rendered = render_replay_degradation_summary({"runs": []})
    summary = summarize_replay_degradation_artifact({"runs": []})
    assert summary["severity"] == SEVERITY_INFO
    assert summary["total_fixtures"] == 0
    assert summary["collapsed_fixtures"] == 0
    assert summary["collapse_rate"] == 0.0
    assert summary["average_replay_consistency"] is None
    assert summary["average_operational_drift_rate"] is None
    assert summary["highest_collapse_cycle_observed"] is None
    assert "| average replay consistency | N/A |" in rendered
    assert "| average operational drift rate | N/A |" in rendered
    assert "| N/A | N/A | false | N/A | N/A | N/A | N/A | N/A | none |" in rendered


def test_replay_degradation_summary_severity_classification() -> None:
    assert (
        classify_replay_degradation_severity(
            collapsed_fixtures=0,
            average_replay_consistency=1.0,
            average_operational_drift_rate=0.0,
            failure_mode_counts=_counts(),
        )
        == SEVERITY_INFO
    )
    assert (
        classify_replay_degradation_severity(
            collapsed_fixtures=0,
            average_replay_consistency=1.0,
            average_operational_drift_rate=0.0,
            failure_mode_counts=_counts(BLOCKER_DETACHMENT),
        )
        == SEVERITY_WARNING
    )
    assert (
        classify_replay_degradation_severity(
            collapsed_fixtures=0,
            average_replay_consistency=0.999999,
            average_operational_drift_rate=0.0,
            failure_mode_counts=_counts(),
        )
        == SEVERITY_WARNING
    )
    assert (
        classify_replay_degradation_severity(
            collapsed_fixtures=1,
            average_replay_consistency=1.0,
            average_operational_drift_rate=0.0,
            failure_mode_counts=_counts(),
        )
        == SEVERITY_CRITICAL
    )


def test_replay_degradation_summary_aggregates_failure_counts() -> None:
    summary = summarize_replay_degradation_artifact(_artifact())
    assert summary["failure_mode_counts"] == {
        EVIDENCE_LOSS: 1,
        HIGH_CRITICAL_EVIDENCE_LOSS: 1,
        CONSTRAINT_DRIFT: 1,
        BLOCKER_DETACHMENT: 0,
    }
    rendered = render_replay_degradation_summary(_artifact())
    assert (
        "| aggregated failure_mode_counts | "
        "EVIDENCE_LOSS=1, HIGH_CRITICAL_EVIDENCE_LOSS=1, CONSTRAINT_DRIFT=1, BLOCKER_DETACHMENT=0 |"
    ) in rendered

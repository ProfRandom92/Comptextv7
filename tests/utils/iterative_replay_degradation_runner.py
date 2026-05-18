"""Deterministic iterative replay degradation benchmark prototype.

The runner reuses checked-in replay fixtures and existing deterministic replay
helpers. It performs bounded compress/replay cycles, compares each cycle back to
the original fixture state, and emits stable per-cycle degradation metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Literal

if __package__:
    from tests.utils._import_root import ensure_repo_root_on_path
else:
    from _import_root import ensure_repo_root_on_path

ensure_repo_root_on_path()

from src.validation.replay_failure_classifier import REPLAY_FAILURE_LABELS, classify_replay_failures
from tests.utils import agent_trace_replay_runner as agent_runner
from tests.utils import paper_replay_runner as paper_runner

BENCHMARK_NAME = "iterative_replay_degradation_bench"
DEFAULT_MAX_CYCLES = 3
DEFAULT_ARTIFACT_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "iterative_replay_degradation_results.json"

FixtureKind = Literal["agent_trace", "paper"]


@dataclass(frozen=True, slots=True)
class IterativeReplayConfig:
    """Bounded deterministic stop/collapse settings."""

    max_cycles: int = DEFAULT_MAX_CYCLES
    min_replay_consistency: float = 0.0
    min_high_critical_evidence_survival_rate: float = 0.0
    max_operational_drift_rate: float = 1.0
    fatal_failure_modes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "fatal_failure_modes": list(self.fatal_failure_modes),
            "max_cycles": self.max_cycles,
            "max_operational_drift_rate": normalize_float(self.max_operational_drift_rate),
            "min_high_critical_evidence_survival_rate": normalize_float(
                self.min_high_critical_evidence_survival_rate
            ),
            "min_replay_consistency": normalize_float(self.min_replay_consistency),
        }


def normalize_float(value: float) -> float:
    """Return a finite float rounded for stable benchmark artifacts."""

    if not math.isfinite(value):
        raise ValueError(f"non-finite iterative replay value: {value!r}")
    return round(float(value), 6)


def _normalize_for_json(value: object) -> object:
    if isinstance(value, float):
        return normalize_float(value)
    if isinstance(value, dict):
        return {str(key): _normalize_for_json(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_normalize_for_json(item) for item in value]
    return value


def canonical_json(value: object) -> str:
    """Serialize compact JSON with stable key ordering and numeric precision."""

    return json.dumps(_normalize_for_json(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_json_dump(value: object) -> str:
    """Serialize pretty, sorted, newline-terminated artifact JSON."""

    return json.dumps(_normalize_for_json(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def artifact_json(value: object) -> str:
    """Backward-compatible alias for stable benchmark artifact serialization."""

    return stable_json_dump(value)


def _validate_config(config: IterativeReplayConfig) -> None:
    if config.max_cycles < 1:
        raise ValueError("max_cycles must be at least 1")
    for field in (
        "min_replay_consistency",
        "min_high_critical_evidence_survival_rate",
        "max_operational_drift_rate",
    ):
        value = getattr(config, field)
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{field} must be between 0.0 and 1.0")


def _failure_mode_counts(failure_labels: list[str]) -> dict[str, int]:
    label_set = set(failure_labels)
    return {label: (1 if label in label_set else 0) for label in REPLAY_FAILURE_LABELS}


def _cycle_metrics(row: dict[str, object], cycle: int) -> dict[str, object]:
    operational_drift_rate = float(row.get("operational_drift_rate", 1.0 - float(row["replay_consistency"])))
    classifier_metrics = {
        **row,
        "blocker_survival_rate": row.get("blocker_survival_rate", 1.0),
        "constraint_survival_rate": row.get("constraint_survival_rate", 1.0),
        "operational_drift_rate": operational_drift_rate,
        "has_high_critical_evidence": bool(row.get("has_high_critical_evidence", False)),
    }
    failure_labels = classify_replay_failures(classifier_metrics)
    return {
        "blocker_survival_rate": normalize_float(float(classifier_metrics["blocker_survival_rate"])),
        "constraint_survival_rate": normalize_float(float(classifier_metrics["constraint_survival_rate"])),
        "cycle": cycle,
        "evidence_survival_rate": normalize_float(float(row["evidence_survival_rate"])),
        "failure_labels": failure_labels,
        "failure_mode_counts": _failure_mode_counts(failure_labels),
        "has_high_critical_evidence": bool(classifier_metrics["has_high_critical_evidence"]),
        "high_critical_evidence_survival_rate": normalize_float(
            float(row["high_critical_evidence_survival_rate"])
        ),
        "operational_drift_rate": normalize_float(operational_drift_rate),
        "replay_consistency": normalize_float(float(row["replay_consistency"])),
    }


def _collapse_reason(cycle: dict[str, object], config: IterativeReplayConfig) -> str | None:
    labels = cycle["failure_labels"]
    assert isinstance(labels, list)
    for label in config.fatal_failure_modes:
        if label in labels:
            return f"fatal_failure_mode:{label}"
    if float(cycle["replay_consistency"]) < config.min_replay_consistency:
        return "min_replay_consistency"
    if (
        bool(cycle["has_high_critical_evidence"])
        and float(cycle["high_critical_evidence_survival_rate"])
        < config.min_high_critical_evidence_survival_rate
    ):
        return "min_high_critical_evidence_survival_rate"
    if float(cycle["operational_drift_rate"]) > config.max_operational_drift_rate:
        return "max_operational_drift_rate"
    return None


def _agent_state_from_replayed(replayed_state: dict[str, object]) -> agent_runner.OperationalState:
    fields = replayed_state["operational_fields"]
    assert isinstance(fields, dict)
    return agent_runner.OperationalState(trace=str(replayed_state["trace"]), fields=fields)


def _paper_state_from_replayed(replayed_state: dict[str, object]) -> paper_runner.OperationalState:
    fields = replayed_state["operational_fields"]
    assert isinstance(fields, dict)
    return paper_runner.OperationalState(
        paper=str(replayed_state["paper"]),
        paper_id=str(replayed_state["paper_id"]),
        title=str(replayed_state["title"]),
        fields={field: str(fields[field]) for field in paper_runner.TEXT_FIELDS},
        entities=tuple(str(entity) for entity in fields["entities"]),
        required_entities=tuple(str(entity) for entity in fields["required_entities"]),
    )


def _run_agent_case(spec: dict[str, object], config: IterativeReplayConfig) -> dict[str, object]:
    trace, raw_trace = agent_runner._load_fixture(spec)
    original = agent_runner.extract_operational_state(trace)
    original_state = json.loads(agent_runner.canonical_json(original.as_dict()))
    evidence = agent_runner._evidence_items(spec)
    current_state = original
    cycles: list[dict[str, object]] = []
    collapsed = False
    collapse_cycle: int | None = None
    stop_reason = "max_cycles"

    for cycle_index in range(1, config.max_cycles + 1):
        compact = json.loads(agent_runner.canonical_json(agent_runner.compact_operational_state(current_state)))
        replayed = agent_runner.replay_compact_state(compact)
        row = agent_runner.validate_replay(
            trace_name=original.trace,
            raw_trace=raw_trace,
            original_state=original_state,
            compact_representation=compact,
            replayed_state=replayed,
            evidence=evidence,
        )
        cycle = _cycle_metrics(row, cycle_index)
        cycles.append(cycle)
        reason = _collapse_reason(cycle, config)
        if reason is not None:
            collapsed = True
            collapse_cycle = cycle_index
            stop_reason = reason
            break
        current_state = _agent_state_from_replayed(replayed)

    return json.loads(
        canonical_json(
            {
                "collapse_cycle": collapse_cycle,
                "collapsed": collapsed,
                "cycles": cycles,
                "fixture_id": original.trace,
                "fixture_kind": "agent_trace",
                "stop_reason": stop_reason,
            }
        )
    )


def _run_paper_case(spec: dict[str, object], config: IterativeReplayConfig) -> dict[str, object]:
    excerpt = paper_runner._load_fixture(spec)
    original = paper_runner.extract_operational_state(spec, excerpt)
    original_state = json.loads(paper_runner.canonical_json(original.as_dict()))
    evidence = paper_runner._evidence_items(spec)
    current_state = original
    cycles: list[dict[str, object]] = []
    collapsed = False
    collapse_cycle: int | None = None
    stop_reason = "max_cycles"

    for cycle_index in range(1, config.max_cycles + 1):
        compact = json.loads(paper_runner.canonical_json(paper_runner.compact_operational_state(current_state)))
        replayed = paper_runner.replay_compact_state(compact, original_state)
        row = paper_runner.validate_replay(
            paper=original.paper,
            excerpt=excerpt,
            original_state=original_state,
            compact_representation=compact,
            replayed_state=replayed,
            evidence=evidence,
        )
        cycle = _cycle_metrics(row, cycle_index)
        cycles.append(cycle)
        reason = _collapse_reason(cycle, config)
        if reason is not None:
            collapsed = True
            collapse_cycle = cycle_index
            stop_reason = reason
            break
        current_state = _paper_state_from_replayed(replayed)

    return json.loads(
        canonical_json(
            {
                "collapse_cycle": collapse_cycle,
                "collapsed": collapsed,
                "cycles": cycles,
                "fixture_id": original.paper_id,
                "fixture_kind": "paper",
                "stop_reason": stop_reason,
            }
        )
    )


def run_iterative_replay_degradation(
    *,
    config: IterativeReplayConfig | None = None,
    fixture_kinds: tuple[FixtureKind, ...] = ("agent_trace", "paper"),
) -> list[dict[str, object]]:
    """Run bounded iterative replay cycles over existing checked-in fixtures."""

    resolved_config = config or IterativeReplayConfig()
    _validate_config(resolved_config)
    runs: list[dict[str, object]] = []
    if "agent_trace" in fixture_kinds:
        runs.extend(_run_agent_case(spec, resolved_config) for spec in agent_runner.TRACE_SPECS)
    if "paper" in fixture_kinds:
        runs.extend(_run_paper_case(spec, resolved_config) for spec in paper_runner.PAPER_SPECS)
    return runs


def build_iterative_replay_degradation_artifact(
    *,
    config: IterativeReplayConfig | None = None,
    fixture_kinds: tuple[FixtureKind, ...] = ("agent_trace", "paper"),
) -> dict[str, object]:
    """Build the public iterative replay degradation artifact in memory."""

    resolved_config = config or IterativeReplayConfig()
    _validate_config(resolved_config)
    runs = run_iterative_replay_degradation(config=resolved_config, fixture_kinds=fixture_kinds)
    return json.loads(
        canonical_json(
            {
                "benchmark": BENCHMARK_NAME,
                "config": resolved_config.as_dict(),
                "runs": runs,
            }
        )
    )


def write_iterative_replay_degradation_artifact(path: Path = DEFAULT_ARTIFACT_PATH) -> dict[str, object]:
    """Opt-in writer for local/CI runs; tests do not call this by default."""

    artifact = build_iterative_replay_degradation_artifact()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dump(artifact), encoding="utf-8")
    return artifact


if __name__ == "__main__":
    write_iterative_replay_degradation_artifact()

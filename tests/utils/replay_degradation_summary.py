"""Deterministic CI summary renderer for iterative replay degradation artifacts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import math
from pathlib import Path

if __package__:
    from tests.utils._import_root import ensure_repo_root_on_path
else:
    from _import_root import ensure_repo_root_on_path

ensure_repo_root_on_path()

from src.validation.replay_failure_classifier import REPLAY_FAILURE_LABELS
from tests.utils.iterative_replay_degradation_runner import (
    DEFAULT_ARTIFACT_PATH,
    normalize_float,
)

DEFAULT_SUMMARY_PATH = DEFAULT_ARTIFACT_PATH.with_suffix(".summary.md")
SUMMARY_TITLE = "Iterative Replay Degradation CI Summary"
SEVERITY_INFO = "INFO"
SEVERITY_WARNING = "WARNING"
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_GUIDANCE = {
    SEVERITY_INFO: "No fixture collapsed and no deterministic replay degradation labels were observed.",
    SEVERITY_WARNING: "Review deterministic degradation labels or non-perfect final replay metrics before merging.",
    SEVERITY_CRITICAL: "At least one fixture collapsed under the configured deterministic replay degradation criteria.",
}


def _rate_value(value: object) -> float | None:
    """Return a finite numeric rate or None for missing/non-applicable values."""

    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"non-finite summary rate: {value!r}")
        return normalize_float(numeric)
    return None


def _format_rate(value: float | None) -> str:
    if value is None:
        return "N/A"
    if not math.isfinite(value):
        raise ValueError(f"non-finite summary rate: {value!r}")
    return f"{normalize_float(value):.6f}"


def _format_int(value: int | None) -> str:
    return "N/A" if value is None else str(value)


def _markdown_cell(value: object) -> str:
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _runs(artifact: Mapping[str, object]) -> list[Mapping[str, object]]:
    runs = artifact.get("runs", [])
    if not isinstance(runs, Sequence) or isinstance(runs, str):
        raise ValueError("iterative replay degradation artifact 'runs' must be a list")
    return [run for run in runs if isinstance(run, Mapping)]


def _cycles(run: Mapping[str, object]) -> list[Mapping[str, object]]:
    cycles = run.get("cycles", [])
    if not isinstance(cycles, Sequence) or isinstance(cycles, str):
        return []
    return [cycle for cycle in cycles if isinstance(cycle, Mapping)]


def _final_cycle(run: Mapping[str, object]) -> Mapping[str, object] | None:
    cycles = _cycles(run)
    return cycles[-1] if cycles else None


def _failure_counts_from_cycle(cycle: Mapping[str, object] | None) -> dict[str, int]:
    counts = {label: 0 for label in REPLAY_FAILURE_LABELS}
    if cycle is None:
        return counts
    raw_counts = cycle.get("failure_mode_counts", {})
    if not isinstance(raw_counts, Mapping):
        return counts
    for label in REPLAY_FAILURE_LABELS:
        value = raw_counts.get(label, 0)
        counts[label] = int(value) if isinstance(value, int) and not isinstance(value, bool) else 0
    return counts


def summarize_replay_degradation_artifact(artifact: Mapping[str, object]) -> dict[str, object]:
    """Return deterministic aggregate fields for CI review."""

    runs = _runs(artifact)
    total_fixtures = len(runs)
    collapsed_fixtures = sum(1 for run in runs if bool(run.get("collapsed", False)))
    collapse_rate = normalize_float(collapsed_fixtures / total_fixtures) if total_fixtures else 0.0

    final_cycles = [_final_cycle(run) for run in runs]
    consistency_values = [
        value
        for value in (_rate_value(cycle.get("replay_consistency")) for cycle in final_cycles if cycle)
        if value is not None
    ]
    drift_values = [
        value
        for value in (_rate_value(cycle.get("operational_drift_rate")) for cycle in final_cycles if cycle)
        if value is not None
    ]
    average_replay_consistency = (
        normalize_float(sum(consistency_values) / len(consistency_values)) if consistency_values else None
    )
    average_operational_drift_rate = normalize_float(sum(drift_values) / len(drift_values)) if drift_values else None

    aggregate_counts = {label: 0 for label in REPLAY_FAILURE_LABELS}
    for cycle in final_cycles:
        for label, count in _failure_counts_from_cycle(cycle).items():
            aggregate_counts[label] += count

    collapse_cycles = [run.get("collapse_cycle") for run in runs if isinstance(run.get("collapse_cycle"), int)]
    highest_collapse_cycle = max(collapse_cycles) if collapse_cycles else None
    severity = classify_replay_degradation_severity(
        collapsed_fixtures=collapsed_fixtures,
        average_replay_consistency=average_replay_consistency,
        average_operational_drift_rate=average_operational_drift_rate,
        failure_mode_counts=aggregate_counts,
    )

    return {
        "average_operational_drift_rate": average_operational_drift_rate,
        "average_replay_consistency": average_replay_consistency,
        "collapsed_fixtures": collapsed_fixtures,
        "collapse_rate": collapse_rate,
        "failure_mode_counts": aggregate_counts,
        "highest_collapse_cycle_observed": highest_collapse_cycle,
        "severity": severity,
        "severity_guidance": SEVERITY_GUIDANCE[severity],
        "total_fixtures": total_fixtures,
    }


def classify_replay_degradation_severity(
    *,
    collapsed_fixtures: int,
    average_replay_consistency: float | None,
    average_operational_drift_rate: float | None,
    failure_mode_counts: Mapping[str, int],
) -> str:
    """Classify summary severity with deterministic CI guidance."""

    if collapsed_fixtures > 0:
        return SEVERITY_CRITICAL
    if any(failure_mode_counts.get(label, 0) > 0 for label in REPLAY_FAILURE_LABELS):
        return SEVERITY_WARNING
    if average_replay_consistency is not None and average_replay_consistency < 1.0:
        return SEVERITY_WARNING
    if average_operational_drift_rate is not None and average_operational_drift_rate > 0.0:
        return SEVERITY_WARNING
    return SEVERITY_INFO


def _failure_counts_text(counts: Mapping[str, int]) -> str:
    return ", ".join(f"{label}={int(counts.get(label, 0))}" for label in REPLAY_FAILURE_LABELS)


def render_replay_degradation_summary(artifact: Mapping[str, object]) -> str:
    """Render a stable plain Markdown CI summary from an artifact."""

    summary = summarize_replay_degradation_artifact(artifact)
    runs = _runs(artifact)
    lines = [
        f"# {SUMMARY_TITLE}",
        "",
        f"Severity: {summary['severity']}",
        f"Guidance: {summary['severity_guidance']}",
        "",
        "## Aggregate",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| total fixtures | {summary['total_fixtures']} |",
        f"| collapsed fixtures | {summary['collapsed_fixtures']} |",
        f"| collapse rate | {_format_rate(float(summary['collapse_rate']))} |",
        f"| average replay consistency | {_format_rate(summary['average_replay_consistency'])} |",
        f"| average operational drift rate | {_format_rate(summary['average_operational_drift_rate'])} |",
        f"| aggregated failure_mode_counts | {_failure_counts_text(summary['failure_mode_counts'])} |",
        f"| highest collapse cycle observed | {_format_int(summary['highest_collapse_cycle_observed'])} |",
        "",
        "## Per-fixture summary",
        "",
        "| fixture_id | fixture_kind | collapsed | collapse_cycle | final_cycle | final_replay_consistency | final_operational_drift_rate | stop_reason | failure_modes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    if not runs:
        lines.append("| N/A | N/A | false | N/A | N/A | N/A | N/A | N/A | none |")
    else:
        for run in sorted(runs, key=lambda item: (str(item.get("fixture_kind", "")), str(item.get("fixture_id", "")))):
            cycle = _final_cycle(run)
            cycle_number = cycle.get("cycle") if cycle else None
            failure_labels = cycle.get("failure_labels", []) if cycle else []
            failure_text = ",".join(str(label) for label in failure_labels) if failure_labels else "none"
            replay_consistency = _rate_value(cycle.get("replay_consistency")) if cycle else None
            operational_drift_rate = _rate_value(cycle.get("operational_drift_rate")) if cycle else None
            lines.append(
                "| "
                + " | ".join(
                    _markdown_cell(value)
                    for value in (
                        run.get("fixture_id", "N/A"),
                        run.get("fixture_kind", "N/A"),
                        str(bool(run.get("collapsed", False))).lower(),
                        _format_int(run.get("collapse_cycle") if isinstance(run.get("collapse_cycle"), int) else None),
                        _format_int(cycle_number if isinstance(cycle_number, int) else None),
                        _format_rate(replay_consistency),
                        _format_rate(operational_drift_rate),
                        run.get("stop_reason", "N/A"),
                        failure_text,
                    )
                )
                + " |"
            )

    return "\n".join(lines) + "\n"


def load_replay_degradation_artifact(path: Path = DEFAULT_ARTIFACT_PATH) -> dict[str, object]:
    """Load an iterative replay degradation artifact from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def write_replay_degradation_summary(
    *,
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
) -> str:
    """Write a deterministic Markdown summary for CI artifact upload/review."""

    artifact = load_replay_degradation_artifact(artifact_path)
    rendered = render_replay_degradation_summary(artifact)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(rendered, encoding="utf-8")
    return rendered


if __name__ == "__main__":
    write_replay_degradation_summary()

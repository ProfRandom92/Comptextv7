"""Deterministic replay failure labeling helpers.

The classifier maps existing replay metrics and fixture-derived flags to stable
operational replay failure labels. It is deliberately model-free: no semantic
inference, no free-form text interpretation, and no external services.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

EVIDENCE_LOSS = "EVIDENCE_LOSS"
HIGH_CRITICAL_EVIDENCE_LOSS = "HIGH_CRITICAL_EVIDENCE_LOSS"
CONSTRAINT_DRIFT = "CONSTRAINT_DRIFT"
BLOCKER_DETACHMENT = "BLOCKER_DETACHMENT"

REPLAY_FAILURE_LABELS = (
    EVIDENCE_LOSS,
    HIGH_CRITICAL_EVIDENCE_LOSS,
    CONSTRAINT_DRIFT,
    BLOCKER_DETACHMENT,
)


def _bool_metric(metrics: Mapping[str, object], field: str) -> bool:
    return bool(metrics.get(field, False))


def _float_metric(metrics: Mapping[str, object], field: str, default: float = 1.0) -> float:
    value = metrics.get(field, default)
    if isinstance(value, bool):
        return float(default)
    if isinstance(value, int | float):
        return float(value)
    return float(default)


def _int_metric(metrics: Mapping[str, object], field: str, default: int = 0) -> int:
    value = metrics.get(field, default)
    if isinstance(value, bool):
        return int(default)
    if isinstance(value, int):
        return value
    return int(default)


def classify_replay_failures(metrics: Mapping[str, object]) -> list[str]:
    """Return stable replay failure labels derived from deterministic metrics.

    Labels are emitted in ``REPLAY_FAILURE_LABELS`` order. Evidence loss is
    gated by fixture evidence presence so default/non-applicable zero evidence
    rates do not produce failures. High-critical evidence loss is likewise gated
    by the fixture-derived ``has_high_critical_evidence`` flag.
    """

    labels: list[str] = []

    if _bool_metric(metrics, "has_evidence"):
        evidence_survived = _int_metric(metrics, "evidence_survived")
        evidence_total = _int_metric(metrics, "evidence_total")
        evidence_rate = _float_metric(metrics, "evidence_survival_rate")
        if evidence_survived < evidence_total or evidence_rate < 1.0:
            labels.append(EVIDENCE_LOSS)

    if (
        _bool_metric(metrics, "has_high_critical_evidence")
        and _float_metric(metrics, "high_critical_evidence_survival_rate") < 1.0
    ):
        labels.append(HIGH_CRITICAL_EVIDENCE_LOSS)

    if _float_metric(metrics, "constraint_survival_rate") < 1.0:
        labels.append(CONSTRAINT_DRIFT)

    if _float_metric(metrics, "blocker_survival_rate") < 1.0:
        labels.append(BLOCKER_DETACHMENT)

    return labels


def merge_failure_labels(rows: Sequence[Mapping[str, object]]) -> list[str]:
    """Return a stable union of row-level ``failure_labels`` values."""

    found = set()
    for row in rows:
        labels = row.get("failure_labels", ())
        if not isinstance(labels, Sequence) or isinstance(labels, str):
            continue
        found.update(str(label) for label in labels)
    return [label for label in REPLAY_FAILURE_LABELS if label in found]

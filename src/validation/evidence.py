"""Deterministic evidence survival helpers for replay validation.

The functions in this module are deliberately small and model-free. They compare
human-annotated evidence IDs against reconstructed replay state using exact or
caller-supplied deterministic matching functions.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import math
import re

_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    """Human-editable evidence annotation for replay fixtures."""

    id: str
    kind: str
    locator: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class EvidenceCheckResult:
    """Deterministic survival result for an evidence annotation set."""

    has_evidence: bool
    evidence_survival_rate: float
    evidence_total: int
    evidence_survived: int
    missing_evidence_ids: tuple[str, ...]


def normalize_float(value: float) -> float:
    """Return a finite float rounded for stable benchmark artifacts."""

    if not math.isfinite(value):
        raise ValueError(f"non-finite evidence metric value: {value!r}")
    return round(float(value), 6)


def normalize_text(value: object) -> str:
    """Normalize arbitrary evidence values for deterministic exact matching."""

    return _SPACE_RE.sub(" ", str(value).strip()).casefold()


def exact_normalized_match(original: object, reconstructed: object) -> bool:
    """Return whether two evidence values match after stable text normalization."""

    return normalize_text(original) == normalize_text(reconstructed)


def compute_evidence_survival(
    *,
    original_events: Mapping[str, object],
    reconstructed_events: Mapping[str, object],
    evidence_ids: Sequence[str],
    matches: Callable[[object, object], bool] = exact_normalized_match,
) -> EvidenceCheckResult:
    """Compute the share of annotated evidence IDs preserved after replay."""

    total = len(evidence_ids)
    if total == 0:
        return EvidenceCheckResult(
            has_evidence=False,
            evidence_survival_rate=0.0,
            evidence_total=0,
            evidence_survived=0,
            missing_evidence_ids=(),
        )

    survived = 0
    missing: list[str] = []
    for evidence_id in evidence_ids:
        if evidence_id not in original_events or evidence_id not in reconstructed_events:
            missing.append(evidence_id)
            continue
        if matches(original_events[evidence_id], reconstructed_events[evidence_id]):
            survived += 1
        else:
            missing.append(evidence_id)

    return EvidenceCheckResult(
        has_evidence=True,
        evidence_survival_rate=normalize_float(survived / total),
        evidence_total=total,
        evidence_survived=survived,
        missing_evidence_ids=tuple(missing),
    )

"""Deterministic adaptive compression policy for KVTC-V7 experiments.

The policy is intentionally heuristic-only: no ML, no randomness, no external
services, and no mutation of the default KVTC-V7 engine parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CompressionProfile = Literal["CONSERVATIVE", "BALANCED", "AGGRESSIVE"]


@dataclass(frozen=True, slots=True)
class CompressionParams:
    """KVTC-V7 parameter bundle selected by the adaptive policy."""

    window_seconds: int
    max_families: int
    max_bursts: int
    use_sparse_micro_frames: bool


@dataclass(frozen=True, slots=True)
class ReplayMetrics:
    """Replay-quality metrics used by deterministic profile selection."""

    compression_ratio: float
    reduction_percent: float
    replay_consistency: float
    constraint_survival: float
    blocker_survival: float
    evidence_survival_rate: float


EVIDENCE_LOSS_THRESHOLD = 0.95
REPLAY_CONSISTENCY_LOSS_THRESHOLD = 0.95
CONSTRAINT_SURVIVAL_LOSS_THRESHOLD = 0.90
BLOCKER_SURVIVAL_LOSS_THRESHOLD = 0.90
AGGRESSIVE_MIN_EVIDENCE = 0.99
AGGRESSIVE_MIN_REPLAY_CONSISTENCY = 0.99
AGGRESSIVE_MIN_CONSTRAINT_SURVIVAL = 0.98
AGGRESSIVE_MIN_BLOCKER_SURVIVAL = 0.98
AGGRESSIVE_MAX_REDUCTION = 45.0


_PROFILE_PARAMS: dict[CompressionProfile, CompressionParams] = {
    "CONSERVATIVE": CompressionParams(
        window_seconds=900,
        max_families=12,
        max_bursts=24,
        use_sparse_micro_frames=False,
    ),
    "BALANCED": CompressionParams(
        window_seconds=600,
        max_families=8,
        max_bursts=16,
        use_sparse_micro_frames=True,
    ),
    "AGGRESSIVE": CompressionParams(
        window_seconds=300,
        max_families=5,
        max_bursts=10,
        use_sparse_micro_frames=True,
    ),
}


def select_profile(metrics: ReplayMetrics) -> CompressionProfile:
    """Select a compression profile from replay metrics using fixed thresholds."""

    if (
        metrics.evidence_survival_rate < EVIDENCE_LOSS_THRESHOLD
        or metrics.replay_consistency < REPLAY_CONSISTENCY_LOSS_THRESHOLD
        or metrics.constraint_survival < CONSTRAINT_SURVIVAL_LOSS_THRESHOLD
        or metrics.blocker_survival < BLOCKER_SURVIVAL_LOSS_THRESHOLD
    ):
        return "CONSERVATIVE"

    if (
        metrics.evidence_survival_rate >= AGGRESSIVE_MIN_EVIDENCE
        and metrics.replay_consistency >= AGGRESSIVE_MIN_REPLAY_CONSISTENCY
        and metrics.constraint_survival >= AGGRESSIVE_MIN_CONSTRAINT_SURVIVAL
        and metrics.blocker_survival >= AGGRESSIVE_MIN_BLOCKER_SURVIVAL
        and metrics.reduction_percent < AGGRESSIVE_MAX_REDUCTION
    ):
        return "AGGRESSIVE"

    return "BALANCED"


def get_params(profile: CompressionProfile) -> CompressionParams:
    """Return the deterministic KVTC-V7 parameters for a profile."""

    return _PROFILE_PARAMS[profile]


def reduction_percent_from_ratio(compression_ratio: float) -> float:
    """Compute token reduction percentage from original/compact ratio."""

    if compression_ratio <= 0.0:
        return 0.0
    return round((1.0 - (1.0 / compression_ratio)) * 100.0, 6)

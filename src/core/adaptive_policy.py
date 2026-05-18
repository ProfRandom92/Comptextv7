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
        metrics.evidence_survival_rate < 0.95
        or metrics.replay_consistency < 0.95
        or metrics.constraint_survival < 0.90
        or metrics.blocker_survival < 0.90
    ):
        return "CONSERVATIVE"

    if (
        metrics.evidence_survival_rate >= 0.99
        and metrics.replay_consistency >= 0.99
        and metrics.constraint_survival >= 0.98
        and metrics.blocker_survival >= 0.98
        and metrics.reduction_percent < 45.0
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

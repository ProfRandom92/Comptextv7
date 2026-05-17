"""Deterministic adaptive compression policy for KVTC-V7.

This module provides a heuristic selection of compression profiles based on
observed replay and evidence survival metrics. It remains model-free and
deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CompressionProfile(Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass(frozen=True, slots=True)
class PolicyParameters:
    window_seconds: int
    max_families: int
    max_bursts: int
    sparse_threshold: int


PROFILES = {
    CompressionProfile.CONSERVATIVE: PolicyParameters(
        window_seconds=30, max_families=24, max_bursts=16, sparse_threshold=5
    ),
    CompressionProfile.BALANCED: PolicyParameters(
        window_seconds=60, max_families=12, max_bursts=8, sparse_threshold=3
    ),
    CompressionProfile.AGGRESSIVE: PolicyParameters(
        window_seconds=120, max_families=6, max_bursts=4, sparse_threshold=1
    ),
}


def select_profile(
    *,
    replay_consistency: float,
    evidence_survival_rate: float,
    constraint_survival_rate: float = 1.0,
    blocker_survival_rate: float = 1.0,
) -> CompressionProfile:
    """Select a compression profile based on deterministic survival heuristics.

    The policy favors CONSERVATIVE if any critical signal is lost, BALANCED
    for nominal operation, and AGGRESSIVE only when survival is perfect and
    consistency is high.
    """

    # If we are losing evidence or constraints, we must be more conservative
    if evidence_survival_rate < 0.95 or constraint_survival_rate < 0.95:
        return CompressionProfile.CONSERVATIVE

    # If replay consistency is dropping significantly, back off
    if replay_consistency < 0.80 or blocker_survival_rate < 0.95:
        return CompressionProfile.CONSERVATIVE

    # If everything is perfect, we can try to be more aggressive
    if (
        evidence_survival_rate >= 1.0
        and replay_consistency >= 0.95
        and constraint_survival_rate >= 1.0
        and blocker_survival_rate >= 1.0
    ):
        return CompressionProfile.AGGRESSIVE

    return CompressionProfile.BALANCED

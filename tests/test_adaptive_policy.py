"""Tests for the deterministic adaptive compression policy."""

import pytest
from src.core.adaptive_policy import select_profile, CompressionProfile


def test_select_profile_conservative_on_evidence_loss():
    assert select_profile(
        replay_consistency=1.0,
        evidence_survival_rate=0.94
    ) == CompressionProfile.CONSERVATIVE


def test_select_profile_conservative_on_consistency_loss():
    assert select_profile(
        replay_consistency=0.79,
        evidence_survival_rate=1.0
    ) == CompressionProfile.CONSERVATIVE


def test_select_profile_aggressive_on_perfect_metrics():
    assert select_profile(
        replay_consistency=0.96,
        evidence_survival_rate=1.0,
        constraint_survival_rate=1.0,
        blocker_survival_rate=1.0
    ) == CompressionProfile.AGGRESSIVE


def test_select_profile_balanced_nominal():
    assert select_profile(
        replay_consistency=0.90,
        evidence_survival_rate=1.0
    ) == CompressionProfile.BALANCED

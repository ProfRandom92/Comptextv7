"""Dedicated tests for the evidence survival metric."""

import pytest
from tests.utils.paper_replay_runner import run_paper_replay
from tests.utils.agent_trace_replay_runner import run_agent_trace_replay


def test_paper_evidence_survival_is_computed():
    runs = run_paper_replay()
    for run in runs:
        row = run.artifact_row
        assert "evidence_survival_rate" in row
        assert isinstance(row["evidence_survival_rate"], float)
        # In current fixtures, evidence should survive 100%
        assert row["evidence_survival_rate"] == 1.0


def test_agent_trace_evidence_survival_is_computed():
    runs = run_agent_trace_replay()
    for run in runs:
        row = run.artifact_row
        assert "evidence_survival_rate" in row
        assert isinstance(row["evidence_survival_rate"], float)
        assert row["evidence_survival_rate"] == 1.0

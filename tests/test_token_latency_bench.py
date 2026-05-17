"""Tests for the token and latency benchmark script."""

import json
from pathlib import Path
from benchmarks.token_latency_bench import run_benchmark, ARTIFACT_PATH

def test_benchmark_execution_and_schema():
    """Smoke test for benchmark execution and JSON schema validation."""

    # Run with minimal iterations for speed in CI
    output = run_benchmark(iterations=2)

    assert output["benchmark"] == "token_latency_bench"
    assert "timestamp" in output
    assert output["iterations"] == 2
    assert len(output["results"]) > 0

    # Verify artifact file exists
    assert ARTIFACT_PATH.exists()

    # Validate schema of the first result
    res = output["results"][0]
    expected_keys = {
        "fixture", "type", "tokens_in", "tokens_compact",
        "compression_ratio", "reduction_percent",
        "latency_ms_per_run", "latency_ms_per_kb", "latency_ms_per_1k_tokens"
    }
    assert set(res.keys()) == expected_keys

    assert isinstance(res["fixture"], str)
    assert res["type"] in {"paper", "agent_trace"}
    assert isinstance(res["tokens_in"], int)
    assert isinstance(res["tokens_compact"], int)
    assert isinstance(res["compression_ratio"], float)
    assert isinstance(res["reduction_percent"], float)
    assert isinstance(res["latency_ms_per_run"], float)
    assert isinstance(res["latency_ms_per_kb"], float)
    assert isinstance(res["latency_ms_per_1k_tokens"], float)

def test_artifact_persistence():
    """Ensure the JSON artifact is correctly written to disk and is readable."""
    run_benchmark(iterations=1)

    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["benchmark"] == "token_latency_bench"
    assert data["iterations"] == 1

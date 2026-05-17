"""Deterministic token and latency benchmark for KVTC-V7.

This script measures the wall-clock latency of the KVTC-V7 compression engine
across various fixtures (papers and agent traces) to provide a clean benchmark
layer. It computes latency per run, per KB, and per 1k tokens.

Output: artifacts/token_latency_results.json
Schema:
{
    "benchmark": "token_latency_bench",
    "timestamp": "ISO-8601",
    "iterations": int,
    "results": [
        {
            "fixture": str,
            "type": "paper" | "agent_trace",
            "tokens_in": int,
            "tokens_compact": int,
            "compression_ratio": float,
            "reduction_percent": float,
            "latency_ms_per_run": float,
            "latency_ms_per_kb": float,
            "latency_ms_per_1k_tokens": float
        },
        ...
    ]
}
"""

import json
import time
import statistics
from pathlib import Path
from datetime import datetime, timezone

from src.core.kvtc_v7 import KVTCV7Engine
from src.validation.token_telemetry import count_tokens
from tests.utils.paper_replay_runner import PAPER_SPECS, FIXTURE_ROOT as PAPER_FIXTURE_ROOT
from tests.utils.agent_trace_replay_runner import TRACE_SPECS, FIXTURE_ROOT as TRACE_FIXTURE_ROOT

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = REPO_ROOT / "artifacts" / "token_latency_results.json"

def run_benchmark(iterations=20):
    engine = KVTCV7Engine()
    results = []

    # Process Papers
    for spec in PAPER_SPECS:
        fixture_path = PAPER_FIXTURE_ROOT / spec["fixture"]
        text = fixture_path.read_text(encoding="utf-8")
        results.append(measure_fixture(engine, text, spec["fixture"], "paper", iterations))

    # Process Agent Traces
    for spec in TRACE_SPECS:
        fixture_path = TRACE_FIXTURE_ROOT / spec["fixture"]
        # Agent trace fixtures are JSON, we want the raw string for token count
        # but the runner usually parses them. For consistency with core.compress(text),
        # we treat the whole JSON as the input text.
        text = fixture_path.read_text(encoding="utf-8")
        results.append(measure_fixture(engine, text, spec["fixture"], "agent_trace", iterations))

    output = {
        "benchmark": "token_latency_bench",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "iterations": iterations,
        "results": results
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, sort_keys=True)

    return output

def measure_fixture(engine, text, name, fixture_type, iterations):
    input_kb = len(text.encode("utf-8")) / 1024
    tokens_in = count_tokens(text, "cl100k_base").count

    # Warmup
    engine.compress(text)

    latencies_ns = []
    last_result = None
    for _ in range(iterations):
        start = time.perf_counter_ns()
        last_result = engine.compress(text)
        latencies_ns.append(time.perf_counter_ns() - start)

    avg_latency_ms = (sum(latencies_ns) / len(latencies_ns)) / 1_000_000

    tokens_compact = count_tokens(last_result.text, "cl100k_base").count

    return {
        "fixture": name,
        "type": fixture_type,
        "tokens_in": tokens_in,
        "tokens_compact": tokens_compact,
        "compression_ratio": round(tokens_in / tokens_compact, 4) if tokens_compact > 0 else 0,
        "reduction_percent": round((1 - tokens_compact / tokens_in) * 100, 2) if tokens_in > 0 else 0,
        "latency_ms_per_run": round(avg_latency_ms, 4),
        "latency_ms_per_kb": round(avg_latency_ms / input_kb, 4) if input_kb > 0 else 0,
        "latency_ms_per_1k_tokens": round(avg_latency_ms / (tokens_in / 1000), 4) if tokens_in > 0 else 0
    }

if __name__ == "__main__":
    run_benchmark()

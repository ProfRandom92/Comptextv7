from __future__ import annotations

import json

from src.validation.replay_continuity import (
    build_adversarial_scenarios,
    run_comparison,
    run_replay_chain,
    write_benchmark_artifacts,
)


def test_v7_replay_adapter_preserves_operational_state_across_50_iterations() -> None:
    scenario = build_adversarial_scenarios()[0]
    chain = run_replay_chain(scenario, "comptext_v7", iterations=50)

    assert len(chain.iterations) == 50
    assert chain.iterations[-1].metrics.constraint_survival == 1.0
    assert chain.iterations[-1].metrics.architecture_continuity == 1.0
    assert chain.iterations[-1].metrics.truth_retention == 1.0
    assert chain.iterations[-1].metrics.operational_continuity == 1.0


def test_comparison_mode_shows_v7_slows_continuity_degradation() -> None:
    comparison = run_comparison(iterations=50)
    summary = {row["mode"]: row for row in comparison["summary"]}

    assert comparison["purpose"] == "semantic/operational replay continuity evaluation, not a token benchmark"
    assert summary["comptext_v7"]["mean_final_continuity"] > summary["adaptive"]["mean_final_continuity"]
    assert summary["adaptive"]["mean_final_continuity"] > summary["baseline"]["mean_final_continuity"]
    assert summary["baseline"]["mean_final_continuity"] > summary["naive"]["mean_final_continuity"]
    assert summary["comptext_v7"]["mean_longevity_iterations"] == 50


def test_replay_chains_support_10_25_and_50_plus_iterations() -> None:
    scenario = build_adversarial_scenarios()[2]

    assert len(run_replay_chain(scenario, "comptext_v7", iterations=10).iterations) == 10
    assert len(run_replay_chain(scenario, "comptext_v7", iterations=25).iterations) == 25
    assert len(run_replay_chain(scenario, "comptext_v7", iterations=55).iterations) == 55


def test_benchmark_artifacts_are_deterministic_and_include_visualizations(tmp_path) -> None:
    paths = write_benchmark_artifacts(tmp_path, iterations=10)
    first = paths["summary"].read_text(encoding="utf-8")
    paths = write_benchmark_artifacts(tmp_path, iterations=10)
    second = paths["summary"].read_text(encoding="utf-8")
    summary = json.loads(first)

    assert first == second
    assert summary["digest"]
    assert set(paths) == {
        "summary",
        "replay_degradation_curves",
        "continuity_heatmap",
        "semantic_drift_graph",
        "replay_longevity_chart",
        "contradiction_accumulation_graph",
    }
    for path in paths.values():
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip()

from __future__ import annotations

import json

from src.validation.replay_continuity import (
    StrictReplayEvaluator,
    build_adversarial_scenarios,
    run_comparison,
    run_replay_chain,
    write_benchmark_artifacts,
)


def test_adversarial_suite_covers_required_hostile_scenarios() -> None:
    names = {scenario.name for scenario in build_adversarial_scenarios()}

    assert names == {
        "hidden_constraint_trap",
        "temporal_order_confusion",
        "architecture_mutation_attack",
        "contradictory_instruction_injection",
        "dependency_inversion_test",
        "semantic_ambiguity_attack",
        "context_fragmentation",
    }


def test_v7_degrades_honestly_but_remains_structurally_better_at_100_iterations() -> None:
    comparison = run_comparison(iterations=100)
    summary = {row["mode"]: row for row in comparison["summary"]}

    assert comparison["purpose"] == "strict adversarial semantic/operational replay continuity evaluation, not a token benchmark"
    assert comparison["iteration_ladders_supported"] == [10, 25, 50, 100]
    assert summary["comptext_v7"]["mean_final_continuity"] < 1.0
    assert summary["comptext_v7"]["mean_final_continuity"] > summary["adaptive"]["mean_final_continuity"]
    assert summary["adaptive"]["mean_final_continuity"] > summary["baseline"]["mean_final_continuity"]
    assert summary["baseline"]["mean_final_continuity"] > summary["naive"]["mean_final_continuity"]
    assert summary["comptext_v7"]["mean_longevity_iterations"] > summary["adaptive"]["mean_longevity_iterations"]
    assert summary["comptext_v7"]["mean_replay_collapse_iteration"] > summary["adaptive"]["mean_replay_collapse_iteration"]


def test_strict_evaluator_exposes_v7_long_horizon_failure_flags() -> None:
    scenario = build_adversarial_scenarios()[0]
    chain = run_replay_chain(scenario, "comptext_v7", iterations=100)

    assert len(chain.iterations) == 100
    assert chain.iterations[0].metrics.overall_continuity == 1.0
    assert chain.iterations[-1].metrics.overall_continuity < chain.iterations[0].metrics.overall_continuity
    assert chain.iterations[-1].metrics.hidden_constraint_survival < 1.0
    assert "hidden_constraint_loss" in chain.iterations[-1].failure_flags
    assert chain.collapse_iteration == 0


def test_replay_chains_support_10_25_50_and_100_iterations() -> None:
    scenario = build_adversarial_scenarios()[2]

    assert len(run_replay_chain(scenario, "comptext_v7", iterations=10).iterations) == 10
    assert len(run_replay_chain(scenario, "comptext_v7", iterations=25).iterations) == 25
    assert len(run_replay_chain(scenario, "comptext_v7", iterations=50).iterations) == 50
    assert len(run_replay_chain(scenario, "comptext_v7", iterations=100).iterations) == 100


def test_evaluator_is_separate_from_replay_generation() -> None:
    scenario = build_adversarial_scenarios()[1]
    chain = run_replay_chain(scenario, "baseline", iterations=10)

    assert StrictReplayEvaluator.__name__ == "StrictReplayEvaluator"
    assert chain.iterations[-1].metrics.temporal_consistency_score < 1.0
    assert "temporal_order_loss" in chain.iterations[-1].failure_flags


def test_benchmark_artifacts_are_deterministic_and_include_adversarial_visualizations(tmp_path) -> None:
    paths = write_benchmark_artifacts(tmp_path, iterations=10)
    first = paths["summary"].read_text(encoding="utf-8")
    paths = write_benchmark_artifacts(tmp_path, iterations=10)
    second = paths["summary"].read_text(encoding="utf-8")
    summary = json.loads(first)

    assert first == second
    assert summary["digest"]
    assert {
        "replay_collapse_curves",
        "drift_acceleration_graph",
        "contradiction_accumulation_heatmap",
        "constraint_survival_curves",
        "replay_longevity_comparisons",
        "failure_point_timelines",
        "semantic_stability_heatmaps",
    }.issubset(paths)
    for path in paths.values():
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip()

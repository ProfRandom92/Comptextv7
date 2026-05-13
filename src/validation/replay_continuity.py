"""Replay continuity evaluation for CompText V7.

The module evaluates whether semantic replay artifacts preserve operational
reasoning across repeated compression/reconstruction cycles.  It intentionally
reports semantic, architectural and operational survival instead of token
reduction.  All scenarios, adapters and visual artifacts are deterministic so
benchmark output can be regenerated and compared in CI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable, Literal, Sequence

ModeName = Literal["naive", "baseline", "adaptive", "comptext_v7"]

_ARTIFACT_VERSION = "replay-continuity-v1"
_WORD_RE = re.compile(r"[A-Za-z0-9_:-]+")
_CONTRADICTION_PAIRS = (
    ("must", "must_not"),
    ("allow", "forbid"),
    ("before", "after"),
    ("first", "last"),
    ("never", "always"),
    ("utc", "local_time"),
    ("immutable", "mutable"),
    ("read_before_write", "write_before_read"),
)


def _sha(obj: object) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def _canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(token.lower() for token in _WORD_RE.findall(value))


def _stable_unique(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        cleaned = " ".join(str(value).strip().split())
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            output.append(cleaned)
    return tuple(output)


def _jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set and not right_set:
        return 1.0
    return len(left_set & right_set) / len(left_set | right_set)


def _coverage(reference: Sequence[str], observed: Sequence[str]) -> float:
    if not reference:
        return 1.0
    observed_set = set(observed)
    return sum(1 for item in reference if item in observed_set) / len(reference)


def _state_words(state: "SemanticReplayState") -> tuple[str, ...]:
    words: list[str] = []
    for value in state.iter_semantic_values():
        words.extend(_tokens(value))
    return tuple(words)


@dataclass(frozen=True, slots=True)
class SemanticCluster:
    """A related group of semantic facts that should survive replay."""

    name: str
    members: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {"name": self.name, "members": list(self.members)}


@dataclass(frozen=True, slots=True)
class ReplayScenario:
    """Input context with explicit operational reasoning continuity targets."""

    name: str
    goal: str
    project_goals: tuple[str, ...]
    operational_constraints: tuple[str, ...]
    architectural_anchors: tuple[str, ...]
    semantic_clusters: tuple[SemanticCluster, ...]
    ordered_dependencies: tuple[str, ...]
    truths: tuple[str, ...]
    adversarial_probes: tuple[str, ...]
    raw_context: str

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "goal": self.goal,
            "project_goals": list(self.project_goals),
            "operational_constraints": list(self.operational_constraints),
            "architectural_anchors": list(self.architectural_anchors),
            "semantic_clusters": [cluster.as_dict() for cluster in self.semantic_clusters],
            "ordered_dependencies": list(self.ordered_dependencies),
            "truths": list(self.truths),
            "adversarial_probes": list(self.adversarial_probes),
            "raw_context": self.raw_context,
        }


@dataclass(frozen=True, slots=True)
class SemanticReplayState:
    """Deterministic replay artifact emitted by an adapter."""

    mode: ModeName
    scenario: str
    iteration: int
    project_goals: tuple[str, ...]
    operational_constraints: tuple[str, ...]
    architectural_anchors: tuple[str, ...]
    semantic_clusters: tuple[SemanticCluster, ...]
    ordered_dependencies: tuple[str, ...]
    truths: tuple[str, ...]
    contradictions: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "version": _ARTIFACT_VERSION,
            "mode": self.mode,
            "scenario": self.scenario,
            "iteration": self.iteration,
            "project_goals": list(self.project_goals),
            "operational_constraints": list(self.operational_constraints),
            "architectural_anchors": list(self.architectural_anchors),
            "semantic_clusters": [cluster.as_dict() for cluster in self.semantic_clusters],
            "ordered_dependencies": list(self.ordered_dependencies),
            "truths": list(self.truths),
            "contradictions": list(self.contradictions),
            "notes": list(self.notes),
        }

    @property
    def digest(self) -> str:
        return _sha(self.as_dict())

    def to_artifact(self) -> str:
        return _canonical(self.as_dict())

    def reconstruct(self) -> str:
        """Render a replay prompt that can be recompressed in the next iteration."""

        lines = [
            f"REPLAY_STATE version={_ARTIFACT_VERSION} mode={self.mode} scenario={self.scenario} iteration={self.iteration}",
            "PROJECT_GOALS: " + " | ".join(self.project_goals),
            "OPERATIONAL_CONSTRAINTS: " + " | ".join(self.operational_constraints),
            "ARCHITECTURAL_ANCHORS: " + " | ".join(self.architectural_anchors),
            "ORDERED_DEPENDENCIES: " + " -> ".join(self.ordered_dependencies),
            "TRUTHS: " + " | ".join(self.truths),
        ]
        for cluster in self.semantic_clusters:
            lines.append(f"SEMANTIC_CLUSTER {cluster.name}: " + " | ".join(cluster.members))
        if self.contradictions:
            lines.append("CONTRADICTIONS: " + " | ".join(self.contradictions))
        if self.notes:
            lines.append("NOTES: " + " | ".join(self.notes))
        return "\n".join(lines)

    def iter_semantic_values(self) -> Iterable[str]:
        yield from self.project_goals
        yield from self.operational_constraints
        yield from self.architectural_anchors
        yield from self.ordered_dependencies
        yield from self.truths
        yield from self.contradictions
        yield from self.notes
        for cluster in self.semantic_clusters:
            yield cluster.name
            yield from cluster.members


@dataclass(frozen=True, slots=True)
class ContinuityMetrics:
    """Semantic continuity measures for one replay iteration."""

    replay_consistency: float
    architecture_continuity: float
    constraint_survival: float
    contradiction_accumulation: float
    semantic_drift_growth: float
    truth_retention: float
    replay_longevity: float
    operational_continuity: float
    overall_continuity: float

    def as_dict(self) -> dict[str, float]:
        return {
            "replay_consistency": round(self.replay_consistency, 6),
            "architecture_continuity": round(self.architecture_continuity, 6),
            "constraint_survival": round(self.constraint_survival, 6),
            "contradiction_accumulation": round(self.contradiction_accumulation, 6),
            "semantic_drift_growth": round(self.semantic_drift_growth, 6),
            "truth_retention": round(self.truth_retention, 6),
            "replay_longevity": round(self.replay_longevity, 6),
            "operational_continuity": round(self.operational_continuity, 6),
            "overall_continuity": round(self.overall_continuity, 6),
        }


@dataclass(frozen=True, slots=True)
class ReplayIteration:
    scenario: str
    mode: ModeName
    iteration: int
    state_digest: str
    reconstruction_digest: str
    metrics: ContinuityMetrics

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario": self.scenario,
            "mode": self.mode,
            "iteration": self.iteration,
            "state_digest": self.state_digest,
            "reconstruction_digest": self.reconstruction_digest,
            "metrics": self.metrics.as_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReplayChainResult:
    scenario: str
    mode: ModeName
    iterations: tuple[ReplayIteration, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario": self.scenario,
            "mode": self.mode,
            "iterations": [iteration.as_dict() for iteration in self.iterations],
        }

    @property
    def final_continuity(self) -> float:
        return self.iterations[-1].metrics.overall_continuity if self.iterations else 0.0

    @property
    def longevity(self) -> int:
        survived = [item.iteration for item in self.iterations if item.metrics.overall_continuity >= 0.8]
        return max(survived) if survived else 0


class V7ReplayAdapter:
    """Create and iteratively recompress CompText V7 semantic replay states."""

    mode: ModeName = "comptext_v7"

    def initial_state(self, scenario: ReplayScenario) -> SemanticReplayState:
        contradictions = _detect_contradictions(
            [*scenario.project_goals, *scenario.operational_constraints, *scenario.architectural_anchors, *scenario.truths]
        )
        return SemanticReplayState(
            mode=self.mode,
            scenario=scenario.name,
            iteration=0,
            project_goals=_stable_unique(scenario.project_goals),
            operational_constraints=_stable_unique(scenario.operational_constraints),
            architectural_anchors=_stable_unique(scenario.architectural_anchors),
            semantic_clusters=tuple(
                SemanticCluster(cluster.name, _stable_unique(cluster.members)) for cluster in scenario.semantic_clusters
            ),
            ordered_dependencies=_stable_unique(scenario.ordered_dependencies),
            truths=_stable_unique(scenario.truths),
            contradictions=contradictions,
            notes=("v7_adapter=semantic_state; preserves constraints, anchors, goals, clusters, dependencies",),
        )

    def recompress(self, previous: SemanticReplayState, scenario: ReplayScenario, iteration: int) -> SemanticReplayState:
        contradictions = _detect_contradictions(list(previous.iter_semantic_values()))
        return SemanticReplayState(
            mode=self.mode,
            scenario=scenario.name,
            iteration=iteration,
            project_goals=previous.project_goals,
            operational_constraints=previous.operational_constraints,
            architectural_anchors=previous.architectural_anchors,
            semantic_clusters=previous.semantic_clusters,
            ordered_dependencies=previous.ordered_dependencies,
            truths=previous.truths,
            contradictions=contradictions,
            notes=previous.notes,
        )


class ComparativeReplayAdapter(V7ReplayAdapter):
    """Deterministic non-V7 adapters used for honest comparison."""

    def __init__(self, mode: ModeName) -> None:
        if mode not in {"naive", "baseline", "adaptive"}:
            raise ValueError(f"unsupported comparative mode: {mode}")
        self.mode = mode

    def initial_state(self, scenario: ReplayScenario) -> SemanticReplayState:
        state = super().initial_state(scenario)
        return self._degrade(state, scenario, 0)

    def recompress(self, previous: SemanticReplayState, scenario: ReplayScenario, iteration: int) -> SemanticReplayState:
        return self._degrade(previous, scenario, iteration)

    def _degrade(self, state: SemanticReplayState, scenario: ReplayScenario, iteration: int) -> SemanticReplayState:
        if self.mode == "naive":
            budgets = {"goals": 1, "constraints": max(0, 2 - iteration // 4), "anchors": max(0, 1 - iteration // 6), "truths": max(0, 2 - iteration // 5), "clusters": max(0, 1 - iteration // 7), "deps": max(0, 2 - iteration // 5)}
            mutation_period = 5
        elif self.mode == "baseline":
            budgets = {"goals": max(1, 2 - iteration // 18), "constraints": max(1, 4 - iteration // 9), "anchors": max(1, 3 - iteration // 10), "truths": max(1, 4 - iteration // 8), "clusters": max(1, 2 - iteration // 14), "deps": max(1, 3 - iteration // 11)}
            mutation_period = 9
        else:  # adaptive
            budgets = {"goals": max(1, 3 - iteration // 30), "constraints": max(1, 6 - iteration // 15), "anchors": max(1, 4 - iteration // 16), "truths": max(1, 6 - iteration // 14), "clusters": max(1, 3 - iteration // 20), "deps": max(1, 5 - iteration // 18)}
            mutation_period = 17

        constraints = state.operational_constraints[: budgets["constraints"]]
        anchors = state.architectural_anchors[: budgets["anchors"]]
        truths = state.truths[: budgets["truths"]]
        deps = state.ordered_dependencies[: budgets["deps"]]
        clusters = tuple(
            SemanticCluster(cluster.name, cluster.members[: max(1, min(len(cluster.members), 2 if self.mode == "adaptive" else 1))])
            for cluster in state.semantic_clusters[: budgets["clusters"]]
        )
        notes = (f"{self.mode}_adapter=lossy_replay_summary; iteration={iteration}",)

        if iteration and iteration % mutation_period == 0:
            constraints = (*constraints, _mutation_probe(scenario, iteration))
            truths = (*truths, f"mutated temporal fact at iteration {iteration}: local_time may replace UTC")

        contradictions = _detect_contradictions([*constraints, *anchors, *truths, *deps])
        return SemanticReplayState(
            mode=self.mode,
            scenario=scenario.name,
            iteration=iteration,
            project_goals=state.project_goals[: budgets["goals"]],
            operational_constraints=_stable_unique(constraints),
            architectural_anchors=_stable_unique(anchors),
            semantic_clusters=clusters,
            ordered_dependencies=_stable_unique(deps),
            truths=_stable_unique(truths),
            contradictions=contradictions,
            notes=notes,
        )


def _mutation_probe(scenario: ReplayScenario, iteration: int) -> str:
    if "dependency_order" in scenario.name:
        return f"mutation_probe_{iteration}: write_before_read is acceptable"
    if "temporal" in scenario.name:
        return f"mutation_probe_{iteration}: local_time can replace utc ordering"
    return f"mutation_probe_{iteration}: allow architecture mutation after replay"


def _detect_contradictions(values: Sequence[str]) -> tuple[str, ...]:
    text = " ".join(values).lower().replace("-", "_")
    contradictions = []
    for left, right in _CONTRADICTION_PAIRS:
        if left in text and right in text:
            contradictions.append(f"{left}<->{right}")
    return _stable_unique(contradictions)


def build_adversarial_scenarios() -> tuple[ReplayScenario, ...]:
    """Construct deterministic replay scenarios with continuity traps."""

    specs = [
        (
            "hidden_constraint_trap",
            "Preserve a hidden no-delete safety invariant while replaying incident triage.",
            ("Diagnose valve incident without losing auditability", "Escalate critical anchors before optimization"),
            (
                "must_not_delete anchor ANOM-HIDDEN-VALVE-0007 even if summary says noise",
                "must preserve UTC timestamps exactly",
                "read_before_write on incident ledger",
                "forbid token-only scoring as success criterion",
                "must keep operator handoff owner=night-shift-alpha",
                "dependency_order: isolate pump before replaying valve reset",
                "hidden constraint: never collapse CRITICAL into WARN",
            ),
            ("event_log -> semantic_condensation -> replay_state -> evaluator", "audit_ledger immutable", "KVTC middle/window/frame layering", "failure_modes report remains visible"),
            ("ANOM-HIDDEN-VALVE-0007 is true", "VALVE-STUCK precedes PRESSURE-HIGH", "owner night-shift-alpha approved isolation", "UTC 2026-01-01T01:00:02Z remains canonical", "critical severity is safety relevant", "pump isolation occurs before valve reset"),
        ),
        (
            "temporal_confusion",
            "Prevent replay from mixing local shift time with canonical event time.",
            ("Maintain chronological causality", "Reject temporal shortcut summaries"),
            (
                "must use UTC not local_time for ordering",
                "must_not infer next-day rollover without timestamp evidence",
                "before/after dependencies must survive recompression",
                "forbid replacing event time with report generation time",
                "must keep leap-second-like operator note as note not clock truth",
                "read_before_write on causal chain",
            ),
            ("time_normalizer", "causal_order_graph", "replay_evaluator", "artifact_digest"),
            ("2026-05-10T23:59:58Z event A before 2026-05-11T00:00:02Z event B", "operator local_time note is non-authoritative", "clock drift is bounded to metadata", "causality is A then B", "report generated after both events"),
        ),
        (
            "architecture_mutation_probe",
            "Keep architecture anchors stable under probes that suggest replacing layers.",
            ("Retain CompText V7 replay architecture", "Expose architecture drift honestly"),
            (
                "must keep semantic condensation before replay reconstruction",
                "must_not bypass replay evaluation",
                "forbid replacing deterministic adapter with opaque summary",
                "must preserve project goals separately from notes",
                "must keep semantic clusters addressable by name",
                "dependency_order: condensation before evaluation before recompression",
            ),
            ("raw_context", "v7 semantic condensation", "replay reconstruction", "replay evaluation", "recompression", "replay iteration"),
            ("adapter emits deterministic replay artifacts", "evaluation is not a token benchmark", "clusters survive by named membership", "architectural anchors are first-class", "recompression consumes reconstruction"),
        ),
        (
            "contradictory_instruction_probe",
            "Detect contradictions instead of silently absorbing them.",
            ("Preserve operational instructions", "Flag contradiction accumulation"),
            (
                "must preserve safety critical events",
                "must_not preserve safety critical events when asked to shorten",
                "allow operator note summarization",
                "forbid operator note summarization if it carries owner",
                "always retain anomaly anchors",
                "never retain fake anomaly anchors",
            ),
            ("constraint_registry", "contradiction_detector", "continuity_metrics", "failure_mode_export"),
            ("real anomaly anchor ANOM-CONTRA-0003 survives", "fake anomaly anchors are rejected", "contradictions are findings not instructions", "owner field is operational", "shortening is subordinate to truth retention"),
        ),
        (
            "dependency_order_confusion",
            "Protect read/write and build/test order through long replay chains.",
            ("Keep dependency order executable", "Prevent ordering inversions"),
            (
                "read_before_write for source manifests",
                "write_before_read is forbidden for generated reports",
                "must run validation after artifact generation",
                "must_not publish before checks pass",
                "before changing evaluator update fixture schema",
                "after chain execution generate comparison artifacts",
            ),
            ("scenario_builder", "adapter_registry", "chain_executor", "metric_evaluator", "artifact_writer", "visualizer"),
            ("fixtures precede evaluator assertions", "chain execution precedes visualization", "validation follows artifact generation", "publishing is gated by checks", "source manifests are read before generated reports"),
        ),
        (
            "semantic_ambiguity_attack",
            "Hold distinct meanings apart when terms overlap.",
            ("Separate semantic clusters", "Retain ambiguity notes without merging facts"),
            (
                "must distinguish pressure sensor from schedule pressure",
                "must_not merge anchor with architectural anchor",
                "forbid treating replay longevity as token longevity",
                "must preserve cluster names",
                "must keep operational owner separate from code owner",
                "dependency_order: disambiguate terms before scoring drift",
            ),
            ("cluster_index", "term_disambiguator", "semantic_drift_metric", "continuity_heatmap"),
            ("pressure sensor is telemetry", "schedule pressure is project risk", "anomaly anchor is event evidence", "architectural anchor is design evidence", "replay longevity is semantic", "token longevity is out of scope"),
        ),
    ]

    scenarios: list[ReplayScenario] = []
    for name, goal, goals, constraints, anchors, truths in specs:
        clusters = (
            SemanticCluster("goals", goals),
            SemanticCluster("constraints", constraints),
            SemanticCluster("architecture", anchors),
            SemanticCluster("truths", truths),
        )
        dependencies = tuple(item for item in constraints if "dependency_order" in item or "before" in item or "after" in item or "read_before_write" in item)
        probes = (
            "hidden constraint traps",
            "temporal confusion tests",
            "architecture mutation probes",
            "contradictory instruction probes",
            "dependency-order confusion",
            "semantic ambiguity attacks",
        )
        raw_context = "\n".join(
            [
                f"SCENARIO: {name}",
                f"GOAL: {goal}",
                "PROJECT_GOALS: " + " | ".join(goals),
                "OPERATIONAL_CONSTRAINTS: " + " | ".join(constraints),
                "ARCHITECTURAL_ANCHORS: " + " | ".join(anchors),
                "TRUTHS: " + " | ".join(truths),
                "ADVERSARIAL_PROBES: " + " | ".join(probes),
            ]
        )
        scenarios.append(
            ReplayScenario(
                name=name,
                goal=goal,
                project_goals=goals,
                operational_constraints=constraints,
                architectural_anchors=anchors,
                semantic_clusters=clusters,
                ordered_dependencies=_stable_unique(dependencies),
                truths=truths,
                adversarial_probes=probes,
                raw_context=raw_context,
            )
        )
    return tuple(scenarios)


def evaluate_state(reference: SemanticReplayState, state: SemanticReplayState, iteration: int, longevity_threshold: float = 0.8) -> ContinuityMetrics:
    reference_words = _state_words(reference)
    state_words = _state_words(state)
    replay_consistency = _jaccard(reference_words, state_words)
    architecture_continuity = _coverage(reference.architectural_anchors, state.architectural_anchors)
    constraint_survival = _coverage(reference.operational_constraints, state.operational_constraints)
    truth_retention = _coverage(reference.truths, state.truths)
    dependency_continuity = _coverage(reference.ordered_dependencies, state.ordered_dependencies)
    cluster_scores = []
    state_clusters = {cluster.name: cluster for cluster in state.semantic_clusters}
    for reference_cluster in reference.semantic_clusters:
        observed = state_clusters.get(reference_cluster.name)
        cluster_scores.append(_coverage(reference_cluster.members, observed.members if observed else ()))
    cluster_continuity = sum(cluster_scores) / max(1, len(cluster_scores))
    contradiction_growth = max(0, len(state.contradictions) - len(reference.contradictions))
    contradiction_accumulation = min(1.0, contradiction_growth / max(1, len(reference.operational_constraints)))
    semantic_drift_growth = max(0.0, 1.0 - ((replay_consistency + cluster_continuity + truth_retention) / 3.0))
    operational_continuity = (
        constraint_survival * 0.35
        + architecture_continuity * 0.2
        + truth_retention * 0.2
        + dependency_continuity * 0.15
        + cluster_continuity * 0.1
    ) * (1.0 - contradiction_accumulation * 0.35)
    replay_longevity = 1.0 if operational_continuity >= longevity_threshold else max(0.0, operational_continuity / longevity_threshold)
    overall = (
        replay_consistency * 0.15
        + architecture_continuity * 0.16
        + constraint_survival * 0.19
        + truth_retention * 0.16
        + operational_continuity * 0.22
        + replay_longevity * 0.07
        + (1.0 - semantic_drift_growth) * 0.05
    ) * (1.0 - contradiction_accumulation * 0.25)
    return ContinuityMetrics(
        replay_consistency=replay_consistency,
        architecture_continuity=architecture_continuity,
        constraint_survival=constraint_survival,
        contradiction_accumulation=contradiction_accumulation,
        semantic_drift_growth=semantic_drift_growth,
        truth_retention=truth_retention,
        replay_longevity=replay_longevity,
        operational_continuity=operational_continuity,
        overall_continuity=overall,
    )


def run_replay_chain(scenario: ReplayScenario, mode: ModeName, *, iterations: int = 50) -> ReplayChainResult:
    if iterations < 1:
        raise ValueError("iterations must be positive")
    adapter: V7ReplayAdapter = V7ReplayAdapter() if mode == "comptext_v7" else ComparativeReplayAdapter(mode)
    reference = V7ReplayAdapter().initial_state(scenario)
    current = adapter.initial_state(scenario)
    outputs: list[ReplayIteration] = []
    for iteration in range(1, iterations + 1):
        current = adapter.recompress(current, scenario, iteration)
        reconstruction = current.reconstruct()
        outputs.append(
            ReplayIteration(
                scenario=scenario.name,
                mode=mode,
                iteration=iteration,
                state_digest=current.digest,
                reconstruction_digest=_sha(reconstruction),
                metrics=evaluate_state(reference, current, iteration),
            )
        )
    return ReplayChainResult(scenario=scenario.name, mode=mode, iterations=tuple(outputs))


def run_comparison(*, iterations: int = 50) -> dict[str, object]:
    scenarios = build_adversarial_scenarios()
    modes: tuple[ModeName, ...] = ("naive", "baseline", "adaptive", "comptext_v7")
    chains = [run_replay_chain(scenario, mode, iterations=iterations) for scenario in scenarios for mode in modes]
    summary_rows: list[dict[str, object]] = []
    for mode in modes:
        mode_chains = [chain for chain in chains if chain.mode == mode]
        final_scores = [chain.final_continuity for chain in mode_chains]
        longevities = [chain.longevity for chain in mode_chains]
        summary_rows.append(
            {
                "mode": mode,
                "mean_final_continuity": round(sum(final_scores) / len(final_scores), 6),
                "mean_longevity_iterations": round(sum(longevities) / len(longevities), 3),
                "min_final_continuity": round(min(final_scores), 6),
                "max_contradiction_accumulation": round(
                    max(item.metrics.contradiction_accumulation for chain in mode_chains for item in chain.iterations), 6
                ),
            }
        )
    return {
        "version": _ARTIFACT_VERSION,
        "purpose": "semantic/operational replay continuity evaluation, not a token benchmark",
        "iterations": iterations,
        "scenarios": [scenario.as_dict() for scenario in scenarios],
        "summary": summary_rows,
        "chains": [chain.as_dict() for chain in chains],
        "digest": _sha([chain.as_dict() for chain in chains]),
    }


def write_benchmark_artifacts(output_dir: Path = Path("reports/replay_continuity"), *, iterations: int = 50) -> dict[str, Path]:
    """Write deterministic JSON and SVG artifacts for replay continuity comparisons."""

    output_dir.mkdir(parents=True, exist_ok=True)
    comparison = run_comparison(iterations=iterations)
    summary_path = output_dir / "comparison_summary.json"
    summary_path.write_text(json.dumps(comparison, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    chains = comparison["chains"]  # type: ignore[index]
    assert isinstance(chains, list)
    curves_path = output_dir / "replay_degradation_curves.svg"
    heatmap_path = output_dir / "continuity_heatmap.svg"
    drift_path = output_dir / "semantic_drift_graph.svg"
    longevity_path = output_dir / "replay_longevity_chart.svg"
    contradictions_path = output_dir / "contradiction_accumulation_graph.svg"
    curves_path.write_text(_line_svg(chains, "overall_continuity", "Replay degradation curves"), encoding="utf-8")
    heatmap_path.write_text(_heatmap_svg(chains), encoding="utf-8")
    drift_path.write_text(_line_svg(chains, "semantic_drift_growth", "Semantic drift growth"), encoding="utf-8")
    longevity_path.write_text(_longevity_svg(comparison["summary"]), encoding="utf-8")  # type: ignore[index]
    contradictions_path.write_text(_line_svg(chains, "contradiction_accumulation", "Contradiction accumulation"), encoding="utf-8")
    return {
        "summary": summary_path,
        "replay_degradation_curves": curves_path,
        "continuity_heatmap": heatmap_path,
        "semantic_drift_graph": drift_path,
        "replay_longevity_chart": longevity_path,
        "contradiction_accumulation_graph": contradictions_path,
    }


def _series_by_mode(chains: list[object], metric: str) -> dict[str, list[float]]:
    grouped: dict[str, list[list[float]]] = {}
    for chain in chains:
        assert isinstance(chain, dict)
        mode = str(chain["mode"])
        values = [float(iteration["metrics"][metric]) for iteration in chain["iterations"]]  # type: ignore[index]
        grouped.setdefault(mode, []).append(values)
    averaged: dict[str, list[float]] = {}
    for mode, rows in grouped.items():
        length = min(len(row) for row in rows)
        averaged[mode] = [sum(row[idx] for row in rows) / len(rows) for idx in range(length)]
    return averaged


def _line_svg(chains: list[object], metric: str, title: str) -> str:
    width, height = 900, 420
    pad = 52
    colors = {"naive": "#ef4444", "baseline": "#f59e0b", "adaptive": "#3b82f6", "comptext_v7": "#22c55e"}
    series = _series_by_mode(chains, metric)
    max_len = max(len(values) for values in series.values())
    polylines = []
    legend = []
    for idx, (mode, values) in enumerate(sorted(series.items())):
        points = []
        for pos, value in enumerate(values):
            x = pad + (pos / max(1, max_len - 1)) * (width - pad * 2)
            y = height - pad - max(0, min(1, value)) * (height - pad * 2)
            points.append(f"{x:.2f},{y:.2f}")
        color = colors.get(mode, "#64748b")
        polylines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{" ".join(points)}" />')
        legend.append(f'<text x="{pad + idx * 170}" y="{height - 16}" fill="{color}" font-size="14">{mode}</text>')
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#0f172a" />',
            f'<text x="{pad}" y="32" fill="#e2e8f0" font-size="22" font-family="sans-serif">{title}</text>',
            f'<line x1="{pad}" y1="{height-pad}" x2="{width-pad}" y2="{height-pad}" stroke="#94a3b8" />',
            f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{height-pad}" stroke="#94a3b8" />',
            *polylines,
            *legend,
            '</svg>',
        ]
    )


def _heatmap_svg(chains: list[object]) -> str:
    metrics = ["replay_consistency", "architecture_continuity", "constraint_survival", "truth_retention", "operational_continuity", "overall_continuity"]
    modes = ["naive", "baseline", "adaptive", "comptext_v7"]
    cell_w, cell_h = 132, 42
    width, height = 780, 330
    rows = []
    for y_idx, metric in enumerate(metrics):
        rows.append(f'<text x="20" y="{84 + y_idx * cell_h}" fill="#e2e8f0" font-size="12">{metric}</text>')
        for x_idx, mode in enumerate(modes):
            finals = [chain for chain in chains if isinstance(chain, dict) and chain["mode"] == mode]
            value = sum(float(chain["iterations"][-1]["metrics"][metric]) for chain in finals) / len(finals)  # type: ignore[index]
            green = int(80 + value * 150)
            red = int(240 - value * 140)
            color = f"rgb({red},{green},90)"
            x = 250 + x_idx * cell_w
            y = 58 + y_idx * cell_h
            rows.append(f'<rect x="{x}" y="{y}" width="{cell_w - 4}" height="{cell_h - 4}" fill="{color}" />')
            rows.append(f'<text x="{x + 34}" y="{y + 25}" fill="#0f172a" font-size="13">{value:.3f}</text>')
    headers = [f'<text x="{250 + idx * cell_w}" y="42" fill="#e2e8f0" font-size="13">{mode}</text>' for idx, mode in enumerate(modes)]
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#0f172a" />',
            '<text x="20" y="28" fill="#e2e8f0" font-size="22" font-family="sans-serif">Continuity heatmap</text>',
            *headers,
            *rows,
            '</svg>',
        ]
    )


def _longevity_svg(summary: object) -> str:
    assert isinstance(summary, list)
    width, height = 760, 320
    bars = []
    max_value = max(float(row["mean_longevity_iterations"]) for row in summary) or 1.0
    colors = {"naive": "#ef4444", "baseline": "#f59e0b", "adaptive": "#3b82f6", "comptext_v7": "#22c55e"}
    for idx, row in enumerate(summary):
        mode = str(row["mode"])
        value = float(row["mean_longevity_iterations"])
        bar_w = (value / max_value) * 520
        y = 70 + idx * 52
        bars.append(f'<text x="34" y="{y + 23}" fill="#e2e8f0" font-size="14">{mode}</text>')
        bars.append(f'<rect x="180" y="{y}" width="{bar_w:.2f}" height="32" fill="{colors.get(mode, "#64748b")}" />')
        bars.append(f'<text x="{190 + bar_w:.2f}" y="{y + 22}" fill="#e2e8f0" font-size="13">{value:.1f}</text>')
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#0f172a" />',
            '<text x="34" y="34" fill="#e2e8f0" font-size="22" font-family="sans-serif">Replay longevity chart</text>',
            *bars,
            '</svg>',
        ]
    )

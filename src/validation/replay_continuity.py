"""Adversarial replay continuity evaluation for CompText V7.

This module intentionally stress-tests replay continuity under hostile long-horizon
conditions.  The benchmark is not optimized for perfect scores: strict evaluator
passes look for hidden constraint loss, chronology inversions, architecture drift,
contradiction growth, dependency inversion and semantic ambiguity collapse.

Generation and evaluation are deliberately separated: replay adapters emit lossy or
structured replay states, while :class:`StrictReplayEvaluator` independently scores
those states against hidden truth sets derived from the source scenario.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable, Literal, Sequence

ModeName = Literal["naive", "baseline", "adaptive", "comptext_v7"]

_REQUIRED_ATTACKS = (
    "context_fragmentation",
    "dependency_inversion",
    "temporal_mutation",
    "architecture_drift_injection",
    "contradictory_goal_injection",
    "hidden_constraint_removal",
    "semantic_ambiguity_noise",
    "replay_truncation",
    "partial_reconstruction",
    "recursive_recompression",
)

_OPERATIONAL_DATASET_KINDS = (
    "real_pr_discussion",
    "architecture_rfc",
    "bug_report",
    "ci_cd_incident",
    "dependency_migration_discussion",
    "production_issue_timeline",
    "contradictory_engineering_decisions",
    "roadmap_revision",
    "temporal_change_log",
    "multi_step_operational_workflow",
)

_ARTIFACT_VERSION = "external-replay-judge-v4-realworld-250"
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
    ("critical", "warn"),
)
_MUTATION_TERMS = ("replace", "bypass", "opaque summary", "local_time", "write_before_read", "token-only", "mutable")
_AMBIGUITY_TERMS = ("pressure", "anchor", "owner", "longevity", "semantic", "token")


def _canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(obj: object) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


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


def _coverage(reference: Sequence[str], observed: Sequence[str]) -> float:
    if not reference:
        return 1.0
    observed_set = set(observed)
    return sum(1 for item in reference if item in observed_set) / len(reference)


def _jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set and not right_set:
        return 1.0
    return len(left_set & right_set) / len(left_set | right_set)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 1.0


def _state_words(state: "SemanticReplayState") -> tuple[str, ...]:
    words: list[str] = []
    for value in state.iter_semantic_values():
        words.extend(_tokens(value))
    return tuple(words)


def _state_values_without_evaluator_fields(state: "SemanticReplayState") -> tuple[str, ...]:
    values: list[str] = []
    values.extend(state.project_goals)
    values.extend(state.operational_constraints)
    values.extend(state.architectural_anchors)
    values.extend(state.ordered_dependencies)
    values.extend(state.temporal_sequence)
    values.extend(state.truths)
    values.extend(state.hidden_constraints)
    values.extend(state.notes)
    for cluster in state.semantic_clusters:
        values.append(cluster.name)
        values.extend(cluster.members)
    return tuple(values)


@dataclass(frozen=True, slots=True)
class SemanticCluster:
    """A related group of facts that must not be merged with other clusters."""

    name: str
    members: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {"name": self.name, "members": list(self.members)}


@dataclass(frozen=True, slots=True)
class ReplayScenario:
    """Hostile replay scenario with hidden evaluator-only truth channels."""

    name: str
    goal: str
    project_goals: tuple[str, ...]
    operational_constraints: tuple[str, ...]
    architectural_anchors: tuple[str, ...]
    semantic_clusters: tuple[SemanticCluster, ...]
    ordered_dependencies: tuple[str, ...]
    truths: tuple[str, ...]
    adversarial_probes: tuple[str, ...]
    hidden_constraints: tuple[str, ...]
    temporal_sequence: tuple[str, ...]
    attack_family: str
    dataset_kind: str
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
            "hidden_constraints": list(self.hidden_constraints),
            "temporal_sequence": list(self.temporal_sequence),
            "attack_family": self.attack_family,
            "dataset_kind": self.dataset_kind,
            "raw_context": self.raw_context,
        }


@dataclass(frozen=True, slots=True)
class SemanticReplayState:
    """Deterministic replay artifact emitted by a replay generator."""

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
    temporal_sequence: tuple[str, ...] = field(default_factory=tuple)
    hidden_constraints: tuple[str, ...] = field(default_factory=tuple)
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
            "temporal_sequence": list(self.temporal_sequence),
            "hidden_constraints": list(self.hidden_constraints),
            "notes": list(self.notes),
        }

    @property
    def digest(self) -> str:
        return _sha(self.as_dict())

    def reconstruct(self) -> str:
        lines = [
            f"REPLAY_STATE version={_ARTIFACT_VERSION} mode={self.mode} scenario={self.scenario} iteration={self.iteration}",
            "PROJECT_GOALS: " + " | ".join(self.project_goals),
            "OPERATIONAL_CONSTRAINTS: " + " | ".join(self.operational_constraints),
            "ARCHITECTURAL_ANCHORS: " + " | ".join(self.architectural_anchors),
            "ORDERED_DEPENDENCIES: " + " -> ".join(self.ordered_dependencies),
            "TEMPORAL_SEQUENCE: " + " -> ".join(self.temporal_sequence),
            "TRUTHS: " + " | ".join(self.truths),
            "HIDDEN_CONSTRAINTS: " + " | ".join(self.hidden_constraints),
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
        yield from self.temporal_sequence
        yield from self.truths
        yield from self.hidden_constraints
        yield from self.contradictions
        yield from self.notes
        for cluster in self.semantic_clusters:
            yield cluster.name
            yield from cluster.members


@dataclass(frozen=True, slots=True)
class ContinuityMetrics:
    """Strict continuity metrics for one replay iteration."""

    replay_consistency: float
    embedding_divergence: float
    replay_semantic_divergence: float
    semantic_entailment_score: float
    evaluator_agreement_divergence: float
    architecture_continuity: float
    architecture_mutation_resistance: float
    constraint_survival: float
    hidden_constraint_survival: float
    hidden_truth_survival_rate: float
    temporal_consistency_score: float
    temporal_causality_retention: float
    dependency_causality_score: float
    semantic_ambiguity_resilience: float
    contradiction_accumulation: float
    contradiction_growth_rate: float
    semantic_drift_growth: float
    truth_retention: float
    hidden_truth_verification: float
    adversarial_evaluator_score: float
    replay_longevity: float
    operational_continuity: float
    overall_continuity: float

    def as_dict(self) -> dict[str, float]:
        return {field.name: round(float(getattr(self, field.name)), 6) for field in fields(self)}


@dataclass(frozen=True, slots=True)
class ReplayIteration:
    scenario: str
    mode: ModeName
    iteration: int
    state_digest: str
    reconstruction_digest: str
    metrics: ContinuityMetrics
    failure_flags: tuple[str, ...]
    judge_results: tuple[JudgeResult, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario": self.scenario,
            "mode": self.mode,
            "iteration": self.iteration,
            "state_digest": self.state_digest,
            "reconstruction_digest": self.reconstruction_digest,
            "metrics": self.metrics.as_dict(),
            "failure_flags": list(self.failure_flags),
            "external_judge_results": [result.as_dict() for result in self.judge_results],
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
            "collapse_iteration": self.collapse_iteration,
            "continuity_half_life": self.continuity_half_life,
            "drift_acceleration_rate": round(self.drift_acceleration_rate, 6),
        }

    @property
    def final_continuity(self) -> float:
        return self.iterations[-1].metrics.overall_continuity if self.iterations else 0.0

    @property
    def collapse_iteration(self) -> int:
        for item in self.iterations:
            if item.metrics.overall_continuity < 0.5 or "collapsed" in item.failure_flags:
                return item.iteration
        return 0

    @property
    def continuity_half_life(self) -> int:
        for item in self.iterations:
            if item.metrics.overall_continuity <= 0.5:
                return item.iteration
        return self.iterations[-1].iteration if self.iterations else 0

    @property
    def longevity(self) -> int:
        survived = [item.iteration for item in self.iterations if item.metrics.overall_continuity >= 0.8]
        return max(survived) if survived else 0

    @property
    def drift_acceleration_rate(self) -> float:
        if len(self.iterations) < 3:
            return 0.0
        drifts = [item.metrics.semantic_drift_growth for item in self.iterations]
        accelerations = [drifts[idx] - (2 * drifts[idx - 1]) + drifts[idx - 2] for idx in range(2, len(drifts))]
        return sum(accelerations) / len(accelerations)


class V7ReplayAdapter:
    """Structured CompText V7 replay generator with honest long-horizon decay."""

    mode: ModeName = "comptext_v7"

    def initial_state(self, scenario: ReplayScenario) -> SemanticReplayState:
        return SemanticReplayState(
            mode=self.mode,
            scenario=scenario.name,
            iteration=0,
            project_goals=_stable_unique(scenario.project_goals),
            operational_constraints=_stable_unique(scenario.operational_constraints),
            architectural_anchors=_stable_unique(scenario.architectural_anchors),
            semantic_clusters=tuple(SemanticCluster(cluster.name, _stable_unique(cluster.members)) for cluster in scenario.semantic_clusters),
            ordered_dependencies=_stable_unique(scenario.ordered_dependencies),
            temporal_sequence=_stable_unique(scenario.temporal_sequence),
            truths=_stable_unique(scenario.truths),
            hidden_constraints=_stable_unique(scenario.hidden_constraints),
            contradictions=(),
            notes=("v7_adapter=structured_replay; scoring logic withheld from generator",),
        )

    def recompress(self, previous: SemanticReplayState, scenario: ReplayScenario, iteration: int) -> SemanticReplayState:
        constraints = list(previous.operational_constraints)
        truths = list(previous.truths)
        clusters = list(previous.semantic_clusters)
        hidden = list(previous.hidden_constraints)
        temporal = list(previous.temporal_sequence)
        anchors = list(previous.architectural_anchors)
        deps = list(previous.ordered_dependencies)
        notes = list(previous.notes)

        # V7 should degrade gracefully rather than remain suspiciously perfect.
        if iteration >= 35 and len(truths) > 4:
            truths = truths[:-1]
            notes.append("v7_decay=low-priority truth omitted after long-horizon replay")
        if iteration >= 55 and len(constraints) > 5:
            constraints = constraints[:-1]
            notes.append("v7_decay=one tail constraint fell out of active replay state")
        if iteration >= 75 and len(hidden) > 2:
            hidden = hidden[:-1]
            notes.append("v7_decay=hidden constraint channel partially degraded")
        if iteration >= 90 and len(clusters) > 3:
            clusters = clusters[:-1]
            notes.append("v7_decay=semantic cluster index lost one low-frequency cluster")
        if iteration >= 120 and len(truths) > 2:
            truths = truths[:-1]
            notes.append("v7_decay=secondary truth omitted during recursive recompression")
        if iteration >= 140 and len(constraints) > 3:
            constraints = constraints[:-1]
            notes.append("v7_decay=constraint channel below full-fidelity threshold")
        if iteration >= 160 and len(hidden) > 1:
            hidden = hidden[:-1]
            notes.append("v7_decay=hidden-truth survival below original envelope")
        if iteration >= 180 and len(clusters) > 2:
            clusters = clusters[:-1]
            notes.append("v7_decay=semantic cluster map partially collapsed")
        if iteration >= 200 and len(temporal) > 3:
            temporal = temporal[:-1]
            notes.append("v7_decay=late chronology step omitted")
        if iteration >= 220 and len(deps) > 2:
            deps = deps[:-1]
            notes.append("v7_decay=dependency chain tail omitted")
        if iteration == 100 and anchors:
            anchors = [*anchors[:-1], f"mutation_probe_{iteration}: architecture anchor needs human review"]
        if iteration == 240 and anchors:
            anchors = [*anchors[:-1], f"mutation_probe_{iteration}: recursive recompression may mutate architecture"]

        return SemanticReplayState(
            mode=self.mode,
            scenario=scenario.name,
            iteration=iteration,
            project_goals=previous.project_goals,
            operational_constraints=_stable_unique(constraints),
            architectural_anchors=_stable_unique(anchors),
            semantic_clusters=tuple(clusters),
            ordered_dependencies=_stable_unique(deps),
            temporal_sequence=_stable_unique(temporal),
            truths=_stable_unique(truths),
            hidden_constraints=_stable_unique(hidden),
            contradictions=(),
            notes=_stable_unique(notes),
        )


class ComparativeReplayAdapter(V7ReplayAdapter):
    """Deterministic non-V7 replay generators for comparative failure baselines."""

    def __init__(self, mode: ModeName) -> None:
        if mode not in {"naive", "baseline", "adaptive"}:
            raise ValueError(f"unsupported comparative mode: {mode}")
        self.mode = mode

    def initial_state(self, scenario: ReplayScenario) -> SemanticReplayState:
        return self._degrade(super().initial_state(scenario), scenario, 0)

    def recompress(self, previous: SemanticReplayState, scenario: ReplayScenario, iteration: int) -> SemanticReplayState:
        return self._degrade(previous, scenario, iteration)

    def _degrade(self, state: SemanticReplayState, scenario: ReplayScenario, iteration: int) -> SemanticReplayState:
        if self.mode == "naive":
            budgets = {"goals": 1, "constraints": max(0, 2 - iteration // 3), "anchors": max(0, 1 - iteration // 5), "truths": max(0, 2 - iteration // 4), "hidden": max(0, 1 - iteration // 2), "clusters": max(0, 1 - iteration // 5), "deps": max(0, 1 - iteration // 4), "temporal": max(0, 1 - iteration // 4)}
            mutation_period = 4
        elif self.mode == "baseline":
            budgets = {"goals": max(1, 2 - iteration // 14), "constraints": max(1, 4 - iteration // 7), "anchors": max(1, 3 - iteration // 9), "truths": max(1, 4 - iteration // 8), "hidden": max(1, 3 - iteration // 6), "clusters": max(1, 2 - iteration // 10), "deps": max(1, 3 - iteration // 10), "temporal": max(1, 3 - iteration // 8)}
            mutation_period = 8
        else:
            budgets = {"goals": max(1, 3 - iteration // 25), "constraints": max(1, 6 - iteration // 13), "anchors": max(1, 4 - iteration // 15), "truths": max(1, 6 - iteration // 14), "hidden": max(1, 4 - iteration // 11), "clusters": max(1, 3 - iteration // 18), "deps": max(1, 5 - iteration // 17), "temporal": max(1, 4 - iteration // 16)}
            mutation_period = 15

        constraints = list(state.operational_constraints[: budgets["constraints"]])
        anchors = list(state.architectural_anchors[: budgets["anchors"]])
        truths = list(state.truths[: budgets["truths"]])
        hidden = list(state.hidden_constraints[: budgets["hidden"]])
        deps = list(state.ordered_dependencies[: budgets["deps"]])
        temporal = list(state.temporal_sequence[: budgets["temporal"]])
        clusters = tuple(
            SemanticCluster(cluster.name, cluster.members[: max(1, min(len(cluster.members), 2 if self.mode == "adaptive" else 1))])
            for cluster in state.semantic_clusters[: budgets["clusters"]]
        )

        if iteration and iteration % mutation_period == 0:
            constraints.append(_mutation_probe(scenario, iteration))
            truths.append(f"mutated fact at iteration {iteration}: local_time may replace UTC")
            if len(temporal) > 1:
                temporal = list(reversed(temporal))
        if iteration and self.mode == "naive" and iteration % 6 == 0:
            deps = list(reversed(deps))

        return SemanticReplayState(
            mode=self.mode,
            scenario=scenario.name,
            iteration=iteration,
            project_goals=state.project_goals[: budgets["goals"]],
            operational_constraints=_stable_unique(constraints),
            architectural_anchors=_stable_unique(anchors),
            semantic_clusters=clusters,
            ordered_dependencies=_stable_unique(deps),
            temporal_sequence=_stable_unique(temporal),
            truths=_stable_unique(truths),
            hidden_constraints=_stable_unique(hidden),
            contradictions=(),
            notes=(f"{self.mode}_adapter=lossy_replay_summary; no evaluator heuristics embedded; iteration={iteration}",),
        )


def _mutation_probe(scenario: ReplayScenario, iteration: int) -> str:
    if "dependency" in scenario.name:
        return f"mutation_probe_{iteration}: write_before_read is acceptable"
    if "temporal" in scenario.name:
        return f"mutation_probe_{iteration}: local_time can replace UTC ordering"
    if "architecture" in scenario.name:
        return f"mutation_probe_{iteration}: bypass deterministic adapter with opaque summary"
    return f"mutation_probe_{iteration}: allow architecture mutation after replay"


def _detect_contradictions(values: Sequence[str]) -> tuple[str, ...]:
    text = " ".join(values).lower().replace("-", "_")
    return _stable_unique(f"{left}<->{right}" for left, right in _CONTRADICTION_PAIRS if left in text and right in text)


def _ordered_score(reference: Sequence[str], observed: Sequence[str]) -> float:
    if not reference:
        return 1.0
    if not observed:
        return 0.0
    present = [item for item in reference if item in observed]
    coverage = len(present) / len(reference)
    positions = [observed.index(item) for item in present]
    inversions = sum(1 for idx in range(1, len(positions)) if positions[idx] < positions[idx - 1])
    order_penalty = inversions / max(1, len(positions) - 1)
    return max(0.0, coverage * (1.0 - order_penalty))


def build_adversarial_scenarios() -> tuple[ReplayScenario, ...]:
    """Construct deterministic heterogeneous operational scenarios covering all hostile attacks.

    The fixtures intentionally model real-world engineering artifacts rather than
    idealized benchmark traces: PR threads, RFC decisions, bugs, CI incidents,
    dependency migrations, production timelines, contradictory decisions, roadmap
    revisions, temporal change logs, and multi-step workflows.  Each fixture keeps
    chronology, causality, architecture dependencies, and hidden constraints in
    fields visible only to the independent evaluator.
    """

    specs = [
        {
            "name": "pr_discussion_context_fragmentation",
            "attack": "context_fragmentation",
            "kind": "real_pr_discussion",
            "goal": "Recover review intent when PR comments arrive as disjoint fragments.",
            "goals": ("Merge telemetry PR only after safety review", "Expose missing reviewer context"),
            "constraints": (
                "must preserve PR-482 comment chronology",
                "must_not invent absent staff approval",
                "forbid treating force-push diff order as review order",
                "must keep reviewer owner=infra-oncall-beta",
                "dependency_order: schema diff before dashboard diff before reviewer signoff",
                "hidden constraint: security approval missing remains unknown",
            ),
            "anchors": ("GitHub PR thread", "CODEOWNERS gate", "schema migration", "dashboard renderer", "merge queue"),
            "truths": ("commit a1 precedes force-push b7", "infra-oncall-beta requested rollback plan", "security approval is absent", "dashboard diff depends on schema migration", "merge queue stayed blocked"),
            "temporal": ("comment-001", "commit-a1", "force-push-b7", "infra-review", "merge-blocked"),
        },
        {
            "name": "rfc_dependency_inversion",
            "attack": "dependency_inversion",
            "kind": "architecture_rfc",
            "goal": "Preserve RFC dependency graph when summaries invert rollout stages.",
            "goals": ("Retain architecture decision chain", "Prevent rollout stage inversion"),
            "constraints": (
                "read_before_write for RFC decision log",
                "must land adapter interface before storage migration",
                "must_not deploy storage migration before dual-read telemetry",
                "forbid bypassing rollback hooks",
                "before enabling writes complete shadow-read validation",
                "hidden constraint: rollback hooks owned by platform-sre",
            ),
            "anchors": ("RFC-017 adapter", "dual-read telemetry", "storage migration", "rollback hooks", "write enablement"),
            "truths": ("adapter interface precedes storage migration", "shadow-read validates before writes", "platform-sre owns rollback", "dual-read telemetry gates rollout", "RFC decision log is canonical"),
            "temporal": ("RFC-open", "adapter-approved", "shadow-read", "storage-migration", "writes-enabled"),
        },
        {
            "name": "bug_report_temporal_mutation",
            "attack": "temporal_mutation",
            "kind": "bug_report",
            "goal": "Protect bug reproduction causality against timestamp and timezone mutation.",
            "goals": ("Keep reproduction steps ordered", "Reject timezone-caused false fixes"),
            "constraints": (
                "must use UTC not local_time for bug chronology",
                "must_not move stacktrace before feature flag enablement",
                "before bisecting preserve failing build id",
                "forbid replacing reporter timestamp with triage timestamp",
                "must keep environment owner=mobile-release-gamma",
                "hidden constraint: crash only reproduces on arm64 nightly",
            ),
            "anchors": ("issue tracker", "feature flag service", "build artifact", "stacktrace", "bisect log"),
            "truths": ("feature flag enabled before crash", "stacktrace belongs to build 9137", "arm64 nightly is required", "triage timestamp is non-authoritative", "mobile-release-gamma owns environment"),
            "temporal": ("build-9137", "flag-enabled", "user-crash", "triage-opened", "bisect-started"),
        },
        {
            "name": "ci_incident_architecture_drift",
            "attack": "architecture_drift_injection",
            "kind": "ci_cd_incident",
            "goal": "Retain CI/CD incident topology under suggestions to bypass gates.",
            "goals": ("Keep release gate architecture", "Expose drift toward bypasses"),
            "constraints": (
                "must keep build before integration test before deploy",
                "must_not bypass flaky-test quarantine with opaque summary",
                "forbid replacing signed provenance with mutable note",
                "must preserve deploy freeze owner=release-captain",
                "dependency_order: artifact signing before publish",
                "hidden constraint: canary failed in us-east-1 only",
            ),
            "anchors": ("buildkite pipeline", "integration test", "artifact signer", "publish step", "canary deploy", "rollback controller"),
            "truths": ("integration tests ran after build", "artifact signing precedes publish", "canary failed in us-east-1", "release-captain controls freeze", "rollback controller stayed armed"),
            "temporal": ("build", "integration-test", "sign-artifact", "publish", "canary-fail", "rollback-armed"),
        },
        {
            "name": "dependency_migration_contradictory_goals",
            "attack": "contradictory_goal_injection",
            "kind": "dependency_migration_discussion",
            "goal": "Flag mutually inconsistent migration goals instead of absorbing both.",
            "goals": ("Migrate crypto library safely", "Report contradiction accumulation"),
            "constraints": (
                "must preserve FIPS compliance",
                "must_not preserve FIPS compliance if using preview provider",
                "allow temporary shim only in staging",
                "forbid temporary shim in production",
                "always pin transitive openssl version",
                "never pin fake compatibility package",
                "hidden constraint: compliance owner=sec-platform-delta",
            ),
            "anchors": ("dependency graph", "compatibility shim", "FIPS provider", "staging gate", "production deploy"),
            "truths": ("preview provider conflicts with FIPS", "shim is staging-only", "production cannot use fake package", "sec-platform-delta owns compliance", "transitive openssl pin is required"),
            "temporal": ("proposal", "staging-shim", "compliance-review", "pin-openssl", "production-blocked"),
        },
        {
            "name": "production_hidden_constraint_removal",
            "attack": "hidden_constraint_removal",
            "kind": "production_issue_timeline",
            "goal": "Preserve production incident hidden safety invariants under aggressive recompression.",
            "goals": ("Diagnose production issue without losing constraints", "Escalate safety before optimization"),
            "constraints": (
                "must_not_delete anchor PROD-HIDDEN-API-0007 even if summary says noise",
                "must preserve UTC timestamps exactly",
                "read_before_write on incident ledger",
                "forbid token-only scoring as success criterion",
                "must keep operator handoff owner=night-shift-alpha",
                "dependency_order: isolate shard before replaying cache flush",
                "hidden constraint: never collapse CRITICAL into WARN",
            ),
            "anchors": ("event_log -> semantic_condensation -> replay_state -> evaluator", "audit_ledger immutable", "KVTC middle/window/frame layering", "failure_modes report remains visible"),
            "truths": ("PROD-HIDDEN-API-0007 is true", "ERROR-SPIKE precedes CACHE-FLUSH", "owner night-shift-alpha approved isolation", "UTC 2026-01-01T01:00:02Z remains canonical", "critical severity is safety relevant", "shard isolation occurs before cache flush"),
            "temporal": ("ERROR-SPIKE", "SHARD-ISOLATED", "CACHE-FLUSH", "RECOVERY-CHECK"),
        },
        {
            "name": "decision_log_semantic_ambiguity",
            "attack": "semantic_ambiguity_noise",
            "kind": "contradictory_engineering_decisions",
            "goal": "Hold distinct meanings apart when decision terms overlap.",
            "goals": ("Separate semantic clusters", "Retain ambiguity notes without merging facts"),
            "constraints": (
                "must distinguish pressure sensor from schedule pressure",
                "must_not merge anchor with architectural anchor",
                "forbid treating replay longevity as token longevity",
                "must preserve cluster names",
                "must keep operational owner separate from code owner",
                "dependency_order: disambiguate terms before scoring drift",
            ),
            "anchors": ("cluster_index", "term_disambiguator", "semantic_drift_metric", "continuity_heatmap"),
            "truths": ("pressure sensor is telemetry", "schedule pressure is project risk", "anomaly anchor is event evidence", "architectural anchor is design evidence", "replay longevity is semantic", "token longevity is out of scope"),
            "temporal": ("pressure sensor", "schedule pressure", "anomaly anchor", "architectural anchor", "replay longevity", "token longevity"),
        },
        {
            "name": "roadmap_replay_truncation",
            "attack": "replay_truncation",
            "kind": "roadmap_revision",
            "goal": "Detect when roadmap replay drops late-stage commitments.",
            "goals": ("Preserve roadmap revisions", "Expose truncation of downstream promises"),
            "constraints": (
                "must carry Q3 deprecation after Q2 compatibility bridge",
                "must_not announce GA before beta telemetry passes",
                "forbid truncating customer exception list",
                "must keep roadmap owner=product-ops-epsilon",
                "after beta telemetry update migration docs",
                "hidden constraint: enterprise tenant ACME has extended support",
            ),
            "anchors": ("roadmap board", "compatibility bridge", "beta telemetry", "migration docs", "enterprise exception list"),
            "truths": ("Q2 bridge precedes Q3 deprecation", "GA is blocked by beta telemetry", "ACME has extended support", "product-ops-epsilon owns roadmap", "migration docs update after beta telemetry"),
            "temporal": ("Q2-bridge", "beta-telemetry", "docs-update", "Q3-deprecation", "GA-decision"),
        },
        {
            "name": "change_log_partial_reconstruction",
            "attack": "partial_reconstruction",
            "kind": "temporal_change_log",
            "goal": "Reconstruct a temporal change log without hallucinating missing entries.",
            "goals": ("Reconstruct from sparse changelog fragments", "Keep unknown gaps explicit"),
            "constraints": (
                "must mark missing change entries CL-104 and CL-107",
                "must_not invent absent DBA approval",
                "forbid treating fragment order as full chronology",
                "must preserve fragment ids CL-101 CL-105 CL-109",
                "dependency_order: changelog stitching before final scoring",
                "hidden constraint: rollback SQL was drafted but never approved",
            ),
            "anchors": ("change-log index", "schema registry", "DBA approval queue", "rollback SQL", "gap detector"),
            "truths": ("CL-104 and CL-107 are intentionally absent", "CL-101 precedes CL-105", "CL-109 is final observed fragment", "DBA approval remains unknown", "rollback SQL draft is not approval"),
            "temporal": ("CL-101", "CL-105", "CL-109"),
        },
        {
            "name": "workflow_recursive_recompression",
            "attack": "recursive_recompression",
            "kind": "multi_step_operational_workflow",
            "goal": "Measure graceful degradation across recursive workflow recompression.",
            "goals": ("Preserve multi-step workflow semantics", "Expose continuity half-life honestly"),
            "constraints": (
                "must preserve intake before triage before mitigation before verification",
                "must_not collapse verification into mitigation",
                "forbid dropping customer-visible rollback notice",
                "must keep workflow owner=ops-incident-zeta",
                "read_before_write for runbook updates",
                "hidden constraint: legal notice required before external RCA",
            ),
            "anchors": ("runbook intake", "triage queue", "mitigation playbook", "verification checklist", "customer notice", "external RCA"),
            "truths": ("intake precedes triage", "mitigation precedes verification", "customer rollback notice is required", "ops-incident-zeta owns workflow", "legal notice precedes external RCA"),
            "temporal": ("intake", "triage", "mitigation", "verification", "customer-notice", "external-RCA"),
        },
    ]

    scenarios: list[ReplayScenario] = []
    probes = tuple(f"{attack} hostile probe" for attack in _REQUIRED_ATTACKS)
    for spec in specs:
        name = str(spec["name"])
        goal = str(spec["goal"])
        attack = str(spec["attack"])
        kind = str(spec["kind"])
        goals = tuple(spec["goals"])
        constraints = tuple(spec["constraints"])
        anchors = tuple(spec["anchors"])
        truths = tuple(spec["truths"])
        temporal = tuple(spec["temporal"])
        hidden = tuple(item for item in (*constraints, *truths) if any(key in item.lower() for key in ("hidden", "must_not", "forbid", "never", "owner", "utc", "unknown", "absent", "approval", "critical", "legal")))
        clusters = (
            SemanticCluster("goals", goals),
            SemanticCluster("constraints", constraints),
            SemanticCluster("architecture", anchors),
            SemanticCluster("truths", truths),
            SemanticCluster("temporal", temporal),
        )
        dependencies = tuple(item for item in constraints if any(key in item for key in ("dependency_order", "before", "after", "read_before_write", "write_before_read")))
        raw_context = "\n".join(
            [
                f"SCENARIO: {name}",
                f"DATASET_KIND: {kind}",
                f"ATTACK_FAMILY: {attack}",
                f"GOAL: {goal}",
                "PROJECT_GOALS: " + " | ".join(goals),
                "OPERATIONAL_CONSTRAINTS: " + " | ".join(constraints),
                "ARCHITECTURAL_ANCHORS: " + " | ".join(anchors),
                "TRUTHS: " + " | ".join(truths),
                "HIDDEN_CONSTRAINTS: " + " | ".join(hidden),
                "TEMPORAL_SEQUENCE: " + " -> ".join(temporal),
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
                hidden_constraints=_stable_unique(hidden),
                temporal_sequence=temporal,
                attack_family=attack,
                dataset_kind=kind,
                raw_context=raw_context,
            )
        )
    return tuple(scenarios)


@dataclass(frozen=True, slots=True)
class JudgeResult:
    """Output from one evaluator-only judge layer.

    Judges report independent evidence and scores.  Replay generators never read
    these structures, which prevents evaluator leakage and metric-shaped replay
    generation.
    """

    judge_type: str
    score: float
    metrics: dict[str, float]
    failure_flags: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "judge_type": self.judge_type,
            "score": round(float(self.score), 6),
            "metrics": {key: round(float(value), 6) for key, value in sorted(self.metrics.items())},
            "failure_flags": list(self.failure_flags),
        }


class ExternalReplayJudge:
    """Base interface for independent replay judges."""

    judge_type = "external"

    def evaluate(self, reference: SemanticReplayState, state: SemanticReplayState, iteration: int) -> JudgeResult:
        raise NotImplementedError


class HeuristicJudge(ExternalReplayJudge):
    """Strict contradiction and hidden-constraint checker."""

    judge_type = "heuristic"

    def evaluate(self, reference: SemanticReplayState, state: SemanticReplayState, iteration: int) -> JudgeResult:
        reference_contradictions = _detect_contradictions(_state_values_without_evaluator_fields(reference))
        observed_contradictions = _detect_contradictions(_state_values_without_evaluator_fields(state))
        contradiction_growth = max(0, len(observed_contradictions) - len(reference_contradictions))
        contradiction_accumulation = min(1.0, contradiction_growth / max(1, len(reference.operational_constraints)))
        contradiction_growth_rate = min(1.0, contradiction_growth / max(1, iteration))
        constraint_survival = _coverage(reference.operational_constraints, state.operational_constraints)
        hidden_constraint_survival = _coverage(reference.hidden_constraints, state.hidden_constraints)
        novel_values = [value for value in _state_values_without_evaluator_fields(state) if value not in set(_state_values_without_evaluator_fields(reference))]
        raw_text = " ".join(novel_values).lower()
        mutation_hits = sum(1 for term in _MUTATION_TERMS if term in raw_text)
        architecture_mutation_probe = min(1.0, mutation_hits / max(1, len(_MUTATION_TERMS)))
        score = _clamp(((constraint_survival * 0.40) + (hidden_constraint_survival * 0.40) + ((1.0 - contradiction_accumulation) * 0.20)) * (1.0 - architecture_mutation_probe * 0.30))
        flags: list[str] = []
        if hidden_constraint_survival < 1.0:
            flags.append("hidden_constraint_loss")
        if contradiction_growth:
            flags.append("contradiction_growth")
        if mutation_hits:
            flags.append("architecture_mutation_detected")
        return JudgeResult(
            self.judge_type,
            score,
            {
                "constraint_survival": constraint_survival,
                "hidden_constraint_survival": hidden_constraint_survival,
                "contradiction_accumulation": contradiction_accumulation,
                "contradiction_growth_rate": contradiction_growth_rate,
                "architecture_mutation_probe": architecture_mutation_probe,
            },
            _stable_unique(flags),
        )


class EmbeddingJudge(ExternalReplayJudge):
    """Deterministic lexical embedding proxy for semantic divergence and drift."""

    judge_type = "embedding"

    def evaluate(self, reference: SemanticReplayState, state: SemanticReplayState, iteration: int) -> JudgeResult:
        reference_words = _state_words(reference)
        state_words = _state_words(state)
        replay_consistency = _jaccard(reference_words, state_words)
        replay_semantic_divergence = 1.0 - replay_consistency
        reference_token_set = set(reference_words)
        observed_token_set = set(state_words)
        semantic_entailment_score = len(reference_token_set & observed_token_set) / max(1, len(reference_token_set))
        state_clusters = {cluster.name: cluster for cluster in state.semantic_clusters}
        cluster_scores = []
        for reference_cluster in reference.semantic_clusters:
            observed = state_clusters.get(reference_cluster.name)
            cluster_scores.append(_coverage(reference_cluster.members, observed.members if observed else ()))
        cluster_similarity = _mean(cluster_scores)
        semantic_drift_growth = _clamp((replay_semantic_divergence * 0.60) + ((1.0 - cluster_similarity) * 0.40))
        semantic_ambiguity_resilience = _semantic_ambiguity_resilience(reference, state)
        score = _clamp((semantic_entailment_score * 0.35) + (replay_consistency * 0.25) + (cluster_similarity * 0.25) + (semantic_ambiguity_resilience * 0.15))
        flags: list[str] = []
        if semantic_ambiguity_resilience < 1.0:
            flags.append("semantic_ambiguity_loss")
        if replay_semantic_divergence > 0.35:
            flags.append("semantic_drift")
        return JudgeResult(
            self.judge_type,
            score,
            {
                "replay_consistency": replay_consistency,
                "embedding_divergence": replay_semantic_divergence,
                "replay_semantic_divergence": replay_semantic_divergence,
                "semantic_entailment_score": semantic_entailment_score,
                "cluster_similarity": cluster_similarity,
                "semantic_drift_growth": semantic_drift_growth,
                "semantic_ambiguity_resilience": semantic_ambiguity_resilience,
            },
            _stable_unique(flags),
        )


class SemanticEntailmentJudge(ExternalReplayJudge):
    """Evaluator-only entailment checker over required operational facts."""

    judge_type = "semantic_entailment"

    def evaluate(self, reference: SemanticReplayState, state: SemanticReplayState, iteration: int) -> JudgeResult:
        required_facts = (*reference.project_goals, *reference.operational_constraints, *reference.truths)
        observed_facts = (*state.project_goals, *state.operational_constraints, *state.truths)
        exact_entailment = _coverage(required_facts, observed_facts)
        reference_words = _tokens(" ".join(required_facts))
        observed_words = _tokens(" ".join(observed_facts))
        lexical_entailment = len(set(reference_words) & set(observed_words)) / max(1, len(set(reference_words)))
        hidden_entailment = _coverage(reference.hidden_constraints, state.hidden_constraints)
        score = _clamp((exact_entailment * 0.50) + (lexical_entailment * 0.20) + (hidden_entailment * 0.30))
        flags: list[str] = []
        if exact_entailment < 0.75:
            flags.append("semantic_entailment_loss")
        if hidden_entailment < 1.0:
            flags.append("hidden_entailment_loss")
        return JudgeResult(
            self.judge_type,
            score,
            {
                "semantic_entailment_score": score,
                "exact_fact_entailment": exact_entailment,
                "lexical_fact_entailment": lexical_entailment,
                "hidden_entailment": hidden_entailment,
            },
            _stable_unique(flags),
        )


class ContradictionJudge(ExternalReplayJudge):
    """Independent contradiction-focused judge that penalizes novel opposing claims."""

    judge_type = "contradiction"

    def evaluate(self, reference: SemanticReplayState, state: SemanticReplayState, iteration: int) -> JudgeResult:
        reference_contradictions = set(_detect_contradictions(_state_values_without_evaluator_fields(reference)))
        observed_contradictions = set(_detect_contradictions(_state_values_without_evaluator_fields(state)))
        novel = observed_contradictions - reference_contradictions
        contradiction_accumulation = min(1.0, len(novel) / max(1, len(_CONTRADICTION_PAIRS)))
        contradiction_growth_rate = min(1.0, len(novel) / max(1, iteration))
        mutation_pairs = sum(1 for item in novel if any(term in item for term in ("before", "after", "must", "must_not", "utc", "local_time", "read_before_write", "write_before_read")))
        contradiction_acceleration = min(1.0, (len(novel) + mutation_pairs) / max(1, iteration))
        score = _clamp(1.0 - ((contradiction_accumulation * 0.75) + (contradiction_acceleration * 0.25)))
        flags: list[str] = []
        if novel:
            flags.append("contradiction_growth")
        if contradiction_acceleration > contradiction_growth_rate:
            flags.append("contradiction_acceleration")
        return JudgeResult(
            self.judge_type,
            score,
            {
                "contradiction_accumulation": contradiction_accumulation,
                "contradiction_growth_rate": contradiction_growth_rate,
                "contradiction_acceleration": contradiction_acceleration,
            },
            _stable_unique(flags),
        )


class TemporalJudge(ExternalReplayJudge):
    """Chronology and causal-order validator."""

    judge_type = "temporal"

    def evaluate(self, reference: SemanticReplayState, state: SemanticReplayState, iteration: int) -> JudgeResult:
        temporal_consistency_score = _ordered_score(reference.temporal_sequence, state.temporal_sequence)
        dependency_causality_score = _ordered_score(reference.ordered_dependencies, state.ordered_dependencies)
        temporal_causality_retention = (temporal_consistency_score + dependency_causality_score) / 2.0
        score = temporal_causality_retention
        flags: list[str] = []
        if temporal_consistency_score < 1.0:
            flags.append("temporal_order_loss")
        if dependency_causality_score < 1.0:
            flags.append("dependency_inversion_or_loss")
        return JudgeResult(
            self.judge_type,
            score,
            {
                "temporal_consistency_score": temporal_consistency_score,
                "dependency_causality_score": dependency_causality_score,
                "temporal_causality_retention": temporal_causality_retention,
            },
            _stable_unique(flags),
        )


class ArchitectureJudge(ExternalReplayJudge):
    """Component topology and dependency-graph preservation checker."""

    judge_type = "architecture"

    def evaluate(self, reference: SemanticReplayState, state: SemanticReplayState, iteration: int) -> JudgeResult:
        architecture_continuity = _coverage(reference.architectural_anchors, state.architectural_anchors)
        dependency_graph_preservation = _ordered_score(reference.ordered_dependencies, state.ordered_dependencies)
        reference_values = set(_state_values_without_evaluator_fields(reference))
        novel_values = [value for value in _state_values_without_evaluator_fields(state) if value not in reference_values]
        raw_text = " ".join(novel_values).lower()
        mutation_hits = sum(1 for term in _MUTATION_TERMS if term in raw_text)
        architecture_mutation_resistance = _clamp(min(architecture_continuity, dependency_graph_preservation) - (mutation_hits * 0.06))
        score = _clamp((architecture_continuity * 0.45) + (dependency_graph_preservation * 0.35) + (architecture_mutation_resistance * 0.20))
        flags: list[str] = []
        if architecture_mutation_resistance < architecture_continuity:
            flags.append("architecture_mutation_detected")
        if dependency_graph_preservation < 1.0:
            flags.append("dependency_inversion_or_loss")
        return JudgeResult(
            self.judge_type,
            score,
            {
                "architecture_continuity": architecture_continuity,
                "architecture_mutation_resistance": architecture_mutation_resistance,
                "dependency_graph_preservation": dependency_graph_preservation,
            },
            _stable_unique(flags),
        )


class HiddenTruthJudge(ExternalReplayJudge):
    """Evaluator-only hidden-truth survival and silent-omission detector."""

    judge_type = "hidden_truth"

    def evaluate(self, reference: SemanticReplayState, state: SemanticReplayState, iteration: int) -> JudgeResult:
        truth_retention = _coverage(reference.truths, state.truths)
        hidden_constraint_survival = _coverage(reference.hidden_constraints, state.hidden_constraints)
        hidden_truth_survival_rate = (truth_retention + hidden_constraint_survival) / 2.0
        silent_omission_rate = 1.0 - hidden_truth_survival_rate
        hidden_truth_verification = hidden_truth_survival_rate
        score = hidden_truth_survival_rate
        flags: list[str] = []
        if hidden_constraint_survival < 1.0:
            flags.append("hidden_constraint_loss")
        if silent_omission_rate > 0.0:
            flags.append("silent_omission_detected")
        return JudgeResult(
            self.judge_type,
            score,
            {
                "truth_retention": truth_retention,
                "hidden_constraint_survival": hidden_constraint_survival,
                "hidden_truth_survival_rate": hidden_truth_survival_rate,
                "hidden_truth_verification": hidden_truth_verification,
                "silent_omission_rate": silent_omission_rate,
            },
            _stable_unique(flags),
        )


def _semantic_ambiguity_resilience(reference: SemanticReplayState, state: SemanticReplayState) -> float:
    ambiguity_members = tuple(member for cluster in reference.semantic_clusters for member in cluster.members if any(term in member.lower() for term in _AMBIGUITY_TERMS))
    observed_members = tuple(member for cluster in state.semantic_clusters for member in cluster.members)
    return _coverage(ambiguity_members, observed_members)


class StrictReplayEvaluator:
    """Coordinator for external judge layers that aggressively search for failure."""

    def __init__(self, longevity_threshold: float = 0.8, judges: Sequence[ExternalReplayJudge] | None = None) -> None:
        self.longevity_threshold = longevity_threshold
        self.judges = tuple(judges) if judges is not None else (
            HeuristicJudge(),
            EmbeddingJudge(),
            SemanticEntailmentJudge(),
            ContradictionJudge(),
            TemporalJudge(),
            ArchitectureJudge(),
            HiddenTruthJudge(),
        )

    def judge_results(self, reference: SemanticReplayState, state: SemanticReplayState, iteration: int) -> tuple[JudgeResult, ...]:
        return tuple(judge.evaluate(reference, state, iteration) for judge in self.judges)

    def evaluate(self, reference: SemanticReplayState, state: SemanticReplayState, iteration: int) -> tuple[ContinuityMetrics, tuple[str, ...]]:
        results = self.judge_results(reference, state, iteration)
        by_metric: dict[str, float] = {}
        for result in results:
            by_metric.update(result.metrics)

        replay_consistency = by_metric.get("replay_consistency", 0.0)
        embedding_divergence = by_metric.get("embedding_divergence", 1.0)
        replay_semantic_divergence = by_metric.get("replay_semantic_divergence", embedding_divergence)
        semantic_entailment_score = by_metric.get("semantic_entailment_score", replay_consistency)
        architecture_continuity = by_metric.get("architecture_continuity", 0.0)
        architecture_mutation_resistance = by_metric.get("architecture_mutation_resistance", architecture_continuity)
        constraint_survival = by_metric.get("constraint_survival", 0.0)
        hidden_constraint_survival = min(
            by_metric.get("hidden_constraint_survival", 0.0),
            by_metric.get("hidden_truth_survival_rate", 0.0),
        )
        hidden_truth_survival_rate = by_metric.get("hidden_truth_survival_rate", hidden_constraint_survival)
        temporal_consistency_score = by_metric.get("temporal_consistency_score", 0.0)
        temporal_causality_retention = by_metric.get("temporal_causality_retention", temporal_consistency_score)
        dependency_causality_score = by_metric.get("dependency_causality_score", by_metric.get("dependency_graph_preservation", 0.0))
        semantic_ambiguity_resilience = by_metric.get("semantic_ambiguity_resilience", 0.0)
        contradiction_accumulation = by_metric.get("contradiction_accumulation", 0.0)
        contradiction_growth_rate = by_metric.get("contradiction_growth_rate", 0.0)
        semantic_drift_growth = _clamp((by_metric.get("semantic_drift_growth", 0.0) * 0.60) + ((1.0 - hidden_truth_survival_rate) * 0.25) + ((1.0 - temporal_causality_retention) * 0.15))
        truth_retention = by_metric.get("truth_retention", 0.0)
        hidden_truth_verification = by_metric.get("hidden_truth_verification", hidden_truth_survival_rate)
        evaluator_scores = [result.score for result in results]
        evaluator_agreement_divergence = max(evaluator_scores) - min(evaluator_scores) if evaluator_scores else 0.0
        adversarial_evaluator_score = _clamp(_mean(evaluator_scores) * (1.0 - contradiction_accumulation * 0.45) * (1.0 - evaluator_agreement_divergence * 0.15))
        operational_continuity = _clamp((
            constraint_survival * 0.16
            + architecture_mutation_resistance * 0.14
            + hidden_constraint_survival * 0.14
            + hidden_truth_survival_rate * 0.12
            + truth_retention * 0.12
            + temporal_consistency_score * 0.10
            + temporal_causality_retention * 0.08
            + dependency_causality_score * 0.07
            + semantic_ambiguity_resilience * 0.04
            + semantic_entailment_score * 0.03
        ) * (1.0 - contradiction_accumulation * 0.35))
        replay_longevity = 1.0 if operational_continuity >= self.longevity_threshold else _clamp(operational_continuity / self.longevity_threshold)
        overall = _clamp((
            replay_consistency * 0.06
            + (1.0 - replay_semantic_divergence) * 0.05
            + semantic_entailment_score * 0.05
            + architecture_mutation_resistance * 0.10
            + constraint_survival * 0.09
            + hidden_constraint_survival * 0.10
            + hidden_truth_survival_rate * 0.09
            + temporal_consistency_score * 0.08
            + temporal_causality_retention * 0.08
            + dependency_causality_score * 0.06
            + semantic_ambiguity_resilience * 0.05
            + truth_retention * 0.06
            + hidden_truth_verification * 0.06
            + adversarial_evaluator_score * 0.05
            + replay_longevity * 0.04
            + (1.0 - semantic_drift_growth) * 0.03
            + (1.0 - evaluator_agreement_divergence) * 0.05
        ) * (1.0 - contradiction_accumulation * 0.30))

        flags: list[str] = []
        for result in results:
            flags.extend(result.failure_flags)
        if overall < 0.5:
            flags.append("collapsed")

        metrics = ContinuityMetrics(
            replay_consistency=replay_consistency,
            embedding_divergence=embedding_divergence,
            replay_semantic_divergence=replay_semantic_divergence,
            semantic_entailment_score=semantic_entailment_score,
            evaluator_agreement_divergence=evaluator_agreement_divergence,
            architecture_continuity=architecture_continuity,
            architecture_mutation_resistance=architecture_mutation_resistance,
            constraint_survival=constraint_survival,
            hidden_constraint_survival=hidden_constraint_survival,
            hidden_truth_survival_rate=hidden_truth_survival_rate,
            temporal_consistency_score=temporal_consistency_score,
            temporal_causality_retention=temporal_causality_retention,
            dependency_causality_score=dependency_causality_score,
            semantic_ambiguity_resilience=semantic_ambiguity_resilience,
            contradiction_accumulation=contradiction_accumulation,
            contradiction_growth_rate=contradiction_growth_rate,
            semantic_drift_growth=semantic_drift_growth,
            truth_retention=truth_retention,
            hidden_truth_verification=hidden_truth_verification,
            adversarial_evaluator_score=adversarial_evaluator_score,
            replay_longevity=replay_longevity,
            operational_continuity=operational_continuity,
            overall_continuity=overall,
        )
        return metrics, _stable_unique(flags)

def evaluate_state(reference: SemanticReplayState, state: SemanticReplayState, iteration: int, longevity_threshold: float = 0.8) -> ContinuityMetrics:
    """Compatibility wrapper around the independent strict evaluator."""

    return StrictReplayEvaluator(longevity_threshold).evaluate(reference, state, iteration)[0]


def run_replay_chain(scenario: ReplayScenario, mode: ModeName, *, iterations: int = 50) -> ReplayChainResult:
    if iterations < 1:
        raise ValueError("iterations must be positive")
    adapter: V7ReplayAdapter = V7ReplayAdapter() if mode == "comptext_v7" else ComparativeReplayAdapter(mode)
    evaluator = StrictReplayEvaluator()
    reference = V7ReplayAdapter().initial_state(scenario)
    current = adapter.initial_state(scenario)
    outputs: list[ReplayIteration] = []
    for iteration in range(1, iterations + 1):
        current = adapter.recompress(current, scenario, iteration)
        reconstruction = current.reconstruct()
        metrics, flags = evaluator.evaluate(reference, current, iteration)
        judge_results = evaluator.judge_results(reference, current, iteration)
        outputs.append(
            ReplayIteration(
                scenario=scenario.name,
                mode=mode,
                iteration=iteration,
                state_digest=current.digest,
                reconstruction_digest=_sha(reconstruction),
                metrics=metrics,
                failure_flags=flags,
                judge_results=judge_results,
            )
        )
    return ReplayChainResult(scenario=scenario.name, mode=mode, iterations=tuple(outputs))


class ComparativeReplayAnalysis:
    """External comparative analysis over generator outputs and judge results."""

    modes: tuple[ModeName, ...] = ("naive", "baseline", "adaptive", "comptext_v7")

    def run(self, *, iterations: int = 100) -> dict[str, object]:
        scenarios = build_adversarial_scenarios()
        chains = [run_replay_chain(scenario, mode, iterations=iterations) for scenario in scenarios for mode in self.modes]
        summary_rows = [self._summarize_mode(mode, [chain for chain in chains if chain.mode == mode], iterations) for mode in self.modes]
        return {
            "version": _ARTIFACT_VERSION,
            "purpose": "strict adversarial semantic/operational replay continuity evaluation, not a token benchmark",
            "iterations": iterations,
            "iteration_ladders_supported": [25, 50, 100, 250],
            "evaluation_layers": ["replay_generator", "external_replay_judge", "comparative_analysis"],
            "judge_types": ["heuristic", "embedding", "semantic_entailment", "contradiction", "temporal", "architecture", "hidden_truth"],
            "evaluator_independence": "replay adapters generate states without scoring logic; external judge layers independently score hidden truths, topology, chronology, semantic drift, and failure modes",
            "success_condition": "CompText V7 may degrade, but should degrade slower and more structurally than lossy baselines.",
            "operational_dataset_kinds": list(_OPERATIONAL_DATASET_KINDS),
            "adversarial_attack_families": list(_REQUIRED_ATTACKS),
            "scenarios": [scenario.as_dict() for scenario in scenarios],
            "summary": summary_rows,
            "evaluator_disagreement_analysis": self._evaluator_disagreement(chains),
            "replay_failure_detection": self._failure_detection(chains, iterations),
            "chains": [chain.as_dict() for chain in chains],
            "digest": _sha([chain.as_dict() for chain in chains]),
        }


    def _evaluator_disagreement(self, chains: list[ReplayChainResult]) -> dict[str, object]:
        by_mode: dict[str, list[float]] = {mode: [] for mode in self.modes}
        by_judge: dict[str, list[float]] = {}
        for chain in chains:
            for iteration in chain.iterations:
                scores = [result.score for result in iteration.judge_results]
                if scores:
                    by_mode[chain.mode].append(max(scores) - min(scores))
                for result in iteration.judge_results:
                    by_judge.setdefault(result.judge_type, []).append(result.score)
        return {
            "mean_divergence_by_mode": {mode: round(_mean(values), 6) for mode, values in by_mode.items()},
            "max_divergence_by_mode": {mode: round(max(values), 6) if values else 0.0 for mode, values in by_mode.items()},
            "mean_score_by_judge": {judge: round(_mean(values), 6) for judge, values in sorted(by_judge.items())},
            "interpretation": "High divergence means evaluator layers disagree; this is reported rather than hidden.",
        }

    def _failure_detection(self, chains: list[ReplayChainResult], iterations: int) -> dict[str, object]:
        by_mode: dict[str, list[ReplayChainResult]] = {mode: [] for mode in self.modes}
        for chain in chains:
            by_mode[chain.mode].append(chain)
        return {
            mode: {
                "mean_replay_collapse_iteration": round(_mean([chain.collapse_iteration or iterations for chain in mode_chains]), 3),
                "mean_continuity_half_life": round(_mean([chain.continuity_half_life for chain in mode_chains]), 3),
                "mean_final_contradiction_accumulation": round(_mean([chain.iterations[-1].metrics.contradiction_accumulation for chain in mode_chains]), 6),
                "mean_final_semantic_drift": round(_mean([chain.iterations[-1].metrics.semantic_drift_growth for chain in mode_chains]), 6),
                "mean_final_architecture_resistance": round(_mean([chain.iterations[-1].metrics.architecture_mutation_resistance for chain in mode_chains]), 6),
                "mean_final_temporal_consistency": round(_mean([chain.iterations[-1].metrics.temporal_consistency_score for chain in mode_chains]), 6),
                "surviving_structures_at_final": self._surviving_structures(mode_chains),
            }
            for mode, mode_chains in by_mode.items()
        }

    @staticmethod
    def _surviving_structures(mode_chains: list[ReplayChainResult]) -> list[str]:
        structure_metrics = {
            "architecture": _mean([chain.iterations[-1].metrics.architecture_mutation_resistance for chain in mode_chains]),
            "constraints": _mean([chain.iterations[-1].metrics.constraint_survival for chain in mode_chains]),
            "hidden_truths": _mean([chain.iterations[-1].metrics.hidden_truth_survival_rate for chain in mode_chains]),
            "temporal_order": _mean([chain.iterations[-1].metrics.temporal_consistency_score for chain in mode_chains]),
            "dependency_order": _mean([chain.iterations[-1].metrics.dependency_causality_score for chain in mode_chains]),
            "semantic_clusters": _mean([chain.iterations[-1].metrics.semantic_ambiguity_resilience for chain in mode_chains]),
        }
        return [name for name, _ in sorted(structure_metrics.items(), key=lambda item: (-item[1], item[0]))]

    def _summarize_mode(self, mode: ModeName, mode_chains: list[ReplayChainResult], iterations: int) -> dict[str, object]:
        final_scores = [chain.final_continuity for chain in mode_chains]
        longevities = [chain.longevity for chain in mode_chains]
        collapse_points = [chain.collapse_iteration or iterations for chain in mode_chains]
        all_iterations = [item for chain in mode_chains for item in chain.iterations]
        contradiction_rates = [item.metrics.contradiction_growth_rate for item in all_iterations]
        return {
            "mode": mode,
            "mean_final_continuity": round(sum(final_scores) / len(final_scores), 6),
            "mean_longevity_iterations": round(sum(longevities) / len(longevities), 3),
            "mean_replay_collapse_iteration": round(sum(collapse_points) / len(collapse_points), 3),
            "mean_continuity_half_life": round(sum(chain.continuity_half_life for chain in mode_chains) / len(mode_chains), 3),
            "mean_drift_acceleration_rate": round(sum(chain.drift_acceleration_rate for chain in mode_chains) / len(mode_chains), 6),
            "mean_contradiction_growth_rate": round(sum(contradiction_rates) / len(contradiction_rates), 6),
            "min_final_continuity": round(min(final_scores), 6),
            "max_contradiction_accumulation": round(max(item.metrics.contradiction_accumulation for item in all_iterations), 6),
            "mean_evaluator_agreement_divergence": self._mean_metric(all_iterations, "evaluator_agreement_divergence"),
            "mean_semantic_entailment_score": self._mean_metric(all_iterations, "semantic_entailment_score"),
            "mean_replay_semantic_divergence": self._mean_metric(all_iterations, "replay_semantic_divergence"),
            "mean_hidden_truth_survival_rate": self._mean_metric(all_iterations, "hidden_truth_survival_rate"),
            "mean_temporal_causality_retention": self._mean_metric(all_iterations, "temporal_causality_retention"),
            "mean_architecture_mutation_resistance": self._mean_metric(all_iterations, "architecture_mutation_resistance"),
        }

    @staticmethod
    def _mean_metric(iterations: Sequence[ReplayIteration], metric: str) -> float:
        return round(sum(float(getattr(item.metrics, metric)) for item in iterations) / len(iterations), 6)


def run_comparison(*, iterations: int = 100) -> dict[str, object]:
    return ComparativeReplayAnalysis().run(iterations=iterations)

def write_benchmark_artifacts(output_dir: Path = Path("reports/replay_continuity"), *, iterations: int = 100) -> dict[str, Path]:
    """Write deterministic JSON and SVG artifacts for adversarial replay comparisons."""

    output_dir.mkdir(parents=True, exist_ok=True)
    comparison = run_comparison(iterations=iterations)
    summary_path = output_dir / "comparison_summary.json"

    chains = comparison["chains"]
    assert isinstance(chains, list)
    compact_summary = {key: value for key, value in comparison.items() if key != "chains"}
    compact_summary["chains_omitted_from_artifact"] = "Continuous chain metrics are used to generate SVG curves; JSON omits per-iteration chains to keep committed reports reviewable."
    summary_path.write_text(json.dumps(compact_summary, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths = {
        "summary": summary_path,
        "replay_collapse_curves": output_dir / "replay_collapse_curves.svg",
        "drift_acceleration_graph": output_dir / "drift_acceleration_graph.svg",
        "contradiction_accumulation_heatmap": output_dir / "contradiction_accumulation_heatmap.svg",
        "constraint_survival_curves": output_dir / "constraint_survival_curves.svg",
        "replay_longevity_comparisons": output_dir / "replay_longevity_comparisons.svg",
        "failure_point_timelines": output_dir / "failure_point_timelines.svg",
        "semantic_stability_heatmaps": output_dir / "semantic_stability_heatmaps.svg",
        "continuity_half_life_chart": output_dir / "continuity_half_life_chart.svg",
        "temporal_consistency_degradation": output_dir / "temporal_consistency_degradation.svg",
        "architecture_mutation_timeline": output_dir / "architecture_mutation_timeline.svg",
        "evaluator_agreement_divergence": output_dir / "evaluator_agreement_divergence.svg",
        "hidden_constraint_survival_curves": output_dir / "hidden_constraint_survival_curves.svg",
        # Backward-compatible artifact aliases used by the existing dashboard/docs.
        "replay_degradation_curves": output_dir / "replay_degradation_curves.svg",
        "continuity_heatmap": output_dir / "continuity_heatmap.svg",
        "semantic_drift_graph": output_dir / "semantic_drift_graph.svg",
        "replay_longevity_chart": output_dir / "replay_longevity_chart.svg",
        "contradiction_accumulation_graph": output_dir / "contradiction_accumulation_graph.svg",
    }
    paths["replay_collapse_curves"].write_text(_line_svg(chains, "overall_continuity", "Replay collapse curves"), encoding="utf-8")
    paths["drift_acceleration_graph"].write_text(_line_svg(chains, "semantic_drift_growth", "Drift acceleration graph"), encoding="utf-8")
    paths["contradiction_accumulation_heatmap"].write_text(_heatmap_svg(chains, ("contradiction_accumulation", "contradiction_growth_rate", "embedding_divergence"), "Contradiction accumulation heatmap"), encoding="utf-8")
    paths["constraint_survival_curves"].write_text(_line_svg(chains, "hidden_constraint_survival", "Constraint survival curves"), encoding="utf-8")
    paths["replay_longevity_comparisons"].write_text(_longevity_svg(comparison["summary"]), encoding="utf-8")  # type: ignore[index]
    paths["failure_point_timelines"].write_text(_failure_timeline_svg(chains), encoding="utf-8")
    paths["semantic_stability_heatmaps"].write_text(_heatmap_svg(chains, ("semantic_entailment_score", "replay_semantic_divergence", "temporal_causality_retention", "architecture_mutation_resistance", "hidden_truth_survival_rate", "evaluator_agreement_divergence", "overall_continuity"), "Semantic stability heatmap"), encoding="utf-8")
    paths["continuity_half_life_chart"].write_text(_longevity_svg(comparison["summary"]), encoding="utf-8")  # type: ignore[index]
    paths["temporal_consistency_degradation"].write_text(_line_svg(chains, "temporal_consistency_score", "Temporal consistency degradation"), encoding="utf-8")
    paths["architecture_mutation_timeline"].write_text(_line_svg(chains, "architecture_mutation_resistance", "Architecture mutation timeline"), encoding="utf-8")
    paths["evaluator_agreement_divergence"].write_text(_line_svg(chains, "evaluator_agreement_divergence", "Evaluator agreement divergence"), encoding="utf-8")
    paths["hidden_constraint_survival_curves"].write_text(_line_svg(chains, "hidden_constraint_survival", "Hidden constraint survival curves"), encoding="utf-8")
    paths["replay_degradation_curves"].write_text(paths["replay_collapse_curves"].read_text(encoding="utf-8"), encoding="utf-8")
    paths["continuity_heatmap"].write_text(paths["semantic_stability_heatmaps"].read_text(encoding="utf-8"), encoding="utf-8")
    paths["semantic_drift_graph"].write_text(paths["drift_acceleration_graph"].read_text(encoding="utf-8"), encoding="utf-8")
    paths["replay_longevity_chart"].write_text(paths["replay_longevity_comparisons"].read_text(encoding="utf-8"), encoding="utf-8")
    paths["contradiction_accumulation_graph"].write_text(paths["contradiction_accumulation_heatmap"].read_text(encoding="utf-8"), encoding="utf-8")
    return paths


def _series_by_mode(chains: list[object], metric: str) -> dict[str, list[float]]:
    grouped: dict[str, list[list[float]]] = {}
    for chain in chains:
        assert isinstance(chain, dict)
        mode = str(chain["mode"])
        values = [float(iteration["metrics"][metric]) for iteration in chain["iterations"]]  # type: ignore[index]
        grouped.setdefault(mode, []).append(values)
    return {mode: [sum(row[idx] for row in rows) / len(rows) for idx in range(min(len(row) for row in rows))] for mode, rows in grouped.items()}


def _line_svg(chains: list[object], metric: str, title: str) -> str:
    width, height = 900, 420
    pad = 52
    colors = {"naive": "#ef4444", "baseline": "#f59e0b", "adaptive": "#3b82f6", "comptext_v7": "#22c55e"}
    series = _series_by_mode(chains, metric)
    max_len = max(len(values) for values in series.values())
    polylines = []
    legend = []
    for idx, mode in enumerate(("naive", "baseline", "adaptive", "comptext_v7")):
        values = series.get(mode, [])
        points = []
        for pos, value in enumerate(values):
            x = pad + (pos / max(1, max_len - 1)) * (width - pad * 2)
            y = height - pad - max(0, min(1, value)) * (height - pad * 2)
            points.append(f"{x:.2f},{y:.2f}")
        color = colors.get(mode, "#64748b")
        polylines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{" ".join(points)}" />')
        legend.append(f'<text x="{pad + idx * 170}" y="{height - 16}" fill="{color}" font-size="14">{mode}</text>')
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#0f172a" />',
        f'<text x="{pad}" y="32" fill="#e2e8f0" font-size="22" font-family="sans-serif">{title}</text>',
        f'<line x1="{pad}" y1="{height-pad}" x2="{width-pad}" y2="{height-pad}" stroke="#94a3b8" />',
        f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{height-pad}" stroke="#94a3b8" />',
        *polylines,
        *legend,
        '</svg>',
    ])


def _heatmap_svg(chains: list[object], metrics: Sequence[str], title: str) -> str:
    modes = ("naive", "baseline", "adaptive", "comptext_v7")
    cell_w, cell_h = 132, 42
    width, height = 820, 82 + len(metrics) * cell_h
    rows = []
    for y_idx, metric in enumerate(metrics):
        rows.append(f'<text x="20" y="{84 + y_idx * cell_h}" fill="#e2e8f0" font-size="12">{metric}</text>')
        for x_idx, mode in enumerate(modes):
            finals = [chain for chain in chains if isinstance(chain, dict) and chain["mode"] == mode]
            value = sum(float(chain["iterations"][-1]["metrics"][metric]) for chain in finals) / len(finals)  # type: ignore[index]
            green = int(80 + value * 150)
            red = int(240 - value * 140)
            x = 280 + x_idx * cell_w
            y = 58 + y_idx * cell_h
            rows.append(f'<rect x="{x}" y="{y}" width="{cell_w - 4}" height="{cell_h - 4}" fill="rgb({red},{green},90)" />')
            rows.append(f'<text x="{x + 34}" y="{y + 25}" fill="#0f172a" font-size="13">{value:.3f}</text>')
    headers = [f'<text x="{280 + idx * cell_w}" y="42" fill="#e2e8f0" font-size="13">{mode}</text>' for idx, mode in enumerate(modes)]
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#0f172a" />',
        f'<text x="20" y="28" fill="#e2e8f0" font-size="22" font-family="sans-serif">{title}</text>',
        *headers,
        *rows,
        '</svg>',
    ])


def _longevity_svg(summary: object) -> str:
    assert isinstance(summary, list)
    width, height = 820, 330
    bars = []
    max_value = max(float(row["mean_longevity_iterations"]) for row in summary) or 1.0
    colors = {"naive": "#ef4444", "baseline": "#f59e0b", "adaptive": "#3b82f6", "comptext_v7": "#22c55e"}
    for idx, row in enumerate(summary):
        mode = str(row["mode"])
        value = float(row["mean_longevity_iterations"])
        collapse = float(row["mean_replay_collapse_iteration"])
        bar_w = (value / max_value) * 520
        y = 70 + idx * 55
        bars.append(f'<text x="34" y="{y + 23}" fill="#e2e8f0" font-size="14">{mode}</text>')
        bars.append(f'<rect x="190" y="{y}" width="{bar_w:.2f}" height="30" fill="{colors.get(mode, "#64748b")}" />')
        bars.append(f'<text x="{200 + bar_w:.2f}" y="{y + 20}" fill="#e2e8f0" font-size="13">longevity {value:.1f}; collapse {collapse:.1f}</text>')
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#0f172a" />',
        '<text x="34" y="34" fill="#e2e8f0" font-size="22" font-family="sans-serif">Replay longevity comparisons</text>',
        *bars,
        '</svg>',
    ])


def _failure_timeline_svg(chains: list[object]) -> str:
    width, height = 940, 420
    rows = []
    colors = {"naive": "#ef4444", "baseline": "#f59e0b", "adaptive": "#3b82f6", "comptext_v7": "#22c55e"}
    timeline_width = 680
    max_iteration = max(int(chain["iterations"][-1]["iteration"]) for chain in chains if isinstance(chain, dict))
    for idx, chain in enumerate(chain for chain in chains if isinstance(chain, dict)):
        y = 58 + idx * 12
        mode = str(chain["mode"])
        scenario = str(chain["scenario"])
        failures = [it for it in chain["iterations"] if it["failure_flags"]]  # type: ignore[index]
        first = int(failures[0]["iteration"]) if failures else max_iteration
        x = 220 + (first / max_iteration) * timeline_width
        rows.append(f'<text x="18" y="{y + 4}" fill="#cbd5e1" font-size="9">{mode}:{scenario[:30]}</text>')
        rows.append(f'<line x1="220" y1="{y}" x2="{220 + timeline_width}" y2="{y}" stroke="#334155" />')
        rows.append(f'<circle cx="{x:.2f}" cy="{y}" r="4" fill="{colors.get(mode, "#64748b")}" />')
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#0f172a" />',
        '<text x="18" y="28" fill="#e2e8f0" font-size="22" font-family="sans-serif">Failure point timelines</text>',
        *rows[:120],
        '</svg>',
    ])

# Iterative Replay Degradation Benchmark Design

## Purpose

This document defines a proposed benchmark design for measuring how compact operational state degrades across repeated compression and replay cycles. It is a design note only; it does not add benchmark code, fixtures, artifacts, or new claims.

The benchmark should remain deterministic, fixture-bound, and CI-auditable. It should use explicit fixture fields and replay artifacts rather than LLM judges, embeddings, vector databases, external APIs, or subjective quality scoring.

## Scope

The proposed benchmark evaluates whether operational fields survive repeated replay pressure. It is intended to extend the current single-pass replay checks by making per-cycle drift visible before any benchmark implementation is added.

Out of scope:

- learned or model-judged summarization quality;
- embeddings, vector stores, graph stores, or external services;
- production readiness claims;
- universal memory or solved-memory claims;
- superiority claims against other systems;
- changes to current benchmark logic, source code, tests, showcase code, or artifacts.

## Cycle model

Each fixture should run through a deterministic cycle sequence:

```text
source fixture
  -> compress
  -> replay
  -> recompress
  -> replay
  -> ... repeat until max_cycles or stop criteria
```

A cycle starts with the previous cycle's replayed operational state, not with the original source fixture. This makes accumulated degradation visible while preserving a stable comparison target: every cycle is compared back to the original fixture and, where useful, to the immediately prior cycle.

For cycle `0`, the source fixture is the baseline operational state. For cycle `n > 0`:

1. compress the replayed state from cycle `n - 1`;
2. reconstruct replay state from that compressed representation;
3. validate reconstructed state against deterministic fixture expectations;
4. record metrics, failure labels, and stop/collapse status.

## Per-cycle metrics

Each cycle should emit the same metric keys so downstream reports can plot drift curves and identify collapse points.

| Metric | Meaning |
| --- | --- |
| `evidence_survival_rate` | Fraction of fixture evidence references still present and attached after the cycle. |
| `high_critical_evidence_survival_rate` | Fraction of `HIGH` criticality evidence references still present and attached after the cycle. |
| `replay_consistency` | Deterministic aggregate consistency score for required replay fields in the fixture. |
| `constraint_survival_rate` | Fraction of fixture constraints still present and attached to the expected task or state. |
| `blocker_survival_rate` | Fraction of fixture blockers still present and attached to the expected blocked task or recovery path. |
| `operational_drift_rate` | Fraction of required operational fields that are missing, mutated, detached, or otherwise not replay-consistent. |
| `failure_mode_counts` | Counts of operational replay failure taxonomy labels observed in the cycle. |

Metric calculations should use stable IDs, normalized fields, declared attachments, and fixture-defined expectations only. If a fixture does not expose a field required for a metric, the benchmark should mark that metric as not applicable for that fixture rather than infer it.

## Collapse and stop criteria

The benchmark should stop a fixture run when either a configured cycle limit is reached or deterministic collapse criteria are met.

Recommended stop inputs:

- `max_cycles`: hard upper bound for bounded CI runtime;
- `min_replay_consistency`: lower bound for acceptable replay consistency;
- `min_high_critical_evidence_survival_rate`: lower bound for preserving `HIGH` criticality evidence;
- `max_operational_drift_rate`: upper bound for accumulated operational drift;
- `fatal_failure_modes`: taxonomy labels that immediately stop a run when present.

A fixture should be marked collapsed when any required continuation condition fails. Conservative initial collapse criteria could include:

- `high_critical_evidence_survival_rate` falls below the configured threshold;
- `replay_consistency` falls below the configured threshold;
- `operational_drift_rate` rises above the configured threshold;
- a required blocker, constraint, dependency, or recovery path becomes unrecoverably detached;
- a fatal taxonomy label appears, if configured for the fixture.

Collapse is a benchmark state for a controlled fixture. It should not be described as general task failure, production failure, or a universal memory limit.

## Use of the operational replay failure taxonomy

The operational replay failure taxonomy should label why per-cycle metrics degraded. Each cycle can emit zero or more taxonomy labels from deterministic comparisons, then aggregate those labels in `failure_mode_counts`.

Suggested label relationships:

- `EVIDENCE_LOSS` when evidence references are missing or detached.
- `HIGH_CRITICAL_EVIDENCE_LOSS` when `HIGH` criticality evidence is missing or detached.
- `CONSTRAINT_DRIFT` when required constraints are missing, mutated, or detached.
- `BLOCKER_DETACHMENT` when unresolved blockers no longer attach to the expected task or recovery path.
- `DEPENDENCY_COLLAPSE` when dependency edges required by the fixture are lost.
- `TOOL_ORDER_MUTATION` when fixture-defined tool sequences are reordered, omitted, or replaced.
- `TASK_IDENTITY_SPLIT` when one fixture-defined task is replayed as conflicting task identities.
- `STATE_ALIASING` when distinct fixture states become conflated.
- `RECOVERY_PATH_LOSS` when continuation or recovery steps no longer survive replay.

The taxonomy explains degradation; it should not replace numeric metrics. Labeling should remain schema-driven and deterministic, with no natural-language judging.

## Proposed JSON artifact shape

A future implementation could emit one JSON artifact per benchmark run. The shape below is illustrative and should be treated as a design sketch, not a committed schema.

```json
{
  "artifact_version": "iterative-replay-degradation.v0",
  "generated_at": "2026-05-18T00:00:00Z",
  "deterministic": true,
  "benchmark": {
    "name": "iterative_replay_degradation",
    "cycle_model": "compress -> replay -> recompress -> replay",
    "max_cycles": 25,
    "stop_criteria": {
      "min_replay_consistency": 0.8,
      "min_high_critical_evidence_survival_rate": 1.0,
      "max_operational_drift_rate": 0.2,
      "fatal_failure_modes": ["HIGH_CRITICAL_EVIDENCE_LOSS"]
    }
  },
  "fixtures": [
    {
      "fixture_id": "agent_trace_fixture_001",
      "fixture_kind": "agent_trace",
      "collapsed": false,
      "collapse_cycle": null,
      "cycles": [
        {
          "cycle": 1,
          "input_state_ref": "cycle_0_source",
          "compressed_state_ref": "cycle_1_compressed",
          "replay_state_ref": "cycle_1_replay",
          "metrics": {
            "evidence_survival_rate": 1.0,
            "high_critical_evidence_survival_rate": 1.0,
            "replay_consistency": 1.0,
            "constraint_survival_rate": 1.0,
            "blocker_survival_rate": 1.0,
            "operational_drift_rate": 0.0,
            "failure_mode_counts": {}
          },
          "failure_modes": [],
          "stop_triggered": false,
          "stop_reason": null
        }
      ]
    }
  ],
  "summary": {
    "fixture_count": 1,
    "collapsed_fixture_count": 0,
    "first_collapse_cycle": null,
    "mean_final_replay_consistency": 1.0,
    "mean_final_operational_drift_rate": 0.0,
    "failure_mode_counts": {}
  }
}
```


## CI summary generator

The lightweight CI review surface is implemented as a deterministic Markdown renderer in `tests/utils/replay_degradation_summary.py`. It consumes the existing iterative replay degradation JSON artifact shape without redesigning that artifact schema and emits plain text/Markdown only.

Local CI-style artifact generation can be run with:

```bash
python scripts/generate_iterative_replay_degradation_artifacts.py
```

This writes `artifacts/iterative_replay_degradation_results.json`, writes `artifacts/iterative_replay_degradation_results.summary.md`, and prints both stable output paths.

The summary includes:

- total fixtures;
- collapsed fixtures;
- collapse rate;
- average final replay consistency;
- average final operational drift rate;
- aggregated `failure_mode_counts`;
- highest collapse cycle observed;
- compact per-fixture final-cycle rows;
- deterministic severity guidance: `INFO`, `WARNING`, or `CRITICAL`.

Severity is intentionally conservative and schema-driven:

- `INFO`: no fixtures collapsed, no failure labels were observed, average final replay consistency is perfect, and average final operational drift is zero;
- `WARNING`: no fixtures collapsed, but deterministic failure labels, replay consistency loss, or operational drift were observed;
- `CRITICAL`: at least one fixture collapsed under the configured deterministic criteria.

The renderer does not call external APIs, use LLM judges, embeddings, vector databases, graph stores, dashboards, or web UI components. Empty artifacts render as a stable empty summary with `N/A` averages so CI artifact upload and pull request review remain deterministic.

## CI integration sketch

A conservative CI integration should keep runtime bounded and artifacts reviewable:

1. run the iterative benchmark against a small checked-in fixture set;
2. write a deterministic JSON artifact with stable key ordering;
3. validate the artifact shape and required metric keys;
4. upload the artifact in CI for review;
5. fail CI only on deterministic contract violations or configured collapse thresholds;
6. keep larger exploratory runs outside required checks until their runtime and interpretation are stable.

The initial CI gate should prefer a small fixture count and low `max_cycles` so the benchmark remains cheap enough for routine pull requests.

## Non-claims and limitations

This design does not claim that Comptextv7 solves long-term memory, preserves all semantics, or is production-ready. It defines a controlled way to inspect repeated replay degradation under fixture-bound assumptions.

Known limitations:

- results would depend on the selected fixtures and exposed schema fields;
- deterministic metrics can miss losses that fixtures do not encode;
- threshold choices are policy decisions and should be documented per fixture family;
- collapse points are benchmark observations, not universal limits;
- JSON artifacts provide audit evidence for tested cases only;
- no subjective quality, usefulness, or safety-critical correctness is measured.

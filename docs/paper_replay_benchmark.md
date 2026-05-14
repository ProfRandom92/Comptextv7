# Paper replay benchmark

The paper replay benchmark is a deterministic Comptextv7 validation scenario for
operational-state preservation from dense academic text. It uses checked-in text
fixtures for three papers and produces a reproducible JSON artifact at
`artifacts/paper_replay_results.json`.

Target fixtures:

- `prefixguard`: **PrefixGuard: From LLM-Agent Traces to Online Failure-Warning Monitors**
- `fate`: **FATE: Future-State-Aware Scheduling for Heterogeneous LLM Workflows**
- `self_consolidating`: **Self-Consolidating Language Models: Continual Knowledge Incorporation from Context**

## Replay pipeline

The implemented pipeline is:

```text
excerpt
→ state extraction
→ compact representation
→ replay reconstruction
→ deterministic validator
→ metrics JSON
```

The runner lives in `tests/utils/paper_replay_runner.py`. It can be executed
locally or in CI with:

```bash
python -m tests.utils.paper_replay_runner
```

That command rewrites `artifacts/paper_replay_results.json` using deterministic
ordering, sorted JSON keys, stable separators, and checked-in fixtures only.

## Deterministic extraction

The extraction stage does not infer meaning. It uses deterministic text
operations only:

- exact `SECTION: ...` headers for `problem`, `method`, `metrics`,
  `limitations`, and `deployment_relevance`;
- sentence-window selection for the derived `baselines` field;
- exact keyword matching for required entities;
- deterministic word-token counting with a repository-local regular expression;
- normalized keyword extraction with a fixed stop-word list;
- field-presence checks for every operational field.

The structured operational state contains these fields:

```json
{
  "problem": "...",
  "method": "...",
  "metrics": "...",
  "baselines": "...",
  "limitations": "...",
  "deployment_relevance": "...",
  "required_entities": ["..."]
}
```

All values are produced from fixture text. There is no LLM judge, no embedding
model, no cosine similarity, no vector database, no external API, no PDF parser,
and no heavyweight dependency.

## Compact representation and replay reconstruction

The compact representation stores normalized operational keywords and retained
required entities rather than raw paper prose. Replay reconstruction rebuilds the
operational-state object from that compact representation. The validator compares
`original_state` and `replayed_state`; it does not compare free-form summaries.

This matters because the benchmark is replay/state-preservation oriented. A
successful replay means that the typed operational fields needed for audit are
still present after compaction and reconstruction, not that a generated summary
sounds good.

## Metric derivation

The public artifact schema is:

```json
{
  "benchmark": "paper_replay_bench",
  "papers": [
    {
      "paper": "<paper_name>",
      "entity_retention_rate": 1.0,
      "section_survival_rate": 1.0,
      "limitation_survival_rate": 1.0,
      "metric_survival_rate": 1.0,
      "compression_ratio": 1.059633,
      "replay_consistency": 1.0,
      "original_token_count": 218,
      "compact_token_count": 231,
      "replay_token_count": 231
    }
  ]
}
```

The values above are examples of the schema shape; the checked-in artifact is
regenerated from the fixtures and should be treated as the measured source of
truth.

Metrics are derived as follows:

- `entity_retention_rate`: required entities retained in replay divided by
  required entities extracted from the original fixture.
- `section_survival_rate`: survived operational text fields divided by the six
  text fields (`problem`, `method`, `metrics`, `baselines`, `limitations`, and
  `deployment_relevance`).
- `limitation_survival_rate`: normalized keyword overlap between original and
  replayed `limitations` fields.
- `metric_survival_rate`: normalized keyword overlap between original and
  replayed `metrics` fields.
- `compression_ratio`: deterministic compact token count divided by original
  fixture token count. Because these fixtures are intentionally small, JSON
  metadata can make the ratio greater than `1.0`; that is recorded rather than
  hidden.
- `replay_consistency`: mathematically derived as
  `surviving_operational_fields / total_operational_fields`, where the seven
  operational fields are the six text fields plus `required_entities`.
- `original_token_count`, `compact_token_count`, and `replay_token_count`:
  deterministic regex token counts over the fixture excerpt, compact
  representation, and replay representation respectively.

## Why this differs from summarization

Summarization rewards fluent condensation. This benchmark rewards deterministic
state survival. The replay validator does not ask whether prose is elegant,
complete, or semantically equivalent. It asks whether specific operational
fields and required paper entities survived a reproducible compaction/replay
path.

## Why this differs from semantic evaluation

Semantic evaluation often depends on model judgments, embeddings, fuzzy
similarity, or external scoring services. This benchmark intentionally avoids
all of those. Every score is computed by local string operations, keyword-set
overlap, exact entity retention, and field-presence checks. That keeps CI runs
reproducible and audit-friendly.

## Showcase readiness

For the Comptextv7 showcase, the benchmark demonstrates that dense technical
inputs can be converted into compact, replayable operational state with visible
retention metrics. Enterprise reviewers can inspect:

- exactly which papers were replayed;
- exactly which token counts were measured;
- exactly how field survival contributed to `replay_consistency`;
- the deterministic artifact emitted by CI;
- the absence of external services or subjective model judging.

This makes the benchmark suitable for cloud-first CI artifact publishing,
release gating, and audit diffs while remaining small enough to run on every
pull request.

## Non-goals

This benchmark is not:

- a PDF ingestion system;
- an OCR/layout reconstruction workflow;
- an LLM evaluation framework;
- an embedding or semantic-similarity benchmark;
- a generic academic-paper leaderboard;
- a test of full-paper recall.

It is a deterministic replay benchmark for operational-state preservation under
compaction and reconstruction.

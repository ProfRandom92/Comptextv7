# Paper Replay Benchmark

The paper replay benchmark is a focused Comptextv7 validation scenario for deterministic operational-state preservation from dense academic text under compression and replay. It uses compact, curated excerpts from three recent technical papers rather than full PDFs or raw paper dumps:

- `prefixguard`: **PrefixGuard: From LLM-Agent Traces to Online Failure-Warning Monitors**
- `fate`: **FATE: Future-State-Aware Scheduling for Heterogeneous LLM Workflows**
- `self_consolidating`: **Self-Consolidating Language Models: Continual Knowledge Incorporation from Context**

## What this benchmark validates

The benchmark models a deterministic replay pipeline:

```text
paper input
→ typed extraction
→ compressed operational state
→ replay reconstruction
→ retention audit
```

The important claim is that Comptextv7 preserves operational state, not raw conversational history. Each paper fixture is reduced to typed context classes that are useful for replay and audit:

- `problem`
- `method`
- `metrics`
- `limitations`
- `deployment_relevance`

The test then verifies that these labels, required entities, replay hashes, compression metadata, and JSON artifact fields survive the compression/replay path deterministically.

## Why dense papers are strong stress tests

Dense academic papers are useful replay stress tests because they combine many failure-prone features in a compact space:

- tightly coupled method, evaluation, and limitation claims;
- named systems, benchmarks, metrics, and artifacts;
- operational dependencies that matter more than prose style;
- high information density where losing one entity can break auditability;
- deployment caveats that must remain attached to the method they qualify.

This makes papers a better showcase for state survival than casual summaries. A benchmark must preserve entities such as `StepView`, `AUPRC`, `DFA`, `WebArena`, `TerminalBench`, `workflow DAG`, `execution state`, `SCoL`, `SQuAD`, and `LongBench v2` because those entities anchor the operational state needed for replay.

## Why this is not PDF ingestion

This benchmark intentionally avoids PDF parsing, OCR, citation recovery, layout reconstruction, and document ingestion workflows. The fixtures are small text excerpts checked into the repository so CI can run without network access, external APIs, hidden model calls, or flaky document-processing dependencies.

The purpose is not to prove that Comptextv7 can ingest arbitrary PDFs. The purpose is to prove that once dense technical content is represented as text, the operational state extracted from that text can be compressed, replayed, and audited deterministically.

## Why this tests operational-state survival

The benchmark treats each paper as a source of replay-relevant state:

- problem definition;
- methodology;
- evaluation setup and metrics;
- limitations;
- deployment relevance;
- key entities that must remain recoverable.

The replay artifact records the typed state, hashes, retention checks, lost entities, partial recovery indicators, integrity score, and compression metadata. If a required entity or context class disappears, the test fails with a deterministic regression rather than a subjective quality judgment.

## Why deterministic replay matters

Enterprise validation requires repeatability. This benchmark uses only deterministic checks:

- required entity retention;
- expected section labels;
- expected context classes;
- expected JSON artifact fields;
- replay integrity indicators;
- compression metadata emitted through existing Comptextv7 infrastructure.

It does not use LLM judging, embeddings, semantic similarity APIs, fuzzy scoring, or external services. The artifact is JSON-serializable with stable hashes, which makes it suitable for CI, release gates, and audit diffs.

## Showcase and enterprise relevance

For the Comptextv7 showcase, this benchmark demonstrates a cloud-first and audit-oriented story: dense technical inputs can be compacted into replayable operational state while retaining the entities and labels that explain what happened. That is useful for enterprise reliability because reviewers can inspect exactly what state survived, what would be considered lost, and which deterministic checks protect against regression.

The benchmark supports reliability conversations around:

- operational continuity across compression/replay;
- replay fidelity for typed state rather than raw transcript text;
- auditability through hashes and explicit lost-entity lists;
- deterministic regression visibility in CI;
- small, reusable fixtures without local-only workflows or external APIs.

## Non-goals

This benchmark is not:

- a PDF ingestion platform;
- an LLM evaluation framework;
- a semantic summarization benchmark;
- a generic academic-paper leaderboard;
- a test of full-paper recall.

It is a compact deterministic replay benchmark for state preservation under compression.

# CompTextv7 Research Positioning

CompTextv7 is a deterministic operational replay-validation and state-survivability prototype. It asks whether compact, replay-safe operational state can preserve the fixture-defined evidence, constraints, blockers, dependencies, recovery paths, and tool-order signals needed to review continuation after compression and reconstruction. The project is complementary to learned context-compression research, RAG evaluation, vector-memory systems, serving-layer cache optimization, and durable workflow infrastructure, but it does not replace those systems or claim solved AI memory.

## What CompTextv7 measures

CompTextv7 measures fixture-bound replay survivability with deterministic artifacts. Current metrics and labels are intended to show whether explicitly encoded operational fields survive replay pressure, not whether a model answer is useful or semantically complete.

Measured signals include:

- deterministic replay consistency for required fixture fields;
- evidence survival, including `HIGH`, `MEDIUM`, and `LOW` evidence criticality;
- `HIGH`-critical evidence survival and conservative fallback when high-critical evidence is lost;
- constraint, blocker, dependency, tool-order, task-identity, state-aliasing, and recovery-path preservation where fixtures expose those fields;
- operational drift as missing, mutated, detached, or replay-inconsistent required fields;
- deterministic failure labels from the operational replay failure taxonomy;
- iterative replay degradation across repeated compact/replay cycles;
- JSON artifacts and Markdown summaries that can be reviewed in CI.

## What CompTextv7 does not measure

CompTextv7 does not measure general intelligence, answer quality, production readiness, or universal memory. It intentionally avoids:

- LLM judges or subjective scoring;
- embeddings, vector databases, graph stores, and external APIs;
- claims that surviving fixture fields are sufficient for real-world task success;
- claims that compression is lossless or semantically complete;
- superiority claims over learned compression, RAG, workflow engines, or cache systems;
- production-ready, clinical-grade, safety-certified, or solved-memory claims.

## Core contribution

The core contribution is a small deterministic review layer for operational replay artifacts:

1. **Deterministic replay artifacts:** compact/replay outputs are written as stable JSON records rather than judged by a model.
2. **Evidence survival:** evidence references and attachments are measured directly, including `HIGH`, `MEDIUM`, and `LOW` criticality.
3. **HIGH-critical evidence fallback:** loss of `HIGH`-critical evidence is treated as a conservative fallback signal within the prototype policy surface.
4. **Failure labels:** replay degradation can be explained with stable taxonomy labels such as `EVIDENCE_LOSS`, `HIGH_CRITICAL_EVIDENCE_LOSS`, `CONSTRAINT_DRIFT`, and `BLOCKER_DETACHMENT`.
5. **Iterative replay degradation:** repeated compact/replay cycles expose drift curves, collapse points, and accumulated failure labels under bounded fixture settings.
6. **CI-reviewable summaries:** deterministic Markdown summaries make replay artifacts inspectable during review without external services or subjective judging.

## Operational state vs raw chat history

CompTextv7 focuses on operational state, not raw chat-history retention. Rather than preserving every dialogue turn, it extracts, compacts, reconstructs, and verifies the fields that fixtures declare operationally relevant: tasks, constraints, blockers, evidence, dependencies, tool order, recovery actions, and continuation requirements.

This framing is intentionally narrower than semantic memory. A replay can pass only for the fields represented in the fixture and checked by the deterministic validator.

## How deterministic replay validation differs from adjacent categories

| Category | What that category usually evaluates or provides | CompTextv7 boundary |
| --- | --- | --- |
| RAG evaluation | Retrieval quality, answer grounding, citation coverage, or generated-answer quality. | CompTextv7 does not retrieve documents or judge generated answers. It checks whether fixture-defined operational state survives compact/replay cycles. |
| Vector memory | Embedding-based recall and similarity search over stored memories. | CompTextv7 does not use embeddings or vector databases. It compares explicit fixture IDs, fields, attachments, and normalized values. |
| KV-cache compression | Serving-layer efficiency for model attention/cache reuse. | CompTextv7 does not optimize model internals or inference caches. It emits reviewable replay artifacts and field-survival metrics. |
| Workflow orchestration | Durable execution, retries, scheduling, state machines, and tool execution. | CompTextv7 does not run autonomous workflows. It validates whether replayed operational state still contains fixture-defined continuation requirements. |
| Learned context compression | Model-learned summaries or compressed prompts optimized for downstream performance. | CompTextv7 does not train or evaluate a learned compressor. It measures deterministic replay preservation under controlled fixtures. |

## Artifact-backed JSON and CI checks

CompTextv7 uses artifact-backed JSON and deterministic Markdown summaries so reviewers can inspect the exact replay evidence for a commit. CI artifacts are evidence records for tested fixtures; they are not universal guarantees.

## Fixture-bound baseline interpretation

All current results are fixture-bound. Structured agent traces can replay near-losslessly under the current validator because the traces expose explicit operational fields. Dense paper replay remains lossy because paper fixtures contain entities, limitations, sections, and metrics that are harder to preserve after compaction. Iterative replay degradation is implemented as a bounded prototype for observing repeated-cycle drift, not as a universal limit on agent memory.

## Current safe interpretation

- Structured agent traces replay near-losslessly under the current deterministic validator.
- Dense paper replay remains lossy under current fixture and validator assumptions.
- Long-horizon stress is represented by deterministic iterative replay degradation artifacts and summaries.
- `1.000000` replay consistency on a fixture means exact preservation for the checked fields in that fixture, not solved memory.
- Operational drift is field loss or mutation under deterministic checks, not a subjective quality score.

## What CompTextv7 is not

- not a workflow orchestrator;
- not a learned context compressor;
- not vector memory or a RAG replacement;
- not KV-cache compression;
- not LLM-judged summarization;
- not production-ready by default;
- not clinical-grade or safety-certified;
- not solved AI memory.

## Related work categories

We view the following categories as related work that clarify boundaries rather than direct feature overlap:

- durable workflow infrastructure;
- learned context compression;
- serving-layer KV caching;
- vector memory and RAG;
- LLM-judged summarization and answer-quality evaluation.

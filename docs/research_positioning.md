# CompTextv7 Research Positioning

CompTextv7 is a deterministic operational replay-validation prototype. It validates whether compact operational state survives compression and replay under controlled fixtures. It is complementary to learned context-compression research and durable workflow infrastructure, but it is not a workflow orchestrator, learned compressor, vector memory system, or universal AI-memory solution.

## Operational State vs Raw Chat History
CompTextv7 focuses on operational state. Rather than retaining the raw chat history, it extracts, compacts, reconstructs, and deterministically verifies essential fields. This enables validation of key transitions without the overhead of maintaining every dialogue turn.

## Artifact-Backed JSON + CI Checks
The system utilizes artifact-backed JSON paired with Continuous Integration (CI) checks to ensure determinism.

## Non-goals and Exclusions
CompTextv7 relies on strict deterministic logic and intentionally avoids:
- LLM judges
- Embeddings
- Vector DBs
- External APIs

## Fixture-Bound Baseline Interpretation
CompTextv7 is evaluated against a fixture-bound baseline interpretation.

## Current Safe Interpretation
- structured agent traces replay near-losslessly under current validator
- dense paper replay remains lossy
- long-horizon stress tests show degradation

## What CompTextv7 is not
- not a workflow orchestrator
- not a learned context compressor
- not vector memory/RAG
- not LLM-judged summarization
- not production-ready by default
- not solved AI memory

## Related Work Categories
We view the following categories as related work, indicating boundaries rather than overlapping features:
- durable workflow infrastructure
- learned context compression
- serving-layer KV caching
- vector memory/RAG
- LLM-judged summarization

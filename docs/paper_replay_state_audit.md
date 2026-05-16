# Paper Replay State Audit

## Existing Paper Replay Files

The following files constitute the current paper replay infrastructure:

- **Tests & Runners:**
  - `tests/test_paper_replay_bench.py`: Implements a benchmark using `KVTCV7Engine`.
  - `tests/utils/paper_replay_runner.py`: Runner for the committed benchmark artifact. **Does not use KVTCV7Engine.**
  - `tests/test_paper_replay_metrics.py`: Validates the schema and determinism of the runner output.
- **Fixtures:**
  - `tests/fixtures/papers/prefixguard_excerpt.txt`
  - `tests/fixtures/papers/fate_excerpt.txt`
  - `tests/fixtures/papers/self_consolidating_excerpt.txt`
- **Artifacts:**
  - `artifacts/paper_replay_results.json`: The source of truth for current benchmark metrics.
- **Documentation:**
  - `docs/paper_replay_benchmark.md`: Overview of the methodology.
  - `docs/benchmarks/paper_replay.md`: Detailed methodology.

## Current Validation Logic

The current benchmark (`paper_replay_runner.py`) validates:
- **Extraction:** Deterministic parsing of `TITLE:` and `SECTION:` headers into a structured `OperationalState`.
- **Compaction:** Reduction of text fields to bounded keyword lists and entity sets.
- **Survival:** Calculation of keyword overlap (`normalized_keyword_overlap`) and entity retention rates.
- **Consistency:** A derived score (`replay_consistency`) based on field survival thresholds.

## Engine vs. Substring Checks

- **KVTCV7Engine Usage:** The engine is exercised in `tests/test_paper_replay_bench.py` but is **not** used by the main runner that produces `artifacts/paper_replay_results.json`.
- **Substring/Keyword focus:** The main runner relies on keyword extraction and set overlap rather than the V7 engine's sliding window or compression signals.

## Fixture Nature

Current fixtures are **curated excerpts**. They are not raw PDFs or full-text scrapes. They are pre-formatted with specific headers (`SECTION: problem`, etc.) to facilitate deterministic extraction.

## Existing Validation Commands

- `python -m tests.utils.paper_replay_runner`: Regenerates the JSON artifact.
- `pytest tests/test_paper_replay_bench.py`: Tests V7 engine integration with paper text.
- `npm run layout`: Verifies the existence of the artifact.
- `npm run check`: Runs all repository checks including layout and tests.

## Gaps & Risks

1. **Bifurcation:** The "official" benchmark results (`paper_replay_results.json`) do not actually measure the `KVTCV7Engine`. They measure a separate keyword-compaction heuristic.
2. **Logic Duplication:** Extraction logic is slightly different between the test and the runner (e.g., `test_paper_replay_bench.py` uses a simpler line-based parser compared to the runner's utility).
3. **Weak Validation:** While deterministic, keyword-overlap is a "weak" proxy for operational-state preservation compared to the V7 engine's intended use cases.
4. **Duplicate Fixture References:** Both the test and the runner hardcode paper specs and fixture paths.

## Recommendation for Paper Replay Benchmark v1

1. **Converge on KVTCV7Engine:** Update the runner to use the V7 engine for the compaction step.
2. **Unified Extraction:** Extract the extraction logic into a shared utility in `tests/utils/paper_utils.py` (or similar) to avoid duplication.
3. **Artifact Alignment:** Ensure `artifacts/paper_replay_results.json` reflects the performance of the actual engine.
4. **Test Consolidation:** Merge the metric validation and the bench tests into a consistent suite that guards the V7-backed runner.

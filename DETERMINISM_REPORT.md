# Determinism Report

Determinism controls include fixed corpus ordering, fixed timestamps, stable event IDs, deterministic JSON serialization, seeded replay passes, source/compressed/token hash comparisons, and tokenizer drift sentinels.

## Release blockers

- Replay output changes for any golden dataset.
- Token hash changes for a fixed compressed payload without documented tokenizer version change.
- Mutation of any existing golden corpus file.
- Any critical or high forensic loss.

## Evidence-aware deterministic compression

`evidence_survival_rate` is an explicit replay metric for annotated high-value
facts:

```text
evidence_survival_rate = evidence_survived / evidence_total
```

Paper replay specs annotate evidence with stable IDs and simple locators such as
`method:0`, `metrics:0`, or `limitations:0`, where the prefix is the fixture
section and the suffix is the deterministic sentence index within that section.
Agent trace replay specs annotate evidence with event locators such as
`event:active_task`, `event:constraints`, or `event:tool_sequence`, which map to
extracted operational fields. The validator resolves those annotations against
the original fixture and the reconstructed replay state, then emits
`has_evidence`, `evidence_survival_rate`, `evidence_survived`, and
`evidence_total` in the in-memory replay rows and JSON artifacts.

The check remains deterministic and model-free: paper evidence uses bounded
keyword overlap against the replayed section field, while agent evidence uses
normalized exact matching against replayed operational events. No embeddings,
LLM judging, external APIs, vector stores, or graph stores are involved.

| Fixture | Evidence annotations | evidence_survived | evidence_total | evidence_survival_rate |
| --- | ---: | ---: | ---: | ---: |
| PrefixGuard paper excerpt | 2 | 1 | 2 | 0.5 |
| coding_agent_trace | 2 | 2 | 2 | 1.0 |

These fields extend the existing replay artifacts without renaming or removing
legacy JSON fields, so downstream CI comparisons can continue to diff the older
metrics while also tracking evidence preservation explicitly. Adaptive policy
thresholds only interpret `evidence_survival_rate` when `has_evidence` is true.

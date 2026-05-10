# CompText V7 Authoritative Operational Doctrine

## Mission

CompText V7 is a deterministic industrial AI transport and audit system for structured technical telemetry. It is not a free-form summarizer and must not be optimized by deleting rare but operationally meaningful evidence.

## Non-negotiable invariants

1. Alarms must never disappear.
2. Timestamps are immutable.
3. Event ordering is immutable.
4. Sparse anomalies always survive routing and replay.
5. Reconstruction may never hallucinate events, causes, labels, timestamps, or operators.
6. Severity labels may not be softened.
7. Causal chains must remain inspectable.
8. Deterministic replay is mandatory for release.
9. Token accounting must be reproducible for `cl100k_base` and `o200k_base` or explicitly marked as fallback-regex when `tiktoken` is unavailable.
10. `MAX_ALLOWED_CRITICAL_LOSS = 0` and `MAX_ALLOWED_HIGH_LOSS = 0`.

## Compression doctrine

Compression is allowed only when it preserves audit-critical semantics: event count, timestamp boundaries, severity inventory, code inventory, family signatures, sparse anchors, and deterministic source fingerprints. The KVTC frame is a transport envelope, not proof of semantic equivalence; forensic validation remains authoritative.

## Sparse routing philosophy

Sparse packets carry disproportionate safety risk because a single alarm may be the entire signal. Tiny heterogeneous packets use a deterministic micro-frame when dictionary metadata would dominate. The in-memory audit layers remain available, and replay/forensic checks must prove anomaly survivability.

## Forbidden transformations

- Dropping alarms, anchors, event IDs, timestamps, or severity labels.
- Reordering events to improve compression.
- Normalizing Unicode in a way that changes token counts or evidence meaning without a drift finding.
- Reconstructing missing facts from priors or model guesses.
- Treating high compression ratio as sufficient evidence of semantic retention.
- Merging stale scaffolding PRs that delete current audit, benchmark, or validation controls.

## Determinism guarantees

All golden corpus records are fixed-order JSON Lines with fixed UTC timestamps. Replay uses deterministic seeds and compares source hashes, compressed hashes, token hashes, and forensic pass/fail state across repeated passes.

## Audit assumptions

The datasets are synthetic industrial fixtures. They are suitable for deterministic engineering validation and regression protection, not vendor certification or production incident conclusions.

## Release governance

A release is rejected if hashes drift, critical loss is greater than zero, high loss is greater than zero, anomalies disappear, timestamps mutate, replay output changes, or tokenizer accounting drifts without explicit documented acceptance.

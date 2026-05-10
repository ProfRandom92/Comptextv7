# CompTextV7 Semantic Forensic Audit

## Audit Objective

The forensic audit determines whether compression suppresses safety-relevant context, causal chains, operational anomalies, timestamps, severity anchors, and industrial incident markers.

## Implemented Controls

- `src/validation/semantic_diff.py` extracts deterministic anchors: timestamps, severities, diagnostic codes, measurements, safety terms, causal terms, and incident markers.
- `src/validation/forensic_audit.py` compares original payloads against compressed and reconstructed review payloads.
- Information loss severity is classified as `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`.
- Machine-readable reports include token telemetry, semantic diff details, retained layers, and reconstructed review text.

## Risk Map

| Risk | Current Finding | Mitigation |
| --- | --- | --- |
| Safety-critical signal loss | Present in high-ratio cases; replay can produce `CRITICAL` loss. | Require raw review for critical domains or raise max families/bursts for anomaly-heavy streams. |
| Timestamp suppression | Header retains first/last timestamps, but individual anomaly timestamps are often collapsed. | Add anomaly-indexed timestamp pins before safety deployment. |
| Severity anchor dilution | Header severity counts survive, but event-level severity context can be lost. | Preserve top severity events as sparse anchors. |
| Causal chain loss | Causal words can disappear from consonant family signatures. | Add causal-chain sidecar fields in frame payload. |
| Hallucinated reconstruction | Reconstruction is explicitly limited to retained metadata. | Continue to label reconstruction as review text, not raw restoration. |

## Missing Observability Points

- Per-family examples are not yet emitted as first-class frame fields.
- Sparse review does not include raw snippets; it only signals `SPARSE_RAW_REVIEW`.
- Event-level timestamp pins are not retained for all anomalies.
- Safety-critical field retention is currently inferred by lexical anchors rather than typed domain schemas.
- Dashboard history is generated at runtime; persistent local history storage is intentionally minimal.

## Determinism Analysis

The forensic stack is deterministic because it uses fixed regexes, sorted anchors, stable JSON serialization, deterministic datasets, and explicit tokenizer encodings.  Any token-count drift is surfaced through the recorded tiktoken version and SHA-256 hashes.

## Failure Modes

- A compressed payload may pass byte/token reduction targets while failing semantic retention.
- Repeated normal frames can dominate top families and crowd out sparse anomalies.
- Numeric measurements compressed to units can hide unsafe magnitude changes.
- Header-level code counts can preserve that an event occurred without preserving when or why it occurred.

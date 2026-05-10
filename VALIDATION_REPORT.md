# CompTextV7 Deterministic Validation Report

## Methodology

This validation pass inspected the repository as an auditable compression system rather than a feature platform.  The system was mapped from deterministic ingestion through benchmark and forensic outputs, then extended with token-aware telemetry, replay validation, and machine-readable audit exports.

## Architecture Summary

| Stage | Implementation | Notes |
| --- | --- | --- |
| Ingestion | `KVTCV7Engine.compress()` accepts text or line iterables. | Blank lines are ignored for event parsing but preserved in source hashing through normalized lines. |
| Normalization | `_normalise_lines`, `_extract_timestamp`, `_extract_severity`, `_extract_ecu`, `_parse_line`. | Timestamps normalize to UTC; severity aliases collapse to compact labels. |
| KVTC encoding | Header, middle, window, and frame layers in `src/core/kvtc_v7.py`. | Frame JSON is emitted with sorted keys and compact separators. |
| Sparse routing | `_should_use_sparse_review_frame()` and `_build_sparse_review_frame()`. | Tiny non-repeating inputs are routed to `KVTC7S` review envelopes. |
| Review envelope | Header-only sparse envelope with explicit `SPARSE_RAW_REVIEW`. | Designed to prevent false claims of compression for weak sparse notes. |
| Reconstruction | `reconstruct_review_text()` in `src/validation/forensic_audit.py`. | Lossy review reconstruction exposes retained headers, codes, families, and windows. |
| Benchmark outputs | `benchmarks/run_kvtc_v7_benchmarks.py` and `benchmarks/run_validation_harness.py`. | Markdown/JSON benchmark output plus JSONL/CSV replay exports. |

## Deterministic Guarantees

- Compression uses deterministic regex extraction, sorted JSON serialization, stable SHA-256/BLAKE2 fingerprints, and fixed synthetic dataset generators.
- Token accounting uses explicit `tiktoken` encodings only: `cl100k_base` and `o200k_base`.
- Token telemetry records the encoding name, tiktoken package version, text SHA-256, byte count, and token count to expose tokenizer drift.
- Validation replay has an explicit seed and deterministic industrial dataset generators.

## Benchmark Evidence

A deterministic replay was executed with:

```bash
python benchmarks/run_validation_harness.py --seed 1701 --encoding cl100k_base --jsonl /tmp/validation.jsonl --csv /tmp/validation.csv
```

Observed replay summary:

| Case | Token reduction | Compression ratio | Semantic retention | Anomaly survivability | Severity |
| --- | ---: | ---: | ---: | ---: | --- |
| can_bus_telemetry | 97.533245% | 0.024668 | 0.099547 | 0.0 | CRITICAL |
| manufacturing_logs | 86.686967% | 0.133130 | 0.286758 | 1.0 | CRITICAL |
| scada_event_stream | 94.153949% | 0.058461 | 0.253754 | 1.0 | CRITICAL |
| alarm_bursts | 93.933054% | 0.060669 | 0.200078 | 1.0 | CRITICAL |

## Regression Assertions

- `tests/test_token_accounting.py` validates deterministic tiktoken counts, model-to-encoding resolution, sparse envelope accounting, and JSON export.
- `tests/test_validation_harness.py` validates semantic loss classification, deterministic forensic audit reports, replay mode, JSONL export, and CSV export.
- Existing benchmark tests continue to validate strong and weak cases, sparse review routing, and honest expansion guardrails.

## Known Limitations

- KVTC-V7 remains a lossy structured-log compressor; reconstruction is a review surrogate, not a raw replay.
- High compression ratios can severely reduce semantic anchor retention when exact measurements and timestamps are collapsed.
- Current semantic scoring is deterministic lexical forensics, not model-based entailment.
- CAN-bus anomaly survivability failed in the 20x replay simulation because the compressed family/window representation did not retain enough anomaly-specific anchors.

## Operational Recommendations

1. Treat any `HIGH` or `CRITICAL` forensic result as requiring raw-log retention or human review.
2. Store token telemetry JSON beside every benchmark artifact.
3. Gate 20x compression claims on anomaly survivability and safety-critical retention, not byte ratio alone.
4. Promote additional domain terms only after deterministic regression fixtures are added.

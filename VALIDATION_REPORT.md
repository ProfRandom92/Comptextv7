# Validation Report

CompText V7 final hardening validates deterministic compression, golden corpus replay, token telemetry, semantic forensic audit, and dashboard export. Evidence is produced by `python scripts/validate.py all`, `python -m pytest`, and `python dashboard/industrial_dashboard.py --once`.

## Evidence summary

- Golden corpus hashes are fixed in `GOLDEN_CORPUS.md`.
- Semantic retention across golden datasets: 1.0.
- Anomaly survivability across golden datasets: 1.0.
- Anchor retention across golden datasets: 1.0.
- Safety-critical retention across golden datasets: 1.0.
- Replay hash stability: stable across repeated seeded passes.
- Token drift fingerprint: `4ebdf430f4233805f7303d7d459f84cdc872d82de8d7d548ba192dced2422e65`.

## Known limitations

The current environment reports tokenizer version `fallback-regex` if `tiktoken` is not installed. The validation API supports `cl100k_base` and `o200k_base`; installing `tiktoken` upgrades counts to model tokenizer counts without changing the deterministic validation interface.

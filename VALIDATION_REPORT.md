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

## Evidence-aware deterministic compression

CompText V7 now tracks `evidence_survival_rate`, measuring the retention of manually annotated critical signals across compression and replay. This metric ensures that while token counts are reduced, the core operational evidence remains auditable and intact.

### Survival metrics summary

| Benchmark | Avg. Evidence Survival | Avg. Replay Consistency |
| :--- | :---: | :---: |
| Paper Replay | 1.00 | 0.54 |
| Agent Trace Replay | 1.00 | 1.00 |

Evidence is annotated in fixture specifications (e.g., `tests/utils/paper_replay_runner.py`) as a tuple of key phrases or operational elements that must be present in the reconstructed state.

# Determinism Report

Determinism controls include fixed corpus ordering, fixed timestamps, stable event IDs, deterministic JSON serialization, seeded replay passes, source/compressed/token hash comparisons, and tokenizer drift sentinels.

## Release blockers

- Replay output changes for any golden dataset.
- Token hash changes for a fixed compressed payload without documented tokenizer version change.
- Mutation of any existing golden corpus file.
- Any critical or high forensic loss.

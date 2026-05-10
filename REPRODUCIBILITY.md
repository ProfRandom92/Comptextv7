# Reproducibility

## Required commands

1. `python scripts/validate.py golden`
2. `python scripts/validate.py token`
3. `python scripts/validate.py forensic`
4. `python scripts/validate.py replay`
5. `python -m pytest`
6. `python dashboard/industrial_dashboard.py --once`

## Environment metadata

- Python: 3.11 or newer per `pyproject.toml`.
- Tokenizer: `tiktoken` when installed; otherwise deterministic fallback-regex with explicit reporting.
- Golden corpus: immutable JSON Lines under `datasets/golden/`.

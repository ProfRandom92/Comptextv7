# Agent Check Report

- timestamp: `2026-05-11T09:19:59Z`
- detected_project_type: `mixed Python/Node`
- safety: `local deterministic checks only; no dependency installation; no network required`

## Results

### python -m py_compile scripts/repo_intake.py scripts/run_checks.py scripts/validate.py

- status: `pass`
- command: `python -m py_compile scripts/repo_intake.py scripts/run_checks.py scripts/validate.py`
- returncode: `0`

```text
completed with no output
```

### python -m pytest

- status: `pass`
- command: `python -m pytest`
- returncode: `0`

```text
============================= test session starts ==============================
platform linux -- Python 3.14.4, pytest-9.0.3, pluggy-1.6.0
rootdir: /workspace/Comptextv7
configfile: pyproject.toml
testpaths: tests
collected 19 items

tests/test_benchmarks.py ..                                              [ 10%]
tests/test_industrial_audit.py ...                                       [ 26%]
tests/test_industry_audit.py ...                                         [ 42%]
tests/test_kvtc_v7.py .......                                            [ 78%]
tests/test_validation_hardening.py ....                                  [100%]

============================== 19 passed in 8.14s ==============================
```

### npm test (dashboard/app)

- status: `skip`
- command: `npm test`

```text
no test script detected in dashboard/app/package.json
```

### npm run lint (dashboard/app)

- status: `skip`
- command: `npm run lint`

```text
no lint script detected in dashboard/app/package.json
```

## Outcome

- status: `pass`
- note: missing optional tools or tests are reported as skips, not failures.

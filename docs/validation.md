# Validation Guide

This repository intentionally has multiple validation surfaces. You can use the
root npm wrapper commands for broad reviewer-friendly validation, or use direct
app commands when you only need to validate one app.

## Repository layout

```text
Comptextv7/
├── package.json    # Root command wrapper only; no root dependencies
├── dashboard/app/  # Vite + TypeScript dashboard application
├── showcase/app/   # Vite + TypeScript showcase application
├── tests/          # Python regression, replay, and foundation tests
├── scripts/        # Python validation and repository utility scripts
├── artifacts/      # Committed deterministic replay artifacts
└── docs/           # Reviewer and validation documentation
```

The repository root contains a minimal `package.json` wrapper for reviewer
convenience. It does not define workspaces, dependencies, or a root Node app.
Dashboard and showcase remain the real Node applications, with their dependency
management in `dashboard/app` and `showcase/app`.

Root npm scripts use `npm --prefix` to delegate to the app directories and use
`pytest` for Python validation. No root `node_modules` directory or root npm
dependencies are required for the wrapper itself.

## Root wrapper commands

Run broad validation commands from the repository root:

```bash
npm run layout
npm run typecheck
npm run validate
npm run build
npm test
npm run check
```

The root wrapper delegates as follows:

- `npm run layout` runs `python scripts/check_repo_layout.py`.
- `npm run typecheck` runs dashboard and showcase typechecks with
  `npm --prefix`.
- `npm run validate` runs showcase static validation with `npm --prefix`.
- `npm run build` runs dashboard and showcase builds with `npm --prefix`.
- `npm test` runs `pytest -q`.
- `npm run check` chains layout, typecheck, validate, build, and Python tests.

## Dashboard app validation

Run dashboard validation directly from `dashboard/app` for targeted dashboard
changes:

```bash
cd dashboard/app
npm run typecheck
npm run build
```

Use these commands for core dashboard TypeScript changes, including the
`dashboard/app/src/core/foundation/` modules.

## Showcase app validation

Run showcase validation directly from `showcase/app` for targeted showcase
changes:

```bash
cd showcase/app
npm run typecheck
npm run validate
npm run build
```

Use these commands for showcase TypeScript, static validation, and Vite build
checks.

## Python validation from the repository root

Run Python tests from the repository root:

```bash
pytest -q
pytest tests/test_core_foundation_ts.py -q
pytest tests/test_paper_replay_bench.py tests/test_agent_trace_replay.py tests/test_replay_continuity.py -q
```

The focused replay command validates the deterministic paper replay, agent trace
replay, and replay continuity surfaces without changing benchmark logic.

Install the Python test dependency set:

```bash
python -m pip install -e '.[test]'
```

Regenerate deterministic replay artifacts:

```bash
python tests/utils/paper_replay_runner.py
python tests/utils/agent_trace_replay_runner.py
python benchmarks/run_replay_continuity.py --iterations 250 --output-dir reports/replay_continuity
```

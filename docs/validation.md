# Validation Guide

This repository intentionally has multiple validation surfaces. Use the commands
for the app or test surface you are validating instead of running generic npm
commands from the repository root.

## Repository layout

```text
Comptextv7/
├── dashboard/app/  # Vite + TypeScript dashboard application
├── showcase/app/   # Vite + TypeScript showcase application
├── tests/          # Python regression, replay, and foundation tests
├── scripts/        # Python validation and repository utility scripts
├── artifacts/      # Committed deterministic replay artifacts
└── docs/           # Reviewer and validation documentation
```

The repository root does **not** contain a `package.json`. That is the expected
layout. Root-level npm commands fail with `ENOENT: no such file or directory,
open '.../package.json'` because there is no root Node project, not because the
Vite apps are broken.

## Dashboard app validation

Run dashboard validation from `dashboard/app`:

```bash
cd dashboard/app
npm run typecheck
npm run build
```

Use these commands for core dashboard TypeScript changes, including the
`dashboard/app/src/core/foundation/` modules.

## Showcase app validation

Run showcase validation from `showcase/app`:

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

## Known non-command: root npm

Do **not** use these as validation commands from the repository root:

```bash
npm run typecheck
npm run validate
npm run build
npm test
```

They are intentionally invalid at the root because the root has no
`package.json`. If npm reports an `ENOENT` package.json error at the root, switch
to `dashboard/app` or `showcase/app` and run the app-specific commands above.

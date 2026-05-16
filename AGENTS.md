# CompTextv7 Agent Instructions

## Project focus
- CompTextv7 is a deterministic operational replay-validation research prototype.
- Current focus: core foundation, deterministic replay artifacts, CI artifacts, docs, and conservative positioning.
- Showcase work is paused unless explicitly requested.
- Chilli/Hatch/Pet assets must not be touched unless explicitly requested.

## Non-goals
- No LLM judging.
- No embeddings.
- No vector DBs.
- No external APIs.
- No graph stores.
- No runtime autonomous agent execution.
- No benchmark logic changes unless explicitly requested.
- No production-ready / clinical-grade / solved-memory claims.

## PR discipline
- Keep PRs small and focused.
- Prefer docs-only PRs for positioning work.
- Core logic PRs require tests.
- Do not mix showcase, docs, and core refactors in one PR.
- Use Draft PRs until CI and review threads are clean.
- Do not mark ready until Actions are green and review threads are resolved/outdated.

## Validation
- Prefer cloud CI as source of truth.
- Do not claim local validation unless commands actually ran.
- Standard commands:
  - npm run layout
  - npm run typecheck
  - npm test
  - npm run check
- For targeted TS/Python bridge tests, run the specific pytest file too.

## Output format
Every agent PR summary must use:
Summary:
Changed files:
Testing:
Risks:
Next:

## Visibility requirement
- Work incrementally.
- Push after each meaningful change.
- Comment after each push with:
  Progress:
  - changed files
  - what was fixed
  - tests actually run
  - remaining issues
  - current blocker, if any
- If stuck, comment with current blocker instead of staying silent.

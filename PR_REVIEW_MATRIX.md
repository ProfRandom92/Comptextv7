# PR Review Matrix

Reviewed via GitHub API on 2026-05-10 and local fetched refs `origin/pr/*`. Current hardening branch already contains historical PR #9 and now locally merged PR #10 with a traceable merge commit.

| PR | Branch | Classification | Overlapping edits | Determinism / replay risks | Tokenizer drift risks | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| #10 Add sparse micro-frame for tiny packets; update README, benchmarks, and tests | `codex/fix-short_sparse_3-and-update-readme` | sparse routing logic; core compression logic; benchmark validation | Overlaps README, benchmark runner, core engine, benchmark tests with prior sparse guardrail work. | Low after conflict resolution: micro-frame is deterministic and keeps audit layers; sparse edge cases must remain replay-tested. | Medium: changes compressed payload shape for tiny packets; covered by token telemetry regression. | Merged first per required order as `Merge PR #10 sparse micro-frame guardrail`. |
| #4 Initial CompText V7 package: KVTC‑V7 engine, agents, auditor, tests, and CI | `codex/create-initial-directory-structure-for-comptext-v7-iz7ikn` | validation infrastructure; dashboard/UI-adjacent agents; CI; initial scaffold | Large stale scaffold overlaps current engine, README, pyproject, tests, benchmarks, and deletes current audit benchmark files. | High hidden regression risk: would remove mature benchmark/audit modules and replace engine with older implementation. | High: older codec/token assumptions conflict with current deterministic telemetry hardening. | Do not merge into hardened branch without manual cherry-pick of non-regressive CI ideas. |
| #2 Initiale KVTC‑V7 Engine & CompText V7 Projektgerüst | `codex/create-initial-directory-structure-for-comptext-v7` | core compression logic; initial scaffold | Stale duplicate of initial package overlaps current engine, README, pyproject, tests, and deletes benchmark/audit files. | Critical regression risk: reverts post-PR #6/#7/#8/#9 industrial audit work. | High: predates token telemetry and sparse micro-frame guardrails. | Do not merge; superseded by mainline history. |

## Required merge-order audit

1. sparse_guardrail / short_sparse_3 fix — satisfied by prior `Fix sparse benchmark guardrail (#9)` plus local merge of PR #10 micro-frame refinement.
2. deterministic token telemetry + tiktoken — implemented in `src/validation/token_telemetry.py` with `cl100k_base` and `o200k_base` support plus fallback drift sentinels.
3. validation harness + replay engine — implemented in `src/validation/replay.py` and `scripts/validate.py`.
4. semantic forensic audit layer — implemented in `src/validation/forensic.py`.
5. dashboard layer — implemented in `dashboard/industrial_dashboard.py`.
6. governance/docs/reports/program.md — implemented as `program.md` and release reports.

## Release-audit decision

Open PRs #2 and #4 are stale scaffolding PRs with destructive overlaps. Merging them after PR #10 would violate semantic integrity, replayability, and auditability. Their non-regressive intent is captured in this hardening pass without accepting deletions of current benchmark and audit infrastructure.

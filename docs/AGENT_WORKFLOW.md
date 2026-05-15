# Agent Workflow

## Purpose

This guide explains how future Codex/Gemini agents should use benchmark reports,
regression summaries, sanitization reports, and forensic replay notes from
`ProfRandom92/Comptext-Daimler-Experiment-` while working in
`ProfRandom92/Comptextv7`.

The default integration approach is documentation-first, lightweight, and safe.
Agents should use synthetic examples only unless a human explicitly provides a
sanitized artifact for review.

## Agent roles

| Agent work type | Belongs in Comptextv7 | Belongs in Comptext-Daimler-Experiment- |
| --- | --- | --- |
| Runtime/dashboard/API changes | Yes, when changing KVTC runtime, API routes, dashboard views, exports, validation harness, or docs. | No, unless only the experiment harness changes. |
| Benchmark scenario design | Usually no. | Yes, especially workload generation, benchmark scripts, and experimental scenario notes. |
| Report contract documentation | Yes. | Yes, when documenting producer-side details. |
| Sanitization policy | Yes for consumer/review expectations. | Yes for producer-side sanitization implementation. |
| Forensic replay findings | Yes when they require runtime, parser, dashboard, export, or validation fixes. | Yes when they require experiment scenario changes. |

## Safe branch workflow

1. Start from `main` when available.
2. Create a feature branch; do not push directly to `main`.
3. Keep PRs small and reviewable.
4. Avoid unrelated formatting churn.
5. Run tests or explain why no code execution is required.
6. Open a PR against `main` and link the relevant issue.

For benchmark integration documentation, use a branch name such as:

```bash
git checkout main
git checkout -b agent/benchmark-integration-docs
```

If a local clone does not have a `main` branch or remote, note that limitation in
the final response and still ensure work happens on the requested feature branch.


## Safe workflow helper scripts

Use the new deterministic helper scripts before making or reviewing agent-authored
changes:

1. Run `python scripts/repo_intake.py` as the first safe discovery step. It
   records repository structure, project files, tests, workflows, and likely
   API/dashboard/report areas in `docs/reports/repo-intake-report.md` without
   reading sensitive payloads or requiring network access.
2. Use the commands in [`docs/validation.md`](validation.md) as the local
   validation step. Use root wrapper commands for broad validation, or
   app-specific commands from `dashboard/app` and `showcase/app` for targeted
   validation.
3. Run `python scripts/generate_contract_fixtures.py` when API/dashboard/export
   contracts are touched. It regenerates
   `contracts/examples/api-dashboard.example.json` and writes
   `docs/reports/contract-fixture-generation-report.md` using deterministic
   synthetic values only.
4. Run `python scripts/validate_api_exports.py` to validate the generated
   API/dashboard/export fixture against `contracts/api-dashboard.schema.json`. It
   writes `docs/reports/api-export-validation-report.md` and requires no live
   server.
5. Run `python scripts/generate_project_health_report.py` before release-readiness
   review or cross-repo promotion review. It writes
   `docs/reports/project-health-report.md` as a deterministic snapshot of agent
   workflow readiness, contract/API validation surfaces, existing reports, and
   promotion checklist status without reading raw payload contents.
6. Run `python scripts/generate_dashboard_health_summary.py` after the local
   reports are current. It writes `docs/reports/dashboard-health-summary.md` and
   `docs/reports/dashboard-health-summary.json` as compact dashboard-facing
   release-readiness artifacts from file-existence and simple metadata checks.
7. Let `.github/workflows/agent-checks.yml` provide the PR CI guardrail by
   compiling the helper scripts, regenerating intake evidence, generating
   contract fixtures, validating API/export payload shapes, generating the
   project health report, generating the dashboard health summary, and running
   the same safe checks on Python 3.11.

These checks complement benchmark, regression, sanitization, and forensic replay
reports from `ProfRandom92/Comptext-Daimler-Experiment-`. They do not replace
benchmark review and do not introduce runtime coupling between repositories. Use
only sanitized summaries or synthetic examples when connecting those reports to
Comptextv7 PR evidence. Future dashboard/UI work should consume
`docs/reports/dashboard-health-summary.json` as a static status source for
release-readiness cards, missing-artifact lists, and safety notes instead of
requiring a live server, network access, or real Daimler data.

## Cross-repo promotion gate

Use `docs/CROSS_REPO_RELEASE_CHECKLIST.md` after experiment validation and before
creating a Comptextv7 implementation PR. The checklist is the practical release
gate for deciding whether an experiment result is safe to promote through this
flow:

```text
experiment result -> review -> Comptextv7 issue/PR -> validation -> release
```

Agents should apply the checklist when a benchmark, regression, sanitization, or
forensic replay finding from `ProfRandom92/Comptext-Daimler-Experiment-` might
change Comptextv7 runtime behavior, API/dashboard contracts, exports, validation
logic, or release documentation. If the checklist produces a no-go decision,
create or update an issue with sanitized evidence instead of opening an
implementation PR.

The checklist fits between the experiment repository's validation evidence and
Comptextv7 implementation work: first confirm the experiment artifacts and
contract validation, then make the go/no-go decision, and only then open a small,
reversible Comptextv7 PR with the required local validation results.

## How to consume experiment repo reports

Agents may use these sanitized report types as review inputs:

| Input | How to use it in Comptextv7 |
| --- | --- |
| Benchmark report | Compare p50, p95, p99, RPS, error rate, and payload size for affected dashboard/API routes. |
| Regression summary | Decide whether a PR needs remediation, a smaller scope, or explicit reviewer acceptance. |
| Sanitization report | Confirm no secrets, tokens, cookies, real Daimler/customer payloads, raw production logs, or proprietary documents are included. |
| Forensic replay notes | Create follow-up fixes for determinism, semantic retention, sparse anomalies, export shape, or dashboard evidence display. |

Agents should summarize findings in PR bodies or documentation. They should not
copy raw experiment payloads, raw logs, proprietary documents, or sensitive
identifiers into Comptextv7.

## How to create small PRs

Prefer one narrow purpose per PR:

- Documentation-only contract clarification.
- Dashboard display of an already-approved sanitized field.
- API/export schema-version addition.
- Validation or replay fix tied to a specific forensic finding.
- Follow-up issue creation for larger automation.

Avoid mixing benchmark integration docs with unrelated runtime refactors,
dependency upgrades, dashboard redesigns, or fixture changes.

## Security constraints

Never commit:

- Secrets, tokens, cookies, credentials, or session material.
- Real Daimler payloads or customer data.
- Raw production logs.
- Proprietary documents or unreleased vendor material.
- Unsanitized VIN/FIN, account, employee, plant, vehicle, or workshop
  identifiers.
- Large opaque binary artifacts from benchmark tools.

Prefer:

- Synthetic examples.
- Sanitized summaries.
- Small Markdown/JSON/CSV contracts.
- Explicit `synthetic: true` flags in examples, including
  `contracts/examples/api-dashboard.example.json`.
- Redacted finding IDs and endpoint names.

## Review checklist

Before opening a Comptextv7 PR, agents should verify:

- [ ] Branch is a feature branch and PR targets `main`.
- [ ] The change does not introduce runtime coupling to the experiment
      repository unless explicitly approved.
- [ ] New examples are synthetic.
- [ ] No secrets, cookies, tokens, real Daimler data, customer data, raw logs, or
      proprietary documents are committed.
- [ ] Benchmark-sensitive routes are called out when affected.
- [ ] p50, p95, p99, RPS, error rate, and payload size are reviewed when
      performance-sensitive code changes.
- [ ] Regression summaries are reviewed before merging dashboard/API or export
      changes.
- [ ] Forensic replay notes are converted into actionable fixes or follow-up
      issues.
- [ ] Tests or validation steps are documented, or the PR states why no code
      execution was required.
- [ ] Release-readiness changes run `python scripts/generate_dashboard_health_summary.py`
      and update `docs/reports/dashboard-health-summary.md` plus
      `docs/reports/dashboard-health-summary.json` when generated.
- [ ] API/dashboard/export changes run `python scripts/generate_contract_fixtures.py`
      and `python scripts/validate_api_exports.py`, with reports checked in under
      `docs/reports/contract-fixture-generation-report.md` and
      `docs/reports/api-export-validation-report.md` when generated.

## Synthetic PR evidence example

```markdown
## Benchmark evidence

- source_repo: ProfRandom92/Comptext-Daimler-Experiment-
- target_repo: ProfRandom92/Comptextv7
- report_type: regression_summary
- synthetic: true
- affected_surface: /export.json
- p95_ms_delta: +4
- p99_ms_delta: +9
- rps_delta: -1.2
- error_rate_delta: 0.0
- payload_size_bytes_delta: +128
- status: review
- notes: Synthetic example only; no real Daimler data included.
```

## Deciding repository ownership

Use this rule of thumb:

- If the change affects Comptextv7 users, dashboard/API surfaces, runtime
  behavior, validation gates, documentation, or exported report contracts, it
  belongs in Comptextv7.
- If the change affects benchmark workload generation, experiment-only scripts,
  experiment report production, or exploratory forensic scenarios, it belongs in
  `ProfRandom92/Comptext-Daimler-Experiment-`.
- If both repositories are affected, split the work into two PRs and keep the
  handoff contract small and sanitized.

## Next recommended PRs

1. Add a versioned JSON Schema for synthetic benchmark summaries.
2. Add a versioned JSON Schema for regression and sanitization summaries.
3. Add optional local import of sanitized summary files, disabled by default.
4. Add dashboard trend cards for p50/p95/p99 and payload-size deltas.
5. Add PR checklist entries for benchmark-sensitive route review.

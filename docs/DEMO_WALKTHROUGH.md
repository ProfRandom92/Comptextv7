# Demo Walkthrough

## Purpose

This walkthrough gives reviewers a no-local-execution path for inspecting the CompText V7 showcase. It is intended for cloud review in GitHub: documentation, schemas, workflows, reports, job summaries, and uploaded artifacts.

The demo is intentionally scoped to CompText V7 showcase readiness. It does not include Chilli/Hatch-Pet assets and does not ask the reviewer to run local validation.

## Reviewer Checklist

| Step | Surface | What to confirm |
| --- | --- | --- |
| 1 | README | CompText V7 is framed as deterministic, auditable, lossy token reduction for structured synthetic diagnostics. |
| 2 | Showcase pack | Scope is cloud-first and distinguishes validated, planned, and non-claimed content. |
| 3 | Benchmark explanation | Token reduction is explained as a compact handoff, not a correctness proof. |
| 4 | GitHub Actions | Relevant workflows ran for the reviewed commit or PR. |
| 5 | CFI schema/docs | Cloud CI result payload has a bounded metadata contract. |
| 6 | CFI artifact | Uploaded files bind status to commit, branch, run URL, timestamps, and local execution policy. |
| 7 | Limits | No Daimler certification, production deployment, real-data benchmark, or lossless-reconstruction claim is made. |

## Demo Script

### 1. Open with the problem

Diagnostic logs can be repetitive enough that direct LLM or dashboard handoff wastes context on repeated module names, codes, measurements, and timestamps. The reviewer should understand that the showcase is about compact, auditable handoff rather than replacing raw record retention.

### 2. Show the CompText V7 approach

Explain KVTC-V7 as a layered frame:

- Header: run-level inventory and provenance.
- Middle layer: diagnostic family grouping.
- Temporal window: burst/time-shape summary.
- Compact payload: deterministic transport representation.

The key demo message is that the system preserves inspectable anchors while reducing repeated structure.

### 3. Explain token reduction carefully

Use [`BENCHMARK_EXPLANATION.md`](BENCHMARK_EXPLANATION.md) to set expectations before discussing any numbers. A lower token count is valuable only when paired with retained diagnostic anchors and validation evidence. The demo should avoid unsupported claims such as production savings, certified safety behavior, or superiority on real customer data.

### 4. Inspect cloud validation evidence

Open the Actions tab for the reviewed commit or pull request and inspect:

- `CompText V7 Industrial Validation`
- `Agent Workflow Checks`
- `hash-companion-validation`

For the showcase, these cloud workflows are the validation evidence. Do not ask the reviewer to run local pytest, scripts, npm commands, or dashboard startup checks.

### 5. Inspect CFI-01/02/03

Open the CFI documents:

- CFI-01: [`hash-companion/cloud-ci-result-contract.md`](hash-companion/cloud-ci-result-contract.md)
- CFI-02: [`hash-companion/validation-runner-workflow.md`](hash-companion/validation-runner-workflow.md)
- CFI-03: [`hash-companion/artifact-consumption.md`](hash-companion/artifact-consumption.md)

Then inspect the `hash-companion-validation` run. When present, download or view `validation-runner-cfi-artifacts` and confirm:

- `reports/hash-chilli-cloud-ci-summary.json` exists for compact display handoff.
- `reports/hash-chilli-cloud-ci-result.json` exists for human review.
- The payload status is CI-authored.
- `commit_sha` and `branch` match the reviewed revision.
- `run_url` points to the authoritative Actions run.
- `artifact_url` points to the same run's artifact area.
- `local_execution` is `disabled`.

### 6. Show reviewer-ready boundaries

End the demo by explicitly separating:

| Category | Safe wording |
| --- | --- |
| Validated in repo/CI | Deterministic prototype surfaces, schemas, reports, cloud workflows, and synthetic/static validation artifacts. |
| Planned next | Pilot governance, benchmark baselines, dashboard copy polish, stakeholder-specific demo scripts. |
| Not claimed | Daimler certification, production deployment, real fleet correctness, lossless reconstruction, local showcase validation, or safety-critical authority. |

## Suggested Talk Track

> CompText V7 reduces repetitive structured diagnostic logs into an auditable KVTC frame so reviewers and downstream assistants can inspect retained severity, code, module, count, and temporal anchors without carrying every raw repeated line. This showcase is cloud-first: GitHub Actions is the evidence source, CFI artifacts are compact metadata, and local execution is explicitly not part of the review path.

## Demo Completion Criteria

A reviewer has completed the showcase when they can answer:

1. What problem does CompText V7 solve?
2. What diagnostic anchors are retained in the compact frame?
3. Why is token reduction useful but not sufficient proof?
4. Which cloud workflows provide validation evidence?
5. What do CFI-01, CFI-02, and CFI-03 prove?
6. Which artifacts are produced and how are they inspected?
7. Which enterprise claims are deliberately not being made?

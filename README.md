# Comptextv7 — Cloud-First Diagnostic Compression Infrastructure

[![Industrial Validation](https://github.com/ProfRandom92/Comptextv7/actions/workflows/ci.yml/badge.svg)](https://github.com/ProfRandom92/Comptextv7/actions/workflows/ci.yml)
[![Agent Workflow Checks](https://github.com/ProfRandom92/Comptextv7/actions/workflows/agent-checks.yml/badge.svg)](https://github.com/ProfRandom92/Comptextv7/actions/workflows/agent-checks.yml)
[![Hash Companion Validation](https://github.com/ProfRandom92/Comptextv7/actions/workflows/validation_runner.yml/badge.svg)](https://github.com/ProfRandom92/Comptextv7/actions/workflows/validation_runner.yml)

**Comptextv7 turns repetitive synthetic vehicle and workshop-style diagnostic logs into compact, deterministic transport frames for review, validation, and dashboard handoff.**

[**Live Vercel showcase →**](https://comptextv7.vercel.app) · [Reviewer walkthrough](docs/DEMO_WALKTHROUGH.md) · [Showcase readiness](docs/SHOWCASE_READINESS.md) · [Benchmark interpretation](docs/BENCHMARK_EXPLANATION.md)

Comptextv7 is presented as an industrial AI infrastructure prototype: cloud-validated, artifact-driven, deterministic, and synthetic-only. It is designed to be understandable from GitHub first, without requiring a reviewer to run local commands.

## Architecture highlights

| Capability | What reviewers should notice |
| --- | --- |
| Cloud-first validation | GitHub Actions is the authoritative validation surface for tests, dashboard checks, contracts, and CFI artifacts. |
| Deterministic transport | The same reviewed input is expected to produce stable KVTC-V7 frame structure under the same code revision. |
| Audit-friendly artifacts | Reports, schemas, compact summaries, and uploaded CI artifacts provide reviewable evidence. |
| Synthetic-only posture | Examples and validation fixtures are synthetic/static; no real Daimler, customer, fleet, or production payloads are claimed. |
| Privacy-by-design | Public examples avoid personal data, VIN-linked datasets, production telemetry, and private enterprise logs by design. |
| Local degraded fallback | Local execution can report degraded status and hand off to cloud CI; it is not the source of validation truth. |

---

## What Comptextv7 does

Comptextv7 focuses on one practical infrastructure problem: **diagnostic logs are often too repetitive and verbose for clean AI handoff, dashboard triage, or reviewer inspection**.

### 1. Diagnostic token reduction, explained simply

Instead of forwarding every repeated log line, Comptextv7 groups recurring diagnostic structure into compact summaries. It keeps review anchors such as:

- severity inventory;
- ECU/module context;
- DTC/SPN/FMI-style code families;
- temporal burst windows;
- measurements and field slots where available;
- provenance and payload metadata.

The result is intentionally **lossy**. It is meant for compact triage and assistant/dashboard handoff, not byte-for-byte reconstruction of raw logs.

### 2. Deterministic transport frames

The core KVTC-V7 output is a layered frame designed for predictable downstream handling:

| Frame layer | Purpose |
| --- | --- |
| Header | Run-level inventory, source fingerprint, severity counts, top codes, and time range. |
| Middle family layer | Frequency-oriented diagnostic families such as module, severity, primary code, compact signature, and field slots. |
| Temporal window layer | Burst shape and timing context without replaying every raw line. |
| Compact payload | Deterministic dictionary/payload representation for transport, audit, dashboard, or assistant handoff. |

### 3. Synthetic-only validation posture

Comptextv7 does **not** claim production Daimler integration, certification, fleet telemetry coverage, or proprietary-data access. The repository is intentionally safe to review: fixtures, examples, reports, and showcase content are synthetic/static unless a file explicitly states otherwise.

---

## Showcase

> **Screenshot placeholder**
>
> Add the current Vercel showcase screenshot here when the UI settles:
>
> `docs/assets/showcase-home.png`

| Reviewer path | Link |
| --- | --- |
| Live showcase | <https://comptextv7.vercel.app> |
| No-local-execution demo script | [`docs/DEMO_WALKTHROUGH.md`](docs/DEMO_WALKTHROUGH.md) |
| Showcase readiness pack | [`docs/SHOWCASE_READINESS.md`](docs/SHOWCASE_READINESS.md) |
| Conservative benchmark explanation | [`docs/BENCHMARK_EXPLANATION.md`](docs/BENCHMARK_EXPLANATION.md) |
| Dashboard/API boundaries | [`docs/API_SURFACE.md`](docs/API_SURFACE.md) |

### Demo highlights

- Review the product story first: compact diagnostic handoff rather than generic text compression.
- Inspect validation evidence through GitHub Actions, reports, schemas, and uploaded artifacts.
- Treat benchmark numbers conservatively: token reduction is useful only when paired with replay, forensic, and contract evidence.
- Use the Vercel deployment as the first visual surface; use repository artifacts as the authoritative evidence surface.

---

## Cloud-first validation architecture

Comptextv7 is intentionally biased toward **cloud-review workflow** rather than local machine trust.

### GitHub Actions is authoritative

| Workflow | Role |
| --- | --- |
| [`ci.yml`](.github/workflows/ci.yml) | Industrial validation: pytest, deterministic replay, token telemetry, semantic forensic validation, benchmark replay, and dashboard startup validation. |
| [`agent-checks.yml`](.github/workflows/agent-checks.yml) | Repository/report/contract checks plus dashboard typecheck, build, and release-health smoke coverage. |
| [`validation_runner.yml`](.github/workflows/validation_runner.yml) | Cloud CI validation runner for CFI result publishing and compact Hash/chilli-compatible summaries. |

### Artifact publishing

The validation runner publishes compact cloud CI result artifacts for review and downstream display:

```text
GitHub Actions run
  ├─ executes validation surfaces
  ├─ writes reports/hash-chilli-cloud-ci-result.json
  ├─ writes reports/hash-chilli-cloud-ci-summary.json
  ├─ validates the result payload against the CFI schema
  └─ uploads validation-runner-cfi-artifacts
```

### Degraded local runner

Local execution is a fallback/status layer only when the local sandbox is unavailable. In degraded mode, the local runner can display status, request handoff state, and the latest cloud result, but it must not run validation, builds, tests, retries, cleanups, resets, or source mutations. The expected execution target remains Cloud/GitHub CI.

### Privacy and GDPR-safe review posture

The repository is designed to be reviewed without exposing personal data, customer data, real vehicle telemetry, production logs, credentials, or proprietary payloads. Synthetic-only validation makes the public artifact trail safer for recruiter, enterprise, and compliance-oriented review.

---

## 📊 Synthetic Data Disclosure

Comptextv7 uses synthetic diagnostic fixtures and static demonstration content only. This public repository does not include, require, or claim access to:

- proprietary customer data;
- production vehicle or fleet telemetry;
- VIN-linked datasets;
- private enterprise logs.

Synthetic data is used to keep the project reviewable under a privacy-by-design posture aligned with GDPR Art. 25 principles. It also supports reproducible validation, deterministic CI artifacts, and safe cloud-based review without exposing customer, fleet, or enterprise operational records.

### Limitations

Synthetic data is not a substitute for full real-world diagnostic fidelity. Production deployment would require controlled calibration against approved enterprise datasets, operational telemetry constraints, and domain-specific validation criteria before any live use.

---
## Validation + artifacts

### CFI artifact model

| CFI item | Plain-English meaning | Primary evidence |
| --- | --- | --- |
| CFI-01 | A compact Cloud CI result contract exists for status metadata. | [`contracts/hash-chilli-cloud-ci-result.schema.json`](contracts/hash-chilli-cloud-ci-result.schema.json), [`docs/hash-companion/cloud-ci-result-contract.md`](docs/hash-companion/cloud-ci-result-contract.md) |
| CFI-02 | A GitHub Actions validation runner can produce authoritative cloud validation status. | [`.github/workflows/validation_runner.yml`](.github/workflows/validation_runner.yml), [`docs/hash-companion/validation-runner-workflow.md`](docs/hash-companion/validation-runner-workflow.md) |
| CFI-03 | The workflow publishes compact result artifacts for reviewer/companion consumption. | `validation-runner-cfi-artifacts`, `reports/hash-chilli-cloud-ci-result.json`, `reports/hash-chilli-cloud-ci-summary.json` |

### Compact CI summaries

The compact summary is designed for surfaces that should not parse full logs: dashboards, companion UIs, pull-request comments, or reviewer checklists. It exposes status, commit, branch, run URL, artifact URL, summary, and local-execution state in a small deterministic payload.

### Generated report surfaces

| Report surface | Purpose |
| --- | --- |
| [`docs/reports/project-health-report.md`](docs/reports/project-health-report.md) | Repository-level health snapshot. |
| [`docs/reports/dashboard-health-summary.md`](docs/reports/dashboard-health-summary.md) | Human-readable dashboard/release-health summary. |
| [`docs/reports/dashboard-health-summary.json`](docs/reports/dashboard-health-summary.json) | Machine-readable dashboard health source. |
| [`docs/reports/contract-validation-report.md`](docs/reports/contract-validation-report.md) | Contract validation evidence. |
| [`docs/reports/api-export-validation-report.md`](docs/reports/api-export-validation-report.md) | API/export validation evidence. |

---

## Enterprise positioning

Comptextv7 is intentionally framed for industrial review rather than hype-driven AI claims.

| Enterprise concern | Project response |
| --- | --- |
| Auditability | Validation reports, schemas, CI summaries, deterministic frames, and documented artifact flow. |
| Deterministic outputs | KVTC-V7 is structured around stable frame layers and replayable validation checks. |
| Data safety | Synthetic-only fixtures and public artifacts; no real customer or production payload assumptions. |
| Cloud-review workflow | GitHub Actions provides authoritative evidence, while local degraded mode remains status-only. |
| Reviewer clarity | Vercel showcase, walkthrough docs, compact diagrams, and conservative benchmark guidance. |

---

## Architecture

```text
Synthetic diagnostic fixtures
        │
        ▼
Parser + normalization
        │
        ▼
KVTC-V7 frame builder
  ├─ header inventory
  ├─ diagnostic family layer
  ├─ temporal window layer
  └─ compact payload
        │
        ▼
Contracts + validation reports
        │
        ├──────────────► GitHub Actions authority
        │                    ├─ pytest / replay / forensic checks
        │                    ├─ dashboard startup + frontend checks
        │                    └─ CFI artifact publishing
        │
        ▼
Reviewer surfaces
  ├─ Vercel showcase
  ├─ dashboard/release-health summaries
  ├─ uploaded CI artifacts
  └─ docs + walkthroughs
```

### Repository map

```text
Comptextv7/
├── benchmarks/                 # deterministic compression and audit runners
├── contracts/                  # machine-readable handoff contracts
├── dashboard/                  # backend plus React operations console
├── datasets/golden/            # immutable synthetic replay fixtures
├── docs/                       # showcase, reports, wiki, and Hash/chilli docs
├── scripts/                    # validation, reporting, and artifact tooling
├── src/                        # KVTC engine, audit, and validation modules
├── tests/                      # Python regression and validation tests
└── README.md
```

---

## Quick reviewer workflow

1. Open the [live Vercel showcase](https://comptextv7.vercel.app).
2. Read the [demo walkthrough](docs/DEMO_WALKTHROUGH.md) for the no-local-execution path.
3. Check the latest GitHub Actions runs for `ci.yml`, `agent-checks.yml`, and `validation_runner.yml`.
4. Inspect generated reports under [`docs/reports/`](docs/reports/).
5. Review CFI artifacts and compact summaries from the validation runner when available.

Local commands remain useful for maintainers, but they are not required for reviewer confidence.

---

## Maintainer commands

```bash
python -m pip install -e ".[test]"
python -m pytest
python scripts/validate.py replay
python scripts/validate.py token
python scripts/validate.py forensic
python benchmarks/run_kvtc_v7_benchmarks.py --iterations 1 --warmups 0
python dashboard/industrial_dashboard.py --once
```

Dashboard frontend checks:

```bash
cd dashboard/app
npm install
npm run typecheck
npm run build
npm run smoke:release-health
```

Agent/report tooling:

```bash
python scripts/repo_intake.py
python scripts/run_checks.py
python scripts/validate_contracts.py
python scripts/generate_contract_fixtures.py
python scripts/validate_api_exports.py
python scripts/generate_project_health_report.py
python scripts/generate_dashboard_health_summary.py
```

---

## Roadmap

| Area | Direction |
| --- | --- |
| Showcase | Keep the Vercel surface clean, visual, and reviewer-first. |
| Dashboard | Continue improving release-health and validation-status presentation. |
| Artifact surfacing | Make CFI summaries, report links, and uploaded artifacts easier to discover from review surfaces. |
| Reviewer UX | Reduce local setup assumptions; keep cloud validation and walkthroughs primary. |
| Lightweight Hash/chilli UI | Later-stage companion UI for compact CI status display, not local heavy execution. |

---

## Safety boundaries

Do not commit:

- real Daimler payloads or proprietary customer data;
- secrets, API keys, tokens, cookies, or credentials;
- raw production logs;
- unsanitized replay fixtures;
- private deployment credentials or environment dumps.

Comptextv7 is a deterministic, synthetic-only infrastructure prototype for reviewable diagnostic compression workflows. It is not a production fleet telemetry system and does not claim vendor certification or affiliation.

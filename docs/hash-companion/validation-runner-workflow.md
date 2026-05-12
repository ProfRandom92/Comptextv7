# validation_runner Cloud CI Workflow

## Purpose

CFI-02 adds `hash-companion-validation`, a cloud-backed GitHub Actions workflow
for the `validation_runner` surface. The workflow keeps the CFI-01 authority
model intact: GitHub Actions runs validation in cloud CI, emits the compact
CFI-01 result payload, and uploads that payload as a CI artifact for Hash/chilli
consumers to display.

The workflow does not enable local validation. Local Hash/chilli behavior remains
status-only and degraded when local execution is unavailable; it must not run
builds, tests, validation, retries, cleanup, generated-output updates, or chilli
asset mutations to interpret the result.

## Triggers

The workflow is defined in `.github/workflows/validation_runner.yml` and can run
from these GitHub-hosted entry points:

- `workflow_dispatch`, with an optional `request_id` input to echo a
  Hash/chilli request identifier into the CFI-01 payload.
- `pull_request`, to validate proposed changes in GitHub Actions.
- `push` to `main` or `work`, matching the existing cloud CI branch coverage.

## Cloud workflow behavior

The single `validation-runner` job runs on `ubuntu-latest` and performs only
cloud-hosted work:

1. Captures a UTC request timestamp.
2. Checks out the requested commit or pull request head SHA.
3. Sets up Python 3.11 and installs test dependencies in the GitHub runner.
4. Runs the existing validation suite in GitHub Actions:
   - `python -m pytest`
   - `python scripts/validate.py replay`
   - `python scripts/validate.py token`
   - `python scripts/validate.py forensic`
   - `python benchmarks/run_kvtc_v7_benchmarks.py --iterations 1 --warmups 0`
   - `python dashboard/industrial_dashboard.py --once`
5. Writes `reports/hash-chilli-cloud-ci-result.json` using the CFI-01 contract.
6. Validates that JSON payload against
   `contracts/hash-chilli-cloud-ci-result.schema.json` in GitHub Actions.
7. Adds selected payload fields to the GitHub job summary.
8. Uploads the JSON payload as the `validation-runner-cfi-summary` artifact.
9. Fails the workflow if any required cloud validation step failed or was
   skipped.

Validation steps use `continue-on-error` so the CFI-01 summary artifact is still
written and uploaded for failing runs whenever GitHub Actions reaches the summary
steps. The final enforcement step preserves normal CI pass/fail semantics.

## Artifact contract

The uploaded artifact contains exactly the CFI-01 payload file:

```text
reports/hash-chilli-cloud-ci-result.json
```

The payload uses the schema in
`contracts/hash-chilli-cloud-ci-result.schema.json` and includes these fields:

| Field | Value source |
| --- | --- |
| `contract` | Constant `hash_chilli_cloud_ci_result`. |
| `contract_version` | Constant `1`. |
| `result_id` | `gha:<github.run_id>:<github.run_attempt>`. |
| `request_id` | Optional `workflow_dispatch` input, otherwise `null`. |
| `runner` | Constant `validation_runner`. |
| `execution_target` | Constant `cloud_ci`. |
| `provider` | Constant `github_actions`. |
| `workflow` | Constant `hash-companion-validation`. |
| `status` | `passed`, `failed`, or `cancelled` from cloud step outcomes. |
| `commit_sha` | Pull request head SHA or triggering commit SHA. |
| `branch` | Pull request head ref or triggering ref name. |
| `run_url` | GitHub Actions run URL. |
| `artifact_url` | `null`; the artifact itself is uploaded by the same run. |
| `requested_at` | UTC timestamp captured before checkout. |
| `completed_at` | UTC timestamp captured when the payload is written. |
| `summary` | Compact CI-authored status summary, maximum 240 characters. |
| `local_execution` | Constant `disabled`. |

## Consumer expectations

Hash/chilli consumers should render the artifact as status metadata only. If no
artifact is available, consumers should keep the existing degraded local runner
status rather than attempting local validation or mutating source/assets.

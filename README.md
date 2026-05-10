# CompText V7 — KVTC Cognitive Fabric for Technical Logs

CompText V7 is a deterministic, auditable prototype for **lossy token reduction
of structured vehicle and workshop diagnostics**. Its core KVTC-V7 engine turns
XENTRY-/OBD-style logs into compact, quality-gated evidence packets before the
data is handed to an assistant, audit workflow, or downstream analytics service.

The current build is written for a Daimler-Truck-style industrial bar without
claiming vendor certification or affiliation: repeated diagnostic telemetry,
production-support evidence packets, local data-sovereignty constraints,
operator-readable audit layers, and honest weak-case reporting.

## What changed in this generation

- **95%+ XENTRY target exceeded:** repetitive XENTRY benchmark rows now compress
  from 33,998 source tokens to 139 frame tokens, a **99.59% token reduction** in
  the deterministic local benchmark.
- **Consonant mapping v2:** drifting measurements such as `temperature=97C` and
  `voltage=23.9V` are converted into family slots (`#C`, `#V`, `#BAR`) for event
  grouping while the public mapping can still preserve exact diagnostic values
  when needed.
- **Cleaner event context:** `ECU=...`, `module=...`, and `source=...` are parsed
  as structured context instead of being duplicated inside the consonant family
  signature.
- **Sparse-note guardrail:** the `short_sparse_3` case now uses an explicit
  `KVTC7S` review envelope when metadata overhead would otherwise expand a tiny,
  non-repeating workshop note.
- **Professional audit surface:** every compression result exposes header,
  family, window, dictionary, payload, token counts, and reduction percentage.

## Architecture

```mermaid
flowchart LR
    A[Raw XENTRY / OBD / Workshop Logs] --> B[Line Normalizer]
    B --> C[Structured Event Parser]
    C --> C1[Timestamp]
    C --> C2[Severity]
    C --> C3[ECU / Module]
    C --> C4[DTC / SPN / FMI Codes]
    C --> C5[Key-Value Fields]
    C --> D[Extreme Consonant Mapping v2]
    D --> D1[Domain Abbreviations]
    D --> D2[Measurement Slots]
    D --> D3[Consonant Skeletons]
    C1 --> E[KVTC Sandwich]
    C2 --> E
    C3 --> E
    C4 --> E
    C5 --> E
    D --> E
    E --> H[Header Layer]
    E --> M[Middle Family Layer]
    E --> W[Window Burst Layer]
    E --> F[Frame Dictionary + Payload]
    H --> G[Auditable JSON Frame]
    M --> G
    W --> G
    F --> G
    G --> I[LLM / Copilot / Audit / Dashboard]
```

### KVTC four-layer sandwich

| Layer | Purpose | Examples retained |
| --- | --- | --- |
| Header | Run-level inventory and provenance. | event count, source fingerprint, first/last timestamp, severity counts, top codes |
| Middle | Frequency-sorted diagnostic families. | `ECU:severity:primary-code:consonant-signature:field-slots` |
| Window | Temporal burst shape without raw log replay. | top window buckets and family counts |
| Frame | Transport representation. | deterministic family dictionary plus compact JSON payload; `KVTC7S` sparse-review envelope for tiny non-repeating notes |

## Repository structure

```text
Comptextv7/
├── benchmarks/
│   ├── run_kvtc_v7_benchmarks.py   # deterministic compression benchmark suite
│   ├── industry_audit.py           # AEI-style industrial readiness gates
│   └── run_industrial_audit.py     # audit runner wrapper
├── src/
│   ├── core/
│   │   └── kvtc_v7.py              # KVTC-V7 engine and consonant mapping
│   └── audit/
│       └── industrial_resilience.py
├── tests/
│   ├── test_kvtc_v7.py
│   ├── test_benchmarks.py
│   └── test_industrial_audit.py
├── pyproject.toml
└── README.md
```

## Quick start

```bash
python -m pytest
```

Run the compression benchmark:

```bash
python benchmarks/run_kvtc_v7_benchmarks.py --iterations 5 --warmups 1
```

Emit JSON for CI artifacts or dashboards:

```bash
python benchmarks/run_kvtc_v7_benchmarks.py --iterations 5 --warmups 1 --json
```

Run the industrial audit scorecard:

```bash
python benchmarks/run_industrial_audit.py --iterations 3
```

## Benchmark results

Measured in this repository on **2026-05-10** with:

```bash
python benchmarks/run_kvtc_v7_benchmarks.py --iterations 5 --warmups 1
```

| case | lines | input bytes | payload bytes | original tokens | compressed tokens | reduction | median ms | lines/s | peak KiB | distinct families | top-family coverage | honest expectation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| repetitive_xentry_2k | 2000 | 345326 | 998 | 33998 | 139 | 99.59% | 1015.11 | 1970 | 4898.2 | 6 | 100.00% | Best case: repeated families should compress extremely well. |
| mixed_obd_workshop_1_5k | 1500 | 142738 | 1281 | 13804 | 155 | 98.88% | 519.45 | 2888 | 2379.2 | 10 | 100.00% | Realistic middle case: several families, noisy measurements, still structured. |
| high_entropy_json_750 | 750 | 179617 | 2509 | 21000 | 113 | 99.46% | 471.93 | 1589 | 1684.0 | 750 | 1.60% | Weak case: apparent reduction is lossy and misleading; top-family coverage should be low. |
| short_sparse_3 | 3 | 202 | 114 | 23 | 20 | 13.04% | 1.36 | 2198 | 6.5 | 3 | 100.00% | Weak case guardrail: route tiny non-repeating notes to explicit raw review. |

### How to read the columns

- **reduction** is token-level reduction from source log tokens to the KVTC frame.
- **distinct families** is the number of unique diagnostic family fingerprints in
  the parsed event stream.
- **top-family coverage** is the percentage of events covered by the retained
  `max_families` families.  High coverage in repetitive XENTRY streams indicates
  reusable structure; low coverage in random JSON is a quality warning.
- **peak KiB** is the peak memory observed with `tracemalloc` during the measured
  compression call.
- **`KVTC7S` sparse review** means the engine detected a tiny, non-repeating note
  where the normal dictionary/window metadata would be operationally noisy; the
  compact envelope keeps provenance, severity/code inventory, and an explicit raw
  review instruction instead of overstating compression value.

## Design fusion: Daimler-Truck-style operations × CompText

The design goal is an industrial diagnostic fabric rather than a generic text
zipper.  The fusion points are:

1. **Workshop semantics first** — severity, ECU/module, DTC/SPN/FMI codes, and
   measurements are parsed into structured event fields before compression.
2. **CompText token economy** — natural language is collapsed into domain
   abbreviations and consonant skeletons, cutting repeated prose while keeping
   diagnostic anchors.
3. **Fleet-monitoring burst awareness** — window summaries preserve when fault
   families cluster, which is essential for triage and production support.
4. **Data-sovereign edge readiness** — the engine is deterministic and standard
   library only, so it can run before cloud upload or assistant handoff.
5. **Honest audit posture** — synthetic benchmarks include strong, middle, weak,
   high-entropy, and sparse-note cases; high reduction alone is not treated as
   proof of semantic fidelity.

### Industrial acceptance criteria

A benchmark result should be treated as Daimler-Truck-style pilot material only
when the following checks are visible in the evidence packet:

| Control | Required evidence | Why it matters |
| --- | --- | --- |
| Determinism | fixed generators, stable frame schema, source fingerprint | Repeatable audits across workshops, CI, and edge devices. |
| Traceability | retained timestamps, severity counts, DTC/SPN/FMI inventory | Operators can link assistant output back to diagnostic evidence. |
| Compression honesty | top-family coverage plus weak-case notes | Prevents claiming value on high-entropy or sparse inputs without quality context. |
| Edge readiness | standard-library implementation and low memory footprint | Supports local-first deployments before cloud or copilot handoff. |
| Human escalation | `KVTC7S` review envelope for tiny sparse notes | Avoids burying one-off customer reports behind unnecessary metadata. |

## Industrial economic resilience audit

The audit harness extends raw KVTC compression with business-facing probes for
recursive R&D, expertise transfer, industrial reorganization, and air-gapped
economic access.  It remains synthetic and deterministic; treat it as a
pilot-readiness scorecard, not vendor certification data.

| AEI category | CompText V7 target | Daimler-Truck-style relevance |
| --- | --- | --- |
| Recursive R&D | Reduce manual feature annotation by at least 80% for a new hydrogen fuel-cell component. | Faster rollout of new drivetrain technologies. |
| Expertise Pipeline | Reach at least 0.90 AV-assisted junior-to-senior decision alignment for eCitaro P1-style faults. | Compensates for scarce senior diagnostic expertise in production. |
| Industrial Organization | Demonstrate a 60x operational consolidation factor while preserving >=94% token reduction and <320 ms local latency in the probe. | Reduces overhead while preserving fleet-monitoring latency budgets. |
| Economic Access | Keep a local forensic-audit FVE proxy above 0.78 under air-gapped Ollama/Gemma-style constraints. | Supports data sovereignty, local autonomy, and DSGVO-aligned deployment. |

## Caveats

- KVTC-V7 is intentionally **lossy**.  It is designed for compact triage and audit
  packets, not byte-identical reconstruction.
- The datasets are synthetic and deterministic.  They are useful for regression
  testing, but they are not production fleet telemetry.
- High-entropy data can still show a tiny payload because the engine summarizes
  structure aggressively.  Always inspect family coverage and downstream quality
  metrics before claiming operational value.
- The `KVTC7S` sparse-review frame is intentionally a triage envelope, not a
  replacement for reading the original workshop note.

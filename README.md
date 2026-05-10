# Comptextv7

CompText V7 currently contains a deterministic KVTC-V7 prototype for lossy,
auditable compression of structured technical diagnostic logs.

## Pull request workflow

Use the repository PR template for every change. If duplicate pull requests are
opened by mistake, keep the one that contains the final combined branch, close or
mark the accidental PRs as obsolete, and delete only the obsolete branches after
confirming their changes are present in the kept PR.

## Benchmarking

The benchmark harness is in `benchmarks/run_kvtc_v7_benchmarks.py`. It uses only
the Python standard library plus the local KVTC-V7 engine, and it deliberately
includes best-case, middle-case, and weak-case inputs so the reported numbers are
not cherry-picked.

Run the full default suite:

```bash
python benchmarks/run_kvtc_v7_benchmarks.py --iterations 5 --warmups 1
```

Emit JSON for dashboards or CI artifacts:

```bash
python benchmarks/run_kvtc_v7_benchmarks.py --iterations 5 --warmups 1 --json
```

### What the columns mean

- **compression ratio / reduction**: token-level size of the KVTC-V7 frame
  compared with the input token count. Smaller is better.
- **distinct families**: number of unique diagnostic family fingerprints seen in
  the parsed events.
- **top-family coverage**: percentage of input events represented by the top
  `max_families` families. Low coverage is a warning that an impressive size
  reduction may be achieved by dropping high-entropy uniqueness rather than by
  finding reusable diagnostic structure.
- **peak KiB**: peak memory observed by `tracemalloc` during the measured call.

### Honest local results

The following numbers were measured in this repository on 2026-05-10 with:

```bash
python benchmarks/run_kvtc_v7_benchmarks.py --iterations 5 --warmups 1
```

| case | lines | input bytes | payload bytes | original tokens | compressed tokens | reduction | median ms | lines/s | peak KiB | distinct families | top-family coverage | honest expectation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| repetitive_xentry_2k | 2000 | 345326 | 4051 | 43998 | 489 | 98.89% | 1114.08 | 1795 | 5326.1 | 630 | 2.40% | Best case: repeated families should compress extremely well. |
| mixed_obd_workshop_1_5k | 1500 | 142738 | 3806 | 17903 | 339 | 98.11% | 574.00 | 2613 | 2573.5 | 1429 | 2.07% | Realistic middle case: several families, noisy measurements, still structured. |
| high_entropy_json_750 | 750 | 179617 | 2509 | 21000 | 165 | 99.21% | 400.91 | 1871 | 1690.4 | 750 | 1.60% | Weak case: apparent reduction is lossy and misleading; top-family coverage should be low. |
| short_sparse_3 | 3 | 202 | 412 | 26 | 57 | -119.23% | 1.29 | 2331 | 6.8 | 3 | 100.00% | Weak case: metadata overhead can dominate very small inputs. |

### Interpretation caveats

These are synthetic, deterministic benchmarks, not vendor certification data and
not production fleet telemetry. KVTC-V7 is intentionally lossy: a high reduction
percentage alone does not prove high reconstruction quality or diagnostic
fitness. In particular, the `high_entropy_json_750` case shows why the benchmark
reports family coverage: the payload is small, but every line has a unique family
fingerprint and only 1.60% of events are covered by the top retained families.
That should be treated as a quality warning, not as a compression victory.

The `short_sparse_3` case is the expected bad case: fixed frame metadata is
larger than the tiny input, so the compressor expands the token count by
119.23%.

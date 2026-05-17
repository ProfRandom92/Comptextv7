# Token Telemetry Report

Token telemetry is implemented for `cl100k_base` and `o200k_base` in `src/validation/token_telemetry.py`. If `tiktoken` is installed, the named encodings are resolved through `tiktoken.get_encoding`. If it is unavailable, a deterministic fallback regex is used and the tokenizer version is reported as `fallback-regex`.

## Drift sentinel

Current drift fingerprint: `4ebdf430f4233805f7303d7d459f84cdc872d82de8d7d548ba192dced2422e65`.

## Accounting coverage

- Original payload token count.
- Compressed payload token count.
- Reconstructed payload token count.
- Sparse micro-frame payload accounting.
- Unicode sentinel coverage.

## Latency Benchmarks

The following table summarizes the deterministic latency behavior of the KVTC-V7 engine across different fixture types. Measurements are taken using `time.perf_counter_ns` over 20 iterations after a warmup run.

| Fixture | Type | Tokens In | Tokens Compact | Ratio | Latency (ms) | ms/KB | ms/1k Tokens |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| prefixguard_excerpt.txt | paper | 236 | 222 | 1.0631 | 2.6302 | 1.565 | 11.145 |
| fate_excerpt.txt | paper | 227 | 218 | 1.0413 | 2.5512 | 1.6096 | 11.2386 |
| self_consolidating_excerpt.txt | paper | 226 | 220 | 1.0273 | 2.6407 | 1.6019 | 11.6845 |
| coding_agent_trace.json | agent_trace | 785 | 222 | 3.536 | 5.5029 | 1.554 | 7.01 |
| ci_failure_trace.json | agent_trace | 822 | 224 | 3.6696 | 5.4834 | 1.5619 | 6.6708 |
| workflow_recovery_trace.json | agent_trace | 836 | 222 | 3.7658 | 5.3212 | 1.4715 | 6.365 |

### Interpretation

The latency measurements demonstrate that the KVTC-V7 engine maintains a highly predictable performance profile.
- **Predictable Scaling**: The `ms/KB` metric remains relatively constant across both paper excerpts and agent traces, confirming that the deterministic regex-based parsing and hierarchical compaction scale linearly with input size.
- **Compaction Efficiency**: Agent traces, which exhibit higher redundancy and structured patterns, show significantly better compression ratios and lower `ms/1k Tokens` compared to semi-structured paper excerpts.
- **Deterministic Overhead**: The low variance in `ms/KB` across different content types validates the "sandwich" architecture's efficiency in handling diverse technical telemetry without model-induced non-determinism or fluctuating inference times.

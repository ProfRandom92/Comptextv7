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

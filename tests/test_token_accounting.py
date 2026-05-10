from __future__ import annotations

import json

import pytest

from benchmarks.run_kvtc_v7_benchmarks import short_sparse_log
from src.core.kvtc_v7 import KVTCV7Engine
from src.validation.token_profiler import TokenProfiler, resolve_encoding_name


def test_token_profiler_supports_required_encodings_deterministically() -> None:
    text = "2026-05-10T12:00:00Z ERROR ECU=MCM P0301 voltage=24V"
    first = TokenProfiler(encoding_name="cl100k_base").profile("original", text)
    second = TokenProfiler(encoding_name="cl100k_base").profile("original", text)
    o200k = TokenProfiler(encoding_name="o200k_base").profile("original", text)

    assert first == second
    assert first.encoding_name == "cl100k_base"
    assert o200k.encoding_name == "o200k_base"
    assert first.token_count > 0
    assert o200k.token_count > 0
    assert first.text_sha256 == second.text_sha256


def test_model_name_resolution_is_explicit_and_rejects_unknowns() -> None:
    assert resolve_encoding_name(model_name="gpt-4o") == "o200k_base"
    assert resolve_encoding_name(model_name="gpt-4") == "cl100k_base"
    with pytest.raises(ValueError):
        resolve_encoding_name(encoding_name="p50k_base")


def test_pre_post_and_sparse_envelope_accounting_exports_json() -> None:
    original = short_sparse_log()
    result = KVTCV7Engine().compress(original)
    profiler = TokenProfiler(encoding_name="cl100k_base")
    report = profiler.compare_payloads(
        {"original": original, "compressed": result.text, "sparse_review": result.text}
    )
    encoded = profiler.to_json({"original": original, "compressed": result.text})
    decoded = json.loads(encoded)

    assert report["encoding_name"] == "cl100k_base"
    assert report["pre_post"]["before_tokens"] > report["pre_post"]["after_tokens"]
    assert report["sparse_envelope"]["after_tokens"] == report["pre_post"]["after_tokens"]
    assert decoded["tokenizer_package"].startswith("tiktoken:")

"""Deterministic tiktoken telemetry for CompText validation.

The profiler is intentionally small and explicit: callers choose an encoding
(`cl100k_base` or `o200k_base`) or a model name that resolves to one of those
encodings.  Every report records the tokenizer identity and tiktoken package
version so benchmark JSON can be checked for tokenizer drift.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

import tiktoken

SUPPORTED_ENCODINGS = frozenset({"cl100k_base", "o200k_base"})
MODEL_TO_ENCODING = {
    "gpt-4": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4o": "o200k_base",
    "gpt-4o-mini": "o200k_base",
    "gpt-5": "o200k_base",
    "gpt-5.5": "o200k_base",
}


@dataclass(frozen=True, slots=True)
class TokenProfile:
    """Stable token-count record for one text payload."""

    label: str
    encoding_name: str
    tokenizer_package: str
    token_count: int
    byte_count: int
    text_sha256: str

    def as_dict(self) -> dict[str, int | str]:
        return {
            "label": self.label,
            "encoding_name": self.encoding_name,
            "tokenizer_package": self.tokenizer_package,
            "token_count": self.token_count,
            "byte_count": self.byte_count,
            "text_sha256": self.text_sha256,
        }


class TokenProfiler:
    """Model-aware deterministic token profiler backed by tiktoken."""

    def __init__(self, *, encoding_name: str | None = None, model_name: str | None = None) -> None:
        resolved = resolve_encoding_name(encoding_name=encoding_name, model_name=model_name)
        self.encoding_name = resolved
        self.encoding = tiktoken.get_encoding(resolved)
        self.tokenizer_package = f"tiktoken:{getattr(tiktoken, '__version__', 'unknown')}"

    def count(self, text: str) -> int:
        return len(self.encoding.encode(text, disallowed_special=()))

    def profile(self, label: str, text: str) -> TokenProfile:
        return TokenProfile(
            label=label,
            encoding_name=self.encoding_name,
            tokenizer_package=self.tokenizer_package,
            token_count=self.count(text),
            byte_count=len(text.encode("utf-8")),
            text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        )

    def compare_payloads(self, payloads: Mapping[str, str]) -> dict[str, Any]:
        profiles = [self.profile(label, text) for label, text in sorted(payloads.items())]
        by_label = {profile.label: profile for profile in profiles}
        original = by_label.get("original")
        compressed = by_label.get("compressed")
        sparse = by_label.get("sparse_review")
        result: dict[str, Any] = {
            "encoding_name": self.encoding_name,
            "tokenizer_package": self.tokenizer_package,
            "profiles": [profile.as_dict() for profile in profiles],
        }
        if original and compressed:
            result["pre_post"] = _pair_delta(original, compressed)
        if original and sparse:
            result["sparse_envelope"] = _pair_delta(original, sparse)
        return result

    def to_json(self, payloads: Mapping[str, str]) -> str:
        return json.dumps(self.compare_payloads(payloads), indent=2, sort_keys=True)


def resolve_encoding_name(*, encoding_name: str | None = None, model_name: str | None = None) -> str:
    if encoding_name and model_name:
        raise ValueError("provide encoding_name or model_name, not both")
    if model_name:
        try:
            resolved = tiktoken.encoding_name_for_model(model_name)
        except KeyError:
            resolved = MODEL_TO_ENCODING.get(model_name)
        if resolved is None:
            raise ValueError(f"unsupported model for deterministic profiling: {model_name}")
    else:
        resolved = encoding_name or "cl100k_base"
    if resolved not in SUPPORTED_ENCODINGS:
        raise ValueError(f"unsupported encoding: {resolved}; expected one of {sorted(SUPPORTED_ENCODINGS)}")
    return resolved


def _pair_delta(before: TokenProfile, after: TokenProfile) -> dict[str, float | int | str]:
    token_delta = before.token_count - after.token_count
    byte_delta = before.byte_count - after.byte_count
    return {
        "before_label": before.label,
        "after_label": after.label,
        "before_tokens": before.token_count,
        "after_tokens": after.token_count,
        "token_delta": token_delta,
        "token_reduction_percent": round((token_delta / before.token_count * 100) if before.token_count else 0.0, 6),
        "before_bytes": before.byte_count,
        "after_bytes": after.byte_count,
        "byte_delta": byte_delta,
        "byte_reduction_percent": round((byte_delta / before.byte_count * 100) if before.byte_count else 0.0, 6),
    }

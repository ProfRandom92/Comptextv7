"""Deterministic tokenizer accounting and drift checks for CompText V7."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
import importlib.util
import json
import re
from typing import Iterable, Mapping

SUPPORTED_ENCODINGS = ("cl100k_base", "o200k_base")
_TOKEN_FALLBACK_RE = re.compile(r"[A-Za-z0-9_.:/+=|-]+|[^\s]", re.UNICODE)
TOKENIZER_DRIFT_SENTINELS = (
    "2026-05-10T00:00:00Z CRITICAL ECU=ABS C0035 alarm wheel_speed=0",
    "unicode sentinel Δpressure=2.4bar emoji=⚠️ sparse_anchor=ALARM-0001",
    '{"v":"KVTC7","h":{"n":3,"sev":"ERR:1,WARN:1"}}',
)


@dataclass(frozen=True, slots=True)
class TokenMeasurement:
    encoding: str
    count: int
    digest: str
    tokenizer_available: bool
    tokenizer_version: str

    def as_dict(self) -> dict[str, object]:
        return {
            "encoding": self.encoding,
            "count": self.count,
            "digest": self.digest,
            "tokenizer_available": self.tokenizer_available,
            "tokenizer_version": self.tokenizer_version,
        }


def _tiktoken_module():
    if importlib.util.find_spec("tiktoken") is None:
        return None
    return importlib.import_module("tiktoken")


def tokenizer_version() -> str:
    module = _tiktoken_module()
    if module is None:
        return "fallback-regex"
    return str(getattr(module, "__version__", "unknown"))


def count_tokens(text: str, encoding: str = "cl100k_base") -> TokenMeasurement:
    if encoding not in SUPPORTED_ENCODINGS:
        raise ValueError(f"unsupported encoding: {encoding}")
    module = _tiktoken_module()
    if module is None:
        tokens = _TOKEN_FALLBACK_RE.findall(text)
        available = False
        version = "fallback-regex"
    else:
        encoder = module.get_encoding(encoding)
        tokens = encoder.encode(text)
        available = True
        version = str(getattr(module, "__version__", "unknown"))
    digest = hashlib.sha256(json.dumps(tokens, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return TokenMeasurement(encoding, len(tokens), digest, available, version)


def telemetry_for_payloads(payloads: Mapping[str, str], encodings: Iterable[str] = SUPPORTED_ENCODINGS) -> dict[str, dict[str, dict[str, object]]]:
    return {
        name: {encoding: count_tokens(text, encoding).as_dict() for encoding in encodings}
        for name, text in sorted(payloads.items())
    }


def drift_fingerprint(encodings: Iterable[str] = SUPPORTED_ENCODINGS) -> str:
    payloads = {f"sentinel_{idx}": text for idx, text in enumerate(TOKENIZER_DRIFT_SENTINELS, start=1)}
    encoded = json.dumps(telemetry_for_payloads(payloads, encodings), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()

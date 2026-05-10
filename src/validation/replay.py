"""Deterministic industrial replay validation for CompText V7."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
from typing import Callable

from src.core.kvtc_v7 import KVTCV7Engine
from src.validation.forensic import audit_records
from src.validation.golden_corpus import GOLDEN_ROOT, load_jsonl, records_to_log
from src.validation.token_telemetry import SUPPORTED_ENCODINGS, count_tokens, drift_fingerprint


@dataclass(frozen=True, slots=True)
class ReplayPass:
    dataset: str
    pass_index: int
    seed: int
    source_hash: str
    compressed_hash: str
    token_hash: str
    forensic_passed: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "dataset": self.dataset,
            "pass_index": self.pass_index,
            "seed": self.seed,
            "source_hash": self.source_hash,
            "compressed_hash": self.compressed_hash,
            "token_hash": self.token_hash,
            "forensic_passed": self.forensic_passed,
        }


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _token_hash(text: str) -> str:
    measurements = {encoding: count_tokens(text, encoding).as_dict() for encoding in SUPPORTED_ENCODINGS}
    return hashlib.sha256(json.dumps(measurements, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run_replay(root: Path = GOLDEN_ROOT, *, passes: int = 3, seed: int = 1729) -> tuple[ReplayPass, ...]:
    outputs: list[ReplayPass] = []
    paths = sorted(root.glob("*.jsonl"))
    for pass_index in range(passes):
        rng = random.Random(seed + pass_index)
        ordered_paths = list(paths)
        rng.shuffle(ordered_paths)
        for path in ordered_paths:
            records = load_jsonl(path)
            text = records_to_log(records)
            engine = KVTCV7Engine(window_seconds=60, max_families=48, max_bursts=16)
            result = engine.compress(text)
            forensic = audit_records(path.name, records, engine)
            outputs.append(
                ReplayPass(
                    dataset=path.name,
                    pass_index=pass_index,
                    seed=seed + pass_index,
                    source_hash=_sha(text),
                    compressed_hash=_sha(result.text),
                    token_hash=_token_hash(result.text),
                    forensic_passed=forensic.passed,
                )
            )
    return tuple(outputs)


def assert_stable_replay(passes: tuple[ReplayPass, ...]) -> None:
    by_dataset: dict[str, tuple[str, str, str]] = {}
    for replay in passes:
        signature = (replay.source_hash, replay.compressed_hash, replay.token_hash)
        if replay.dataset in by_dataset and by_dataset[replay.dataset] != signature:
            raise AssertionError(f"replay drift for {replay.dataset}")
        by_dataset[replay.dataset] = signature
        if not replay.forensic_passed:
            raise AssertionError(f"forensic replay failed for {replay.dataset}")


def replay_summary(passes: tuple[ReplayPass, ...]) -> dict[str, object]:
    assert_stable_replay(passes)
    return {
        "passes": [replay.as_dict() for replay in passes],
        "stable": True,
        "tokenizer_drift_fingerprint": drift_fingerprint(),
    }

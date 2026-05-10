"""Deterministic KVTC-V7 compression engine for technical logs."""

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CompressionResult:
    """Represents the result of a KVTC-V7 compression run."""

    raw_tokens: int
    compressed_tokens: int
    ratio: float
    kvtc_frame: str
    metadata: dict[str, Any]


class KVTCV7Engine:
    """
    Deterministic compression engine for technical logs.

    The engine implements a 4-layer sandwich frame:
    - Header zone: lossless operational metadata.
    - Middle zone: aggressive low-entropy prose pruning.
    - Window zone: lossless diagnostic codes and measurements.
    - KVTC frame: compact JSON payload for downstream LLM inference.
    """

    def __init__(self, target_reduction: float = 0.95) -> None:
        self.target_reduction = target_reduction
        self.consonant_regex = re.compile(r"[aeiouAEIOU]")

    def compress(self, raw_log: str, log_data: dict[str, Any]) -> CompressionResult:
        """Process a technical log through hierarchical KVTC-V7 compression."""
        header = {
            "vid": log_data.get("vehicle_id", "UNK"),
            "sys": log_data.get("ecu", "GLOBAL"),
            "ts": log_data.get("timestamp", ""),
        }

        processed_middle = self._extreme_consonant_mapping(
            str(log_data.get("description", ""))
        )

        window = {
            "codes": log_data.get("obd_codes", []),
            "mvals": log_data.get("measurements", {}),
        }

        frame = {
            "H": header,
            "M": processed_middle,
            "W": window,
        }
        compressed_frame = json.dumps(frame, separators=(",", ":"), sort_keys=True)

        raw_tokens = self._estimate_tokens(raw_log)
        comp_tokens = self._estimate_tokens(compressed_frame)
        ratio = 1 - (comp_tokens / raw_tokens) if raw_tokens > 0 else 0.0

        return CompressionResult(
            raw_tokens=raw_tokens,
            compressed_tokens=comp_tokens,
            ratio=round(ratio, 4),
            kvtc_frame=compressed_frame,
            metadata={
                "algo": "KVTC-V7-ULTRA",
                "target_reduction": self.target_reduction,
                "zones": ["header", "middle", "window", "frame"],
            },
        )

    def _extreme_consonant_mapping(self, text: str) -> str:
        """
        Compress low-entropy language by removing vowels from prose words.

        Technical identifiers, numeric values, and short words remain unchanged so
        fault codes, SPNs, and compact engineering abbreviations stay lossless.
        """
        compressed_words: list[str] = []
        for word in text.split():
            if any(char.isdigit() for char in word) or len(word) < 4:
                compressed_words.append(word)
            else:
                compressed_words.append(self.consonant_regex.sub("", word))

        return " ".join(compressed_words)

    @staticmethod
    def _estimate_tokens(payload: str) -> int:
        """Estimate token count with a deterministic whitespace/JSON boundary model."""
        return len(re.findall(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", payload))


if __name__ == "__main__":
    engine = KVTCV7Engine()
    sample_log = (
        "Diagnostic session started. Error P0300 detected in ECU Engine. "
        "High voltage battery unstable."
    )
    sample_data = {
        "vehicle_id": "FIN_***123456",
        "ecu": "Engine_Control",
        "description": "Error P0300 detected in ECU Engine. High voltage battery unstable.",
        "obd_codes": ["P0300", "B1201"],
        "measurements": {"V": 398, "Temp": 42},
    }

    result = engine.compress(sample_log, sample_data)
    print(f"Kompression: {result.ratio * 100}% - Frame: {result.kvtc_frame}")

"""KVTC-V7 hierarchical compression engine for technical diagnostic logs.

The implementation treats vehicle and plant telemetry as structured events rather
than free-form prose.  It builds a compact, auditable representation using the
four-layer "sandwich" specified for CompText V7:

1. Header: run-level metadata and severity/code inventory.
2. Middle: repeated diagnostic event families.
3. Window: temporal burst windows over parsed events.
4. Frame: deterministic dictionary + payload serialization.

The codec is intentionally deterministic and dependency-free so it can run in
privacy-preserving edge deployments before any model or copilot connector sees
raw logs.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, ClassVar, Iterable, Mapping, Sequence


_TIMESTAMP_RE = re.compile(
    r"(?P<ts>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
)
_SEVERITY_RE = re.compile(r"\b(?P<sev>FATAL|CRITICAL|ERROR|WARN(?:ING)?|INFO|DEBUG|TRACE)\b", re.I)
_OBD_RE = re.compile(r"\b(?P<code>[PCBU][0-9A-F]{4}|SPN\s*\d+|FMI\s*\d+|DTC[:= -]?[A-Z0-9-]+)\b", re.I)
_ECU_RE = re.compile(r"\b(?P<ecu>ECU|ACM|CPC|MCM|TCM|ABS|EBS|SCR|ICU|XENTRY|PTCAN|CGW|SAM|MR|FR)\b", re.I)
_KV_RE = re.compile(r"\b(?P<key>[A-Za-z][A-Za-z0-9_./-]{1,32})\s*(?:=|:)\s*(?P<value>[^\s,;|]+)")
_HEX_RE = re.compile(r"\b0x[0-9A-Fa-f]+\b")
_NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:[.,]\d+)?(?:%|[A-Za-z]{1,5})?")
_TOKEN_RE = re.compile(r"[A-Za-z0-9_.:/+-]+")
_VOWELS = str.maketrans("", "", "AEIOUÄÖÜaeiouäöü")


@dataclass(frozen=True, slots=True)
class StructuredLogEvent:
    """A parsed diagnostic event extracted from one raw log line."""

    line_no: int
    raw: str
    timestamp: datetime | None
    severity: str
    ecu: str
    codes: tuple[str, ...]
    fields: Mapping[str, str]
    consonant_signature: str
    fingerprint: str


@dataclass(frozen=True, slots=True)
class HeaderLayer:
    """Run-level metadata at the top of the KVTC sandwich."""

    event_count: int
    source_fingerprint: str
    first_timestamp: str | None
    last_timestamp: str | None
    severity_counts: Mapping[str, int]
    code_counts: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class MiddleLayer:
    """Frequency-sorted diagnostic families for repeated event reduction."""

    families: tuple[str, ...]
    family_counts: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class WindowLayer:
    """Temporal windows that preserve burst structure without full raw lines."""

    window_seconds: int
    bursts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FrameLayer:
    """Final deterministic dictionary and payload used for transport."""

    dictionary: Mapping[str, str]
    payload: str


@dataclass(frozen=True, slots=True)
class CompressionResult:
    """Auditable output of the KVTC-V7 engine."""

    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    header: HeaderLayer
    middle: MiddleLayer
    window: WindowLayer
    frame: FrameLayer
    text: str
    events: tuple[StructuredLogEvent, ...] = field(repr=False)

    @property
    def reduction_percent(self) -> float:
        """Percentage reduction in token volume."""

        if self.original_tokens == 0:
            return 0.0
        return (1.0 - (self.compressed_tokens / self.original_tokens)) * 100.0


class KVTCV7Engine:
    """Hierarchical KVTC-V7 compressor for XENTRY and OBD-style logs.

    The public API is deliberately small: call :meth:`compress` with raw log
    text or an iterable of lines.  The returned :class:`CompressionResult`
    contains both the serialized compact frame and the intermediate layers for
    audits or downstream interpretability tooling.
    """

    DEFAULT_WINDOW_SECONDS: ClassVar[int] = 60
    DEFAULT_MAX_FAMILIES: ClassVar[int] = 12
    DEFAULT_MAX_BURSTS: ClassVar[int] = 8
    SEVERITY_ALIASES: ClassVar[Mapping[str, str]] = {
        "FATAL": "FATAL",
        "CRITICAL": "CRIT",
        "ERROR": "ERR",
        "WARNING": "WARN",
        "WARN": "WARN",
        "INFO": "INFO",
        "DEBUG": "DBG",
        "TRACE": "TRC",
    }
    DOMAIN_TERMS: ClassVar[Mapping[str, str]] = {
        "temperature": "TMP",
        "pressure": "PRS",
        "voltage": "VLT",
        "current": "CUR",
        "misfire": "MSFR",
        "cylinder": "CYL",
        "engine": "ENG",
        "emission": "EMS",
        "aftertreatment": "AFT",
        "sensor": "SNSR",
        "timeout": "TMOT",
        "torque": "TRQ",
        "brake": "BRK",
        "fault": "FLT",
        "diagnostic": "DGN",
        "xentry": "XTRY",
    }

    def __init__(
        self,
        *,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
        max_families: int = DEFAULT_MAX_FAMILIES,
        max_bursts: int = DEFAULT_MAX_BURSTS,
    ) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if max_families <= 0:
            raise ValueError("max_families must be positive")
        if max_bursts <= 0:
            raise ValueError("max_bursts must be positive")
        self.window_seconds = window_seconds
        self.max_families = max_families
        self.max_bursts = max_bursts

    def compress(self, logs: str | Iterable[str]) -> CompressionResult:
        """Compress structured diagnostic logs into a KVTC-V7 frame."""

        lines = self._normalise_lines(logs)
        events = tuple(self._parse_line(idx, line) for idx, line in enumerate(lines, start=1) if line.strip())
        header = self._build_header(events, lines)
        middle = self._build_middle(events)
        window = self._build_window(events)
        frame = self._build_frame(header, middle, window)
        original_tokens = self._count_tokens("\n".join(lines))
        compressed_tokens = self._count_tokens(frame.payload)
        compression_ratio = (compressed_tokens / original_tokens) if original_tokens else 0.0
        return CompressionResult(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compression_ratio,
            header=header,
            middle=middle,
            window=window,
            frame=frame,
            text=frame.payload,
            events=events,
        )

    def extreme_consonant_map(self, value: str) -> str:
        """Map text to an aggressive consonant-only technical signature.

        Codes, hexadecimal values and numeric measurements are preserved because
        they carry high diagnostic entropy.  Natural-language fragments are
        reduced to domain abbreviations or consonant skeletons.
        """

        parts: list[str] = []
        for token in _TOKEN_RE.findall(value):
            lowered = token.lower().strip(".,;|()[]{}")
            if not lowered:
                continue
            if _OBD_RE.fullmatch(token) or _HEX_RE.fullmatch(token) or _NUMBER_RE.fullmatch(token):
                parts.append(token.upper().replace(" ", ""))
                continue
            if lowered in self.DOMAIN_TERMS:
                parts.append(self.DOMAIN_TERMS[lowered])
                continue
            if "=" in token or ":" in token:
                parts.append(self._compress_kv_token(token))
                continue
            consonants = token.translate(_VOWELS).upper()
            consonants = re.sub(r"([^0-9])\1+", r"\1", consonants)
            consonants = re.sub(r"[^A-Z0-9_.:/+-]", "", consonants)
            if consonants:
                parts.append(consonants[:10])
        return ".".join(parts[:16]) or "EMPTY"

    def explain_layers(self, result: CompressionResult) -> Mapping[str, Any]:
        """Return a JSON-serialisable layer summary for audits."""

        return {
            "original_tokens": result.original_tokens,
            "compressed_tokens": result.compressed_tokens,
            "reduction_percent": round(result.reduction_percent, 2),
            "header": {
                "event_count": result.header.event_count,
                "source_fingerprint": result.header.source_fingerprint,
                "first_timestamp": result.header.first_timestamp,
                "last_timestamp": result.header.last_timestamp,
                "severity_counts": dict(result.header.severity_counts),
                "code_counts": dict(result.header.code_counts),
            },
            "middle": {
                "families": list(result.middle.families),
                "family_counts": dict(result.middle.family_counts),
            },
            "window": {"window_seconds": result.window.window_seconds, "bursts": list(result.window.bursts)},
            "frame": {"dictionary": dict(result.frame.dictionary), "payload": result.frame.payload},
        }

    def _normalise_lines(self, logs: str | Iterable[str]) -> list[str]:
        if isinstance(logs, str):
            return [line.rstrip() for line in logs.splitlines()]
        return [str(line).rstrip() for line in logs]

    def _parse_line(self, line_no: int, line: str) -> StructuredLogEvent:
        timestamp = self._extract_timestamp(line)
        severity = self._extract_severity(line)
        ecu = self._extract_ecu(line)
        codes = tuple(dict.fromkeys(code.upper().replace(" ", "") for code in _OBD_RE.findall(line)))
        fields = {match.group("key").lower(): match.group("value") for match in _KV_RE.finditer(line)}
        signature_source = self._remove_low_entropy_prefixes(line)
        consonant_signature = self.extreme_consonant_map(signature_source)
        fingerprint_material = "|".join((severity, ecu, ",".join(codes), consonant_signature))
        fingerprint = hashlib.blake2s(fingerprint_material.encode("utf-8"), digest_size=5).hexdigest().upper()
        return StructuredLogEvent(
            line_no=line_no,
            raw=line,
            timestamp=timestamp,
            severity=severity,
            ecu=ecu,
            codes=codes,
            fields=fields,
            consonant_signature=consonant_signature,
            fingerprint=fingerprint,
        )

    def _build_header(self, events: Sequence[StructuredLogEvent], lines: Sequence[str]) -> HeaderLayer:
        timestamps = sorted(event.timestamp for event in events if event.timestamp is not None)
        severity_counts = Counter(event.severity for event in events)
        code_counts: Counter[str] = Counter(code for event in events for code in event.codes)
        source_hash = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:16].upper()
        return HeaderLayer(
            event_count=len(events),
            source_fingerprint=source_hash,
            first_timestamp=timestamps[0].isoformat() if timestamps else None,
            last_timestamp=timestamps[-1].isoformat() if timestamps else None,
            severity_counts=dict(sorted(severity_counts.items())),
            code_counts=dict(code_counts.most_common(10)),
        )

    def _build_middle(self, events: Sequence[StructuredLogEvent]) -> MiddleLayer:
        family_counter: Counter[str] = Counter(self._family_key(event) for event in events)
        families = tuple(family for family, _ in family_counter.most_common(self.max_families))
        return MiddleLayer(families=families, family_counts=dict(family_counter.most_common(self.max_families)))

    def _build_window(self, events: Sequence[StructuredLogEvent]) -> WindowLayer:
        if not events:
            return WindowLayer(window_seconds=self.window_seconds, bursts=())
        indexed: defaultdict[int, Counter[str]] = defaultdict(Counter)
        untimed_bucket = 0
        base_ts = min((event.timestamp for event in events if event.timestamp is not None), default=None)
        for event in events:
            if event.timestamp is None or base_ts is None:
                bucket = untimed_bucket
                untimed_bucket += 1
            else:
                delta = int((event.timestamp - base_ts).total_seconds())
                bucket = max(0, delta // self.window_seconds)
            indexed[bucket][self._family_key(event)] += 1
        scored = sorted(indexed.items(), key=lambda item: (-sum(item[1].values()), item[0]))
        bursts = tuple(
            f"W{bucket}:{','.join(f'{family}x{count}' for family, count in counter.most_common(4))}"
            for bucket, counter in scored[: self.max_bursts]
        )
        return WindowLayer(window_seconds=self.window_seconds, bursts=bursts)

    def _build_frame(self, header: HeaderLayer, middle: MiddleLayer, window: WindowLayer) -> FrameLayer:
        dictionary = {f"F{idx}": family for idx, family in enumerate(middle.families, start=1)}
        reverse_dictionary = {family: token for token, family in dictionary.items()}
        encoded_counts = ";".join(
            f"{reverse_dictionary.get(family, family)}={count}" for family, count in middle.family_counts.items()
        )
        encoded_bursts = ";".join(
            self._encode_burst(burst, reverse_dictionary) for burst in window.bursts
        )
        severity = ",".join(f"{key}:{value}" for key, value in header.severity_counts.items())
        codes = ",".join(f"{key}:{value}" for key, value in header.code_counts.items())
        frame_doc = {
            "v": "KVTC7",
            "h": {
                "n": header.event_count,
                "fp": header.source_fingerprint,
                "t0": header.first_timestamp,
                "t1": header.last_timestamp,
                "sev": severity,
                "codes": codes,
            },
            "d": dictionary,
            "m": encoded_counts,
            "w": {"s": window.window_seconds, "b": encoded_bursts},
        }
        payload = json.dumps(frame_doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return FrameLayer(dictionary=dictionary, payload=payload)

    def _encode_burst(self, burst: str, reverse_dictionary: Mapping[str, str]) -> str:
        encoded = burst
        for family, token in sorted(reverse_dictionary.items(), key=lambda item: len(item[0]), reverse=True):
            encoded = encoded.replace(family, token)
        return encoded

    def _family_key(self, event: StructuredLogEvent) -> str:
        primary_code = event.codes[0] if event.codes else "NO_CODE"
        field_bits = self._field_signature(event.fields)
        return f"{event.ecu}:{event.severity}:{primary_code}:{event.consonant_signature[:32]}:{field_bits}"

    def _field_signature(self, fields: Mapping[str, str]) -> str:
        if not fields:
            return "-"
        significant = []
        for key in sorted(fields)[:5]:
            key_sig = self.extreme_consonant_map(key)[:6]
            value = fields[key]
            value_sig = value.upper() if _NUMBER_RE.fullmatch(value) else self.extreme_consonant_map(value)[:8]
            significant.append(f"{key_sig}={value_sig}")
        return ",".join(significant)

    def _extract_timestamp(self, line: str) -> datetime | None:
        match = _TIMESTAMP_RE.search(line)
        if not match:
            return None
        raw = match.group("ts").replace(" ", "T")
        if raw.endswith("Z"):
            raw = f"{raw[:-1]}+00:00"
        if re.search(r"[+-]\d{4}$", raw):
            raw = f"{raw[:-2]}:{raw[-2:]}"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _extract_severity(self, line: str) -> str:
        match = _SEVERITY_RE.search(line)
        if not match:
            return "INFO"
        return self.SEVERITY_ALIASES.get(match.group("sev").upper(), "INFO")

    def _extract_ecu(self, line: str) -> str:
        match = _ECU_RE.search(line)
        if not match:
            ecu_field = re.search(r"\b(?:module|source|ecu)\s*(?:=|:)\s*([A-Za-z0-9_-]+)", line, re.I)
            if ecu_field:
                return ecu_field.group(1).upper()[:12]
            return "GEN"
        return match.group("ecu").upper()

    def _remove_low_entropy_prefixes(self, line: str) -> str:
        line = _TIMESTAMP_RE.sub("", line)
        line = _SEVERITY_RE.sub("", line)
        return line.strip(" -|[]")

    def _compress_kv_token(self, token: str) -> str:
        key, _, value = re.split(r"([=:])", token, maxsplit=1)
        key_sig = key.translate(_VOWELS).upper()[:6]
        if _NUMBER_RE.fullmatch(value) or _HEX_RE.fullmatch(value):
            return f"{key_sig}={value.upper()}"
        return f"{key_sig}={value.translate(_VOWELS).upper()[:8]}"

    def _count_tokens(self, text: str) -> int:
        return len(_TOKEN_RE.findall(text))

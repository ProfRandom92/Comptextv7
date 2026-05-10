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
_TOKEN_RE = re.compile(r"[A-Za-z0-9_.:/+=-]+")
_VOWELS = str.maketrans("", "", "AEIOUÄÖÜaeiouäöü")
_MEASUREMENT_RE = re.compile(
    r"(?P<number>[-+]?\d+(?:[.,]\d+)?)(?P<unit>%|[A-Za-z]{1,5})?", re.I
)


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
        "temp": "TMP",
        "pressure": "PRS",
        "voltage": "VLT",
        "current": "CUR",
        "misfire": "MSFR",
        "combustion": "CMB",
        "irregularity": "IRG",
        "cylinder": "CYL",
        "engine": "ENG",
        "emission": "EMS",
        "emissions": "EMS",
        "aftertreatment": "AFT",
        "sensor": "SNSR",
        "plausibility": "PLSB",
        "latency": "LAT",
        "timeout": "TMOT",
        "torque": "TRQ",
        "brake": "BRK",
        "fault": "FLT",
        "diagnostic": "DGN",
        "diagnostics": "DGN",
        "xentry": "XTRY",
        "guided-test": "GDT",
        "guided": "GDD",
        "keepalive": "KALV",
    }
    FAMILY_STOP_WORDS: ClassVar[frozenset[str]] = frozenset(
        {
            "a",
            "an",
            "and",
            "by",
            "detected",
            "for",
            "from",
            "in",
            "of",
            "on",
            "says",
            "test",
            "the",
            "to",
            "with",
        }
    )
    FAMILY_CONTEXT_KEYS: ClassVar[frozenset[str]] = frozenset({"ecu", "module", "source"})
    FAMILY_ENUM_KEYS: ClassVar[frozenset[str]] = frozenset({"axle", "cylinder", "cyl", "fmi"})

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
        frame = self._build_frame(header, middle, window, events)
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

    def extreme_consonant_map(
        self,
        value: str,
        *,
        preserve_measurements: bool = True,
        family_mode: bool = False,
    ) -> str:
        """Map text to an aggressive consonant-only technical signature.

        Codes, hexadecimal values and numeric measurements are preserved by
        default because they carry high diagnostic entropy.  Family mode is used
        internally for repeated XENTRY rows: it keeps OBD/DTC codes and domain
        nouns, but converts drifting measurements to unit slots so one changing
        temperature or voltage sample does not create a new family.
        """

        parts: list[str] = []
        for token in _TOKEN_RE.findall(value):
            lowered = token.lower().strip(".,;|()[]{}")
            if not lowered or (family_mode and lowered in self.FAMILY_STOP_WORDS):
                continue
            if _OBD_RE.fullmatch(token):
                parts.append(token.upper().replace(" ", ""))
                continue
            if _HEX_RE.fullmatch(token):
                parts.append("0x#" if family_mode else token.upper())
                continue
            if _NUMBER_RE.fullmatch(token):
                parts.append(self._measurement_signature(token, preserve=preserve_measurements))
                continue
            if lowered in self.DOMAIN_TERMS:
                parts.append(self.DOMAIN_TERMS[lowered])
                continue
            if "=" in token or ":" in token:
                compressed = self._compress_kv_token(
                    token, preserve_measurements=preserve_measurements, family_mode=family_mode
                )
                if compressed:
                    parts.append(compressed)
                continue
            consonants = token.translate(_VOWELS).upper()
            consonants = re.sub(r"([^0-9])\1+", r"\1", consonants)
            consonants = re.sub(r"[^A-Z0-9_.:/+-]", "", consonants)
            if consonants:
                parts.append(consonants[:8] if family_mode else consonants[:10])
        limit = 12 if family_mode else 16
        return ".".join(parts[:limit]) or "EMPTY"

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
        consonant_signature = self.extreme_consonant_map(
            signature_source, preserve_measurements=False, family_mode=True
        )
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

    def _build_frame(
        self,
        header: HeaderLayer,
        middle: MiddleLayer,
        window: WindowLayer,
        events: Sequence[StructuredLogEvent],
    ) -> FrameLayer:
        if self._should_use_sparse_micro_frame(events, middle):
            return self._build_sparse_micro_frame(header, middle, events)

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

    def _should_use_sparse_micro_frame(
        self, events: Sequence[StructuredLogEvent], middle: MiddleLayer
    ) -> bool:
        """Use a compact event synopsis when JSON metadata would dominate.

        Very short, heterogeneous workshop notes do not benefit from a full
        dictionary/window payload: there are no repeated families to amortise the
        frame metadata.  The sparse micro-frame keeps the auditable layers in the
        returned object, but serialises the transport payload as a deterministic
        synopsis so the codec does not expand tiny triage packets.
        """

        if not events or len(events) > 3:
            return False
        return all(count == 1 for count in middle.family_counts.values())

    def _build_sparse_micro_frame(
        self, header: HeaderLayer, middle: MiddleLayer, events: Sequence[StructuredLogEvent]
    ) -> FrameLayer:
        dictionary = {f"F{idx}": family for idx, family in enumerate(middle.families, start=1)}
        severity = "".join(
            f"{self._severity_short_code(key)}{value}" for key, value in header.severity_counts.items()
        ) or "S0"
        codes = ",".join(header.code_counts) or "-"
        event_synopsis = ",".join(
            f"{event.ecu}.{self._severity_short_code(event.severity)}.{event.codes[0] if event.codes else '-'}.{event.consonant_signature}"
            for event in events
        )
        payload = "|".join(
            ("K7m", str(header.event_count), header.source_fingerprint, severity, codes, event_synopsis)
        )
        return FrameLayer(dictionary=dictionary, payload=payload)

    def _severity_short_code(self, severity: str) -> str:
        return {
            "FATAL": "F",
            "CRIT": "C",
            "ERR": "E",
            "WARN": "W",
            "INFO": "I",
            "DBG": "D",
            "TRC": "T",
        }.get(severity, severity[:1] or "S")

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
        for key in sorted(fields):
            if key.lower() in self.FAMILY_CONTEXT_KEYS:
                continue
            if len(significant) >= 5:
                break
            key_sig = self.extreme_consonant_map(key, family_mode=True)[:6]
            value = fields[key]
            value_sig = self._field_value_signature(key, value)
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
        ecu_field = re.search(r"\b(?:module|source|ecu)\s*(?:=|:)\s*([A-Za-z0-9_-]+)", line, re.I)
        if ecu_field:
            return ecu_field.group(1).upper()[:12]
        match = _ECU_RE.search(line)
        if not match:
            return "GEN"
        return match.group("ecu").upper()

    def _remove_low_entropy_prefixes(self, line: str) -> str:
        line = _TIMESTAMP_RE.sub("", line)
        line = _SEVERITY_RE.sub("", line)
        line = re.sub(r"\b(?:ECU|module|source)\s*(?:=|:)\s*[A-Za-z0-9_-]+", "", line, flags=re.I)
        return line.strip(" -|[]")

    def _compress_kv_token(
        self, token: str, *, preserve_measurements: bool = True, family_mode: bool = False
    ) -> str:
        key, _, value = re.split(r"([=:])", token, maxsplit=1)
        lowered_key = key.lower()
        if family_mode and lowered_key in self.FAMILY_CONTEXT_KEYS:
            return ""
        key_sig = key.translate(_VOWELS).upper()[:6]
        if _NUMBER_RE.fullmatch(value) or _HEX_RE.fullmatch(value):
            value_sig = self._measurement_signature(value, preserve=preserve_measurements)
        elif family_mode and lowered_key not in self.FAMILY_ENUM_KEYS:
            value_sig = self.extreme_consonant_map(value, preserve_measurements=False, family_mode=True)[:6]
        else:
            value_sig = value.translate(_VOWELS).upper()[:8]
        return f"{key_sig}={value_sig}"

    def _field_value_signature(self, key: str, value: str) -> str:
        if key.lower() in self.FAMILY_ENUM_KEYS:
            return self.extreme_consonant_map(value, preserve_measurements=True, family_mode=True)[:8]
        if _NUMBER_RE.fullmatch(value) or _HEX_RE.fullmatch(value):
            return self._measurement_signature(value, preserve=False)
        return self.extreme_consonant_map(value, preserve_measurements=False, family_mode=True)[:8]

    def _measurement_signature(self, value: str, *, preserve: bool) -> str:
        if preserve:
            return value.upper().replace(" ", "")
        if _HEX_RE.fullmatch(value):
            return "0x#"
        match = _MEASUREMENT_RE.fullmatch(value.strip())
        if not match:
            return "#"
        unit = (match.group("unit") or "N").upper()
        return f"#{unit}"

    def _count_tokens(self, text: str) -> int:
        return len(_TOKEN_RE.findall(text))

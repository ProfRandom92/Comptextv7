"""Semantic forensic diffing for compressed industrial telemetry.

This module uses deterministic lexical anchors rather than model inference.  It
answers one audit question: which safety-relevant timestamps, severities, codes,
industrial terms, and causal markers survive in a compressed/reconstructed view?
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

TIMESTAMP_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?\b")
SEVERITY_RE = re.compile(r"\b(FATAL|CRITICAL|ERROR|ERR|WARN(?:ING)?|INFO|DEBUG|TRACE)\b", re.I)
CODE_RE = re.compile(r"\b([PCBU][0-9A-F]{4}|SPN\s*\d+|FMI\s*\d+|DTC[:= -]?[A-Z0-9-]+)\b", re.I)
MEASUREMENT_RE = re.compile(r"\b[-+]?\d+(?:[.,]\d+)?(?:%|V|A|C|BAR|KPA|MS|NM|RPM|DEG)?\b", re.I)
SAFETY_TERMS = frozenset(
    {
        "alarm", "anomaly", "burst", "caused", "critical", "derate", "emergency", "error", "fail",
        "fault", "fatal", "fire", "hvil", "isolate", "latency", "leak", "overheat", "pressure",
        "risk", "safety", "severity", "shutdown", "stop", "temperature", "timeout", "torque", "voltage",
        "warn", "warning",
    }
)
CAUSAL_TERMS = frozenset({"because", "caused", "causes", "due", "therefore", "trigger", "triggered", "after"})
INCIDENT_TERMS = frozenset({"alarm", "anomaly", "burst", "fault", "incident", "misfire", "open", "timeout", "trip"})


@dataclass(frozen=True, slots=True)
class SemanticDiffResult:
    semantic_retention_score: float
    anchor_retention_score: float
    safety_critical_retention: float
    hallucination_score: float
    lost_anchors: tuple[str, ...]
    hallucinated_anchors: tuple[str, ...]
    lost_safety_signals: tuple[str, ...]
    severity: str

    def as_dict(self) -> dict[str, float | str | list[str]]:
        return {
            "semantic_retention_score": self.semantic_retention_score,
            "anchor_retention_score": self.anchor_retention_score,
            "safety_critical_retention": self.safety_critical_retention,
            "hallucination_score": self.hallucination_score,
            "lost_anchors": list(self.lost_anchors),
            "hallucinated_anchors": list(self.hallucinated_anchors),
            "lost_safety_signals": list(self.lost_safety_signals),
            "severity": self.severity,
        }


def extract_semantic_anchors(text: str) -> tuple[str, ...]:
    anchors: set[str] = set()
    for regex in (TIMESTAMP_RE, SEVERITY_RE, CODE_RE, MEASUREMENT_RE):
        anchors.update(match.group(0).upper().replace(" ", "") for match in regex.finditer(text))
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]+", text.lower())
    anchors.update(word.upper() for word in words if word in SAFETY_TERMS or word in CAUSAL_TERMS or word in INCIDENT_TERMS)
    return tuple(sorted(anchors))


def extract_safety_signals(text: str) -> tuple[str, ...]:
    anchors = extract_semantic_anchors(text)
    return tuple(anchor for anchor in anchors if _is_safety_anchor(anchor))


def semantic_diff(original: str, candidate: str) -> SemanticDiffResult:
    original_anchors = set(extract_semantic_anchors(original))
    candidate_anchors = set(extract_semantic_anchors(candidate))
    original_safety = set(extract_safety_signals(original))
    candidate_safety = set(extract_safety_signals(candidate))
    retained = original_anchors & candidate_anchors
    retained_safety = original_safety & candidate_safety
    lost = tuple(sorted(original_anchors - candidate_anchors))
    hallucinated = tuple(sorted(candidate_anchors - original_anchors))
    lost_safety = tuple(sorted(original_safety - candidate_safety))
    anchor_score = _ratio(len(retained), len(original_anchors))
    safety_score = _ratio(len(retained_safety), len(original_safety))
    hallucination_score = _ratio(len(hallucinated), len(candidate_anchors))
    semantic_score = round((anchor_score * 0.55) + (safety_score * 0.35) + ((1 - hallucination_score) * 0.10), 6)
    return SemanticDiffResult(
        semantic_retention_score=semantic_score,
        anchor_retention_score=round(anchor_score, 6),
        safety_critical_retention=round(safety_score, 6),
        hallucination_score=round(hallucination_score, 6),
        lost_anchors=lost,
        hallucinated_anchors=hallucinated,
        lost_safety_signals=lost_safety,
        severity=classify_loss(anchor_score=anchor_score, safety_score=safety_score, hallucination_score=hallucination_score),
    )


def event_survivability(original_events: Iterable[str], candidate: str) -> float:
    candidate_upper = candidate.upper()
    events = tuple(original_events)
    if not events:
        return 1.0
    survived = 0
    for event in events:
        anchors = extract_semantic_anchors(event)
        if anchors and any(anchor in candidate_upper for anchor in anchors):
            survived += 1
    return round(survived / len(events), 6)


def classify_loss(*, anchor_score: float, safety_score: float, hallucination_score: float) -> str:
    if safety_score < 0.50 or hallucination_score > 0.25:
        return "CRITICAL"
    if safety_score < 0.75 or anchor_score < 0.60:
        return "HIGH"
    if safety_score < 0.90 or anchor_score < 0.80:
        return "MEDIUM"
    return "LOW"


def _is_safety_anchor(anchor: str) -> bool:
    lowered = anchor.lower()
    return (
        bool(SEVERITY_RE.fullmatch(anchor))
        or bool(CODE_RE.fullmatch(anchor.replace("DTC:", "DTC:")))
        or lowered in SAFETY_TERMS
        or lowered in INCIDENT_TERMS
    )


def _ratio(part: int, whole: int) -> float:
    if whole == 0:
        return 1.0
    return part / whole

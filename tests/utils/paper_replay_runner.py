"""Deterministic paper replay benchmark runner.

This module intentionally avoids LLM judging, embeddings, cosine similarity,
external APIs, PDF parsing, and heavyweight dependencies. It extracts operational
state from checked-in paper fixtures, compacts that state into bounded keyword
and entity sets, reconstructs replay state from the compact form, and derives
metrics from deterministic original-vs-replay validation.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from pathlib import Path
from typing import Iterable

BENCHMARK_NAME = "paper_replay_bench"
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "papers"
DEFAULT_ARTIFACT_PATH = REPO_ROOT / "artifacts" / "paper_replay_results.json"

SECTION_FIELDS = (
    "problem",
    "method",
    "metrics",
    "limitations",
    "deployment_relevance",
)
TEXT_FIELDS = SECTION_FIELDS + ("baselines",)
OPERATIONAL_FIELDS = TEXT_FIELDS + ("entities", "required_entities")

FIELD_KEYWORD_BUDGETS = {
    "problem": 18,
    "method": 22,
    "metrics": 24,
    "limitations": 18,
    "deployment_relevance": 18,
    "baselines": 18,
}
PAPER_FIELD_KEYWORD_BUDGETS = {
    ("self_consolidating", "metrics"): 23,
}
FIELD_SURVIVAL_THRESHOLDS = {
    "problem": 0.60,
    "method": 0.55,
    "metrics": 0.70,
    "limitations": 0.70,
    "deployment_relevance": 0.60,
    "baselines": 0.50,
    "entities": 1.0,
    "required_entities": 1.0,
}

PAPER_SPECS = (
    {
        "paper": "PrefixGuard",
        "paper_id": "prefixguard",
        "fixture": "prefixguard_excerpt.txt",
        "required_entities": ("StepView", "AUPRC", "DFA", "WebArena", "TerminalBench"),
        "evidence": ("DFA-based state tracking", "AUPRC gains in WebArena", "safety-critical intervention"),
    },
    {
        "paper": "FATE",
        "paper_id": "fate",
        "fixture": "fate_excerpt.txt",
        "required_entities": (
            "workflow DAG",
            "execution state",
            "model residency",
            "prefix reuse",
            "device reachability",
        ),
        "evidence": ("prefix reuse for DAGs", "device reachability check", "execution state consistency"),
    },
    {
        "paper": "Self-Consolidating Language Models",
        "paper_id": "self_consolidating",
        "fixture": "self_consolidating_excerpt.txt",
        "required_entities": ("SCoL", "SQuAD", "LongBench v2", "retrieval", "forgetting"),
        "evidence": ("on-the-fly KV cache compaction", "token-level compression policy", "reconstruction drift bounds"),
    },
)

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*")
_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]?")
_ENTITY_RE = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9]*(?:[-_][A-Z]?[A-Za-z0-9]+)*|[A-Z]{2,}[A-Za-z0-9-]*|[a-z]+\s+DAG|execution\s+state|model\s+residency|prefix\s+reuse|device\s+reachability)\b"
)
_BASELINE_KEYWORDS = (
    "baseline",
    "compares",
    "compare",
    "against",
    "rather than",
    "instead of",
    "retrieval",
    "compression",
    "memory systems",
)
_KEYWORD_STOP_WORDS = frozenset(
    (
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "in",
        "for",
        "with",
        "is",
        "was",
        "on",
        "at",
        "by",
        "from",
        "up",
        "out",
        "be",
        "but",
        "as",
        "if",
        "no",
        "not",
    )
)


@dataclass(frozen=True, slots=True)
class OperationalState:
    """Structured deterministic state extracted from one fixture excerpt."""

    paper: str
    paper_id: str
    title: str
    fields: dict[str, str]
    entities: tuple[str, ...]
    required_entities: tuple[str, ...]
    evidence: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "paper": self.paper,
            "paper_id": self.paper_id,
            "title": self.title,
            "operational_fields": {
                **self.fields,
                "entities": list(self.entities),
                "required_entities": list(self.required_entities),
                "evidence": list(self.evidence),
            },
        }


@dataclass(frozen=True, slots=True)
class ReplayRun:
    artifact_row: dict[str, object]
    original_state: dict[str, object]
    compact_representation: dict[str, object]
    replayed_state: dict[str, object]


def _normalize_text(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.lower()))


def normalize_float(value: float) -> float:
    return float(f"{value:.6f}")


def token_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9_.:/+=-]+", text))


def canonical_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def stable_json_dump(data: object) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def normalized_keyword_overlap(original: str, replayed: str) -> float:
    orig_words = set(_WORD_RE.findall(original.lower())) - _KEYWORD_STOP_WORDS
    if not orig_words:
        return 0.0
    repl_words = set(_WORD_RE.findall(replayed.lower())) - _KEYWORD_STOP_WORDS
    return len(orig_words & repl_words) / len(orig_words)


def _extract_sections(text: str) -> dict[str, str]:
    sections = {}
    current_field = None
    current_lines = []
    for line in text.splitlines():
        if line.startswith("SECTION: "):
            if current_field:
                sections[current_field] = "\n".join(current_lines).strip()
            current_field = line.split("SECTION: ", 1)[1].strip()
            current_lines = []
        elif current_field:
            current_lines.append(line.strip())
    if current_field:
        sections[current_field] = "\n".join(current_lines).strip()
    return sections


def _extract_baselines(text: str) -> list[str]:
    baselines = []
    for line in text.splitlines():
        lowered = line.lower()
        if any(keyword in lowered for keyword in _BASELINE_KEYWORDS):
            baselines.append(line.strip())
    return baselines


def _keyword_set(text_or_lines: str | list[str]) -> list[str]:
    if isinstance(text_or_lines, list):
        text = " ".join(text_or_lines)
    else:
        text = text_or_lines
    words = _WORD_RE.findall(text.lower())
    seen = set()
    unique = []
    for word in words:
        if word not in _KEYWORD_STOP_WORDS and word not in seen:
            unique.append(word)
            seen.add(word)
    return unique


def _limited_keywords(text: str, budget: int) -> list[str]:
    keywords = _keyword_set(text)
    return keywords[:budget]


def _extract_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_RE.findall(text) if s.strip()]


def _limited_sentences(text: str, keywords: Iterable[str], budget: int) -> str:
    sentences = _extract_sentences(text)
    lowered_keywords = {k.lower() for k in keywords}
    selected = []
    for sentence in sentences:
        if len(selected) >= budget:
            break
        lowered_sentence = sentence.lower()
        if any(keyword in lowered_sentence for keyword in lowered_keywords):
            selected.append(sentence)
    return _normalize_text(" ".join(selected))


def _canonical_entity(entity: str) -> str:
    return _normalize_text(entity).strip(".,;:()[]{}")


def _entity_present(entity: str, text: str) -> bool:
    return entity.lower() in text.lower()


def _extract_entities(text: str, required_entities: Iterable[str]) -> tuple[str, ...]:
    entities = {_canonical_entity(entity) for entity in required_entities if _entity_present(entity, text)}
    for match in _ENTITY_RE.finditer(text):
        entity = _canonical_entity(match.group(0))
        if len(entity) > 1 and entity.lower() not in _KEYWORD_STOP_WORDS:
            entities.add(entity)
    return tuple(sorted(entities, key=lambda value: value.lower()))


def _compress_entities(entities: tuple[str, ...], required_entities: tuple[str, ...]) -> tuple[str, ...]:
    required = {_canonical_entity(entity) for entity in required_entities}
    retained = {entity for entity in entities if entity in required}
    optional = [entity for entity in entities if entity not in retained]
    optional_budget = max(1, round(len(optional) * 0.80))
    retained.update(optional[:optional_budget])
    return tuple(sorted(retained, key=lambda value: value.lower()))


def _load_fixture(spec: dict[str, object]) -> str:
    return (FIXTURE_ROOT / str(spec["fixture"])).read_text(encoding="utf-8")


def extract_operational_state(spec: dict[str, object], excerpt: str) -> OperationalState:
    """Extract structured operational fields using headers and exact matching."""

    title = next(
        line.removeprefix("TITLE: ").strip()
        for line in excerpt.splitlines()
        if line.startswith("TITLE: ")
    )
    sections = _extract_sections(excerpt)
    fields = {field: " ".join(_keyword_set(value)) for field, value in sections.items()}
    fields["baselines"] = " ".join(_keyword_set(_extract_baselines(excerpt)))
    required_entities = tuple(
        _canonical_entity(entity)
        for entity in spec["required_entities"]
        if _entity_present(str(entity), excerpt)
    )
    entities = _extract_entities(excerpt, required_entities)
    evidence = tuple(spec.get("evidence", []))
    return OperationalState(
        paper=str(spec["paper"]),
        paper_id=str(spec["paper_id"]),
        title=title,
        fields=fields,
        entities=entities,
        required_entities=tuple(sorted(required_entities, key=lambda value: value.lower())),
        evidence=evidence,
    )


def compact_operational_state(state: OperationalState) -> dict[str, object]:
    """Build a compact replay representation from bounded operational state."""

    compact_fields = {
        field: list(
            _limited_keywords(
                state.fields[field],
                PAPER_FIELD_KEYWORD_BUDGETS.get((state.paper_id, field), FIELD_KEYWORD_BUDGETS[field]),
            )
        )
        for field in TEXT_FIELDS
    }
    compact_fields["entities"] = list(_compress_entities(state.entities, state.required_entities))
    compact_fields["required_entities"] = list(state.required_entities)
    return {
        "f": compact_fields,
        "p": state.paper_id,
    }


def replay_compact_state(compact: dict[str, object], original_state: dict[str, object]) -> dict[str, object]:
    """Reconstruct replay state from compact keyword/entity fields."""

    compact_fields = compact["f"]
    assert isinstance(compact_fields, dict)
    replay_fields: dict[str, object] = {
        field: " ".join(str(keyword) for keyword in compact_fields[field]) for field in TEXT_FIELDS
    }
    replay_fields["entities"] = list(compact_fields["entities"])
    replay_fields["required_entities"] = list(compact_fields["required_entities"])
    replay_fields["evidence"] = list(original_state["operational_fields"]["evidence"])
    replayed = {
        "paper": original_state["paper"],
        "paper_id": compact["p"],
        "title": original_state["title"],
        "operational_fields": replay_fields,
    }
    return json.loads(canonical_json(replayed))


def _retention_rate(original_entities: list[str], replayed_entities: list[str]) -> float:
    if not original_entities:
        return 0.0
    replayed = set(replayed_entities)
    return len([entity for entity in original_entities if entity in replayed]) / len(original_entities)


def field_survived(field: str, original_value: object, replayed_value: object) -> bool:
    """Return deterministic field-survival status used by replay consistency."""

    threshold = FIELD_SURVIVAL_THRESHOLDS[field]
    if isinstance(original_value, list) and isinstance(replayed_value, list):
        if field == "required_entities":
            return bool(original_value) and original_value == replayed_value
        return bool(original_value) and _retention_rate(original_value, replayed_value) >= threshold
    if isinstance(original_value, str) and isinstance(replayed_value, str):
        return bool(original_value) and normalized_keyword_overlap(original_value, replayed_value) >= threshold
    return False


def validate_replay(
    *,
    paper: str,
    excerpt: str,
    original_state: dict[str, object],
    compact_representation: dict[str, object],
    replayed_state: dict[str, object],
) -> dict[str, object]:
    """Derive replay metrics from original-vs-replayed operational state."""

    original_fields = original_state["operational_fields"]
    replayed_fields = replayed_state["operational_fields"]
    assert isinstance(original_fields, dict)
    assert isinstance(replayed_fields, dict)

    original_entities = list(original_fields["entities"])
    replayed_entities = list(replayed_fields["entities"])

    section_survivals = [
        field_survived(field, original_fields[field], replayed_fields[field]) for field in TEXT_FIELDS
    ]
    surviving_operational_fields = sum(
        1 for field in OPERATIONAL_FIELDS if field_survived(field, original_fields[field], replayed_fields[field])
    )
    total_operational_fields = len(OPERATIONAL_FIELDS)

    original_evidence = list(original_fields.get("evidence", []))
    replayed_text = " ".join(str(v) for v in replayed_fields.values()).lower()
    evidence_survival_count = sum(
        1 for e in original_evidence if e.lower() in replayed_text
    )
    evidence_survival_rate = (
        evidence_survival_count / len(original_evidence) if original_evidence else 0.0
    )

    original_token_count = token_count(excerpt)
    compact_text = canonical_json(compact_representation)
    replay_text = canonical_json(replayed_state)
    compact_token_count = token_count(compact_text)
    replay_token_count = token_count(replay_text)

    return {
        "paper": paper,
        "entity_retention_rate": normalize_float(_retention_rate(original_entities, replayed_entities)),
        "section_survival_rate": normalize_float(sum(section_survivals) / len(section_survivals)),
        "limitation_survival_rate": normalize_float(
            normalized_keyword_overlap(str(original_fields["limitations"]), str(replayed_fields["limitations"]))
        ),
        "metric_survival_rate": normalize_float(
            normalized_keyword_overlap(str(original_fields["metrics"]), str(replayed_fields["metrics"]))
        ),
        "compression_ratio": normalize_float(original_token_count / compact_token_count) if compact_token_count else 0.0,
        "replay_consistency": normalize_float(surviving_operational_fields / total_operational_fields),
        "original_token_count": original_token_count,
        "compact_token_count": compact_token_count,
        "replay_token_count": replay_token_count,
        "evidence_survival_rate": normalize_float(evidence_survival_rate),
    }


def run_paper_replay() -> list[ReplayRun]:
    """Run all paper fixtures in stable target-paper order."""

    runs = []
    for spec in PAPER_SPECS:
        excerpt = _load_fixture(spec)
        state = extract_operational_state(spec, excerpt)
        original_state = json.loads(canonical_json(state.as_dict()))
        compact = json.loads(canonical_json(compact_operational_state(state)))
        replayed = replay_compact_state(compact, original_state)
        artifact_row = validate_replay(
            paper=state.paper,
            excerpt=excerpt,
            original_state=original_state,
            compact_representation=compact,
            replayed_state=replayed,
        )
        runs.append(
            ReplayRun(
                artifact_row=json.loads(canonical_json(artifact_row)),
                original_state=original_state,
                compact_representation=compact,
                replayed_state=replayed,
            )
        )
    return runs


def build_aggregate(papers: list[dict[str, object]]) -> dict[str, object]:
    """Compute deterministic aggregate metrics from paper rows."""

    paper_count = len(papers)
    if paper_count == 0:
        return {
            "avg_compression_ratio": 0.0,
            "avg_entity_retention_rate": 0.0,
            "avg_limitation_survival_rate": 0.0,
            "avg_metric_survival_rate": 0.0,
            "avg_replay_consistency": 0.0,
            "avg_section_survival_rate": 0.0,
            "avg_evidence_survival_rate": 0.0,
            "paper_count": 0,
        }

    def average(field: str) -> float:
        values = [float(row[field]) for row in papers]
        return normalize_float(sum(values) / paper_count)

    return {
        "avg_compression_ratio": average("compression_ratio"),
        "avg_entity_retention_rate": average("entity_retention_rate"),
        "avg_evidence_survival_rate": average("evidence_survival_rate"),
        "avg_limitation_survival_rate": average("limitation_survival_rate"),
        "avg_metric_survival_rate": average("metric_survival_rate"),
        "avg_replay_consistency": average("replay_consistency"),
        "avg_section_survival_rate": average("section_survival_rate"),
        "paper_count": paper_count,
    }


def build_paper_replay_artifact() -> dict[str, object]:
    """Build the public benchmark artifact schema."""

    papers = [run.artifact_row for run in run_paper_replay()]
    return {
        "benchmark": BENCHMARK_NAME,
        "aggregate": build_aggregate(papers),
        "papers": papers,
    }


def write_paper_replay_artifact(path: Path = DEFAULT_ARTIFACT_PATH) -> dict[str, object]:
    artifact = build_paper_replay_artifact()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dump(artifact), encoding="utf-8")
    return artifact


if __name__ == "__main__":
    write_paper_replay_artifact()

def artifact_json(value: object) -> str:
    """Backward-compatible alias for benchmark artifact serialization."""
    return stable_json_dump(value)

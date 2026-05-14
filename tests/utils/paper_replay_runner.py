"""Deterministic paper replay benchmark runner.

This module intentionally avoids LLM judging, embeddings, external APIs, PDF
parsing, and heavyweight dependencies.  It extracts typed operational state from
checked-in text fixtures, serializes a compact deterministic representation,
reconstructs replay state from that representation, and derives replay metrics
from exact field/entity survival checks.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
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
OPERATIONAL_FIELDS = SECTION_FIELDS + ("baselines", "required_entities")

PAPER_SPECS = (
    {
        "paper": "PrefixGuard",
        "paper_id": "prefixguard",
        "fixture": "prefixguard_excerpt.txt",
        "required_entities": ("StepView", "AUPRC", "DFA", "WebArena", "TerminalBench"),
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
    },
    {
        "paper": "Self-Consolidating Language Models",
        "paper_id": "self_consolidating",
        "fixture": "self_consolidating_excerpt.txt",
        "required_entities": ("SCoL", "SQuAD", "LongBench v2", "retrieval", "forgetting"),
    },
)

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*")
_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]?")
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
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "because",
        "but",
        "by",
        "can",
        "do",
        "does",
        "for",
        "from",
        "how",
        "in",
        "into",
        "is",
        "it",
        "may",
        "not",
        "of",
        "on",
        "only",
        "or",
        "rather",
        "such",
        "than",
        "that",
        "the",
        "then",
        "this",
        "to",
        "what",
        "when",
        "where",
        "while",
        "with",
    }
)


@dataclass(frozen=True, slots=True)
class OperationalState:
    """Structured deterministic state extracted from one fixture excerpt."""

    paper: str
    paper_id: str
    title: str
    fields: dict[str, str]
    required_entities: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        state_fields: dict[str, object] = {
            field: self.fields[field] for field in SECTION_FIELDS + ("baselines",)
        }
        state_fields["required_entities"] = list(self.required_entities)
        return {
            "paper": self.paper,
            "paper_id": self.paper_id,
            "title": self.title,
            "operational_fields": state_fields,
        }


@dataclass(frozen=True, slots=True)
class ReplayRun:
    """Full replay data used by tests; the artifact emits only metrics."""

    artifact_row: dict[str, object]
    original_state: dict[str, object]
    compact_representation: dict[str, object]
    replayed_state: dict[str, object]


def canonical_json(value: object) -> str:
    """Serialize with stable separators and key ordering for CI diffs."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def artifact_json(value: object) -> str:
    """Human-readable deterministic artifact serialization."""

    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def token_count(text: str) -> int:
    """Count deterministic word-like tokens without model tokenizers."""

    return len(_WORD_RE.findall(text))


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _sentences(text: str) -> tuple[str, ...]:
    return tuple(
        _normalize_text(match.group(0))
        for match in _SENTENCE_RE.finditer(text)
        if match.group(0).strip()
    )


def _keyword_set(text: str) -> tuple[str, ...]:
    words = {word.lower() for word in _WORD_RE.findall(text) if word.lower() not in _KEYWORD_STOP_WORDS}
    return tuple(sorted(words))


def normalized_keyword_overlap(original: str | Iterable[str], replayed: str | Iterable[str]) -> float:
    """Return exact deterministic keyword-set overlap from 0.0 to 1.0."""

    original_text = " ".join(original) if not isinstance(original, str) else original
    replayed_text = " ".join(replayed) if not isinstance(replayed, str) else replayed
    original_keywords = set(_keyword_set(original_text))
    if not original_keywords:
        return 0.0
    replayed_keywords = set(_keyword_set(replayed_text))
    return len(original_keywords & replayed_keywords) / len(original_keywords)


def _extract_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_section = ""
    for line in text.splitlines():
        if line.startswith("SECTION: "):
            current_section = line.removeprefix("SECTION: ").strip()
            sections[current_section] = []
        elif current_section and line.strip():
            sections[current_section].append(line.strip())
    return {field: _normalize_text(" ".join(sections.get(field, ()))) for field in SECTION_FIELDS}


def _extract_baselines(text: str) -> str:
    selected = []
    lowered_keywords = tuple(keyword.lower() for keyword in _BASELINE_KEYWORDS)
    for sentence in _sentences(text):
        lowered_sentence = sentence.lower()
        if any(keyword in lowered_sentence for keyword in lowered_keywords):
            selected.append(sentence)
    return _normalize_text(" ".join(selected))


def _entity_present(entity: str, text: str) -> bool:
    return entity.lower() in text.lower()


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
        entity for entity in spec["required_entities"] if _entity_present(str(entity), excerpt)
    )
    return OperationalState(
        paper=str(spec["paper"]),
        paper_id=str(spec["paper_id"]),
        title=title,
        fields=fields,
        required_entities=required_entities,
    )


def compact_operational_state(state: OperationalState) -> dict[str, object]:
    """Build the compact replay representation from deterministic keywords."""

    fields = state.as_dict()["operational_fields"]
    assert isinstance(fields, dict)
    compact_fields = {
        field_name: fields[field_name] for field_name in SECTION_FIELDS + ("baselines",)
    }
    compact_fields["required_entities"] = list(state.required_entities)
    return {
        "paper": state.paper,
        "paper_id": state.paper_id,
        "title": state.title,
        "operational_fields": compact_fields,
    }


def replay_compact_state(compact: dict[str, object]) -> dict[str, object]:
    """Reconstruct replay state from compact keyword fields and entity lists."""

    compact_fields = compact["operational_fields"]
    assert isinstance(compact_fields, dict)
    replay_fields: dict[str, object] = {
        field_name: str(compact_fields[field_name]) for field_name in SECTION_FIELDS + ("baselines",)
    }
    replay_fields["required_entities"] = list(compact_fields["required_entities"])
    replayed = {
        "paper": compact["paper"],
        "paper_id": compact["paper_id"],
        "title": compact["title"],
        "operational_fields": replay_fields,
    }
    return json.loads(canonical_json(replayed))


def _retention_rate(original_entities: list[str], replayed_entities: list[str]) -> float:
    if not original_entities:
        return 0.0
    replayed = set(replayed_entities)
    return len([entity for entity in original_entities if entity in replayed]) / len(original_entities)


def _field_survived(original_value: object, replayed_value: object) -> bool:
    if isinstance(original_value, list) and isinstance(replayed_value, list):
        return bool(original_value) and original_value == replayed_value
    if isinstance(original_value, str) and isinstance(replayed_value, str):
        return bool(original_value) and normalized_keyword_overlap(original_value, replayed_value) == 1.0
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

    original_entities = list(original_fields["required_entities"])
    replayed_entities = list(replayed_fields["required_entities"])

    section_survivals = [
        _field_survived(original_fields[field], replayed_fields[field])
        for field in SECTION_FIELDS + ("baselines",)
    ]
    surviving_operational_fields = sum(
        1 for field in OPERATIONAL_FIELDS if _field_survived(original_fields[field], replayed_fields[field])
    )
    total_operational_fields = len(OPERATIONAL_FIELDS)

    original_token_count = token_count(excerpt)
    compact_text = canonical_json(compact_representation)
    replay_text = canonical_json(replayed_state)
    compact_token_count = token_count(compact_text)
    replay_token_count = token_count(replay_text)

    return {
        "paper": paper,
        "entity_retention_rate": round(_retention_rate(original_entities, replayed_entities), 6),
        "section_survival_rate": round(sum(section_survivals) / len(section_survivals), 6),
        "limitation_survival_rate": round(
            normalized_keyword_overlap(str(original_fields["limitations"]), str(replayed_fields["limitations"])), 6
        ),
        "metric_survival_rate": round(
            normalized_keyword_overlap(str(original_fields["metrics"]), str(replayed_fields["metrics"])), 6
        ),
        "compression_ratio": round(compact_token_count / original_token_count, 6) if original_token_count else 0.0,
        "replay_consistency": round(surviving_operational_fields / total_operational_fields, 6),
        "original_token_count": original_token_count,
        "compact_token_count": compact_token_count,
        "replay_token_count": replay_token_count,
    }


def run_paper_replay() -> list[ReplayRun]:
    """Run all paper fixtures in stable target-paper order."""

    runs = []
    for spec in PAPER_SPECS:
        excerpt = _load_fixture(spec)
        state = extract_operational_state(spec, excerpt)
        original_state = json.loads(canonical_json(state.as_dict()))
        compact = json.loads(canonical_json(compact_operational_state(state)))
        replayed = replay_compact_state(compact)
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


def build_paper_replay_artifact() -> dict[str, object]:
    """Build the public benchmark artifact schema."""

    return {
        "benchmark": BENCHMARK_NAME,
        "papers": [run.artifact_row for run in run_paper_replay()],
    }


def write_paper_replay_artifact(path: Path = DEFAULT_ARTIFACT_PATH) -> dict[str, object]:
    artifact = build_paper_replay_artifact()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(artifact_json(artifact), encoding="utf-8")
    return artifact


if __name__ == "__main__":
    write_paper_replay_artifact()

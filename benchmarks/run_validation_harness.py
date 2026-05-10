"""Run deterministic industrial replay validation for CompTextV7."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.validation.validation_harness import ValidationHarness  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1701, help="Deterministic replay seed.")
    parser.add_argument("--encoding", choices=("cl100k_base", "o200k_base"), default="cl100k_base")
    parser.add_argument("--jsonl", type=Path, help="Optional JSONL export path.")
    parser.add_argument("--csv", type=Path, help="Optional CSV export path.")
    args = parser.parse_args()

    harness = ValidationHarness(seed=args.seed, encoding_name=args.encoding)
    results = harness.replay()
    if args.jsonl:
        harness.export_jsonl(results, args.jsonl)
    if args.csv:
        harness.export_csv(results, args.csv)
    print(json.dumps([result.as_dict() for result in results], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

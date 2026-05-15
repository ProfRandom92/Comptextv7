"""Validate the expected multi-app repository layout.

The repository root intentionally has no package.json. Dashboard and showcase
Node commands belong to their app directories.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    REPO_ROOT / "dashboard" / "app" / "package.json",
    REPO_ROOT / "showcase" / "app" / "package.json",
    REPO_ROOT / "artifacts" / "paper_replay_results.json",
    REPO_ROOT / "artifacts" / "agent_trace_replay_results.json",
)


def check_repo_layout() -> list[str]:
    """Return human-readable layout errors for missing or unexpected files."""
    errors = [
        f"missing required file: {path.relative_to(REPO_ROOT)}"
        for path in REQUIRED_FILES
        if not path.is_file()
    ]

    root_package = REPO_ROOT / "package.json"
    if root_package.exists():
        errors.append("unexpected root package.json: root npm commands are not part of this layout")

    return errors


def main() -> int:
    errors = check_repo_layout()
    if errors:
        for error in errors:
            print(error)
        return 1

    print("repository layout OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

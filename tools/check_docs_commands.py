"""Check documented pymada-* command names against pyproject.toml."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
SCAN_DIRS = [ROOT / "docs", ROOT / "examples"]
# Historical markdown under archive_docs is intentionally excluded. Archived
# files may contain old state snapshots or future target names; current command
# consistency is enforced only for live docs and examples.
COMMAND_RE = re.compile(r"\bpymada-[A-Za-z0-9_-]+\b")
HISTORICAL_HINTS = ("historical", "history", "future target", "历史", "未来")


def main() -> int:
    registered = set(_console_scripts())
    failures: list[str] = []
    warnings: list[str] = []
    occurrences = 0

    for path in _scan_files():
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for command in COMMAND_RE.findall(line):
                occurrences += 1
                if command in registered:
                    continue
                location = f"{path.relative_to(ROOT)}:{line_no}: {command}"
                if _is_historical_or_future(line):
                    warnings.append(location)
                else:
                    failures.append(location)

    if failures:
        print("Docs command check failed: unregistered pymada-* commands found.")
        for failure in failures:
            print(f"- {failure}")
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"- {warning}")
        return 1

    print("Docs command check passed.")
    print(f"Summary: {occurrences} pymada-* mentions, {len(registered)} registered commands.")
    print("Archive note: archive_docs is not scanned.")
    if warnings:
        print("Warnings for historical/future mentions:")
        for warning in warnings:
            print(f"- {warning}")
    return 0


def _console_scripts() -> list[str]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    scripts = data.get("project", {}).get("scripts", {})
    if not isinstance(scripts, dict):
        raise RuntimeError("pyproject.toml [project.scripts] must be a table")
    return sorted(str(name) for name in scripts)


def _scan_files() -> list[Path]:
    files: list[Path] = []
    for directory in SCAN_DIRS:
        if not directory.exists():
            continue
        files.extend(path for path in directory.rglob("*") if path.is_file() and path.suffix in {".md", ".py"})
    return sorted(files)


def _is_historical_or_future(line: str) -> bool:
    lowered = line.lower()
    return any(hint in lowered for hint in HISTORICAL_HINTS)


if __name__ == "__main__":
    raise SystemExit(main())

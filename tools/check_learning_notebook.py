"""Validate the static pymadagascar learning notebook."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "docs" / "PYMADAGASCAR_LEARNING_GUIDE.ipynb"
PROJECT_STATUS = ROOT / "docs" / "PROJECT_STATUS.md"
PYPROJECT = ROOT / "pyproject.toml"
CLI_DIR = ROOT / "pymadagascar" / "cli"

MIN_MARKDOWN_CELLS = 8
MAX_CODE_CELLS = 4
REQUIRED_KEYWORDS = {
    "pymadagascar",
    "RSF",
    "pure Python",
    "CLI",
    "Python API",
    "seismic",
    "inversion",
    "LinearOperator",
    "LeastSquaresProblem",
    "CGLS",
    "preconditioner",
    "x = M z",
}
ABSOLUTE_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]|/(?:home/hcz|mnt)/)")


def main() -> int:
    failures = validate_learning_notebook()
    if failures:
        print("Learning notebook check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    notebook = load_notebook()
    markdown_count = _cell_count(notebook, "markdown")
    code_count = _cell_count(notebook, "code")
    cli_modules = _cli_modules()
    console_scripts = _console_scripts()
    print("Learning notebook check passed.")
    print(
        "Summary: valid static learning notebook with "
        f"{markdown_count} Markdown cells, {code_count} code cells, "
        f"{len(cli_modules)} CLI modules, {len(console_scripts)} console_scripts, "
        f"{_pytest_file_count()} pytest files, and {_workflow_count()} workflows."
    )
    return 0


def validate_learning_notebook(path: Path = NOTEBOOK) -> list[str]:
    """Return static validation failures for the learning notebook."""

    failures: list[str] = []
    if not path.is_file():
        return [f"missing learning notebook: {path.relative_to(ROOT)}"]
    if list((ROOT / "docs").glob("*.xmind")):
        failures.append("legacy XMind artifacts remain in docs")
    if (ROOT / "tools" / "check_mindmap.py").exists():
        failures.append("legacy check_mindmap.py remains; use check_learning_notebook.py")

    try:
        notebook = load_notebook(path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"learning notebook is not valid JSON: {exc}"]

    if notebook.get("nbformat") != 4:
        failures.append("learning notebook must use nbformat 4")
    if not isinstance(notebook.get("nbformat_minor"), int):
        failures.append("learning notebook must declare integer nbformat_minor")

    metadata = notebook.get("metadata")
    if not isinstance(metadata, dict):
        failures.append("learning notebook metadata must be an object")
    else:
        if not isinstance(metadata.get("kernelspec"), dict):
            failures.append("learning notebook metadata must include kernelspec")
        if not isinstance(metadata.get("language_info"), dict):
            failures.append("learning notebook metadata must include language_info")

    cells = notebook.get("cells")
    if not isinstance(cells, list):
        return failures + ["learning notebook cells must be a list"]

    markdown_cells = [cell for cell in cells if cell.get("cell_type") == "markdown"]
    code_cells = [cell for cell in cells if cell.get("cell_type") == "code"]
    if len(markdown_cells) < MIN_MARKDOWN_CELLS:
        failures.append(
            f"learning notebook must contain at least {MIN_MARKDOWN_CELLS} Markdown cells"
        )
    if len(code_cells) > MAX_CODE_CELLS:
        failures.append(
            f"learning notebook should stay light: at most {MAX_CODE_CELLS} code cells"
        )

    joined_text = "\n".join(_cell_source(cell) for cell in cells)
    normalized_text = joined_text.lower()
    missing_keywords = sorted(
        keyword for keyword in REQUIRED_KEYWORDS if keyword.lower() not in normalized_text
    )
    if missing_keywords:
        failures.append("learning notebook is missing keywords: " + ", ".join(missing_keywords))
    if ABSOLUTE_PATH_RE.search(joined_text):
        failures.append("learning notebook contains local absolute paths")

    for index, cell in enumerate(cells, start=1):
        if not isinstance(cell, dict):
            failures.append(f"cell {index} must be an object")
            continue
        if cell.get("attachments"):
            failures.append(f"cell {index} contains attachments; keep notebook text-only")
        if cell.get("cell_type") == "code":
            outputs = cell.get("outputs", [])
            if outputs:
                failures.append(f"code cell {index} contains saved outputs")

    failures.extend(_validate_project_status_inventory())
    return failures


def load_notebook(path: Path = NOTEBOOK) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise json.JSONDecodeError("notebook root must be an object", "", 0)
    return data


def _cell_source(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(str(part) for part in source)
    return str(source)


def _cell_count(notebook: dict[str, Any], cell_type: str) -> int:
    cells = notebook.get("cells", [])
    if not isinstance(cells, list):
        return 0
    return sum(1 for cell in cells if isinstance(cell, dict) and cell.get("cell_type") == cell_type)


def _validate_project_status_inventory() -> list[str]:
    text = PROJECT_STATUS.read_text(encoding="utf-8")
    failures: list[str] = []
    if "Mindmap artifacts |" in text:
        failures.append("PROJECT_STATUS.md still lists Mindmap artifacts")

    live_notebooks = _learning_notebook_count()
    match = re.search(r"Learning notebooks \| ([0-9]+) \|", text)
    if match is None:
        failures.append("PROJECT_STATUS.md must list Learning notebooks")
    elif int(match.group(1)) != live_notebooks:
        failures.append(
            "PROJECT_STATUS.md Learning notebooks is "
            f"{match.group(1)}, live repository is {live_notebooks}"
        )
    return failures


def _cli_modules() -> list[str]:
    return sorted(
        path.stem
        for path in CLI_DIR.glob("*.py")
        if path.name not in {"__init__.py", "base.py"}
    )


def _console_scripts() -> dict[str, str]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    scripts = data.get("project", {}).get("scripts", {})
    if not isinstance(scripts, dict):
        raise RuntimeError("pyproject.toml [project.scripts] must be a table")
    return {str(name): str(target) for name, target in scripts.items()}


def _pytest_file_count() -> int:
    return len(list((ROOT / "tests").glob("test_*.py")))


def _workflow_count() -> int:
    return len(
        [
            path
            for path in (ROOT / "examples" / "my_workflows").glob("*.py")
            if not path.name.startswith("_")
        ]
    )


def _learning_notebook_count() -> int:
    return len(list((ROOT / "docs").glob("*.ipynb")))


if __name__ == "__main__":
    raise SystemExit(main())

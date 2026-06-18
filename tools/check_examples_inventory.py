"""Check live example syntax, documentation, imports, and output-dir contracts."""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
USER_GUIDE = ROOT / "docs" / "USER_GUIDE.md"
WORKFLOW_README = EXAMPLES / "my_workflows" / "README.md"
EXAMPLE_RE = re.compile(r"examples/([A-Za-z0-9_]+\.py)")
HISTORICAL_OUTPUT_DIRS = (ROOT / "_tmp_linear_operator_demo", EXAMPLES / "_output")
ABSOLUTE_PATH_RE = re.compile(r"""(?x)
    (?<![A-Za-z0-9_])
    [A-Za-z]:[\\/]
    |
    Path\(\s*["']/["']\s*\)
""")


def main() -> int:
    examples = _top_level_examples()
    workflows = _workflow_scripts()
    failures = validate_examples(examples, workflows)

    if failures:
        print("Examples inventory check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Examples inventory check passed.")
    print(
        f"Summary: {len(examples)} top-level examples, "
        f"{len(workflows)} workflows, 1 workflow helper."
    )
    historical = [str(path.relative_to(ROOT)) for path in HISTORICAL_OUTPUT_DIRS if path.exists()]
    if historical:
        print("Historical ignored output directories present: " + ", ".join(historical))
    print("Archive note: archive_docs is not scanned.")
    return 0


def validate_examples(
    examples: list[Path] | None = None,
    workflows: list[Path] | None = None,
) -> list[str]:
    examples = _top_level_examples() if examples is None else examples
    workflows = _workflow_scripts() if workflows is None else workflows
    failures: list[str] = []

    guide_text = _read(USER_GUIDE)
    documented = set(EXAMPLE_RE.findall(guide_text))
    actual = {path.name for path in examples}
    missing_docs = sorted(actual - documented)
    stale_docs = sorted(documented - actual)
    if missing_docs:
        failures.append("USER_GUIDE.md is missing examples: " + ", ".join(missing_docs))
    if stale_docs:
        failures.append("USER_GUIDE.md lists missing examples: " + ", ".join(stale_docs))

    workflow_text = _read(WORKFLOW_README)
    missing_workflows = [path.name for path in workflows if path.name not in workflow_text]
    if missing_workflows:
        failures.append(
            "examples/my_workflows/README.md is missing workflows: "
            + ", ".join(missing_workflows)
        )

    for path in [*examples, *workflows]:
        relative = path.relative_to(ROOT)
        text = _read(path)
        try:
            tree = ast.parse(text, filename=str(relative))
        except SyntaxError as exc:
            failures.append(f"{relative} does not parse: {exc}")
            continue

        if not _has_main_function(tree):
            failures.append(f"{relative} has no main() function")
        if not _has_main_guard(tree):
            failures.append(f"{relative} has no __main__ guard")
        if ABSOLUTE_PATH_RE.search(text):
            failures.append(f"{relative} contains an absolute path literal")
        if path.parent == EXAMPLES and not _accepts_output_directory(tree, text):
            failures.append(
                f"{relative} must accept an output-directory argument or use tempfile"
            )
        failures.extend(_missing_pymadagascar_imports(tree, relative))

    return failures


def _top_level_examples() -> list[Path]:
    return sorted(EXAMPLES.glob("*.py"))


def _workflow_scripts() -> list[Path]:
    return sorted(
        path
        for path in (EXAMPLES / "my_workflows").glob("*.py")
        if not path.name.startswith("_")
    )


def _has_main_function(tree: ast.Module) -> bool:
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "main"
        for node in tree.body
    )


def _has_main_guard(tree: ast.Module) -> bool:
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        try:
            value = ast.literal_eval(node.test)
        except (ValueError, TypeError):
            value = None
        if value is False:
            continue
        if (
            isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == "__name__"
            and any(
                isinstance(comparator, ast.Constant) and comparator.value == "__main__"
                for comparator in node.test.comparators
            )
        ):
            return True
    return False


def _accepts_output_directory(tree: ast.Module, text: str) -> bool:
    if "tempfile." in text:
        return True
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name != "main":
            continue
        positional = [*node.args.posonlyargs, *node.args.args]
        return bool(positional or node.args.vararg or node.args.kwarg)
    return False


def _missing_pymadagascar_imports(tree: ast.Module, relative: Path) -> list[str]:
    failures: list[str] = []
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names if alias.name.startswith("pymadagascar"))
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("pymadagascar"):
            modules.add(node.module)
    for module in sorted(modules):
        if importlib.util.find_spec(module) is None:
            failures.append(f"{relative} imports missing module {module}")
    return failures


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())

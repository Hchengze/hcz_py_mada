"""Check that CLI modules, console scripts, and CLI inventory docs agree."""

from __future__ import annotations

import ast
import importlib
import re
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI_DIR = ROOT / "pymadagascar" / "cli"
PYPROJECT = ROOT / "pyproject.toml"
INVENTORY = ROOT / "docs" / "USER_GUIDE.md"


def main() -> int:
    cli_modules = _cli_modules()
    console_scripts = _console_scripts()
    failures = validate_cli_inventory(cli_modules, console_scripts)

    if failures:
        print("CLI inventory check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    registered_modules = {
        target.partition(":")[0].removeprefix("pymadagascar.cli.")
        for target in console_scripts.values()
    }
    module_only = sorted(set(cli_modules) - registered_modules)
    print("CLI inventory check passed.")
    print(f"Summary: {len(cli_modules)} CLI modules, {len(console_scripts)} console_scripts.")
    print("Runtime check: every CLI module imports, exposes main(), and has a __main__ guard.")
    if module_only:
        print("Module-only CLI entry points use python -m: " + ", ".join(module_only))
    return 0


def validate_cli_inventory(
    cli_modules: list[str] | None = None,
    console_scripts: dict[str, str] | None = None,
) -> list[str]:
    cli_modules = _cli_modules() if cli_modules is None else cli_modules
    console_scripts = _console_scripts() if console_scripts is None else console_scripts
    inventory_text = _read(INVENTORY)
    documented_modules = _inventory_names(inventory_text, "CLI Module Inventory")
    documented_console_scripts = _inventory_names(inventory_text, "Console Scripts")
    failures: list[str] = []

    missing_modules = sorted(set(cli_modules) - documented_modules)
    if missing_modules:
        failures.append("USER_GUIDE.md is missing CLI modules: " + ", ".join(missing_modules))
    extra_modules = sorted(documented_modules - set(cli_modules))
    if extra_modules:
        failures.append("USER_GUIDE.md lists missing CLI modules: " + ", ".join(extra_modules))

    script_names = set(console_scripts)
    missing_scripts = sorted(script_names - documented_console_scripts)
    if missing_scripts:
        failures.append("USER_GUIDE.md is missing console_scripts: " + ", ".join(missing_scripts))
    extra_scripts = sorted(documented_console_scripts - script_names)
    if extra_scripts:
        failures.append(
            "USER_GUIDE.md lists unregistered console_scripts: " + ", ".join(extra_scripts)
        )

    documented_scripts = set(re.findall(r"\bpymada-[A-Za-z0-9_-]+\b", inventory_text))
    unregistered = sorted(documented_scripts - script_names)
    if unregistered:
        failures.append(
            "USER_GUIDE.md documents unregistered pymada-* commands: " + ", ".join(unregistered)
        )

    failures.extend(_validate_cli_modules(cli_modules))
    failures.extend(_validate_console_script_targets(console_scripts, set(cli_modules)))
    return failures


def _cli_modules() -> list[str]:
    return sorted(
        path.stem
        for path in CLI_DIR.glob("*.py")
        if path.name not in {"base.py", "__init__.py"}
    )


def _console_scripts() -> dict[str, str]:
    data = tomllib.loads(_read(PYPROJECT))
    scripts = data.get("project", {}).get("scripts", {})
    if not isinstance(scripts, dict):
        raise RuntimeError("pyproject.toml [project.scripts] must be a table")
    return dict(sorted((str(name), str(target)) for name, target in scripts.items()))


def _validate_cli_modules(cli_modules: list[str]) -> list[str]:
    failures: list[str] = []
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    for name in cli_modules:
        path = CLI_DIR / f"{name}.py"
        try:
            tree = ast.parse(_read(path), filename=str(path.relative_to(ROOT)))
        except SyntaxError as exc:
            failures.append(f"CLI module {name} does not parse: {exc}")
            continue
        if not _has_main_guard(tree):
            failures.append(f"CLI module {name} has no __main__ guard")
        module_name = f"pymadagascar.cli.{name}"
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            failures.append(f"CLI module {module_name} does not import: {exc}")
            continue
        if not callable(getattr(module, "main", None)):
            failures.append(f"CLI module {module_name} does not expose callable main()")
    return failures


def _validate_console_script_targets(
    console_scripts: dict[str, str],
    cli_modules: set[str],
) -> list[str]:
    failures: list[str] = []
    for script, target in console_scripts.items():
        if not script.startswith("pymada-"):
            failures.append(f"console script does not use pymada-* prefix: {script}")
        module_name, separator, attribute = target.partition(":")
        if not separator or not module_name or not attribute:
            failures.append(f"console script {script} has invalid target: {target}")
            continue
        expected_prefix = "pymadagascar.cli."
        if not module_name.startswith(expected_prefix):
            failures.append(f"console script {script} targets a non-CLI module: {target}")
            continue
        short_name = module_name.removeprefix(expected_prefix)
        if short_name not in cli_modules:
            failures.append(f"console script {script} targets missing CLI module: {module_name}")
            continue
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            failures.append(f"console script {script} target does not import: {exc}")
            continue
        if not callable(getattr(module, attribute, None)):
            failures.append(f"console script {script} target is not callable: {target}")
    return failures


def _has_main_guard(tree: ast.Module) -> bool:
    for node in tree.body:
        if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
            continue
        if not isinstance(node.test.left, ast.Name) or node.test.left.id != "__name__":
            continue
        if any(
            isinstance(comparator, ast.Constant) and comparator.value == "__main__"
            for comparator in node.test.comparators
        ):
            return True
    return False


def _inventory_names(text: str, heading: str) -> set[str]:
    marker = f"## {heading}"
    if marker not in text:
        raise RuntimeError(f"USER_GUIDE.md is missing {marker}")
    section = text.split(marker, 1)[1].split("\n## ", 1)[0]
    match = re.search(r"```text\s*(.*?)```", section, flags=re.DOTALL)
    if not match:
        raise RuntimeError(f"{marker} must contain a text inventory block")
    if heading == "Console Scripts":
        return set(re.findall(r"\bpymada-[A-Za-z0-9_-]+\b", match.group(1)))
    return set(re.findall(r"(?<![A-Za-z0-9_-])[a-z][a-z0-9_]*(?![A-Za-z0-9_-])", match.group(1)))


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

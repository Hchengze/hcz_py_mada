from __future__ import annotations

import importlib
from pathlib import Path
import subprocess
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
CLI_DIR = ROOT / "pymadagascar" / "cli"
CLI_MODULES = sorted(
    path.stem
    for path in CLI_DIR.glob("*.py")
    if path.name not in {"__init__.py", "base.py"}
)
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
CONSOLE_SCRIPTS = PYPROJECT["project"]["scripts"]


def test_all_cli_modules_import_and_expose_main() -> None:
    assert len(CLI_MODULES) == 167
    failures: list[str] = []
    for name in CLI_MODULES:
        module_name = f"pymadagascar.cli.{name}"
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - summarized assertion below.
            failures.append(f"{module_name}: import failed: {exc}")
            continue
        if not callable(getattr(module, "main", None)):
            failures.append(f"{module_name}: callable main() missing")
    assert failures == []


def test_console_script_targets_resolve() -> None:
    assert len(CONSOLE_SCRIPTS) == 65
    failures: list[str] = []
    for script, target in sorted(CONSOLE_SCRIPTS.items()):
        module_name, attribute = target.split(":", 1)
        module = importlib.import_module(module_name)
        if not callable(getattr(module, attribute, None)):
            failures.append(f"{script}: target is not callable: {target}")
    assert failures == []


def test_every_cli_module_supports_python_m_help() -> None:
    failures: list[str] = []
    for name in CLI_MODULES:
        module_name = f"pymadagascar.cli.{name}"
        result = subprocess.run(
            [sys.executable, "-m", module_name, "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )
        if result.returncode != 0:
            failures.append(
                f"{module_name}: exit={result.returncode}: "
                f"{(result.stderr or result.stdout).strip()[-300:]}"
            )
    assert failures == []

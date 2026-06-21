"""Smoke tests for release consistency tools."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_check_release_tool_runs() -> None:
    result = _run_tool("check_release.py")
    assert result.returncode == 0, result.stderr + result.stdout
    assert "Release check passed" in result.stdout


def test_check_cli_inventory_tool_runs() -> None:
    result = _run_tool("check_cli_inventory.py")
    assert result.returncode == 0, result.stderr + result.stdout
    assert "CLI inventory check passed" in result.stdout
    assert "134 CLI modules" in result.stdout
    assert "25 console_scripts" in result.stdout


def test_check_docs_commands_tool_runs() -> None:
    result = _run_tool("check_docs_commands.py")
    assert result.returncode == 0, result.stderr + result.stdout
    assert "Docs command check passed" in result.stdout


def test_check_examples_inventory_tool_runs() -> None:
    result = _run_tool("check_examples_inventory.py")
    assert result.returncode == 0, result.stderr + result.stdout
    assert "Examples inventory check passed" in result.stdout
    assert "34 top-level examples" in result.stdout
    assert "15 workflows" in result.stdout


def test_check_learning_notebook_tool_runs() -> None:
    result = _run_tool("check_learning_notebook.py")
    assert result.returncode == 0, result.stderr + result.stdout
    assert "Learning notebook check passed" in result.stdout
    assert "134 CLI modules" in result.stdout
    assert "25 console_scripts" in result.stdout
    assert "82 pytest files" in result.stdout
    assert "15 workflows" in result.stdout


def _run_tool(name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / name)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

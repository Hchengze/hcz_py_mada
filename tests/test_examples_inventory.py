from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
TOP_LEVEL_EXAMPLES = sorted(path.name for path in EXAMPLES.glob("*.py"))


def test_top_level_example_inventory_is_complete() -> None:
    assert len(TOP_LEVEL_EXAMPLES) == 34


@pytest.mark.parametrize("script_name", TOP_LEVEL_EXAMPLES)
def test_top_level_example_smoke_does_not_write_into_examples(
    script_name: str,
    tmp_path: Path,
) -> None:
    before = _example_files()
    output_dir = tmp_path / script_name.removesuffix(".py")
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(ROOT)
        if not env.get("PYTHONPATH")
        else str(ROOT) + os.pathsep + env["PYTHONPATH"]
    )

    result = subprocess.run(
        [sys.executable, str(EXAMPLES / script_name), str(output_dir)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0, (
        f"{script_name} failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert _example_files() == before


def _example_files() -> set[Path]:
    return {
        path.relative_to(EXAMPLES)
        for path in EXAMPLES.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }

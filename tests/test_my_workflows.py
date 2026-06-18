from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = PROJECT_ROOT / "examples" / "my_workflows"

WORKFLOWS = [
    "basic_rsf_io_workflow.py",
    "spike_math_window_workflow.py",
    "fft_bandpass_workflow.py",
    "plot_grey_graph_workflow.py",
    "seismic_basic_agc_mute_stack_workflow.py",
]


def test_my_workflow_scripts_are_documented() -> None:
    readme = (WORKFLOW_DIR / "README.md").read_text(encoding="utf-8")

    for script_name in WORKFLOWS:
        assert script_name in readme


@pytest.mark.parametrize("script_name", WORKFLOWS)
def test_my_workflow_runs_and_writes_outputs(script_name: str, tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not env.get("PYTHONPATH")
        else str(PROJECT_ROOT) + os.pathsep + env["PYTHONPATH"]
    )

    output_dir = tmp_path / script_name.removesuffix(".py")
    result = subprocess.run(
        [sys.executable, str(WORKFLOW_DIR / script_name), str(output_dir)],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"{script_name} failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )

    outputs = [path for path in output_dir.iterdir() if path.suffix.lower() in {".rsf", ".png"}]
    assert outputs, f"{script_name} did not write any RSF or PNG outputs"

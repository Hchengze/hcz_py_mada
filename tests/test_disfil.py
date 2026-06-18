from __future__ import annotations

from pathlib import Path
import os
import re
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.cli.disfil import main as disfil_main
from pymadagascar.generic import disfil_array as package_disfil_array
from pymadagascar.generic.info import DisfilError, disfil_array, disfil_rsf
from pymadagascar.io.rsf import RSFHeader, write_rsf
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_disfil_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not env.get("PYTHONPATH")
        else str(PROJECT_ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    return subprocess.run(
        [sys.executable, "-m", "pymadagascar.cli.disfil", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _write_sample(path: Path, data: np.ndarray) -> None:
    write_rsf(
        path,
        data,
        RSFHeader(
            {
                "o1": 0.0,
                "d1": 1.0,
                "label1": "Sample",
                "o2": 0.0,
                "d2": 1.0,
                "label2": "Trace",
            }
        ),
    )


def test_disfil_array_1d_dump() -> None:
    data = np.array([0.0, 1.25, 2.5], dtype=np.float32)

    assert disfil_array(data) == "0\t0\n1\t1.25\n2\t2.5"
    assert package_disfil_array(data) == "0\t0\n1\t1.25\n2\t2.5"


def test_disfil_rsf_2d_rsf_axis_format(tmp_path: Path) -> None:
    path = tmp_path / "sample.rsf"
    data = np.arange(6, dtype=np.float32).reshape(2, 3)
    _write_sample(path, data)

    text = disfil_rsf(path, max_values=6, axis_format="rsf")

    assert text.splitlines() == [
        "i1=0,i2=0\t0",
        "i1=1,i2=0\t1",
        "i1=2,i2=0\t2",
        "i1=0,i2=1\t3",
        "i1=1,i2=1\t4",
        "i1=2,i2=1\t5",
    ]


def test_disfil_array_precision() -> None:
    data = np.array([1.234567, 12345.678], dtype=np.float64)

    assert disfil_array(data, precision=4) == "0\t1.235\n1\t1.235e+04"


def test_disfil_array_max_values_truncates() -> None:
    data = np.arange(6, dtype=np.int32)

    text = disfil_array(data, max_values=3)

    assert text.splitlines() == [
        "0\t0",
        "1\t1",
        "2\t2",
        "# truncated: shown=3 total=6 max=3",
    ]


def test_disfil_array_complex_values() -> None:
    data = np.array([1 + 2j, 3 - 4j], dtype=np.complex64)

    assert disfil_array(data) == "0\t1+2j\n1\t3-4j"


def test_disfil_cli_outputs_text(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "sample.rsf"
    _write_sample(path, np.arange(4, dtype=np.float32))

    code = disfil_main([str(path), "precision=3", "max=4", "axis_format=none"])
    captured = capsys.readouterr()

    assert code == 0
    assert captured.out == "0\n1\n2\n3\n"


def test_disfil_cli_subprocess_smoke(tmp_path: Path) -> None:
    path = tmp_path / "sample.rsf"
    _write_sample(path, np.arange(4, dtype=np.float32).reshape(2, 2))

    result = _run_disfil_cli([str(path), "max=4", "axis_format=multi"], tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "(0,0)\t0\n(0,1)\t1\n(1,0)\t2\n(1,1)\t3\n"


def test_disfil_large_array_default_limit() -> None:
    data = np.arange(1002, dtype=np.float32)

    lines = disfil_array(data).splitlines()

    assert len(lines) == 1001
    assert lines[0] == "0\t0"
    assert lines[-2] == "999\t999"
    assert lines[-1] == "# truncated: shown=1000 total=1002 max=1000"


def test_disfil_header_shape_mismatch() -> None:
    data = np.arange(4, dtype=np.float32)

    with pytest.raises(DisfilError, match="does not match data shape"):
        disfil_array(data, RSFHeader({"n1": 5}))


def test_original_sfdisfil_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfdisfil"):
        pytest.skip("Original Madagascar sfdisfil is not installed")

    path = tmp_path / "sample.rsf"
    _write_sample(path, np.arange(4, dtype=np.float32))

    original = run_original_madagascar(
        ["sfdisfil", "number=n", "col=999"],
        cwd=tmp_path,
        require_program="sfdisfil",
        stdin_path=path,
        decode_stdout=True,
    )
    python_text = disfil_rsf(path, max_values=4, precision=6, axis_format="none")

    assert _parse_numbers(python_text) == pytest.approx(_parse_numbers(original.stdout))


def _parse_numbers(text: str) -> list[float]:
    return [float(token) for token in re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?", text)]

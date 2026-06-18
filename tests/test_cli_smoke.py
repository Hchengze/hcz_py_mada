from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys

import numpy as np

from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(name: str, args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    script = shutil.which(f"pymada-{name}")
    command = [script, *args] if script else [sys.executable, "-m", f"pymadagascar.cli.{name}", *args]
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not env.get("PYTHONPATH")
        else str(PROJECT_ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"command failed: {' '.join(command)}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    return result


def _sample_header() -> RSFHeader:
    return RSFHeader(
        {
            "o1": 1.0,
            "d1": 0.5,
            "label1": "Sample",
            "unit1": "s",
        }
    )


def test_pyproject_registers_stable_console_scripts() -> None:
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    expected = {
        "pymada-info",
        "pymada-get",
        "pymada-disfil",
        "pymada-real",
        "pymada-imag",
        "pymada-cmplx",
        "pymada-rtoc",
        "pymada-noise",
        "pymada-ricker",
        "pymada-spike",
        "pymada-math",
        "pymada-window",
        "pymada-attr",
        "pymada-put",
        "pymada-dd",
        "pymada-cat",
        "pymada-transp",
        "pymada-fft",
        "pymada-bandpass",
        "pymada-byte",
        "pymada-smooth",
        "pymada-boxsmooth",
        "pymada-mask",
        "pymada-cut",
        "pymada-reverse",
    }

    for script in expected:
        assert f"{script} =" in pyproject


def test_spike_cli_smoke_writes_rsf_shape_and_header(tmp_path: Path) -> None:
    output = tmp_path / "spike.rsf"

    _run_cli("spike", ["n1=5", "k1=3", "out=" + str(output)], tmp_path)
    result = read_rsf(output)

    assert result.header.dimensions == (5,)
    assert result.header["data_format"] == "native_float"
    assert result.header["d1"] == "0.004"
    np.testing.assert_array_equal(result.data, np.array([0, 0, 1, 0, 0], dtype=np.float32))


def test_window_cli_smoke_updates_axis_metadata(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "window.rsf"
    write_rsf(input_path, np.arange(8, dtype=np.float32), _sample_header())

    _run_cli("window", [str(input_path), "out=" + str(output_path), "f1=2", "n1=3"], tmp_path)
    result = read_rsf(output_path)

    assert result.header.dimensions == (3,)
    assert result.header["o1"] == "2"
    assert result.header["d1"] == "0.5"
    np.testing.assert_array_equal(result.data, np.array([2, 3, 4], dtype=np.float32))


def test_math_cli_smoke_writes_deterministic_expression(tmp_path: Path) -> None:
    output = tmp_path / "math.rsf"

    _run_cli("math", ["n1=4", "output=x1*2+1", "out=" + str(output)], tmp_path)
    result = read_rsf(output)

    assert result.header.dimensions == (4,)
    np.testing.assert_array_equal(result.data, np.array([1, 3, 5, 7], dtype=np.float32))


def test_attr_cli_smoke_outputs_statistics(tmp_path: Path) -> None:
    input_path = tmp_path / "stats.rsf"
    write_rsf(input_path, np.array([0.0, 2.0, 4.0], dtype=np.float32), _sample_header())

    result = _run_cli("attr", [str(input_path)], tmp_path)

    assert "min: 0" in result.stdout
    assert "max: 4" in result.stdout
    assert "mean: 2" in result.stdout
    assert "nonzero_count: 2" in result.stdout


def test_put_cli_smoke_updates_harmless_header_key(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "put.rsf"
    data = np.arange(4, dtype=np.float32)
    write_rsf(input_path, data, _sample_header())

    _run_cli(
        "put",
        [str(input_path), "out=" + str(output_path), "label1=Depth", "unit1=m", "survey=demo"],
        tmp_path,
    )
    result = read_rsf(output_path)

    assert result.header["label1"] == "Depth"
    assert result.header["unit1"] == "m"
    assert result.header["survey"] == "demo"
    np.testing.assert_array_equal(result.data, data)


def test_dd_cli_smoke_converts_float32_to_float64(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "double.rsf"
    data = np.array([0.2, 1.6, -1.6], dtype=np.float32)
    write_rsf(input_path, data, _sample_header())

    _run_cli("dd", [str(input_path), "out=" + str(output_path), "type=float64"], tmp_path)
    result = read_rsf(output_path)

    assert result.data.dtype == np.float64
    assert result.header["data_format"] == "native_double"
    np.testing.assert_allclose(result.data, data.astype(np.float64))

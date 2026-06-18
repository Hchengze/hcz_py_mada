from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.generic import (
    cmplx_rsf as package_cmplx_rsf,
    imag_rsf as package_imag_rsf,
    real_rsf as package_real_rsf,
    rtoc_rsf as package_rtoc_rsf,
)
from pymadagascar.generic.complex_tools import (
    ComplexToolError,
    cmplx_rsf,
    imag_rsf,
    real_rsf,
    rtoc_rsf,
)
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _header() -> RSFHeader:
    return RSFHeader(
        {
            "o1": 0.25,
            "d1": 0.5,
            "label1": "Frequency",
            "unit1": "Hz",
            "o2": 10.0,
            "d2": 2.0,
            "label2": "Trace",
        }
    )


def _write_complex(path: Path) -> np.ndarray:
    data = np.array(
        [[1.0 + 2.0j, -3.0 - 4.0j, 5.0 + 0.5j], [7.0 - 8.0j, 0.0 + 0.0j, -1.5 + 3.5j]],
        dtype=np.complex64,
    )
    write_rsf(path, data, _header())
    return data


def _write_real(path: Path, data: np.ndarray | None = None) -> np.ndarray:
    values = (
        np.array([[1.0, -3.0, 5.0], [7.0, 0.0, -1.5]], dtype=np.float32)
        if data is None
        else data
    )
    write_rsf(path, values, _header())
    return values


def _run_cli(name: str, args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not env.get("PYTHONPATH")
        else str(PROJECT_ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    return subprocess.run(
        [sys.executable, "-m", f"pymadagascar.cli.{name}", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_real_rsf_extracts_real_part_and_header(tmp_path: Path) -> None:
    input_path = tmp_path / "complex.rsf"
    output_path = tmp_path / "real.rsf"
    data = _write_complex(input_path)

    result = real_rsf(input_path, output_path)
    loaded = read_rsf(output_path)

    assert package_real_rsf is real_rsf
    assert result.header_path == output_path.resolve()
    assert loaded.data.dtype == np.float32
    assert loaded.header["data_format"] == "native_float"
    assert loaded.header["esize"] == "4"
    assert loaded.header["label1"] == "Frequency"
    np.testing.assert_allclose(loaded.data, data.real.astype(np.float32))


def test_imag_rsf_extracts_imaginary_part(tmp_path: Path) -> None:
    input_path = tmp_path / "complex.rsf"
    output_path = tmp_path / "imag.rsf"
    data = _write_complex(input_path)

    imag_rsf(input_path, output_path)
    loaded = read_rsf(output_path)

    assert package_imag_rsf is imag_rsf
    assert loaded.data.dtype == np.float32
    np.testing.assert_allclose(loaded.data, data.imag.astype(np.float32))


def test_cmplx_rsf_combines_real_and_imaginary_parts(tmp_path: Path) -> None:
    real_path = tmp_path / "real.rsf"
    imag_path = tmp_path / "imag.rsf"
    output_path = tmp_path / "complex.rsf"
    real_data = _write_real(real_path)
    imag_data = _write_real(imag_path, np.array([[2.0, -4.0, 0.5], [-8.0, 0.0, 3.5]], dtype=np.float32))

    cmplx_rsf(real_path, imag_path, output_path)
    loaded = read_rsf(output_path)

    assert package_cmplx_rsf is cmplx_rsf
    assert loaded.data.dtype == np.complex64
    assert loaded.header["data_format"] == "native_complex"
    assert loaded.header["esize"] == "8"
    assert loaded.header["label2"] == "Trace"
    np.testing.assert_allclose(loaded.data, real_data.astype(np.complex64) + 1j * imag_data)


def test_rtoc_rsf_adds_zero_imaginary_part(tmp_path: Path) -> None:
    input_path = tmp_path / "real.rsf"
    output_path = tmp_path / "complex.rsf"
    data = _write_real(input_path)

    rtoc_rsf(input_path, output_path)
    loaded = read_rsf(output_path)

    assert package_rtoc_rsf is rtoc_rsf
    assert loaded.data.dtype == np.complex64
    np.testing.assert_allclose(loaded.data.real, data.astype(np.float32))
    np.testing.assert_allclose(loaded.data.imag, 0.0)


def test_cmplx_rsf_rejects_shape_mismatch_without_output(tmp_path: Path) -> None:
    real_path = tmp_path / "real.rsf"
    imag_path = tmp_path / "imag.rsf"
    output_path = tmp_path / "complex.rsf"
    _write_real(real_path, np.arange(6, dtype=np.float32).reshape(2, 3))
    _write_real(imag_path, np.arange(4, dtype=np.float32).reshape(2, 2))

    with pytest.raises(ComplexToolError, match="same shape"):
        cmplx_rsf(real_path, imag_path, output_path)

    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + "@").exists()


def test_real_and_imag_reject_real_input(tmp_path: Path) -> None:
    input_path = tmp_path / "real.rsf"
    _write_real(input_path)

    with pytest.raises(ComplexToolError, match="requires a complex"):
        real_rsf(input_path, tmp_path / "real_out.rsf")
    with pytest.raises(ComplexToolError, match="requires a complex"):
        imag_rsf(input_path, tmp_path / "imag_out.rsf")


def test_cmplx_and_rtoc_reject_complex_input(tmp_path: Path) -> None:
    complex_path = tmp_path / "complex.rsf"
    real_path = tmp_path / "real.rsf"
    _write_complex(complex_path)
    _write_real(real_path)

    with pytest.raises(ComplexToolError, match="requires a real numeric"):
        cmplx_rsf(complex_path, real_path, tmp_path / "bad_cmplx.rsf")
    with pytest.raises(ComplexToolError, match="requires a real numeric"):
        rtoc_rsf(complex_path, tmp_path / "bad_rtoc.rsf")


@pytest.mark.cli
def test_complex_tool_cli_subprocess_smoke(tmp_path: Path) -> None:
    complex_path = tmp_path / "complex.rsf"
    real_path = tmp_path / "real.rsf"
    imag_path = tmp_path / "imag.rsf"
    rebuilt_path = tmp_path / "rebuilt.rsf"
    rtoc_path = tmp_path / "rtoc.rsf"
    data = _write_complex(complex_path)

    real_result = _run_cli("real", [str(complex_path), "out=" + str(real_path)], tmp_path)
    imag_result = _run_cli("imag", [str(complex_path), "out=" + str(imag_path)], tmp_path)
    cmplx_result = _run_cli("cmplx", [str(real_path), str(imag_path), "out=" + str(rebuilt_path)], tmp_path)
    rtoc_result = _run_cli("rtoc", [str(real_path), "out=" + str(rtoc_path)], tmp_path)

    assert real_result.returncode == 0, real_result.stderr
    assert imag_result.returncode == 0, imag_result.stderr
    assert cmplx_result.returncode == 0, cmplx_result.stderr
    assert rtoc_result.returncode == 0, rtoc_result.stderr
    np.testing.assert_allclose(read_rsf(real_path).data, data.real)
    np.testing.assert_allclose(read_rsf(imag_path).data, data.imag)
    np.testing.assert_allclose(read_rsf(rebuilt_path).data, data)
    assert read_rsf(rtoc_path).data.dtype == np.complex64


@pytest.mark.original_madagascar
def test_original_sfreal_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfreal"):
        pytest.skip("Original Madagascar sfreal is not installed")

    input_path = tmp_path / "complex.rsf"
    original = tmp_path / "original_real.rsf"
    python = tmp_path / "python_real.rsf"
    _write_complex(input_path)

    run_original_madagascar(
        ["sfreal", "in=complex.rsf", "out=original_real.rsf"],
        cwd=tmp_path,
        require_program="sfreal",
    )
    real_rsf(input_path, python)

    assert_rsf_allclose(original, python, ignore_keys={"in"})


@pytest.mark.original_madagascar
def test_original_sfimag_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfimag"):
        pytest.skip("Original Madagascar sfimag is not installed")

    input_path = tmp_path / "complex.rsf"
    original = tmp_path / "original_imag.rsf"
    python = tmp_path / "python_imag.rsf"
    _write_complex(input_path)

    run_original_madagascar(
        ["sfimag", "in=complex.rsf", "out=original_imag.rsf"],
        cwd=tmp_path,
        require_program="sfimag",
    )
    imag_rsf(input_path, python)

    assert_rsf_allclose(original, python, ignore_keys={"in"})


@pytest.mark.original_madagascar
def test_original_sfcmplx_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfcmplx"):
        pytest.skip("Original Madagascar sfcmplx is not installed")

    real_path = tmp_path / "real.rsf"
    imag_path = tmp_path / "imag.rsf"
    original = tmp_path / "original_cmplx.rsf"
    python = tmp_path / "python_cmplx.rsf"
    _write_real(real_path)
    _write_real(imag_path, np.array([[2.0, -4.0, 0.5], [-8.0, 0.0, 3.5]], dtype=np.float32))

    run_original_madagascar(
        ["sfcmplx", "real.rsf", "imag.rsf", "out=original_cmplx.rsf"],
        cwd=tmp_path,
        require_program="sfcmplx",
    )
    cmplx_rsf(real_path, imag_path, python)

    assert_rsf_allclose(original, python, ignore_keys={"in"})


@pytest.mark.original_madagascar
def test_original_sfrtoc_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfrtoc"):
        pytest.skip("Original Madagascar sfrtoc is not installed")

    input_path = tmp_path / "real.rsf"
    original = tmp_path / "original_rtoc.rsf"
    python = tmp_path / "python_rtoc.rsf"
    _write_real(input_path)

    run_original_madagascar(
        ["sfrtoc", "in=real.rsf", "out=original_rtoc.rsf"],
        cwd=tmp_path,
        require_program="sfrtoc",
    )
    rtoc_rsf(input_path, python)

    assert_rsf_allclose(original, python, ignore_keys={"in"})

from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.generic.file_ops import FileToolError, copy_rsf_dataset, remove_rsf_dataset
from pymadagascar.generic.stats import StatError, max_rsf, min_rsf, minmax_rsf
from pymadagascar.io.rsf import RSFHeader, read_header, read_rsf, write_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _header() -> RSFHeader:
    return RSFHeader({"o1": 0.0, "d1": 0.5, "label1": "Sample", "unit1": "s"})


def _write_input(path: Path, data: np.ndarray | None = None, *, data_format: str | None = None) -> np.ndarray:
    values = np.array([[1.0, -2.0, 3.0], [4.0, 5.0, -6.0]], dtype=np.float32) if data is None else data
    write_rsf(path, values, _header(), data_format=data_format)
    return values


def _run_cli(module: str, args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not env.get("PYTHONPATH")
        else str(PROJECT_ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    return subprocess.run(
        [sys.executable, "-m", f"pymadagascar.cli.{module}", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_copy_rsf_dataset_copies_header_and_sidecar_bytes(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "copy.rsf"
    data = _write_input(input_path)
    source_sidecar = read_header(input_path).binary_path(input_path)
    source_bytes = source_sidecar.read_bytes()

    result = copy_rsf_dataset(input_path, output_path)
    copied = read_rsf(output_path)

    assert result.header_path == output_path.resolve()
    assert result.binary_path == output_path.with_name("copy.rsf@").resolve()
    assert read_header(output_path)["in"] == "./copy.rsf@"
    assert result.binary_path.read_bytes() == source_bytes
    assert source_sidecar.read_bytes() == source_bytes
    np.testing.assert_array_equal(copied.data, data)


def test_copy_rsf_dataset_preserves_ascii_float_sidecar(tmp_path: Path) -> None:
    input_path = tmp_path / "ascii.rsf"
    output_path = tmp_path / "ascii_copy.rsf"
    data = np.array([1.25, -2.5, 3.75], dtype=np.float32)
    _write_input(input_path, data, data_format="ascii_float")
    source_header = read_header(input_path)
    source_text = source_header.binary_path(input_path).read_text(encoding="utf-8")

    copy_rsf_dataset(input_path, output_path)
    copied_header = read_header(output_path)
    copied = read_rsf(output_path)

    assert copied_header["data_format"] == "ascii_float"
    assert copied_header.binary_path(output_path).read_text(encoding="utf-8") == source_text
    np.testing.assert_allclose(copied.data, data)


def test_copy_rsf_dataset_rejects_overwrite_by_default(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "copy.rsf"
    _write_input(input_path)
    _write_input(output_path)

    with pytest.raises(FileToolError, match="overwrite"):
        copy_rsf_dataset(input_path, output_path)

    copy_rsf_dataset(input_path, output_path, overwrite=True)
    np.testing.assert_array_equal(read_rsf(output_path).data, read_rsf(input_path).data)


def test_remove_rsf_dataset_dry_run_is_default(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    _write_input(input_path)
    sidecar = read_header(input_path).binary_path(input_path)

    result = remove_rsf_dataset(input_path)

    assert result.dry_run is True
    assert sidecar.resolve() in result.paths
    assert input_path.resolve() in result.paths
    assert input_path.exists()
    assert sidecar.exists()


def test_remove_rsf_dataset_requires_confirmation_for_delete(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    _write_input(input_path)
    sidecar = read_header(input_path).binary_path(input_path)

    with pytest.raises(FileToolError, match="confirm"):
        remove_rsf_dataset(input_path, dry_run=False)

    result = remove_rsf_dataset(input_path, dry_run=False, confirm=True)

    assert result.dry_run is False
    assert not input_path.exists()
    assert not sidecar.exists()


def test_remove_rsf_dataset_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(FileToolError, match="directory"):
        remove_rsf_dataset(tmp_path)


def test_minmax_rsf_global_values_and_indices(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    _write_input(input_path)

    minimum = min_rsf(input_path)
    maximum = max_rsf(input_path)

    assert minimum.value == -6.0
    assert minimum.index == (1, 2)
    assert maximum.value == 5.0
    assert maximum.index == (1, 1)


def test_minmax_rsf_axis_uses_rsf_axis_numbers(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    data = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.int32)
    _write_input(input_path, data)

    axis1 = min_rsf(input_path, axis=1)
    axis2 = max_rsf(input_path, axis=2)

    np.testing.assert_array_equal(axis1.value, np.array([1, 4]))
    np.testing.assert_array_equal(axis2.value, np.array([4, 5, 6]))


def test_minmax_rsf_nan_policy_omit(tmp_path: Path) -> None:
    input_path = tmp_path / "nan.rsf"
    data = np.array([np.nan, 2.0, -1.0], dtype=np.float32)
    _write_input(input_path, data)

    propagated = minmax_rsf(input_path, kind="min")
    omitted = minmax_rsf(input_path, kind="min", nan_policy="omit")

    assert np.isnan(propagated.value)
    assert omitted.value == -1.0
    assert omitted.index == (2,)


def test_minmax_rsf_complex_policy(tmp_path: Path) -> None:
    input_path = tmp_path / "complex.rsf"
    data = np.array([1 + 2j, 3 + 4j], dtype=np.complex64)
    write_rsf(input_path, data, _header())

    with pytest.raises(StatError, match="complex"):
        max_rsf(input_path)

    result = max_rsf(input_path, complex_policy="abs")
    assert result.value == pytest.approx(5.0)
    assert result.index == (1,)


def test_cp_rm_min_max_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    copy_path = tmp_path / "copy.rsf"
    _write_input(input_path)

    cp_result = _run_cli("cp", [str(input_path), "out=" + str(copy_path)], tmp_path)
    assert cp_result.returncode == 0, cp_result.stderr
    np.testing.assert_array_equal(read_rsf(copy_path).data, read_rsf(input_path).data)

    min_result = _run_cli("min", [str(copy_path)], tmp_path)
    assert min_result.returncode == 0, min_result.stderr
    assert "value=-6" in min_result.stdout
    assert "index=1,2" in min_result.stdout

    max_result = _run_cli("max", [str(copy_path), "axis=1"], tmp_path)
    assert max_result.returncode == 0, max_result.stderr
    assert "values=3,5" in max_result.stdout

    dry_run = _run_cli("rm", [str(copy_path)], tmp_path)
    assert dry_run.returncode == 0, dry_run.stderr
    assert "would_remove=" in dry_run.stdout
    assert copy_path.exists()

    removed = _run_cli("rm", [str(copy_path), "confirm=y"], tmp_path)
    assert removed.returncode == 0, removed.stderr
    assert "removed=" in removed.stdout
    assert not copy_path.exists()
    assert not copy_path.with_name("copy.rsf@").exists()


def test_rm_cli_rejects_actual_delete_without_confirm(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    _write_input(input_path)

    result = _run_cli("rm", [str(input_path), "dry_run=n"], tmp_path)

    assert result.returncode == 2
    assert "confirm=y" in result.stderr
    assert input_path.exists()


def test_original_sfcp_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfcp"):
        pytest.skip("Original Madagascar sfcp is not installed")

    input_path = tmp_path / "input.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    _write_input(input_path, np.arange(6, dtype=np.float32).reshape(2, 3))

    run_original_madagascar(["sfcp", "input.rsf", "original.rsf"], cwd=tmp_path, require_program="sfcp")
    assert _run_cli("cp", [str(input_path), "out=" + str(python)], tmp_path).returncode == 0

    assert_rsf_allclose(original, python, ignore_keys={"in"})


def test_original_sfrm_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfrm"):
        pytest.skip("Original Madagascar sfrm is not installed")

    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    _write_input(original)
    _write_input(python)

    run_original_madagascar(["sfrm", "original.rsf"], cwd=tmp_path, require_program="sfrm")
    assert _run_cli("rm", [str(python), "confirm=y"], tmp_path).returncode == 0

    assert not original.exists()
    assert not original.with_name("original.rsf@").exists()
    assert not python.exists()
    assert not python.with_name("python.rsf@").exists()


def test_original_sfmin_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfmin"):
        pytest.skip("Original Madagascar sfmin is not installed")

    input_path = tmp_path / "input.rsf"
    original = tmp_path / "original_min.rsf"
    _write_input(input_path)

    run_original_madagascar(["sfmin", "in=input.rsf", "out=original_min.rsf", "axis=0"], cwd=tmp_path, require_program="sfmin")

    assert float(read_rsf(original).data.ravel()[0]) == pytest.approx(float(min_rsf(input_path).value))


def test_original_sfmax_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfmax"):
        pytest.skip("Original Madagascar sfmax is not installed")

    input_path = tmp_path / "input.rsf"
    original = tmp_path / "original_max.rsf"
    _write_input(input_path)

    run_original_madagascar(["sfmax", "in=input.rsf", "out=original_max.rsf", "axis=0"], cwd=tmp_path, require_program="sfmax")

    assert float(read_rsf(original).data.ravel()[0]) == pytest.approx(float(max_rsf(input_path).value))

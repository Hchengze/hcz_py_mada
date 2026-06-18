from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.generic.byte import ByteScaleError, byte_rsf, byte_scale
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.plot._common import pyplot
from pymadagascar.plot.grey import grey


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _header() -> RSFHeader:
    return RSFHeader(
        {
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "o2": 100.0,
            "d2": 25.0,
            "label2": "Trace",
            "unit2": "m",
        }
    )


def test_byte_scale_simple_range() -> None:
    data = np.array([0.0, 0.5, 1.0], dtype=np.float32)

    result = byte_scale(data)

    assert result.dtype == np.int32
    np.testing.assert_array_equal(result, np.array([0, 128, 255], dtype=np.int32))


def test_byte_scale_clip() -> None:
    data = np.array([-2.0, -1.0, 0.0, 1.0, 2.0], dtype=np.float32)

    result = byte_scale(data, clip=1.0)

    np.testing.assert_array_equal(result, np.array([0, 0, 128, 255, 255], dtype=np.int32))


def test_byte_scale_pclip() -> None:
    data = np.array([-10.0, -1.0, 0.0, 1.0, 10.0], dtype=np.float32)

    result = byte_scale(data, pclip=50.0)

    np.testing.assert_array_equal(result, np.array([0, 0, 128, 255, 255], dtype=np.int32))


def test_byte_scale_allpos() -> None:
    data = np.array([-1.0, 0.0, 0.5, 1.0, 2.0], dtype=np.float32)

    result = byte_scale(data, clip=1.0, allpos=True)

    np.testing.assert_array_equal(result, np.array([0, 0, 128, 255, 255], dtype=np.int32))


def test_byte_scale_nan_and_inf_output_zero() -> None:
    data = np.array([0.0, np.nan, 1.0, np.inf, -np.inf], dtype=np.float32)

    result = byte_scale(data)

    np.testing.assert_array_equal(result, np.array([0, 0, 255, 0, 0], dtype=np.int32))


def test_byte_scale_rejects_complex() -> None:
    with pytest.raises(ByteScaleError, match="real-valued"):
        byte_scale(np.array([1.0 + 2.0j], dtype=np.complex64))


def test_byte_rsf_writes_native_int_and_inherits_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "byte.rsf"
    data = np.arange(6, dtype=np.float32).reshape(2, 3)
    write_rsf(input_path, data, _header())

    byte_rsf(input_path, output_path)
    result = read_rsf(output_path)

    assert result.data.dtype == np.int32
    assert result.header["data_format"] == "native_int"
    assert result.header.dimensions == (3, 2)
    assert result.header["label1"] == "Time"
    assert result.header["unit2"] == "m"
    assert int(result.data.min()) == 0
    assert int(result.data.max()) == 255


def test_byte_cli_subprocess(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "byte.rsf"
    write_rsf(input_path, np.array([-2.0, 0.0, 2.0], dtype=np.float32), _header())
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not env.get("PYTHONPATH")
        else str(PROJECT_ROOT) + os.pathsep + env["PYTHONPATH"]
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pymadagascar.cli.byte",
            str(input_path),
            "out=" + str(output_path),
            "clip=1",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    scaled = read_rsf(output_path)
    np.testing.assert_array_equal(scaled.data, np.array([0, 128, 255], dtype=np.int32))


def test_byte_output_can_feed_grey_quicklook(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    byte_path = tmp_path / "byte.rsf"
    png_path = tmp_path / "byte.png"
    data = np.arange(60, dtype=np.float32).reshape(6, 10)
    write_rsf(input_path, data, _header())

    scaled = byte_rsf(input_path, byte_path)
    fig = grey(scaled.data, scaled.header, output_path=png_path, clip=255.0, pclip=None, colorbar=False)
    pyplot().close(fig)

    assert png_path.exists()
    assert png_path.stat().st_size > 100
    assert png_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

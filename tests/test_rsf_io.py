from pathlib import Path

import numpy as np
import pytest

from pymadagascar.io.rsf import (
    RSFArray,
    RSFError,
    RSFHeader,
    read_header,
    read_rsf,
    write_header,
    write_rsf,
)


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
MADAGASCAR_EXAMPLE = (
    WORKSPACE_ROOT
    / "src-master"
    / "book"
    / "tccs"
    / "interpfault"
    / "interpfault-teapot"
    / "den.rsf"
)


def test_1d_float32_round_trip(tmp_path: Path) -> None:
    data = np.linspace(0.0, 1.0, 7, dtype=np.float32)
    header = RSFHeader({"d1": 0.004, "o1": 0.1, "label1": "Time", "unit1": "s"})

    written = write_rsf(tmp_path / "trace.rsf", data, header)
    result = read_rsf(tmp_path / "trace.rsf")

    assert isinstance(written, RSFArray)
    assert result.header.dimensions == (7,)
    assert result.header.shape == (7,)
    assert result.header["data_format"] == "native_float"
    assert result.header["esize"] == "4"
    assert result.header["label1"] == "Time"
    assert result.header["unit1"] == "s"
    np.testing.assert_array_equal(result.data, data)


def test_2d_int32_round_trip_preserves_rsf_axis_order(tmp_path: Path) -> None:
    data = np.arange(12, dtype=np.int32).reshape(3, 4)
    write_rsf(tmp_path / "panel.rsf", data, {"o1": 1.5, "d2": 25.0})

    result = read_rsf(tmp_path / "panel.rsf")

    assert result.header.dimensions == (4, 3)
    assert result.header.shape == data.shape
    assert result.header["n1"] == "4"
    assert result.header["n2"] == "3"
    assert result.header["data_format"] == "native_int"
    np.testing.assert_array_equal(result.data, data)


def test_3d_complex64_round_trip(tmp_path: Path) -> None:
    real = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    imag = np.flip(real, axis=-1)
    data = (real + 1j * imag).astype(np.complex64)
    header = RSFHeader(
        {
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "o2": 100.0,
            "d2": 25.0,
            "label2": "Offset",
            "o3": 1.0,
            "d3": 1.0,
            "label3": "CMP",
        }
    )

    write_rsf(tmp_path / "cube.rsf", data, header)
    result = read_rsf(tmp_path / "cube.rsf")

    assert result.header.dimensions == (4, 3, 2)
    assert result.header.shape == data.shape
    assert result.header["data_format"] == "native_complex"
    assert result.header["esize"] == "8"
    np.testing.assert_array_equal(result.data, data)


def test_float64_binary_round_trip(tmp_path: Path) -> None:
    data = np.arange(6, dtype=np.float64).reshape(2, 3) / 10.0

    write_rsf(tmp_path / "double.rsf", data, RSFHeader({"label1": "Sample"}))
    result = read_rsf(tmp_path / "double.rsf")

    assert result.data.dtype == np.float64
    assert result.header["data_format"] == "native_double"
    assert result.header["esize"] == "8"
    np.testing.assert_array_equal(result.data, data)


def test_ascii_float_1d_round_trip(tmp_path: Path) -> None:
    data = np.array([0.0, 1.5, -2.25, 3.0], dtype=np.float32)

    written = write_rsf(tmp_path / "ascii1.rsf", data, data_format="ascii_float")
    result = read_rsf(tmp_path / "ascii1.rsf")

    assert written.header["data_format"] == "ascii_float"
    assert written.header["esize"] == "0"
    assert result.data.dtype == np.float32
    assert result.header.dimensions == (4,)
    assert "0" in written.binary_path.read_text(encoding="utf-8")
    np.testing.assert_allclose(result.data, data)


def test_ascii_float_2d_round_trip_from_float64_input(tmp_path: Path) -> None:
    data = (np.arange(12, dtype=np.float64).reshape(3, 4) / 7.0) - 0.5

    write_rsf(tmp_path / "ascii2.rsf", data, {"label1": "Sample"}, data_format="ascii_float")
    result = read_rsf(tmp_path / "ascii2.rsf")

    assert result.header["data_format"] == "ascii_float"
    assert result.header["esize"] == "0"
    assert result.header.dimensions == (4, 3)
    assert result.data.dtype == np.float32
    np.testing.assert_allclose(result.data, data.astype(np.float32))


def test_ascii_float_3d_round_trip_from_header_request(tmp_path: Path) -> None:
    data = np.linspace(-1.0, 1.0, 24, dtype=np.float32).reshape(2, 3, 4)
    header = RSFHeader({"data_format": "ascii_float", "label3": "Inline"})

    write_rsf(tmp_path / "ascii3.rsf", data, header)
    result = read_rsf(tmp_path / "ascii3.rsf")

    assert result.header["data_format"] == "ascii_float"
    assert result.header["label3"] == "Inline"
    assert result.header.dimensions == (4, 3, 2)
    np.testing.assert_allclose(result.data, data)


def test_ascii_float_legacy_esize_zero_without_data_format(tmp_path: Path) -> None:
    header_path = tmp_path / "legacy.rsf"
    data_path = tmp_path / "legacy.rsf@"
    write_header(
        header_path,
        RSFHeader({"n1": 3, "esize": 0, "in": "./legacy.rsf@"}),
    )
    data_path.write_text("1 2.5 -3\n", encoding="utf-8")

    result = read_rsf(header_path)

    assert result.header.data_format == "ascii_float"
    np.testing.assert_allclose(result.data, np.array([1.0, 2.5, -3.0], dtype=np.float32))


def test_rejects_unsupported_ascii_format(tmp_path: Path) -> None:
    data = np.arange(3, dtype=np.float32)

    with pytest.raises(RSFError, match="Only ascii_float output is supported"):
        write_rsf(tmp_path / "bad_ascii.rsf", data, data_format="ascii_double")


def test_rejects_reading_unsupported_ascii_format(tmp_path: Path) -> None:
    header_path = tmp_path / "bad_ascii_read.rsf"
    data_path = tmp_path / "bad_ascii_read.rsf@"
    write_header(
        header_path,
        RSFHeader({"n1": 3, "data_format": "ascii_double", "esize": 0, "in": "./bad_ascii_read.rsf@"}),
    )
    data_path.write_text("1 2 3\n", encoding="utf-8")

    with pytest.raises(RSFError, match="ASCII data_format is not supported"):
        read_rsf(header_path)


def test_header_round_trip(tmp_path: Path) -> None:
    header = RSFHeader(
        {
            "data_format": "native_float",
            "esize": 4,
            "in": "./custom.rsf@",
            "n1": 5,
            "d1": 0.25,
            "o1": -1.0,
            "label1": "Time sample",
            "unit1": "s",
        }
    )

    write_header(tmp_path / "custom.rsf", header)
    result = read_header(tmp_path / "custom.rsf")

    assert result["data_format"] == "native_float"
    assert result["esize"] == "4"
    assert result["in"] == "./custom.rsf@"
    assert result["n1"] == "5"
    assert result["d1"] == "0.25"
    assert result["o1"] == "-1"
    assert result["label1"] == "Time sample"
    assert result["unit1"] == "s"


def test_binary_sidecar_path_is_automatic(tmp_path: Path) -> None:
    data = np.arange(5, dtype=np.float32)

    result = write_rsf(tmp_path / "auto.rsf", data, None)

    assert result.binary_path == (tmp_path / "auto.rsf@").resolve()
    assert (tmp_path / "auto.rsf@").exists()
    assert read_header(tmp_path / "auto.rsf")["in"] == "./auto.rsf@"


def test_rejects_unsupported_dtype(tmp_path: Path) -> None:
    data = np.arange(3, dtype=np.int64)

    with pytest.raises(RSFError, match="Unsupported dtype"):
        write_rsf(tmp_path / "bad.rsf", data)


def test_reads_existing_madagascar_example_header_and_binary() -> None:
    if not MADAGASCAR_EXAMPLE.exists():
        pytest.skip("No complete Madagascar example RSF file found in src-master")

    binary = MADAGASCAR_EXAMPLE.with_name("den.rsf@")
    if not binary.exists():
        pytest.skip("Madagascar example header exists but binary sidecar is missing")

    header = read_header(MADAGASCAR_EXAMPLE)
    result = read_rsf(MADAGASCAR_EXAMPLE)

    assert header["data_format"] == "native_float"
    assert header["in"] == "./den.rsf@"
    assert header.dimensions == (401, 357)
    assert result.data.shape == (357, 401)
    assert result.data.dtype == np.float32
    assert result.binary_path == binary.resolve()

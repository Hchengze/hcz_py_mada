from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.segyread import main as segyread_main
from pymadagascar.cli.segywrite import main as segywrite_main
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.io.segy import (
    SegyError,
    extract_trace_header_table,
    read_segy_headers,
    rsf_to_segy,
    segy_to_rsf,
)
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


def _header() -> RSFHeader:
    return RSFHeader(
        {
            "n1": 5,
            "n2": 3,
            "o1": 0.1,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "o2": 0.0,
            "d2": 1.0,
            "label2": "Trace",
        }
    )


def _data() -> np.ndarray:
    return np.array(
        [
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [2.0, 3.0, 4.0, 5.0, 6.0],
            [-1.0, 0.0, 1.0, 0.0, -1.0],
        ],
        dtype=np.float32,
    )


def _trace_headers() -> list[dict[str, int]]:
    return [
        {"cdp": 101, "offset": 50, "sx": 1000, "sy": 2000, "gx": 1100, "gy": 2100},
        {"cdp": 102, "offset": 60, "sx": 1001, "sy": 2001, "gx": 1101, "gy": 2101},
        {"cdp": 103, "offset": 70, "sx": 1002, "sy": 2002, "gx": 1102, "gy": 2102},
    ]


def _make_segy(tmp_path: Path, *, endian: str = "big", sample_format: int = 5) -> Path:
    rsf_path = tmp_path / "input.rsf"
    segy_path = tmp_path / "input.sgy"
    write_rsf(rsf_path, _data(), _header())
    rsf_to_segy(
        rsf_path,
        segy_path,
        endian=endian,
        sample_format=sample_format,
        trace_headers=_trace_headers(),
        textual_header="C 1 SMALL SYNTHETIC SEG-Y FOR TESTS",
    )
    return segy_path


def test_rsf_to_segy_writes_headers(tmp_path: Path) -> None:
    segy_path = _make_segy(tmp_path)

    headers = read_segy_headers(segy_path)

    assert headers.endian == "big"
    assert headers.sample_format == 5
    assert headers.samples_per_trace == 5
    assert headers.sample_interval_us == 4000
    assert headers.trace_count == 3
    assert headers.binary_header["hns"] == 5
    assert headers.binary_header["hdt"] == 4000
    assert headers.trace_headers[0]["cdp"] == 101
    assert headers.trace_headers[1]["offset"] == 60
    assert "SMALL SYNTHETIC" in headers.textual_header


def test_segy_to_rsf_reads_data_and_metadata(tmp_path: Path) -> None:
    segy_path = _make_segy(tmp_path)
    output_path = tmp_path / "output.rsf"
    csv_path = tmp_path / "headers.csv"

    segy_to_rsf(segy_path, output_path, trace_header_csv=csv_path)
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, _data())
    assert loaded.header.dimensions == (5, 3)
    assert loaded.header["o1"] == "0.1"
    assert loaded.header["d1"] == "0.004"
    assert loaded.header["segy_format"] == "5"
    assert loaded.header["segy_sample_interval_us"] == "4000"
    assert "segy_textual_header_b64" in loaded.header
    assert csv_path.exists()


def test_trace_header_extraction_to_csv(tmp_path: Path) -> None:
    segy_path = _make_segy(tmp_path)
    csv_path = tmp_path / "trace_headers.csv"

    rows = extract_trace_header_table(segy_path, keys=["cdp", "offset", "sx", "gx"], output_csv=csv_path)

    assert rows == [
        {"trace": 1, "cdp": 101, "offset": 50, "sx": 1000, "gx": 1100},
        {"trace": 2, "cdp": 102, "offset": 60, "sx": 1001, "gx": 1101},
        {"trace": 3, "cdp": 103, "offset": 70, "sx": 1002, "gx": 1102},
    ]
    assert "cdp,offset" in csv_path.read_text(encoding="utf-8")


def test_sample_interval_preserved_round_trip(tmp_path: Path) -> None:
    segy_path = _make_segy(tmp_path)
    output_path = tmp_path / "output.rsf"

    segy_to_rsf(segy_path, output_path)
    loaded = read_rsf(output_path)

    assert float(loaded.header["d1"]) == pytest.approx(0.004)
    assert float(loaded.header["o1"]) == pytest.approx(0.1)


def test_little_endian_segy_auto_detection(tmp_path: Path) -> None:
    segy_path = _make_segy(tmp_path, endian="little")
    output_path = tmp_path / "little.rsf"

    segy_to_rsf(segy_path, output_path, endian="auto")
    loaded = read_rsf(output_path)
    headers = read_segy_headers(segy_path)

    assert headers.endian == "little"
    assert loaded.header["segy_endian"] == "little"
    np.testing.assert_allclose(loaded.data, _data())


def test_ibm_float_sample_format_round_trip(tmp_path: Path) -> None:
    segy_path = _make_segy(tmp_path, sample_format=1)
    output_path = tmp_path / "ibm.rsf"

    segy_to_rsf(segy_path, output_path)
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, _data(), rtol=1e-5, atol=1e-6)
    assert loaded.header["segy_format"] == "1"


def test_segyread_cli(tmp_path: Path) -> None:
    segy_path = _make_segy(tmp_path)
    output_path = tmp_path / "cli.rsf"
    csv_path = tmp_path / "cli_headers.csv"

    code = segyread_main([str(segy_path), "out=" + str(output_path), "headers=" + str(csv_path)])
    loaded = read_rsf(output_path)

    assert code == 0
    np.testing.assert_allclose(loaded.data, _data())
    assert csv_path.exists()


def test_segywrite_cli(tmp_path: Path) -> None:
    rsf_path = tmp_path / "input.rsf"
    segy_path = tmp_path / "cli.sgy"
    write_rsf(rsf_path, _data(), _header())

    code = segywrite_main([str(rsf_path), "out=" + str(segy_path), "format=5"])
    headers = read_segy_headers(segy_path)

    assert code == 0
    assert headers.samples_per_trace == 5
    assert headers.trace_count == 3
    assert headers.sample_interval_us == 4000


def test_rejects_unknown_trace_header_key(tmp_path: Path) -> None:
    segy_path = _make_segy(tmp_path)

    with pytest.raises(SegyError, match="unknown SEG-Y trace header key"):
        extract_trace_header_table(segy_path, keys=["not_a_key"])


def test_original_sfsegyread_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfsegyread"):
        pytest.skip("Original Madagascar sfsegyread is not installed")

    segy_path = _make_segy(tmp_path)
    original_path = tmp_path / "original.rsf"
    trace_path = tmp_path / "trace.rsf"
    python_path = tmp_path / "python.rsf"

    run_original_madagascar(
        [
            "sfsegyread",
            "tape=input.sgy",
            "out=original.rsf",
            "tfile=trace.rsf",
            "format=5",
            "endian=y",
        ],
        cwd=tmp_path,
        require_program="sfsegyread",
    )
    segy_to_rsf(segy_path, python_path)

    np.testing.assert_allclose(read_rsf(python_path).data, read_rsf(original_path).data, atol=1e-6)

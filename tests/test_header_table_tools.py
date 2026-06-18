from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.generic.header_table import (
    HeaderTableError,
    format_header_table_attr,
    header_table_attr,
    header_table_math,
    header_table_sort,
    read_header_table,
    write_header_table,
)
from pymadagascar.io.rsf import RSFHeader, read_header, read_rsf, write_rsf
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _write_table(path: Path) -> None:
    write_header_table(
        path,
        {
            "offset": np.array([300.0, 100.0, 100.0, 200.0], dtype=np.float32),
            "cdp": np.array([30.0, 10.0, 11.0, 20.0], dtype=np.float32),
            "trace": np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32),
        },
        RSFHeader({"o2": 0.0, "d2": 1.0, "label2": "Input trace"}),
    )


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


def test_header_table_read_write_keys_and_metadata(tmp_path: Path) -> None:
    path = tmp_path / "headers.rsf"
    write_header_table(
        path,
        {"offset": [100, 200, 300], "cdp": [10, 20, 30]},
        RSFHeader({"survey": "demo"}),
    )

    table = read_header_table(path)
    header = read_header(path)

    assert table.keys == ("offset", "cdp")
    assert table.data.dtype == np.dtype("int32")
    assert table.data.shape == (3, 2)
    np.testing.assert_array_equal(table.column("offset"), np.array([100, 200, 300], dtype=np.int32))
    assert header["header_table"] == "pymadagascar-minimal"
    assert header["header_keys"] == "offset,cdp"
    assert header["key1"] == "offset"
    assert header["key2"] == "cdp"
    assert header["survey"] == "demo"
    assert header["label1"] == "Header key"


def test_headerattr_single_multi_all_and_missing_key(tmp_path: Path) -> None:
    path = tmp_path / "headers.rsf"
    _write_table(path)

    single = header_table_attr(path, keys="offset")
    multi = header_table_attr(path, keys=["offset", "cdp"])
    all_stats = header_table_attr(path)
    text = format_header_table_attr(multi)

    assert single == [{"key": "offset", "count": 4, "min": 100.0, "max": 300.0, "mean": 175.0}]
    assert [item["key"] for item in multi] == ["offset", "cdp"]
    assert [item["key"] for item in all_stats] == ["offset", "cdp", "trace"]
    assert text.splitlines() == [
        "key count min max mean",
        "offset 4 100 300 175",
        "cdp 4 10 30 17.75",
    ]

    with pytest.raises(HeaderTableError, match="no key 'missing'"):
        header_table_attr(path, keys="missing")


def test_headerattr_cli_subprocess(tmp_path: Path) -> None:
    path = tmp_path / "headers.rsf"
    _write_table(path)

    result = _run_cli("headerattr", [str(path), "key=offset,cdp"], tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "key count min max mean",
        "offset 4 100 300 175",
        "cdp 4 10 30 17.75",
    ]


def test_headermath_new_key_overwrite_and_input_unchanged(tmp_path: Path) -> None:
    path = tmp_path / "headers.rsf"
    out_new = tmp_path / "math_new.rsf"
    out_overwrite = tmp_path / "math_overwrite.rsf"
    _write_table(path)
    original = read_header_table(path)

    header_table_math(path, out_new, "offset*offset", out_key="offset2")
    new_table = read_header_table(out_new)

    assert new_table.keys == ("offset", "cdp", "trace", "offset2")
    np.testing.assert_allclose(new_table.column("offset2"), original.column("offset") ** 2)
    assert read_header(out_new)["key4"] == "offset2"
    np.testing.assert_allclose(read_header_table(path).data, original.data)

    with pytest.raises(HeaderTableError, match="already exists"):
        header_table_math(path, tmp_path / "bad.rsf", "offset+1", out_key="offset")

    header_table_math(path, out_overwrite, "offset+1", out_key="offset", overwrite=True)
    np.testing.assert_allclose(
        read_header_table(out_overwrite).column("offset"),
        original.column("offset") + 1,
    )


def test_headermath_multivariable_missing_key_and_illegal_expression(tmp_path: Path) -> None:
    path = tmp_path / "headers.rsf"
    out = tmp_path / "math.rsf"
    _write_table(path)

    header_table_math(path, out, "offset + cdp*2", out_key="fold")
    table = read_header_table(out)

    np.testing.assert_allclose(
        table.column("fold"),
        np.array([360.0, 120.0, 122.0, 240.0], dtype=np.float32),
    )

    with pytest.raises(HeaderTableError, match="unknown variable"):
        header_table_math(path, tmp_path / "missing.rsf", "missing+1", out_key="bad")
    with pytest.raises(HeaderTableError, match="unsupported"):
        header_table_math(path, tmp_path / "illegal.rsf", "__import__('os')", out_key="bad")


def test_headermath_cli_subprocess(tmp_path: Path) -> None:
    path = tmp_path / "headers.rsf"
    out = tmp_path / "math_cli.rsf"
    _write_table(path)

    result = _run_cli(
        "headermath",
        [str(path), "out=" + str(out), "output=offset2", "expr=offset^2"],
        tmp_path,
    )

    assert result.returncode == 0, result.stderr
    table = read_header_table(out)
    assert table.keys[-1] == "offset2"
    np.testing.assert_allclose(table.column("offset2"), np.array([90000, 10000, 10000, 40000]))


def test_headersort_ascending_descending_stable_and_metadata(tmp_path: Path) -> None:
    path = tmp_path / "headers.rsf"
    asc = tmp_path / "asc.rsf"
    desc = tmp_path / "desc.rsf"
    _write_table(path)

    header_table_sort(path, asc, "offset")
    header_table_sort(path, desc, "offset", reverse=True)

    asc_table = read_header_table(asc)
    desc_table = read_header_table(desc)
    np.testing.assert_allclose(asc_table.column("offset"), np.array([100, 100, 200, 300]))
    np.testing.assert_allclose(asc_table.column("trace"), np.array([2, 3, 4, 1]))
    np.testing.assert_allclose(desc_table.column("offset"), np.array([300, 200, 100, 100]))
    np.testing.assert_allclose(desc_table.column("trace"), np.array([1, 4, 2, 3]))
    assert asc_table.keys == ("offset", "cdp", "trace")
    assert read_header(asc)["label2"] == "Input trace"

    with pytest.raises(HeaderTableError, match="no key 'missing'"):
        header_table_sort(path, tmp_path / "missing.rsf", "missing")


def test_headersort_cli_subprocess(tmp_path: Path) -> None:
    path = tmp_path / "headers.rsf"
    out = tmp_path / "sort_cli.rsf"
    _write_table(path)

    result = _run_cli("headersort", [str(path), "out=" + str(out), "key=cdp", "reverse=y"], tmp_path)

    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(read_header_table(out).column("cdp"), np.array([30, 20, 11, 10]))


def test_original_sfheaderattr_smoke_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfheaderattr"):
        pytest.skip("Original Madagascar sfheaderattr is not installed")

    path = tmp_path / "headers.rsf"
    _write_table(path)

    result = run_original_madagascar(
        ["sfheaderattr", "segy=n"],
        cwd=tmp_path,
        require_program="sfheaderattr",
        stdin_path=path,
        decode_stdout=True,
    )

    assert result.returncode == 0
    assert "offset" in result.stdout
    assert "mean" in result.stdout


def test_original_sfheadermath_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfheadermath"):
        pytest.skip("Original Madagascar sfheadermath is not installed")

    path = tmp_path / "headers.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    _write_table(path)

    run_original_madagascar(
        [
            "sfheadermath",
            "in=headers.rsf",
            "out=original.rsf",
            "segy=n",
            "key=offset",
            "output=offset*2",
        ],
        cwd=tmp_path,
        require_program="sfheadermath",
    )
    header_table_math(path, python, "offset*2", out_key="offset", overwrite=True)

    np.testing.assert_allclose(read_rsf(original).data, read_rsf(python).data)


def test_original_sfheadersort_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfheadersort"):
        pytest.skip("Original Madagascar sfheadersort is not installed")

    data_path = tmp_path / "data.rsf"
    key_path = tmp_path / "key.rsf"
    original = tmp_path / "original.rsf"
    table_path = tmp_path / "headers.rsf"
    python = tmp_path / "python.rsf"

    write_rsf(data_path, np.array([[10.0], [20.0], [30.0]], dtype=np.float32), RSFHeader({"label1": "Sample"}))
    write_rsf(key_path, np.array([2.0, 1.0, 3.0], dtype=np.float32), RSFHeader({"label1": "Sort key"}))
    write_header_table(
        table_path,
        {"rank": [2.0, 1.0, 3.0], "value": [10.0, 20.0, 30.0]},
    )

    run_original_madagascar(
        ["sfheadersort", "in=data.rsf", "head=key.rsf", "out=original.rsf"],
        cwd=tmp_path,
        require_program="sfheadersort",
    )
    header_table_sort(table_path, python, "rank")

    np.testing.assert_allclose(read_rsf(original).data.reshape(-1), read_header_table(python).column("value"))

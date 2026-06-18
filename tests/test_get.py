from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.cli.get import main as get_main
from pymadagascar.generic import get_header_value as package_get_header_value
from pymadagascar.generic.info import (
    HeaderCastError,
    HeaderKeyError,
    format_header_values,
    get_header_value,
    get_header_values,
)
from pymadagascar.io.rsf import RSFHeader, read_header, write_rsf
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _write_sample(path: Path) -> np.ndarray:
    data = np.arange(6, dtype=np.float32).reshape(2, 3)
    write_rsf(
        path,
        data,
        RSFHeader(
            {
                "o1": 1.0,
                "d1": 0.5,
                "label1": "Time",
                "unit1": "s",
                "o2": 10.0,
                "d2": 2.0,
                "label2": "Trace",
                "unit2": "km",
                "survey": "demo",
            }
        ),
    )
    return data


def _run_get_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not env.get("PYTHONPATH")
        else str(PROJECT_ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    return subprocess.run(
        [sys.executable, "-m", "pymadagascar.cli.get", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_get_header_value_returns_single_key(tmp_path: Path) -> None:
    path = tmp_path / "sample.rsf"
    _write_sample(path)

    assert get_header_value(path, "n1") == "3"
    assert get_header_value(path, "label1") == "Time"
    assert package_get_header_value(path, "n1") == "3"


def test_get_header_values_preserves_key_order(tmp_path: Path) -> None:
    path = tmp_path / "sample.rsf"
    _write_sample(path)

    values = get_header_values(path, ["n2", "n1", "d1"])

    assert list(values.items()) == [("n2", "2"), ("n1", "3"), ("d1", "0.5")]
    assert format_header_values(values) == "n2=2\nn1=3\nd1=0.5"


def test_get_header_value_missing_key_raises(tmp_path: Path) -> None:
    path = tmp_path / "sample.rsf"
    _write_sample(path)

    with pytest.raises(HeaderKeyError, match="header key not found: missing"):
        get_header_value(path, "missing")


def test_get_header_value_default_for_missing_key(tmp_path: Path) -> None:
    path = tmp_path / "sample.rsf"
    _write_sample(path)

    assert get_header_value(path, "missing", default="fallback") == "fallback"
    assert get_header_values(path, ["n1", "missing"], default="0", cast="int")["missing"] == 0


def test_get_header_value_casts_to_int_and_float(tmp_path: Path) -> None:
    path = tmp_path / "sample.rsf"
    _write_sample(path)

    assert get_header_value(path, "n1", cast="int") == 3
    assert get_header_value(path, "d1", cast="float") == pytest.approx(0.5)
    assert get_header_value(path, "d1", cast="string") == "0.5"


def test_get_header_value_cast_error(tmp_path: Path) -> None:
    path = tmp_path / "sample.rsf"
    _write_sample(path)

    with pytest.raises(HeaderCastError, match="cannot cast header key 'label1'"):
        get_header_value(path, "label1", cast="float")


def test_get_header_roundtrip_after_write(tmp_path: Path) -> None:
    path = tmp_path / "roundtrip.rsf"
    data = _write_sample(path)
    header = read_header(path)
    values = get_header_values(path, ["n1", "n2", "data_format", "in"])

    assert header.dimensions == (3, 2)
    assert values["n1"] == str(data.shape[1])
    assert values["n2"] == str(data.shape[0])
    assert values["data_format"] == "native_float"
    assert values["in"].endswith("roundtrip.rsf@")


def test_get_cli_outputs_single_and_multi_key(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "sample.rsf"
    _write_sample(path)

    code = get_main([str(path), "key=n1,d1"])
    captured = capsys.readouterr()

    assert code == 0
    assert captured.out == "n1=3\nd1=0.5\n"


def test_get_cli_supports_default_format_and_parform(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "sample.rsf"
    _write_sample(path)

    code = get_main([str(path), "key=n1,missing", "default=4", "format=int", "parform=n"])
    captured = capsys.readouterr()

    assert code == 0
    assert captured.out == "3\n4\n"


def test_get_cli_reports_missing_key(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "sample.rsf"
    _write_sample(path)

    code = get_main([str(path), "key=missing"])
    captured = capsys.readouterr()

    assert code == 2
    assert "header key not found: missing" in captured.err


def test_get_cli_subprocess_smoke(tmp_path: Path) -> None:
    path = tmp_path / "sample.rsf"
    _write_sample(path)

    result = _run_get_cli([str(path), "key=n1,n2,d1"], tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "n1=3\nn2=2\nd1=0.5\n"


def test_original_sfget_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfget"):
        pytest.skip("Original Madagascar sfget is not installed")

    path = tmp_path / "sample.rsf"
    _write_sample(path)

    original = run_original_madagascar(
        ["sfget", "n1", "d1"],
        cwd=tmp_path,
        require_program="sfget",
        stdin_path=path,
        decode_stdout=True,
    )
    python = _run_get_cli([str(path), "key=n1,d1"], tmp_path)

    assert python.returncode == 0, python.stderr
    assert python.stdout.strip() == original.stdout.strip()

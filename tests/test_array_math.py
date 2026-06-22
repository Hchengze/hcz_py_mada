from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.add import main as add_main
from pymadagascar.cli.clip import main as clip_main
from pymadagascar.cli.normalize import main as normalize_main
from pymadagascar.cli.scale import main as scale_main
from pymadagascar.generic.array_math import (
    ArrayMathError,
    add_rsf,
    clip_rsf,
    normalize_rsf,
    scale_rsf,
)
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


def _header(**updates: object) -> RSFHeader:
    values = {
        "o1": 0.5,
        "d1": 0.25,
        "label1": "Time",
        "unit1": "s",
        "o2": 10.0,
        "d2": 2.0,
        "label2": "Trace",
        "unit2": "km",
    }
    values.update(updates)
    return RSFHeader(values)


def _write(path: Path, data: np.ndarray, header: RSFHeader | None = None) -> None:
    write_rsf(path, data, header or _header())


def test_add_two_rsf_files(tmp_path: Path) -> None:
    first = tmp_path / "first.rsf"
    second = tmp_path / "second.rsf"
    output = tmp_path / "sum.rsf"
    a = np.arange(6, dtype=np.float32).reshape(2, 3)
    b = 10 + np.arange(6, dtype=np.float32).reshape(2, 3)
    _write(first, a)
    _write(second, b)

    result = add_rsf([first, second], output)
    loaded = read_rsf(output)

    assert result.header_path == output.resolve()
    assert loaded.data.dtype == np.float32
    np.testing.assert_array_equal(loaded.data, a + b)


def test_add_inherits_header_from_first_input(tmp_path: Path) -> None:
    first = tmp_path / "first.rsf"
    second = tmp_path / "second.rsf"
    output = tmp_path / "sum.rsf"
    _write(first, np.ones((2, 3), dtype=np.float32), _header(label1="First"))
    _write(second, np.ones((2, 3), dtype=np.float32), _header(label1="Second"))

    add_rsf([first, second], output)
    loaded = read_rsf(output)

    assert loaded.header["label1"] == "First"
    assert loaded.header["unit2"] == "km"
    assert loaded.header.dimensions == (3, 2)


def test_scale_by_constant(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output = tmp_path / "scaled.rsf"
    data = np.arange(6, dtype=np.float32).reshape(2, 3)
    _write(input_path, data)

    scale_rsf(input_path, output, scale=2.0)
    loaded = read_rsf(output)

    assert loaded.data.dtype == np.float32
    np.testing.assert_array_equal(loaded.data, data * 2.0)


def test_scale_promotes_int_to_float(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output = tmp_path / "scaled.rsf"
    data = np.arange(6, dtype=np.int32).reshape(2, 3)
    _write(input_path, data)

    scale_rsf(input_path, output, scale=0.5)
    loaded = read_rsf(output)

    assert loaded.data.dtype == np.float32
    np.testing.assert_array_equal(loaded.data, data.astype(np.float32) * 0.5)


def test_clip_symmetric_threshold(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output = tmp_path / "clipped.rsf"
    data = np.array([-2.0, -0.5, 0.0, 0.5, 3.0], dtype=np.float32)
    _write(input_path, data, _header())

    clip_rsf(input_path, output, clip=1.0)
    loaded = read_rsf(output)

    np.testing.assert_array_equal(
        loaded.data,
        np.array([-1.0, -0.5, 0.0, 0.5, 1.0], dtype=np.float32),
    )


def test_clip_value_and_nonfinite_follow_sfclip_subset(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output = tmp_path / "clipped.rsf"
    data = np.array(
        [-np.inf, -2.0, -0.5, np.nan, 0.5, 3.0, np.inf],
        dtype=np.float32,
    )
    _write(input_path, data, _header())

    clip_rsf(input_path, output, clip=1.0, value=2.5)
    loaded = read_rsf(output)

    np.testing.assert_array_equal(
        loaded.data,
        np.array([-2.5, -2.5, -0.5, 2.5, 0.5, 2.5, 2.5], dtype=np.float32),
    )


def test_normalize_by_max_ignores_nan_and_preserves_nan(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output = tmp_path / "normalized.rsf"
    data = np.array([-2.0, 0.0, 4.0, np.nan], dtype=np.float32)
    _write(input_path, data, _header())

    normalize_rsf(input_path, output, mode="max")
    loaded = read_rsf(output)

    np.testing.assert_array_equal(
        loaded.data,
        np.array([-0.5, 0.0, 1.0, np.nan], dtype=np.float32),
    )


def test_normalize_by_rms(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output = tmp_path / "normalized.rsf"
    data = np.array([3.0, 4.0], dtype=np.float32)
    _write(input_path, data, _header())

    normalize_rsf(input_path, output, mode="rms")
    loaded = read_rsf(output)

    rms = np.sqrt(np.mean(np.square(data)))
    np.testing.assert_allclose(loaded.data, data / rms)


def test_shape_mismatch_raises_clear_error(tmp_path: Path) -> None:
    first = tmp_path / "first.rsf"
    second = tmp_path / "second.rsf"
    output = tmp_path / "sum.rsf"
    _write(first, np.ones((2, 3), dtype=np.float32))
    _write(second, np.ones((2, 4), dtype=np.float32))

    with pytest.raises(ArrayMathError, match="shape mismatch"):
        add_rsf([first, second], output)

    assert not output.exists()


def test_cli_add(tmp_path: Path) -> None:
    first = tmp_path / "first.rsf"
    second = tmp_path / "second.rsf"
    output = tmp_path / "sum.rsf"
    a = np.arange(6, dtype=np.float32).reshape(2, 3)
    b = np.ones((2, 3), dtype=np.float32)
    _write(first, a)
    _write(second, b)

    code = add_main([str(first), str(second), "out=" + str(output)])
    loaded = read_rsf(output)

    assert code == 0
    np.testing.assert_array_equal(loaded.data, a + b)


def test_cli_scale(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output = tmp_path / "scaled.rsf"
    data = np.arange(6, dtype=np.float32)
    _write(input_path, data)

    code = scale_main([str(input_path), "scale=3.0", "out=" + str(output)])
    loaded = read_rsf(output)

    assert code == 0
    np.testing.assert_array_equal(loaded.data, data * 3.0)


def test_cli_clip(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output = tmp_path / "clipped.rsf"
    _write(input_path, np.array([-2.0, 2.0], dtype=np.float32))

    code = clip_main([str(input_path), "clip=1.0", "value=2.0", "out=" + str(output)])
    loaded = read_rsf(output)

    assert code == 0
    np.testing.assert_array_equal(loaded.data, np.array([-2.0, 2.0], dtype=np.float32))


def test_cli_normalize(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output = tmp_path / "normalized.rsf"
    _write(input_path, np.array([-2.0, 4.0], dtype=np.float32))

    code = normalize_main([str(input_path), "mode=max", "out=" + str(output)])
    loaded = read_rsf(output)

    assert code == 0
    np.testing.assert_array_equal(loaded.data, np.array([-0.5, 1.0], dtype=np.float32))


def test_cli_add_requires_explicit_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first = tmp_path / "first.rsf"
    second = tmp_path / "second.rsf"
    _write(first, np.ones(2, dtype=np.float32))
    _write(second, np.ones(2, dtype=np.float32))

    code = add_main([str(first), str(second)])

    assert code == 2
    assert "Missing required parameter: out=" in capsys.readouterr().err


def test_cli_normalize_reports_bad_mode(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_path = tmp_path / "input.rsf"
    output = tmp_path / "bad.rsf"
    _write(input_path, np.ones(2, dtype=np.float32))

    code = normalize_main([str(input_path), "mode=median", "out=" + str(output)])

    assert code == 2
    assert "mode= must be max or rms" in capsys.readouterr().err
    assert not output.exists()


def test_original_sfscale_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfscale"):
        pytest.skip("Original Madagascar sfscale is not installed")

    input_path = tmp_path / "input.rsf"
    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    data = np.arange(6, dtype=np.float32)
    _write(input_path, data)

    run_original_madagascar(
        ["sfscale", "in=input.rsf", "out=original.rsf", "dscale=2.0"],
        cwd=tmp_path,
        require_program="sfscale",
    )
    assert scale_main([str(input_path), "scale=2.0", "out=" + str(python)]) == 0

    assert_rsf_allclose(original, python, ignore_keys={"in"})

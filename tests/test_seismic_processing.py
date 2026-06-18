from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.agc import main as agc_main
from pymadagascar.cli.gain import main as gain_main
from pymadagascar.cli.mute import main as mute_main
from pymadagascar.cli.stack import main as stack_main
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic.agc import AGCError, agc_rsf
from pymadagascar.seismic.gain import gain_rsf
from pymadagascar.seismic.mute import MuteError, mute_rsf
from pymadagascar.seismic.stack import StackError, stack_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


def _header_2d(n1: int = 5, n2: int = 3) -> RSFHeader:
    return RSFHeader(
        {
            "n1": n1,
            "o1": 0.0,
            "d1": 0.1,
            "label1": "Time",
            "unit1": "s",
            "n2": n2,
            "o2": 0.0,
            "d2": 100.0,
            "label2": "Offset",
            "unit2": "m",
        }
    )


def _header_3d(n1: int = 5, n2: int = 3, n3: int = 2) -> RSFHeader:
    header = _header_2d(n1=n1, n2=n2)
    header["n3"] = n3
    header["o3"] = 1.0
    header["d3"] = 1.0
    header["label3"] = "Shot"
    return header


def _local_rms_agc(values: np.ndarray, window: int) -> np.ndarray:
    kernel = np.ones(window, dtype=np.float64)
    power = np.convolve(values.astype(np.float64) ** 2, kernel, mode="same")
    fold = np.convolve(np.ones(values.size, dtype=np.float64), kernel, mode="same")
    rms = np.sqrt(power / fold)
    return np.where(rms > 1e-12, values / rms, 0.0).astype(np.float32)


def test_gain_applies_power_along_time_axis(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "gain.rsf"
    data = np.ones((3, 5), dtype=np.float32)
    write_rsf(input_path, data, _header_2d())

    gain_rsf(input_path, output_path, power=1.0, scale=2.0, axis=1)
    loaded = read_rsf(output_path)

    expected_gain = 2.0 * np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
    np.testing.assert_allclose(loaded.data, np.broadcast_to(expected_gain, data.shape))
    assert loaded.header.dimensions == (5, 3)
    assert loaded.header["label1"] == "Time"


def test_gain_works_on_3d_gather(tmp_path: Path) -> None:
    input_path = tmp_path / "cube.rsf"
    output_path = tmp_path / "gain.rsf"
    data = np.ones((2, 3, 5), dtype=np.float32)
    write_rsf(input_path, data, _header_3d())

    gain_rsf(input_path, output_path, power=0.0, scale=3.0, axis=1)
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, np.full_like(data, 3.0))
    assert loaded.header.dimensions == (5, 3, 2)


def test_agc_normalizes_constant_traces(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "agc.rsf"
    data = np.full((3, 5), 2.0, dtype=np.float32)
    write_rsf(input_path, data, _header_2d())

    agc_rsf(input_path, output_path, rect=0.3, axis=1)
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, np.ones_like(data), atol=1e-6)
    assert loaded.header["d1"] == "0.1"


def test_agc_uses_header_spacing_to_convert_window(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "agc.rsf"
    data = np.array([[1.0, 2.0, 4.0, 8.0, 16.0]], dtype=np.float32)
    write_rsf(input_path, data, _header_2d(n2=1))

    agc_rsf(input_path, output_path, rect=0.2, axis=1)
    loaded = read_rsf(output_path)

    expected = _local_rms_agc(data[0], window=2).reshape(1, 5)
    np.testing.assert_allclose(loaded.data, expected, atol=1e-6)


def test_agc_rejects_complex_input(tmp_path: Path) -> None:
    input_path = tmp_path / "complex.rsf"
    output_path = tmp_path / "agc.rsf"
    write_rsf(input_path, np.ones((2, 5), dtype=np.complex64), _header_2d(n2=2))

    with pytest.raises(AGCError, match="real-valued"):
        agc_rsf(input_path, output_path, rect=0.2)

    assert not output_path.exists()


def test_mute_zeros_samples_before_linear_mute_time(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "mute.rsf"
    data = np.ones((3, 5), dtype=np.float32)
    write_rsf(input_path, data, _header_2d())

    mute_rsf(input_path, output_path, t0=0.1, v=1000.0, axis=1, offset_axis=2)
    loaded = read_rsf(output_path)

    expected = np.array(
        [
            [0.0, 1.0, 1.0, 1.0, 1.0],
            [0.0, 0.0, 1.0, 1.0, 1.0],
            [0.0, 0.0, 0.0, 1.0, 1.0],
        ],
        dtype=np.float32,
    )
    np.testing.assert_allclose(loaded.data, expected)
    assert loaded.header.dimensions == (5, 3)


def test_mute_applies_sine_squared_taper(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "mute.rsf"
    data = np.ones((1, 5), dtype=np.float32)
    write_rsf(input_path, data, _header_2d(n2=1))

    mute_rsf(input_path, output_path, t0=0.1, v=1000.0, taper=0.2)
    loaded = read_rsf(output_path)

    expected = np.array([[0.0, 0.0, 0.5, 1.0, 1.0]], dtype=np.float32)
    np.testing.assert_allclose(loaded.data, expected, atol=1e-6)


def test_mute_rejects_bad_velocity(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.ones((2, 5), dtype=np.float32), _header_2d(n2=2))

    with pytest.raises(MuteError, match="v= must be positive"):
        mute_rsf(input_path, output_path, t0=0.0, v=0.0)


def test_stack_axis2_updates_header(tmp_path: Path) -> None:
    input_path = tmp_path / "gather.rsf"
    output_path = tmp_path / "stack.rsf"
    data = np.array(
        [
            [1.0, 2.0, 3.0, 4.0],
            [3.0, 4.0, 5.0, 6.0],
            [0.0, 0.0, 0.0, 0.0],
        ],
        dtype=np.float32,
    )
    write_rsf(input_path, data, _header_2d(n1=4, n2=3))

    stack_rsf(input_path, output_path, axis=2)
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, np.array([2.0, 3.0, 4.0, 5.0], dtype=np.float32))
    assert loaded.header.dimensions == (4,)
    assert loaded.header["label1"] == "Time"
    assert "n2" not in loaded.header


def test_stack_3d_axis2_preserves_other_axes(tmp_path: Path) -> None:
    input_path = tmp_path / "cube.rsf"
    output_path = tmp_path / "stack.rsf"
    data = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    write_rsf(input_path, data, _header_3d(n1=4, n2=3, n3=2))

    stack_rsf(input_path, output_path, axis=2, nonzero=False)
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, np.mean(data, axis=1))
    assert loaded.header.dimensions == (4, 2)
    assert loaded.header["label1"] == "Time"
    assert loaded.header["label2"] == "Shot"


def test_stack_rms_mode(tmp_path: Path) -> None:
    input_path = tmp_path / "gather.rsf"
    output_path = tmp_path / "rms.rsf"
    data = np.array([[3.0, 4.0], [0.0, 0.0], [4.0, 3.0]], dtype=np.float32)
    write_rsf(input_path, data, _header_2d(n1=2, n2=3))

    stack_rsf(input_path, output_path, axis=2, mode="rms")
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, np.array([np.sqrt(12.5), np.sqrt(12.5)], dtype=np.float32))


def test_stack_rejects_bad_mode(tmp_path: Path) -> None:
    input_path = tmp_path / "gather.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.ones((2, 5), dtype=np.float32), _header_2d(n2=2))

    with pytest.raises(StackError, match="mode="):
        stack_rsf(input_path, output_path, mode="median")


def test_gain_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "gain.rsf"
    data = np.ones((2, 5), dtype=np.float32)
    write_rsf(input_path, data, _header_2d(n2=2))

    code = gain_main([str(input_path), "out=" + str(output_path), "power=1", "scale=2"])
    loaded = read_rsf(output_path)

    assert code == 0
    np.testing.assert_allclose(loaded.data[0], np.array([0.2, 0.4, 0.6, 0.8, 1.0], dtype=np.float32))


def test_agc_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "agc.rsf"
    write_rsf(input_path, np.full((2, 5), 2.0, dtype=np.float32), _header_2d(n2=2))

    code = agc_main([str(input_path), "out=" + str(output_path), "rect=0.3"])
    loaded = read_rsf(output_path)

    assert code == 0
    np.testing.assert_allclose(loaded.data, 1.0, atol=1e-6)


def test_mute_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "mute.rsf"
    write_rsf(input_path, np.ones((3, 5), dtype=np.float32), _header_2d())

    code = mute_main([str(input_path), "out=" + str(output_path), "t0=0.1", "v=1000"])
    loaded = read_rsf(output_path)

    assert code == 0
    np.testing.assert_allclose(loaded.data[0], np.array([0.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float32))


def test_stack_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "stack.rsf"
    data = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    write_rsf(input_path, data, _header_2d(n1=2, n2=2))

    code = stack_main([str(input_path), "out=" + str(output_path), "axis=2", "nonzero=n"])
    loaded = read_rsf(output_path)

    assert code == 0
    np.testing.assert_allclose(loaded.data, np.array([2.0, 3.0], dtype=np.float32))
    assert loaded.header.dimensions == (2,)


def test_cli_reports_missing_gain_power(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.ones((2, 5), dtype=np.float32), _header_2d(n2=2))

    code = gain_main([str(input_path), "out=" + str(output_path)])

    assert code == 2
    assert "Missing required parameter: power=" in capsys.readouterr().err


def test_original_sfpow_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfpow"):
        pytest.skip("Original Madagascar sfpow is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    data = np.ones((2, 5), dtype=np.float32)
    write_rsf(input_path, data, _header_2d(n2=2))

    run_original_madagascar(
        ["sfpow", "in=input.rsf", "out=original.rsf", "pow1=1"],
        cwd=tmp_path,
        require_program="sfpow",
    )
    gain_rsf(input_path, python_path, power=1.0, axis=1)

    np.testing.assert_allclose(
        read_rsf(original_path).data.ravel(),
        read_rsf(python_path).data.ravel(),
        rtol=1e-6,
        atol=1e-6,
    )


def test_original_sfstack_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfstack"):
        pytest.skip("Original Madagascar sfstack is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    data = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    write_rsf(input_path, data, _header_2d(n1=2, n2=2))

    run_original_madagascar(
        ["sfstack", "in=input.rsf", "out=original.rsf", "axis=2"],
        cwd=tmp_path,
        require_program="sfstack",
    )
    stack_rsf(input_path, python_path, axis=2)

    np.testing.assert_allclose(
        read_rsf(original_path).data.ravel(),
        read_rsf(python_path).data.ravel(),
        rtol=1e-6,
        atol=1e-6,
    )

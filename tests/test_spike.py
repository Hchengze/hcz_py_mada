from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.spike import main as spike_main
from pymadagascar.core.axis import Axis
from pymadagascar.generic.spike import spike
from pymadagascar.io.rsf import read_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


def test_api_1d_single_spike() -> None:
    result = spike((5,), locations=(3,))

    np.testing.assert_array_equal(
        result.data,
        np.array([0, 0, 1, 0, 0], dtype=np.float32),
    )
    assert result.header.dimensions == (5,)
    assert result.header["data_format"] == "native_float"


def test_api_locations_are_one_based() -> None:
    result = spike((3,), locations=1)

    np.testing.assert_array_equal(result.data, np.array([1, 0, 0], dtype=np.float32))


def test_api_2d_single_spike_uses_rsf_axis_order() -> None:
    result = spike((4, 3), locations=(2, 3))
    expected = np.zeros((3, 4), dtype=np.float32)
    expected[2, 1] = 1.0

    assert result.data.shape == (3, 4)
    np.testing.assert_array_equal(result.data, expected)
    assert result.header.dimensions == (4, 3)


def test_api_3d_single_spike() -> None:
    result = spike((4, 3, 2), locations=(4, 2, 1))
    expected = np.zeros((2, 3, 4), dtype=np.float32)
    expected[0, 1, 3] = 1.0

    np.testing.assert_array_equal(result.data, expected)
    assert result.header.dimensions == (4, 3, 2)


def test_api_multiple_spikes_and_magnitudes() -> None:
    result = spike(
        (6,),
        locations=[2, 4, 6],
        magnitudes=[2.0, -1.0, 0.5],
    )

    np.testing.assert_array_equal(
        result.data,
        np.array([0, 2, 0, -1, 0, 0.5], dtype=np.float32),
    )


def test_api_default_zero_background_when_no_locations() -> None:
    result = spike((4,))

    np.testing.assert_array_equal(result.data, np.zeros(4, dtype=np.float32))


def test_api_header_defaults_match_sfspike() -> None:
    result = spike((5, 2))

    assert result.header["n1"] == "5"
    assert result.header["n2"] == "2"
    assert result.header["o1"] == "0"
    assert result.header["d1"] == "0.004"
    assert result.header["label1"] == "Time"
    assert result.header["unit1"] == "s"
    assert result.header["o2"] == "0"
    assert result.header["d2"] == "0.1"
    assert result.header["label2"] == "Distance"
    assert result.header["unit2"] == "km"


def test_api_custom_axes_and_dtype() -> None:
    result = spike(
        (4,),
        locations=2,
        magnitudes=3.0,
        axes=[Axis(n=4, o=10.0, d=2.5, label="Depth", unit="m")],
        dtype="float64",
    )

    assert result.data.dtype == np.float64
    assert result.header["data_format"] == "native_double"
    assert result.header["esize"] == "8"
    assert result.header["o1"] == "10"
    assert result.header["d1"] == "2.5"
    assert result.header["label1"] == "Depth"
    assert result.header["unit1"] == "m"
    np.testing.assert_array_equal(result.data, np.array([0, 3, 0, 0], dtype=np.float64))


def test_api_rejects_out_of_bounds_location() -> None:
    with pytest.raises(ValueError, match="outside"):
        spike((4,), locations=5)


def test_cli_writes_output_rsf(tmp_path: Path) -> None:
    output = tmp_path / "spike.rsf"

    code = spike_main(["n1=5", "k1=3", "out=" + str(output)])
    result = read_rsf(output)

    assert code == 0
    np.testing.assert_array_equal(result.data, np.array([0, 0, 1, 0, 0], dtype=np.float32))
    assert result.header["d1"] == "0.004"


def test_cli_multiple_spikes_and_header_params(tmp_path: Path) -> None:
    output = tmp_path / "panel.rsf"

    code = spike_main(
        [
            "n1=4",
            "n2=3",
            "nsp=2",
            "k1=2,4",
            "k2=1,3",
            "mag=2,-1",
            "o1=1.5",
            "d1=0.5",
            "label1=Depth",
            "unit1=m",
            "out=" + str(output),
        ]
    )
    result = read_rsf(output)
    expected = np.zeros((3, 4), dtype=np.float32)
    expected[0, 1] = 2.0
    expected[2, 3] = -1.0

    assert code == 0
    np.testing.assert_array_equal(result.data, expected)
    assert result.header["o1"] == "1.5"
    assert result.header["d1"] == "0.5"
    assert result.header["label1"] == "Depth"
    assert result.header["unit1"] == "m"


def test_cli_missing_output_reports_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = spike_main(["n1=4", "k1=2"])

    assert code == 2
    assert "Missing required parameter: out=" in capsys.readouterr().err


def test_cli_original_sfspike_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfspike"):
        pytest.skip("Original Madagascar sfspike is not installed")

    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    run_original_madagascar(
        ["sfspike", "n1=5", "k1=3", "out=original.rsf"],
        cwd=tmp_path,
        require_program="sfspike",
    )
    assert spike_main(["n1=5", "k1=3", "out=" + str(python)]) == 0

    assert_rsf_allclose(original, python, ignore_keys={"in"})

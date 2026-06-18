from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.conv import main as conv_main
from pymadagascar.cli.corr import main as corr_main
from pymadagascar.cli.xcorr import main as xcorr_main
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.signal.convolution import (
    ConvolutionError,
    convolve_rsf,
    correlate_rsf,
    fft_convolve,
    xcorr_rsf,
    xcorr_traces,
)
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


def _header_1d(n1: int = 4, o1: float = 0.0, d1: float = 1.0) -> RSFHeader:
    return RSFHeader({"n1": n1, "o1": o1, "d1": d1, "label1": "Time", "unit1": "s"})


def _header_2d(n1: int = 4, n2: int = 2, o1: float = 0.0, d1: float = 1.0) -> RSFHeader:
    return RSFHeader(
        {
            "n1": n1,
            "o1": o1,
            "d1": d1,
            "label1": "Time",
            "unit1": "s",
            "n2": n2,
            "o2": 10.0,
            "d2": 2.0,
            "label2": "Trace",
        }
    )


def test_simple_convolution_full(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    filter_path = tmp_path / "filter.rsf"
    output_path = tmp_path / "conv.rsf"
    data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    kernel = np.array([1.0, 1.0], dtype=np.float32)
    write_rsf(input_path, data, _header_1d(n1=3, o1=2.0))
    write_rsf(filter_path, kernel, _header_1d(n1=2, o1=-1.0))

    convolve_rsf(input_path, filter_path, output_path, mode="full", method="direct")
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, np.convolve(data, kernel, mode="full"))
    assert loaded.header.dimensions == (4,)
    assert loaded.header["o1"] == "1"
    assert loaded.header["d1"] == "1"
    assert loaded.header["label1"] == "Time"


def test_simple_correlation_full(tmp_path: Path) -> None:
    first_path = tmp_path / "first.rsf"
    second_path = tmp_path / "second.rsf"
    output_path = tmp_path / "corr.rsf"
    first = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    second = np.array([0.0, 1.0], dtype=np.float32)
    write_rsf(first_path, first, _header_1d(n1=3, o1=0.0))
    write_rsf(second_path, second, _header_1d(n1=2, o1=0.0))

    correlate_rsf(first_path, second_path, output_path, mode="full", method="direct")
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, np.correlate(first, second, mode="full"))
    assert loaded.header.dimensions == (4,)
    assert loaded.header["o1"] == "-1"


def test_delta_convolution_returns_shifted_signal(tmp_path: Path) -> None:
    input_path = tmp_path / "delta.rsf"
    filter_path = tmp_path / "signal.rsf"
    output_path = tmp_path / "conv.rsf"
    delta = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    signal = np.array([2.0, 3.0], dtype=np.float32)
    write_rsf(input_path, delta, _header_1d(n1=3))
    write_rsf(filter_path, signal, _header_1d(n1=2))

    convolve_rsf(input_path, filter_path, output_path, mode="full", method="direct")
    loaded = read_rsf(output_path)

    np.testing.assert_allclose(loaded.data, np.convolve(delta, signal, mode="full"))


@pytest.mark.parametrize("mode", ["full", "same", "valid"])
def test_fft_convolve_matches_numpy(mode: str) -> None:
    rng = np.random.default_rng(1234)
    data = rng.normal(size=32).astype(np.float32)
    kernel = rng.normal(size=11).astype(np.float32)

    np.testing.assert_allclose(fft_convolve(data, kernel, mode=mode), np.convolve(data, kernel, mode=mode), atol=1e-5)


def test_rsf_fft_and_direct_convolution_match(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    filter_path = tmp_path / "filter.rsf"
    direct_path = tmp_path / "direct.rsf"
    fft_path = tmp_path / "fft.rsf"
    data = np.linspace(-1.0, 1.0, 64, dtype=np.float32)
    kernel = np.hanning(17).astype(np.float32)
    write_rsf(input_path, data, _header_1d(n1=data.size, d1=0.004))
    write_rsf(filter_path, kernel, _header_1d(n1=kernel.size, d1=0.004))

    convolve_rsf(input_path, filter_path, direct_path, mode="same", method="direct")
    convolve_rsf(input_path, filter_path, fft_path, mode="same", method="fft")

    np.testing.assert_allclose(read_rsf(fft_path).data, read_rsf(direct_path).data, atol=1e-5)


def test_multitrace_convolution_with_one_kernel(tmp_path: Path) -> None:
    input_path = tmp_path / "gather.rsf"
    filter_path = tmp_path / "filter.rsf"
    output_path = tmp_path / "conv.rsf"
    data = np.array([[1.0, 2.0, 4.0, 8.0], [0.0, 1.0, 0.0, -1.0]], dtype=np.float32)
    kernel = np.array([1.0, -1.0], dtype=np.float32)
    write_rsf(input_path, data, _header_2d())
    write_rsf(filter_path, kernel, _header_1d(n1=2))

    convolve_rsf(input_path, filter_path, output_path, mode="same", axis=1)
    loaded = read_rsf(output_path)

    expected = np.stack([np.convolve(trace, kernel, mode="same") for trace in data])
    np.testing.assert_allclose(loaded.data, expected)
    assert loaded.header.dimensions == (4, 2)
    assert loaded.header["label2"] == "Trace"


def test_multitrace_pairwise_correlation(tmp_path: Path) -> None:
    first_path = tmp_path / "first.rsf"
    second_path = tmp_path / "second.rsf"
    output_path = tmp_path / "corr.rsf"
    first = np.array([[1.0, 2.0, 0.0, 0.0], [0.0, 1.0, 2.0, 1.0]], dtype=np.float32)
    second = np.array([[1.0, 0.0], [1.0, -1.0]], dtype=np.float32)
    write_rsf(first_path, first, _header_2d(n1=4, n2=2))
    write_rsf(second_path, second, _header_2d(n1=2, n2=2))

    correlate_rsf(first_path, second_path, output_path, mode="full", axis=1)
    loaded = read_rsf(output_path)

    expected = np.stack([np.correlate(a, b, mode="full") for a, b in zip(first, second)])
    np.testing.assert_allclose(loaded.data, expected)
    assert loaded.header.dimensions == (5, 2)


def test_xcorr_traces_multitrace() -> None:
    data = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)

    result = xcorr_traces(data, axis=-1, mode="full", method="direct")

    expected = np.stack([np.correlate(trace, trace, mode="full") for trace in data])
    np.testing.assert_allclose(result, expected)


def test_xcorr_rsf_updates_lag_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "xcorr.rsf"
    data = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    write_rsf(input_path, data, _header_2d(n1=3, n2=2, d1=0.5))

    xcorr_rsf(input_path, output_path, mode="full", axis=1)
    loaded = read_rsf(output_path)

    assert loaded.header.dimensions == (5, 2)
    assert loaded.header["o1"] == "-1"
    assert loaded.header["d1"] == "0.5"
    assert loaded.header["label1"] == "Lag"


def test_valid_mode_header_start(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    filter_path = tmp_path / "filter.rsf"
    output_path = tmp_path / "valid.rsf"
    write_rsf(input_path, np.arange(5, dtype=np.float32), _header_1d(n1=5, o1=10.0, d1=2.0))
    write_rsf(filter_path, np.ones(3, dtype=np.float32), _header_1d(n1=3, o1=0.0, d1=2.0))

    convolve_rsf(input_path, filter_path, output_path, mode="valid")
    loaded = read_rsf(output_path)

    assert loaded.header.dimensions == (3,)
    assert loaded.header["o1"] == "14"


def test_sampling_mismatch_rejected(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    filter_path = tmp_path / "filter.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.ones(5, dtype=np.float32), _header_1d(n1=5, d1=1.0))
    write_rsf(filter_path, np.ones(3, dtype=np.float32), _header_1d(n1=3, d1=2.0))

    with pytest.raises(ConvolutionError, match="sampling mismatch"):
        convolve_rsf(input_path, filter_path, output_path)

    assert not output_path.exists()


def test_conv_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    filter_path = tmp_path / "filter.rsf"
    output_path = tmp_path / "conv.rsf"
    data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    kernel = np.array([1.0, 1.0], dtype=np.float32)
    write_rsf(input_path, data, _header_1d(n1=3))
    write_rsf(filter_path, kernel, _header_1d(n1=2))

    code = conv_main([str(input_path), str(filter_path), "out=" + str(output_path), "mode=full"])
    loaded = read_rsf(output_path)

    assert code == 0
    np.testing.assert_allclose(loaded.data, np.convolve(data, kernel, mode="full"))


def test_corr_cli(tmp_path: Path) -> None:
    first_path = tmp_path / "first.rsf"
    second_path = tmp_path / "second.rsf"
    output_path = tmp_path / "corr.rsf"
    first = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    second = np.array([0.0, 1.0], dtype=np.float32)
    write_rsf(first_path, first, _header_1d(n1=3))
    write_rsf(second_path, second, _header_1d(n1=2))

    code = corr_main([str(first_path), str(second_path), "out=" + str(output_path)])
    loaded = read_rsf(output_path)

    assert code == 0
    np.testing.assert_allclose(loaded.data, np.correlate(first, second, mode="full"))


def test_xcorr_cli(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "xcorr.rsf"
    data = np.array([1.0, 0.0, 2.0], dtype=np.float32)
    write_rsf(input_path, data, _header_1d(n1=3))

    code = xcorr_main([str(input_path), "out=" + str(output_path), "axis=1"])
    loaded = read_rsf(output_path)

    assert code == 0
    np.testing.assert_allclose(loaded.data, np.correlate(data, data, mode="full"))


def test_cli_reports_bad_mode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "input.rsf"
    filter_path = tmp_path / "filter.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.ones(3, dtype=np.float32), _header_1d(n1=3))
    write_rsf(filter_path, np.ones(2, dtype=np.float32), _header_1d(n1=2))

    code = conv_main([str(input_path), str(filter_path), "out=" + str(output_path), "mode=center"])

    assert code == 2
    assert "mode= must be full, same, or valid" in capsys.readouterr().err
    assert not output_path.exists()


def test_original_sfconv_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfconv"):
        pytest.skip("Original Madagascar sfconv is not installed")

    input_path = tmp_path / "input.rsf"
    filter_path = tmp_path / "filter.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    kernel = np.array([1.0, 1.0], dtype=np.float32)
    write_rsf(input_path, data, _header_1d(n1=3))
    write_rsf(filter_path, kernel, _header_1d(n1=2))

    run_original_madagascar(
        ["sfconv", "in=input.rsf", "filt=filter.rsf", "out=original.rsf", "trans=y"],
        cwd=tmp_path,
        require_program="sfconv",
    )
    convolve_rsf(input_path, filter_path, python_path, mode="full", method="direct")

    np.testing.assert_allclose(read_rsf(python_path).data, read_rsf(original_path).data, atol=1e-5)

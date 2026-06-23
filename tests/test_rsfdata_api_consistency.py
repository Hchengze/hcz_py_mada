from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

import pymadagascar
from pymadagascar import RSFData
from pymadagascar.io.rsf import RSFHeader, write_rsf


EXPECTED_CHAIN_METHODS = {
    "costaper",
    "threshold",
    "spectra",
    "fft1",
    "cosft",
    "spectra2",
    "envelope",
    "linear",
    "remap1",
    "spline",
    "t2warp",
    "slice",
    "max1",
    "matmult",
    "match",
    "linefit",
    "avo",
    "fold",
    "ai2refl",
    "nmo",
    "halfint",
    "moveout",
    "cos2ang",
    "isin2ang",
    "map2coh",
    "autocorr",
    "convolve",
    "cconv",
    "envcorr",
    "shifts",
    "stacks",
    "deriv",
    "causint",
    "integral",
    "clip2",
    "mutter",
    "diff",
    "abs",
    "sign",
    "sqrt",
    "log",
    "exp",
    "pow",
    "histogram",
    "quantile",
    "mean",
    "rms",
    "var",
    "std",
    "median",
    "range_stats",
    "isnan",
    "fillnan",
    "demean",
    "detrend",
    "decimate",
    "bandstop",
    "notch",
    "localrms",
    "noise",
    "boxsmooth",
    "smooth",
    "laplac",
    "trapez",
    "pad",
    "spray",
    "windowfunc",
    "psd",
    "csd",
    "coherence",
    "spectrogram",
    "snr",
    "welch",
    "welchcsd",
    "transfer",
    "whiten",
    "specnorm",
    "freqattr",
    "firfilter",
    "filtfilt",
    "bandenergy",
    "filterbank",
}


def _header_1d(n1: int, *, d1: float = 0.5) -> RSFHeader:
    return RSFHeader(
        {
            "n1": n1,
            "o1": 0.0,
            "d1": d1,
            "label1": "Time",
            "unit1": "s",
        }
    )


def _header_2d(n1: int, n2: int) -> RSFHeader:
    header = _header_1d(n1)
    header["n2"] = n2
    header["o2"] = -100.0
    header["d2"] = 100.0
    header["label2"] = "Offset"
    header["unit2"] = "m"
    return header


def test_expected_rsfdata_chain_methods_exist() -> None:
    missing = sorted(name for name in EXPECTED_CHAIN_METHODS if not callable(getattr(RSFData, name, None)))
    assert missing == []


def test_all_declared_public_exports_resolve() -> None:
    missing = sorted(name for name in pymadagascar.__all__ if not hasattr(pymadagascar, name))
    assert missing == []


def test_default_and_inplace_behavior_are_consistent() -> None:
    data = np.array([-1.0, 0.25, 2.0], dtype=np.float32)
    original = RSFData(data, _header_1d(data.size))

    copied = original.threshold(value=0.5)
    np.testing.assert_array_equal(original.numpy(), data)
    assert copied is not original

    returned = original.threshold(value=0.5, inplace=True)
    assert returned is original
    np.testing.assert_array_equal(original.numpy(), np.array([-1.0, 0.0, 2.0], dtype=np.float32))
    assert original.path is None


def test_inplace_shape_change_updates_header_and_returns_self() -> None:
    data = np.arange(6, dtype=np.float32).reshape(2, 3)
    rsf = RSFData(data, _header_2d(n1=3, n2=2))

    returned = rsf.linear(axis=1, n=5, d=0.25, inplace=True)

    assert returned is rsf
    assert rsf.shape == (2, 5)
    assert rsf.header.dimensions == (5, 2)
    assert rsf.header["d1"] == "0.25"


@pytest.mark.parametrize("operand_kind", ["rsfdata", "ndarray", "list", "path"])
@pytest.mark.parametrize(
    "operation",
    ["convolve", "envcorr", "diff", "csd", "coherence", "welchcsd", "transfer"],
)
def test_double_input_methods_accept_consistent_operand_types(
    operation: str,
    operand_kind: str,
    tmp_path: Path,
) -> None:
    data = np.array([0.0, 1.0, 3.0, 1.0, 0.0], dtype=np.float32)
    other = (
        np.array([0.25, 0.5, 0.25], dtype=np.float32)
        if operation == "convolve"
        else data.copy()
    )
    source = RSFData(data, _header_1d(data.size))
    operand: object
    if operand_kind == "rsfdata":
        operand = RSFData(other, _header_1d(other.size))
    elif operand_kind == "ndarray":
        operand = other.copy()
    elif operand_kind == "list":
        operand = other.tolist()
    else:
        operand_path = tmp_path / f"{operation}_operand.rsf"
        write_rsf(operand_path, other, _header_1d(other.size))
        operand = operand_path

    if operation == "convolve":
        result = source.convolve(operand, mode="same")
        expected = source.convolve(other, mode="same")
    elif operation == "envcorr":
        result = source.envcorr(operand, mode="same")
        expected = source.envcorr(other, mode="same")
    elif operation == "csd":
        result = source.csd(operand, window="boxcar")
        expected = source.csd(other, window="boxcar")
    elif operation == "coherence":
        result = source.coherence(operand, window="boxcar", nperseg=4, noverlap=2)
        expected = source.coherence(other, window="boxcar", nperseg=4, noverlap=2)
    elif operation == "welchcsd":
        result = source.welchcsd(
            operand,
            window="boxcar",
            nperseg=4,
            noverlap=2,
        )
        expected = source.welchcsd(
            other,
            window="boxcar",
            nperseg=4,
            noverlap=2,
        )
    elif operation == "transfer":
        result = source.transfer(
            operand,
            window="boxcar",
            nperseg=4,
            noverlap=2,
        )
        expected = source.transfer(
            other,
            window="boxcar",
            nperseg=4,
            noverlap=2,
        )
    else:
        result = source.diff(operand, metric="rms")
        expected = source.diff(other, metric="rms")

    assert isinstance(result, RSFData)
    np.testing.assert_allclose(result.numpy(), expected.numpy(), atol=1e-6)
    np.testing.assert_array_equal(source.numpy(), data)


def test_double_input_methods_reject_missing_paths_and_scalars(tmp_path: Path) -> None:
    rsf = RSFData(np.ones(4, dtype=np.float32), _header_1d(4))

    with pytest.raises(FileNotFoundError, match="second operand"):
        rsf.convolve(tmp_path / "missing.rsf")
    with pytest.raises(ValueError, match="non-scalar"):
        rsf.diff(1.0)


def test_shape_preserving_contract() -> None:
    data = np.arange(10, dtype=np.float32).reshape(2, 5)
    header = _header_2d(n1=5, n2=2)
    rsf = RSFData(data, header)

    results = [
        rsf.costaper(widths={1: 1}),
        rsf.threshold(value=1.0),
        rsf.envelope(axis=1),
        rsf.shifts(shift=1, axis=1),
        rsf.deriv(axis=1),
        rsf.causint(axis=1),
        rsf.integral(axis=1),
        rsf.clip2(max_value=4.0),
        rsf.mutter(v=1000.0),
        rsf.abs(),
        rsf.sign(),
        rsf.exp(),
        rsf.pow(2.0),
        rsf.fillnan(0.0, mode="nonfinite"),
        rsf.isnan(mode="nonfinite"),
        rsf.demean(axis=1),
        rsf.detrend(axis=1),
        rsf.bandstop(axis=1, fmin=0.2, fmax=0.4),
        rsf.notch(axis=1, f0=0.3, width=0.2),
        rsf.localrms(axis=1, rect=3),
        rsf.noise(var=0.0, mean=0.0, seed=1),
        rsf.boxsmooth(rect=2, axes=1),
        rsf.smooth(rect=2, axes=1),
        rsf.laplac(axes=1, spacing_from_header=False),
        rsf.trapez(axis=1, frequency=(0.05, 0.1, 0.4, 0.45)),
        rsf.windowfunc(axis=1, kind="hann"),
        rsf.whiten(axis=1),
        rsf.specnorm(axis=1),
        rsf.firfilter([0.25, 0.5, 0.25], axis=1),
        rsf.filtfilt([0.25, 0.5, 0.25], axis=1, pad=False),
    ]

    for result in results:
        assert result.shape == rsf.shape
        assert result.header.dimensions == rsf.header.dimensions
        assert result.header["label1"] == "Time"
        assert result.header["label2"] == "Offset"


def test_axis_changing_and_removing_header_contracts() -> None:
    data = np.arange(15, dtype=np.float32).reshape(3, 5)
    rsf = RSFData(data, _header_2d(n1=5, n2=3))

    spectrum = rsf.spectra(axis=1, average=False)
    fft1 = rsf.fft1(axis=1)
    cosft = rsf.cosft(axis=1)
    spectrum2 = rsf.spectra2(axes=(1, 2), average=False)
    density = rsf.psd(axis=1, average=False)
    welch_density = rsf.welch(
        axis=1,
        nperseg=4,
        noverlap=2,
        average=False,
    )
    time_frequency = rsf.spectrogram(axis=1, nperseg=4, noverlap=2)
    attributes = rsf.freqattr(axis=1)
    band_energy = rsf.bandenergy(axis=1, bands="0.1:0.4", average=False)
    resampled = rsf.linear(axis=1, n=7, d=0.25)
    remapped = rsf.remap1(axis=1, n=7, d=0.25)
    splined = rsf.spline(axis=1, n=7, d=0.25)
    warped = rsf.t2warp(axis=1, pad=7)
    decimated = rsf.decimate(2, axis=1, anti_alias=False)
    sliced = rsf.slice(axis=2, index=1)
    picked = rsf.max1(axis=1, mode="coord")
    stacked = rsf.stacks(axis=2, statistic="mean")

    assert spectrum.shape == (3, 3)
    assert spectrum.header["label1"] == "Frequency"
    assert spectrum.header["unit1"] == "Hz"
    assert fft1.shape == (3, 3)
    assert fft1.header["label1"] == "Frequency"
    assert cosft.shape == rsf.shape
    assert cosft.header["label1"] == "Frequency"
    assert spectrum2.shape == (3, 3)
    assert spectrum2.header["label1"] == "Frequency"
    assert spectrum2.header["label2"] == "Wavenumber"
    assert density.shape == (3, 3)
    assert density.header["label1"] == "Frequency"
    assert welch_density.shape == (3, 3)
    assert welch_density.header["label1"] == "Frequency"
    assert time_frequency.header["label1"] == "Frequency"
    assert time_frequency.header["label2"] == "Window time"
    assert attributes.shape == (3, 3)
    assert band_energy.shape == (3, 1)
    assert attributes.header["frequency_attributes"] == "dominant,centroid,bandwidth"
    assert resampled.shape == (3, 7)
    assert resampled.header.dimensions == (7, 3)
    assert remapped.shape == (3, 7)
    assert remapped.header.dimensions == (7, 3)
    assert remapped.header["remap1_order"] == "1"
    assert splined.shape == (3, 7)
    assert splined.header["spline_boundary"] == "natural"
    assert warped.shape == (3, 7)
    assert warped.header["n1_t2warp"] == "5"
    assert decimated.shape == (3, 3)
    assert decimated.header.dimensions == (3, 3)
    assert decimated.header["d1"] == "1"
    assert sliced.shape == (5,)
    assert sliced.header.dimensions == (5,)
    assert picked.shape == (3,)
    assert picked.header.dimensions == (3,)
    assert stacked.shape == (5,)
    assert stacked.header.dimensions == (5,)


def test_dtype_contracts_and_scalar_diff() -> None:
    complex_data = np.array([1 + 1j, 0.1 + 0.1j], dtype=np.complex64)
    thresholded = RSFData(complex_data, _header_1d(2)).threshold(value=0.5)
    assert thresholded.dtype == np.dtype("complex64")

    real64 = RSFData(np.arange(8, dtype=np.float64), _header_1d(8))
    assert real64.envelope().dtype == np.dtype("float64")
    metric = real64.diff(real64.copy(), metric="max_abs")
    assert metric.shape == (1,)
    assert metric.dtype == np.dtype("float64")
    assert metric.header["label1"] == "Difference"
    assert metric.header["difference_metric"] == "max_abs"


def test_statistics_shape_header_and_dtype_contracts() -> None:
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    rsf = RSFData(data, _header_2d(n1=4, n2=3))

    global_mean = rsf.mean()
    axis_mean = rsf.mean(axis=1)
    axis_range = rsf.range_stats(axis=1)

    assert global_mean.shape == (1,)
    assert global_mean.dtype == np.dtype("float64")
    assert global_mean.header["label1"] == "Mean"
    assert axis_mean.shape == (3,)
    assert axis_mean.header["label1"] == "Offset"
    assert axis_range.shape == (3, 2)
    assert axis_range.header.dimensions == (2, 3)
    assert axis_range.header["range_fields"] == "min,max"


def test_scalar_diff_inplace_follows_general_inplace_contract() -> None:
    rsf = RSFData(np.arange(4, dtype=np.float32), _header_1d(4))

    returned = rsf.diff(rsf.copy(), inplace=True)

    assert returned is rsf
    assert rsf.shape == (1,)
    np.testing.assert_array_equal(rsf.numpy(), np.array([0.0], dtype=np.float64))

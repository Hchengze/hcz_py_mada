"""Small-data spectral QC and window-function helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Sequence

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


WindowKind = Literal["hann", "hamming", "blackman", "bartlett", "boxcar", "cosine"]
SpectralScaling = Literal["density", "spectrum"]
SpectrogramMode = Literal["magnitude", "power"]
SNRUnit = Literal["db", "ratio"]
TransferMethod = Literal["H1", "H2"]
SpectralNormalizeMode = Literal["unit_rms", "unit_max"]
FrequencyAttribute = Literal["dominant", "centroid", "bandwidth"]
SampleWindow = slice | tuple[int, int] | Sequence[int]


class SpectralQCError(ValueError):
    """Raised when a spectral-QC request is invalid."""


def window_function(
    n: int,
    kind: WindowKind = "hann",
    periodic: bool = False,
    dtype: Any = np.float32,
) -> np.ndarray:
    """Return a standard NumPy-backed one-dimensional window."""

    size = int(n)
    if size < 1:
        raise SpectralQCError("n must be a positive integer")
    normalized = _normalize_window_kind(kind)
    work_size = size + 1 if periodic and size > 1 else size
    if normalized == "hann":
        values = np.hanning(work_size)
    elif normalized == "hamming":
        values = np.hamming(work_size)
    elif normalized == "blackman":
        values = np.blackman(work_size)
    elif normalized == "bartlett":
        values = np.bartlett(work_size)
    elif normalized == "boxcar":
        values = np.ones(work_size, dtype=np.float64)
    else:
        index = np.arange(work_size, dtype=np.float64)
        values = np.sin(np.pi * (index + 0.5) / work_size)
    if periodic and size > 1:
        values = values[:-1]
    return np.ascontiguousarray(values.astype(dtype))


def apply_window(
    data: Any,
    kind: WindowKind = "hann",
    axis: int = 1,
    periodic: bool = False,
    normalize: bool = False,
) -> np.ndarray:
    """Apply a standard window along one 1-based RSF axis."""

    array = _coerce_numeric_array(data)
    numpy_axis = _numpy_axis(axis, array.ndim)
    weights = window_function(
        array.shape[numpy_axis],
        kind=kind,
        periodic=periodic,
        dtype=np.float64,
    )
    if normalize:
        coherent_gain = float(np.mean(weights))
        if abs(coherent_gain) <= np.finfo(np.float64).eps:
            raise SpectralQCError("window has zero coherent gain and cannot be normalized")
        weights = weights / coherent_gain
    shape = [1] * array.ndim
    shape[numpy_axis] = weights.size
    result = array * weights.reshape(shape)
    return np.ascontiguousarray(result.astype(_transform_dtype(array), copy=False))


def psd(
    data: Any,
    dt: float,
    axis: int = 1,
    nfft: int | None = None,
    window: WindowKind = "hann",
    average: bool = False,
    scaling: SpectralScaling = "density",
) -> np.ndarray:
    """Return a one-sided periodogram PSD or power spectrum."""

    array = _coerce_real_finite_array(data, operation="psd")
    numpy_axis = _numpy_axis(axis, array.ndim)
    sample_interval = _positive_float(dt, "dt")
    fft_size = _normalize_nfft(nfft, array.shape[numpy_axis])
    scale_mode = _normalize_scaling(scaling)
    weights = window_function(array.shape[numpy_axis], kind=window, dtype=np.float64)
    transformed = _windowed_rfft(array, weights, numpy_axis, fft_size)
    values = np.abs(transformed) ** 2
    values *= _periodogram_scale(weights, sample_interval, scale_mode)
    values *= _one_sided_multiplier(fft_size).reshape(
        _axis_shape(values.ndim, numpy_axis, fft_size // 2 + 1)
    )
    if average:
        other_axes = tuple(index for index in range(values.ndim) if index != numpy_axis)
        if other_axes:
            values = np.mean(values, axis=other_axes)
    return np.ascontiguousarray(values.astype(_real_output_dtype(array)))


def csd(
    a: Any,
    b: Any,
    dt: float,
    axis: int = 1,
    nfft: int | None = None,
    window: WindowKind = "hann",
    scaling: SpectralScaling = "density",
) -> np.ndarray:
    """Return the one-sided cross spectral density ``conj(A) * B``."""

    left, right = _coerce_real_pair(a, b, operation="csd")
    numpy_axis = _numpy_axis(axis, left.ndim)
    sample_interval = _positive_float(dt, "dt")
    fft_size = _normalize_nfft(nfft, left.shape[numpy_axis])
    scale_mode = _normalize_scaling(scaling)
    weights = window_function(left.shape[numpy_axis], kind=window, dtype=np.float64)
    left_fft = _windowed_rfft(left, weights, numpy_axis, fft_size)
    right_fft = _windowed_rfft(right, weights, numpy_axis, fft_size)
    values = np.conjugate(left_fft) * right_fft
    values *= _periodogram_scale(weights, sample_interval, scale_mode)
    values *= _one_sided_multiplier(fft_size).reshape(
        _axis_shape(values.ndim, numpy_axis, fft_size // 2 + 1)
    )
    return np.ascontiguousarray(values.astype(_complex_output_dtype(left, right)))


def coherence(
    a: Any,
    b: Any,
    dt: float,
    axis: int = 1,
    nfft: int | None = None,
    window: WindowKind = "hann",
    eps: float = 1e-12,
    nperseg: int | None = None,
    noverlap: int | None = None,
) -> np.ndarray:
    """Return magnitude-squared coherence using short-segment averaging."""

    left, right = _coerce_real_pair(a, b, operation="coherence")
    numpy_axis = _numpy_axis(axis, left.ndim)
    _positive_float(dt, "dt")
    epsilon = _positive_float(eps, "eps")
    segment_length, overlap = _segment_parameters(
        left.shape[numpy_axis], nperseg=nperseg, noverlap=noverlap
    )
    fft_size = _normalize_nfft(nfft, segment_length)
    weights = window_function(segment_length, kind=window, dtype=np.float64)
    left_fft = _segmented_rfft(left, numpy_axis, segment_length, overlap, fft_size, weights)
    right_fft = _segmented_rfft(right, numpy_axis, segment_length, overlap, fft_size, weights)
    pxx = np.mean(np.abs(left_fft) ** 2, axis=-2)
    pyy = np.mean(np.abs(right_fft) ** 2, axis=-2)
    pxy = np.mean(np.conjugate(left_fft) * right_fft, axis=-2)
    denominator = pxx * pyy
    values = np.zeros_like(denominator, dtype=np.float64)
    valid = denominator > epsilon
    values[valid] = np.abs(pxy[valid]) ** 2 / denominator[valid]
    values = np.clip(values, 0.0, 1.0)
    restored = np.moveaxis(values, -1, numpy_axis)
    return np.ascontiguousarray(restored.astype(_real_output_dtype(left, right)))


def spectrogram(
    data: Any,
    dt: float,
    axis: int = 1,
    nperseg: int = 64,
    noverlap: int | None = None,
    window: WindowKind = "hann",
    mode: SpectrogramMode = "power",
) -> np.ndarray:
    """Return a short-time spectrum with frequency as RSF axis 1.

    This subset supports RSF axis 1 for 1D signals and trace panels. The NumPy
    result shape is ``(..., nframe, nfrequency)``.
    """

    array = _coerce_real_finite_array(data, operation="spectrogram")
    if int(axis) != 1:
        raise SpectralQCError("spectrogram currently supports only RSF axis 1")
    sample_interval = _positive_float(dt, "dt")
    del sample_interval
    numpy_axis = _numpy_axis(axis, array.ndim)
    segment_length, overlap = _segment_parameters(
        array.shape[numpy_axis], nperseg=nperseg, noverlap=noverlap
    )
    mode_value = str(mode).strip().lower()
    if mode_value not in {"magnitude", "power"}:
        raise SpectralQCError("mode must be magnitude or power")
    weights = window_function(segment_length, kind=window, dtype=np.float64)
    transformed = _segmented_rfft(
        array,
        numpy_axis,
        segment_length,
        overlap,
        segment_length,
        weights,
    )
    coherent_gain = max(float(np.sum(weights)), np.finfo(np.float64).eps)
    if mode_value == "magnitude":
        values = np.abs(transformed) / coherent_gain
        values *= _one_sided_multiplier(segment_length)
    else:
        values = np.abs(transformed) ** 2 / (coherent_gain * coherent_gain)
        values *= _one_sided_multiplier(segment_length)
    return np.ascontiguousarray(values.astype(_real_output_dtype(array)))


def snr(
    data: Any,
    signal_window: SampleWindow | None = None,
    noise_window: SampleWindow | None = None,
    axis: int = 1,
    mode: str = "rms",
    unit: SNRUnit = "db",
    eps: float = 1e-12,
) -> np.ndarray:
    """Return per-trace RMS signal-to-noise ratio.

    ``noise_window`` is required unless ``signal_window`` is supplied, in which
    case the complement of the signal window is used as noise.
    """

    array = _coerce_numeric_array(data)
    if not bool(np.all(np.isfinite(array))):
        raise SpectralQCError("snr requires finite input")
    if str(mode).strip().lower() != "rms":
        raise SpectralQCError("mode currently supports only rms")
    unit_value = str(unit).strip().lower()
    if unit_value not in {"db", "ratio"}:
        raise SpectralQCError("unit must be db or ratio")
    epsilon = _positive_float(eps, "eps")
    numpy_axis = _numpy_axis(axis, array.ndim)
    length = array.shape[numpy_axis]
    signal_indices = _window_indices(signal_window, length, "signal_window")
    noise_indices = _window_indices(noise_window, length, "noise_window")
    if signal_indices is None and noise_indices is None:
        raise SpectralQCError("noise_window is required when signal_window is omitted")
    if signal_indices is None:
        signal_indices = np.arange(length)
    if noise_indices is None:
        mask = np.ones(length, dtype=bool)
        mask[signal_indices] = False
        noise_indices = np.flatnonzero(mask)
        if noise_indices.size == 0:
            raise SpectralQCError("signal_window leaves no samples for the noise complement")
    signal_values = np.take(array, signal_indices, axis=numpy_axis)
    noise_values = np.take(array, noise_indices, axis=numpy_axis)
    signal_rms = np.sqrt(np.mean(np.abs(signal_values) ** 2, axis=numpy_axis))
    noise_rms = np.sqrt(np.mean(np.abs(noise_values) ** 2, axis=numpy_axis))
    ratio = signal_rms / np.maximum(noise_rms, epsilon)
    result = 20.0 * np.log10(np.maximum(ratio, epsilon)) if unit_value == "db" else ratio
    output = np.asarray(result, dtype=np.float64)
    if output.ndim == 0:
        output = output.reshape(1)
    return np.ascontiguousarray(output)


def welch_psd(
    data: Any,
    dt: float,
    axis: int = 1,
    nperseg: int = 128,
    noverlap: int | None = None,
    window: WindowKind = "hann",
    nfft: int | None = None,
    scaling: SpectralScaling = "density",
    average: bool = True,
) -> np.ndarray:
    """Return a one-sided Welch PSD from overlapping windowed segments."""

    array = _coerce_real_finite_array(data, operation="welch")
    numpy_axis = _numpy_axis(axis, array.ndim)
    sample_interval = _positive_float(dt, "dt")
    segment_length, overlap = _segment_parameters(
        array.shape[numpy_axis],
        nperseg=nperseg,
        noverlap=noverlap,
    )
    fft_size = _normalize_nfft(nfft, segment_length)
    scale_mode = _normalize_scaling(scaling)
    weights = window_function(segment_length, kind=window, dtype=np.float64)
    transformed = _segmented_rfft(
        array,
        numpy_axis,
        segment_length,
        overlap,
        fft_size,
        weights,
    )
    values = np.mean(np.abs(transformed) ** 2, axis=-2)
    values *= _periodogram_scale(weights, sample_interval, scale_mode)
    values *= _one_sided_multiplier(fft_size)
    values = np.moveaxis(values, -1, numpy_axis)
    if average:
        other_axes = tuple(index for index in range(values.ndim) if index != numpy_axis)
        if other_axes:
            values = np.mean(values, axis=other_axes)
    return np.ascontiguousarray(values.astype(_real_output_dtype(array)))


def welch_csd(
    a: Any,
    b: Any,
    dt: float,
    axis: int = 1,
    nperseg: int = 128,
    noverlap: int | None = None,
    window: WindowKind = "hann",
    nfft: int | None = None,
    scaling: SpectralScaling = "density",
    average: bool = True,
) -> np.ndarray:
    """Return a one-sided Welch cross spectral density ``conj(A) * B``."""

    left, right = _coerce_real_pair(a, b, operation="welchcsd")
    numpy_axis = _numpy_axis(axis, left.ndim)
    sample_interval = _positive_float(dt, "dt")
    segment_length, overlap = _segment_parameters(
        left.shape[numpy_axis],
        nperseg=nperseg,
        noverlap=noverlap,
    )
    fft_size = _normalize_nfft(nfft, segment_length)
    scale_mode = _normalize_scaling(scaling)
    weights = window_function(segment_length, kind=window, dtype=np.float64)
    left_fft = _segmented_rfft(
        left,
        numpy_axis,
        segment_length,
        overlap,
        fft_size,
        weights,
    )
    right_fft = _segmented_rfft(
        right,
        numpy_axis,
        segment_length,
        overlap,
        fft_size,
        weights,
    )
    values = np.mean(np.conjugate(left_fft) * right_fft, axis=-2)
    values *= _periodogram_scale(weights, sample_interval, scale_mode)
    values *= _one_sided_multiplier(fft_size)
    values = np.moveaxis(values, -1, numpy_axis)
    if average:
        other_axes = tuple(index for index in range(values.ndim) if index != numpy_axis)
        if other_axes:
            values = np.mean(values, axis=other_axes)
    return np.ascontiguousarray(values.astype(_complex_output_dtype(left, right)))


def transfer_function(
    input_signal: Any,
    output_signal: Any,
    dt: float,
    axis: int = 1,
    nperseg: int = 128,
    noverlap: int | None = None,
    window: WindowKind = "hann",
    nfft: int | None = None,
    method: TransferMethod = "H1",
    eps: float = 1e-12,
) -> np.ndarray:
    """Estimate an H1 or H2 frequency response from paired real signals."""

    source, response = _coerce_real_pair(
        input_signal,
        output_signal,
        operation="transfer",
    )
    numpy_axis = _numpy_axis(axis, source.ndim)
    _positive_float(dt, "dt")
    epsilon = _positive_float(eps, "eps")
    method_value = str(method).strip().upper()
    if method_value not in {"H1", "H2"}:
        raise SpectralQCError("method must be H1 or H2")
    segment_length, overlap = _segment_parameters(
        source.shape[numpy_axis],
        nperseg=nperseg,
        noverlap=noverlap,
    )
    fft_size = _normalize_nfft(nfft, segment_length)
    weights = window_function(segment_length, kind=window, dtype=np.float64)
    source_fft = _segmented_rfft(
        source,
        numpy_axis,
        segment_length,
        overlap,
        fft_size,
        weights,
    )
    response_fft = _segmented_rfft(
        response,
        numpy_axis,
        segment_length,
        overlap,
        fft_size,
        weights,
    )
    pxx = np.mean(np.abs(source_fft) ** 2, axis=-2)
    pyy = np.mean(np.abs(response_fft) ** 2, axis=-2)
    pxy = np.mean(np.conjugate(source_fft) * response_fft, axis=-2)
    if method_value == "H1":
        values = _safe_spectral_divide(pxy, pxx, epsilon)
    else:
        values = _safe_spectral_divide(pyy, np.conjugate(pxy), epsilon)
    restored = np.moveaxis(values, -1, numpy_axis)
    return np.ascontiguousarray(restored.astype(_complex_output_dtype(source, response)))


def spectral_whiten(
    data: Any,
    dt: float,
    axis: int = 1,
    floor: float = 1e-6,
    smooth: int = 0,
    phase: str = "preserve",
) -> np.ndarray:
    """Whiten real data by dividing its spectrum by a stabilized amplitude."""

    array = _coerce_real_finite_array(data, operation="whiten")
    numpy_axis = _numpy_axis(axis, array.ndim)
    _positive_float(dt, "dt")
    relative_floor = _positive_float(floor, "floor")
    smooth_width = int(smooth)
    if smooth_width < 0:
        raise SpectralQCError("smooth must be non-negative")
    if str(phase).strip().lower() != "preserve":
        raise SpectralQCError("phase currently supports only preserve")
    transformed = np.fft.rfft(array.astype(np.float64, copy=False), axis=numpy_axis)
    amplitude = np.abs(transformed)
    denominator = (
        _moving_average_axis(amplitude, smooth_width, numpy_axis)
        if smooth_width > 1
        else amplitude
    )
    peak = np.max(denominator, axis=numpy_axis, keepdims=True)
    stabilized = np.maximum(
        denominator,
        relative_floor * np.maximum(peak, np.finfo(np.float64).eps),
    )
    whitened = transformed / stabilized
    result = np.fft.irfft(whitened, n=array.shape[numpy_axis], axis=numpy_axis)
    return np.ascontiguousarray(result.astype(_real_output_dtype(array)))


def spectral_normalize(
    data: Any,
    dt: float,
    axis: int = 1,
    mode: SpectralNormalizeMode = "unit_rms",
    band: tuple[float | None, float | None] | None = None,
    eps: float = 1e-12,
) -> np.ndarray:
    """Normalize each trace by an RMS or maximum spectral amplitude."""

    array = _coerce_real_finite_array(data, operation="specnorm")
    numpy_axis = _numpy_axis(axis, array.ndim)
    sample_interval = _positive_float(dt, "dt")
    epsilon = _positive_float(eps, "eps")
    mode_value = str(mode).strip().lower()
    if mode_value not in {"unit_rms", "unit_max"}:
        raise SpectralQCError("mode must be unit_rms or unit_max")
    transformed = np.fft.rfft(array.astype(np.float64, copy=False), axis=numpy_axis)
    frequencies = np.fft.rfftfreq(array.shape[numpy_axis], d=sample_interval)
    selected = _frequency_band_mask(frequencies, band)
    selected_values = np.take(transformed, np.flatnonzero(selected), axis=numpy_axis)
    amplitudes = np.abs(selected_values)
    if mode_value == "unit_rms":
        scale = np.sqrt(np.mean(amplitudes * amplitudes, axis=numpy_axis, keepdims=True))
    else:
        scale = np.max(amplitudes, axis=numpy_axis, keepdims=True)
    normalized = transformed / np.maximum(scale, epsilon)
    result = np.fft.irfft(normalized, n=array.shape[numpy_axis], axis=numpy_axis)
    return np.ascontiguousarray(result.astype(_real_output_dtype(array)))


def frequency_attributes(
    psd_or_signal: Any,
    dt: float | None = None,
    axis: int = 1,
    input_kind: str = "signal",
    attrs: Sequence[FrequencyAttribute | str] = (
        "dominant",
        "centroid",
        "bandwidth",
    ),
    fmin: float | None = None,
    fmax: float | None = None,
    frequency_origin: float = 0.0,
) -> np.ndarray:
    """Return dominant, centroid, and weighted-standard-deviation bandwidth.

    For ``input_kind="signal"``, ``dt`` is the time sample interval. For
    ``input_kind="psd"``, ``dt`` is the frequency-bin spacing and the first
    frequency is zero.
    """

    array = _coerce_real_finite_array(psd_or_signal, operation="freqattr")
    numpy_axis = _numpy_axis(axis, array.ndim)
    kind = str(input_kind).strip().lower()
    if kind == "signal":
        if dt is None:
            raise SpectralQCError("dt is required for signal input")
        sample_interval = _positive_float(dt, "dt")
        power = psd(
            array,
            sample_interval,
            axis=axis,
            window="hann",
            average=False,
            scaling="spectrum",
        ).astype(np.float64, copy=False)
        frequencies = np.fft.rfftfreq(array.shape[numpy_axis], d=sample_interval)
    elif kind == "psd":
        if dt is None:
            raise SpectralQCError("dt must provide frequency spacing for PSD input")
        frequency_spacing = _positive_float(dt, "dt")
        if bool(np.any(array < 0.0)):
            raise SpectralQCError("PSD input must be non-negative")
        power = array.astype(np.float64, copy=False)
        origin = float(frequency_origin)
        if not np.isfinite(origin):
            raise SpectralQCError("frequency_origin must be finite")
        frequencies = (
            origin
            + np.arange(array.shape[numpy_axis], dtype=np.float64) * frequency_spacing
        )
    else:
        raise SpectralQCError("input_kind must be signal or psd")

    attribute_names = _normalize_frequency_attributes(attrs)
    selected = _frequency_band_mask(frequencies, (fmin, fmax))
    selected_indices = np.flatnonzero(selected)
    selected_power = np.take(power, selected_indices, axis=numpy_axis)
    selected_frequencies = frequencies[selected]
    moved = np.moveaxis(selected_power, numpy_axis, -1)
    total = np.sum(moved, axis=-1)
    if bool(np.any(total <= np.finfo(np.float64).eps)):
        raise SpectralQCError("frequency attributes require positive spectral energy")
    centroid = np.sum(moved * selected_frequencies, axis=-1) / total
    variance = (
        np.sum(moved * (selected_frequencies - centroid[..., None]) ** 2, axis=-1)
        / total
    )
    dominant = selected_frequencies[np.argmax(moved, axis=-1)]
    values = {
        "dominant": dominant,
        "centroid": centroid,
        "bandwidth": np.sqrt(np.maximum(variance, 0.0)),
    }
    result = np.stack([values[name] for name in attribute_names], axis=-1)
    return np.ascontiguousarray(result.astype(_real_output_dtype(array)))


def windowfunc_rsf(
    input_path: str | Path | None,
    output_path: str | Path,
    *,
    n: int | None = None,
    kind: WindowKind = "hann",
    axis: int = 1,
    apply: bool = False,
    periodic: bool = False,
    normalize: bool = False,
) -> RSFArray:
    """Generate a one-dimensional window or apply it to an RSF dataset."""

    if apply:
        if input_path is None:
            raise SpectralQCError("input RSF is required when apply=y")
        rsf = read_rsf(input_path)
        result = apply_window(
            rsf.data,
            kind=kind,
            axis=axis,
            periodic=periodic,
            normalize=normalize,
        )
        header = rsf.header.copy()
    else:
        if input_path is not None:
            raise SpectralQCError("set apply=y to apply a window to an input RSF")
        if n is None:
            raise SpectralQCError("n1= is required when generating a window")
        result = window_function(n, kind=kind, periodic=periodic)
        header = RSFHeader(
            {"n1": int(n), "o1": 0.0, "d1": 1.0, "label1": "Window sample"}
        )
    header["window_kind"] = _normalize_window_kind(kind)
    header["window_periodic"] = bool(periodic)
    header["window_normalized"] = bool(normalize)
    return write_rsf(output_path, result, header)


def psd_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    nfft: int | None = None,
    window: WindowKind = "hann",
    average: bool = False,
    scaling: SpectralScaling = "density",
) -> RSFArray:
    """Write a periodogram PSD with a frequency-axis header."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    dt = cube.axis(rsf_axis).d
    result = psd(
        rsf.data,
        dt,
        axis=rsf_axis,
        nfft=nfft,
        window=window,
        average=average,
        scaling=scaling,
    )
    fft_size = _normalize_nfft(nfft, cube.axis(rsf_axis).n)
    header = _frequency_header(
        rsf.header,
        axis=rsf_axis,
        nfrequency=fft_size // 2 + 1,
        nfft=fft_size,
        dt=dt,
        average=average,
    )
    header["spectral_estimator"] = "periodogram"
    header["spectral_scaling"] = scaling
    header["spectral_window"] = window
    return write_rsf(output_path, result, header)


def csd_rsf(
    a_path: str | Path,
    b_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    nfft: int | None = None,
    window: WindowKind = "hann",
    scaling: SpectralScaling = "density",
) -> RSFArray:
    """Write a two-input cross spectral density."""

    left = read_rsf(a_path)
    right = read_rsf(b_path)
    cube = Hypercube.from_header(left.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    dt = cube.axis(rsf_axis).d
    result = csd(
        left.data,
        right.data,
        dt,
        axis=rsf_axis,
        nfft=nfft,
        window=window,
        scaling=scaling,
    )
    result = np.ascontiguousarray(result.astype(np.complex64, copy=False))
    fft_size = _normalize_nfft(nfft, cube.axis(rsf_axis).n)
    header = _frequency_header(
        left.header,
        axis=rsf_axis,
        nfrequency=fft_size // 2 + 1,
        nfft=fft_size,
        dt=dt,
    )
    header["spectral_estimator"] = "cross-periodogram"
    header["spectral_scaling"] = scaling
    header["spectral_window"] = window
    return write_rsf(output_path, result, header)


def coherence_rsf(
    a_path: str | Path,
    b_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    nfft: int | None = None,
    window: WindowKind = "hann",
    eps: float = 1e-12,
    nperseg: int | None = None,
    noverlap: int | None = None,
) -> RSFArray:
    """Write magnitude-squared coherence with a frequency-axis header."""

    left = read_rsf(a_path)
    right = read_rsf(b_path)
    cube = Hypercube.from_header(left.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    source_axis = cube.axis(rsf_axis)
    segment_length, overlap = _segment_parameters(
        source_axis.n, nperseg=nperseg, noverlap=noverlap
    )
    fft_size = _normalize_nfft(nfft, segment_length)
    result = coherence(
        left.data,
        right.data,
        source_axis.d,
        axis=rsf_axis,
        nfft=fft_size,
        window=window,
        eps=eps,
        nperseg=segment_length,
        noverlap=overlap,
    )
    header = _frequency_header(
        left.header,
        axis=rsf_axis,
        nfrequency=fft_size // 2 + 1,
        nfft=fft_size,
        dt=source_axis.d,
    )
    header["spectral_estimator"] = "segment-averaged coherence"
    header["spectral_window"] = window
    header["nperseg"] = segment_length
    header["noverlap"] = overlap
    return write_rsf(output_path, result, header)


def spectrogram_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    nperseg: int = 64,
    noverlap: int | None = None,
    window: WindowKind = "hann",
    mode: SpectrogramMode = "power",
) -> RSFArray:
    """Write an axis-1 STFT magnitude or power spectrogram."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    if rsf_axis != 1:
        raise SpectralQCError("spectrogram currently supports only RSF axis 1")
    source_axis = cube.axis(1)
    segment_length, overlap = _segment_parameters(
        source_axis.n, nperseg=nperseg, noverlap=noverlap
    )
    result = spectrogram(
        rsf.data,
        source_axis.d,
        axis=1,
        nperseg=segment_length,
        noverlap=overlap,
        window=window,
        mode=mode,
    )
    hop = segment_length - overlap
    frequency_axis = Axis(
        n=segment_length // 2 + 1,
        o=0.0,
        d=1.0 / (segment_length * source_axis.d),
        label="Frequency",
        unit=_frequency_unit(source_axis.unit),
    )
    frame_axis = Axis(
        n=result.shape[-2],
        o=source_axis.o + 0.5 * (segment_length - 1) * source_axis.d,
        d=hop * source_axis.d,
        label="Window time",
        unit=source_axis.unit,
    )
    header = Hypercube([frequency_axis, frame_axis, *cube.axes[1:]]).to_header(rsf.header)
    header["spectrogram_mode"] = mode
    header["spectral_window"] = window
    header["nperseg"] = segment_length
    header["noverlap"] = overlap
    return write_rsf(output_path, result, header)


def snr_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    signal_window: SampleWindow | None = None,
    noise_window: SampleWindow | None = None,
    axis: int = 1,
    mode: str = "rms",
    unit: SNRUnit = "db",
    eps: float = 1e-12,
) -> RSFArray:
    """Write global or per-trace RMS SNR values."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    result = snr(
        rsf.data,
        signal_window=signal_window,
        noise_window=noise_window,
        axis=rsf_axis,
        mode=mode,
        unit=unit,
        eps=eps,
    )
    remaining = [item for index, item in enumerate(cube.axes, start=1) if index != rsf_axis]
    axes = remaining or [Axis(n=1, label="SNR", unit="dB" if unit == "db" else "ratio")]
    header = Hypercube(axes).to_header(rsf.header)
    header["statistic"] = "snr"
    header["snr_axis"] = rsf_axis
    header["snr_mode"] = mode
    header["snr_unit"] = unit
    if signal_window is not None:
        header["signal_window"] = _format_window(signal_window)
    if noise_window is not None:
        header["noise_window"] = _format_window(noise_window)
    return write_rsf(output_path, result, header)


def welch_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    nperseg: int = 128,
    noverlap: int | None = None,
    window: WindowKind = "hann",
    nfft: int | None = None,
    scaling: SpectralScaling = "density",
    average: bool = True,
) -> RSFArray:
    """Write a Welch PSD with one-sided frequency metadata."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    source_axis = cube.axis(rsf_axis)
    segment_length, overlap = _segment_parameters(
        source_axis.n,
        nperseg=nperseg,
        noverlap=noverlap,
    )
    fft_size = _normalize_nfft(nfft, segment_length)
    result = welch_psd(
        rsf.data,
        source_axis.d,
        axis=rsf_axis,
        nperseg=segment_length,
        noverlap=overlap,
        window=window,
        nfft=fft_size,
        scaling=scaling,
        average=average,
    )
    header = _frequency_header(
        rsf.header,
        axis=rsf_axis,
        nfrequency=fft_size // 2 + 1,
        nfft=fft_size,
        dt=source_axis.d,
        average=average,
    )
    header["spectral_estimator"] = "welch"
    header["spectral_scaling"] = scaling
    header["spectral_window"] = window
    header["nperseg"] = segment_length
    header["noverlap"] = overlap
    return write_rsf(output_path, result, header)


def welchcsd_rsf(
    a_path: str | Path,
    b_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    nperseg: int = 128,
    noverlap: int | None = None,
    window: WindowKind = "hann",
    nfft: int | None = None,
    scaling: SpectralScaling = "density",
    average: bool = True,
) -> RSFArray:
    """Write a Welch cross spectral density."""

    left = read_rsf(a_path)
    right = read_rsf(b_path)
    cube = Hypercube.from_header(left.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    source_axis = cube.axis(rsf_axis)
    segment_length, overlap = _segment_parameters(
        source_axis.n,
        nperseg=nperseg,
        noverlap=noverlap,
    )
    fft_size = _normalize_nfft(nfft, segment_length)
    result = welch_csd(
        left.data,
        right.data,
        source_axis.d,
        axis=rsf_axis,
        nperseg=segment_length,
        noverlap=overlap,
        window=window,
        nfft=fft_size,
        scaling=scaling,
        average=average,
    )
    result = np.ascontiguousarray(result.astype(np.complex64, copy=False))
    header = _frequency_header(
        left.header,
        axis=rsf_axis,
        nfrequency=fft_size // 2 + 1,
        nfft=fft_size,
        dt=source_axis.d,
        average=average,
    )
    header["spectral_estimator"] = "welch-csd"
    header["spectral_scaling"] = scaling
    header["spectral_window"] = window
    header["nperseg"] = segment_length
    header["noverlap"] = overlap
    return write_rsf(output_path, result, header)


def transfer_rsf(
    source_path: str | Path,
    response_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    nperseg: int = 128,
    noverlap: int | None = None,
    window: WindowKind = "hann",
    nfft: int | None = None,
    method: TransferMethod = "H1",
    eps: float = 1e-12,
) -> RSFArray:
    """Write an H1 or H2 transfer-function estimate."""

    source = read_rsf(source_path)
    response = read_rsf(response_path)
    cube = Hypercube.from_header(source.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    source_axis = cube.axis(rsf_axis)
    segment_length, overlap = _segment_parameters(
        source_axis.n,
        nperseg=nperseg,
        noverlap=noverlap,
    )
    fft_size = _normalize_nfft(nfft, segment_length)
    result = transfer_function(
        source.data,
        response.data,
        source_axis.d,
        axis=rsf_axis,
        nperseg=segment_length,
        noverlap=overlap,
        window=window,
        nfft=fft_size,
        method=method,
        eps=eps,
    )
    result = np.ascontiguousarray(result.astype(np.complex64, copy=False))
    header = _frequency_header(
        source.header,
        axis=rsf_axis,
        nfrequency=fft_size // 2 + 1,
        nfft=fft_size,
        dt=source_axis.d,
    )
    header["spectral_estimator"] = "transfer-function"
    header["transfer_method"] = str(method).upper()
    header["spectral_window"] = window
    header["nperseg"] = segment_length
    header["noverlap"] = overlap
    return write_rsf(output_path, result, header)


def whiten_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    floor: float = 1e-6,
    smooth: int = 0,
    phase: str = "preserve",
) -> RSFArray:
    """Write a phase-preserving spectrally whitened dataset."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    result = spectral_whiten(
        rsf.data,
        cube.axis(rsf_axis).d,
        axis=rsf_axis,
        floor=floor,
        smooth=smooth,
        phase=phase,
    )
    header = rsf.header.copy()
    header["spectral_operation"] = "whiten"
    header["whiten_axis"] = rsf_axis
    header["whiten_floor"] = floor
    header["whiten_smooth"] = int(smooth)
    header["whiten_phase"] = phase
    return write_rsf(output_path, result, header)


def specnorm_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    mode: SpectralNormalizeMode = "unit_rms",
    fmin: float | None = None,
    fmax: float | None = None,
    eps: float = 1e-12,
) -> RSFArray:
    """Write a spectrum-normalized dataset."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    result = spectral_normalize(
        rsf.data,
        cube.axis(rsf_axis).d,
        axis=rsf_axis,
        mode=mode,
        band=(fmin, fmax),
        eps=eps,
    )
    header = rsf.header.copy()
    header["spectral_operation"] = "normalize"
    header["specnorm_axis"] = rsf_axis
    header["specnorm_mode"] = mode
    if fmin is not None:
        header["specnorm_fmin"] = fmin
    if fmax is not None:
        header["specnorm_fmax"] = fmax
    return write_rsf(output_path, result, header)


def freqattr_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    input_kind: str = "signal",
    attrs: Sequence[FrequencyAttribute | str] = (
        "dominant",
        "centroid",
        "bandwidth",
    ),
    fmin: float | None = None,
    fmax: float | None = None,
) -> RSFArray:
    """Write per-trace frequency attributes on a leading attribute axis."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    source_axis = cube.axis(rsf_axis)
    kind = str(input_kind).strip().lower()
    spacing = source_axis.d
    attribute_names = _normalize_frequency_attributes(attrs)
    result = frequency_attributes(
        rsf.data,
        spacing,
        axis=rsf_axis,
        input_kind=kind,
        attrs=attribute_names,
        fmin=fmin,
        fmax=fmax,
        frequency_origin=source_axis.o,
    )
    remaining = [
        item for index, item in enumerate(cube.axes, start=1) if index != rsf_axis
    ]
    frequency_unit = (
        source_axis.unit if kind == "psd" else _frequency_unit(source_axis.unit)
    )
    attribute_axis = Axis(
        n=len(attribute_names),
        o=0.0,
        d=1.0,
        label="Frequency attribute",
        unit=frequency_unit,
    )
    header = Hypercube([attribute_axis, *remaining]).to_header(rsf.header)
    header["frequency_attributes"] = ",".join(attribute_names)
    header["frequency_attribute_input"] = kind
    header["bandwidth_definition"] = "weighted_standard_deviation"
    if fmin is not None:
        header["frequency_attribute_fmin"] = fmin
    if fmax is not None:
        header["frequency_attribute_fmax"] = fmax
    return write_rsf(output_path, result, header)


def _windowed_rfft(
    array: np.ndarray,
    weights: np.ndarray,
    axis: int,
    nfft: int,
) -> np.ndarray:
    shape = _axis_shape(array.ndim, axis, weights.size)
    return np.fft.rfft(
        array.astype(np.float64, copy=False) * weights.reshape(shape),
        n=nfft,
        axis=axis,
    )


def _segmented_rfft(
    array: np.ndarray,
    axis: int,
    nperseg: int,
    noverlap: int,
    nfft: int,
    weights: np.ndarray,
) -> np.ndarray:
    moved = np.moveaxis(array.astype(np.float64, copy=False), axis, -1)
    hop = nperseg - noverlap
    starts = list(range(0, moved.shape[-1] - nperseg + 1, hop))
    segments = np.stack([moved[..., start : start + nperseg] for start in starts], axis=-2)
    return np.fft.rfft(segments * weights, n=nfft, axis=-1)


def _periodogram_scale(
    weights: np.ndarray,
    dt: float,
    scaling: SpectralScaling,
) -> float:
    if scaling == "density":
        sampling_frequency = 1.0 / dt
        return 1.0 / (sampling_frequency * float(np.sum(weights * weights)))
    coherent_gain = float(np.sum(weights))
    return 1.0 / (coherent_gain * coherent_gain)


def _one_sided_multiplier(nfft: int) -> np.ndarray:
    multiplier = np.ones(nfft // 2 + 1, dtype=np.float64)
    if nfft % 2 == 0:
        multiplier[1:-1] = 2.0
    else:
        multiplier[1:] = 2.0
    return multiplier


def _frequency_header(
    source: RSFHeader,
    *,
    axis: int,
    nfrequency: int,
    nfft: int,
    dt: float,
    average: bool = False,
) -> RSFHeader:
    cube = Hypercube.from_header(source)
    source_axis = cube.axis(axis)
    frequency_axis = Axis(
        n=nfrequency,
        o=0.0,
        d=1.0 / (nfft * dt),
        label="Frequency",
        unit=_frequency_unit(source_axis.unit),
    )
    if average:
        return Hypercube([frequency_axis]).to_header(source)
    return cube.update_axis(
        axis,
        n=frequency_axis.n,
        o=frequency_axis.o,
        d=frequency_axis.d,
        label=frequency_axis.label,
        unit=frequency_axis.unit,
    ).to_header(source)


def _coerce_numeric_array(data: Any) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim < 1 or array.ndim > 3:
        raise SpectralQCError("spectral QC currently supports 1D, 2D, and 3D data")
    if array.size == 0 or array.dtype.kind not in {"f", "i", "u", "c"}:
        raise SpectralQCError("input must contain numeric samples")
    return array


def _coerce_real_finite_array(data: Any, *, operation: str) -> np.ndarray:
    array = _coerce_numeric_array(data)
    if np.iscomplexobj(array):
        raise SpectralQCError(f"{operation} currently requires real-valued input")
    if not bool(np.all(np.isfinite(array))):
        raise SpectralQCError(f"{operation} requires finite input")
    return array


def _coerce_real_pair(a: Any, b: Any, *, operation: str) -> tuple[np.ndarray, np.ndarray]:
    left = _coerce_real_finite_array(a, operation=operation)
    right = _coerce_real_finite_array(b, operation=operation)
    if left.shape != right.shape:
        raise SpectralQCError(f"{operation} inputs must have identical shapes")
    return left, right


def _numpy_axis(axis: int, ndim: int) -> int:
    return ndim - _validate_axis(axis, ndim)


def _validate_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise SpectralQCError(f"axis must be between 1 and {ndim}, got {axis}")
    return value


def _normalize_window_kind(value: str) -> WindowKind:
    normalized = str(value).strip().lower()
    aliases = {"hanning": "hann", "rectangular": "boxcar", "rect": "boxcar"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"hann", "hamming", "blackman", "bartlett", "boxcar", "cosine"}:
        raise SpectralQCError(
            "window kind must be hann, hamming, blackman, bartlett, boxcar, or cosine"
        )
    return normalized  # type: ignore[return-value]


def _normalize_scaling(value: str) -> SpectralScaling:
    normalized = str(value).strip().lower()
    if normalized not in {"density", "spectrum"}:
        raise SpectralQCError("scaling must be density or spectrum")
    return normalized  # type: ignore[return-value]


def _normalize_nfft(value: int | None, minimum: int) -> int:
    size = minimum if value is None else int(value)
    if size < minimum:
        raise SpectralQCError(f"nfft must be at least {minimum}")
    return size


def _segment_parameters(
    length: int,
    *,
    nperseg: int | None,
    noverlap: int | None,
) -> tuple[int, int]:
    segment = min(256, length) if nperseg is None else int(nperseg)
    if segment < 2 or segment > length:
        raise SpectralQCError(f"nperseg must be between 2 and axis length {length}")
    overlap = segment // 2 if noverlap is None else int(noverlap)
    if overlap < 0 or overlap >= segment:
        raise SpectralQCError("noverlap must be non-negative and smaller than nperseg")
    return segment, overlap


def _window_indices(
    value: SampleWindow | None,
    length: int,
    name: str,
) -> np.ndarray | None:
    if value is None:
        return None
    if isinstance(value, slice):
        start, stop, step = value.indices(length)
        if step != 1:
            raise SpectralQCError(f"{name} slice step must be 1")
    else:
        items = tuple(int(item) for item in value)
        if len(items) != 2:
            raise SpectralQCError(f"{name} must contain start and stop samples")
        start, stop = items
    if start < 0 or stop > length or start >= stop:
        raise SpectralQCError(f"{name} must satisfy 0 <= start < stop <= {length}")
    return np.arange(start, stop)


def _format_window(value: SampleWindow) -> str:
    if isinstance(value, slice):
        return f"{value.start or 0}:{value.stop}"
    items = tuple(value)
    return f"{items[0]}:{items[1]}"


def _axis_shape(ndim: int, axis: int, size: int) -> tuple[int, ...]:
    shape = [1] * ndim
    shape[axis] = size
    return tuple(shape)


def _positive_float(value: float, name: str) -> float:
    result = float(value)
    if not np.isfinite(result) or result <= 0.0:
        raise SpectralQCError(f"{name} must be positive and finite")
    return result


def _transform_dtype(array: np.ndarray) -> np.dtype[Any]:
    if array.dtype == np.dtype("float64"):
        return np.dtype("float64")
    if array.dtype == np.dtype("complex128"):
        return np.dtype("complex128")
    if np.iscomplexobj(array):
        return np.dtype("complex64")
    return np.dtype("float32")


def _real_output_dtype(*arrays: np.ndarray) -> np.dtype[Any]:
    if any(array.dtype in {np.dtype("float64"), np.dtype("complex128")} for array in arrays):
        return np.dtype("float64")
    return np.dtype("float32")


def _complex_output_dtype(*arrays: np.ndarray) -> np.dtype[Any]:
    if any(array.dtype == np.dtype("float64") for array in arrays):
        return np.dtype("complex128")
    return np.dtype("complex64")


def _frequency_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    if unit == "s":
        return "Hz"
    if unit.startswith("1/"):
        return unit[2:]
    return f"1/{unit}"


def _safe_spectral_divide(
    numerator: np.ndarray,
    denominator: np.ndarray,
    eps: float,
) -> np.ndarray:
    result = np.zeros_like(numerator, dtype=np.complex128)
    valid = np.abs(denominator) > eps
    result[valid] = numerator[valid] / denominator[valid]
    return result


def _moving_average_axis(
    values: np.ndarray,
    width: int,
    axis: int,
) -> np.ndarray:
    if width <= 1:
        return values
    left = width // 2
    right = width - 1 - left
    padding = [(0, 0)] * values.ndim
    padding[axis] = (left, right)
    padded = np.pad(values, padding, mode="edge")
    kernel = np.ones(width, dtype=np.float64) / width
    return np.apply_along_axis(
        lambda trace: np.convolve(trace, kernel, mode="valid"),
        axis,
        padded,
    )


def _frequency_band_mask(
    frequencies: np.ndarray,
    band: tuple[float | None, float | None] | None,
) -> np.ndarray:
    lower, upper = (None, None) if band is None else band
    if lower is not None:
        lower = float(lower)
        if not np.isfinite(lower) or lower < 0.0:
            raise SpectralQCError("fmin must be non-negative and finite")
    if upper is not None:
        upper = float(upper)
        if not np.isfinite(upper) or upper <= 0.0:
            raise SpectralQCError("fmax must be positive and finite")
    if lower is not None and upper is not None and lower >= upper:
        raise SpectralQCError("fmin must be smaller than fmax")
    mask = np.ones(frequencies.size, dtype=bool)
    if lower is not None:
        mask &= frequencies >= lower
    if upper is not None:
        mask &= frequencies <= upper
    if not bool(np.any(mask)):
        raise SpectralQCError("selected frequency band contains no samples")
    return mask


def _normalize_frequency_attributes(
    attrs: Sequence[FrequencyAttribute | str],
) -> tuple[FrequencyAttribute, ...]:
    if isinstance(attrs, str):
        items = [item.strip() for item in attrs.split(",") if item.strip()]
    else:
        items = [str(item).strip().lower() for item in attrs]
    if not items:
        raise SpectralQCError("attrs must contain at least one frequency attribute")
    allowed = {"dominant", "centroid", "bandwidth"}
    invalid = sorted(set(items) - allowed)
    if invalid:
        raise SpectralQCError(
            "attrs may contain only dominant, centroid, and bandwidth"
        )
    if len(set(items)) != len(items):
        raise SpectralQCError("attrs must not contain duplicates")
    return tuple(items)  # type: ignore[return-value]


__all__ = [
    "SpectralQCError",
    "apply_window",
    "coherence",
    "coherence_rsf",
    "csd",
    "csd_rsf",
    "frequency_attributes",
    "freqattr_rsf",
    "psd",
    "psd_rsf",
    "snr",
    "snr_rsf",
    "spectral_normalize",
    "spectral_whiten",
    "spectrogram",
    "spectrogram_rsf",
    "specnorm_rsf",
    "transfer_function",
    "transfer_rsf",
    "welch_csd",
    "welch_psd",
    "welch_rsf",
    "welchcsd_rsf",
    "whiten_rsf",
    "window_function",
    "windowfunc_rsf",
]

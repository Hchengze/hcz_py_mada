"""Small-data FIR design, filtering, and response-QC helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Sequence

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.signal.spectral import SpectralQCError, window_function


FIRWindow = Literal["hann", "hamming", "blackman", "bartlett", "boxcar"]
FIRMode = Literal["same"]
FrequencyResponseMode = Literal["complex", "amplitude", "power"]
BandEnergyMode = Literal["energy", "power", "rms"]
FrequencyBand = tuple[float, float]


class FIRFilterError(ValueError):
    """Raised when an FIR design or filtering request is invalid."""


def firwin(
    numtaps: int,
    cutoff: float | Sequence[float],
    fs: float | None = None,
    pass_zero: bool = True,
    window: FIRWindow = "hann",
    scale: bool = True,
    dtype: Any = np.float64,
) -> np.ndarray:
    """Design a low/high/band-pass or band-stop FIR with a windowed sinc.

    When ``fs`` is omitted, cutoff values are normalized so 1.0 is Nyquist.
    One cutoff selects low-pass/high-pass from ``pass_zero``. Two cutoffs
    select band-stop/band-pass respectively.
    """

    taps_count = _positive_integer(numtaps, "numtaps")
    frequencies, sampling_rate = _normalize_cutoff(cutoff, fs)
    kind = _filter_kind(frequencies, bool(pass_zero))
    if kind in {"highpass", "bandstop"} and taps_count % 2 == 0:
        raise FIRFilterError(
            "highpass and bandstop designs require odd numtaps for nonzero Nyquist gain"
        )

    sample_index = np.arange(taps_count, dtype=np.float64)
    center = 0.5 * (taps_count - 1)
    relative = sample_index - center

    def lowpass(cutoff_frequency: float) -> np.ndarray:
        normalized = cutoff_frequency / sampling_rate
        return 2.0 * normalized * np.sinc(2.0 * normalized * relative)

    if kind == "lowpass":
        coefficients = lowpass(frequencies[0])
    elif kind == "highpass":
        coefficients = _unit_impulse(taps_count) - lowpass(frequencies[0])
    elif kind == "bandpass":
        coefficients = lowpass(frequencies[1]) - lowpass(frequencies[0])
    else:
        coefficients = _unit_impulse(taps_count) - (
            lowpass(frequencies[1]) - lowpass(frequencies[0])
        )

    try:
        weights = window_function(
            taps_count,
            kind=window,
            periodic=False,
            dtype=np.float64,
        )
    except SpectralQCError as exc:
        raise FIRFilterError(str(exc)) from exc
    coefficients *= weights

    if scale:
        reference = _scale_frequency(kind, frequencies, sampling_rate)
        phase = np.exp(-2j * np.pi * reference * sample_index / sampling_rate)
        gain = float(abs(np.sum(coefficients * phase)))
        if gain <= np.finfo(np.float64).eps:
            raise FIRFilterError("designed filter has zero gain at its scaling frequency")
        coefficients /= gain

    output_dtype = np.dtype(dtype)
    if output_dtype not in {np.dtype("float32"), np.dtype("float64")}:
        raise FIRFilterError("dtype must be float32 or float64")
    return np.ascontiguousarray(coefficients.astype(output_dtype))


def firwin_rsf(
    output_path: str | Path,
    *,
    numtaps: int,
    cutoff: float | Sequence[float],
    fs: float | None = None,
    pass_zero: bool = True,
    window: FIRWindow = "hann",
    scale: bool = True,
) -> RSFArray:
    """Design FIR coefficients and write a one-dimensional RSF filter."""

    coefficients = firwin(
        numtaps,
        cutoff,
        fs=fs,
        pass_zero=pass_zero,
        window=window,
        scale=scale,
    )
    frequencies, sampling_rate = _normalize_cutoff(cutoff, fs)
    spacing = 1.0 / sampling_rate if fs is not None else 1.0
    header = RSFHeader(
        {
            "n1": coefficients.size,
            "o1": -0.5 * (coefficients.size - 1) * spacing,
            "d1": spacing,
            "label1": "Lag",
            "unit1": "s" if fs is not None else "sample",
            "fir_kind": _filter_kind(frequencies, bool(pass_zero)),
            "fir_cutoff": ",".join(f"{value:g}" for value in frequencies),
            "fir_window": window,
            "fir_scale": bool(scale),
            "fir_fs": sampling_rate if fs is not None else "normalized",
        }
    )
    return write_rsf(output_path, coefficients, header)


def fir_filter(
    data: Any,
    taps: Any,
    axis: int = 1,
    mode: FIRMode = "same",
) -> np.ndarray:
    """Apply a one-dimensional FIR along a 1-based RSF axis."""

    array = _coerce_numeric_finite_array(data, operation="fir_filter")
    coefficients = _coerce_taps(taps)
    if str(mode).strip().lower() != "same":
        raise FIRFilterError("mode currently supports only same")
    numpy_axis = _numpy_axis(axis, array.ndim)
    length = array.shape[numpy_axis]
    if coefficients.size > length:
        raise FIRFilterError("tap count must not exceed the selected data-axis length")

    moved = np.moveaxis(array, numpy_axis, -1)
    traces = moved.reshape((-1, length))
    output_dtype = _filter_output_dtype(array, coefficients)
    output = np.empty(traces.shape, dtype=output_dtype)
    start = (coefficients.size - 1) // 2
    for index, trace in enumerate(traces):
        full = np.convolve(trace, coefficients, mode="full")
        output[index] = full[start : start + length]
    restored = output.reshape(moved.shape)
    return np.ascontiguousarray(np.moveaxis(restored, -1, numpy_axis))


def firfilter_rsf(
    input_path: str | Path,
    taps_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    mode: FIRMode = "same",
) -> RSFArray:
    """Apply a one-dimensional RSF FIR filter and preserve input geometry."""

    source = read_rsf(input_path)
    filter_rsf = read_rsf(taps_path)
    cube = Hypercube.from_header(source.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    coefficients = _coerce_taps(filter_rsf.data)
    _validate_filter_sampling(source.header, filter_rsf.header, rsf_axis)
    result = fir_filter(source.data, coefficients, axis=rsf_axis, mode=mode)
    header = source.header.copy()
    header["fir_axis"] = rsf_axis
    header["fir_numtaps"] = coefficients.size
    header["fir_mode"] = mode
    return write_rsf(output_path, result, header)


def zero_phase_fir_filter(
    data: Any,
    taps: Any,
    axis: int = 1,
    pad: bool = True,
) -> np.ndarray:
    """Apply forward and reverse FIR passes with optional reflection padding."""

    array = _coerce_numeric_finite_array(data, operation="filtfilt")
    coefficients = _coerce_taps(taps)
    numpy_axis = _numpy_axis(axis, array.ndim)
    length = array.shape[numpy_axis]
    if coefficients.size > length:
        raise FIRFilterError("tap count must not exceed the selected data-axis length")

    work = array
    pad_length = 0
    if pad and length > 1 and coefficients.size > 1:
        pad_length = min(3 * (coefficients.size - 1), length - 1)
        widths = [(0, 0)] * array.ndim
        widths[numpy_axis] = (pad_length, pad_length)
        work = np.pad(array, widths, mode="reflect")

    forward = fir_filter(work, coefficients, axis=axis)
    backward = np.flip(
        fir_filter(np.flip(forward, axis=numpy_axis), coefficients, axis=axis),
        axis=numpy_axis,
    )
    if pad_length:
        slices = [slice(None)] * backward.ndim
        slices[numpy_axis] = slice(pad_length, pad_length + length)
        backward = backward[tuple(slices)]
    return np.ascontiguousarray(backward)


def filtfilt_rsf(
    input_path: str | Path,
    taps_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    pad: bool = True,
) -> RSFArray:
    """Apply a forward/reverse FIR and preserve input geometry."""

    source = read_rsf(input_path)
    filter_rsf = read_rsf(taps_path)
    cube = Hypercube.from_header(source.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    coefficients = _coerce_taps(filter_rsf.data)
    _validate_filter_sampling(source.header, filter_rsf.header, rsf_axis)
    result = zero_phase_fir_filter(
        source.data,
        coefficients,
        axis=rsf_axis,
        pad=pad,
    )
    header = source.header.copy()
    header["fir_axis"] = rsf_axis
    header["fir_numtaps"] = coefficients.size
    header["fir_zero_phase"] = True
    header["fir_pad"] = bool(pad)
    return write_rsf(output_path, result, header)


def freq_response(
    taps: Any,
    fs: float | None = None,
    nfft: int = 512,
) -> tuple[np.ndarray, np.ndarray]:
    """Return one-sided frequency coordinates and complex FIR response."""

    coefficients = _coerce_taps(taps)
    fft_size = _positive_integer(nfft, "nfft")
    if fft_size < coefficients.size:
        raise FIRFilterError("nfft must be at least the tap count")
    sampling_rate = 2.0 if fs is None else _positive_float(fs, "fs")
    response = np.fft.fft(coefficients, n=fft_size)[: fft_size // 2 + 1]
    frequencies = np.arange(response.size, dtype=np.float64) * sampling_rate / fft_size
    complex_dtype = (
        np.complex128
        if coefficients.dtype in {np.dtype("float64"), np.dtype("complex128")}
        else np.complex64
    )
    return (
        np.ascontiguousarray(frequencies),
        np.ascontiguousarray(response.astype(complex_dtype)),
    )


def freqz_rsf(
    taps_path: str | Path,
    output_path: str | Path,
    *,
    fs: float | None = None,
    nfft: int = 512,
    mode: FrequencyResponseMode = "complex",
) -> RSFArray:
    """Write the complex, amplitude, or power response of a 1D FIR."""

    filter_rsf = read_rsf(taps_path)
    coefficients = _coerce_taps(filter_rsf.data)
    frequencies, response = freq_response(coefficients, fs=fs, nfft=nfft)
    mode_value = str(mode).strip().lower()
    if mode_value == "complex":
        result = response.astype(np.complex64)
    elif mode_value == "amplitude":
        result = np.abs(response).astype(_real_output_dtype(coefficients))
    elif mode_value == "power":
        result = (np.abs(response) ** 2).astype(_real_output_dtype(coefficients))
    else:
        raise FIRFilterError("mode must be complex, amplitude, or power")

    header = RSFHeader(
        {
            "n1": result.size,
            "o1": 0.0,
            "d1": frequencies[1] - frequencies[0] if result.size > 1 else 0.0,
            "label1": "Frequency",
            "unit1": "Hz" if fs is not None else "Nyquist",
            "frequency_response_mode": mode_value,
            "fir_numtaps": coefficients.size,
            "fir_nfft": int(nfft),
        }
    )
    return write_rsf(output_path, result, header)


def band_energy(
    data: Any,
    dt: float,
    bands: str | Sequence[Sequence[float]],
    axis: int = 1,
    mode: BandEnergyMode = "rms",
    average: bool = True,
) -> np.ndarray:
    """Return per-band energy, mean power, or RMS along one RSF axis."""

    array = _coerce_real_finite_array(data, operation="band_energy")
    sample_interval = _positive_float(dt, "dt")
    normalized_bands = parse_frequency_bands(bands)
    numpy_axis = _numpy_axis(axis, array.ndim)
    length = array.shape[numpy_axis]
    nyquist = 0.5 / sample_interval
    _validate_bands(normalized_bands, nyquist)
    mode_value = _normalize_band_mode(mode)

    spectrum = np.fft.rfft(array.astype(np.float64), axis=numpy_axis)
    frequencies = np.fft.rfftfreq(length, d=sample_interval)
    values: list[np.ndarray] = []
    for low, high in normalized_bands:
        mask = (frequencies >= low) & (frequencies <= high)
        if not bool(np.any(mask)):
            raise FIRFilterError(
                f"frequency band {low:g}:{high:g} contains no FFT bins"
            )
        shape = [1] * array.ndim
        shape[numpy_axis] = mask.size
        selected = spectrum * mask.reshape(shape)
        filtered = np.fft.irfft(selected, n=length, axis=numpy_axis)
        squared = filtered * filtered
        if mode_value == "energy":
            statistic = np.sum(squared, axis=numpy_axis)
        elif mode_value == "power":
            statistic = np.mean(squared, axis=numpy_axis)
        else:
            statistic = np.sqrt(np.mean(squared, axis=numpy_axis))
        values.append(statistic)

    result = np.stack(values, axis=-1)
    if average and result.ndim > 1:
        result = np.mean(result, axis=tuple(range(result.ndim - 1)))
    return np.ascontiguousarray(result.astype(_real_output_dtype(array)))


def bandenergy_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    bands: str | Sequence[Sequence[float]],
    axis: int = 1,
    mode: BandEnergyMode = "rms",
    average: bool = True,
) -> RSFArray:
    """Write a frequency-band energy/RMS table."""

    source = read_rsf(input_path)
    cube = Hypercube.from_header(source.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    normalized_bands = parse_frequency_bands(bands)
    result = band_energy(
        source.data,
        cube.axis(rsf_axis).d,
        normalized_bands,
        axis=rsf_axis,
        mode=mode,
        average=average,
    )
    band_axis = Axis(
        n=len(normalized_bands),
        o=0.0,
        d=1.0,
        label="Frequency band",
        unit="index",
    )
    if average:
        axes = [band_axis]
    else:
        axes = [band_axis] + [
            item for index, item in enumerate(cube.axes, start=1) if index != rsf_axis
        ]
    header = Hypercube(axes).to_header(source.header)
    header["statistic"] = f"band_{_normalize_band_mode(mode)}"
    header["bandenergy_axis"] = rsf_axis
    header["bandenergy_average"] = bool(average)
    header["frequency_bands"] = _format_bands(normalized_bands)
    for index, (low, high) in enumerate(normalized_bands, start=1):
        header[f"band{index}"] = f"{low:g}:{high:g}"
    return write_rsf(output_path, result, header)


def filter_bank(
    data: Any,
    dt: float,
    bands: str | Sequence[Sequence[float]],
    axis: int = 1,
    numtaps: int = 101,
    window: FIRWindow = "hann",
) -> np.ndarray:
    """Apply a bank of centered windowed-sinc FIR band-pass filters."""

    array = _coerce_real_finite_array(data, operation="filter_bank")
    sample_interval = _positive_float(dt, "dt")
    normalized_bands = parse_frequency_bands(bands)
    numpy_axis = _numpy_axis(axis, array.ndim)
    if int(numtaps) > array.shape[numpy_axis]:
        raise FIRFilterError("numtaps must not exceed the selected data-axis length")
    sampling_rate = 1.0 / sample_interval
    _validate_bands(normalized_bands, 0.5 * sampling_rate)
    filtered = []
    for band in normalized_bands:
        coefficients = firwin(
            numtaps,
            band,
            fs=sampling_rate,
            pass_zero=False,
            window=window,
            scale=True,
            dtype=np.float64,
        )
        filtered.append(fir_filter(array, coefficients, axis=axis))
    return np.ascontiguousarray(
        np.stack(filtered, axis=0).astype(_real_output_dtype(array))
    )


def filterbank_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    bands: str | Sequence[Sequence[float]],
    axis: int = 1,
    numtaps: int = 101,
    window: FIRWindow = "hann",
) -> RSFArray:
    """Write FIR-filtered data with a new highest RSF frequency-band axis."""

    source = read_rsf(input_path)
    cube = Hypercube.from_header(source.header)
    rsf_axis = _validate_axis(axis, cube.ndim)
    normalized_bands = parse_frequency_bands(bands)
    result = filter_bank(
        source.data,
        cube.axis(rsf_axis).d,
        normalized_bands,
        axis=rsf_axis,
        numtaps=numtaps,
        window=window,
    )
    axes = [
        *cube.axes,
        Axis(
            n=len(normalized_bands),
            o=0.0,
            d=1.0,
            label="Frequency band",
            unit="index",
        ),
    ]
    header = Hypercube(axes).to_header(source.header)
    header["filterbank_axis"] = rsf_axis
    header["filterbank_numtaps"] = int(numtaps)
    header["filterbank_window"] = window
    header["frequency_bands"] = _format_bands(normalized_bands)
    for index, (low, high) in enumerate(normalized_bands, start=1):
        header[f"band{index}"] = f"{low:g}:{high:g}"
    return write_rsf(output_path, result, header)


def parse_frequency_bands(
    bands: str | Sequence[Sequence[float]],
) -> tuple[FrequencyBand, ...]:
    """Parse ``low:high`` pairs from a CLI string or Python sequence."""

    parsed: list[FrequencyBand] = []
    if isinstance(bands, str):
        tokens = [item.strip() for item in bands.split(",") if item.strip()]
        for token in tokens:
            pieces = [item.strip() for item in token.split(":")]
            if len(pieces) != 2:
                raise FIRFilterError(
                    "bands must use comma-separated low:high pairs"
                )
            try:
                parsed.append((float(pieces[0]), float(pieces[1])))
            except ValueError as exc:
                raise FIRFilterError(f"invalid frequency band {token!r}") from exc
    else:
        for value in bands:
            if len(value) != 2:
                raise FIRFilterError("each frequency band must contain two values")
            parsed.append((float(value[0]), float(value[1])))
    if not parsed:
        raise FIRFilterError("at least one frequency band is required")
    for low, high in parsed:
        if not np.isfinite(low) or not np.isfinite(high) or low < 0.0 or low >= high:
            raise FIRFilterError(
                f"frequency bands require finite 0 <= low < high, got {low:g}:{high:g}"
            )
    return tuple(parsed)


def _normalize_cutoff(
    cutoff: float | Sequence[float],
    fs: float | None,
) -> tuple[tuple[float, ...], float]:
    if np.isscalar(cutoff):
        values = (float(cutoff),)
    else:
        values = tuple(float(value) for value in cutoff)
    if len(values) not in {1, 2}:
        raise FIRFilterError("cutoff must contain one or two frequencies")
    if not all(np.isfinite(value) for value in values):
        raise FIRFilterError("cutoff frequencies must be finite")
    if any(left >= right for left, right in zip(values, values[1:])):
        raise FIRFilterError("cutoff frequencies must be strictly increasing")
    sampling_rate = 2.0 if fs is None else _positive_float(fs, "fs")
    nyquist = 0.5 * sampling_rate
    if values[0] <= 0.0 or values[-1] >= nyquist:
        unit = "normalized Nyquist" if fs is None else f"Nyquist ({nyquist:g})"
        raise FIRFilterError(f"cutoff frequencies must be strictly between 0 and {unit}")
    return values, sampling_rate


def _filter_kind(frequencies: Sequence[float], pass_zero: bool) -> str:
    if len(frequencies) == 1:
        return "lowpass" if pass_zero else "highpass"
    return "bandstop" if pass_zero else "bandpass"


def _scale_frequency(
    kind: str,
    frequencies: Sequence[float],
    sampling_rate: float,
) -> float:
    if kind in {"lowpass", "bandstop"}:
        return 0.0
    if kind == "highpass":
        return 0.5 * sampling_rate
    return 0.5 * (frequencies[0] + frequencies[1])


def _unit_impulse(numtaps: int) -> np.ndarray:
    impulse = np.zeros(numtaps, dtype=np.float64)
    impulse[(numtaps - 1) // 2] = 1.0
    return impulse


def _coerce_taps(taps: Any) -> np.ndarray:
    coefficients = np.asarray(taps)
    if coefficients.ndim > 1:
        coefficients = np.squeeze(coefficients)
    if coefficients.ndim == 0 and coefficients.size == 1:
        coefficients = coefficients.reshape(1)
    if coefficients.ndim != 1 or coefficients.size < 1:
        raise FIRFilterError("taps must be a non-empty one-dimensional array")
    if coefficients.dtype.kind not in {"f", "i", "u", "c"}:
        raise FIRFilterError("taps must contain numeric values")
    if not bool(np.all(np.isfinite(coefficients))):
        raise FIRFilterError("taps must contain finite values")
    return np.ascontiguousarray(coefficients)


def _coerce_numeric_finite_array(data: Any, *, operation: str) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim < 1 or array.ndim > 3:
        raise FIRFilterError(f"{operation} currently supports 1D, 2D, and 3D data")
    if array.size == 0 or array.dtype.kind not in {"f", "i", "u", "c"}:
        raise FIRFilterError(f"{operation} requires numeric input")
    if not bool(np.all(np.isfinite(array))):
        raise FIRFilterError(f"{operation} requires finite input")
    return array


def _coerce_real_finite_array(data: Any, *, operation: str) -> np.ndarray:
    array = _coerce_numeric_finite_array(data, operation=operation)
    if np.iscomplexobj(array):
        raise FIRFilterError(f"{operation} currently requires real-valued input")
    return array


def _validate_filter_sampling(
    data_header: RSFHeader,
    filter_header: RSFHeader,
    data_axis: int,
) -> None:
    data_spacing = float(data_header.get(f"d{data_axis}", 1.0))
    filter_spacing = float(filter_header.get("d1", data_spacing))
    if not np.isclose(data_spacing, filter_spacing, rtol=1e-6, atol=1e-12):
        raise FIRFilterError(
            f"sampling mismatch: d{data_axis}={data_spacing:g} and taps d1={filter_spacing:g}"
        )


def _validate_bands(bands: Sequence[FrequencyBand], nyquist: float) -> None:
    for low, high in bands:
        if high >= nyquist:
            raise FIRFilterError(
                f"frequency band {low:g}:{high:g} must end below Nyquist ({nyquist:g})"
            )


def _format_bands(bands: Sequence[FrequencyBand]) -> str:
    return ",".join(f"{low:g}:{high:g}" for low, high in bands)


def _normalize_band_mode(mode: str) -> BandEnergyMode:
    value = str(mode).strip().lower()
    if value not in {"energy", "power", "rms"}:
        raise FIRFilterError("mode must be energy, power, or rms")
    return value  # type: ignore[return-value]


def _numpy_axis(axis: int, ndim: int) -> int:
    return ndim - _validate_axis(axis, ndim)


def _validate_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 1 or value > ndim:
        raise FIRFilterError(f"axis must be between 1 and {ndim}, got {axis}")
    return value


def _positive_integer(value: int, name: str) -> int:
    number = int(value)
    if number < 1 or number != value:
        raise FIRFilterError(f"{name} must be a positive integer")
    return number


def _positive_float(value: float, name: str) -> float:
    number = float(value)
    if not np.isfinite(number) or number <= 0.0:
        raise FIRFilterError(f"{name} must be a positive finite value")
    return number


def _filter_output_dtype(data: np.ndarray, taps: np.ndarray) -> np.dtype[Any]:
    if np.iscomplexobj(data) or np.iscomplexobj(taps):
        return np.dtype("complex64")
    if data.dtype == np.dtype("float64") or taps.dtype == np.dtype("float64"):
        return np.dtype("float64")
    return np.dtype("float32")


def _real_output_dtype(*arrays: np.ndarray) -> np.dtype[Any]:
    if any(np.asarray(array).dtype == np.dtype("float64") for array in arrays):
        return np.dtype("float64")
    return np.dtype("float32")


__all__ = [
    "FIRFilterError",
    "band_energy",
    "bandenergy_rsf",
    "filter_bank",
    "filterbank_rsf",
    "filtfilt_rsf",
    "fir_filter",
    "firfilter_rsf",
    "firwin",
    "firwin_rsf",
    "freq_response",
    "freqz_rsf",
    "parse_frequency_bands",
    "zero_phase_fir_filter",
]

"""High-level Pythonic RSF data interface."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import tempfile
from typing import Any

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.generic.array_math import clip_rsf, normalize_rsf, scale_rsf
from pymadagascar.generic.attr import attr_rsf
from pymadagascar.generic.difference import diff_rsf
from pymadagascar.generic.pad import pad_rsf
from pymadagascar.generic.rotate import rotate_rsf
from pymadagascar.generic.sampling import linear_rsf, max1_rsf, slice_rsf
from pymadagascar.generic.spray import spray_rsf
from pymadagascar.generic.statistics import (
    fillnan_rsf,
    isnan_rsf,
    mean_rsf,
    median_rsf,
    range_rsf,
    rms_rsf,
    std_rsf,
    var_rsf,
)
from pymadagascar.generic.unary import (
    abs_rsf,
    exp_rsf,
    histogram_rsf,
    log_rsf,
    pow_rsf,
    quantile_rsf,
    sign_rsf,
    sqrt_rsf,
)
from pymadagascar.generic.window import window as window_array
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.plot.graph import graph
from pymadagascar.plot.grey import grey
from pymadagascar.seismic.agc import agc_rsf
from pymadagascar.seismic.mute import mute_rsf, mutter_rsf
from pymadagascar.seismic.stack import stack_rsf, stacks_rsf
from pymadagascar.signal.calculus import causint_rsf, deriv_rsf, integral_rsf
from pymadagascar.signal.conditioning import clip2_rsf, shifts_rsf
from pymadagascar.signal.convolution import autocorr_rsf, cconv_rsf, convolve_rsf, envcorr_rsf
from pymadagascar.signal.fft import fft_rsf, ifft_rsf, irfft_rsf, rfft_rsf
from pymadagascar.signal.fir import (
    bandenergy_rsf,
    filterbank_rsf,
    filtfilt_rsf,
    firfilter_rsf,
)
from pymadagascar.signal.filter import bandpass_rsf, highpass_rsf, lowpass_rsf
from pymadagascar.signal.preprocessing import costaper_rsf, envelope_rsf, spectra_rsf, threshold_rsf
from pymadagascar.signal.qc import (
    bandstop_rsf,
    decimate_rsf,
    demean_rsf,
    detrend_rsf,
    localrms_rsf,
    notch_rsf,
)
from pymadagascar.signal.spectral import (
    coherence_rsf,
    csd_rsf,
    freqattr_rsf,
    psd_rsf,
    snr_rsf,
    spectrogram_rsf,
    specnorm_rsf,
    transfer_rsf,
    welch_rsf,
    welchcsd_rsf,
    whiten_rsf,
    windowfunc_rsf,
)


PathLike = str | Path
FileOperation = Callable[..., RSFArray]


def read(path: PathLike) -> "RSFData":
    """Read a file-backed RSF dataset into a high-level ``RSFData`` object."""

    return RSFData.from_rsf_array(read_rsf(path))


def write(
    path: PathLike,
    data: Any,
    header: RSFHeader | dict[str, Any] | None = None,
    *,
    data_format: str | None = None,
) -> "RSFData":
    """Write an array-like object or ``RSFData`` to RSF and return ``RSFData``."""

    if isinstance(data, RSFData):
        return data.write(path, data_format=data_format)
    return RSFData.from_rsf_array(write_rsf(path, np.asarray(data), header, data_format=data_format))


class RSFData:
    """A light, chainable wrapper around NumPy data and RSF metadata.

    Transform methods return a new ``RSFData`` by default. Pass
    ``inplace=True`` when an operation should update the current object.
    """

    def __init__(
        self,
        data: Any,
        header: RSFHeader | dict[str, Any] | None = None,
        *,
        path: PathLike | None = None,
        copy: bool = True,
    ) -> None:
        array = np.array(data, copy=copy)
        rsf_header = header.copy() if isinstance(header, RSFHeader) else RSFHeader(header)
        rsf_header.set_dimensions_from_shape(array.shape)
        self._data = np.ascontiguousarray(array)
        self._header = rsf_header
        self._path = Path(path).expanduser().resolve() if path is not None else None

    @classmethod
    def from_rsf_array(cls, rsf: RSFArray, *, copy: bool = True) -> "RSFData":
        """Create ``RSFData`` from a low-level ``RSFArray``."""

        return cls(rsf.data, rsf.header, path=rsf.header_path, copy=copy)

    @property
    def path(self) -> Path | None:
        """Source or last written header path, if known."""

        return self._path

    @property
    def header(self) -> RSFHeader:
        """Return a defensive copy of the RSF header."""

        return self._header.copy()

    @property
    def shape(self) -> tuple[int, ...]:
        """NumPy storage shape."""

        return self._data.shape

    @property
    def dtype(self) -> np.dtype[Any]:
        """NumPy dtype."""

        return self._data.dtype

    @property
    def ndim(self) -> int:
        """Number of NumPy dimensions."""

        return self._data.ndim

    @property
    def axes(self) -> tuple[Axis, ...]:
        """RSF axes in 1-based RSF order."""

        return Hypercube.from_header(self._header).axes

    def __array__(self, dtype: Any = None) -> np.ndarray:
        return np.asarray(self._data, dtype=dtype)

    def numpy(self, *, copy: bool = True) -> np.ndarray:
        """Return the NumPy array. The default is a defensive copy."""

        return np.array(self._data, copy=copy)

    def copy(self) -> "RSFData":
        """Return a deep copy of this object."""

        return RSFData(self._data, self._header, path=self._path, copy=True)

    def to_rsf_array(self, *, copy: bool = True) -> RSFArray:
        """Return a low-level ``RSFArray`` view or copy."""

        data = np.array(self._data, copy=copy)
        return RSFArray(data, self._header.copy(), header_path=self._path)

    def write(self, path: PathLike, *, data_format: str | None = None) -> "RSFData":
        """Write this object to RSF and return the written ``RSFData``."""

        return RSFData.from_rsf_array(
            write_rsf(path, self._data, self._header.copy(), data_format=data_format)
        )

    def window(
        self,
        *,
        axis: int | tuple[int, ...] | list[int] | None = None,
        f: int | tuple[int, ...] | list[int] | dict[int, int] | None = None,
        n: int | tuple[int, ...] | list[int] | dict[int, int] | None = None,
        j: int | tuple[int, ...] | list[int] | dict[int, int] | None = None,
        inplace: bool = False,
    ) -> "RSFData":
        """Window data using 1-based RSF axes and zero-based ``f`` samples."""

        result = window_array(self._data, self._header, axis=axis, f=f, n=n, j=j)
        return self._from_result(result, inplace=inplace)

    def scale(self, value: float | complex, *, inplace: bool = False) -> "RSFData":
        """Multiply data by a scalar."""

        return self._from_file_op(scale_rsf, scale=value, inplace=inplace)

    def rotate(self, rotations: dict[int, int], *, inplace: bool = False) -> "RSFData":
        """Cyclically rotate samples using 1-based RSF axis ``rot#`` counts."""

        return self._from_file_op(rotate_rsf, rotations=rotations, inplace=inplace)

    def pad(
        self,
        *,
        n: dict[int, int] | None = None,
        beg: dict[int, int] | None = None,
        end: dict[int, int] | None = None,
        value: float = 0.0,
        inplace: bool = False,
    ) -> "RSFData":
        """Pad one or more 1-based RSF axes with a constant value."""

        return self._from_file_op(
            pad_rsf,
            n=n,
            beg=beg,
            end=end,
            value=value,
            inplace=inplace,
        )

    def spray(
        self,
        *,
        axis: int = 2,
        n: int,
        o: float = 0.0,
        d: float = 1.0,
        label: str | None = None,
        unit: str | None = None,
        inplace: bool = False,
    ) -> "RSFData":
        """Insert a new 1-based RSF axis and duplicate samples along it."""

        return self._from_file_op(
            spray_rsf,
            axis=axis,
            n=n,
            o=o,
            d=d,
            label=label,
            unit=unit,
            inplace=inplace,
        )

    def clip(self, clip: float, *, inplace: bool = False) -> "RSFData":
        """Symmetrically clip real data to ``[-clip, clip]``."""

        return self._from_file_op(clip_rsf, clip=clip, inplace=inplace)

    def normalize(self, mode: str = "max", *, inplace: bool = False) -> "RSFData":
        """Normalize by max absolute value or RMS amplitude."""

        return self._from_file_op(normalize_rsf, mode=mode, inplace=inplace)

    def fft(self, *, axis: int = 1, norm: str | None = None, inplace: bool = False) -> "RSFData":
        """Compute a centered complex FFT along one RSF axis."""

        return self._from_file_op(fft_rsf, axis=axis, norm=norm, inplace=inplace)

    def ifft(self, *, axis: int = 1, norm: str | None = None, inplace: bool = False) -> "RSFData":
        """Invert a centered complex FFT along one RSF axis."""

        return self._from_file_op(ifft_rsf, axis=axis, norm=norm, inplace=inplace)

    def rfft(self, *, axis: int = 1, norm: str | None = None, inplace: bool = False) -> "RSFData":
        """Compute a real-to-complex FFT along one RSF axis."""

        return self._from_file_op(rfft_rsf, axis=axis, norm=norm, inplace=inplace)

    def irfft(
        self,
        *,
        axis: int = 1,
        n: int | None = None,
        norm: str | None = None,
        inplace: bool = False,
    ) -> "RSFData":
        """Invert a real-to-complex FFT along one RSF axis."""

        return self._from_file_op(irfft_rsf, axis=axis, n=n, norm=norm, inplace=inplace)

    def bandpass(
        self,
        *,
        flo: float,
        fhi: float,
        axis: int = 1,
        taper: float = 0.0,
        inplace: bool = False,
    ) -> "RSFData":
        """Apply a zero-phase FFT bandpass filter."""

        return self._from_file_op(
            bandpass_rsf,
            flo=flo,
            fhi=fhi,
            axis=axis,
            taper=taper,
            inplace=inplace,
        )

    def lowpass(
        self,
        *,
        fcut: float,
        axis: int = 1,
        taper: float = 0.0,
        inplace: bool = False,
    ) -> "RSFData":
        """Apply a zero-phase FFT lowpass filter."""

        return self._from_file_op(lowpass_rsf, fcut=fcut, axis=axis, taper=taper, inplace=inplace)

    def highpass(
        self,
        *,
        fcut: float,
        axis: int = 1,
        taper: float = 0.0,
        inplace: bool = False,
    ) -> "RSFData":
        """Apply a zero-phase FFT highpass filter."""

        return self._from_file_op(highpass_rsf, fcut=fcut, axis=axis, taper=taper, inplace=inplace)

    def demean(
        self,
        *,
        axis: int | None = None,
        nan_policy: str = "propagate",
        inplace: bool = False,
    ) -> "RSFData":
        """Subtract the global or axis-wise mean."""

        return self._from_file_op(
            demean_rsf,
            axis=axis,
            nan_policy=nan_policy,
            inplace=inplace,
        )

    def detrend(
        self,
        *,
        axis: int = 1,
        type: str = "linear",
        nan_policy: str = "propagate",
        inplace: bool = False,
    ) -> "RSFData":
        """Remove a constant or linear least-squares trend."""

        return self._from_file_op(
            detrend_rsf,
            axis=axis,
            type=type,
            nan_policy=nan_policy,
            inplace=inplace,
        )

    def decimate(
        self,
        factor: int,
        *,
        axis: int = 1,
        anti_alias: bool = True,
        filter: str = "moving_average",
        inplace: bool = False,
    ) -> "RSFData":
        """Downsample one axis and update its sampling interval."""

        return self._from_file_op(
            decimate_rsf,
            factor=factor,
            axis=axis,
            anti_alias=anti_alias,
            filter=filter,
            inplace=inplace,
        )

    def bandstop(
        self,
        *,
        fmin: float,
        fmax: float,
        axis: int = 1,
        taper: float = 0.0,
        inplace: bool = False,
    ) -> "RSFData":
        """Apply a zero-phase FFT band-stop filter."""

        return self._from_file_op(
            bandstop_rsf,
            fmin=fmin,
            fmax=fmax,
            axis=axis,
            taper=taper,
            inplace=inplace,
        )

    def notch(
        self,
        *,
        f0: float,
        width: float | None = None,
        q: float | None = None,
        axis: int = 1,
        taper: float = 0.0,
        inplace: bool = False,
    ) -> "RSFData":
        """Apply a narrow zero-phase FFT band-stop filter."""

        return self._from_file_op(
            notch_rsf,
            f0=f0,
            width=width,
            q=q,
            axis=axis,
            taper=taper,
            inplace=inplace,
        )

    def localrms(
        self,
        *,
        rect: int,
        axis: int = 1,
        inplace: bool = False,
    ) -> "RSFData":
        """Compute centered sliding RMS along one axis."""

        return self._from_file_op(
            localrms_rsf,
            rect=rect,
            axis=axis,
            inplace=inplace,
        )

    def windowfunc(
        self,
        *,
        kind: str = "hann",
        axis: int = 1,
        periodic: bool = False,
        normalize: bool = False,
        inplace: bool = False,
    ) -> "RSFData":
        """Apply a standard window along one RSF axis."""

        return self._from_file_op(
            windowfunc_rsf,
            kind=kind,
            axis=axis,
            apply=True,
            periodic=periodic,
            normalize=normalize,
            inplace=inplace,
        )

    def psd(
        self,
        *,
        axis: int = 1,
        nfft: int | None = None,
        window: str = "hann",
        average: bool = False,
        scaling: str = "density",
        inplace: bool = False,
    ) -> "RSFData":
        """Compute a one-sided periodogram PSD."""

        return self._from_file_op(
            psd_rsf,
            axis=axis,
            nfft=nfft,
            window=window,
            average=average,
            scaling=scaling,
            inplace=inplace,
        )

    def csd(
        self,
        other: Any,
        *,
        axis: int = 1,
        nfft: int | None = None,
        window: str = "hann",
        scaling: str = "density",
        inplace: bool = False,
    ) -> "RSFData":
        """Compute cross spectral density with another compatible dataset."""

        return self._from_binary_file_op(
            csd_rsf,
            other,
            operand_name="other.rsf",
            operand_axis=axis,
            axis=axis,
            nfft=nfft,
            window=window,
            scaling=scaling,
            inplace=inplace,
        )

    def coherence(
        self,
        other: Any,
        *,
        axis: int = 1,
        nfft: int | None = None,
        window: str = "hann",
        eps: float = 1e-12,
        nperseg: int | None = None,
        noverlap: int | None = None,
        inplace: bool = False,
    ) -> "RSFData":
        """Compute short-segment magnitude-squared coherence."""

        return self._from_binary_file_op(
            coherence_rsf,
            other,
            operand_name="other.rsf",
            operand_axis=axis,
            axis=axis,
            nfft=nfft,
            window=window,
            eps=eps,
            nperseg=nperseg,
            noverlap=noverlap,
            inplace=inplace,
        )

    def spectrogram(
        self,
        *,
        axis: int = 1,
        nperseg: int = 64,
        noverlap: int | None = None,
        window: str = "hann",
        mode: str = "power",
        inplace: bool = False,
    ) -> "RSFData":
        """Compute an axis-1 STFT magnitude or power spectrogram."""

        return self._from_file_op(
            spectrogram_rsf,
            axis=axis,
            nperseg=nperseg,
            noverlap=noverlap,
            window=window,
            mode=mode,
            inplace=inplace,
        )

    def snr(
        self,
        *,
        axis: int = 1,
        signal_window: tuple[int, int] | list[int] | slice | None = None,
        noise_window: tuple[int, int] | list[int] | slice | None = None,
        mode: str = "rms",
        unit: str = "db",
        eps: float = 1e-12,
        inplace: bool = False,
    ) -> "RSFData":
        """Compute per-trace RMS SNR from explicit sample windows."""

        return self._from_file_op(
            snr_rsf,
            axis=axis,
            signal_window=signal_window,
            noise_window=noise_window,
            mode=mode,
            unit=unit,
            eps=eps,
            inplace=inplace,
        )

    def welch(
        self,
        *,
        axis: int = 1,
        nperseg: int = 128,
        noverlap: int | None = None,
        window: str = "hann",
        nfft: int | None = None,
        scaling: str = "density",
        average: bool = True,
        inplace: bool = False,
    ) -> "RSFData":
        """Compute a one-sided Welch PSD."""

        return self._from_file_op(
            welch_rsf,
            axis=axis,
            nperseg=nperseg,
            noverlap=noverlap,
            window=window,
            nfft=nfft,
            scaling=scaling,
            average=average,
            inplace=inplace,
        )

    def welchcsd(
        self,
        other: Any,
        *,
        axis: int = 1,
        nperseg: int = 128,
        noverlap: int | None = None,
        window: str = "hann",
        nfft: int | None = None,
        scaling: str = "density",
        average: bool = True,
        inplace: bool = False,
    ) -> "RSFData":
        """Compute a Welch cross spectral density."""

        return self._from_binary_file_op(
            welchcsd_rsf,
            other,
            operand_name="other.rsf",
            operand_axis=axis,
            axis=axis,
            nperseg=nperseg,
            noverlap=noverlap,
            window=window,
            nfft=nfft,
            scaling=scaling,
            average=average,
            inplace=inplace,
        )

    def transfer(
        self,
        response: Any,
        *,
        axis: int = 1,
        nperseg: int = 128,
        noverlap: int | None = None,
        window: str = "hann",
        nfft: int | None = None,
        method: str = "H1",
        eps: float = 1e-12,
        inplace: bool = False,
    ) -> "RSFData":
        """Estimate an H1 or H2 response from this source to a response."""

        return self._from_binary_file_op(
            transfer_rsf,
            response,
            operand_name="response.rsf",
            operand_axis=axis,
            axis=axis,
            nperseg=nperseg,
            noverlap=noverlap,
            window=window,
            nfft=nfft,
            method=method,
            eps=eps,
            inplace=inplace,
        )

    def whiten(
        self,
        *,
        axis: int = 1,
        floor: float = 1e-6,
        smooth: int = 0,
        phase: str = "preserve",
        inplace: bool = False,
    ) -> "RSFData":
        """Apply phase-preserving spectral whitening."""

        return self._from_file_op(
            whiten_rsf,
            axis=axis,
            floor=floor,
            smooth=smooth,
            phase=phase,
            inplace=inplace,
        )

    def specnorm(
        self,
        *,
        axis: int = 1,
        mode: str = "unit_rms",
        fmin: float | None = None,
        fmax: float | None = None,
        eps: float = 1e-12,
        inplace: bool = False,
    ) -> "RSFData":
        """Normalize spectral RMS or maximum amplitude in a frequency band."""

        return self._from_file_op(
            specnorm_rsf,
            axis=axis,
            mode=mode,
            fmin=fmin,
            fmax=fmax,
            eps=eps,
            inplace=inplace,
        )

    def freqattr(
        self,
        *,
        axis: int = 1,
        input_kind: str = "signal",
        attrs: tuple[str, ...] | list[str] = (
            "dominant",
            "centroid",
            "bandwidth",
        ),
        fmin: float | None = None,
        fmax: float | None = None,
        inplace: bool = False,
    ) -> "RSFData":
        """Compute per-trace frequency attributes."""

        return self._from_file_op(
            freqattr_rsf,
            axis=axis,
            input_kind=input_kind,
            attrs=attrs,
            fmin=fmin,
            fmax=fmax,
            inplace=inplace,
        )

    def firfilter(
        self,
        taps: Any,
        *,
        axis: int = 1,
        mode: str = "same",
        inplace: bool = False,
    ) -> "RSFData":
        """Apply a one-dimensional FIR along a selected RSF axis."""

        return self._from_binary_file_op(
            firfilter_rsf,
            taps,
            operand_name="taps.rsf",
            operand_axis=axis,
            axis=axis,
            mode=mode,
            inplace=inplace,
        )

    def filtfilt(
        self,
        taps: Any,
        *,
        axis: int = 1,
        pad: bool = True,
        inplace: bool = False,
    ) -> "RSFData":
        """Apply a forward/reverse zero-phase FIR approximation."""

        return self._from_binary_file_op(
            filtfilt_rsf,
            taps,
            operand_name="taps.rsf",
            operand_axis=axis,
            axis=axis,
            pad=pad,
            inplace=inplace,
        )

    def bandenergy(
        self,
        *,
        axis: int = 1,
        bands: str | tuple[tuple[float, float], ...] | list[list[float]],
        mode: str = "rms",
        average: bool = True,
        inplace: bool = False,
    ) -> "RSFData":
        """Compute explicit frequency-band energy, power, or RMS."""

        return self._from_file_op(
            bandenergy_rsf,
            axis=axis,
            bands=bands,
            mode=mode,
            average=average,
            inplace=inplace,
        )

    def filterbank(
        self,
        *,
        axis: int = 1,
        bands: str | tuple[tuple[float, float], ...] | list[list[float]],
        numtaps: int = 101,
        window: str = "hann",
        inplace: bool = False,
    ) -> "RSFData":
        """Apply a small FIR band-pass bank and add a highest RSF band axis."""

        return self._from_file_op(
            filterbank_rsf,
            axis=axis,
            bands=bands,
            numtaps=numtaps,
            window=window,
            inplace=inplace,
        )

    def costaper(
        self,
        *,
        widths: int | tuple[int, ...] | list[int] | dict[int, int],
        axes: int | tuple[int, ...] | list[int] | None = None,
        inplace: bool = False,
    ) -> "RSFData":
        """Apply a shape-preserving cosine taper on selected RSF axes."""

        return self._from_file_op(costaper_rsf, widths=widths, axes=axes, inplace=inplace)

    def threshold(
        self,
        *,
        value: float,
        mode: str = "hard",
        substitute: float | complex = 0.0,
        inplace: bool = False,
    ) -> "RSFData":
        """Apply hard or soft magnitude thresholding."""

        return self._from_file_op(
            threshold_rsf,
            value=value,
            mode=mode,
            substitute=substitute,
            inplace=inplace,
        )

    def spectra(
        self,
        *,
        axis: int = 1,
        mode: str = "amplitude",
        average: bool = True,
        inplace: bool = False,
    ) -> "RSFData":
        """Compute a simple one-sided spectrum along one RSF axis."""

        return self._from_file_op(
            spectra_rsf,
            axis=axis,
            mode=mode,
            average=average,
            inplace=inplace,
        )

    def envelope(self, *, axis: int = 1, inplace: bool = False) -> "RSFData":
        """Compute an analytic-signal envelope along one RSF axis."""

        return self._from_file_op(envelope_rsf, axis=axis, inplace=inplace)

    def deriv(
        self,
        *,
        axis: int = 1,
        method: str = "central",
        scale_by_d: bool = True,
        inplace: bool = False,
    ) -> "RSFData":
        """Compute a first finite-difference derivative along one RSF axis."""

        return self._from_file_op(
            deriv_rsf,
            axis=axis,
            method=method,
            scale_by_d=scale_by_d,
            inplace=inplace,
        )

    def causint(
        self,
        *,
        axis: int = 1,
        scale_by_d: bool = False,
        inplace: bool = False,
    ) -> "RSFData":
        """Apply forward causal cumulative integration."""

        return self._from_file_op(
            causint_rsf,
            axis=axis,
            scale_by_d=scale_by_d,
            inplace=inplace,
        )

    def integral(
        self,
        *,
        axis: int = 1,
        method: str = "trapezoid",
        scale_by_d: bool = True,
        inplace: bool = False,
    ) -> "RSFData":
        """Compute a cumulative cumsum or trapezoid integral."""

        return self._from_file_op(
            integral_rsf,
            axis=axis,
            method=method,
            scale_by_d=scale_by_d,
            inplace=inplace,
        )

    def clip2(
        self,
        *,
        min_value: float | None = None,
        max_value: float | None = None,
        pclip: float | None = None,
        symmetric: bool = False,
        inplace: bool = False,
    ) -> "RSFData":
        """Clip amplitudes with explicit or percentile-derived bounds."""

        return self._from_file_op(
            clip2_rsf,
            min_value=min_value,
            max_value=max_value,
            pclip=pclip,
            symmetric=symmetric,
            inplace=inplace,
        )

    def abs(self, *, inplace: bool = False) -> "RSFData":
        """Return sample magnitudes; complex input becomes real magnitude."""

        return self._from_file_op(abs_rsf, inplace=inplace)

    def sign(self, *, inplace: bool = False) -> "RSFData":
        """Return -1, 0, or 1 for real samples."""

        return self._from_file_op(sign_rsf, inplace=inplace)

    def sqrt(self, *, invalid: str = "nan", inplace: bool = False) -> "RSFData":
        """Return real square roots with nan or raise invalid handling."""

        return self._from_file_op(sqrt_rsf, invalid=invalid, inplace=inplace)

    def log(
        self,
        *,
        base: str | float = "e",
        invalid: str = "nan",
        inplace: bool = False,
    ) -> "RSFData":
        """Return real logarithms with configurable base and invalid handling."""

        return self._from_file_op(
            log_rsf,
            base=base,
            invalid=invalid,
            inplace=inplace,
        )

    def exp(self, *, inplace: bool = False) -> "RSFData":
        """Return the real sample-wise exponential."""

        return self._from_file_op(exp_rsf, inplace=inplace)

    def pow(self, exponent: float, *, inplace: bool = False) -> "RSFData":
        """Raise real samples to a scalar exponent."""

        return self._from_file_op(
            pow_rsf,
            exponent=exponent,
            inplace=inplace,
        )

    def histogram(
        self,
        *,
        bins: int = 10,
        min_value: float | None = None,
        max_value: float | None = None,
        density: bool = False,
        inplace: bool = False,
    ) -> "RSFData":
        """Return a two-column bin-center/count-or-density table."""

        return self._from_file_op(
            histogram_rsf,
            bins=bins,
            min_value=min_value,
            max_value=max_value,
            density=density,
            inplace=inplace,
        )

    def quantile(
        self,
        q: float | tuple[float, ...] | list[float],
        *,
        axis: int | None = None,
        nan_policy: str = "propagate",
        inplace: bool = False,
    ) -> "RSFData":
        """Return global or axis-wise quantiles with an explicit q axis."""

        return self._from_file_op(
            quantile_rsf,
            q=q,
            axis=axis,
            nan_policy=nan_policy,
            inplace=inplace,
        )

    def mean(
        self,
        *,
        axis: int | None = None,
        nan_policy: str = "propagate",
        inplace: bool = False,
    ) -> "RSFData":
        """Return a global or axis-wise arithmetic mean."""

        return self._from_file_op(
            mean_rsf,
            axis=axis,
            nan_policy=nan_policy,
            inplace=inplace,
        )

    def rms(
        self,
        *,
        axis: int | None = None,
        nan_policy: str = "propagate",
        inplace: bool = False,
    ) -> "RSFData":
        """Return a global or axis-wise root-mean-square statistic."""

        return self._from_file_op(
            rms_rsf,
            axis=axis,
            nan_policy=nan_policy,
            inplace=inplace,
        )

    def var(
        self,
        *,
        axis: int | None = None,
        ddof: int = 0,
        nan_policy: str = "propagate",
        inplace: bool = False,
    ) -> "RSFData":
        """Return a global or axis-wise variance."""

        return self._from_file_op(
            var_rsf,
            axis=axis,
            ddof=ddof,
            nan_policy=nan_policy,
            inplace=inplace,
        )

    def std(
        self,
        *,
        axis: int | None = None,
        ddof: int = 0,
        nan_policy: str = "propagate",
        inplace: bool = False,
    ) -> "RSFData":
        """Return a global or axis-wise standard deviation."""

        return self._from_file_op(
            std_rsf,
            axis=axis,
            ddof=ddof,
            nan_policy=nan_policy,
            inplace=inplace,
        )

    def median(
        self,
        *,
        axis: int | None = None,
        nan_policy: str = "propagate",
        inplace: bool = False,
    ) -> "RSFData":
        """Return a global or axis-wise median."""

        return self._from_file_op(
            median_rsf,
            axis=axis,
            nan_policy=nan_policy,
            inplace=inplace,
        )

    def range_stats(
        self,
        *,
        axis: int | None = None,
        nan_policy: str = "propagate",
        inplace: bool = False,
    ) -> "RSFData":
        """Return min/max pairs with an explicit two-sample field axis."""

        return self._from_file_op(
            range_rsf,
            axis=axis,
            nan_policy=nan_policy,
            inplace=inplace,
        )

    def isnan(
        self,
        *,
        mode: str = "nan",
        inplace: bool = False,
    ) -> "RSFData":
        """Return a shape-preserving int32 finite/non-finite mask."""

        return self._from_file_op(
            isnan_rsf,
            mode=mode,
            inplace=inplace,
        )

    def fillnan(
        self,
        value: float | complex = 0.0,
        *,
        mode: str = "nan",
        inplace: bool = False,
    ) -> "RSFData":
        """Replace selected non-finite samples while preserving shape and dtype."""

        return self._from_file_op(
            fillnan_rsf,
            value=value,
            mode=mode,
            inplace=inplace,
        )

    def linear(
        self,
        *,
        axis: int = 1,
        n: int | None = None,
        o: float | None = None,
        d: float | None = None,
        fill: float = 0.0,
        inplace: bool = False,
    ) -> "RSFData":
        """Linearly resample one regular RSF axis."""

        return self._from_file_op(
            linear_rsf,
            axis=axis,
            n=n,
            o=o,
            d=d,
            fill=fill,
            inplace=inplace,
        )

    def slice(self, *, axis: int = 3, index: int = 0, inplace: bool = False) -> "RSFData":
        """Extract a fixed zero-based index along one RSF axis."""

        return self._from_file_op(slice_rsf, axis=axis, index=index, inplace=inplace)

    def max1(
        self,
        *,
        axis: int = 1,
        mode: str = "value",
        abs_search: bool = False,
        nan_policy: str = "propagate",
        inplace: bool = False,
    ) -> "RSFData":
        """Pick maxima along one RSF axis as value, index, or coordinate."""

        return self._from_file_op(
            max1_rsf,
            axis=axis,
            mode=mode,
            abs_search=abs_search,
            nan_policy=nan_policy,
            inplace=inplace,
        )

    def autocorr(
        self,
        *,
        axis: int = 1,
        mode: str = "full",
        normalize: bool = False,
        max_lag: int | None = None,
        method: str = "auto",
        inplace: bool = False,
    ) -> "RSFData":
        """Autocorrelate traces along one RSF axis."""

        return self._from_file_op(
            autocorr_rsf,
            axis=axis,
            mode=mode,
            normalize=normalize,
            max_lag=max_lag,
            method=method,
            inplace=inplace,
        )

    def convolve(
        self,
        kernel: Any,
        *,
        axis: int = 1,
        mode: str = "same",
        method: str = "auto",
        inplace: bool = False,
    ) -> "RSFData":
        """Convolve with a 1D or compatible RSFData/array kernel."""

        return self._from_binary_file_op(
            convolve_rsf,
            kernel,
            operand_name="kernel.rsf",
            operand_axis=axis,
            axis=axis,
            mode=mode,
            method=method,
            inplace=inplace,
        )

    def cconv(
        self,
        kernel: Any,
        *,
        axis: int = 1,
        inplace: bool = False,
    ) -> "RSFData":
        """Circularly convolve with a 1D kernel along one RSF axis."""

        return self._from_binary_file_op(
            cconv_rsf,
            kernel,
            operand_name="kernel.rsf",
            operand_axis=axis,
            axis=axis,
            inplace=inplace,
        )

    def envcorr(
        self,
        other: Any,
        *,
        axis: int = 1,
        mode: str = "same",
        normalize: bool = True,
        method: str = "auto",
        inplace: bool = False,
    ) -> "RSFData":
        """Correlate analytic-signal envelopes with another signal or template."""

        return self._from_binary_file_op(
            envcorr_rsf,
            other,
            operand_name="other.rsf",
            operand_axis=axis,
            axis=axis,
            mode=mode,
            normalize=normalize,
            method=method,
            inplace=inplace,
        )

    def shifts(
        self,
        *,
        shift: int,
        axis: int = 1,
        fill: float | complex = 0.0,
        circular: bool = False,
        inplace: bool = False,
    ) -> "RSFData":
        """Shift samples by an integer amount along one RSF axis."""

        return self._from_file_op(
            shifts_rsf,
            shift=shift,
            axis=axis,
            fill=fill,
            circular=circular,
            inplace=inplace,
        )

    def stacks(
        self,
        *,
        axis: int = 1,
        statistic: str = "sum",
        nonzero: bool = False,
        inplace: bool = False,
    ) -> "RSFData":
        """Stack over one RSF axis using sum, mean, rms, or count_nonzero."""

        return self._from_file_op(
            stacks_rsf,
            axis=axis,
            statistic=statistic,
            nonzero=nonzero,
            inplace=inplace,
        )

    def agc(
        self,
        *,
        rect: float,
        axis: int = 1,
        eps: float = 1e-12,
        inplace: bool = False,
    ) -> "RSFData":
        """Apply local RMS automatic gain control."""

        return self._from_file_op(agc_rsf, rect=rect, axis=axis, eps=eps, inplace=inplace)

    def mute(
        self,
        *,
        t0: float,
        v: float,
        axis: int = 1,
        offset_axis: int = 2,
        taper: float = 0.0,
        inplace: bool = False,
    ) -> "RSFData":
        """Apply a linear top mute."""

        return self._from_file_op(
            mute_rsf,
            t0=t0,
            v=v,
            axis=axis,
            offset_axis=offset_axis,
            taper=taper,
            inplace=inplace,
        )

    def mutter(
        self,
        *,
        time_axis: int = 1,
        offset_axis: int = 2,
        v: float,
        t0: float = 0.0,
        side: str = "above",
        taper: int = 0,
        inplace: bool = False,
    ) -> "RSFData":
        """Apply a small linear above/below mute to a 2D gather."""

        return self._from_file_op(
            mutter_rsf,
            time_axis=time_axis,
            offset_axis=offset_axis,
            v=v,
            t0=t0,
            side=side,
            taper=taper,
            inplace=inplace,
        )

    def stack(
        self,
        *,
        axis: int = 2,
        mode: str = "mean",
        nonzero: bool = True,
        inplace: bool = False,
    ) -> "RSFData":
        """Stack over one RSF axis."""

        return self._from_file_op(
            stack_rsf,
            axis=axis,
            mode=mode,
            nonzero=nonzero,
            inplace=inplace,
        )

    def attr(self) -> dict[str, Any]:
        """Return basic data statistics."""

        with tempfile.TemporaryDirectory(prefix="pymada_rsfdata_") as tmp:
            input_path = Path(tmp) / "input.rsf"
            write_rsf(input_path, self._data, self._header.copy())
            stats = attr_rsf(input_path)
        stats["path"] = self._path if self._path is not None else Path("<memory>")
        return stats

    def diff(
        self,
        match: Any,
        *,
        metric: str = "sum_square",
        inplace: bool = False,
    ) -> "RSFData":
        """Return a one-sample whole-dataset difference metric."""

        return self._from_binary_file_op(
            diff_rsf,
            match,
            operand_name="match.rsf",
            operand_axis=1,
            metric=metric,
            inplace=inplace,
        )

    def plot_grey(self, *, output_path: PathLike | None = None, **kwargs: Any) -> Any:
        """Plot this object as a 2D grey image and return the Matplotlib figure."""

        return grey(self._data, self._header, output_path=output_path, **kwargs)

    def plot_graph(self, *, output_path: PathLike | None = None, **kwargs: Any) -> Any:
        """Plot this object as a 1D graph and return the Matplotlib figure."""

        return graph(self._data, self._header, output_path=output_path, **kwargs)

    def _from_file_op(self, op: FileOperation, *, inplace: bool, **kwargs: Any) -> "RSFData":
        with tempfile.TemporaryDirectory(prefix="pymada_rsfdata_") as tmp:
            directory = Path(tmp)
            input_path = directory / "input.rsf"
            output_path = directory / "output.rsf"
            write_rsf(input_path, self._data, self._header.copy())
            result = op(input_path, output_path, **kwargs)
            loaded = read_rsf(result.header_path or output_path)
        return self._from_result(RSFArray(loaded.data, loaded.header), inplace=inplace)

    def _from_binary_file_op(
        self,
        op: FileOperation,
        operand: Any,
        *,
        operand_name: str,
        operand_axis: int,
        inplace: bool,
        **kwargs: Any,
    ) -> "RSFData":
        with tempfile.TemporaryDirectory(prefix="pymada_rsfdata_") as tmp:
            directory = Path(tmp)
            input_path = directory / "input.rsf"
            output_path = directory / "output.rsf"
            write_rsf(input_path, self._data, self._header.copy())
            operand_path = self._write_operand(
                directory,
                operand,
                operand_name,
                axis=operand_axis,
            )
            result = op(input_path, operand_path, output_path, **kwargs)
            loaded = read_rsf(result.header_path or output_path)
        return self._from_result(RSFArray(loaded.data, loaded.header), inplace=inplace)

    def _from_result(self, result: RSFArray, *, inplace: bool) -> "RSFData":
        data = np.ascontiguousarray(np.asarray(result.data).copy())
        header = result.header.copy()
        if inplace:
            self._data = data
            self._header = header
            self._path = result.header_path
            return self
        return RSFData(data, header, path=result.header_path, copy=False)

    def _write_operand(
        self,
        directory: Path,
        operand: Any,
        filename: str,
        *,
        axis: int,
    ) -> Path:
        if isinstance(operand, (str, Path)):
            path = Path(operand).expanduser()
            if not path.exists():
                raise FileNotFoundError(f"second operand RSF does not exist: {path}")
            return path
        path = directory / filename
        if isinstance(operand, RSFData):
            write_rsf(path, operand._data, operand._header.copy())
            return path

        data = np.asarray(operand)
        if data.ndim == 0:
            raise ValueError(
                "second operand must be an RSFData, RSF path, or non-scalar array-like object"
            )
        if data.ndim == 1:
            axis_obj = Hypercube.from_header(self._header).axis(axis)
            header = RSFHeader(
                {
                    "n1": data.size,
                    "o1": 0.0,
                    "d1": axis_obj.d,
                    "label1": axis_obj.label or "Sample",
                    "unit1": axis_obj.unit or "",
                }
            )
        elif data.shape == self._data.shape:
            header = self._header.copy()
        else:
            header = RSFHeader()
        write_rsf(path, data, header)
        return path


__all__ = ["RSFData", "read", "write"]

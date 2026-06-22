# User Guide

## Install

Use the repository root and the documented local interpreter:

```powershell
cd E:\HczDocument\BaiduDisk\BaiduSyncdisk\HCZ_work\CodexProject\HCZ_madagascar\hcz_mada
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install -e ".[test]" --no-build-isolation
```

The absolute paths above record the validated local baseline. Replace them
with your repository path and project-environment Python on another machine;
they are examples, not installation requirements.

This default editable install builds a pure-Python `py3-none-any` wheel. It
does not run CMake and does not require Ninja or a C++ compiler.

If your shell has trouble with extras syntax:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install -e . --no-build-isolation
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install pytest matplotlib
```

The default install does not compile C++. Pure Python must remain usable without
a compiler.

The current PowerShell PATH does not include the environment's scripts
directory. Add it before using the registered `pymada-*` commands by name:

```powershell
$env:PATH = "D:\HczApp\Anaconda\envs\mywork\Scripts;" + $env:PATH
```

Optional C++ builds are explicit and separate from the release baseline:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install -e ".[cpp]" --no-build-isolation
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install -e . --no-build-isolation --config-settings=wheel.cmake=true --config-settings=cmake.define.PYMADAGASCAR_BUILD_CPP=ON
```

That opt-in path also requires a working C++17 compiler.

## Tests and Release Checks

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q -rs
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_release.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_cli_inventory.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_docs_commands.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_examples_inventory.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_learning_notebook.py
```

WSL environment probe:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_wsl_madagascar.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_wsl_madagascar.py --strict
```

The default probe is non-blocking. `--strict` returns failure when the selected
distribution, shell environment, Conda Python, pymadagascar import, or required
Madagascar commands are unavailable. It also accepts `--distro`, `--user`,
`--shell auto|bash|zsh`, and `--conda-env`.
For persistent machine-local defaults, set `PYMADAGASCAR_WSL_USER` and/or
`PYMADAGASCAR_WSL_CONDA_ENV` instead of editing the tracked script.

The validated environment is:

```bash
wsl.exe -d ubuntu2204 -u hcz
conda activate pymadagascar-dev
cd /mnt/e/HczDocument/BaiduDisk/BaiduSyncdisk/HCZ_work/CodexProject/HCZ_madagascar/hcz_mada
python -m pytest -q
python -m pytest -q -rs -m original_madagascar
python tools/check_learning_notebook.py
python tools/check_wsl_madagascar.py --strict
```

Use Linux `/mnt/<drive>/...` paths inside WSL; do not pass Windows `E:\...`
paths to Linux `sf*` programs. An unavailable upstream command is an optional
skip. A failure after the command is found is a real comparison result and
must be investigated rather than converted to a skip.

## Learning Notebook

Open `docs/PYMADAGASCAR_LEARNING_GUIDE.ipynb` with Jupyter, VS Code, or any
notebook viewer.

The notebook is a compact learning guide for project positioning, package
structure, quick usage, geophysical topic navigation, and the operator/
inversion foundation. It is not the API stability authority; use
`API_AND_COMPATIBILITY.md` for API contracts and `KNOWN_LIMITATIONS.md` for
detailed boundaries. The eight Markdown documents remain authoritative.

## Console Scripts

The 42 registered console scripts are:

```text
pymada-info, pymada-get, pymada-disfil, pymada-real, pymada-imag,
pymada-cmplx, pymada-rtoc, pymada-noise, pymada-ricker, pymada-spike,
pymada-math, pymada-clip, pymada-window, pymada-attr, pymada-put, pymada-dd, pymada-cat,
pymada-transp, pymada-fft, pymada-fft1, pymada-bandpass, pymada-byte, pymada-smooth,
pymada-boxsmooth, pymada-laplac, pymada-trapez, pymada-cosft, pymada-spectra2,
pymada-remap1, pymada-spline, pymada-t2warp, pymada-mask, pymada-cut, pymada-reverse, pymada-pad,
pymada-spray, pymada-scale, pymada-rotate, pymada-stack,
pymada-matmult, pymada-match, pymada-linefit
```

Examples:

```powershell
pymada-spike n1=10 k1=5 out=spike.rsf
pymada-info spike.rsf
pymada-clip spike.rsf out=clipped.rsf clip=1 value=1
pymada-window spike.rsf out=win.rsf n1=5 f1=0
pymada-fft win.rsf out=fft.rsf axis=1
pymada-fft1 win.rsf out=fft1.rsf axis=1
pymada-cosft win.rsf out=cosft.rsf axis=1
pymada-spectra2 panel.rsf out=spectra2.rsf axes=1,2
pymada-remap1 win.rsf out=remap1.rsf n=9 o=0 d=0.5
pymada-spline win.rsf out=spline.rsf n=9 o=0 d=0.5
pymada-t2warp win.rsf out=t2warp.rsf pad=9
pymada-matmult vector.rsf matrix.rsf out=matmult.rsf
pymada-match filter.rsf data.rsf out=matched.rsf
pymada-linefit table.rsf out=linefit.rsf n=100 o=0 d=1
pymada-laplac win.rsf out=laplac.rsf axis=1 spacing_from_header=n
pymada-trapez win.rsf out=trapez.rsf axis=1 frequency=0.05,0.1,0.4,0.45
pymada-stack win.rsf out=stack.rsf axis=1 mode=sum
pymada-pad win.rsf out=padded.rsf beg1=1 end1=1
pymada-spray win.rsf out=sprayed.rsf axis=2 n=3
```

All other CLI modules are module-only and must be called with `python -m`.
Names printed by older module help are compatibility labels only; the
authoritative installed command list is the 42-entry console-script inventory
above.

## CLI Module Inventory

There are 146 user-facing CLI modules:

```text
abs, acoustic2d, add, agc, attr, autocorr, bandenergy, bandpass, bandstop, bin, boxsmooth,
byte, cat, causint, cconjgrad, cconv, cdottest, clip, clip2, cmplx, coherence,
conjgrad, conv, convolve, corr, cosft, costaper, cp, csd, cut, dd, decimate, demean,
deriv, detrend,
diff, disfil, div, dottest,
envcorr, envelope, exp, fft, fft1, fillnan, filterbank, filtfilt, firfilter, firwin,
fk, fkfilter, freqattr, freqz, gain, get, graph, grey,
headerattr, headercut, headermath, headersort, headerwindow, highpass,
histogram, ifft, imag, info, integral, interleave, iradon, isnan, kirchhoff,
laplac, linear, linefit, localrms, log, lowpass, mask, math, match, matmult, max, max1, mean, median, min, mul,
mute, mutter, nmo, noise, normalize, notch, pad, pow, psd, put, quantile, radon,
range, real,
remap1, reshape, reverse, rfft, ricker, rm, rms, rotate, rtoc, scale, segyread, segywrite,
semblance, shifts, sign, slice, smooth, snr, specnorm, spectra, spectra2, spectrogram,
spike, spray, spline, sqrt, stack, stacks, std, t2warp, threshold, tile, tpow, transfer, trapez, transp,
var, welch, welchcsd, whiten, wiggle, window, windowfunc, xcorr
```

Module-only examples:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.cp input.rsf out=copy.rsf
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.mul a.rsf b.rsf out=mul.rsf
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.headerwindow data.rsf mask.rsf out=win.rsf axis=2
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.headerattr headers.rsf key=offset,cdp
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.headermath headers.rsf out=headers2.rsf out_key=offset2 expr=offset*offset
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.headersort headers2.rsf out=sorted.rsf key=offset reverse=n
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.dottest matrix.rsf seed=0
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.cdottest cmatrix.rsf seed=0
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.conjgrad matrix.rsf rhs.rsf out=x.rsf mode=normal niter=20 tol=1e-6
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.cconjgrad cmatrix.rsf crhs.rsf out=cx.rsf mode=normal niter=20 tol=1e-6
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.costaper input.rsf out=taper.rsf width1=8
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.threshold taper.rsf out=threshold.rsf value=0.1 mode=soft
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.spectra threshold.rsf out=spectra.rsf axis=1 mode=amplitude average=y
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.fft1 threshold.rsf out=fft1.rsf axis=1
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.cosft threshold.rsf out=cosft.rsf axis=1
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.spectra2 panel.rsf out=spectra2.rsf axes=1,2
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.remap1 trace.rsf out=remap1.rsf n=200 o=0 d=0.004
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.spline trace.rsf out=spline.rsf n=200 o=0 d=0.004
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.t2warp trace.rsf out=t2warp.rsf pad=200
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.matmult vector.rsf matrix.rsf out=matmult.rsf
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.match filter.rsf data.rsf out=matched.rsf
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.linefit table.rsf out=linefit.rsf n=100 o=0 d=1
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.envelope threshold.rsf out=envelope.rsf axis=1
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.linear input.rsf out=resampled.rsf axis=1 n=200 o=0 d=0.004
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.bin points.rsf out=grid.rsf x=0 y=1 value=2 n1=50 o1=0 d1=1 n2=40 o2=0 d2=1 statistic=mean
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.slice cube.rsf out=slice.rsf axis=3 index=0
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.max1 panel.rsf out=pick.rsf axis=1 mode=coord abs=y
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.autocorr trace.rsf out=autocorr.rsf axis=1 mode=full normalize=y max_lag=50
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.convolve data.rsf wavelet.rsf out=conv.rsf axis=1 mode=same
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.cconv data.rsf kernel.rsf out=cconv.rsf axis=1
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.envcorr a.rsf b.rsf out=envcorr.rsf axis=1 mode=same normalize=y
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.shifts data.rsf out=shifted.rsf axis=1 shift=3 fill=0
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.stacks gather.rsf out=stack.rsf axis=2 statistic=mean
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.deriv trace.rsf out=deriv.rsf axis=1 method=central scale_by_d=y
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.causint trace.rsf out=causint.rsf axis=1 scale_by_d=y
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.integral trace.rsf out=integral.rsf axis=1 method=trapezoid
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.clip2 gather.rsf out=clip.rsf pclip=99 symmetric=y
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.mutter gather.rsf out=muted.rsf v=1800 t0=0.015 side=above taper=6
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.diff gather.rsf muted.rsf out=diff.rsf metric=rms
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.abs input.rsf out=abs.rsf
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.sign input.rsf out=sign.rsf
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.sqrt abs.rsf out=sqrt.rsf invalid=nan
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.log abs.rsf out=log.rsf base=e invalid=nan
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.exp input.rsf out=exp.rsf
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.pow input.rsf out=pow.rsf exponent=2
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.histogram input.rsf out=hist.rsf bins=50 min=-1 max=1
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.quantile input.rsf out=q.rsf q=0.05,0.5,0.95
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.mean input.rsf out=mean.rsf
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.rms input.rsf out=rms.rsf axis=1 nan_policy=omit
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.var input.rsf out=var.rsf axis=2 ddof=0
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.std input.rsf out=std.rsf
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.median input.rsf out=median.rsf axis=1
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.range input.rsf out=range.rsf nan_policy=omit
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.isnan input.rsf out=mask.rsf mode=nonfinite
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.fillnan input.rsf out=filled.rsf mode=nonfinite value=0
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.demean input.rsf out=demean.rsf axis=1 nan_policy=omit
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.detrend input.rsf out=detrend.rsf axis=1 type=linear
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.decimate input.rsf out=decimated.rsf axis=1 factor=4 anti_alias=y
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.bandstop input.rsf out=bandstop.rsf axis=1 fmin=45 fmax=55 taper=2
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.notch input.rsf out=notch.rsf axis=1 f0=50 width=4
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.localrms input.rsf out=localrms.rsf axis=1 rect=21
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.windowfunc out=window.rsf n1=128 kind=hann
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.psd input.rsf out=psd.rsf axis=1 average=y scaling=density
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.csd a.rsf b.rsf out=csd.rsf axis=1
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.coherence a.rsf b.rsf out=coherence.rsf axis=1 nperseg=128 noverlap=64
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.spectrogram input.rsf out=spectrogram.rsf axis=1 nperseg=64 noverlap=32 mode=power
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.snr input.rsf out=snr.rsf axis=1 signal=40:120 noise=0:30 unit=db
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.welch input.rsf out=welch.rsf axis=1 nperseg=128 noverlap=64 average=y
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.welchcsd source.rsf response.rsf out=welchcsd.rsf axis=1 nperseg=128 noverlap=64
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.transfer source.rsf response.rsf out=transfer.rsf axis=1 method=H1 nperseg=128 noverlap=64
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.whiten input.rsf out=whitened.rsf axis=1 floor=1e-6 smooth=5
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.specnorm input.rsf out=normalized.rsf axis=1 mode=unit_rms fmin=5 fmax=60
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.freqattr input.rsf out=attributes.rsf axis=1 attrs=dominant,centroid,bandwidth fmin=5 fmax=80
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.firwin out=taps.rsf numtaps=101 cutoff=35 fs=500 window=hamming
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.firfilter input.rsf taps.rsf out=filtered.rsf axis=1
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.filtfilt input.rsf taps.rsf out=zero_phase.rsf axis=1 pad=y
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.freqz taps.rsf out=response.rsf fs=500 nfft=1024 mode=amplitude
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.bandenergy input.rsf out=energy.rsf axis=1 bands=10:30,60:90 mode=rms average=y
D:\HczApp\Anaconda\envs\mywork\python.exe -m pymadagascar.cli.filterbank input.rsf out=bank.rsf axis=1 bands=10:30,60:90 numtaps=101
```

## Parameter Style

CLI tools support Madagascar-style `key=value` arguments and a stable `par=file`
subset. Parameter files support `key=value`, blank lines, `#` comments, quoted
strings, list/repeat syntax, and left-to-right override order.

## Python API

```python
from pymadagascar import RSFData, read, write
from pymadagascar.generic.array_math import multiply_rsf, divide_rsf
from pymadagascar.generic.header_mask import header_window_rsf, header_cut_rsf
from pymadagascar.generic.header_table import read_header_table, write_header_table
from pymadagascar.generic.difference import difference_metric, diff_rsf
from pymadagascar.generic.linear_operator import MatrixOperator, dot_test, conjugate_gradient_normal
from pymadagascar.generic.sampling import linear_resample, bin_2d, slice_array, max1
from pymadagascar.generic.statistics import mean, rms, variance, std, median, range_stats, isnan_mask, fillnan
from pymadagascar.generic.unary import absolute, sign, sqrt, log, exp, power, histogram, quantile
from pymadagascar.io.rsf import read_rsf, write_rsf
from pymadagascar.seismic.mute import mutter, mutter_rsf
from pymadagascar.signal.calculus import deriv, causal_integrate, integral
from pymadagascar.signal.convolution import autocorr, convolve, circular_convolve, envelope_correlation
from pymadagascar.signal.conditioning import clip2, shift
from pymadagascar.signal.preprocessing import cosine_taper, threshold, spectra, envelope
from pymadagascar.signal.qc import demean, detrend, decimate, bandstop, notch, local_rms
from pymadagascar.signal.spectral import (
    window_function, apply_window, psd, csd, coherence, spectrogram, snr,
    welch_psd, welch_csd, transfer_function, spectral_whiten,
    spectral_normalize, frequency_attributes,
)
from pymadagascar.signal.fir import (
    firwin, fir_filter, zero_phase_fir_filter, freq_response,
    band_energy, filter_bank,
)
```

`RSFData` is a high-level convenience wrapper over stable lower-level RSF APIs.
Most high-level transforms return a new `RSFData` object by default rather than
mutating in place. Transform methods that expose `inplace=True` return the same
object after replacing its data and header. Shape-reducing and scalar methods
follow the same rule, so use their default non-mutating form when the original
volume must remain available.

RSFData signal preprocessing chain:

```python
from pymadagascar import read

processed = (
    read("input.rsf")
    .costaper(widths={1: 8})
    .threshold(value=0.1, mode="soft")
    .envelope(axis=1)
)
processed.write("envelope.rsf")

spectrum = read("input.rsf").spectra(axis=1, mode="amplitude", average=True)
spectrum.write("spectrum.rsf")
```

RSFData generic sampling chain:

```python
from pymadagascar import read

resampled = read("panel.rsf").linear(axis=1, n=200, o=0.0, d=0.004)
picked = resampled.max1(axis=1, mode="coord", abs_search=True)
picked.write("picked_coordinates.rsf")

slice2d = read("cube.rsf").slice(axis=3, index=0)
slice2d.write("slice2d.rsf")
```

`bin` works on table-like point RSFs and is intentionally not exposed as an
`RSFData` chain method.

RSFData signal correlation and conditioning chain:

```python
from pymadagascar import read

processed = (
    read("gather.rsf")
    .convolve([0.25, 0.5, 0.25], axis=1, mode="same")
    .shifts(shift=2, axis=1)
    .stacks(axis=2, statistic="mean")
)
processed.write("conditioned_stack.rsf")

autocorr = read("trace.rsf").autocorr(axis=1, max_lag=50, normalize=True)
similarity = read("trace.rsf").envcorr(read("template.rsf"), axis=1)
```

The second operand of `convolve`, `cconv`, `envcorr`, `csd`, `coherence`,
`welchcsd`, `transfer`, and `diff` may be an
`RSFData`, an RSF path, a NumPy array, or a Python list. A 1D array/list is
treated as a template on the selected axis; a multidimensional array must meet
the lower-level operation's shape rules. Path inputs keep their own RSF
metadata.

RSFData axis calculus, amplitude conditioning, and gather QC:

```python
from pymadagascar import read

conditioned = (
    read("trace.rsf")
    .clip2(pclip=99.0, symmetric=True)
    .deriv(axis=1, method="central")
    .causint(axis=1, scale_by_d=True)
)
conditioned.write("conditioned_trace.rsf")

muted = read("gather.rsf").mutter(
    v=1800.0,
    t0=0.015,
    side="above",
    taper=6,
)
metric = read("gather.rsf").diff(muted, metric="rms")
metric.write("mute_difference.rsf")
```

RSFData unary transforms and distribution QC:

```python
from pymadagascar import read

amplitude = read("input.rsf").abs().sqrt().pow(2.0)
amplitude.write("amplitude.rsf")

hist = read("input.rsf").histogram(bins=50, min_value=-1.0, max_value=1.0)
hist.write("histogram.rsf")

quantiles = read("input.rsf").quantile([0.05, 0.5, 0.95])
quantiles.write("quantiles.rsf")
```

`RSFData.abs()` is intentionally named like the mathematical operation and is
safe as an instance method. The lower-level function is named `absolute()` to
avoid shadowing Python's built-in `abs`. `RSFData.pow()` is sample-wise scalar
power; it is not upstream `sfpow`'s coordinate-axis gain, which remains covered
by the existing `tpow` subset.

RSFData robust statistics and non-finite QC:

```python
from pymadagascar import read

clean = read("input.rsf").fillnan(0.0, mode="nonfinite")
trace_rms = clean.rms(axis=1)
trace_range = clean.range_stats(axis=1)
mask = read("input.rsf").isnan(mode="nonfinite")

trace_rms.write("trace_rms.rsf")
trace_range.write("trace_range.rsf")
mask.write("nonfinite_mask.rsf")
```

Global statistics return one-sample float64 `RSFData` objects. Axis statistics
remove the selected 1-based RSF axis. `range_stats()` uses a new two-sample RSF
axis 1 with `range_fields=min,max`; `isnan()` returns an int32 0/1 mask.

RSFData signal and small-gather QC chain:

```python
from pymadagascar import read

qc = (
    read("gather.rsf")
    .demean(axis=1, nan_policy="omit")
    .detrend(axis=1, type="linear")
    .notch(axis=1, f0=50.0, width=4.0, taper=1.0)
    .decimate(4, axis=1, anti_alias=True)
    .localrms(axis=1, rect=21)
)
qc.write("gather_qc.rsf")
```

`decimate` changes only the selected axis: `n#` is reduced, `d#` is multiplied
by the factor, and `o#` is preserved. The other five methods preserve shape.

RSFData spectral QC chain:

```python
from pymadagascar import read

source = read("gather.rsf")
windowed = source.windowfunc(kind="hann", axis=1)
average_psd = windowed.psd(axis=1, average=True, scaling="density")
coherent = source.coherence(
    read("reference.rsf"),
    axis=1,
    nperseg=128,
    noverlap=64,
)
time_frequency = source.spectrogram(axis=1, nperseg=64, noverlap=32)
trace_snr = source.snr(axis=1, signal_window=(40, 120), noise_window=(0, 30))
```

`psd` and `csd` are single-periodogram estimates. `coherence` performs simple
short-segment averaging. `spectrogram` currently supports RSF axis 1 and emits
frequency on output axis 1 and window-center time on axis 2. `snr` requires an
explicit noise window or derives noise from the complement of a supplied
signal window.

RSFData spectral averaging and attributes:

```python
from pymadagascar import read

source = read("source.rsf")
response = read("response.rsf")
welch_density = source.welch(nperseg=128, noverlap=64, average=True)
cross_density = source.welchcsd(response, nperseg=128, noverlap=64)
response_h1 = source.transfer(response, nperseg=128, noverlap=64, method="H1")
conditioned = source.whiten(smooth=5).specnorm(fmin=5.0, fmax=60.0)
attributes = conditioned.freqattr(fmin=5.0, fmax=80.0)
```

`welch` and `welchcsd` average overlapping, windowed segment spectra.
`transfer` returns complex H1 or H2 response estimates. `whiten` preserves
phase while stabilizing spectral amplitudes, and `specnorm` applies one
trace-wise scalar derived from the selected spectrum. `freqattr` reports
dominant frequency, power centroid, and power-weighted standard-deviation
bandwidth.

RSFData FIR and band-QC chain:

```python
from pymadagascar import read
from pymadagascar.signal.fir import firwin

source = read("gather.rsf")
taps = firwin(101, 35.0, fs=500.0, window="hamming")
filtered = source.firfilter(taps)
zero_phase = source.filtfilt(taps, pad=True)
energy = zero_phase.bandenergy(bands="10:30,60:90", average=False)
bank = source.filterbank(bands="10:30,60:90", numtaps=101)
```

`firfilter` and `filtfilt` accept taps as an `RSFData`, RSF path, 1D NumPy
array, or Python list. Generated taps and file-backed data must use matching
sample spacing. `bandenergy` removes the analyzed axis and adds frequency-band
axis 1; `filterbank` preserves all source axes and adds the band axis as the
highest RSF axis. `firwin` and `freq_response` remain standalone functions
because they generate or diagnose a filter rather than transform an existing
dataset.

## Use by Topic

- **General RSF work:** start with `read_rsf`/`write_rsf`, `RSFData`,
  `window`, `put/get/info`, `dd`, `cat`, `transp`, and the basic RSF workflow.
- **Signal processing:** combine FFT/filter, taper, spectra, envelope,
  convolution/correlation, shifts, calculus, demean/detrend, decimation,
  notch/band-stop, local RMS, standard windows, PSD/CSD/coherence,
  spectrogram/SNR QC, Welch estimates, FIR design/filtering, band energy, and the
  `fft_bandpass_workflow.py` or focused signal demos.
- **Statistics and QC:** use `attr`, clipping/thresholding, histogram,
  quantile, robust statistics, non-finite masks/filling, and the two
  distribution-QC demos.
- **Seismic gather QC:** use gain/AGC, mute/mutter, stack/stacks, max1, bin,
  slice, quicklook plots, and `seismic_basic_agc_mute_stack_workflow.py`.
- **Operators and least squares:** use `MatrixOperator`, dot tests,
  composition helpers, regularization operators, and the prototype
  least-squares problem diagnostics only for small in-memory problems. Current
  CG/CGNR default functions retain their original result contract. The
  direct-module prototype helpers `run_cg_with_history` and
  `run_cgnr_with_history` optionally produce `SolverResult`/`SolverHistory`;
  they are not root/API exports or CLI features. Bounded `run_cgls` and
  `run_cgls_problem` now solve small real/complex in-memory problems and
  return the same diagnostics containers. Regularization must be supplied
  through `LeastSquaresProblem`; optional right/model-space preconditioners use
  `IdentityPreconditioner` or `DiagonalPreconditioner` with `x=M z`. Results
  remain model-space, while convergence residual metadata is explicit about
  latent versus model space. Bounded `run_lsqr` and `run_lsqr_problem` provide
  an unpreconditioned direct-module LSQR prototype for small deterministic
  least-squares problems, including regularized `LeastSquaresProblem` objects
  through the same augmented system and nonzero `x0` through a shifted residual
  correction solve. Preconditioned LSQR and domain inversion remain
  unimplemented. Preconditioning changes variables/scaling, while
  regularization changes the objective. Start with
  `linear_operator_tools_demo.py` for the stable small operator subset, and
  `examples/my_workflows/lsqr_minimal_example.py` for the bounded LSQR learning
  prototype.
- **Prototype geophysics:** NMO, semblance, FK, Radon, SEG-Y, acoustic2d, and
  Kirchhoff require their documented dimensionality and geometry assumptions.
  Treat them as controlled prototypes, not drop-in Madagascar replacements.

Stage D-1 provides a retained DAS-specific workflow prototype by combining the
current RSF, signal, correlation, picking, and plotting tools:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\das_void_diffraction_workflow.py
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\das_void_diffraction_workflow.py D:\tmp\pymada_das_void
```

Without an output argument the workflow creates a system temporary directory.
It writes raw and FK-filtered RSF gathers, raw and curve-overlay PNGs, a
simulated-pick CSV, and an inversion JSON. The synthetic array is built as
`data[time, channel]` and transposed to project RSF storage convention with
time on axis 1. This is a kinematic workflow prototype; HDF5/TDMS/DAT adapters,
gauge-length response, production channel geometry, chunking, and field-data
fixtures remain future work.
It remains available for experiments, but D-2 adapter, gauge-response, and
automatic-picking work is not the current development route.

## Seismic Topic S1 Contract Workflow

Run the deterministic S1 workflow from the repository root:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_signal_contract_workflow.py
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_signal_contract_workflow.py D:\tmp\pymada_s1
```

Without an output argument, the workflow creates a new system temporary
directory. It writes a regular signed-offset synthetic gather, processed
gather, stack, stack PSD, quicklook PNG, and JSON acceptance metrics. Temporary
intermediate RSFs record the existing demean, detrend, bandpass, and AGC steps.

This workflow uses `pymadagascar.testing.seismic_fixtures`, which is an internal
testing module rather than a stable public API. It requires neither original
Madagascar nor the optional C++ extension. It is a contract regression, not a
field-scale or production seismic-processing recipe.

## Seismic Topic S2 Metrics Workflow

Run the deterministic S2 metrics/QC workflow from the repository root:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_signal_metrics_workflow.py
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_signal_metrics_workflow.py D:\tmp\pymada_s2
```

Without an output argument, the workflow creates a new system temporary
directory. It writes raw, intermediate, processed, and stacked RSFs, a
processed-gather quicklook PNG, and `s2_qc_report.json`.

The report separates filter-stage SNR/frequency metrics from final AGC, mute,
and stack metrics. It records explicit windows and bands, scalar metrics, and
broad boolean regression checks without local absolute paths. The
`pymadagascar.testing.seismic_metrics` helper and JSON schema are internal
testing contracts. This is a repeatable QC/regression example, not a production
processing workflow or field-data acceptance report.

## Seismic Topic S3 NMO Contract Workflow

Run the deterministic S3 NMO prototype contract workflow from the repository
root:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_nmo_contract_workflow.py
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_nmo_contract_workflow.py D:\tmp\pymada_s3
```

Without an output argument, the workflow creates a new system temporary
directory. It writes the raw S1 hyperbolic gather, correct-velocity NMO gather,
wrong-velocity NMO gather, pre/post/wrong-velocity stacks, a corrected-gather
quicklook PNG, and `s3_nmo_qc_report.json`.

The report checks event flattening, correct-vs-wrong velocity behavior, stack
peak increase and timing, finite samples, noise-window behavior, and
axis/header preservation. It runs the existing NMO prototype with `half=n`
because S1 stores full signed offsets. This is a prototype contract regression,
not velocity analysis, production NMO, field-data QC, or a public JSON format.

## Seismic Topic S4-1 Semblance Contract Workflow

Run the deterministic S4-1 Semblance prototype contract workflow from the
repository root:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_semblance_contract_workflow.py
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_semblance_contract_workflow.py D:\tmp\pymada_s4_semblance
```

Without an output argument, the workflow creates a new system temporary
directory. It writes the raw S1 hyperbolic gather, a Semblance velocity panel,
true-velocity and wrong-velocity NMO stacks, a velocity-panel quicklook PNG,
and `s4_semblance_qc_report.json`.

The report records the `Mvscan.c` source-audit target, true-vs-wrong velocity
response, velocity-panel peak metrics, finite fraction, and header/axis
checks. The workflow does not call original Madagascar or require C++. It is a
prototype contract regression for the current Python Semblance subset, not a
full `sfvscan` clone, production velocity-picking flow, field-data QC process,
or public JSON format.

## Seismic Topic S4-2 Geometry Contract Workflow

Run the deterministic S4-2 small-gather geometry contract workflow from the
repository root:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_geometry_contract_workflow.py
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_geometry_contract_workflow.py D:\tmp\pymada_s4_geometry
```

Without an output argument, the workflow creates a new system temporary
directory. It writes an S1-compatible regular signed-offset gather RSF, an
explicit offset-vector RSF, a minimal numeric source/receiver table RSF, and
`s4_geometry_report.json`.

The report checks that ordinary RSF `o2/d2/n2` offsets, the explicit offset
vector, and the source/receiver table agree; that
`offset = receiver_x - source_x`; that
`midpoint = 0.5 * (source_x + receiver_x)`; and that the SEG-Y trace-header
boundary remains out of scope. This workflow uses
`pymadagascar.testing.seismic_geometry`, which is internal testing
infrastructure. It is not a production geometry loader, not `sfsegyheader`, not
a SEG-Y trace-header adapter, not a survey database, and not a public JSON
format.

## Seismic Topic S4-3 FK Contract Workflow

Run the deterministic S4-3 FK prototype contract workflow from the repository
root:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_fk_contract_workflow.py
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_fk_contract_workflow.py D:\tmp\pymada_s4_fk
```

Without an output argument, the workflow creates a new system temporary
directory. It writes a deterministic regular plane-wave panel RSF, an FK
spectrum RSF, an FK-filtered panel RSF, a spectrum quicklook PNG, and
`s4_fk_qc_report.json`.

The report records that no direct `Mfk.c` generic FK transform source was
found and uses `../src-master/system/generic/Mdipfilter.c` as the nearest
dip/f-k/fan-filter reference. It checks analytic FK peak position, target
apparent-velocity preservation, reject apparent-velocity suppression, finite
values, and header/axis metadata. The workflow does not call original
Madagascar or require C++. It is a prototype contract regression for the
current Python FK subset, not a full `sfdipfilter` clone, field-data FK
process, Radon workflow, or public JSON format.

## Seismic Topic S5 Integrated Workflow

Run the deterministic S5 integrated small-gather processing workflow from the
repository root:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_small_gather_processing_workflow.py
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_small_gather_processing_workflow.py D:\tmp\pymada_s5
```

Without an output argument, the workflow creates a new system temporary
directory. It writes the raw S1 hyperbolic gather, explicit offset vector,
minimal source/receiver table, processed gather, NMO true/wrong gathers,
pre/post/wrong stacks, Semblance panel, FK spectrum, FK-filtered gather,
quicklook PNGs, and `s5_integrated_qc_report.json`.

The report combines S4-2 geometry checks, S2-style pipeline metrics, S3 NMO
true-vs-wrong behavior, S4-1 Semblance peak checks, S4-3 FK finite/header/energy
checks, stack ratios, and a boolean rollup. It does not call original
Madagascar or require C++. It is a small deterministic regression workflow,
not production velocity analysis, full FK/Radon processing, field-data QC,
SEG-Y/header work, or a public JSON format.

## Seismic Topic S6-2 Slant-Stack Contract Workflow

Run the deterministic S6-2 small slant-stack contract workflow from the
repository root:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_slant_stack_contract_workflow.py
D:\HczApp\Anaconda\envs\mywork\python.exe examples\my_workflows\seismic_slant_stack_contract_workflow.py D:\tmp\pymada_s6_slant
```

Without an output argument, the workflow creates a new system temporary
directory. It writes an analytic linear-event gather, an adjoint slant-stack
panel, a small Radon model, a modeled gather, a panel quicklook PNG, and
`s6_slant_stack_qc_report.json`.

The report records that `radon` is used as the adjoint slant stack `m=A^T d`
and `iradon` is used as modeling `d=A m`. It checks dot-test consistency,
true-slope versus wrong-slope response, modeled-event predictability, finite
values, and header/axis metadata. The workflow does not call original
Madagascar or require C++. It is a prototype contract regression for the
current Python slant-stack subset, not a full `sfslant` clone, not
high-resolution `sfradon`, not solved Radon inversion, not velocity picking,
and not a public JSON format.

## Naming Guide

| Names | Project meaning |
| --- | --- |
| `mute` / `mutter` | `mute` is the older top-mute API: early samples only, at least 2D, taper in physical time units. `mutter` is the newer 2D regular-axis subset with `side=above|below` and taper in samples. Both remain for compatibility. |
| `stack` / `stacks` | `stack` is the classic seismic stack subset, defaulting to nonzero-fold mean. `stacks`/`stack_along_axis` is the generic statistic subset with sum/mean/rms/count_nonzero. |
| `clip` / `clip2` / `threshold` | `clip` applies a symmetric explicit amplitude cap. `clip2` supports one/two-sided or percentile-derived caps. `threshold` suppresses small magnitudes with hard or soft shrinkage. |
| `conv` / `convolve` | Both CLI modules call the same two-input convolution implementation. `conv` is the older compatibility module; `convolve` is the clearer module-only name and Python API name. |
| `corr` / `xcorr` / `autocorr` / `envcorr` / `cconv` | `corr` is two-input cross-correlation; `xcorr` is the older trace-autocorrelation module; `autocorr` adds normalization and max-lag selection; `envcorr` correlates envelopes; `cconv` is circular convolution. |
| `dd` / `diff` | `dd` copies or converts RSF dtype/endian/form. `diff` computes one whole-dataset scalar QC metric. |
| `get` / `info` / `attr` / `headerattr` | `get` queries ordinary RSF header keys; `info` describes file/header layout; `attr` reports binary-array statistics; `headerattr` reports columns in the minimal header-table subset. |

## Examples

Focused getting-started and I/O demos:

- `examples/local_quickstart.py`, `examples/read_write_rsf_demo.py`,
  `examples/pythonic_usage_demo.py`, `examples/get_demo.py`, and
  `examples/disfil_demo.py`.
- `examples/spike_demo.py`, `examples/math_demo.py`,
  `examples/window_demo.py`, and `examples/plot_demo.py`.

Focused generic and format demos:

- `examples/byte_demo.py`, `examples/cat_demo.py`,
  `examples/transp_demo.py`, and `examples/complex_tools_demo.py`.
- `examples/cp_rm_min_max_demo.py`,
  `examples/mul_div_tpow_interleave_demo.py`,
  `examples/mask_cut_reverse_demo.py`,
  `examples/header_window_cut_demo.py`, and
  `examples/header_table_tools_demo.py`.

Signal, seismic, operator, and prototype demos:

- `examples/noise_demo.py`, `examples/ricker_demo.py`,
  `examples/smooth_demo.py`, and `examples/signal_preprocessing_demo.py`.
- `examples/signal_correlation_conditioning_demo.py`,
  `examples/axis_calculus_conditioning_demo.py`,
  `examples/seismic_gather_qc_demo.py`, and
  `examples/generic_sampling_demo.py`.
- `examples/unary_distribution_qc_demo.py` and
  `examples/robust_statistics_nan_qc_demo.py`.
- `examples/signal_qc_foundation_demo.py` demonstrates bias/trend removal,
  narrow-band suppression, decimation, local RMS, and an RSFData chain.
- `examples/spectral_qc_demo.py` demonstrates standard windows, PSD,
  coherence, spectrogram, explicit-window SNR, and an RSFData chain.
- `examples/spectral_averaging_attributes_demo.py` demonstrates Welch PSD/CSD,
  H1 transfer estimation, whitening, spectral normalization, frequency
  attributes, and an RSFData chain.
- `examples/fir_filter_design_demo.py` demonstrates FIR coefficient design,
  response diagnostics, single/forward-reverse filtering, band energy, a
  filter bank, and an RSFData chain.
- `examples/linear_operator_tools_demo.py` and
  `examples/kirchhoff_demo.py`.

All 34 top-level examples accept an optional output-directory argument or use a
system temporary directory. The inventory/smoke tests execute them with pytest
temporary directories. The fifteen scripts under `examples/my_workflows/` are
longer compositional workflows; top-level examples remain focused feature
demos, so the apparent overlap is intentional rather than duplicate ownership.

For predictable local runs, pass an output directory explicitly:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe examples\local_quickstart.py D:\tmp\pymada_quickstart
```

Workflow scripts use a newly created system temporary directory when no output
directory is supplied. Historical `_tmp_*` and `examples/*_output` directories
are ignored by version control; release smoke tests never write new files into
`examples/`.

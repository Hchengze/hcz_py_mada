# Pythonic RSFData Usage

`RSFData` is a light high-level wrapper for local Python workflows. It does not
replace the stable low-level APIs (`read_rsf`, `write_rsf`, file-backed CLI
helpers, or individual processing functions). It is a convenience layer for
working with RSF data as ordinary Python objects.

## Basic Pattern

```python
from pymadagascar import read

d = read("shot.rsf")
processed = (
    d.window(axis=1, f=0, n=1000)
     .bandpass(flo=5, fhi=80)
     .agc(rect=0.5)
)
processed.plot_grey(output_path="processed.png")
processed.write("processed.rsf")
```

Transform methods return a new `RSFData` object by default. The original object
is not modified unless `inplace=True` is passed explicitly.

## Object Model

```python
from pymadagascar import RSFData, read, write

d = read("input.rsf")        # -> RSFData
array = d.numpy()            # defensive NumPy copy
view = d.numpy(copy=False)   # explicit mutable view of internal data
header = d.header            # defensive RSFHeader copy
axes = d.axes                # tuple[Axis, ...] in RSF 1-based order
d.shape                      # NumPy storage shape
d.write("output.rsf")        # write RSF header + sidecar
```

Top-level `write(path, data, header=None)` mirrors `write_rsf` order and returns
`RSFData`:

```python
from pymadagascar import write

d = write("synthetic.rsf", array, header)
```

## Stable Chain Methods

These methods are backed by currently stable or stable-subset lower-level APIs:

| Method | Lower-level API | Notes |
| --- | --- | --- |
| `window(axis=None, f=None, n=None, j=None)` | `generic.window.window` | Uses 1-based RSF axis numbers; `f` is zero-based sample index. |
| `scale(value)` | `generic.array_math.scale_rsf` | Scalar multiply. |
| `clip(clip)` | `generic.array_math.clip_rsf` | Real symmetric clipping. |
| `normalize(mode="max")` | `generic.array_math.normalize_rsf` | `mode="max"` or `mode="rms"`. |
| `fft(axis=1, norm=None)` | `signal.fft.fft_rsf` | NumPy FFT subset; see `SIGNAL_COMPATIBILITY.md`. |
| `ifft(axis=1, norm=None)` | `signal.fft.ifft_rsf` | Inverts centered full FFT layout. |
| `rfft(axis=1, norm=None)` | `signal.fft.rfft_rsf` | Real-to-complex non-negative frequency spectrum. |
| `irfft(axis=1, n=None, norm=None)` | `signal.fft.irfft_rsf` | Inverts RFFT layout. |
| `bandpass(flo, fhi, axis=1, taper=0)` | `signal.filter.bandpass_rsf` | FFT-domain zero-phase taper subset. |
| `lowpass(fcut, axis=1, taper=0)` | `signal.filter.lowpass_rsf` | FFT-domain zero-phase taper subset. |
| `highpass(fcut, axis=1, taper=0)` | `signal.filter.highpass_rsf` | FFT-domain zero-phase taper subset. |
| `agc(rect, axis=1, eps=1e-12)` | `seismic.agc.agc_rsf` | Stable local RMS AGC subset. |
| `mute(t0, v, axis=1, offset_axis=2, taper=0)` | `seismic.mute.mute_rsf` | Stable linear top-mute subset. |
| `stack(axis=2, mode="mean", nonzero=True)` | `seismic.stack.stack_rsf` | Stable stack subset; may reduce dimensionality. |
| `attr()` | `generic.attr.attr_rsf` | Returns basic in-memory statistics. |
| `write(path, data_format=None)` | `io.rsf.write_rsf` | Writes header + sidecar and returns the written `RSFData`. |

## Quicklook Plot Methods

`plot_grey()` and `plot_graph()` are Matplotlib quicklook helpers. They are
useful in local scripts, but plotting remains a partial replacement for
Madagascar VPlot rather than a byte-level-compatible plotting system.

```python
d.plot_grey(output_path="panel.png", pclip=99)
trace.plot_graph(output_path="trace.pdf")
```

If `output_path` is omitted, the Matplotlib figure object is returned. The
project uses a non-interactive backend for tests and scripts.

## In-place Rule

Default behavior is non-mutating:

```python
a = read("input.rsf")
b = a.scale(2.0)
assert a is not b
```

Use `inplace=True` only when mutation is intentional:

```python
a.scale(2.0, inplace=True)
```

`numpy()` and `header` return defensive copies by default. Use
`numpy(copy=False)` only when you intentionally want direct array mutation.

## Explicit Non-goals

The first `RSFData` pass does not wrap prototype APIs such as NMO, Semblance,
FK/Radon, Kirchhoff migration, acoustic modeling, SEG-Y, or broad VPlot
compatibility. Those modules remain available through their explicit lower-level
APIs and should not be treated as stable high-level chain methods until a future
task promotes them with tests and docs.

The high-level wrapper may use temporary file-backed RSF roundtrips internally
for lower-level APIs that are intentionally file-to-file. This preserves stable
APIs instead of rewriting their implementations.

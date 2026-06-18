# API Stability

本文说明当前 API 稳定性边界。后续重构时，应优先保持 stable API 不破坏。

## 已稳定 API

以下接口可以作为后续模块的基础依赖：

### RSF I/O

- `pymadagascar.io.rsf.RSFHeader`
- `pymadagascar.io.rsf.RSFArray`
- `pymadagascar.io.rsf.read_header(path)`
- `pymadagascar.io.rsf.write_header(path, header)`
- `pymadagascar.io.rsf.read_rsf(path)`
- `pymadagascar.io.rsf.write_rsf(path, data, header=None, *, data_format=None)`
- `read_rsf/write_rsf` 的 `ascii_float` sidecar 子集：`data_format=ascii_float`, `esize=0`, 1D/2D/3D float 数据；不包含其他 ASCII/XDR/form 组合。

### High-level Python API

- `pymadagascar.RSFData`
- `pymadagascar.read(path) -> RSFData`
- `pymadagascar.write(path, data, header=None, *, data_format=None) -> RSFData`
- `RSFData.write(path, *, data_format=None)`
- `RSFData.copy()`
- `RSFData.numpy(copy=True)`
- `RSFData.header`, `RSFData.shape`, `RSFData.dtype`, `RSFData.ndim`, `RSFData.axes`, `RSFData.path`
- `RSFData.window(...)`, `scale(...)`, `clip(...)`, `normalize(...)`
- `RSFData.fft(...)`, `ifft(...)`, `rfft(...)`, `irfft(...)`
- `RSFData.bandpass(...)`, `lowpass(...)`, `highpass(...)`
- `RSFData.agc(...)`, `mute(...)`, `stack(...)`
- `RSFData.attr()`
- `RSFData.plot_grey(...)`, `plot_graph(...)` as plotting quicklook wrappers

These methods are a convenience wrapper over stable lower-level APIs. Transform
methods are non-mutating by default and accept `inplace=True` for explicit
mutation. Plot quicklook methods are available but inherit the plotting module's
partial/VPlot-substitute status; see `docs/PYTHONIC_USAGE.md`.

### Core metadata and params

- `pymadagascar.core.axis.Axis`
- `pymadagascar.core.hypercube.Hypercube`
- `pymadagascar.core.params.RSFParams`
- `RSFParams.get_int/get_float/get_bool/get_string/get_list`
- `RSFParams` 的 `par=file` 稳定子集：空白/换行分隔的 `key=value`、空行、`#` 注释、单/双引号字符串、list/repeat 语法、重复 key 后者覆盖前者，以及按 argv 从左到右处理的覆盖顺序。
- `pymadagascar.cli.base.open_input`
- `pymadagascar.cli.base.open_output`
- `pymadagascar.cli.base.run_rsf_command`

### Generic modules

- `spike(shape, locations=None, magnitudes=None, axes=None, dtype="float32")`
- `math_rsf(expression, header=None, data=None, shape=None, axes=None)`
- `safe_eval_math(expression, variables)`
- `window(data, header, axis=None, n=None, f=None, j=None)`
- `window_rsf(rsf_array, params)`
- `info_rsf(path)`, `get_header_value(path, key, default=<missing>, cast=None)`, `get_header_values(path, keys, default=<missing>, cast=None)`, `format_header_values(values, parform=True)`, `disfil_array(data, header=None, max_values=None, precision=6, axis_format="flat")`, `disfil_rsf(path, max_values=None, precision=6, axis_format="flat")`, `attr_rsf(path)`, `put_header(path, updates, output_path=None)`
- `cat_arrays(arrays, headers, axis)`, `cat_rsf(inputs, output, axis)`
- `transpose_array(data, header, order)`, `transpose_rsf(...)`, `reshape_rsf(...)`
- `mask_rsf(input_path, output_path, min_value=None, max_value=None)`, `cut_rsf(input_path, output_path, axis=1, f=0, n=None, j=1)`, `reverse_rsf(input_path, output_path, axis=1, update_header=True)`
- `copy_rsf`, `convert_dtype_rsf`, `convert_endian_rsf`
- `copy_rsf_dataset(input_path, output_path, overwrite=False)`：`sfcp`-style file-level RSF header+sidecar copy subset; preserves sidecar bytes and updates output `in=`.
- `remove_rsf_dataset(path, dry_run=True, confirm=False, missing_ok=False)`：`sfrm`-style safe delete subset; dry-run by default and actual deletion requires explicit confirmation.
- `min_rsf(path, axis=None, nan_policy="propagate")`, `max_rsf(...)`, `minmax_rsf(...)`：script-friendly RSF min/max statistic subset. These report Python values/key=value CLI text and are not full `sfstack` alias clones.
- `multiply_rsf(input_path, other, output_path, scalar=None)`：`sfmul`/`sfadd mode=mul` stable subset for RSF x RSF or RSF x scalar.
- `divide_rsf(input_path, other, output_path, scalar=None, zero_policy="raise")`：`sfdiv`/`sfadd mode=div` stable subset for RSF / RSF or RSF / scalar. Zero denominators are explicit; default policy raises.
- `tpow_rsf(input_path, output_path, power=1.0, axis=1, abs_time=False)`：`sftpow`-style stable subset using 1-based RSF axes and local Axis coordinate convention.
- `interleave_rsf(input_paths, output_path, axis=1)`：`sfinterleave` stable subset for two or more same-shape RSF files.
- `header_window_rsf(input_path, mask_path, output_path, axis=2, keep_nonzero=True)`：`sfheaderwindow` stable Python mask subset. It does not implement the full Madagascar header table system.
- `header_cut_rsf(input_path, mask_path, output_path, axis=2, cut_nonzero=True)`：`sfheadercut` stable Python mask subset. It preserves shape/header and does not implement SEG-Y trace headers.
- `real_rsf(input_path, output_path)`, `imag_rsf(input_path, output_path)`, `cmplx_rsf(real_path, imag_path, output_path)`, `rtoc_rsf(input_path, output_path)`
- `noise(shape=None, header=None, seed=None, mean=0.0, std=1.0, distribution="normal")`, `add_noise(data, std=1.0, seed=None, distribution="normal")`, `noise_rsf(input_path=None, output_path=None, ...)`
- `add_rsf`, `scale_rsf`, `clip_rsf`, `normalize_rsf`
- `byte_scale(data, clip=None, pclip=None, bias=None, allpos=False)`, `byte_rsf(input_path, output_path, ...)`：Python byte scaling 替代子集，输出 `int32`/`native_int` 的 0..255 等级。
- `pad_rsf`, `spray_rsf`, `tile_rsf`

### Signal modules

- `fft_rsf`, `ifft_rsf`, `rfft_rsf`, `irfft_rsf`
- `fft_axis_header_update`
- `bandpass_rsf`, `lowpass_rsf`, `highpass_rsf`, `make_filter_taper`
- `triangle_smooth(data, rect, axes=None, repeat=1)`, `box_smooth(data, rect, axes=None, repeat=1)`, `smooth_rsf(input_path, output_path, rect, axes=None, repeat=1, kind="triangle")`
- `convolve_rsf`, `correlate_rsf`, `xcorr_traces`, `xcorr_rsf`, `fft_convolve`
- `ricker_wavelet(frequency, dt, nt, t0=None, peak_time=None, amplitude=1.0)`, `ricker_rsf(output_path, frequency, dt, nt, ...)`

### Testing helpers

- `compare_arrays`, `compare_headers`, `compare_rsf`, `assert_rsf_allclose`
- `make_1d_rsf`, `make_2d_rsf`, `make_3d_rsf`, `make_spike`, `make_ramp`, `make_sine`, `make_random`
- `original_madagascar_available`, `run_original_madagascar`, `run_pymadagascar`, `compare_command_outputs`

### Hybrid wrappers

Stable wrapper behavior:

- `pymadagascar.hybrid.cpp_available()`
- `pymadagascar.hybrid.backend_name()`
- `pymadagascar.hybrid.last_backend()`
- `pymadagascar.hybrid.add_arrays_cpp(a, b)`
- `pymadagascar.hybrid.scale_array_cpp(a, scale)`
- `pymadagascar.hybrid.batch_xcorr_cpp(data, axis=-1, mode="full")`
- `pymadagascar.hybrid.last_xcorr_backend()`

这些函数名中带 `_cpp`，但 Python fallback 仍必须可用。

## 暂不稳定 API

以下 API 可被后续任务改进，但改动必须同步测试和 docs：

- `pymadagascar.io.segy.*`
- `pymadagascar.seismic.nmo.*`
- `pymadagascar.seismic.semblance.*`
- `pymadagascar.seismic.fk.*`
- `pymadagascar.seismic.radon.*`
- `pymadagascar.imaging.kirchhoff.*`
- `pymadagascar.modeling.acoustic2d.*`
- `pymadagascar.plot.*` 的绘图参数。

这些模块是 prototype 或 partial，接口可以演进，但不应随意破坏已有测试用例。

## 不建议外部使用的内部 API

以下以下划线开头或明显内部用途的函数不应作为外部 API：

- `pymadagascar.hybrid.array_ops._load_core`
- `pymadagascar.hybrid.array_ops._reset_core_for_tests`
- `pymadagascar.hybrid.xcorr._batch_xcorr_numpy`
- `pymadagascar.hybrid.xcorr._reset_xcorr_for_tests`
- `pymadagascar.signal.convolution._*`
- `pymadagascar.signal.fft._*`
- `pymadagascar.signal.filter._*`
- `pymadagascar.seismic._utils.*`
- CLI 模块中的 `*_command` 可供测试复用，但对外推荐 `main()` 或 Python API。

## 后续重构不能破坏的接口

后续迁移时不得破坏：

- `read_rsf/write_rsf` 基本 roundtrip。
- `RSFHeader.dimensions` 和 `RSFArray.data/header` 的语义。
- CLI `key=value` 参数风格。
- CLI `par=file` 参数文件展开和从左到右覆盖顺序。
- CLI 输入位置参数 + `out=` 风格。
- `Axis`/`Hypercube` 的 1-based RSF axis 访问。
- `testing.runner` 对原始 Madagascar 不存在时的 skip-friendly 行为。
- Hybrid fallback：没有 `_core` 时不能抛出硬错误。

## 命名规范

- 文件和模块使用小写 snake_case。
- Python API 使用动词短语：`read_rsf`, `write_rsf`, `nmo_correct`, `semblance_scan`。
- CLI 模块名使用 Madagascar 命令去掉 `sf` 后的短名：`spike`, `window`, `cat`。
- Hybrid wrapper 可保留 `_cpp` 后缀，表示“优先 C++、自动 fallback”，不是“必须 C++”。
- 内部函数以下划线开头。
- 错误类型使用 `<Module>Error`：`ConvolutionError`, `NMOError`, `SegyError`。

## 兼容性承诺

当前承诺的是行为级兼容和测试可验证，不承诺：

- 与 Madagascar 输出文本字节级一致。
- 与 VPlot 输出像素级一致。
- 与原始 C API 内存模型一致。
- 大文件性能等价。
- 所有历史参数、别名和边界行为完全一致。

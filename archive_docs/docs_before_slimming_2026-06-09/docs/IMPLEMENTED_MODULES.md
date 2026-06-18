# Implemented Modules

> Current-use note, 2026-06-09: this file remains a module-level audit, but the
> release gate and aggregate counts now live in
> `docs/MASTER_HANDOFF_BEFORE_BATCH_MIGRATION.md`, `docs/RELEASE_CHECKLIST.md`,
> `docs/CLI_INVENTORY.md`, and `docs/TEST_STATUS.md`.

本文按 M0-M26 审计当前已完成模块。完成度含义：

- `complete`：API/CLI/pytest/示例或文档齐备，适合作为后续依赖。
- `partial`：核心可用，但 Madagascar 兼容参数或格式覆盖不完整。
- `prototype`：小规模验证原型，不代表完整工业级实现。
- `broken`：当前不可用。审计时没有发现 broken 模块。

## Module Matrix

| 模块 | 名称 | 源码文件 | 测试文件 | CLI | examples/docs | 完成度 | 主要已知问题 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M0 | 项目目录、AGENTS、迁移计划 | `AGENTS.md`, `MIGRATION_PLAN.md`, `pyproject.toml`, `pytest.ini` | 全项目 pytest | 无 | `docs/*.md` | complete | 早期计划文档描述与当前单包结构有差异，以本目录 docs 为准。 |
| M1 | RSF I/O | `pymadagascar/io/rsf.py` | `tests/test_rsf_io.py` | 被所有 CLI 复用 | `examples/read_write_rsf_demo.py` | complete | 主要支持 native binary；streaming/stdout 兼容有限。 |
| M2 | CLI 参数与管道层 | `pymadagascar/core/params.py`, `pymadagascar/cli/base.py` | `tests/test_cli_params.py`, `tests/test_cli_smoke.py` | `pymadagascar/cli/*.py`, stable `pymada-*` scripts | `docs/MADAGASCAR_COMPATIBILITY.md`, `docs/CLI_INVENTORY.md`, `docs/LOCAL_INSTALL_AND_USAGE.md` | complete | 只为稳定命令注册 console scripts；`par=file` 常用子集已稳定，历史扩展语义仍有限。 |
| M3 | Axis 与 Hypercube | `pymadagascar/core/axis.py`, `pymadagascar/core/hypercube.py` | `tests/test_hypercube.py` | 被 window/cat/transp/FFT 等复用 | `docs/API_STABILITY.md` | complete | 规则采样模型；不处理不规则几何。 |
| M4 | 测试、对照和回归体系 | `pymadagascar/testing/*.py` | `tests/test_testing_compare.py`, `tests/test_testing_runner.py` | runner 可被测试调用 | `docs/TEST_STATUS.md` | complete | 本机未安装 Madagascar，所有原始对照 skip。 |
| M5 | `sfspike` 重写 | `pymadagascar/generic/spike.py` | `tests/test_spike.py` | `python -m pymadagascar.cli.spike` | `examples/spike_demo.py` | complete | 只覆盖常用 spike 子集，不完整复刻全部 sfspike 参数。 |
| M6 | `sfmath` 重写 | `pymadagascar/generic/math.py` | `tests/test_math.py` | `python -m pymadagascar.cli.math` | `examples/math_demo.py` | complete | 安全表达式白名单；不支持任意 Madagascar math 表达式扩展。 |
| P1-04 | `sfnoise` 合成噪声 | `pymadagascar/generic/noise.py` | `tests/test_noise.py` | `noise` CLI | `examples/noise_demo.py` | complete | normal/uniform seeded 子集；NumPy RNG 不与原始 Madagascar 随机序列字节级一致。 |
| P1-05 | `sfricker`-related Ricker wavelet | `pymadagascar/signal/wavelet.py` | `tests/test_wavelet.py` | `ricker` CLI | `examples/ricker_demo.py` | complete | direct time-domain wavelet generator；原始 `sfricker` 频谱估计和 `sfricker1/2` 卷积族未复刻。 |
| M7 | `sfwindow` 重写 | `pymadagascar/generic/window.py` | `tests/test_window.py` | `python -m pymadagascar.cli.window` | `examples/window_demo.py` | complete | `min/max/squeeze` 等复杂兼容只做部分覆盖。 |
| M8 | `sfin/sfget/sfdisfil/sfattr/sfput` | `pymadagascar/generic/info.py`, `attr.py`, `put.py` | `tests/test_info_attr_put.py`, `tests/test_get.py`, `tests/test_disfil.py` | `info`, `get`, `disfil`, `attr`, `put` CLI | `examples/get_demo.py`, `examples/disfil_demo.py` | complete | 输出文本不保证与 Madagascar 字节级一致；`sfget` 的 `all=y`/stdin header-table 模式和 `sfdisfil` 原始 printf 分栏未实现。 |
| M9 | `sfcat` 重写 | `pymadagascar/generic/cat.py` | `tests/test_cat.py` | `python -m pymadagascar.cli.cat` | `examples/cat_demo.py` | complete | 不支持超大文件 streaming 拼接。 |
| M10 | `sftransp/reshape` | `pymadagascar/generic/transp.py` | `tests/test_transp.py` | `transp`, `reshape` CLI | `examples/transp_demo.py` | complete | 只做内存内转置/reshape。 |
| M11 | `sfdd` 重写 | `pymadagascar/generic/dd.py` | `tests/test_dd.py` | `python -m pymadagascar.cli.dd` | 无单独 example | partial | XDR/ascii/更多 dtype/form 未完整覆盖。 |
| P1-03 | `sfreal/sfimag/sfcmplx/sfrtoc` 复数工具 | `pymadagascar/generic/complex_tools.py` | `tests/test_complex_tools.py` | `real`, `imag`, `cmplx`, `rtoc` CLI | `examples/complex_tools_demo.py` | complete | file-backed `complex64/native_complex` 稳定；`sfrtoc pair=y` 和 `complex128` 落盘暂未实现。 |
| M12 | 基础数组数学 | `pymadagascar/generic/array_math.py` | `tests/test_array_math.py` | `add`, `scale`, `clip`, `normalize` CLI | 无单独 example | complete | 仅实现常用加法、缩放、裁剪、归一化。 |
| M13 | padding/spray/tile | `pymadagascar/generic/pad.py`, `spray.py` | `tests/test_pad_spray.py` | `pad`, `spray`, `tile` CLI | 无单独 example | complete | 复杂 padding 模式和边界策略未完整复刻。 |
| M14 | Matplotlib 可视化替代 | `pymadagascar/plot/*.py` | `tests/test_plot.py` | `grey`, `graph`, `wiggle` CLI | `examples/plot_demo.py` | partial | 不复刻 VPlot，不保证像素级一致。 |
| M15 | FFT | `pymadagascar/signal/fft.py` | `tests/test_fft.py` | `fft`, `ifft`, `rfft` CLI | 无单独 example | complete | 基于 NumPy FFT；归一化和频率轴与 Madagascar 可能有细节差异。 |
| M16 | 频率域滤波 | `pymadagascar/signal/filter.py` | `tests/test_filter.py` | `bandpass`, `lowpass`, `highpass` CLI | 无单独 example | complete | 滤波器定义是 NumPy 原型，不保证与 `sfbandpass` 完全一致。 |
| M17 | 卷积、相关、互相关 | `pymadagascar/signal/convolution.py` | `tests/test_convolution.py` | `conv`, `corr`, `xcorr` CLI | 无单独 example | complete | 复杂 Madagascar 变体未统一；长序列性能待 hybrid。 |
| M18 | SEG-Y/RSF 转换 | `pymadagascar/io/segy.py` | `tests/test_segy.py` | `segyread`, `segywrite` CLI | 无单独 example | partial | 仅小型 2D synthetic 覆盖；可选第三方库/复杂 SEG-Y 需后续加强。 |
| M19 | 地震道集基础处理 | `pymadagascar/seismic/gain.py`, `agc.py`, `mute.py`, `stack.py` | `tests/test_seismic_processing.py` | `gain`, `agc`, `mute`, `stack` CLI | 无单独 example | complete | 数学定义为清晰原型，未保证所有 Madagascar 参数。 |
| M20 | NMO 与 Semblance | `pymadagascar/seismic/nmo.py`, `semblance.py` | `tests/test_nmo_semblance.py` | `nmo`, `semblance` CLI | 无单独 example | prototype | Python 循环热点明显；速度函数和 offset 机制仍需扩展。 |
| M21 | FK 谱和 FK 滤波 | `pymadagascar/seismic/fk.py` | `tests/test_fk.py` | `fk`, `fkfilter` CLI | 无单独 example | prototype | mask 定义简单；未覆盖复杂 fan/dip filter 行为。 |
| M22 | Radon/tau-p | `pymadagascar/seismic/radon.py` | `tests/test_radon.py` | `radon`, `iradon` CLI | 无单独 example | prototype | 当前是小规模 adjoint/prototype，不是稀疏或最小二乘反演。 |
| M23 | 成像算法原型 | `pymadagascar/imaging/kirchhoff.py`, `DESIGN.md` | `tests/test_kirchhoff.py` | `kirchhoff` CLI | `examples/kirchhoff_demo.py` | prototype | 简化 2D post-stack Kirchhoff；无反走样、半导数、工业权重。 |
| M24 | 2D acoustic FD 正演原型 | `pymadagascar/modeling/acoustic2d.py` | `tests/test_acoustic2d.py` | `acoustic2d` CLI | 无单独 example | prototype | 教学实现；简单吸收边界；无弹性波/各向异性/GPU。 |
| M25 | Hybrid 工程骨架 | `pyproject.toml`, `CMakeLists.txt`, `cpp/bindings.cpp`, `pymadagascar/hybrid/array_ops.py` | `tests/test_hybrid_import.py` | 无独立 CLI | `docs/build_hybrid.md` | partial | 默认不编译 C++；当前机器无 C++ 编译器。 |
| M26 | C++ kernel 和 benchmark | `cpp/kernels/xcorr.cpp`, `pymadagascar/hybrid/xcorr.py`, `benchmarks/bench_xcorr.py` | `tests/test_hybrid_xcorr.py` | 无独立 CLI | `benchmarks/bench_xcorr_report.md` | partial | C++ 未在当前机器编译，真实加速比暂不可测。 |
| Stage B-1 | system/main small utilities | `pymadagascar/generic/file_ops.py`, `pymadagascar/generic/stats.py` | `tests/test_cp_rm_min_max.py` | `cp`, `rm`, `min`, `max` module-only CLI | `examples/cp_rm_min_max_demo.py` | stable subset | `sfcp/sfrm` safe file utilities; `sfmin/sfmax` text statistics, not full `sfstack` alias clones. |

## Current CLI Modules

当前所有模块仍可通过 `python -m pymadagascar.cli.<name>` 调用。已注册的稳定 console scripts 包括：

`pymada-info`, `pymada-get`, `pymada-disfil`, `pymada-real`, `pymada-imag`, `pymada-cmplx`, `pymada-rtoc`, `pymada-noise`, `pymada-ricker`, `pymada-spike`, `pymada-math`, `pymada-window`, `pymada-attr`, `pymada-put`, `pymada-dd`, `pymada-cat`, `pymada-transp`, `pymada-fft`, `pymada-bandpass`, `pymada-byte`, `pymada-smooth`, `pymada-boxsmooth`, `pymada-mask`, `pymada-cut`, `pymada-reverse`。

当前 CLI 模块包括：

`acoustic2d`, `add`, `agc`, `attr`, `bandpass`, `boxsmooth`, `byte`, `cat`, `clip`, `cmplx`, `conv`, `corr`, `cp`, `cut`, `dd`, `disfil`, `fft`, `fk`, `fkfilter`, `gain`, `get`, `graph`, `grey`, `highpass`, `ifft`, `imag`, `info`, `iradon`, `kirchhoff`, `lowpass`, `mask`, `math`, `max`, `min`, `mute`, `nmo`, `noise`, `normalize`, `pad`, `put`, `radon`, `real`, `reshape`, `reverse`, `rfft`, `ricker`, `rm`, `rtoc`, `scale`, `segyread`, `segywrite`, `semblance`, `smooth`, `spike`, `spray`, `stack`, `tile`, `transp`, `wiggle`, `window`, `xcorr`。

## Examples Present

当前 examples：

- `cat_demo.py`
- `byte_demo.py`
- `complex_tools_demo.py`
- `cp_rm_min_max_demo.py`
- `disfil_demo.py`
- `get_demo.py`
- `kirchhoff_demo.py`
- `local_quickstart.py`
- `mask_cut_reverse_demo.py`
- `math_demo.py`
- `noise_demo.py`
- `plot_demo.py`
- `pythonic_usage_demo.py`
- `read_write_rsf_demo.py`
- `ricker_demo.py`
- `smooth_demo.py`
- `spike_demo.py`
- `transp_demo.py`
- `window_demo.py`

本地 workflow examples：

- `my_workflows/basic_rsf_io_workflow.py`
- `my_workflows/spike_math_window_workflow.py`
- `my_workflows/fft_bandpass_workflow.py`
- `my_workflows/plot_grey_graph_workflow.py`
- `my_workflows/seismic_basic_agc_mute_stack_workflow.py`

缺少独立 example 的模块仍可通过 pytest 查看调用方式。

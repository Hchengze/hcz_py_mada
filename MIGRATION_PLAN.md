# MIGRATION_PLAN.md

本文是 `hcz_mada` 的分阶段迁移计划。目标是在不修改原始 Madagascar 源码的前提下，开发两个 Python 友好的版本：

- A. `pymadagascar-pure`：Python + NumPy/SciPy 实现，优先正确性、可读性和独立安装。
- B. `pymadagascar-hybrid`：Python 负责 RSF I/O、参数解析、流程组织、API 和 CLI，C/C++ 负责高性能核心。

原始 Madagascar 源码只作为只读参考，位置为 `../src-master`。

## 迁移优先级

总体优先级如下：

1. RSF header/binary 数据读写。
2. 命令行参数解析，包括 `key=value`、`par=file`、bool、数组参数、stdin/stdout。
3. 基础数组操作命令，例如 `window`、`math`、`spike`、`cat`、`put`、`transp`。
4. 基础数据检查接口和最小绘图接口，例如 `sfin`、`sfattr`、Matplotlib quicklook。
5. FFT、滤波、卷积、互相关等信号处理模块。
6. 地震处理和成像模块。
7. 性能敏感模块进入 `pymadagascar-hybrid`，通过 pybind11/Cython/cffi 暴露给 Python。

建议先让 `pymadagascar-pure` 建立完整行为基线，再把热点算法迁入 `pymadagascar-hybrid`。hybrid 版本不应复制 Madagascar 的全局 `sf_file` 状态模型，Python 层应负责 RSF 文件和参数，C/C++ 层只接收明确的数组、shape、dtype 和数值参数。

## 优先模块表

| 原始 Madagascar 程序名 | 原始源码路径 | 功能说明 | 输入输出格式 | 迁移难度 | 是否适合纯 Python | 是否建议保留 C/C++ | 推荐 Python API 名称 | 推荐 CLI 名称 | 测试方法 |
|---|---|---|---|---|---|---|---|---|---|
| RSF I/O API | `api/c/file.c`, `api/c/files.c`, `api/python/m8r.py` | 读写 RSF 文本头、定位 binary 数据、处理 `data_format`、`esize`、`n1..n9`、stdin/stdout | 输入/输出 `.rsf` header + native/ascii/xdr binary；第一阶段支持 native float/int/complex/short/double 和 ascii float | 高 | 是，必须先做 pure | 否，除非后期为大文件 streaming 优化 | `pymadagascar.io.read_rsf`, `write_rsf`, `RsfHeader`, `RsfFile` | 无单独 CLI；被所有 `sf*` 命令复用 | header parser 单测、dtype/shape roundtrip、stdin/stdout fixture、与 `sfdd`/`sfin` 对照 |
| 参数解析 API | `api/c/getpar.c`, `api/c/simtab.c`, `api/python/m8r.py` | Madagascar 风格命令行参数解析，支持 `key=value`、`par=file`、bool、数组、默认值 | argv、参数文件、环境参数；输出 typed 参数对象 | 中 | 是 | 否 | `pymadagascar.cli.parse_args`, `Par` | 无单独 CLI；被所有命令复用 | 参数表单测、重复 key、数组扩展、bool y/n/1/0、par 文件对照 |
| `sfspike` | `system/main/spike.c` | 生成 spikes、boxes、planes、constants；可从输入继承 axis header | 可无输入生成 RSF；输出 float RSF | 中 | 是 | 否 | `pymadagascar.commands.spike`, `pymadagascar.signal.spike` | `sfspike` | 小尺寸 golden RSF；`n#`、`k#`、`l#`、`mag`、axis header 对照 |
| `sfwindow` | `system/main/window.c` | 按 `f#`、`j#`、`n#` 或 `min#`/`max#` 切片，更新 axis header | 输入任意 esize RSF；输出 window 后 RSF | 中 | 是 | 后期可为大文件 out-of-core 优化 | `pymadagascar.commands.window`, `pymadagascar.io.window` | `sfwindow` | 1D/2D/3D 切片、负 `f#`、`squeeze`、header 更新、原命令对照 |
| `sfput` | `system/main/put.c` | 将命令行参数写入 output header，并复制数据 | 输入 RSF；输出 RSF header 修改 + binary 原样复制 | 低 | 是 | 否 | `pymadagascar.commands.put`, `RsfHeader.update` | `sfput` | header 精确比较、binary hash 不变、stdin/stdout 对照 |
| `sfcat` / `sfmerge` / `sfrcat` | `system/main/cat.c` | 沿指定 axis 拼接多个 RSF 数据集，支持输入文件列表和 stdin | 多个 RSF 输入；输出拼接 RSF | 中 | 是 | 后期可为超大文件 streaming 优化 | `pymadagascar.commands.cat`, `pymadagascar.io.concat` | `sfcat`, `sfmerge`, `sfrcat` | axis 拼接、header 兼容错误、order、space、多个文件对照 |
| `sftransp` | `system/main/transp.c` | 交换两个轴，支持内存受限 out-of-core 模式 | 输入任意 esize RSF；输出转置 RSF | 中 | 是 | 大数组 out-of-core 可保留 C++ 优化 | `pymadagascar.commands.transp`, `pymadagascar.io.transpose` | `sftransp` | 2D/3D/4D 转置、`plane=12/23`、axis header 更新、binary 顺序对照 |
| `sfmath` | `system/main/math.c` | 对一个或多个 RSF 输入执行表达式计算，支持 float/complex 函数 | 输入 float/complex RSF 或无输入生成；输出 float/complex RSF | 高 | 是，但表达式解析要谨慎 | 否，除非表达式执行成为热点 | `pymadagascar.commands.math`, `pymadagascar.math.evaluate` | `sfmath` | 安全表达式解析单测、多输入变量、complex 函数、header 兼容、原命令对照 |
| `sfin` | `system/main/in.c` | 显示 RSF 文件信息、维度、format、数据文件路径 | 输入 RSF；输出文本报告 | 低 | 是 | 否 | `pymadagascar.commands.info`, `pymadagascar.io.inspect` | `sfin` | 文本关键字段匹配、缺失 header 错误、stdin/file 对照 |
| `sfattr` | `system/main/attr.c` | 统计 rms、mean、norm、variance、std、max、min、nonzero、samples | 输入 float/complex/int 等 RSF；输出文本或指定字段 | 低到中 | 是 | 否 | `pymadagascar.commands.attr`, `pymadagascar.testing.stats` | `sfattr` | NumPy 统计对照、complex 行为、`want=`、NaN/Inf、原命令关键字段对照 |
| `sfdd` | `system/main/dd.c` | 数据格式和 dtype 转换，例如 ascii/native/xdr、float/int/complex/short/double | 输入 RSF；输出转换后 RSF | 中到高 | 是，先做 native/ascii 子集 | XDR/大文件可后期优化 | `pymadagascar.commands.dd`, `pymadagascar.io.convert` | `sfdd` | dtype roundtrip、ascii/native 转换、`esize`/`data_format`、截断/四舍五入、原命令对照 |
| `sfscale` | `system/main/scale.c` | 对数据乘缩放系数或归一化 | 输入 RSF；输出同 shape RSF | 低 | 是 | 否 | `pymadagascar.commands.scale`, `pymadagascar.array.scale` | `sfscale` | 小数组精确/近似比较、header 保持、CLI 对照 |
| `sfadd` / `sfmul` / `sfdiv` | `system/main/add.c` | 多输入数组加法、乘法、除法和 scale 组合 | 多个 RSF 输入；输出 RSF | 中 | 是 | 否 | `pymadagascar.commands.add`, `multiply`, `divide` | `sfadd`, `sfmul`, `sfdiv` | 多输入 shape 检查、scale 参数、float/complex、原命令对照 |
| `sfgrey` / `sfbyte` / `sfbar` | `plot/main/grey.c` | raster plot、byte 映射和 scalebar；原实现输出 VPlot 或 uchar RSF | 输入 float/uchar RSF；输出 VPlot 或 uchar RSF | 高 | 部分适合：先做 byte/quicklook | 完整 VPlot 暂不保留 | `pymadagascar.plot.grey`, `quicklook` | `sfgrey` 可后期兼容；M1 不承诺完整 | 第一阶段只测 byte/PNG quicklook；暂不对照 VPlot 字节级输出 |
| `sfgraph` | `plot/main/graph.c` | 曲线图，原实现输出 VPlot | 输入 RSF；输出 VPlot | 高 | 部分适合 Matplotlib 替代 | 否，完整 VPlot 暂缓 | `pymadagascar.plot.graph` | 暂不提供完整 `sfgraph` | Matplotlib smoke test、图片尺寸和非空像素检查；不做 VPlot 对照 |
| `sfwiggle` | `plot/main/wiggle.c` | 地震 wiggle trace 绘图，原实现输出 VPlot | 输入 float RSF；输出 VPlot | 高 | 适合 Matplotlib 近似实现 | 否，完整 VPlot 暂缓 | `pymadagascar.plot.wiggle` | 暂不提供完整 `sfwiggle` | 小型 CMP 图像 smoke test；不做 VPlot 对照 |
| `sfclip` | `system/generic/Mclip.c` | 按阈值裁剪 float 数据，处理 NaN/Inf 符号 | 输入 float RSF；输出 float RSF | 低 | 是 | 否 | `pymadagascar.signal.clip` | `sfclip` | 全分支小数组、NaN/Inf、`value=` 默认值、原命令对照 |
| `sfsmooth` | `system/generic/Msmooth.c`, `api/c/triangle*.c` | 多维 triangle/box smoothing，可 adjoint/diff/repeat | 输入 float RSF；输出 float RSF | 中 | 是，NumPy/SciPy 可实现 | 大数组和多维循环可后期 C++ | `pymadagascar.signal.smooth` | `sfsmooth` | 1D/2D smoothing、`rect#`、`repeat`、`box#`、adjoint 关系、原命令对照 |
| `sfbandpass` | `system/generic/Mbandpass.c`, `api/c/butter.c` | Butterworth bandpass，支持 zero phase/minimum phase | 输入 float RSF；输出 float RSF | 中 | 是，SciPy signal 适合 | 否，除非需要 bit-level legacy 对齐 | `pymadagascar.signal.bandpass` | `sfbandpass` | impulse response、Nyquist 错误、`flo/fhi/nplo/nphi/phase`、原命令容差对照 |
| `sffft1` | `system/generic/Mfft1.c`, `api/c/kiss_fft*` | 沿第 1 轴 real-to-complex 或 inverse FFT，更新频率 axis | 输入 float 或 complex RSF；输出 complex 或 float RSF | 中 | 是，NumPy/SciPy FFT 适合 | hybrid 可保留 FFTW/KISS 后端 | `pymadagascar.signal.fft1`, `ifft1` | `sffft1` | 正反变换 roundtrip、axis `n1/o1/d1`、`opt/sym/inv`、原命令容差对照 |
| `sfspectra` | `system/generic/Mspectra.c` | 计算频谱，可对所有 trace 求平均 | 输入 float RSF；输出 float spectrum RSF | 中 | 是 | FFT 后端可后期优化 | `pymadagascar.signal.spectra` | `sfspectra` | 单频正弦峰值、`all=y/n`、axis header、原命令对照 |
| `sfconvolve` / `sfxcor` 候选 | `su/lib/convolution.c`, `su/lib/xcor.c`, `api/c/helicon.c`, `user/gee/Mconv.c`, `user/chenyk/Mxcorr.c` | 卷积、互相关、helical convolution；核心库和 user 命令分散 | 输入数组或 RSF；输出数组或 RSF | 中到高 | 是，NumPy/SciPy 适合 | 对长序列/多维局部卷积建议 C++ | `pymadagascar.signal.convolve`, `correlate` | 第一阶段不承诺统一 CLI；后续可定 `sfconv`, `sfxcor` | 先测纯数组 API，再选一个原始命令做 golden 对照；避免早期覆盖所有 user 变体 |
| `sfricker` | `system/seismic/Mricker.c` | Ricker wavelet estimation，输出估计结果和 `ma` 辅助输出 | 输入 float spectrum/data RSF；输出 float RSF + `ma` | 中 | 是 | 否 | `pymadagascar.seismic.ricker` | `sfricker` | 合成 Ricker 谱、`niter/m`、辅助输出 header、原命令对照 |
| `sfnmo` | `system/seismic/Mnmo.c`, `system/seismic/fint1.c` | normal moveout，支持 velocity、offset、mask、stretch mute、slowness/squared | 输入 CMP float RSF + velocity/offset/mask；输出 corrected RSF | 高 | 是，作为 reference | 是，核心插值和循环建议 hybrid | `pymadagascar.seismic.nmo` | `sfnmo` | 小型 CMP 合成、constant velocity、mask、half/full offset、adjacent sample 对照、原命令容差对照 |
| `sfveltran` | `system/seismic/Mveltran.c`, `system/seismic/veltran.c` | hyperbolic Radon/velocity transform，支持 adjoint | 输入 CMP 或 velocity panel RSF；输出 transform RSF | 高 | 是，先做 reference | 是，性能核心建议 C++ | `pymadagascar.seismic.veltran` | `sfveltran` | dot-product adjoint test、小型合成事件、header 参数、原命令对照 |
| `sfstolt` | `system/seismic/Mstolt.c`, `system/seismic/fint1.c` | post-stack Stolt modeling/migration，需要输入 lateral cosine transform | 输入 transformed float RSF；输出 modeled/migrated RSF | 很高 | 可做小规模 reference | 是，建议 hybrid 后期 | `pymadagascar.imaging.stolt` | `sfstolt` | 暂不进 M1/M2；M3 后期用小模型、roundtrip 和原命令对照 |
| `sfkirchnew` | `system/seismic/Mkirchnew.c`, `system/seismic/kirchnew.c` | 2D post-stack Kirchhoff time migration/modeling with antialiasing | 输入 data/model RSF + velocity；输出 migrated/modeled RSF | 很高 | 小规模 reference 可行 | 是，建议 C++ | `pymadagascar.imaging.kirchhoff_time` | `sfkirchnew` | 暂不进 M1；后期 dot-product test、小模型、原命令对照 |
| `sfsegyread` / `sfsuread` | `system/seismic/Msegyread.c`, `system/seismic/segy.c`, `su/lib/segy.h` | SEG-Y/SU 到 RSF 转换，拆分 data header 和 trace header | 输入 SEG-Y/SU；输出 RSF data + headers | 高 | 部分可用 segyio/obspy | C/C++ 可保留 legacy 解析 | `pymadagascar.seismic.segy.read` | `sfsegyread`, `sfsuread` | M1 不做；后期使用小型 SEG-Y fixture、header key 对照 |

## 第一阶段不要做的模块

第一阶段 M1 只做 RSF I/O、参数解析和基础命令。以下内容明确暂缓：

- 完整 VPlot 兼容系统：`plot`、`pens`、`rsfplot`、`vp_*` 输出字节级兼容暂不做。M1 只允许做 Matplotlib quicklook 或 `sfbyte` 类数据映射子集。
- 与 SCons 深度绑定的文档生成系统：`framework/rsf/doc.py`、`RSF_Docmerge`、`sfdoc` 生成数据库、`book` 自动论文构建暂不迁移。
- 原始 SCons 构建和安装系统：`SConstruct`、`configure`、`scons/*.tar.gz`、`admin` 发布脚本不迁移。
- 大型偏移和成像程序：`sfstolt`、`sfgazdag`、`sfkirchnew`、`sfzomig`、`sfsstep2`、`sfpmig` 等不进 M1。
- 大型 HPC/研究系统：`trip/iwave`、`trip/rvl`、MPI、CUDA、PETSc 相关目录不进 M1。
- `user/*` 全量贡献目录：只在某个明确算法被选中时逐个迁移，不批量搬运。
- SEG-Y/SU 深度兼容：`sfsegyread`、`sfsegywrite`、`su/lib` 放到 M3/M4 后评估。
- 暂时缺少小型、可公开、可重复测试数据的模块不做。
- 任何需要远程下载大数据的 `book/data` 示例不作为必跑测试。

## 推荐仓库结构

建议采用一个工作区、两个包、共享测试资产的结构：

```text
hcz_mada/
  AGENTS.md
  MIGRATION_PLAN.md
  pymadagascar-pure/
    pyproject.toml
    src/
      pymadagascar/
        __init__.py
        io/
          header.py
          binary.py
          formats.py
          streaming.py
        cli/
          parser.py
          registry.py
          stdinout.py
        commands/
          spike.py
          window.py
          cat.py
          put.py
          transp.py
          math.py
          attr.py
        signal/
          fft.py
          filters.py
          convolution.py
          spectra.py
          smoothing.py
        seismic/
          wavelets.py
          nmo.py
          veltran.py
          segy.py
        imaging/
          stolt.py
          kirchhoff.py
        plot/
          quicklook.py
          grey.py
          wiggle.py
        testing/
          fixtures.py
          compare.py
          golden.py
    tests/
      unit/
      cli/
      golden/
      comparison/
    examples/
    docs/
  pymadagascar-hybrid/
    pyproject.toml
    src/
      pymadagascar_hybrid/
        __init__.py
        signal/
        seismic/
        imaging/
        bindings/
    cpp/
      signal/
      seismic/
      imaging/
      bindings/
    tests/
      unit/
      benchmark/
      comparison/
    examples/
    docs/
  shared/
    fixtures/
      rsf/
      segy/
      npz/
    golden/
    notes/
```

包边界建议：

- `pymadagascar-pure` 不依赖原始 Madagascar，也不依赖 `pymadagascar-hybrid`。
- `pymadagascar-hybrid` 可以复用 pure 的测试 fixture 和 API 设计，但运行时不应要求安装原始 Madagascar。
- 两个包的用户层 API 尽量一致，hybrid 可作为性能后端。
- 对照测试可以选择性调用原始 `sf*` 命令，但必须可 skip，不能成为安装前提。

## 里程碑

### M1：RSF I/O + 基础命令

目标：

- 建立 `pymadagascar-pure` 包骨架。
- 实现 RSF header/binary I/O。
- 实现 Madagascar 风格参数解析。
- 实现基础命令：`sfspike`、`sfin`、`sfattr`、`sfput`、`sfwindow`、`sfcat`、`sftransp`、`sfscale`。
- `sfmath` 进入设计和最小安全表达式原型，可作为 M1 后段交付，不阻塞 M1 基础完成。

验收：

- native float/int/complex roundtrip 通过。
- 小型 golden RSF fixture 通过。
- CLI 支持 `< in.rsf > out.rsf` 和 `in=`/`out=`。
- 与原始 Madagascar 对照测试可运行或可 skip。

### M2：信号处理算法

目标：

- 实现 `sfclip`、`sfsmooth`、`sfbandpass`、`sffft1`、`sfspectra`。
- 建立卷积/互相关 pure API：`convolve`、`correlate`，先不承诺覆盖所有 user 命令变体。
- 完善 `sfmath` 表达式解析和多输入兼容。

验收：

- FFT 正反变换 roundtrip 通过。
- 滤波和频谱在合成信号上有可解释结果。
- 与原始 `sfclip`、`sfsmooth`、`sfbandpass`、`sffft1`、`sfspectra` 做 golden 对照。
- 所有信号处理 API 都能直接接收 NumPy array，也能通过 RSF CLI 使用。

### M3：地震处理算法

目标：

- 实现小规模、可验证的地震处理模块：`sfricker`、`sfnmo`、`sfveltran`。
- 建立 `seismic` 子包的数据约定：time axis、offset axis、velocity panel、mask、header 参数。
- 初步评估 SEG-Y/SU：只做读取 fixture 和设计，不承诺完整 `sfsegyread`。
- 选择一个小型成像模块做调研，不进入性能承诺。

验收：

- `sfnmo` 支持 constant velocity、velocity file、offset file、mask 和 stretch mute 的核心路径。
- `sfveltran` 通过 adjoint dot-product test。
- 所有 M3 算法都有原始源码位置、算法说明、Python API、CLI、单元测试、对照测试和文档示例。

### M4：高性能 C/C++ 扩展

目标：

- 建立 `pymadagascar-hybrid` 包骨架和 pybind11/Cython/cffi 绑定策略。
- 将 M2/M3 中最耗时的核心迁入 C/C++，优先候选：NMO 插值循环、velocity transform、large-array transpose、FFT backend、Kirchhoff kernel。
- 保持 Python API 与 pure 一致，允许用户选择 backend。

验收：

- 至少一个 signal 模块和一个 seismic 模块有 hybrid 后端。
- hybrid 输出与 pure/golden 在约定容差内一致。
- 性能 benchmark 记录输入规模、平台、命令和 baseline。
- C/C++ 层只做核心计算，不直接解析 RSF header 或命令行参数。

## 测试策略

每个迁移模块都必须包含：

- 原始源码位置记录。
- 算法原理说明。
- Python API 测试。
- CLI 测试。
- RSF header 和 binary roundtrip 测试。
- 与原始 Madagascar 行为对照的 golden 测试。
- 文档示例。

测试数据优先级：

1. 手工构造的小型 NumPy arrays。
2. 小型 RSF fixture。
3. 原始 Madagascar 生成的 golden output。
4. 可选真实地震数据小样本。
5. 大型 `book/data` 示例只作为后期手动验收，不作为默认 CI。

数值比较规则：

- shape、dtype、axis header 精确比较。
- float/complex 数据使用 `numpy.testing.assert_allclose`，每个算法显式写容差。
- 文本报告只比较稳定关键字段。
- 随机模块必须固定 seed。
- 若本机没有原始 Madagascar 环境，对照测试必须 skip，而不是失败。


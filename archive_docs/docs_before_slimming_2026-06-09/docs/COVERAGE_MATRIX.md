# Coverage Matrix

本文描述当前项目对 Madagascar 功能类别的覆盖情况。它不是完整功能承诺，而是下一阶段迁移排序依据。

## Coverage Denominators

本文中的覆盖率采用两个口径：

- 全量 Madagascar command-surface 口径：`56 / 2114 = 2.65%`，包含 `system/`、`plot/`、known alias 和大量 `user/*` 程序。这个数字用于说明距离完整 Madagascar 生态有多远，不代表当前产品目标。
- core `system/` + `plot/main` command-surface 口径：`51 / 301 = 16.94%`，更接近当前 Python 包的目标范围。

Stage B-1 note: `sfcp` and `sfrm` are direct `system/main` source-backed additions. `sfmin` and `sfmax` are counted as command-surface/alias coverage because upstream maps them to `sfstack`; they are documented as Python statistic subsets, not full `sfstack` alias clones.

Stage B-2 note: `sfinterleave` is a direct `system/main` source-backed
addition; `sfmul` and `sfdiv` are counted as `sfadd` alias coverage; `sftpow`
is implemented as a stable subset from `user/nobody/Mtpow.c` and therefore
increases full command-surface coverage but not the core `system/ + plot/main`
count.

Stage B-3-1 note: `sfheaderwindow` and `sfheadercut` are direct `system/main`
source-backed additions. The current implementation is a Python mask/header RSF
subset, not a full Madagascar header table clone.

本项目不以完整迁移 `user/*`、VPlot/pens、SCons/book、IWAVE/RVL、MPI/CUDA/PETSc 或 2000+ 命令为近期目标。

## Status Legend

- `stable`: 当前项目范围内可作为本地工作流依赖。
- `stable subset`: 常用路径可用并有测试，但不是完整 Madagascar 参数克隆。
- `partial`: 核心路径可用，格式、参数或兼容覆盖仍不完整。
- `prototype`: 适合小数据、教学、实验或后续设计验证，不应视为完整 Madagascar 替代。
- `simplified prototype`: 有意简化了原始算法或物理/成像机制的 prototype。

## 已覆盖的功能类别

| 类别 | 当前文件 | 状态 |
| --- | --- | --- |
| RSF header/binary/ascii_float I/O | `pymadagascar/io/rsf.py` | stable subset |
| Pythonic high-level RSFData API | `pymadagascar/api.py` | stable convenience layer |
| RSF 参数解析和 CLI 基础层 | `pymadagascar/core/params.py`, `pymadagascar/cli/base.py` | stable subset |
| Axis/Hypercube 元数据 | `pymadagascar/core/axis.py`, `hypercube.py` | stable |
| 基础生成与数组操作 | `pymadagascar/generic/*.py` | stable subset |
| 基础绘图替代 | `pymadagascar/plot/*.py` | partial |
| FFT/滤波/平滑/卷积/互相关 | `pymadagascar/signal/*.py` | stable subset |
| SEG-Y 2D 原型 | `pymadagascar/io/segy.py` | 2D prototype |
| 道集基础处理 | `pymadagascar/seismic/gain.py`, `agc.py`, `mute.py`, `stack.py` | stable subset |
| NMO/Semblance | `pymadagascar/seismic/nmo.py`, `semblance.py` | prototype |
| FK 分析/滤波 | `pymadagascar/seismic/fk.py` | prototype |
| Radon/tau-p | `pymadagascar/seismic/radon.py` | prototype |
| Kirchhoff migration 原型 | `pymadagascar/imaging/kirchhoff.py` | simplified prototype |
| Acoustic 2D modeling 原型 | `pymadagascar/modeling/acoustic2d.py` | simplified prototype |
| Hybrid C++ skeleton | `cpp/`, `pymadagascar/hybrid/` | partial |

## 已实现的 sfxxx 类命令

当前名称不是原始 `sfxxx` 二进制。所有命令都支持 Python module CLI；一批稳定命令还注册了 `pymada-*` console scripts，详见 `docs/CLI_INVENTORY.md`。

Note: 本地 `src-master` 审计没有确认连续值缩放类 `sfbyte` 主程序；只发现 `sfbyte2rsf`/`sfswapbyte` 等 byte 文件转换或字节序工具。因此当前 `byte` 是 Python quicklook 替代子集，不计作 VPlot 或 `SF_UCHAR` 字节级兼容。

| Madagascar 风格 | 当前 CLI | 当前状态 |
| --- | --- | --- |
| `sfspike` | `python -m pymadagascar.cli.spike` | 可用子集 |
| `sfmath` | `python -m pymadagascar.cli.math` | 可用安全表达式子集 |
| `sfnoise` | `python -m pymadagascar.cli.noise` | normal/uniform seeded noise stable subset |
| `sfricker` | `python -m pymadagascar.cli.ricker` | direct time-domain Ricker wavelet generator stable subset; original `sfricker` spectral estimation is not cloned |
| `sfsmooth` | `python -m pymadagascar.cli.smooth` | triangle smoothing Python stable subset |
| `sfboxsmooth` | `python -m pymadagascar.cli.boxsmooth` | centered box smoothing Python stable subset |
| `sfwindow` | `python -m pymadagascar.cli.window` | 可用子集 |
| `sfin` | `python -m pymadagascar.cli.info` | 文本不完全一致 |
| `sfget` | `python -m pymadagascar.cli.get` | header query stable subset |
| `sfdisfil` | `python -m pymadagascar.cli.disfil` | 小数据 deterministic text dump 子集 |
| `sfattr` | `python -m pymadagascar.cli.attr` | 常用统计可用 |
| `sfput` | `python -m pymadagascar.cli.put` | header 更新可用 |
| `sfcat` | `python -m pymadagascar.cli.cat` | 内存内拼接可用 |
| `sfcp` | `python -m pymadagascar.cli.cp` | safe header+sidecar file copy subset; no `sfmv` behavior |
| `sftransp` | `python -m pymadagascar.cli.transp` | 内存内转置可用 |
| `sfmask` | `python -m pymadagascar.cli.mask` | inclusive min/max 0/1 mask stable subset |
| `sfmax` | `python -m pymadagascar.cli.max` | script-friendly max statistic subset; upstream is `sfstack` alias |
| `sfmin` | `python -m pymadagascar.cli.min` | script-friendly min statistic subset; upstream is `sfstack` alias |
| `sfcut` | `python -m pymadagascar.cli.cut` | shape-preserving data zeroing stable subset |
| `sfreverse` | `python -m pymadagascar.cli.reverse` | axis reversal stable subset with `o#`/`d#` update |
| `sfheaderwindow` | `python -m pymadagascar.cli.headerwindow` | mask/header RSF window subset; continuous selections only |
| `sfheadercut` | `python -m pymadagascar.cli.headercut` | mask/header RSF cut subset; shape-preserving |
| `sfmul` | `python -m pymadagascar.cli.mul` | `sfadd` alias multiply stable subset; RSF x RSF or RSF x scalar |
| `sfdiv` | `python -m pymadagascar.cli.div` | `sfadd` alias divide stable subset with explicit `zero_policy` |
| `sftpow` | `python -m pymadagascar.cli.tpow` | time-power gain stable subset using 1-based RSF axis |
| `sfinterleave` | `python -m pymadagascar.cli.interleave` | same-shape RSF interleave stable subset |
| reshape 类命令 | `python -m pymadagascar.cli.reshape` | 样点数一致时可用 |
| `sfdd` | `python -m pymadagascar.cli.dd` | dtype/endian/ascii_float 子集 |
| `sfreal` | `python -m pymadagascar.cli.real` | complex real-part stable subset |
| `sfimag` | `python -m pymadagascar.cli.imag` | complex imaginary-part stable subset |
| `sfcmplx` | `python -m pymadagascar.cli.cmplx` | real+imag to complex stable subset |
| `sfrtoc` | `python -m pymadagascar.cli.rtoc` | real to complex stable subset, `pair=` deferred |
| `sfrm` | `python -m pymadagascar.cli.rm` | safe dry-run/confirm header+sidecar removal subset |
| `sfadd` | `python -m pymadagascar.cli.add` | 基础加法 |
| `sfscale` | `python -m pymadagascar.cli.scale` | 常数缩放 |
| `sfclip` | `python -m pymadagascar.cli.clip` | 基础裁剪 |
| byte scaling 类 | `python -m pymadagascar.cli.byte` | Python 替代子集；输出 `native_int` 0..255 |
| normalize 类 | `python -m pymadagascar.cli.normalize` | 项目自定义 |
| `sfpad` | `python -m pymadagascar.cli.pad` | 基础 padding |
| `sfspray` | `python -m pymadagascar.cli.spray` | 基础 spray |
| tile 类 | `python -m pymadagascar.cli.tile` | 项目自定义 |
| `sfgrey` | `python -m pymadagascar.cli.grey` | Matplotlib 替代 |
| `sfgraph` | `python -m pymadagascar.cli.graph` | Matplotlib 替代 |
| `sfwiggle` | `python -m pymadagascar.cli.wiggle` | Matplotlib 替代 |
| `sffft1` 类 | `python -m pymadagascar.cli.fft`, `ifft`, `rfft` | NumPy FFT stable subset; see `docs/SIGNAL_COMPATIBILITY.md` |
| `sfbandpass` 类 | `python -m pymadagascar.cli.bandpass`, `lowpass`, `highpass` | NumPy 频域滤波 stable subset; see `docs/SIGNAL_COMPATIBILITY.md` |
| conv/corr/xcorr 类 | `python -m pymadagascar.cli.conv`, `corr`, `xcorr` | NumPy 原型 |
| `sfsegyread` | `python -m pymadagascar.cli.segyread` | 2D prototype |
| `sfsegywrite` | `python -m pymadagascar.cli.segywrite` | 2D prototype |
| `sfpow`/gain 类 | `python -m pymadagascar.cli.gain` | 基础 gain |
| AGC 类 | `python -m pymadagascar.cli.agc` | 基础 AGC |
| mute 类 | `python -m pymadagascar.cli.mute` | 基础 mute |
| `sfstack` | `python -m pymadagascar.cli.stack` | 基础 stack |
| `sfnmo` | `python -m pymadagascar.cli.nmo` | prototype |
| `sfvscan` 类 | `python -m pymadagascar.cli.semblance` | prototype |
| FK 类 | `python -m pymadagascar.cli.fk`, `fkfilter` | prototype |
| `sfslant`/Radon 类 | `python -m pymadagascar.cli.radon`, `iradon` | prototype |
| `sfkirchnew` 类 | `python -m pymadagascar.cli.kirchhoff` | simplified prototype |
| acoustic2d 项目命令 | `python -m pymadagascar.cli.acoustic2d` | simplified prototype |

## 尚未覆盖的 Madagascar 功能类别

- 完整 VPlot/Vppen/pens 图形系统。
- SCons flow、book 文档生成和 reproducible paper 系统。
- 全量 `system/main`、`system/generic`、`system/seismic` 命令。
- `user/*` 贡献程序。
- `trip/iwave`、RVL、MPI、CUDA、PETSc 等大型研究系统。
- 完整 SU/SEG-Y legacy 兼容层。
- 完整 Madagascar C/C++/Fortran/Matlab/Octave/Julia/Java API。
- out-of-core 大文件 streaming 算法。
- 精确 bit-level 兼容的 `xdr_*`、ASCII form、复杂 endian/form 组合；当前只覆盖 `ascii_float` text sidecar 小子集。

## 建议优先迁移的 sfxxx 类命令

| 优先级 | 命令/类别 | 原因 | 推荐路线 |
| --- | --- | --- | --- |
| P0 | byte scaling Python 替代、`sfdisfil` 格式扩展 | 调试、quicklook 和兼容性基础；`byte` 替代、`sfget` 和小数据 `sfdisfil` 子集已覆盖 | pure Python |
| P0 | 已完成：`sfsmooth`/`sfboxsmooth` Python 子集 | 信号/地震处理常用基础模块；后续可在有 benchmark 后加 hybrid | pure Python 已完成，hybrid 后续 |
| P1 | 已完成：`sfmask`/`sfcut`/`sfreverse` generic array 子集 | 本地数据检查、切除和轴反转常用基础工具 | pure Python |
| P1 | `sfricker1/2` Ricker convolution family | direct `sfricker`-related wavelet generation is covered; convolution/filter variants remain open | pure Python first, hybrid only if needed |
| P1 | 已完成：`sfbandpass/sffft1` 测试与参数兼容说明增强 | 与现有模块直接相关；新增 `docs/SIGNAL_COMPATIBILITY.md`，参数扩展仍按需后续 | pure Python + 对照测试 |
| P1 | `sfnmo/sfvscan` 更完整兼容 | 地震处理核心 | pure baseline + C++ kernel |
| P2 | `sfveltran`/velocity transform | Radon/velocity 分析核心 | prototype 后 hybrid |
| P2 | Kirchhoff/Stolt 小规模扩展 | 成像路线 | 先 design，再 hybrid |
| P2 | acoustic2d C++ kernel | modeling 性能路线 | hybrid C++ |

## 暂时不建议迁移的复杂模块

- 完整 VPlot 字节级兼容。
- `book/` 大规模示例和远程数据下载。
- `trip/iwave`、`trip/rvl`、MPI/CUDA/PETSc。
- 大型 3D prestack migration、PSPI、Gazdag、industrial RTM。
- 全量 `user/*`。
- 原始 Madagascar 构建、安装、发布和 SCons 插件系统。

## Pure Python 可实现模块

适合继续 pure Python 的模块：

- header/metadata 工具：`sfin` 增强、`sfget` 后续 `all=y`/stdin 行为、`sfdisfil` 后续 printf/column 兼容扩展。
- 小数组和测试数据生成：`sfnoise` 已覆盖 normal/uniform seeded 子集；`sfricker` 相关 direct Ricker wavelet generator 已覆盖，原始 `sfricker` 频谱估计和 `sfricker1/2` 卷积族仍待实现。
- 基础数组变换：byte scaling, `sfmask`/`sfcut`/`sfreverse`, `sfsmooth`/`sfboxsmooth` 已有稳定 Python 子集，`sfstack` 仍可扩展；复数工具 `sfreal/sfimag/sfcmplx/sfrtoc` 已有稳定文件子集，后续只需补高级参数或 dtype 扩展。
- 文件/format 子集：`ascii_float` 已有最小 sidecar 支持；后续可评估更多 RSF form/dtype 组合和 SEG-Y small fixture。
- 可视化替代：Matplotlib quicklook。

## Hybrid C/C++ 推荐模块

推荐进入 C++ 的热点：

- `batch_xcorr_cpp` 扩展到 direct convolution/correlation。
- NMO interpolation inner loop。
- Semblance velocity scan inner loop。
- Radon forward/adjoint scatter/gather loop。
- Acoustic 2D finite-difference time stepping。
- Kirchhoff hyperbola summation。
- FK mask 大数组应用只在证明 NumPy 不够时进入 C++。

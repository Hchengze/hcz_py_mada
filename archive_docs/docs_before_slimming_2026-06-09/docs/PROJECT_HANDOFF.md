# Project Handoff

生成日期：2026-06-09。本文基于当前仓库真实文件和测试结果生成，用于在新的 Codex 对话中继续开发。

## 项目目标

本项目在 `hcz_mada/` 下维护一个 Python 友好的 Madagascar/RSF 重构原型。目标分为两条线：

- `pymadagascar-pure`：以 Python + NumPy/SciPy/Matplotlib 实现常用 RSF I/O、CLI、基础数组处理、信号处理和地震处理原型，不依赖原始 Madagascar 安装环境。
- `pymadagascar-hybrid`：Python 继续负责 RSF I/O、参数解析、API 和 CLI，高耗时内核逐步迁移到 C/C++，通过 pybind11 暴露给 Python；C++ 不可用时必须自动 fallback 到 NumPy/Python。

当前完成的是 M0 到 M26 的原型迁移，不等于完整复刻 Madagascar。

覆盖率口径必须区分：全量源码/alias command-surface 口径约为 `56 / 2114 = 2.65%`，core `system/` + `plot/main` command-surface 口径约为 `51 / 301 = 16.94%`。前者包含大量 `user/*` 研究程序，不是当前近期目标；当前目标是本地可用的 Python RSF/地球物理工具包。

## 当前代码结构

当前主要目录：

- `pymadagascar/io/`：RSF I/O 和 SEG-Y 转换原型。
- `pymadagascar/core/`：`Axis`、`Hypercube`、`RSFParams` 参数模型。
- `pymadagascar/cli/`：67 个用户向 Python CLI 模块，均可通过 `python -m pymadagascar.cli.<name>` 调用；25 个稳定命令注册为 `pymada-*` console scripts。Stage B-1 新增的 `cp/rm/min/max`、Stage B-2 新增的 `mul/div/tpow/interleave`、Stage B-3-1 新增的 `headerwindow/headercut` 都是 module-only CLI。
- `pymadagascar/generic/`：spike、math、noise、window、info、attr、put、cat/interleave、transp、dd、complex tools、array math（add/mul/div/scale/clip/normalize/tpow）、byte、mask/cut/reverse、header mask/window/cut、pad/spray/tile。
- `pymadagascar/signal/`：FFT、滤波、平滑、卷积/相关/互相关、Ricker wavelet。
- `pymadagascar/seismic/`：gain、AGC、mute、stack、NMO、semblance、FK、Radon。
- `pymadagascar/imaging/`：简化 2D Kirchhoff time migration 原型。
- `pymadagascar/modeling/`：简化 2D acoustic finite-difference 正演原型。
- `pymadagascar/plot/`：Matplotlib 替代层：grey、graph、wiggle。
- `pymadagascar/hybrid/`：可选 C++ 扩展包装和 NumPy fallback。
- `pymadagascar/testing/`：RSF 对比、fixture、原始 Madagascar 调用 runner。
- `cpp/`：pybind11 绑定和 C++ kernel。
- `tests/`：43 个 pytest 文件。
- `examples/`：21 个顶层示例脚本，另有 `examples/my_workflows/` 中的 5 个本地 workflow 脚本和 1 个 helper。
- `benchmarks/`：`batch_xcorr_cpp` benchmark 脚本和当前报告。

更多细节见 `docs/IMPLEMENTED_MODULES.md` 和 `docs/COVERAGE_MATRIX.md`。

## Pure Python 状态

Pure Python 层目前是主线，测试覆盖较完整。RSF I/O、基础 CLI、基础数组命令、FFT/滤波/平滑/卷积、SEG-Y 原型、基础地震处理、NMO/semblance/FK/Radon、Kirchhoff、acoustic2d 和 high-level `RSFData` convenience API 都已有可运行 API、CLI 或 pytest。

这些实现优先保证清晰、可测和小数据正确性。成像、正演、Radon、NMO/semblance 等属于 prototype，不是工业级性能实现。

## Hybrid C/C++ 状态

Hybrid 工程骨架已建立：

- `pyproject.toml`
- `CMakeLists.txt`
- `cpp/bindings.cpp`
- `cpp/kernels/array_ops.cpp`
- `cpp/kernels/xcorr.cpp`
- `pymadagascar/hybrid/array_ops.py`
- `pymadagascar/hybrid/xcorr.py`

已实现 C++ kernel：

- `add_arrays_cpp(a, b)`
- `scale_array_cpp(a, scale)`
- `batch_xcorr_cpp(data, axis=-1, mode="full")`

当前环境中 `pymadagascar.hybrid.cpp_available()` 为 `False`，因为 `mywork` 环境没有 C++ 编译器。Python fallback 可用并通过测试。显式启用 C++ 构建时失败原因是 `No CMAKE_CXX_COMPILER could be found`。

## 当前可运行的命令

当前在 `pyproject.toml` 中注册了一批稳定 `console_scripts`，安装后可直接调用：

```powershell
pymada-info input.rsf
pymada-get input.rsf key=n1,n2,d1
pymada-disfil input.rsf max=20 precision=6
pymada-cmplx real.rsf imag.rsf out=complex.rsf
pymada-real complex.rsf out=real.rsf
pymada-imag complex.rsf out=imag.rsf
pymada-rtoc real.rsf out=complex0.rsf
pymada-noise n1=100 out=noise.rsf seed=1 std=0.1
pymada-ricker out=wavelet.rsf f=25 dt=0.001 nt=256
pymada-spike n1=10 out=spike.rsf
pymada-math n1=100 output="sin(x1)" out=math.rsf
pymada-window input.rsf out=win.rsf n1=20 f1=5
pymada-fft input.rsf out=fft.rsf axis=1
pymada-bandpass input.rsf out=bp.rsf flo=5 fhi=40
pymada-byte input.rsf out=byte.rsf pclip=99
pymada-smooth input.rsf out=smooth.rsf rect1=3
pymada-mask input.rsf out=mask.rsf min=0 max=1
```

当前注册的 console scripts：

`pymada-info`, `pymada-get`, `pymada-disfil`, `pymada-real`, `pymada-imag`, `pymada-cmplx`, `pymada-rtoc`, `pymada-noise`, `pymada-ricker`, `pymada-spike`, `pymada-math`, `pymada-window`, `pymada-attr`, `pymada-put`, `pymada-dd`, `pymada-cat`, `pymada-transp`, `pymada-fft`, `pymada-bandpass`, `pymada-byte`, `pymada-smooth`, `pymada-boxsmooth`, `pymada-mask`, `pymada-cut`, `pymada-reverse`。

所有 CLI 仍保留模块方式调用，未注册为 console script 的 prototype 或扩展命令请继续使用 `python -m`：

```powershell
python -m pymadagascar.cli.nmo gather.rsf velocity.rsf out=nmo.rsf
python -m pymadagascar.cli.acoustic2d vel.rsf out=shot.rsf nt=100 dt=0.001 sx=10 sz=10
```

全部 CLI 文件见 `pymadagascar/cli/` 和 `docs/CLI_INVENTORY.md`。

## 当前不可运行或不稳定的命令

- 只有稳定命令注册为 `pymada-*` console scripts；prototype 命令和多数扩展命令仍推荐 `python -m pymadagascar.cli.<name>`。
- 依赖原始 Madagascar 的对照测试当前全部 skip，因为本机 PATH 中没有 `sfspike`、`sfmath`、`sfwindow` 等原始程序。
- Hybrid C++ 扩展当前未编译；C++ 专项测试 skip，benchmark 只记录 NumPy reference。
- SEG-Y 支持是小型 2D 原型，不覆盖复杂 3D、全部 trace header、非标准 sample format。
- Imaging/modeling 是教学和验证原型，不是完整 Madagascar 成像/正演系统。

## 关键设计原则

- 不修改 `../src-master` 原始 Madagascar 源码。
- 一个模块一个任务，不做跨模块大重构。
- 每个新模块必须包含 Python API、CLI、pytest、docs、examples。
- Python API 先作为行为基线；C/C++ 只替换稳定且热点明确的内层 kernel。
- C++ 扩展失败不能破坏 pure Python 可用性。
- RSF 轴约定保持 Madagascar 风格：`n1` 为最快变化轴；CLI 轴号使用 1-based 风格，内部 NumPy 轴转换必须明确。
- 原始 Madagascar 对照测试必须可 skip，但 Python 内部测试不能被跳过。

## 新对话应该先读的文件

新 Codex 对话开始前必须先读：

- `AGENTS.md`
- `docs/PROJECT_HANDOFF.md`
- `docs/NEXT_MIGRATION_BACKLOG.md`
- `docs/TEST_STATUS.md`
- `docs/API_STABILITY.md`
- `docs/MASTER_HANDOFF_BEFORE_BATCH_MIGRATION.md`

需要了解历史迁移计划时再读：

- `MIGRATION_PLAN.md`
- `docs/IMPLEMENTED_MODULES.md`
- `docs/COVERAGE_MATRIX.md`
- `docs/MADAGASCAR_COMPATIBILITY.md`

需要 hybrid 构建信息时读：

- `docs/build_hybrid.md`
- `benchmarks/bench_xcorr_report.md`

## 新对话绝对不能做什么

- 不得修改、格式化、删除或移动 `../src-master`。
- 不得新增算法功能，除非用户明确要求进入下一个模块。
- 不得把原始 Madagascar 安装环境作为 pure Python 的硬依赖。
- 不得绕过现有 pytest，也不得把失败测试静默改成 skip。
- 不得把 C++ 扩展设为运行必需项。
- 不得一次性迁移大型 imaging、IWAVE、RVL、VPlot、SCons 文档系统或 `user/*` 大量程序。

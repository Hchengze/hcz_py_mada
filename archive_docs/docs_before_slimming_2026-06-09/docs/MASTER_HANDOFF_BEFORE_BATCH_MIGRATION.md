# Master Handoff Before Batch Migration

生成日期：2026-06-09。本文是阶段 0 交接基线，只记录当前真实状态，不代表新增功能已经进入阶段 A-H。

## 1. 项目当前定位

当前项目是一个 Python 友好的 Madagascar/RSF 本地工具包原型，核心目标是让 RSF 数据读写、常用 `sfxxx` 风格命令、地球物理处理流程、pytest、examples 和 docs 形成可长期维护的 Python 工作流。

当前项目不是什么：

- 不是完整 Madagascar clone。
- 不是一次性迁移 2000+ `sf*` 命令的项目。
- 不是 VPlot/pens、SCons/book、`user/*`、IWAVE/RVL/MPI/CUDA/PETSc 的近期复刻项目。
- 不是依赖原始 Madagascar 安装环境才能运行的包装层。

近期目标：保持 pure Python 主线稳定，完善 RSF I/O、CLI、generic/signal/seismic 基础能力、测试、文档和本地 examples。

长期目标：在 pure Python 永远可用、测试体系健康、文档同步的基础上，按 batch 逐步迁移更多 Madagascar 功能；热点内核可以进入 optional C++，但必须先有 Python fallback、benchmark 和精度测试。

## 2. 当前真实完成度

覆盖率：

- 全量 Madagascar/alias 口径：`46 / 2114 = 2.18%`。
- core `system/` + `plot/main` 口径：`42 / 301 = 13.95%`。
- `system/main`：`22 / 39 = 56.41%`。
- `system/generic`：`9 / 88 = 10.23%`。
- `system/seismic`：`7 / 158 = 4.43%`。
- `plot/main`：`3 / 16 = 18.75%`。
- `user/*`：`4 / 1792 = 0.22%`，不作为近期目标。

测试结果：

- `D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q`：`431 passed, 38 skipped in 18.03s`。
- `D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q -rs`：`431 passed, 38 skipped in 14.33s`。
- `D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q -rs -m original_madagascar`：`37 skipped, 432 deselected in 0.66s`。
- plain `python` 当前 PowerShell PATH 中不可用。

当前数量：

- CLI module：57 个用户向模块，不含 `base.py` 和 `__init__.py`。
- console_scripts：25 个 `pymada-*`。
- pytest 文件：40 个，阶段 A 新增 `tests/test_release_tools.py`。
- examples：23 个，不含 `examples/my_workflows/_common.py` helper。
- docs：20 个，阶段 A 新增 `docs/RELEASE_CHECKLIST.md` 和 `docs/CHANGELOG.md`。
- hybrid C++ 文件：5 个。

当前 console_scripts：

`pymada-info`, `pymada-get`, `pymada-disfil`, `pymada-real`, `pymada-imag`, `pymada-cmplx`, `pymada-rtoc`, `pymada-noise`, `pymada-ricker`, `pymada-spike`, `pymada-math`, `pymada-window`, `pymada-attr`, `pymada-put`, `pymada-dd`, `pymada-cat`, `pymada-transp`, `pymada-fft`, `pymada-bandpass`, `pymada-byte`, `pymada-smooth`, `pymada-boxsmooth`, `pymada-mask`, `pymada-cut`, `pymada-reverse`。

Pythonic API 状态：

- `pymadagascar.RSFData`, `pymadagascar.read`, `pymadagascar.write` 已存在。
- `RSFData` 是 high-level convenience wrapper，不替代底层稳定 API。
- transform 默认非原地修改；只有显式 `inplace=True` 才 mutation。
- 已包装 stable/stable-subset 的 window、array math、FFT/filter、AGC/mute/stack、attr、quicklook plot。
- 没有包装 NMO/Semblance/FK/Radon/Kirchhoff/acoustic2d/SEG-Y 等 prototype。

Hybrid 状态：

- `pymadagascar.hybrid.cpp_available()` 当前返回 `False`。
- `pymadagascar._core` 当前不可 import。
- C++ kernels 源码包括 `add_arrays_cpp`, `scale_array_cpp`, `batch_xcorr_cpp`。
- Python/NumPy fallback 可用并通过测试。
- C++ 不是硬依赖；默认 `PYMADAGASCAR_BUILD_CPP=OFF`。

## 3. 当前已实现模块总览

- `io`：RSF header/native binary/ascii_float stable subset；SEG-Y 2D prototype。
- `core`：`Axis`, `Hypercube`, `RSFParams`，含 `key=value` 和 stable `par=file` 子集。
- `cli`：57 个 module CLI，所有可 `python -m pymadagascar.cli.<name>`；25 个 stable console_scripts。
- `generic`：spike、math、info/get/disfil/attr/put、cat/transp/reshape、dd、complex tools、array math、byte、mask/cut/reverse、pad/spray/tile、noise。
- `signal`：FFT/IFFT/RFFT/IRFFT、bandpass/lowpass/highpass、smooth/boxsmooth、conv/corr/xcorr、Ricker wavelet。
- `seismic`：gain、AGC、mute、stack stable subset；NMO、semblance、FK、Radon prototype。
- `imaging`：简化 2D Kirchhoff time migration prototype。
- `modeling`：简化 2D acoustic finite-difference prototype。
- `plot`：Matplotlib grey/graph/wiggle quicklook，partial VPlot substitute。
- `hybrid`：optional C++ wrapper 和 NumPy fallback。
- `testing`：array/header/RSF compare helpers、fixtures、optional original Madagascar runner。
- `examples`：18 个顶层脚本和 5 个 workflow examples。
- `docs`：状态、覆盖率、兼容性、CLI inventory、Pythonic usage、signal compatibility、limitations、install/use 和 handoff 文档。

## 4. 当前稳定 API 分层

Stable：

- `Axis`, `Hypercube`。
- `RSFParams` 常用 typed getters、`key=value`、stable `par=file` 子集。
- CLI base helper 和 testing helper。
- `info/get/attr/put` 的核心路径。

Stable subset：

- RSF I/O：native binary 和 `ascii_float` 小子集。
- stable `pymada-*` console_scripts。
- generic 基础命令：spike、math、window、cat、transp/reshape、dd、complex tools、noise、array math、byte、mask/cut/reverse、pad/spray/tile。
- signal 基础命令：FFT/filter/smooth/convolution/Ricker。
- seismic gather 基础处理：gain、AGC、mute、stack。
- `RSFData` high-level convenience wrapper over stable/stable-subset lower-level APIs。

Partial：

- plotting quicklook。
- `sfdd` dtype/endian/ascii_float 子集。
- SEG-Y small 2D conversion。

Prototype：

- NMO、Semblance、FK、Radon。
- SEG-Y 2D。
- plotting substitute relative to VPlot。

Simplified prototype：

- Kirchhoff migration。
- Acoustic 2D modeling。

Internal：

- private helper functions。
- `pymadagascar.seismic._utils`。
- CLI command helper functions not documented as public API。

Optional：

- hybrid C++ wrappers。
- original Madagascar comparison tests。

## 5. 当前主要限制

- Full Madagascar coverage 很低：`2.18%` 是真实全量口径。
- `user/*` 不作为近期目标。
- VPlot/SCons/book 不作为近期目标。
- 大文件 streaming/out-of-core 仍有限；多数实现会把数组读入内存。
- optional original Madagascar comparison 未必在本机真正运行；当前本机所有 37 个 original comparison tests 都 skip。
- hybrid C++ 未编译；当前只验证 Python fallback。
- SEG-Y 仅是小型 2D prototype。
- imaging/modeling 仍是简化原型。
- CLI 文本、plot 像素、随机数序列、FFT/filter 归一化和历史参数不追求字节级一致。

## 6. 下一阶段迁移原则

- 不再零散迁移单命令。
- 采用 batch migration，每个 batch 先有 plan。
- 每个命令必须有 Python API、CLI、pytest、docs、example。
- 对应 Madagascar 命令必须有 optional comparison test；缺少上游 `sf*` 时合理 skip。
- 每个 batch 结束后必须更新 coverage、CLI inventory、API stability、known limitations、test status。
- 不允许破坏 pure Python。
- 不允许把 prototype 误标为 stable。
- C++ 必须先有 Python fallback、benchmark、精度测试和明确收益。
- 不允许把真实失败测试改成 skip。
- 不允许修改原始 Madagascar 源码。

## 7. 后续建议阶段

- 阶段 A：发布前稳定化。重点是 docs/test/packaging/API contract，不新增大功能。
- 阶段 B：`system/main` 剩余基础命令。优先 header、copy/move、linear-operator helper 等小范围工具。
- 阶段 C：`system/generic` 高频命令。优先 book 热点和本地工作流常用工具。
- 阶段 D：插值/重采样/规则化。先设计 stretch/remap/spline/bin 的 Python baseline。
- 阶段 E：地震道集处理增强。扩展 AGC/mute/stack/NMO offset/header/table 机制。
- 阶段 F：速度分析/Radon/FK。收敛 semblance、Radon adjoint/LS、FK/dipfilter 参数兼容。
- 阶段 G：成像与正演。先设计与 fixture，再考虑 Kirchhoff/acoustic2d C++ kernel。
- 阶段 H：长期覆盖率扩展机制。建立周期性 source scan、coverage matrix 更新和 migration gate。

## 8. 下一阶段开始前必须阅读

- `AGENTS.md`
- `pyproject.toml`
- `pytest.ini`
- `docs/MASTER_HANDOFF_BEFORE_BATCH_MIGRATION.md`
- `docs/PROJECT_HANDOFF.md`
- `docs/TEST_STATUS.md`
- `docs/API_STABILITY.md`
- `docs/COVERAGE_MATRIX.md`
- `docs/MADAGASCAR_FULL_COVERAGE_AUDIT.md`
- `docs/NEXT_100_TASKS.md`
- `docs/NEXT_MIGRATION_BACKLOG.md`
- `docs/CLI_INVENTORY.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/MADAGASCAR_COMPATIBILITY.md`
- `docs/PYTHONIC_USAGE.md`
- `docs/SIGNAL_COMPATIBILITY.md`
- `docs/ORIGINAL_MADAGASCAR_COMPARISON.md`
- `docs/WSL_MADAGASCAR_TESTING.md`
- `docs/LOCAL_INSTALL_AND_USAGE.md`
- `docs/build_hybrid.md` if touching hybrid.

## 9. 下一阶段绝对不要做

- 不要直接迁移大型 imaging。
- 不要直接迁移完整 VPlot。
- 不要直接迁移 SCons/book。
- 不要直接迁移全量 `user/*`。
- 不要直接做 C++。
- 不要改动原始 Madagascar 源码。
- 不要跳过测试。
- 不要把失败测试改成 skip。
- 不要把原始 Madagascar 或 C++ extension 变成 pure Python 的硬依赖。

## 10. 阶段 A 更新

阶段 A 新增发布前稳定化检查资产：

- `docs/RELEASE_CHECKLIST.md`
- `docs/CHANGELOG.md`
- `tools/check_release.py`
- `tools/check_cli_inventory.py`
- `tools/check_docs_commands.py`
- `tests/test_release_tools.py`

## 11. Stage B-1 Update

Stage B-1 implemented a small `system/main` utility batch only:

- Batch plan: `docs/batch_plans/STAGE_B_SYSTEM_MAIN_PLAN.md`.
- New module-only CLIs: `python -m pymadagascar.cli.cp`, `python -m pymadagascar.cli.rm`, `python -m pymadagascar.cli.min`, and `python -m pymadagascar.cli.max`.
- New APIs: `copy_rsf_dataset`, `remove_rsf_dataset`, `min_rsf`, `max_rsf`, and `minmax_rsf`.
- New tests: `tests/test_cp_rm_min_max.py`.
- New example: `examples/cp_rm_min_max_demo.py`.
- Current CLI module count: 61 user-facing modules; console_scripts remain 25.
- Current test file count: 41; top-level examples are now 19 plus 5 workflow scripts.
- Coverage command-surface count after this batch: `50 / 2114 = 2.37%`; core `system/` + `plot/main` command-surface count: `46 / 301 = 15.28%`.
- `sfcp` and `sfrm` map to `../src-master/system/main/cp.c` and `../src-master/system/main/rm.c`.
- `sfmin` and `sfmax` are upstream `sfstack` aliases; pymadagascar exposes script-friendly text statistics, not full `sfstack` alias RSF-output compatibility.

## 12. Stage B-2 Update

Stage B-2 implemented a small `system/main` / generic array batch only:

- Batch plan updated: `docs/batch_plans/STAGE_B_SYSTEM_MAIN_PLAN.md`.
- New module-only CLIs: `python -m pymadagascar.cli.mul`, `python -m pymadagascar.cli.div`, `python -m pymadagascar.cli.tpow`, and `python -m pymadagascar.cli.interleave`.
- New APIs: `multiply_rsf`, `divide_rsf`, `tpow_rsf`, and `interleave_rsf`.
- New tests: `tests/test_mul_div_tpow_interleave.py`; release tool test baseline updated to 65 CLI modules.
- New example: `examples/mul_div_tpow_interleave_demo.py`.
- Current CLI module count after B-2: 65 user-facing modules; console_scripts remain 25.
- Current test file count after B-2: 42; top-level examples are now 20 plus 5 workflow scripts.
- Coverage command-surface count after B-2: `54 / 2114 = 2.55%`; core `system/` + `plot/main` command-surface count: `49 / 301 = 16.28%`.
- `sfmul` and `sfdiv` map to `alias:sfadd`, implemented by `../src-master/system/main/add.c`.
- `sftpow` maps to `../src-master/user/nobody/Mtpow.c`; it is full command-surface coverage but not core `system/ + plot/main` coverage.
- `sfinterleave` maps to `../src-master/system/main/interleave.c`.
- B-3 header commands and B-4 dottest/conjgrad remain deferred.

## 13. WSL Original Comparison Update

Optional original Madagascar comparisons can be run from WSL when a Madagascar
installation is available there. The intended distribution name for this
workstation is `ubuntu2204`.

- Setup and runbook: `docs/WSL_MADAGASCAR_TESTING.md`.
- Windows-side probe tool: `tools/check_wsl_madagascar.py`.
- This is optional only; pure Python pytest must not depend on WSL or original
  Madagascar.
- Older WSL Madagascar versions should be recorded as version differences, not
  used to weaken pure Python tests.

## 14. Stage B-3-1 Update

Stage B-3-1 implemented the first minimal header/metadata batch only:

- Batch plan updated: `docs/batch_plans/STAGE_B_SYSTEM_MAIN_PLAN.md`.
- Design document added: `docs/design/HEADER_METADATA_COMMANDS_DESIGN.md`.
- New module-only CLIs: `python -m pymadagascar.cli.headerwindow` and
  `python -m pymadagascar.cli.headercut`.
- New APIs: `header_window_rsf` and `header_cut_rsf`.
- New tests: `tests/test_header_window_cut.py`; release tool test baseline
  updated to 67 CLI modules.
- New example: `examples/header_window_cut_demo.py`.
- Current CLI module count after B-3-1: 67 user-facing modules; console_scripts
  remain 25.
- Current test file count after B-3-1: 43; top-level examples are now 21 plus
  5 workflow scripts.
- Coverage command-surface count after B-3-1:
  `56 / 2114 = 2.65%`; core `system/` + `plot/main` command-surface count:
  `51 / 301 = 16.94%`.
- Direct `system/main` source-backed count after B-3-1:
  `27 / 39 = 69.23%`.
- `sfheaderwindow` maps to `../src-master/system/main/headerwindow.c`.
- `sfheadercut` maps to `../src-master/system/main/headercut.c`.
- Both pymadagascar implementations are ordinary-RSF mask/header subsets, not
  full Madagascar header table or SEG-Y trace-header compatibility.
- `sfheaderattr`, `sfheadermath`, `sfheadersort`, and `sfsegyheader` remain
  deferred.

这些工具只做 release baseline、CLI inventory 和 docs command-name 一致性检查，不运行新算法，不要求原始 Madagascar，不要求 C++ extension，不自动修改文档。

阶段 A 验证结果：

- `D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q`：`434 passed, 38 skipped in 14.32s`。
- `D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q -rs`：`434 passed, 38 skipped in 14.65s`。
- `tools/check_release.py`：passed。
- `tools/check_cli_inventory.py`：passed，57 CLI modules，25 console_scripts。
- `tools/check_docs_commands.py`：passed，262 documented `pymada-*` mentions all registered。
- plain `python` 仍不在当前 PowerShell PATH 中。

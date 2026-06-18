# Next Migration Backlog

本文是新对话继续开发时的任务池。开始任何新任务前，先读 `docs/PROJECT_HANDOFF.md`、`docs/TEST_STATUS.md` 和本文。

## 阶段 A：发布前稳定化状态

阶段 A 已完成发布前基线整理：

- 新增 `docs/RELEASE_CHECKLIST.md` 和 `docs/CHANGELOG.md`。
- 新增 `tools/check_release.py`、`tools/check_cli_inventory.py`、`tools/check_docs_commands.py`。
- 新增 `tests/test_release_tools.py`。
- 历史文档保留但已标注历史性质或同步当前 CLI/examples 状态。

阶段 A 之后的下一步是阶段 B：从 `system/main` 剩余基础命令和小范围维护任务开始。阶段 B 不做 C++，不做大型成像，不直接迁移 VPlot/SCons/book 或全量 `user/*`。

## Stage B-1 Completed: system/main small utilities

- Added `copy_rsf_dataset` and module-only `python -m pymadagascar.cli.cp` as a safe `sfcp` subset.
- Added `remove_rsf_dataset` and module-only `python -m pymadagascar.cli.rm` as a dry-run/confirm `sfrm` subset.
- Added `min_rsf`, `max_rsf`, `minmax_rsf` and module-only `python -m pymadagascar.cli.min/max` as script-friendly statistic subsets.
- Added `docs/batch_plans/STAGE_B_SYSTEM_MAIN_PLAN.md`, `tests/test_cp_rm_min_max.py`, and `examples/cp_rm_min_max_demo.py`.
- `sfmv` remains deferred. `sfmin/sfmax` are not full upstream `sfstack` alias RSF-output clones.

## Stage B-2 Completed: system/main / generic array operations

- Added `multiply_rsf` and module-only `python -m pymadagascar.cli.mul` as an
  `sfmul`/`sfadd mode=mul` subset.
- Added `divide_rsf` and module-only `python -m pymadagascar.cli.div` as an
  `sfdiv`/`sfadd mode=div` subset with explicit `zero_policy`.
- Added `tpow_rsf` and module-only `python -m pymadagascar.cli.tpow` as an
  `sftpow` time-power gain subset.
- Added `interleave_rsf` and module-only
  `python -m pymadagascar.cli.interleave` as an `sfinterleave` subset.
- No new `pymada-*` console scripts were registered.

## Stage B-3-1 Completed: header mask/window/cut subset

- Added `docs/design/HEADER_METADATA_COMMANDS_DESIGN.md` to separate ordinary
  RSF headers, mask RSFs, header tables, trace headers, and SEG-Y trace
  headers.
- Added `header_window_rsf` and module-only
  `python -m pymadagascar.cli.headerwindow` as an `sfheaderwindow` mask subset.
- Added `header_cut_rsf` and module-only
  `python -m pymadagascar.cli.headercut` as an `sfheadercut` mask subset.
- No new `pymada-*` console scripts were registered.

Next Stage B work should proceed to B-3-2 only after deciding whether the
project wants a first-class header table model. B-3-2 candidates are
`sfheaderattr`, `sfheadermath`, and `sfheadersort`. `sfsegyheader` should remain
a separate B-3-3 SEG-Y trace-header design task. Do not start C++, large
imaging/modeling, VPlot, SCons/book, broad `user/*` migration, or B-4
dottest/conjgrad work.

## P0：交接后第一批维护任务

| 任务 | 难度 | 涉及文件 | 推荐测试方法 | 需要原始 Madagascar 对照 | 需要 C++ 加速 |
| --- | --- | --- | --- | --- | --- |
| 已完成：注册稳定 `console_scripts` 并保留 `python -m` fallback | 低 | `pyproject.toml`, `pymadagascar/cli/*.py`, docs | CLI subprocess tests | 否 | 否 |
| 已完成：增加 docs 对每个 CLI 的最小调用示例 | 低 | `docs/`, `examples/` | doctest 或 smoke subprocess | 否 | 否 |
| 已完成：建立真实 Madagascar 可选对照环境说明 | 中 | `docs/TEST_STATUS.md`, `pymadagascar/testing/runner.py` | 在有 RSFROOT/PATH 的机器跑 `pytest -rs` | 是 | 否 |
| 已完成：修正并统一 `pymada-*` 与 `python -m` 命名文档 | 低 | `docs/*.md`, examples | 文档审查 + CLI smoke | 否 | 否 |
| 已完成：阶段 A release/check 工具 | 低 | `tools/check_release.py`, `tools/check_cli_inventory.py`, `tools/check_docs_commands.py`, `tests/test_release_tools.py`, docs | release tool subprocess tests + pytest | 否 | 否 |

## P1：基础兼容性增强

| 任务 | 难度 | 涉及文件 | 推荐测试方法 | 需要原始 Madagascar 对照 | 需要 C++ 加速 |
| --- | --- | --- | --- | --- | --- |
| 已完成：`sfget`/header query 工具 | 低 | `pymadagascar/generic/info.py`, `pymadagascar/cli/get.py` | header fixture + CLI | 是，已添加 optional test | 否 |
| 已完成：`sfdisfil` 小数据文本 dump | 低 | `pymadagascar/generic/info.py`, `pymadagascar/cli/disfil.py` | deterministic text tests | 是，已添加 optional test | 否 |
| 已完成：`sfreal/sfimag/sfcmplx/sfrtoc` 复数数据工具 | 低 | `pymadagascar/generic/complex_tools.py`, `pymadagascar/cli/{real,imag,cmplx,rtoc}.py` | complex fixture + CLI subprocess | 是，已添加 optional test | 否 |
| 已完成：`sfbyte`/byte scaling 子集 | 中 | `pymadagascar/generic/byte.py`, `pymadagascar/cli/byte.py` | range/clip/pclip/allpos/CLI tests | 原始源码未确认连续值 `sfbyte` 主程序；按 Python 替代记录 | 否 |
| 已完成：RSF `ascii_float` sidecar 子集 | 中 | `pymadagascar/io/rsf.py`, `generic/dd.py` | binary/ascii roundtrip + `sfdd form=ascii` tests | 是，已有 optional comparison | 否 |
| 已完成：`par=file` 更完整兼容 | 中 | `pymadagascar/core/params.py` | parser unit + CLI subprocess | 是，源码语义已审计 | 否 |
| 已完成：`sfmask`/`sfcut`/`sfreverse` generic array tools | low/medium | `pymadagascar/generic/{mask,cut,reverse}.py`, `pymadagascar/cli/{mask,cut,reverse}.py` | mask/cut/reverse unit tests + CLI subprocess | yes, optional tests added | no |
| 已完成：Stage B-1 `sfcp`/`sfrm`/`sfmin`/`sfmax` small utility batch | low/medium | `pymadagascar/generic/{file_ops,stats}.py`, `pymadagascar/cli/{cp,rm,min,max}.py` | API tests + CLI subprocess + optional original comparison skips | yes, optional tests added | no |
| 已完成：Stage B-2 `sfmul`/`sfdiv`/`sftpow`/`sfinterleave` array batch | low/medium | `pymadagascar/generic/{array_math,interleave}.py`, `pymadagascar/cli/{mul,div,tpow,interleave}.py` | API tests + CLI subprocess + optional original comparison skips | yes, optional tests added | no |
| 已完成：Stage B-3-1 `sfheaderwindow`/`sfheadercut` mask subset | low/medium | `pymadagascar/generic/header_mask.py`, `pymadagascar/cli/{headerwindow,headercut}.py`, `docs/design/HEADER_METADATA_COMMANDS_DESIGN.md` | API tests + CLI subprocess + optional original comparison skips | yes, optional tests added | no |

## P1：信号处理扩展

| 任务 | 难度 | 涉及文件 | 推荐测试方法 | 需要原始 Madagascar 对照 | 需要 C++ 加速 |
| --- | --- | --- | --- | --- | --- |
| 已完成：`sfsmooth` triangle / `sfboxsmooth` box smoothing | 中 | `pymadagascar/signal/smooth.py`, `pymadagascar/cli/{smooth,boxsmooth}.py` | impulse response + constant/header/CLI tests | 是，已有 `sfsmooth` optional comparison | 可后续，有 benchmark 后再做 |
| 已完成：`sfnoise` synthetic noise | 低 | `pymadagascar/generic/noise.py`, `pymadagascar/cli/noise.py`, `examples/noise_demo.py` | seeded deterministic tests | 是，已添加 optional test | 否 |
| 已完成：`sfricker`-related direct Ricker wavelet 工具 | 低 | `pymadagascar/signal/wavelet.py`, `pymadagascar/cli/ricker.py`, `examples/ricker_demo.py` | frequency/peak/header/CLI/acoustic2d reuse tests | 是，已添加 related `sfricker1` optional smoke | 否 |
| `sfricker1/2` Ricker convolution family | 中 | future `signal/wavelet.py` or `signal/filter.py` extension | impulse response + original comparison | 是 | 可选 |
| 更完整 `sfbandpass` 参数 | 中 | `pymadagascar/signal/filter.py` | impulse/sine/edge frequencies | 是 | 否 |
| Direct convolution C++ kernel | 中 | `cpp/kernels/`, `pymadagascar/hybrid/` | C++ vs NumPy + benchmark | 可选 | 是 |

## P1：地震处理核心

| 任务 | 难度 | 涉及文件 | 推荐测试方法 | 需要原始 Madagascar 对照 | 需要 C++ 加速 |
| --- | --- | --- | --- | --- | --- |
| NMO offset header/table 支持 | 中 | `pymadagascar/seismic/nmo.py`, CLI | synthetic CMP + header tests | 是 | 后续 |
| `nmo_interpolate_cpp` | 中 | `cpp/kernels/nmo.cpp`, `hybrid/nmo.py` | Python vs C++ tolerance + benchmark | 可选 | 是 |
| `semblance_scan_cpp` | 中高 | `cpp/kernels/semblance.cpp`, `hybrid/semblance.py` | synthetic velocity peak + benchmark | 可选 | 是 |
| AGC/mute/stack 参数兼容扩展 | 中 | `pymadagascar/seismic/*.py` | small gather tests | 是 | 否 |

## P2：数据格式和真实数据

| 任务 | 难度 | 涉及文件 | 推荐测试方法 | 需要原始 Madagascar 对照 | 需要 C++ 加速 |
| --- | --- | --- | --- | --- | --- |
| 建立小型公开 SEG-Y fixture | 中 | `tests/data/`, `tests/test_segy.py` | read/write/header CSV tests | 是，建议 | 否 |
| SEG-Y 3D inline/crossline 原型 | 高 | `pymadagascar/io/segy.py` | synthetic 3D SEG-Y | 是 | 否 |
| Trace header table 与 RSF sidecar 设计 | 中 | `io/segy.py`, docs | CSV/parquet roundtrip | 可选 | 否 |

## P2：Radon/FK/成像/正演

| 任务 | 难度 | 涉及文件 | 推荐测试方法 | 需要原始 Madagascar 对照 | 需要 C++ 加速 |
| --- | --- | --- | --- | --- | --- |
| Radon least-squares 接口 | 高 | `pymadagascar/seismic/radon.py` | adjoint + synthetic event | 是 | 后续 |
| Radon scatter/gather C++ kernel | 高 | `cpp/kernels/radon.cpp` | dot-product + benchmark | 可选 | 是 |
| FK filter 参数兼容扩展 | 中 | `pymadagascar/seismic/fk.py` | slope event + mask tests | 是 | 可选 |
| Kirchhoff C++ summation kernel | 高 | `cpp/kernels/kirchhoff.cpp` | diffraction peak + benchmark | 可选 | 是 |
| Acoustic 2D C++ time stepping | 高 | `cpp/kernels/acoustic2d.cpp` | travel time + stability + benchmark | 可选 | 是 |

## P3：暂缓或不建议

| 任务 | 原因 |
| --- | --- |
| 完整 VPlot/pens 字节级复刻 | 成本高、Python 替代层已能 quicklook |
| 完整 SCons/book reproducible paper 系统 | 与 Python 包目标不同 |
| 全量 `user/*` 程序迁移 | 范围巨大，缺少统一测试数据 |
| `trip/iwave`/RVL/MPI/CUDA/PETSc | 大型独立研究系统，应另立项目或专项 |
| 大型 3D prestack migration/RTM | 需要完整设计、数据和性能路线 |

## 每个新任务的最低完成标准

每个新模块必须包含：

- 原始 Madagascar 源码位置和行为摘要。
- Python API。
- CLI。
- pytest。
- 与原始 Madagascar 的可选对照测试，未安装时 skip。
- docs 更新。
- examples 或最小可运行示例。
- 如果是 hybrid：Python fallback、C++ vs Python 精度测试、benchmark 报告。

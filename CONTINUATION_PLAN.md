# Continuation Plan

生成日期：2026-06-06。本文只基于当前 `hcz_mada/` 仓库文件、文档和本次 pytest 结果生成，不依赖旧聊天记录。

## 已阅读和检查的依据

- `AGENTS.md`
- `docs/PROJECT_HANDOFF.md`
- `docs/IMPLEMENTED_MODULES.md`
- `docs/COVERAGE_MATRIX.md`
- `docs/TEST_STATUS.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/NEXT_MIGRATION_BACKLOG.md`
- `docs/API_STABILITY.md`
- `docs/MADAGASCAR_COMPATIBILITY.md`
- `pyproject.toml`
- `pytest.ini`
- `pymadagascar/`、`tests/`、`examples/`、`benchmarks/`、`cpp/` 的当前结构

## 当前完成度判断

当前项目已经完成 M0-M26 的“可运行原型迁移”。这意味着 pure Python 版本已经有较完整的基础骨架：RSF I/O、CLI 参数层、常用 generic 命令、FFT/滤波/卷积、SEG-Y 小型原型、基础地震处理、NMO/Semblance/FK/Radon、Kirchhoff 和 acoustic2d 都有 API、CLI 和 pytest 覆盖。

但这不等于完整 Madagascar 复刻。当前更准确的定位是：

- pure Python 主线可作为后续迁移基线。
- 多数基础模块已能被后续模块依赖。
- 成像、正演、Radon、FK、NMO/Semblance 是小规模验证原型，不是工业级实现。
- hybrid 工程骨架存在，但当前机器未编译 C++ 扩展，真实加速比未验证。
- 原始 Madagascar 对照测试机制存在，但本机缺少原始 `sf*` 命令，因此对照测试全部 skip。

当前结构检查结果：

- `pymadagascar/` 下有 `cli`、`core`、`generic`、`hybrid`、`imaging`、`io`、`modeling`、`plot`、`seismic`、`signal`、`testing`。
- `pymadagascar/cli/` 当前有 45 个 Python CLI 文件，包括 `__init__.py` 和 44 个命令模块。
- `tests/` 当前有 30 个 pytest 文件。
- `examples/` 当前有 9 个顶层示例脚本，另有 `examples/my_workflows/` 中的 5 个本地 workflow 脚本。
- `docs/` 当前有 14 个项目状态、入口和兼容性文档。
- `pyproject.toml` 已注册一批稳定 `pymada-*` console scripts；所有 CLI 模块仍保留 `python -m pymadagascar.cli.<name>` 调用。
- 在当前路径及上层 `HCZ_madagascar/` 路径运行 `git status --short` 均显示不是 git 仓库，当前环境无法用 git 状态判断未提交改动。

## M0-M26 完成度分层

这里的“真完成”指在当前项目承诺范围内 API/CLI/pytest/docs 或示例足够完整，可作为后续依赖；不表示与原始 Madagascar 字节级或全参数兼容。

| 模块 | 状态 | 判断 |
| --- | --- | --- |
| M0 项目目录、AGENTS、迁移计划 | 真完成 | 项目规则、文档和测试入口存在；早期计划与当前结构有差异时以 `docs/` 为准。 |
| M1 RSF I/O | 真完成 | 常用 native binary RSF header/data roundtrip 可用；streaming、XDR、ASCII 全组合不完整。 |
| M2 CLI 参数与管道层 | 真完成 | `key=value`、位置输入、`out=`、基础类型解析可用；稳定命令已注册 console scripts。 |
| M3 Axis/Hypercube | 真完成 | 规则采样轴模型稳定；不处理不规则几何。 |
| M4 测试、对照和回归体系 | 真完成 | 测试 helper 和 optional original Madagascar runner 可用；本机对照测试 skip。 |
| M5 `sfspike` 子集 | 真完成 | API/CLI/tests/example 可用；只覆盖常用子集。 |
| M6 `sfmath` 子集 | 真完成 | 安全表达式白名单可用；不支持完整 Madagascar math 语言。 |
| M7 `sfwindow` 子集 | 真完成 | 常用 window 操作可用；复杂 `min/max/squeeze` 兼容有限。 |
| M8 `sfin/sfattr/sfput` | 真完成 | 常用 header/info/attr/put 可用；文本输出不保证字节级一致。 |
| M9 `sfcat` 子集 | 真完成 | 内存内拼接可用；无 out-of-core streaming。 |
| M10 `sftransp/reshape` | 真完成 | 内存内转置和 reshape 可用。 |
| M11 `sfdd` 子集 | partial | dtype/endian 常用转换可用；XDR、ASCII、更多 form/dtype 未完整覆盖。 |
| M12 基础数组数学 | 真完成 | add/scale/clip/normalize 可用。 |
| M13 padding/spray/tile | 真完成 | 基础 padding/spray/tile 可用；复杂边界策略不完整。 |
| M14 Matplotlib 可视化替代 | partial | grey/graph/wiggle smoke tests 可用；不复刻 VPlot 或像素级行为。 |
| M15 FFT | 真完成 | NumPy FFT API/CLI/tests 可用；归一化和频率轴与 Madagascar 可能有差异。 |
| M16 频率域滤波 | 真完成 | lowpass/highpass/bandpass 原型可用；不保证完整 `sfbandpass` 兼容。 |
| M17 卷积/相关/互相关 | 真完成 | direct/fft 基础功能可用；复杂 Madagascar 变体和性能待加强。 |
| M18 SEG-Y/RSF 转换 | partial | 小型 2D synthetic 可用；真实 SEG-Y、3D、trace header 覆盖不足。 |
| M19 地震道集基础处理 | 真完成 | gain/AGC/mute/stack 基础行为可用；参数兼容仍有限。 |
| M20 NMO 与 Semblance | prototype | 小规模正确性原型；offset/速度函数机制和性能需要扩展。 |
| M21 FK 谱和 FK 滤波 | prototype | 小规模 fan/velocity mask 原型；复杂 dip/fan filter 未覆盖。 |
| M22 Radon/tau-p | prototype | forward/adjoint 小规模原型；不是完整 LS/sparse Radon。 |
| M23 Kirchhoff migration | prototype | 简化 2D post-stack time migration；缺 antialiasing、half-derivative、工业权重。 |
| M24 Acoustic 2D modeling | prototype | 教学级 FD 正演；简单边界，无弹性波/各向异性/GPU/并行。 |
| M25 Hybrid 工程骨架 | partial | pybind11/CMake/scikit-build-core 骨架存在；默认不编译 C++，当前无编译器。 |
| M26 C++ xcorr kernel 和 benchmark | partial | C++ 源码、wrapper、benchmark 存在；本机未编译，真实加速比不可测。 |

汇总：

- 真完成：M0-M10、M12-M13、M15-M17、M19。
- partial：M11、M14、M18、M25、M26。
- prototype：M20-M24。
- 当前未发现 broken 模块。

## 本次 pytest 结果

运行命令：

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q -rs
```

运行目录：

```text
hcz_mada/
```

当前结果：

```text
323 passed, 25 skipped in 7.94s
```

失败数量：0。

因此本次没有测试失败原因需要修复。25 个 skip 是环境性 skip，主要原因如下：

- 原始 Madagascar 命令未安装或不在 PATH：`sfscale`、`sfcat`、`sfconv`、`sfdd`、`sffft1`、`sfbandpass`、`sfdipfilter`、`sfin`、`sfattr`、`sfput`、`sfkirchnew`、`sfmath`、`sfnmo`、`sfvscan`、`sfpad`、`sfspray`、`sfslant`、`sfsegyread`、`sfpow`、`sfstack`、`sfspike`、`sftransp`、`sfwindow`。
- 原始 Madagascar command-line programs 未安装，runner 相关对照测试 skip。
- optional C++ extension 当前未编译，`test_hybrid_xcorr.py` 中 C++ backend 对照测试 skip。

## 当前最大风险

1. 兼容性风险：原始 Madagascar 对照测试机制存在，但当前环境没有 `sf*` 命令，真实兼容性尚未被持续验证。
2. 发布入口风险：稳定 `pymada-*` console scripts 已注册，但 prototype 和多数扩展命令仍只建议 `python -m`；后续新增 CLI 时必须同步文档和 smoke tests，避免入口命名再次混淆。
3. 误用风险：M20-M24 是 prototype，容易被误认为完整地震处理、成像或正演实现。
4. 数据格式风险：RSF I/O 对 native binary 覆盖较好，但 ASCII/XDR/form/endian/streaming/out-of-core 仍是兼容短板。
5. Hybrid 风险：C++ 源码和 wrapper 存在，但当前机器无 C++ 编译器，无法证明 `_core` 扩展、benchmark 和实际加速路径。
6. 质量工具风险：当前没有 ruff/mypy/black/isort 配置，风格和类型约束主要依赖人工审查与 pytest。
7. 工作区管理风险：当前路径不是 git 仓库，后续修改前应确认是否需要在其它位置纳入版本控制。

## 是否需要先修复测试或重构架构

不建议立刻做大规模架构重构。当前 pytest 全部通过，基础 API 稳定边界已经在 `docs/API_STABILITY.md` 中列出，后续应保持小步演进。

建议先做 P0 级维护和兼容性收敛，而不是直接新增大型算法：

- 先处理 CLI 入口命名：注册 `console_scripts`，或在文档中明确放弃 `pymada-*` 可执行名。
- 补齐每个 CLI 的最小调用示例和 smoke subprocess 测试。
- 建立真实 Madagascar 环境的可重复对照测试说明。
- 明确 partial/prototype 模块的边界，避免后续功能建立在未稳定行为上。

不需要“修复失败测试”，因为当前没有失败测试。但需要维护 skipped 测试的透明度，尤其是原始 Madagascar 和 C++ 编译环境相关 skip。

## 下一阶段优先级建议

建议下一步先做“阶段 1：项目入口和兼容性基线稳定化”。原因是它风险低、影响面大，能让后续所有模块更容易被测试、安装和使用。

优先顺序：

1. 决定并实现 CLI 入口策略：注册 `console_scripts`，或统一文档只支持 `python -m`。
2. 为核心 CLI 建立最小 subprocess smoke tests。
3. 更新 docs，消除 `pymada-*`、`sfxxx`、`python -m` 之间的命名歧义。
4. 完善真实 Madagascar 对照环境说明，不要求本机必须安装，但要能在有 `RSFROOT/PATH` 的机器复跑。

在这些完成前，不建议先做 NMO/Semblance C++、Radon、Kirchhoff 或 acoustic2d 的性能扩展。

## 后续阶段划分和验收标准

建议分成 5 个阶段推进。

### 阶段 1：入口、文档和测试基线稳定

目标：

- 统一 CLI 入口策略。
- 补齐核心命令的最小示例。
- 让新用户能安装、运行、测试，而不会混淆当前可执行名。

建议任务：

- 注册 `console_scripts` 或明确放弃 `pymada-*`。
- 为常用 CLI 增加 subprocess smoke tests。
- 更新 `PROJECT_HANDOFF.md`、`MADAGASCAR_COMPATIBILITY.md`、`TEST_STATUS.md`、examples。
- 明确当前不是完整 Madagascar 复刻。

验收标准：

- `python -m pytest -q -rs` 通过。
- 所有文档中的 CLI 命令在当前安装方式下可运行。
- `pyproject.toml`、docs、examples 对入口命名没有冲突。
- 原始 Madagascar 不存在时，optional comparison tests 仍合理 skip。

### 阶段 2：基础兼容工具和 RSF 格式增强

目标：

- 优先补齐调试、header 查询和小数据检查工具。
- 降低后续模块开发的文件格式风险。

建议任务：

- 实现 `sfget`/header query 子集。
- 实现 `sfdisfil` 小数据文本 dump。
- 实现 `sfbyte`/byte scaling 子集。
- 增强 `par=file` 解析。
- 逐步增强 RSF `ascii_*`、更多 dtype/form 支持。

验收标准：

- 每个新命令都有 Python API、CLI、pytest、docs、最小示例。
- 每个新命令都有 optional original Madagascar comparison test，未安装时 skip。
- RSF roundtrip 覆盖新增 dtype/form。
- 旧的 309 个通过测试不回退。

### 阶段 3：信号处理和合成数据基础扩展

目标：

- 增强常用信号处理模块，给地震处理和对照测试提供更可靠 fixture。

建议任务：

- 实现 `sfsmooth` triangle/box smoothing。
- 实现 `sfnoise` seeded synthetic noise。
- 实现 `sfricker` wavelet 工具。
- 扩展 `sfbandpass/sffft1` 参数兼容。

验收标准：

- impulse、sine、seeded random fixture 测试可重复。
- CLI 输出 header 和 shape 正确。
- 与原始 Madagascar 的差异被记录在 `KNOWN_LIMITATIONS.md` 或测试注释中。
- 性能热点先记录 benchmark，不急于 C++ 化。

### 阶段 4：地震处理核心和 Hybrid 加速

目标：

- 先稳定 pure Python 数学行为，再把明确热点迁移到 C++。

建议任务：

- 扩展 NMO offset header/table 支持。
- 扩展 Semblance velocity scan 的输入机制。
- 添加 `nmo_interpolate_cpp` 和 `semblance_scan_cpp`，保持 Python fallback。
- 扩展 direct convolution/correlation C++ kernel。

验收标准：

- pure Python baseline 与 C++ kernel 在小数据上数值一致。
- 没有 C++ 编译器时 pure Python pytest 仍通过。
- 有 C++ 编译器时 hybrid 专项测试通过，并更新 benchmark 报告。
- benchmark 记录误差、backend、耗时和内存。

### 阶段 5：真实数据、SEG-Y、Radon/FK/成像/正演收敛

目标：

- 把 prototype 模块从“演示可用”逐步推向“边界清晰、可对照、可扩展”。

建议任务：

- 建立小型公开 SEG-Y fixture。
- 扩展 SEG-Y 3D inline/crossline 原型和 trace header sidecar 设计。
- 设计 Radon least-squares 接口。
- 扩展 FK filter 参数兼容。
- 对 Kirchhoff 和 acoustic2d 先写 design，再决定 C++ kernel。

验收标准：

- 所有真实数据 fixture 可小体积、可复现、可合法纳入仓库或明确下载流程。
- prototype 模块新增行为都有 synthetic event 测试和可选 Madagascar 对照。
- 大型内层循环不在 Python 中无边界扩张；进入 C++ 前必须有 pure Python baseline 和 benchmark。
- docs 清楚区分 prototype、partial、stable API。

## 当前建议

下一步优先进入阶段 1。当前测试是绿色的，不需要先修失败测试；但建议先修正入口、文档和对照测试环境说明，再新增算法功能。这样后续做 `sfget/sfdisfil/sfbyte`、`sfsmooth/sfnoise/sfricker` 或 hybrid kernel 时，测试与使用路径会更稳。

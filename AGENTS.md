# AGENTS.md

本文件是 `hcz_mada` 项目的短协作规则。所有新 Codex 对话开始开发前必须先读本文。

## 必读文档

开始任何新任务前，先读：

1. `docs/PROJECT_HANDOFF.md`
2. `docs/NEXT_MIGRATION_BACKLOG.md`
3. `docs/TEST_STATUS.md`

需要更多上下文时继续读：

- `docs/IMPLEMENTED_MODULES.md`
- `docs/COVERAGE_MATRIX.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/API_STABILITY.md`
- `docs/MADAGASCAR_COMPATIBILITY.md`
- `docs/build_hybrid.md`
- `MIGRATION_PLAN.md`
- `DESIGN.md`

## 项目目标

本项目在 `hcz_mada/` 下维护 Madagascar/RSF 的 Python 友好重构原型：

- pure Python：Python + NumPy/SciPy/Matplotlib，优先正确性、可读性、可维护性。
- hybrid：Python API/CLI + 可选 C/C++ kernel，C++ 不可用时必须自动 fallback。

当前完成 M0-M26，但这不是完整 Madagascar 迁移。

## 绝对边界

- 不得修改、格式化、删除、移动 `../src-master`。
- 不得一次性重写整个项目。
- 不得在用户未要求时实现新算法。
- 不得把原始 Madagascar、`RSFROOT`、SCons 构建产物作为 pure Python 的硬依赖。
- 不得让 C++ 扩展失败导致 Python API 不可用。
- 不得静默删除、跳过或弱化已有测试。

## 新模块最低标准

任何新模块都必须包含：

- 原始 Madagascar 源码位置和行为摘要。
- Python API。
- CLI。
- pytest。
- docs 更新。
- examples 或最小可运行示例。
- 与原始 Madagascar 的可选对照测试；本机未安装原始命令时必须合理 skip。

Hybrid 模块还必须包含：

- Python fallback。
- C++ vs Python 精度测试。
- benchmark 脚本和报告。
- 无 C++ 编译器时不破坏 pure Python。

## 修改前后检查

修改前：

- 查看 `docs/PROJECT_HANDOFF.md` 和 `docs/NEXT_MIGRATION_BACKLOG.md`。
- 确认任务只涉及一个模块或一个紧密相关的小命令组。
- 先读当前真实代码，不凭记忆改。

修改后至少运行：

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q
```

如果新增或修改 hybrid C++，还要运行：

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest tests\test_hybrid_import.py tests\test_hybrid_xcorr.py -q
```

如果项目之后新增 ruff/mypy/black/isort 配置，必须同时运行对应检查，并更新 `docs/TEST_STATUS.md`。

## 兼容性原则

- CLI 保持 Madagascar `key=value` 风格。
- RSF 轴号在 CLI 中使用 1-based 风格，内部 NumPy 轴转换要明确。
- RSF I/O、header、dtype、axis 更新必须有测试。
- 与 Madagascar 行为不同的地方必须写入 `docs/KNOWN_LIMITATIONS.md` 或 `docs/MADAGASCAR_COMPATIBILITY.md`。

## 推荐下一步

优先从 `docs/NEXT_MIGRATION_BACKLOG.md` 的 P0/P1 任务中选择。当前最值得推进的是：

- 注册或明确 CLI console scripts。
- `sfget/sfdisfil/sfbyte` 等基础兼容工具。
- `sfsmooth/sfnoise/sfricker`。
- NMO/Semblance 的 C++ kernel。
- 为真实 Madagascar 环境建立可重复对照测试。

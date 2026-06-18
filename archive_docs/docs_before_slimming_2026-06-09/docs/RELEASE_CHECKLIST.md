# Release Checklist

生成日期：2026-06-09。本文用于阶段 A 发布前稳定化检查。

## 1. 项目定位确认

- 本项目不是完整 Madagascar clone。
- 本项目是 Python 友好的 RSF/地球物理本地工具包。
- pure Python 必须始终可用。
- C++/hybrid 只能是 optional acceleration，不能成为运行硬依赖。

## 2. 环境检查

- Python 版本：`pyproject.toml` 要求 `>=3.10`。
- 当前推荐解释器：`D:\HczApp\Anaconda\envs\mywork\python.exe`。
- editable install：从 `hcz_mada/` 目录安装。
- 测试依赖：`pytest`。
- 绘图依赖：`matplotlib`，用于 plot quicklook 和相关测试。
- NumPy 是核心依赖。
- SciPy 当前不是硬依赖；不要把它作为 pure Python 基线必需项。
- 原始 Madagascar 是 optional，只用于 `original_madagascar` 对照测试。
- C++ compiler 是 optional，只用于显式构建 `pymadagascar._core`。

## 3. 安装检查

推荐命令：

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install -e ".[test]" --no-build-isolation
```

如果 shell 不支持 `".[test]"`，分步安装：

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install -e . --no-build-isolation
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install pytest matplotlib
```

默认 `PYMADAGASCAR_BUILD_CPP=OFF`，不编译 C++ 时包仍必须可 import、可运行 API/CLI、可通过 pure Python 测试。

## 4. 测试检查

必须运行：

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q -rs
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_release.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_cli_inventory.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_docs_commands.py
```

建议按需运行：

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_wsl_madagascar.py
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q -rs -m original_madagascar
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest tests\test_hybrid_import.py tests\test_hybrid_xcorr.py -q -rs
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest tests\test_my_workflows.py -q
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest tests\test_cli_smoke.py -q
```

WSL Madagascar optional comparison:

- Windows 本机可以没有原始 Madagascar；pure Python 测试不得依赖 `sf*`。
- 如需使用 WSL 中的 Madagascar，对照环境为 `ubuntu2204`。
- PowerShell 先运行 `wsl -l -v` 和
  `D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_wsl_madagascar.py`。
- 真正的 `original_madagascar` pytest 应进入 WSL 后运行：
  `wsl -d ubuntu2204`，在 WSL 中设置 `RSFROOT/PATH`，进入仓库并执行
  `python -m pytest -q -rs -m original_madagascar`。
- 如果 WSL Madagascar 版本较旧，差异应记录为 version difference，不得破坏 pure Python baseline。

Examples smoke 应至少覆盖 `examples/local_quickstart.py` 和 `examples/my_workflows/`，当前由 pytest workflow smoke 维护。

## 5. CLI 检查

- 当前有 67 个用户向 CLI module，不含 `base.py` 和 `__init__.py`。
- 当前有 25 个 `pymada-*` console_scripts。
- `pyproject.toml` 的 console_scripts 必须与 `docs/CLI_INVENTORY.md` 对齐。
- 未注册 CLI 必须使用 `python -m pymadagascar.cli.<name>`，不能在文档里写成可直接运行的 `pymada-*`。
- 运行 `tools/check_cli_inventory.py` 和 `tools/check_docs_commands.py`。

## 6. 文档检查

发布前检查这些文档是否与代码、测试、examples 对齐：

- `docs/TEST_STATUS.md`
- `docs/CLI_INVENTORY.md`
- `docs/API_STABILITY.md`
- `docs/COVERAGE_MATRIX.md`
- `docs/MADAGASCAR_FULL_COVERAGE_AUDIT.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/MADAGASCAR_COMPATIBILITY.md`
- `docs/PYTHONIC_USAGE.md`
- `docs/SIGNAL_COMPATIBILITY.md`
- `docs/MASTER_HANDOFF_BEFORE_BATCH_MIGRATION.md`
- `docs/CHANGELOG.md`
- `docs/WSL_MADAGASCAR_TESTING.md`
- `docs/design/HEADER_METADATA_COMMANDS_DESIGN.md`

历史交接文档可以保留旧状态，但必须有明确 historical note，最新状态以 master handoff 和 test status 为准。

## 7. 覆盖率检查

- full coverage 和 core coverage 不得混用。
- 当前 full Madagascar/alias command-surface coverage 是 `56 / 2114 = 2.65%`。
- 当前 core `system/` + `plot/main` command-surface coverage 是 `51 / 301 = 16.94%`。
- `user/*` 不作为近期目标。
- VPlot/SCons/book/IWAVE/RVL/MPI/CUDA/PETSc 不作为近期目标。

## 8. 发布前禁止事项

- 不允许把失败测试改成 skip。
- 不允许破坏 pure Python fallback。
- 不允许把 prototype 标为 stable。
- 不允许文档中出现未注册的 `pymada-*`。
- 不允许未测试就更新覆盖率。
- 不允许直接迁移大型模块。
- 不允许在 release check 中偷偷新增算法、新增迁移批次、编译 C++ 或改动原始 Madagascar 源码。

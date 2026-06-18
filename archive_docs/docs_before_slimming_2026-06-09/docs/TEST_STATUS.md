# Test Status

生成日期：2026-06-09。测试环境：

- Python：`D:\HczApp\Anaconda\envs\mywork\python.exe`
- 工作目录：`hcz_mada/`
- 原始 Madagascar 程序：未安装或不在 PATH。
- Hybrid C++ 扩展：未编译，`pymadagascar.hybrid.cpp_available()` 返回 `False`。

## Pytest

命令：

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q
```

结果：

```text
462 passed, 48 skipped in 19.18s
```

失败数量：0。

2026-06-09 stage-A audit note: plain `python` was not available on this
PowerShell PATH, so the documented project interpreter
`D:\HczApp\Anaconda\envs\mywork\python.exe` is the authoritative local test
interpreter for this status file.
Stage B-1 recheck: plain `python` is still not available on the current
PowerShell PATH.
Stage B-2 recheck: plain `python` is still not available on the current
PowerShell PATH; `D:\HczApp\Anaconda\envs\mywork\python.exe` remains the local
test interpreter.
Stage B-3-1 recheck: plain `python` is still not available on the current
PowerShell PATH; `D:\HczApp\Anaconda\envs\mywork\python.exe` remains the local
test interpreter.

## Slow Tests

Stage B-3-1 did not rerun the durations sweep; this section is the Stage A
snapshot. The authoritative Stage B-3-1 full-suite result is the Pytest section
above and the `-q -rs` result below.

命令：

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q --durations=10
```

结果：

```text
434 passed, 38 skipped in 14.70s
```

最慢 10 个测试：

| 用例 | 时间 |
| --- | ---: |
| `tests/test_complex_tools.py::test_complex_tool_cli_subprocess_smoke` | 0.78s |
| `tests/test_my_workflows.py::test_my_workflow_runs_and_writes_outputs[plot_grey_graph_workflow.py]` | 0.72s |
| `tests/test_mask_cut_reverse.py::test_mask_cut_reverse_cli_subprocess` | 0.61s |
| `tests/test_my_workflows.py::test_my_workflow_runs_and_writes_outputs[seismic_basic_agc_mute_stack_workflow.py]` | 0.60s |
| `tests/test_noise.py::test_noise_cli_subprocess_generates_and_adds_noise` | 0.44s |
| `tests/test_fft.py::test_fft_cli_subprocess_round_trip` | 0.41s |
| `tests/test_byte.py::test_byte_output_can_feed_grey_quicklook` | 0.40s |
| `tests/test_plot.py::test_graph_writes_pdf` | 0.26s |
| `tests/test_my_workflows.py::test_my_workflow_runs_and_writes_outputs[fft_bandpass_workflow.py]` | 0.23s |
| `tests/test_smooth.py::test_smooth_cli_subprocess` | 0.23s |

当前没有明显慢测试瓶颈。

## Skipped Tests

48 个 skip 的原因，使用 `-q -rs` 和 `-m original_madagascar` 检查：

| 测试文件 | 原因 |
| --- | --- |
| `tests/test_array_math.py` | 原始 `sfscale` 未安装 |
| `tests/test_cat.py` | 原始 `sfcat` 未安装 |
| `tests/test_complex_tools.py` | 原始 `sfreal`, `sfimag`, `sfcmplx`, `sfrtoc` 未安装 |
| `tests/test_convolution.py` | 原始 `sfconv` 未安装 |
| `tests/test_cp_rm_min_max.py` | 原始 `sfcp`, `sfrm`, `sfmin`, `sfmax` 未安装 |
| `tests/test_dd.py` | 原始 `sfdd` 未安装 |
| `tests/test_disfil.py` | 原始 `sfdisfil` 未安装 |
| `tests/test_fft.py` | 原始 `sffft1` 未安装 |
| `tests/test_filter.py` | 原始 `sfbandpass` 未安装 |
| `tests/test_fk.py` | 原始 `sfdipfilter` 未安装 |
| `tests/test_get.py` | 原始 `sfget` 未安装 |
| `tests/test_header_window_cut.py` | 原始 `sfheaderwindow`, `sfheadercut` 未安装 |
| `tests/test_hybrid_xcorr.py` | optional C++ extension 未编译 |
| `tests/test_info_attr_put.py` | 原始 `sfin`, `sfattr`, `sfput` 未安装 |
| `tests/test_kirchhoff.py` | 原始 `sfkirchnew` 未安装 |
| `tests/test_mask_cut_reverse.py` | 原始 `sfmask`, `sfcut`, `sfreverse` 未安装 |
| `tests/test_math.py` | 原始 `sfmath` 未安装 |
| `tests/test_mul_div_tpow_interleave.py` | 原始 `sfmul`, `sfdiv`, `sftpow`, `sfinterleave` 未安装 |
| `tests/test_nmo_semblance.py` | 原始 `sfnmo`, `sfvscan` 未安装 |
| `tests/test_noise.py` | 原始 `sfnoise` 未安装 |
| `tests/test_pad_spray.py` | 原始 `sfpad`, `sfspray` 未安装 |
| `tests/test_radon.py` | 原始 `sfslant` 未安装 |
| `tests/test_segy.py` | 原始 `sfsegyread` 未安装 |
| `tests/test_seismic_processing.py` | 原始 `sfpow`, `sfstack` 未安装 |
| `tests/test_smooth.py` | 原始 `sfsmooth` 未安装 |
| `tests/test_spike.py` | 原始 `sfspike` 未安装 |
| `tests/test_testing_runner.py` | 原始 Madagascar command-line programs 未安装 |
| `tests/test_transp.py` | 原始 `sftransp` 未安装 |
| `tests/test_wavelet.py` | 原始 `sfricker1` 未安装 |
| `tests/test_window.py` | 原始 `sfwindow` 未安装 |

手工检查 PATH 中缺失的代表程序：

`sfspike`, `sfget`, `sfdisfil`, `sfmath`, `sfnoise`, `sfricker1`, `sfwindow`, `sfheaderwindow`, `sfheadercut`, `sfin`, `sfattr`, `sfput`, `sfcat`, `sftransp`, `sfcp`, `sfrm`, `sfmin`, `sfmax`, `sfmul`, `sfdiv`, `sftpow`, `sfinterleave`, `sfdd`, `sfreal`, `sfimag`, `sfcmplx`, `sfrtoc`, `sfbandpass`, `sffft1`, `sfnmo`, `sfsegyread`。

## Original Madagascar Comparison Tests

Current machine status: original Madagascar `sf*` programs are not installed or
not on `PATH`, so tests marked `original_madagascar` skip when their required
command is unavailable. This is expected and must not make pure Python tests
fail. In the current environment, `-m original_madagascar` selects 47 tests; all
47 skip because the required upstream commands are unavailable. The remaining
skip in the full suite is the optional hybrid C++ backend test.

WSL optional comparison note: the intended WSL distribution for this workstation
is `ubuntu2204`; see `docs/WSL_MADAGASCAR_TESTING.md`. In the current
Windows/Codex session, `tools/check_wsl_madagascar.py` could not access that
distribution:

```text
WSL_E_DISTRO_NOT_FOUND
wsl -l -v: no installed distributions are visible in this session
```

No WSL `original_madagascar` pytest run was performed in this session. If
`ubuntu2204` is available in a normal PowerShell session, enter WSL and run
`python -m pytest -q -rs -m original_madagascar` from inside the WSL repository
path. Older Madagascar behavior should be recorded as version differences and
must not make pure Python tests depend on Madagascar.

Marker strategy:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q -rs -m original_madagascar
```

Current marker-only check:

```text
47 skipped, 463 deselected in 0.51s
```

Current full `-q -rs` check:

```text
462 passed, 48 skipped in 19.18s
```

Use the command above on a machine where original Madagascar is installed and
`sf*` programs are discoverable through `PATH` or `RSFROOT/bin`. Use `-rs` to
show skip reasons for commands that are still missing.

The setup checklist and platform notes are in
`docs/ORIGINAL_MADAGASCAR_COMPARISON.md`.

## Release Check Tools

命令：

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe tools\check_release.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools\check_cli_inventory.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools\check_docs_commands.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools\check_wsl_madagascar.py
```

结果：

```text
check_release.py: passed
check_cli_inventory.py: passed; 67 CLI modules, 25 console_scripts
check_docs_commands.py: passed; 262 pymada-* mentions, all registered
check_wsl_madagascar.py: failed in this Windows/Codex session; ubuntu2204 not visible to WSL
```

前三个 release 工具不依赖原始 Madagascar、C++ extension、plain `python` 或外部大数据。`check_wsl_madagascar.py` 是手动 optional 探测工具；失败只表示当前 WSL/Madagascar 对照环境不可用，不影响 pure Python 测试基线。

## Quality Checks

当前仓库没有 ruff/mypy/black/isort 配置文件，也没有在 `pyproject.toml` 中配置对应工具。

`mywork` 环境检查：

```text
ruff=False, mypy=False, black=False, isort=False
```

因此本次没有运行 ruff、mypy、black、isort。后续如果新增配置，必须在本文件中记录对应命令和结果。

## Hybrid Tests

命令：

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest tests\test_hybrid_import.py tests\test_hybrid_xcorr.py -q
```

结果：

```text
17 passed, 1 skipped in 0.19s
```

skip 原因：`optional C++ extension is not built in this environment`。

## Hybrid Build Status

默认安装使用 fallback 安全路径：

```powershell
$env:PATH = "D:\HczApp\Anaconda\envs\mywork\Scripts;" + $env:PATH
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install -e . --no-build-isolation
```

该命令已成功。

显式启用 C++ 扩展时失败：

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install -e . --no-build-isolation --config-settings=cmake.define.PYMADAGASCAR_BUILD_CPP=ON
```

失败原因：

```text
No CMAKE_CXX_COMPILER could be found
```

需要安装 Visual Studio Build Tools C++ 编译器或配置 `CXX`/`CMAKE_CXX_COMPILER`。

## Benchmark Status

命令：

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe benchmarks\bench_xcorr.py --ntraces 128 --nsamples 256 --dtype float32 --mode full --repeat 5 --report benchmarks\bench_xcorr_report.md
```

结果：

| implementation | backend | time_s | speedup_vs_python | peak_mem_mib | max_abs_error |
| --- | --- | ---: | ---: | ---: | ---: |
| `python_numpy` | `python_numpy` | 0.001133 | 1.000 | 0.252 | reference |
| `hybrid_cpp` | unavailable | n/a | n/a | n/a | n/a |

C++ 加速比暂不可测，原因是缺少 C++ 编译器。

## 需要特殊环境的测试

- 需要原始 Madagascar：所有 `original_madagascar_available(...)` 对照测试。
- 需要 SEG-Y 测试数据：当前使用 synthetic 小数据；真实数据回归尚未建立。
- 需要 C++ 编译环境：`tests/test_hybrid_xcorr.py::test_batch_xcorr_cpp_result_matches_numpy_when_extension_available` 和后续所有 C++ backend benchmark。

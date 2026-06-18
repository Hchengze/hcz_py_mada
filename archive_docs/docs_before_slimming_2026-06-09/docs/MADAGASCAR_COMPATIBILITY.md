# Madagascar Compatibility

本文说明当前项目与 Madagascar/RSF 的兼容范围和差异。

## 参数风格兼容部分

当前 `RSFParams` 和 CLI 基础层支持：

- `key=value` 参数。
- `par=file` 参数文件：文件中可写空白或换行分隔的 `key=value`。
- 位置输入文件，例如 `input.rsf out=output.rsf`。
- `in=file.rsf` 和 `out=file.rsf` 风格。
- bool 参数：`yes/no`, `true/false`, `y/n`, `1/0`。
- int/float/string/list 类型读取。
- 参数文件中的空行、`#` 注释行和行尾注释。
- 单引号或双引号字符串，例如 `label1="Time sample"`。
- 重复 key 使用最后一次出现的值；`par=file` 与命令行参数按从左到右顺序处理，因此后出现的参数覆盖先出现的参数。
- 默认值。
- 缺失必要参数时报错。
- 每个 CLI 通过 `main(argv)` 支持测试。

CLI 轴号通常保持 Madagascar 风格 1-based。例如 `axis=1` 指 RSF `n1` 轴。

## 数据格式兼容部分

当前 RSF I/O 支持：

- 文本 header。
- binary sidecar 文件。
- `ascii_float` text sidecar 子集：`data_format=ascii_float`, `esize=0`。
- `in=` 指向 sidecar 数据文件。
- `n1/n2/n3...` 维度。
- `o1/d1/label1/unit1...` 轴元数据。
- 常用 native dtype：`float32`, `float64`, `int32`, `complex64`。
- `ascii_float` 读写 1D/2D/3D float 数据；读取返回 NumPy `float32`。
- 多维数组中 `n1` 为最快变化轴的 Madagascar/RSF 约定。
- header/data roundtrip。

`Hypercube`/`Axis` 用于统一规则采样轴元数据。

## 兼容性分层

当前项目按三层理解 Madagascar 兼容性：

| 层级 | 当前范围 | 说明 |
| --- | --- | --- |
| 兼容子集 | RSF header/binary I/O、`ascii_float` text sidecar、`n/o/d/label/unit` 轴元数据、`key=value` CLI 参数、常用 `sfspike/sfmath/sfnoise/sfricker/sfwindow/sfin/sfget/sfdisfil/sfattr/sfput/sfcat/sftransp/sfmask/sfcut/sfreverse/sfcp/sfrm/sfmin/sfmax/sfdd/sfreal/sfimag/sfcmplx/sfrtoc` 子集 | 目标是对小型确定 fixture 行为一致或数值接近，并通过 optional original Madagascar comparison tests 验证。 |
| Python 风格替代 | Matplotlib `grey/graph/wiggle`、NumPy FFT/filter/convolution、Python API、`pymada-*` console scripts、hybrid wrapper fallback | 目标是本地 Python 工作流顺手、可测试、可维护，不复制 Madagascar 的 C API、VPlot/pens 或 SCons 生态。 |
| 不追求字节级一致 | CLI 文本输出、VPlot 文件、SCons/book 构建、所有 legacy 参数和 alias、复杂 streaming/out-of-core 行为、工业级 imaging/modeling 数值细节 | 这些差异必须在文档或测试注释中说明，不能假装是完整 Madagascar clone。 |

`stable subset` 表示当前项目范围内可用，不表示完整参数兼容；`prototype` 表示小数据验证或后续设计基线，不应作为生产级 Madagascar 替代。

## 行为不一致的部分

当前项目不追求完全复刻以下行为：

- 原始 CLI 输出文本的字节级一致性。
- 原始 `sf*` 程序所有参数、别名和历史兼容路径。
- Madagascar C API 的全局状态、`sf_file` 生命周期和 SCons 环境。
- VPlot/pens 输出格式。
- 大文件 streaming 行为和性能。
- 某些数值算法的边界、归一化、权重和 antialiasing 细节。
- `sfmath` 的完整表达式语言；当前只允许安全白名单表达式。
- `par=file` 当前是稳定实用子集，支持常见参数文件、注释、引号、list 和覆盖顺序；不复刻原始 C API 的 `sf_parenv` 环境变量注入、selfdoc/sfdoc 启动行为、全局参数表生命周期、stdin 参数文件或 RSF header 三字节结束标记读取。
- `sfbandpass`、`sffft1` 等信号处理命令的全部 legacy 参数；当前 NumPy 子集和差异详见 `docs/SIGNAL_COMPATIBILITY.md`。
- `ascii_float` 支持使用 sidecar 文本数据文件，写出时默认每行最多 8 个空白分隔数字；不追求原始 `sfdd form=ascii line=/format=/strip=` 的字节级文本一致。
- `sfget` 当前是文件路径驱动的 header query 子集；缺失 key 默认报错，提供 `default=` 时返回默认值。原始 `sfget` 对缺失 key 只 warning 并继续，这里为了脚本稳定性有意不同。
- `sfdisfil` 当前使用 Python-friendly one-value-per-line 文本格式；只保证小数据数值序列稳定，不保证原始 printf 分栏、`header=`/`trailer=` 或字节级文本一致。
- `sfreal/sfimag/sfcmplx/sfrtoc` 当前覆盖 file-backed RSF 的常用复数转换路径；`sfimag` 在原始 Madagascar 中是 `sfreal` 的 alias，本项目保留独立 Python CLI；`sfrtoc pair=y` 暂未实现；当前 RSF I/O 不支持落盘 `complex128`。
- `sfnoise` 当前使用 NumPy RNG；固定 `seed=` 在 pymadagascar 内可重复，但随机数序列不追求与原始 Madagascar 的 `init_genrand`/Box-Muller 实现一致。直接 `n1/n2/...` 生成噪声是 Python-friendly 扩展，原始 `sfnoise` 通过 `rep=y` 替换输入数据。
- `sfricker` 当前实现的是 Python-friendly direct time-domain Ricker wavelet generator，支持 `frequency/f`, `dt`, `nt`, `peak_time/t0` 和 `amplitude`。原始 `system/seismic/Mricker.c` 是从输入频谱估计 Ricker 参数，`sfricker1/2` 是卷积/非平稳卷积工具；这些行为没有在当前子集中复刻。
- `sfmask` 子集支持 real/int/float RSF 的 inclusive `min=`/`max=`，输出 `native_int` 的 0/1 mask；不支持 complex input。
- `sfcut` 子集支持用 1-based RSF `axis=` 以及 0-based `f=`, `n=`, `j=` 或 `f#/n#/j#` 指定要置零的样点窗口。它不改变 shape/header。`sfheadercut` 是基于 mask/header RSF 的不同命令，当前仅实现 Python mask 子集。
- `sfreverse` 子集支持 `axis=` 或非负 `which=` 位掩码，默认像 Madagascar `opt=y` 一样更新反转轴的 `o#` 和 `d#`；也支持 `update_header=no`/`opt=i` 保留 header。原始 `opt=n` 和 out-of-core/memsize 行为没有复刻。
- `sfcp` 子集是 file-backed RSF header+sidecar 的安全复制，会更新输出 header 的 `in=`，但不实现 `sfmv` 或 stdin/stdout streaming。
- `sfmul`/`sfdiv` 子集来自 upstream `sfadd` alias 行为，只覆盖 RSF x RSF、RSF x scalar、RSF / RSF 和 RSF / scalar；不复刻 `sfadd` 的多输入预处理参数。`sfdiv` 使用显式 `zero_policy`，默认遇到零分母报错。
- `sftpow` 子集按 1-based `axis=` 沿指定 RSF 轴施加 `t ** power`，使用本项目 `Axis.coordinates()` 约定 `o+i*d`；原始 `Mtpow.c` 的 `o+(i+1)d`、`xpow=` 和 float-only 限制没有完整复刻。
- `sfinterleave` 子集要求所有输入 shape 一致，沿 1-based `axis=` 交错，输出轴长度为输入轴长度乘以输入文件数，并继承第一个输入的 `o#`/`d#`。
- `sfheaderwindow`/`sfheadercut` 子集使用一维 mask/header RSF 沿 1-based `axis=` 选择或置零普通 RSF 数据。`sfheaderwindow` 只接受连续 mask 选择并更新规则轴 `n#`/`o#`；`sfheadercut` 保持 shape/header。两者都不支持完整 Madagascar header table、trace header 或 SEG-Y trace header。
- `sfrm` 子集默认 dry-run；实际删除需要 `confirm=y`。目录、递归、Unix `-f/-i/-v` shorthand flags 和交互式 prompt 没有复刻。
- `sfmin/sfmax` 子集输出 deterministic key=value text statistic。原始 `sfmin/sfmax` 是 `sfstack` alias 并写 RSF 输出；当前 Python CLI 的文本格式不追求与原始输出一致。

## 暂未实现的 Madagascar 机制

- `par=file` 的历史扩展语义，例如 `sf_parenv` 环境变量参数注入、selfdoc/sfdoc 行为、stdin 参数文件、C API 全局状态和所有旧式转义细节。
- 完整 `DATAPATH`/`RSFROOT`/SCons flow 集成。
- 全部 `data_format`，尤其是 XDR 和 ASCII 全组合；当前只新增了 `ascii_float`，没有实现 `ascii_int/ascii_double/ascii_complex` 等。
- 原始 `sfget` 的 `all=y` 和 stdin header-table 模式，完整 `sfdisfil` printf/column/header/trailer 行为，完整 `sfbyte`，原始 `sfricker` 频谱估计/`sfricker1/2` 卷积族，完整 `sfcut` 坐标窗口别名/streaming 行为、完整 `sfheaderwindow inv=`/非连续 trace 选择、完整 header table/headermath/headersort 语义、`sfreverse opt=n`/out-of-core 控制、完整 `sfadd` multi-input preprocessing、`sftpow xpow=`，以及 `sfrtoc pair=y`。
- 完整 SEG-Y/SU trace header 兼容。
- 完整 VPlot。
- 完整 3D/industrial imaging/modeling。
- 全量 `book/`, `user/`, `trip/` 目录迁移。

## 当前对照测试机制

对照测试位于各 `tests/test_*.py` 中，通常模式为：

1. 用 `pymadagascar.testing.runner.original_madagascar_available("sfxxx")` 检查原始命令。
2. 不可用时 `pytest.skip(...)`。
3. 可用时运行 `run_original_madagascar(...)`。
4. 用 `read_rsf` 和 `numpy.testing.assert_allclose` 比较 Python 输出和原始输出。

当前本机未安装原始 Madagascar 命令，因此所有原始对照测试 skip。详见 `docs/TEST_STATUS.md`。

## 如何增加新的兼容性测试

新增一个迁移模块时，至少添加：

1. Pure Python deterministic unit test。
2. RSF roundtrip test。
3. CLI test。
4. 原始 Madagascar optional comparison test。

推荐模板：

```python
def test_original_sfxxx_comparison_when_available(tmp_path):
    if not original_madagascar_available("sfxxx"):
        pytest.skip("Original Madagascar sfxxx is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"

    # create small deterministic fixture
    # run original sfxxx
    # run pymadagascar implementation
    # compare data/header with tolerances
```

比较规则：

- shape 和 header 关键字段应精确比较。
- float/complex data 使用 `assert_allclose`。
- 容差必须按 dtype 和算法说明。
- 如果原始 Madagascar 行为与本项目设计不同，测试名和注释要说明差异。

## 当前建议的对照测试优先级

| 优先级 | 命令 | 原因 |
| --- | --- | --- |
| P0 | `sfspike`, `sfwindow`, `sfcat`, `sftransp`, `sfdd` | 基础命令影响范围最大 |
| P0 | `sfin`, `sfget`, `sfdisfil`, `sfattr`, `sfput` | header、数据检查和小数据 dump 基础 |
| P0 | `sfreal`, `sfimag`, `sfcmplx`, `sfrtoc` | FFT、复谱和后续复数滤波的基础 |
| P1 | `sfmath`, `sfnoise`, `sffft1`, `sfbandpass` | 合成数据和数值差异容易积累 |
| P1 | `sfnmo`, `sfvscan` | 地震处理核心 |
| P2 | `sfsegyread`, `sfsegywrite` | 需要真实格式数据 |
| P2 | `sfkirchnew`, `sfslant` | prototype 需要谨慎收敛 |

## 新对话兼容性提醒

不要为了让某个原始对照测试“看起来通过”而静默改变公共 API。正确流程是：

1. 阅读原始源码。
2. 写清楚 Madagascar 行为。
3. 判断是否应兼容。
4. 若兼容，改实现和测试。
5. 若不兼容，在 `docs/KNOWN_LIMITATIONS.md` 和测试注释中记录。

## Pytest Marker And Environment Reference

Original Madagascar comparison tests are selected with the
`original_madagascar` pytest marker. They remain optional and should skip when
the required upstream `sf*` executable is not available.

Use:

```powershell
python -m pytest -q -rs -m original_madagascar
```

Environment setup, `RSFROOT`/`PATH` checks, platform notes, and marker policy are
documented in `docs/ORIGINAL_MADAGASCAR_COMPARISON.md`.

# Local Install And Usage

本文面向本地长期使用 `pymadagascar` 的工作流。当前目标是 Python 友好的 RSF/地球物理处理工具，不是完整复刻 Madagascar 的 2000+ 命令。

## Install

建议在已有 Python 环境中从 `hcz_mada/` 目录安装 editable 包：

```powershell
cd E:\HczDocument\BaiduDisk\BaiduSyncdisk\HCZ_work\CodexProject\HCZ_madagascar\hcz_mada
python -m pip install -e ".[test]" --no-build-isolation
```

当前 Windows 本机记录的推荐解释器是：

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe
```

如果 PowerShell PATH 中没有 plain `python`，请把下面示例中的 `python`
替换为该完整路径。

如果你的 shell 不喜欢 `".[test]"`，可以先安装包，再确认 pytest 已可用：

```powershell
python -m pip install -e . --no-build-isolation
python -m pip install pytest matplotlib
```

默认安装不会编译 C++ extension。`pyproject.toml` 中 `PYMADAGASCAR_BUILD_CPP=OFF` 是故意的，这保证没有 C++ 编译器时 pure Python 版本仍然可用。

## Run Tests

完整测试：

```powershell
python -m pytest -q
```

带 skip 原因：

```powershell
python -m pytest -q -rs
```

当前本机没有原始 Madagascar `sf*` 程序，相关 optional comparison tests 会 skip。当前环境也没有 C++ 编译器，C++ backend 专项测试会 skip 或走 Python fallback。

发布前轻量检查：

```powershell
python tools\check_release.py
python tools\check_cli_inventory.py
python tools\check_docs_commands.py
```

这些检查不依赖原始 Madagascar、C++ extension 或外部大数据。

## CLI Usage

安装后，稳定的本地命令可以直接用 `pymada-*`：

```powershell
pymada-spike n1=10 k1=5 out=spike.rsf
pymada-info spike.rsf
pymada-get spike.rsf key=n1,d1
pymada-disfil spike.rsf max=10 axis_format=flat
pymada-math n1=100 o1=0 d1=0.004 output="sin(2*pi*10*x1)" out=sine.rsf
pymada-noise n1=100 o1=0 d1=0.004 out=noise.rsf seed=1 std=0.1
pymada-ricker out=ricker.rsf f=25 dt=0.001 nt=256 peak_time=0.04
pymada-window sine.rsf out=sine_win.rsf f1=10 n1=50
pymada-attr sine_win.rsf
pymada-dd sine_win.rsf out=sine_double.rsf type=float64
pymada-fft sine_win.rsf out=sine_fft.rsf axis=1
pymada-real sine_fft.rsf out=sine_fft_real.rsf
pymada-imag sine_fft.rsf out=sine_fft_imag.rsf
pymada-rtoc sine_win.rsf out=sine_complex.rsf
pymada-noise sine_win.rsf out=sine_noisy.rsf seed=1 std=0.1
pymada-bandpass sine.rsf out=sine_bp.rsf flo=5 fhi=20 axis=1 taper=2
pymada-byte sine.rsf out=sine_byte.rsf pclip=99
pymada-smooth sine.rsf out=sine_smooth.rsf rect1=3
pymada-mask sine.rsf out=sine_mask.rsf min=-0.5 max=0.5
```

稳定 CLI 都支持 Madagascar 风格 `par=file` 参数文件。参数文件可包含空行、
`#` 注释、引号字符串、list/repeat 语法；命令行和参数文件按从左到右顺序
处理，后出现的同名 key 覆盖前面的值。例如：

```powershell
@"
# spike.par
n1=10
k1=5
label1="Time sample"
"@ | Set-Content spike.par

pymada-spike par=spike.par out=spike.rsf
pymada-spike par=spike.par n1=20 out=spike20.rsf
```

当前注册的 console scripts：

当前共有 25 个已注册 console scripts：

`pymada-info`, `pymada-get`, `pymada-disfil`, `pymada-real`, `pymada-imag`, `pymada-cmplx`, `pymada-rtoc`, `pymada-noise`, `pymada-ricker`, `pymada-spike`, `pymada-math`, `pymada-window`, `pymada-attr`, `pymada-put`, `pymada-dd`, `pymada-cat`, `pymada-transp`, `pymada-fft`, `pymada-bandpass`, `pymada-byte`, `pymada-smooth`, `pymada-boxsmooth`, `pymada-mask`, `pymada-cut`, `pymada-reverse`。

所有 CLI 模块仍可用模块方式调用：

```powershell
python -m pymadagascar.cli.spike n1=10 k1=5 out=spike.rsf
python -m pymadagascar.cli.grey panel.rsf out=panel.png
python -m pymadagascar.cli.cp input.rsf out=copy.rsf
python -m pymadagascar.cli.min input.rsf axis=0
python -m pymadagascar.cli.max input.rsf axis=1
python -m pymadagascar.cli.rm copy.rsf dry_run=y
```

Stage B-1 note: `cp`, `rm`, `min`, and `max` are module-only entry points.
They are not registered as console scripts; use `python -m`.

完整清单见 `docs/CLI_INVENTORY.md`。

## Python API Usage

```python
from pathlib import Path

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.generic.math import math_rsf
from pymadagascar.generic.noise import noise_rsf
from pymadagascar.generic.info import disfil_rsf, get_header_values
from pymadagascar.generic.spike import spike
from pymadagascar.generic.window import window_rsf
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.signal.wavelet import ricker_rsf

out = Path("work")
out.mkdir(exist_ok=True)

data = np.arange(12, dtype=np.float32).reshape(3, 4)
header = RSFHeader({"o1": 0.0, "d1": 0.004, "label1": "Time", "unit1": "s"})
write_rsf(out / "input.rsf", data, header)

rsf = read_rsf(out / "input.rsf")
axis_values = get_header_values(out / "input.rsf", ["n1", "d1", "label1"])
text_dump = disfil_rsf(out / "input.rsf", max_values=8)
sp = spike((16,), locations=8)
wave = math_rsf("sin(2*pi*10*x1)", axes=[Axis(n=64, o=0.0, d=0.004)])
win = window_rsf(RSFArray(wave.data, wave.header), {"f1": 8, "n1": 32})

write_rsf(out / "spike.rsf", sp.data, sp.header)
write_rsf(out / "wave.rsf", wave.data, wave.header)
write_rsf(out / "wave_window.rsf", win.data, win.header)
noise_rsf(out / "wave_window.rsf", out / "wave_noisy.rsf", seed=1, std=0.1)
ricker_rsf(out / "ricker.rsf", frequency=25.0, dt=0.001, nt=256, peak_time=0.04)
```

更多本地示例见 `examples/local_quickstart.py`, `examples/cp_rm_min_max_demo.py` 和 `examples/my_workflows/`。

运行 workflow 示例：

```powershell
python examples\my_workflows\basic_rsf_io_workflow.py
python examples\my_workflows\fft_bandpass_workflow.py .\scratch\fft_workflow
```

## No Original Madagascar Installed

Pure Python 功能不依赖原始 Madagascar。没有 `sfspike`、`sfmath`、`sfwindow` 等原始命令时：

- `pymadagascar` API 和 CLI 仍可运行。
- pytest 中的 optional original Madagascar comparison tests 会自动 skip。
- 不要把 `RSFROOT` 或原始 SCons 构建产物当作 pure Python 的硬依赖。

如果你之后安装了原始 Madagascar 并把 `sf*` 放到 `PATH`，可以运行：

```powershell
python -m pytest -q -rs
```

这会自动启用可用命令的对照测试。

## No C++ Compiler Installed

没有 C++ 编译器是受支持场景：

- 默认不编译 `pymadagascar._core`。
- `pymadagascar.hybrid.cpp_available()` 会返回 `False`。
- hybrid wrapper 必须自动 fallback 到 NumPy/Python。
- pure Python API 和 CLI 不能因为 C++ 不可用而失败。

只有当你明确要验证 C++ backend 时，才需要安装 Visual Studio Build Tools 或配置 `CXX`/`CMAKE_CXX_COMPILER`，再显式启用：

```powershell
python -m pip install -e . --no-build-isolation --config-settings=cmake.define.PYMADAGASCAR_BUILD_CPP=ON
```

## Prototype Modules

以下模块目前是 prototype 或 partial，适合小数据实验、教学和后续开发基线，不应当当作完整工业实现：

- `pymadagascar.io.segy.*`: 小型 2D SEG-Y/RSF 转换原型。
- `pymadagascar.plot.*`: Matplotlib quicklook，不复刻 VPlot/pens。
- `pymadagascar.seismic.nmo.*`: NMO 原型，offset/header/table 机制仍需扩展。
- `pymadagascar.seismic.semblance.*`: velocity scan 原型。
- `pymadagascar.seismic.fk.*`: FK spectrum/filter 原型。
- `pymadagascar.seismic.radon.*`: Radon/tau-p adjoint/prototype。
- `pymadagascar.imaging.kirchhoff.*`: 简化 2D post-stack Kirchhoff。
- `pymadagascar.modeling.acoustic2d.*`: 教学级 acoustic finite-difference 正演。
- `pymadagascar.hybrid.*`: 可选加速包装，当前机器可能只走 Python fallback。

稳定 API 边界见 `docs/API_STABILITY.md`。

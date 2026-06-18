# Signal Compatibility

本文档记录当前 `pymadagascar.signal` 中 FFT 和 bandpass 子集的 Madagascar
兼容范围。它是工作流兼容说明，不是原始 Madagascar 数值实现的完整复刻承诺。

## 原始源码核对

- `sffft1`: `../src-master/system/generic/Mfft1.c`
- `sfbandpass`: `../src-master/system/generic/Mbandpass.c`

## `sffft1` 子集

当前项目把原始 `sffft1` 拆成更 Python 化的接口：

| 功能 | Python API | CLI |
| --- | --- | --- |
| full complex FFT | `fft_rsf(input_path, output_path, axis=1, norm=None)` | `pymada-fft` or `python -m pymadagascar.cli.fft` |
| full complex inverse FFT | `ifft_rsf(input_path, output_path, axis=1, norm=None)` | `python -m pymadagascar.cli.ifft` |
| real-to-complex FFT | `rfft_rsf(input_path, output_path, axis=1, norm=None)` | `python -m pymadagascar.cli.rfft` |
| complex-to-real inverse real FFT | `irfft_rsf(input_path, output_path, axis=1, norm=None, n=None)` | API only |

参数兼容表：

| Madagascar 参数或行为 | 当前支持 | 说明 |
| --- | --- | --- |
| `in=` / positional input | yes | CLI 支持位置输入，也支持常规 `in=` 风格。 |
| `out=` | yes | 输出 RSF header path。 |
| first-axis FFT | yes | `axis=1` 是默认值。 |
| other axes | Python extension | `axis=` 使用 RSF 1-based 轴号，可处理 1D/2D/3D 常用数组。 |
| `inv=y` | partial | 当前用单独的 `ifft_rsf`/`irfft_rsf` 表达 inverse path，不复刻单一 `sffft1 inv=y` CLI。 |
| `sym=y` | no | 可用 NumPy `norm=ortho` 做对称归一化，但不声明与原始 Hermitian `sym` 字节级一致。 |
| `opt=y/n` | no | 当前不做 `kiss_fft_next_fast_size` 自动 padding。频率轴基于实际输入长度。 |
| `ot=` / `ot` file | no | 不实现 time-origin phase rotation 或逐道 origin 文件。 |
| `memsize=` / streaming | no | 当前为 in-memory NumPy 实现。 |
| `verb=` | no | CLI 不复刻原始 warning/verbosity 文本。 |
| `norm=` | Python extension | 支持 NumPy 的 `backward`, `forward`, `ortho`，或省略使用 NumPy 默认。 |

FFT 约定：

- `fft_rsf` 使用 `np.fft.fft` 后 `fftshift`，输出 full centered complex spectrum。
- `ifft_rsf` 假定输入来自 `fft_rsf` 的 centered full spectrum，先 `ifftshift` 再逆变换。
- `rfft_rsf` 使用 `np.fft.rfft`，只保存非负频率，`n# = n//2 + 1`。
- full FFT 频率轴来自 `np.fft.fftshift(np.fft.fftfreq(n, d))`。
- RFFT 频率轴来自 `np.fft.rfftfreq(n, d)`，`o#=0`，`d#=1/(n*d#)`。
- transform 后会保存 `fft_n#`, `fft_o#`, `fft_d#`, `fft_label#`, `fft_unit#`，inverse 时恢复这些 metadata。
- full FFT/RFFT 输出 `complex64/native_complex`；`irfft_rsf` 输出 `float32`。

与原始 Madagascar 的主要差异：

- 原始 `sffft1` 是第一轴 real/Hermitian FFT 主程序；当前 `pymada-fft` 是 full complex FFT，`python -m pymadagascar.cli.rfft` 才是更接近 forward `sffft1 opt=n` 的路径。
- 原始 `sffft1` 默认会选择 optimal FFT size；当前实现不自动 padding。
- 原始 forward/inverse 中包含 `ot` origin phase correction；当前未实现。
- 当前 optional original comparison 只覆盖 small forward `sffft1 opt=n` 与 `rfft_rsf` 的对照；inverse path 仅在文档中说明约定差异。

## `sfbandpass` 子集

当前项目实现的是 NumPy FFT 域 zero-phase taper 子集，不是原始 Butterworth 滤波器复刻。

| 功能 | Python API | CLI |
| --- | --- | --- |
| bandpass | `bandpass_rsf(input_path, output_path, flo, fhi, axis=1, taper=0.0)` | `pymada-bandpass` or `python -m pymadagascar.cli.bandpass` |
| lowpass | `lowpass_rsf(input_path, output_path, fcut, axis=1, taper=0.0)` | `python -m pymadagascar.cli.lowpass` |
| highpass | `highpass_rsf(input_path, output_path, fcut, axis=1, taper=0.0)` | `python -m pymadagascar.cli.highpass` |

参数兼容表：

| Madagascar 参数或行为 | 当前支持 | 说明 |
| --- | --- | --- |
| `in=` / positional input | yes | CLI 支持位置输入，也支持常规 `in=` 风格。 |
| `out=` | yes | 输出 RSF header path。 |
| `flo=` | yes | bandpass 低频 pass edge，单位是 cycles per `d#` unit。当前 CLI 要求显式提供。 |
| `fhi=` | yes | bandpass 高频 pass edge，必须小于等于 Nyquist。当前 CLI 要求显式提供。 |
| default `flo=0` / `fhi=Nyquist` | partial | API 可用 `lowpass_rsf`/`highpass_rsf` 表达对应情况；`bandpass` CLI 为稳定脚本要求显式 `flo` 和 `fhi`。 |
| first-axis filtering | yes | `axis=1` 是默认值。 |
| other axes | Python extension | `axis=` 使用 RSF 1-based 轴号，可处理 1D/2D/3D 常用数组。 |
| `phase=n` zero phase | yes, different algorithm | 当前总是 zero-phase FFT taper。 |
| `phase=y` minimum phase | no | 不实现原始 minimum-phase Butterworth 路径。 |
| `nplo=` / `nphi=` | no | 不实现 Butterworth pole count。 |
| `taper=` | Python extension | cosine taper width，单位与 `flo/fhi/fcut` 一致；`taper=0` 为矩形响应。 |
| streaming trace loop | no | 当前为 in-memory NumPy 实现。 |

Bandpass 约定：

- 输入必须是 real-valued RSF。
- 频率轴使用 `np.fft.rfftfreq(n, d#)`。
- `taper=0` 时 passband 边界是 inclusive：`freq >= flo` 且 `freq <= fhi`。
- `taper>0` 时使用 cosine transition，低端区间 `[flo-taper, flo]` 从 0 平滑到 1，高端区间 `[fhi, fhi+taper]` 从 1 平滑到 0。
- 输出 shape/header 继承输入，不修改采样轴。
- 输入 `float64` 时输出 `float64/native_double`；其他 real 输入当前输出 `float32/native_float`。

与原始 Madagascar 的主要差异：

- 原始 `sfbandpass` 使用 Butterworth low/high cutoff，参数有 `phase`, `nplo`, `nphi`。
- 当前实现使用频域乘法和 cosine taper，因此幅频响应、边界过渡和相位行为不与原始 `sfbandpass` 字节级一致。
- 当前 optional original comparison 只做小 fixture shape/header smoke，对数值等价不做承诺。

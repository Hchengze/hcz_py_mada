# CLI Inventory

生成日期：2026-06-09。本文列出当前 `pymadagascar.cli` 模块、对应 Madagascar 风格命令、调用方式、输入输出、稳定性和最小示例。

## 调用策略

本项目现在注册一批稳定的本地 console scripts。安装后可直接调用：

```powershell
pymada-spike n1=10 k1=5 out=spike.rsf
```

所有 CLI 模块仍保留 `python -m pymadagascar.cli.<name>` 调用方式。未注册 console script 的命令，应使用 `python -m`。

当前有 67 个用户向 CLI 模块（不含 `base.py` 和 `__init__.py`）和 25 个已注册 `console_scripts`。

当前已注册的 console scripts：

`pymada-info`, `pymada-get`, `pymada-disfil`, `pymada-real`, `pymada-imag`, `pymada-cmplx`, `pymada-rtoc`, `pymada-noise`, `pymada-ricker`, `pymada-spike`, `pymada-math`, `pymada-window`, `pymada-attr`, `pymada-put`, `pymada-dd`, `pymada-cat`, `pymada-transp`, `pymada-fft`, `pymada-bandpass`, `pymada-byte`, `pymada-smooth`, `pymada-boxsmooth`, `pymada-mask`, `pymada-cut`, `pymada-reverse`。

P0-03 audit note: docs currently mention only the registered `pymada-*` names above. All other CLI examples use `python -m pymadagascar.cli.<name>`.

Stage B-1 note: `cp`, `rm`, `min`, and `max` are module-only CLIs. They are not registered as console scripts in `pyproject.toml`; use `python -m`.

Stage B-2 note: `mul`, `div`, `tpow`, and `interleave` are module-only CLIs.
They are not registered as console scripts in `pyproject.toml`; use
`python -m pymadagascar.cli.<name>`.

Stage B-3-1 note: `headerwindow` and `headercut` are module-only CLIs. They
are Python mask/header RSF subsets and are not registered as console scripts.

Signal compatibility note: `fft`, `ifft`, `rfft`, `bandpass`, `lowpass`, and `highpass`
follow the NumPy-based subset documented in `docs/SIGNAL_COMPATIBILITY.md`.

## 命令清单

| CLI module | Madagascar style | Current invocation | Input | Output | Status | Minimal example |
| --- | --- | --- | --- | --- | --- | --- |
| `base` | n/a | internal helper only | n/a | n/a | internal | n/a |
| `acoustic2d` | modeling simplified prototype | `python -m pymadagascar.cli.acoustic2d` | velocity RSF | shot RSF | simplified prototype | `python -m pymadagascar.cli.acoustic2d vel.rsf out=shot.rsf nt=100 dt=0.001 sx=10 sz=10` |
| `add` | `sfadd` subset | `python -m pymadagascar.cli.add` | one or more RSF files | RSF | stable subset | `python -m pymadagascar.cli.add a.rsf b.rsf out=sum.rsf` |
| `agc` | AGC-style processing | `python -m pymadagascar.cli.agc` | real RSF gather | RSF | stable subset | `python -m pymadagascar.cli.agc gather.rsf out=agc.rsf rect1=5` |
| `attr` | `sfattr` subset | `pymada-attr` or `python -m pymadagascar.cli.attr` | RSF | text statistics | stable | `pymada-attr input.rsf` |
| `bandpass` | `sfbandpass` subset | `pymada-bandpass` or `python -m pymadagascar.cli.bandpass` | real RSF | filtered RSF | stable subset; see `docs/SIGNAL_COMPATIBILITY.md` | `pymada-bandpass input.rsf out=bp.rsf flo=5 fhi=40 axis=1` |
| `boxsmooth` | `sfboxsmooth` Python subset | `pymada-boxsmooth` or `python -m pymadagascar.cli.boxsmooth` | real RSF | smoothed RSF | stable subset | `pymada-boxsmooth input.rsf out=box.rsf rect1=3 rect2=5` |
| `byte` | byte scaling Python substitute | `pymada-byte` or `python -m pymadagascar.cli.byte` | real RSF | `native_int` RSF with levels 0..255 | stable subset | `pymada-byte input.rsf out=byte.rsf pclip=99` |
| `cat` | `sfcat` subset | `pymada-cat` or `python -m pymadagascar.cli.cat` | two or more RSF files | concatenated RSF | stable subset | `pymada-cat a.rsf b.rsf out=cat.rsf axis=2` |
| `clip` | `sfclip` subset | `python -m pymadagascar.cli.clip` | RSF | clipped RSF | stable subset | `python -m pymadagascar.cli.clip input.rsf out=clip.rsf clip=1` |
| `cmplx` | `sfcmplx` subset | `pymada-cmplx` or `python -m pymadagascar.cli.cmplx` | real RSF and imaginary RSF | complex RSF | stable subset | `pymada-cmplx real.rsf imag.rsf out=complex.rsf` |
| `conv` | convolution-style command | `python -m pymadagascar.cli.conv` | input RSF and filter RSF | RSF | stable subset | `python -m pymadagascar.cli.conv input.rsf filter.rsf out=conv.rsf mode=full` |
| `corr` | correlation-style command | `python -m pymadagascar.cli.corr` | input RSF and filter RSF | RSF | stable subset | `python -m pymadagascar.cli.corr input.rsf filter.rsf out=corr.rsf mode=full` |
| `cp` | `sfcp` safe file-level subset | `python -m pymadagascar.cli.cp` | RSF header + sidecar | copied RSF header + copied sidecar | stable subset | `python -m pymadagascar.cli.cp input.rsf out=copy.rsf overwrite=n` |
| `cut` | `sfcut` subset | `pymada-cut` or `python -m pymadagascar.cli.cut` | RSF | shape-preserving RSF with selected samples zeroed | stable subset | `pymada-cut input.rsf out=cut.rsf axis=1 f=10 n=20` |
| `dd` | `sfdd` subset | `pymada-dd` or `python -m pymadagascar.cli.dd` | RSF | converted/copied RSF | partial | `pymada-dd input.rsf out=double.rsf type=float64`; `pymada-dd input.rsf out=ascii.rsf form=ascii` |
| `disfil` | `sfdisfil` subset | `pymada-disfil` or `python -m pymadagascar.cli.disfil` | RSF | deterministic text values | stable subset | `pymada-disfil input.rsf max=20 precision=6 axis_format=flat` |
| `div` | `sfdiv`/`sfadd mode=div` subset | `python -m pymadagascar.cli.div` | RSF and RSF/scalar denominator | divided RSF | stable subset; default `zero_policy=raise` | `python -m pymadagascar.cli.div a.rsf b.rsf out=div.rsf`; `python -m pymadagascar.cli.div a.rsf out=div.rsf scalar=2` |
| `fft` | `sffft1`-style FFT | `pymada-fft` or `python -m pymadagascar.cli.fft` | RSF | complex RSF | stable subset; see `docs/SIGNAL_COMPATIBILITY.md` | `pymada-fft input.rsf out=fft.rsf axis=1` |
| `fk` | FK spectrum prototype | `python -m pymadagascar.cli.fk` | 2D RSF | complex FK RSF | prototype | `python -m pymadagascar.cli.fk gather.rsf out=fk.rsf` |
| `fkfilter` | `sfdipfilter`/FK filter subset | `python -m pymadagascar.cli.fkfilter` | 2D RSF | filtered RSF | prototype | `python -m pymadagascar.cli.fkfilter gather.rsf out=filtered.rsf vmin=1 vmax=5` |
| `gain` | `sfpow`/gain subset | `python -m pymadagascar.cli.gain` | real RSF | gained RSF | stable subset | `python -m pymadagascar.cli.gain input.rsf out=gain.rsf tpow=2` |
| `get` | `sfget` subset | `pymada-get` or `python -m pymadagascar.cli.get` | RSF | text header values | stable subset | `pymada-get input.rsf key=n1,n2,d1` |
| `graph` | `sfgraph` substitute | `python -m pymadagascar.cli.graph` | 1D RSF | PNG/PDF | partial plotting substitute | `python -m pymadagascar.cli.graph trace.rsf out=trace.png title=Trace` |
| `grey` | `sfgrey` substitute | `python -m pymadagascar.cli.grey` | 2D RSF | PNG/PDF | partial plotting substitute | `python -m pymadagascar.cli.grey panel.rsf out=panel.png title=Panel` |
| `headercut` | `sfheadercut` mask subset | `python -m pymadagascar.cli.headercut` | RSF and one-dimensional mask/header RSF | shape-preserving cut RSF | stable subset; not full header table clone | `python -m pymadagascar.cli.headercut data.rsf mask.rsf out=cut.rsf axis=2 cut_nonzero=y` |
| `headerwindow` | `sfheaderwindow` mask subset | `python -m pymadagascar.cli.headerwindow` | RSF and one-dimensional mask/header RSF | windowed RSF | stable subset; continuous masks only | `python -m pymadagascar.cli.headerwindow data.rsf mask.rsf out=win.rsf axis=2` |
| `highpass` | `sfbandpass`-style highpass | `python -m pymadagascar.cli.highpass` | real RSF | filtered RSF | stable subset | `python -m pymadagascar.cli.highpass input.rsf out=hp.rsf fcut=10 axis=1` |
| `ifft` | inverse FFT | `python -m pymadagascar.cli.ifft` | complex RSF | complex/real-like RSF | stable subset | `python -m pymadagascar.cli.ifft fft.rsf out=ifft.rsf axis=1` |
| `imag` | `sfimag` subset | `pymada-imag` or `python -m pymadagascar.cli.imag` | complex RSF | real-valued imaginary component RSF | stable subset | `pymada-imag complex.rsf out=imag.rsf` |
| `info` | `sfin` subset | `pymada-info` or `python -m pymadagascar.cli.info` | RSF | text metadata | stable | `pymada-info input.rsf` |
| `interleave` | `sfinterleave` subset | `python -m pymadagascar.cli.interleave` | two or more matching RSF files | interleaved RSF | stable subset | `python -m pymadagascar.cli.interleave a.rsf b.rsf out=interleave.rsf axis=1` |
| `iradon` | inverse Radon prototype | `python -m pymadagascar.cli.iradon` | Radon model RSF | data RSF | prototype | `python -m pymadagascar.cli.iradon model.rsf out=data.rsf` |
| `kirchhoff` | `sfkirchnew` simplified prototype | `python -m pymadagascar.cli.kirchhoff` | post-stack RSF | image RSF | simplified prototype | `python -m pymadagascar.cli.kirchhoff data.rsf out=image.rsf velocity=2000` |
| `lowpass` | `sfbandpass`-style lowpass | `python -m pymadagascar.cli.lowpass` | real RSF | filtered RSF | stable subset | `python -m pymadagascar.cli.lowpass input.rsf out=lp.rsf fcut=40 axis=1` |
| `mask` | `sfmask` subset | `pymada-mask` or `python -m pymadagascar.cli.mask` | real RSF | `native_int` 0/1 mask RSF | stable subset | `pymada-mask input.rsf out=mask.rsf min=0 max=1` |
| `math` | `sfmath` subset | `pymada-math` or `python -m pymadagascar.cli.math` | optional RSF or shape params | RSF | stable subset | `pymada-math n1=100 output="sin(x1)" out=math.rsf` |
| `max` | `sfmax` scalar/axis statistic subset | `python -m pymadagascar.cli.max` | real RSF | deterministic key=value text | stable subset; not full `sfstack` alias clone | `python -m pymadagascar.cli.max input.rsf axis=0 nan_policy=omit` |
| `min` | `sfmin` scalar/axis statistic subset | `python -m pymadagascar.cli.min` | real RSF | deterministic key=value text | stable subset; not full `sfstack` alias clone | `python -m pymadagascar.cli.min input.rsf axis=1` |
| `mul` | `sfmul`/`sfadd mode=mul` subset | `python -m pymadagascar.cli.mul` | RSF and RSF/scalar multiplier | multiplied RSF | stable subset | `python -m pymadagascar.cli.mul a.rsf b.rsf out=mul.rsf`; `python -m pymadagascar.cli.mul a.rsf out=mul.rsf scalar=2` |
| `mute` | mute-style gather processing | `python -m pymadagascar.cli.mute` | gather RSF | muted RSF | stable subset | `python -m pymadagascar.cli.mute gather.rsf out=mute.rsf t0=0.2 slope=0.5` |
| `nmo` | `sfnmo` subset | `python -m pymadagascar.cli.nmo` | gather RSF and velocity | corrected gather RSF | prototype | `python -m pymadagascar.cli.nmo gather.rsf velocity.rsf out=nmo.rsf` |
| `noise` | `sfnoise` subset | `pymada-noise` or `python -m pymadagascar.cli.noise` | optional RSF or shape params | noisy/generated RSF | stable subset | `pymada-noise n1=100 out=noise.rsf seed=1 std=0.1` |
| `ricker` | `sfricker`-related wavelet generator subset | `pymada-ricker` or `python -m pymadagascar.cli.ricker` | frequency/time params | 1D Ricker wavelet RSF | stable subset | `pymada-ricker out=wavelet.rsf f=25 dt=0.001 nt=256` |
| `normalize` | project-defined normalize | `python -m pymadagascar.cli.normalize` | RSF | normalized RSF | stable subset | `python -m pymadagascar.cli.normalize input.rsf out=norm.rsf` |
| `pad` | `sfpad` subset | `python -m pymadagascar.cli.pad` | RSF | padded RSF | stable subset | `python -m pymadagascar.cli.pad input.rsf out=pad.rsf beg1=2 end1=2` |
| `put` | `sfput` subset | `pymada-put` or `python -m pymadagascar.cli.put` | RSF | copied RSF with header updates | stable | `pymada-put input.rsf out=updated.rsf label1=Time unit1=s` |
| `radon` | `sfslant`/Radon prototype | `python -m pymadagascar.cli.radon` | gather RSF | Radon model RSF | prototype | `python -m pymadagascar.cli.radon gather.rsf out=radon.rsf` |
| `real` | `sfreal` subset | `pymada-real` or `python -m pymadagascar.cli.real` | complex RSF | real-valued real component RSF | stable subset | `pymada-real complex.rsf out=real.rsf` |
| `reshape` | reshape-style command | `python -m pymadagascar.cli.reshape` | RSF | reshaped RSF | stable subset | `python -m pymadagascar.cli.reshape input.rsf out=reshape.rsf n1=10 n2=10` |
| `reverse` | `sfreverse` subset | `pymada-reverse` or `python -m pymadagascar.cli.reverse` | RSF | reversed RSF | stable subset | `pymada-reverse input.rsf out=rev.rsf axis=1` |
| `rfft` | real FFT | `python -m pymadagascar.cli.rfft` | real RSF | complex RSF | stable subset; see `docs/SIGNAL_COMPATIBILITY.md` | `python -m pymadagascar.cli.rfft input.rsf out=rfft.rsf axis=1` |
| `rtoc` | `sfrtoc` subset | `pymada-rtoc` or `python -m pymadagascar.cli.rtoc` | real RSF | complex RSF with zero imaginary part | stable subset | `pymada-rtoc input.rsf out=complex.rsf` |
| `rm` | `sfrm` safe file-level subset | `python -m pymadagascar.cli.rm` | RSF header path(s) | text list of selected/removed files | stable subset; dry-run by default | `python -m pymadagascar.cli.rm input.rsf dry_run=y`; `python -m pymadagascar.cli.rm input.rsf confirm=y` |
| `scale` | `sfscale` subset | `python -m pymadagascar.cli.scale` | RSF | scaled RSF | stable subset | `python -m pymadagascar.cli.scale input.rsf out=scaled.rsf scale=2` |
| `segyread` | `sfsegyread` small subset | `python -m pymadagascar.cli.segyread` | small SEG-Y | RSF | 2D prototype | `python -m pymadagascar.cli.segyread input.sgy out=data.rsf` |
| `segywrite` | `sfsegywrite` small subset | `python -m pymadagascar.cli.segywrite` | RSF | small SEG-Y | 2D prototype | `python -m pymadagascar.cli.segywrite input.rsf out=data.sgy` |
| `semblance` | `sfvscan`-style semblance | `python -m pymadagascar.cli.semblance` | gather RSF | semblance RSF | prototype | `python -m pymadagascar.cli.semblance gather.rsf out=semblance.rsf vmin=1000 vmax=3000 nv=20` |
| `smooth` | `sfsmooth` Python subset | `pymada-smooth` or `python -m pymadagascar.cli.smooth` | real RSF | smoothed RSF | stable subset | `pymada-smooth input.rsf out=smooth.rsf rect1=3 rect2=5` |
| `spike` | `sfspike` subset | `pymada-spike` or `python -m pymadagascar.cli.spike` | shape params | RSF | stable subset | `pymada-spike n1=10 k1=5 out=spike.rsf` |
| `spray` | `sfspray` subset | `python -m pymadagascar.cli.spray` | RSF | sprayed RSF | stable subset | `python -m pymadagascar.cli.spray input.rsf out=spray.rsf axis=2 n=3` |
| `stack` | `sfstack` subset | `python -m pymadagascar.cli.stack` | RSF | stacked RSF | stable subset | `python -m pymadagascar.cli.stack gather.rsf out=stack.rsf axis=2` |
| `tile` | project-defined tile | `python -m pymadagascar.cli.tile` | RSF | tiled RSF | stable subset | `python -m pymadagascar.cli.tile input.rsf out=tile.rsf axis=2 n=3` |
| `transp` | `sftransp` subset | `pymada-transp` or `python -m pymadagascar.cli.transp` | RSF | transposed RSF | stable subset | `pymada-transp input.rsf out=transp.rsf order=2,1` |
| `tpow` | `sftpow` subset | `python -m pymadagascar.cli.tpow` | RSF | gained RSF | stable subset | `python -m pymadagascar.cli.tpow input.rsf out=tpow.rsf power=1.5 axis=1` |
| `wiggle` | `sfwiggle` substitute | `python -m pymadagascar.cli.wiggle` | 2D RSF | PNG/PDF | partial plotting substitute | `python -m pymadagascar.cli.wiggle gather.rsf out=wiggle.png` |
| `window` | `sfwindow` subset | `pymada-window` or `python -m pymadagascar.cli.window` | RSF | windowed RSF | stable subset | `pymada-window input.rsf out=win.rsf f1=5 n1=20` |
| `xcorr` | cross-correlation command | `python -m pymadagascar.cli.xcorr` | 2D trace RSF | correlation RSF | stable subset | `python -m pymadagascar.cli.xcorr traces.rsf out=xcorr.rsf axis=1 mode=full` |

## Stability Legend

- `stable`: suitable as a local workflow dependency inside the current project scope.
- `stable subset`: usable and tested for common behavior, but not a full Madagascar parameter clone.
- `partial`: core path works, but format or compatibility coverage is intentionally incomplete.
- `prototype`: useful for experiments and small fixtures; not an industrial or complete Madagascar replacement.
- `simplified prototype`: prototype that intentionally omits important original algorithm, physics, amplitude, or performance details.
- `2D prototype`: prototype limited to small 2D fixtures and not a full 3D/trace-header format implementation.
- `internal`: helper module, not a user-facing command.

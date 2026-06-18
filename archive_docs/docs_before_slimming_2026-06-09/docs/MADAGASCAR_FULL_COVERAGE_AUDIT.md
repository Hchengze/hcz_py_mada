# Madagascar Full Coverage Audit

Generated: 2026-06-09. This audit is based on the local `src-master/` tree and the current `hcz_mada/pymadagascar/` project files. It does not depend on old chat history.

## Methodology

- Original-command scan: local `src-master` `M*.c`, `M*.cc`, `M*.cpp`, `M*.f90`, and `M*.f` files, plus `system/` and `plot/` `SConstruct` `progs` lists and known aliases.
- Main-program scan: C/C++ `int main(...)` and Fortran `program ...` entries.
- Book-command scan: command tokens in `book/**/SConstruct`, `SConscript`, `.py`, `.sh`, and `.rsfproj`; this is heuristic and is not a precise build list.
- Current-project scan: `pymadagascar/cli`, `pymadagascar/**/*.py`, `tests/test_*.py`, `examples/**/*.py`, `docs/*.md`, and `cpp/`.
- Commands whose behavior cannot be reliably inferred from source comments remain marked `unknown`.
- `sfbyte` is not counted as a confirmed standalone original source program in this audit; the local source scan found related tools such as `Mbyte2rsf.c` and `Mswapbyte.c`, but not `byte.c`/`Mbyte.c`.

## A. Overview

| Item | Count / status | Notes |
| --- | ---: | --- |
| Original source files | 13372 | Full `src-master/` tree |
| C/C++/Fortran main/program files | 2425 | Scanned for `int main` or Fortran `program` |
| `M*` main-program candidate files | 2063 | Common `Mxxx` -> `sfxxx` naming rule |
| Source/SConstruct `sfxxx` command candidates | 2094 | Excludes aliases |
| `sfxxx` command candidates plus known aliases | 2114 | Full command-surface denominator |
| Core `system/` + `plot/main` command candidates | 301 | Includes known aliases |
| `user/` contributed command candidates | 1792 | Mostly research prototypes or author-specific tools |
| Python scripts in original tree | 439 | Framework/book/tests/scripts |
| Book files | 6020 | Papers, figures, SConstruct files, data, etc. |
| Heuristic command short names in book tree | 1062 | Not a precise build list |
| Current `pymadagascar` CLI modules | 67 | Excludes `base.py` and `__init__.py`; Stage B-3-1 added module-only `headerwindow/headercut` |
| Current public Python functions | 290 | Rough AST scan of top-level public `def`; excludes class methods |
| Current pytest files | 43 | `hcz_mada/tests/test_*.py` |
| Current examples | 26 | 21 top-level scripts + 5 `examples/my_workflows/*.py`; excludes workflow helper |
| Current docs | 21 + 1 batch plan + 1 design | 21 top-level `docs/*.md`, `docs/batch_plans/STAGE_B_SYSTEM_MAIN_PLAN.md`, and `docs/design/HEADER_METADATA_COMMANDS_DESIGN.md` |
| Current hybrid C++ files | 5 | `cpp/bindings.cpp`, `cpp/kernels/array_ops.cpp`, `array_ops.hpp`, `xcorr.cpp`, `xcorr.hpp` |
| Current command-surface mapped coverage | 56 | Stage B-3-1 added `sfheaderwindow` and `sfheadercut` as direct `system/main` mask subsets |
| Full command-surface coverage | 2.65% | 56 / 2114 |
| Core `system/` + `plot/main` command-surface coverage | 16.94% | 51 / 301 |

Coverage denominator note: `56 / 2114` is the conservative full-source-and-alias command-surface denominator and includes many `user/*` research programs. `51 / 301` is the core `system/` + `plot/main` command-surface denominator, closer to the current Python package target. This project is a local Python RSF/geophysics toolkit, not a complete clone of 2000+ Madagascar commands.

### Coverage By Core Source Group

| Source group | Original commands | Implemented matches | Coverage | Implemented examples |
| --- | ---: | ---: | ---: | --- |
| `system/main` | 39 | 27 | 69.23% | sfadd, sfattr, sfcat, sfcmplx, sfcp, sfcut, sfdd, sfdisfil, sfget, sfheadercut, sfheaderwindow, sfinterleave, sfin, sfmask, sfmath, sfpad, sfput, sfreal, sfreverse, sfrm, sfrtoc, sfscale, sfspike, sfspray, sfstack, sftransp, sfwindow |
| `system/generic` | 88 | 9 | 10.23% | sfagc, sfbandpass, sfboxsmooth, sfclip, sfdipfilter, sffft1, sfnoise, sfpow, sfsmooth |
| `system/seismic` | 158 | 7 | 4.43% | sfkirchnew, sfnmo, sfricker, sfsegyread, sfsegywrite, sfslant, sfvscan |
| `plot/main` | 16 | 3 | 18.75% | sfgraph, sfgrey, sfwiggle |
| `user/` | 1792 | 5 | 0.28% | sfconv, sfmute, sfreshape, sftpow, sfxcorr |

### Current Pure Python Coverage

Pure Python coverage is concentrated in RSF I/O, header/info utilities, basic array commands, FFT/filter/convolution, small SEG-Y fixtures, basic seismic processing, NMO/Semblance/FK/Radon prototypes, simplified Kirchhoff, simplified acoustic2d, and the high-level `RSFData` convenience API. Most covered commands have Python APIs, module CLIs, and pytest coverage, but many are intentionally stable subsets rather than full Madagascar clones.

### Current Hybrid Coverage

- `pymadagascar.hybrid.array_ops`: `add_arrays_cpp`, `scale_array_cpp`; NumPy fallback is required when C++ is unavailable.
- `pymadagascar.hybrid.xcorr`: `batch_xcorr_cpp(data, axis=-1, mode="full")`; NumPy fallback is required when C++ is unavailable.
- `cpp/`: `bindings.cpp`, `kernels/array_ops.*`, `kernels/xcorr.*`.
- Current environment has not compiled the C++ extension, so real speedup is not verified locally.

### Current Test Coverage

- Current test file count: 43.
- `tests/test_cp_rm_min_max.py` covers Stage B-1 API behavior, subprocess CLI behavior, and optional original-Madagascar comparisons for `sfcp/sfrm/sfmin/sfmax`.
- `tests/test_mul_div_tpow_interleave.py` covers Stage B-2 API behavior, subprocess CLI behavior, error policies, and optional original-Madagascar comparisons for `sfmul/sfdiv/sftpow/sfinterleave`.
- `tests/test_header_window_cut.py` covers Stage B-3-1 mask/header window/cut behavior, subprocess CLI behavior, and optional original-Madagascar comparisons for `sfheaderwindow/sfheadercut`.
- Pure Python tests do not require original Madagascar or C++.
- Optional original comparison tests skip when upstream `sf*` commands are unavailable.
- The latest full pytest status is recorded in `docs/TEST_STATUS.md`.

## B. Functional Coverage By Category

| Category | Original command candidates | Implemented matches | Implemented examples | Representative gaps | Suggested priority |
| --- | ---: | ---: | --- | --- | --- |
| RSF I/O and formats | 22 | 3 | sfdd, sfsegyread, sfsegywrite | sfsum, sfsuread, sfsuwrite, sfsuplane, sfotsu, sfdatasucjb2rsf2d, sfnhcrssurf, sfdatasucjb2rsf3d, sfdatasucjb2rsf3dnh, sfeikonal_surf, sfeikonal_surf_dv1d, sfpcrsurv3 | P0/P1 first |
| header/info/metadata | 13 | 7 | sfattr, sfdisfil, sfget, sfheadercut, sfheaderwindow, sfin, sfput | sfheadermath, sfheaderattr, sftahheadermath, sfheadersort, sfsegyheader, sffileheader, sfgenheaderallreceiver | P0/P1 first |
| generic array operations | 26 | 23 | sfadd, sfcat, sfclip, sfcmplx, sfcut, sfdiv, sfimag, sfinterleave, sfmask, sfmax, sfmin, sfmul, sfpad, sfpow, sfreal, sfreverse, sfrtoc, sfscale, sfspray, sfstack, sftpow, sftransp, sfwindow | remaining alias edge cases | P0/P1 first |
| math/expression and synthetic data | 10 | 4 | sfmath, sfnoise, sfricker, sfspike | sfricker1, sfsin, sfricker2, sflorenz, sfmandelbrot, sfrandrefl | P0/P1 first |
| FFT/spectral | 58 | 1 | sffft1 | sffft3, sfspectra, sfcosft, sffft2, sffftexp0, sffreqlet, sfspectra2, sffftwave2, sfcfftwave2, sffftexp3, sffft3d, sffftwave3p | P2/P3 or defer |
| filtering/smoothing | 56 | 4 | sfbandpass, sfdipfilter, sfsmooth, sfboxsmooth | sfthreshold1, sfthreshold, sfcostaper, sfdwt, sfpwsmooth, sfnsmooth1, sfsmoothder, sfcanny, sfsmooth2, sfthreshold2 | P0/P1 first |
| convolution/correlation | 29 | 2 | sfconv, sfxcorr | sfhelicon, sfconvolve, sfautocorr, sfconverted, sfenvcorr, sfconvolve2, sftdconvert, sfcorral, sfcconv, sfconvert0eq, sfhconv, sfwcorr | P2/P3 or defer |
| interpolation/resampling | 64 | 0 | - | sfbin, sfslice, sfspline, sfiwarp, sfintbin, sfremap1, sft2warp, sfstretch, sfwarp1, sflogstretch, sfdatstretch, sfnmostretch | P2/P3 or defer |
| seismic gather processing | 41 | 2 | sfagc, sfmute | sfmutter, sfenvelope, sfstacks, sffold, sfsnrstack, sfshot2cmp, sftahstack, sfshpwstack, sffinstack, sfsmstack, sfmshots, sfshstack | P2/P3 or defer |
| velocity/NMO/DMO/AVO | 69 | 2 | sfnmo, sfvscan | sfdmo, sfinmo, sfavo, sfovc, sftahnmo, sfvelcon, sfmoveout, sfpnmo, sfpsovc, sfvelinv, sfsimivscan, sfinmo3 | P2/P3 or defer |
| FK/Radon/velocity transform | 32 | 1 | sfslant | sfradon, sfhradon, sffkoclet, sfradon2, sfitaupmo, sfradon34, sfdiradon2, sfdiradon34, sfmyradon2, sfptaupmoVTI, sffkamo, sfptaupmo | P2/P3 or defer |
| migration/imaging | 75 | 1 | sfkirchnew | sfstolt, sfmig3, sfmig2, sfzomig, sfpipwdmig2, sfpreconstkirch, sfgazdag, sfzomig3, sflinmig3, sfkirmigsr, sflspiazpwdmig3, sfpmig | P2/P3 or defer |
| wave-equation modeling | 221 | 0 | - | sfwave, sffdip, sfawefd2d, sfkirmod, sfawefd, sfwave1, sfewefd, sfewefd2, sfewefd2d, sfhdefd, sfawefd3d, sfsglfdcp1 | P2/P3 or defer |
| inversion/optimization/operators | 46 | 0 | - | sfconjgrad, sffwiupdate, sfmpisfwi, sffwiobj, sffwidir, sfcconjgrad, sfmpifwigradlr, sfmpipfwi, sfdottest, sffwigrad, sffwipe, sfinvqfilt | P2/P3 or defer |
| plotting/visualization | 15 | 3 | sfgraph, sfgrey, sfwiggle | sfgrey3, sfbox, sfdots, sfcontour, sfcontour3, sfgrey4, sfbargraph, sfgraph3, sfthplot, sfplas, sfvplotdiff, sfpldb | P2/P3 or defer |
| user contributed programs | 1221 | 1 | sfreshape | sfmax2, sfplane, sfrect1, sfdip, sfproj, sfflat, sfpick, sflabel, sfzero, sfdistance, sfss, sfpoly | P2/P3 or defer |
| trip/IWAVE/RVL | 0 | 0 | - | - | P2/P3 or defer |
| other/unknown | 116 | 2 | sfcp, sfrm | sfmax1, sflinear, sfclip2, sfshifts, sfderiv, sfmatch, sfcausint, sfomp, sfvofz, sfdiffraction | P2/P3 or defer |

### Required Category Notes
- `RSF I/O`: RSF header/binary I/O exists in Python and is a stable dependency; full ASCII/XDR/form/streaming compatibility remains missing.
- `header/info/metadata`: `sfin/sfget/sfdisfil/sfattr/sfput` and B-3-1 `sfheaderwindow/sfheadercut` mask subsets are covered; `sfheaderattr`, `sfheadermath`, `sfheadersort`, and `sfsegyheader` remain high-value gaps.
- `generic array operations`: Basic add/mul/div/scale/clip/cat/interleave/window/transp/pad/spray/stack, mask/cut/reverse, tpow, min/max statistics, and complex split/combine/real-to-complex tools are covered; many `system/main` utility aliases and edge cases remain open.
- `math/expression`: `sfmath` safe subset, `sfspike`, `sfnoise` normal/uniform seeded subset, and a direct time-domain `sfricker`-related wavelet generator are covered; full Madagascar expression language, original random sequence identity, original `sfricker` spectrum estimation and `sfricker1/2` convolution are not covered.
- `window/cat/transpose/reshape`: Covered as in-memory operations; large streaming behavior is not covered.
- `type conversion`: `sfdd` is partial; XDR, ASCII and more dtype/form combinations remain P1/P2.
- `plotting/visualization`: `sfgrey/sfgraph/sfwiggle` have Matplotlib substitutes; VPlot/pens byte-level compatibility is intentionally not covered.
- `FFT/spectral`: `sffft1` family is covered by NumPy FFT subset; `sffft3`, `sfcosft`, spectra tools are open.
- `filtering`: `sfbandpass` subset and `sfdipfilter`/FK-filter prototype exist; many filters and exact parameter behavior remain open.
- `convolution/correlation`: Project has conv/corr/xcorr APIs; exact local original command mapping is partial, with C++ acceleration only for batch xcorr fallback wrapper.
- `interpolation`: Only limited internal interpolation is present; Madagascar ENO/spline/stretch/remap family is largely uncovered.
- `smoothing`: `sfsmooth` and `sfboxsmooth` now have stable Python subsets. `sfcsmooth` and `sfdsmooth` remain unimplemented and should wait for an explicit task.
- `seismic gather processing`: Gain/AGC/mute/stack are covered as clear prototypes; parameter compatibility remains limited.
- `velocity analysis`: `sfnmo/sfvscan` are prototypes; velocity transform and richer offset/header mechanics are still open.
- `NMO/DMO`: `sfnmo` is prototype; DMO/GDMO/FKDMO families are not covered.
- `stacking`: `sfstack` basic stack is covered; aliases and advanced stack/semblance flows are not covered.
- `FK/Radon`: `sfdipfilter` subset and `sfslant`/Radon prototype exist; velocity transform/Radon LS/complex FK filters remain open.
- `migration/imaging`: `sfkirchnew` has a simplified 2D prototype; Stolt/Gazdag/shot/prestack/wave-equation migration families are not covered.
- `wave-equation modeling`: `acoustic2d` is project-defined prototype, not a direct full Madagascar modeler; most wave equation tools remain open.
- `inversion/optimization`: Testing helpers cover comparisons; solver/conjgrad/dottest/inversion APIs are mostly not migrated.
- `linear operators`: No general Madagascar linear-operator framework is implemented beyond small algorithm-specific routines.
- `reproducible workflow/SCons`: Not implemented by design; Python package focuses on API/CLI rather than book/SCons reproduction.
- `book examples`: Book tree has thousands of files and over one thousand heuristic command short names; not suitable for wholesale migration.
- `tests and datasets`: Current project has deterministic small fixtures; no real SEG-Y or original Madagascar CI environment yet.
- `APIs for C/C++/Fortran/Python/Matlab/Octave`: Original tree has multi-language APIs; pymadagascar currently only targets Python with optional pybind11 C++ kernels.

### Book Command Hotspots Heuristic

| Command | Heuristic mentions | Implemented | Category |
| --- | ---: | --- | --- |
| `sfwindow` | 10161 | yes | generic array operations |
| `sfgrey` | 8245 | yes | plotting/visualization |
| `sfmath` | 6981 | yes | math/expression and synthetic data |
| `sftransp` | 5971 | yes | generic array operations |
| `sfin` | 4878 | yes | header/info/metadata |
| `sfput` | 4609 | yes | header/info/metadata |
| `sfscale` | 3356 | yes | generic array operations |
| `sfclip` | 3243 | yes | generic array operations |
| `sfmax1` | 3055 | no | other/unknown |
| `sfadd` | 3018 | yes | generic array operations |
| `sfmax2` | 2852 | no | user contributed programs |
| `sfgraph` | 2844 | yes | plotting/visualization |
| `sfcat` | 2379 | yes | generic array operations |
| `sfplane` | 2339 | no | user contributed programs |
| `sfrect1` | 2312 | no | user contributed programs |
| `sfmask` | 2286 | yes | generic array operations |
| `sfpad` | 2169 | yes | generic array operations |
| `sfdip` | 2075 | no | user contributed programs |
| `sfstack` | 1910 | yes | generic array operations |
| `sfdd` | 1906 | yes | RSF I/O and formats |
| `sfspike` | 1652 | yes | math/expression and synthetic data |
| `sfproj` | 1572 | no | user contributed programs |
| `sfgrey3` | 1496 | no | plotting/visualization |
| `sfreal` | 1334 | yes | generic array operations |
| `sfnoise` | 1331 | yes | math/expression and synthetic data |
| `sfflat` | 1318 | no | user contributed programs |
| `sfsmooth` | 1191 | yes | filtering/smoothing |
| `sfspray` | 1149 | yes | generic array operations |
| `sfnmo` | 1091 | yes | velocity/NMO/DMO/AVO |
| `sffft3` | 1015 | no | FFT/spectral |
| `sfpick` | 903 | no | user contributed programs |
| `sfbin` | 903 | no | interpolation/resampling |
| `sflabel` | 851 | no | user contributed programs |
| `sfzero` | 840 | no | user contributed programs |
| `sfdistance` | 834 | no | user contributed programs |
| `sfget` | 800 | yes | header/info/metadata |
| `sffft1` | 791 | yes | FFT/spectral |
| `sfslice` | 711 | no | interpolation/resampling |
| `sfwave` | 707 | no | wave-equation modeling |
| `sfss` | 694 | no | user contributed programs |

### Original API and Test Surface

| API language/group | Source files | Test files under API | Current pymadagascar equivalent |
| --- | ---: | ---: | --- |
| `c` | 141 | 3 | optional pybind11 kernels only |
| `python` | 20 | 9 | Python package API |
| `c++` | 17 | 10 | optional pybind11 kernels only |
| `java` | 13 | 2 | not targeted |
| `matlab` | 12 | 2 | not targeted |
| `f90` | 9 | 3 | not targeted |
| `f77` | 7 | 2 | not targeted |
| `julia` | 6 | 4 | not targeted |
| `chapel` | 5 | 3 | not targeted |
| `octave` | 4 | 0 | not targeted |

| Source test/data group | Files | Notes |
| --- | ---: | --- |
| `api` | 235 | scanned local source tree |
| `plot/test` | 31 | scanned local source tree |
| `pens/tests` | 69 | scanned local source tree |
| `trip/test` | 52 | scanned local source tree |
| `book` | 6020 | scanned local source tree |

## C. Full Original Command Matrix

Field notes: `Implemented` means the current `pymadagascar` tree has a mapped API,
CLI, and/or test entry for the command. It does not imply complete parameter
compatibility. `Original comparison` means pytest has an optional comparison hook
when upstream Madagascar is installed. `Pure Python`, `Hybrid C++`, and `Defer`
are migration recommendations, not current implementation status.

| Command | Source path | One-line function | Implemented | pymadagascar API | pymadagascar CLI | pytest | Original comparison | Priority | Difficulty | Pure Python | Hybrid C++ | Defer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sfdisfil | system/main/disfil.c | Print out data values. | yes | pymadagascar.generic.info.disfil_array/disfil_rsf | pymadagascar.cli.disfil | yes | yes | covered | done | yes | no | no |
| sfget | system/main/get.c | Output parameters from the header. | yes | pymadagascar.generic.info.get_header_value/get_header_values | pymadagascar.cli.get | yes | yes | covered | done | yes | no | no |
| sfsmooth | system/generic/Msmooth.c | Multi-dimensional triangle smoothing. | yes | pymadagascar.signal.smooth.triangle_smooth/smooth_rsf | pymadagascar.cli.smooth | yes | yes | covered | done | yes | optional later | no |
| sfbin | system/generic/Mbin.c | Data binning in 2-D slices. | no | - | - | no | no | P1 | medium | yes | optional later | no |
| sfboxsmooth | system/generic/Mboxsmooth.c | Multi-dimensional smoothing with boxes. | yes | pymadagascar.signal.smooth.box_smooth/smooth_rsf | pymadagascar.cli.boxsmooth | yes | no | covered | done | yes | optional later | no |
| sfcconjgrad | system/main/cconjgrad.c | Generic conjugate-gradient solver for linear inversion with complex data | no | - | - | no | no | P1 | low/medium | yes | no | no |
| sfcdottest | system/main/cdottest.c | Generic dot-product test for complex linear operators with adjoints | no | - | - | no | no | P1 | low/medium | yes | no | no |
| sfcmplx | system/main/cmplx.c | Create a complex dataset from its real and imaginary parts. | yes | pymadagascar.generic.complex_tools.cmplx_rsf | pymadagascar.cli.cmplx | yes | yes | covered | done | yes | no | no |
| sfconjgrad | system/main/conjgrad.c | Generic conjugate-gradient solver for linear inversion | no | - | - | no | no | P1 | low/medium | yes | no | no |
| sfcp | system/main/cp.c | Copy or move a dataset. | yes | `copy_rsf_dataset` | `python -m pymadagascar.cli.cp` | yes | yes | Done B-1 | low/medium | yes | no | no |
| sfcut | system/main/cut.c | Zero a portion of the dataset. | yes | pymadagascar.generic.cut.cut_rsf | pymadagascar.cli.cut | yes | yes | covered | done | yes | no | no |
| sfdottest | system/main/dottest.c | Generic dot-product test for linear operators with adjoints | no | - | - | no | no | P1 | low/medium | yes | no | no |
| sffft3 | system/generic/Mfft3.c | FFT transform on extra axis. | no | - | - | no | no | P1 | medium | yes | optional later | no |
| sfheaderattr | system/seismic/Mheaderattr.c | Display header attributes. | no | - | - | no | no | P1 | medium | yes | optional later | no |
| sfheadercut | system/main/headercut.c | Zero a portion of a dataset based on a header mask. | yes | pymadagascar.generic.header_mask.header_cut_rsf | pymadagascar.cli.headercut | yes | yes | Done B-3-1 | low/medium | yes | no | Python mask subset; no full header table |
| sfheadermath | system/seismic/Mheadermath.c | Mathematical operations, possibly on header keys. | no | - | - | no | no | P1 | medium | yes | optional later | no |
| sfheadersort | system/main/headersort.c | Sort a dataset according to a header key. | no | - | - | no | no | P1 | low/medium | yes | no | no |
| sfheaderwindow | system/main/headerwindow.c | Window a dataset based on a header mask. | yes | pymadagascar.generic.header_mask.header_window_rsf | pymadagascar.cli.headerwindow | yes | yes | Done B-3-1 | low/medium | yes | no | Python mask subset; continuous masks only |
| sfinterleave | system/main/interleave.c | Combine several datasets by interleaving. | yes | pymadagascar.generic.interleave.interleave_rsf | pymadagascar.cli.interleave | yes | yes | Done B-2 | low/medium | yes | no | subset requires same full shape |
| sflinear | system/generic/Mlinear.c | 1-D linear interpolation. | no | - | - | no | no | P1 | medium | yes | optional later | no |
| sfmask | system/main/mask.c | Create a mask. | yes | pymadagascar.generic.mask.mask_rsf | pymadagascar.cli.mask | yes | yes | covered | done | yes | no | no |
| sfmax1 | system/generic/Mmax1.c | Picking local maxima on the first axis. | no | - | - | no | no | P1 | medium | yes | optional later | no |
| sfmutter | system/generic/Mmutter.c | Muting. | no | - | - | no | no | P1 | medium | yes | optional later | no |
| sfnoise | system/generic/Mnoise.c | Add random noise to the data. | yes | pymadagascar.generic.noise.noise/add_noise/noise_rsf | pymadagascar.cli.noise | yes | yes | covered | done | yes | no | no |
| sfomp | system/main/omp.c | OpenMP wrapper for embarassingly parallel jobs. | no | - | - | no | no | P1 | low/medium | yes | no | no |
| sfreal | system/main/real.c | Extract real (sfreal) or imaginary (sfimag) part of a complex dataset. | yes | pymadagascar.generic.complex_tools.real_rsf/imag_rsf | pymadagascar.cli.real/pymadagascar.cli.imag | yes | yes | covered | done | yes | no | no |
| sfreverse | system/main/reverse.c | Reverse one or more axes in the data hypercube. | yes | pymadagascar.generic.reverse.reverse_rsf | pymadagascar.cli.reverse | yes | yes | covered | done | yes | no | no |
| sfricker | system/seismic/Mricker.c | Ricker wavelet estimation. | yes (direct generator subset) | pymadagascar.signal.wavelet.ricker_wavelet/ricker_rsf | pymadagascar.cli.ricker | yes | partial related `sfricker1` smoke | covered | done | yes | no | no |
| sfrm | system/main/rm.c | Remove RSF files together with their data. | yes | `remove_rsf_dataset` | `python -m pymadagascar.cli.rm` | yes | yes | Done B-1 | low/medium | yes | no | no |
| sfrotate | system/main/rotate.c | Rotate a portion of one or more axes in the data hypercube. | no | - | - | no | no | P1 | low/medium | yes | no | no |
| sfrtoc | system/main/rtoc.c | Convert real data to complex (by adding zero imaginary part). | yes | pymadagascar.generic.complex_tools.rtoc_rsf | pymadagascar.cli.rtoc | yes | yes | covered | done | yes | no | no |
| sfsegyheader | system/seismic/Msegyheader.c | Make a trace header file for segywrite. | no | - | - | no | no | P1 | medium | yes | optional later | no |
| sfslice | system/generic/Mslice.c | Extract a slice using picked surface (usually from a stack or a semblance). | no | - | - | no | no | P1 | medium | yes | optional later | no |
| sfspectra | system/generic/Mspectra.c (+1) | Frequency spectra. | no | - | - | no | no | P1 | medium | yes | optional later | no |
| sfspline | system/generic/Mspline.c | 1-D cubic spline interpolation. | no | - | - | no | no | P1 | medium | yes | optional later | no |
| sfaastack | system/seismic/Maastack.c | Stack with antialiasing | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfagmig | system/seismic/Magmig.c | Angle-gather constant-velocity time migration. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfai2refl | system/seismic/Mai2refl.c | Convert acoustic impedance to reflectivity. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfaliasp | system/generic/Maliasp.c | Aliasing test. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfanovc | system/seismic/Manovc.c | Oriented anisotropy continuation: shifted hyperbola travel-time approximation. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfanovcv | system/seismic/Manovcv.c | Oriented anisotropy continuation: shifted hyperbola travel-time approximation. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfavo | system/seismic/Mavo.c | Compute intercept and gradient by least squares. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfbeamspray | system/seismic/Mbeamspray.c | 2-D beam spraying. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfbin1 | system/generic/Mbin1.c | Data binning in 1-D slices. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfburg | system/generic/Mburg.c | Burg's method for 1-D PEF estimation | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfc2r | system/seismic/Mc2r.c | Cartesian-Coordinates to Riemannian-Coordinates interpolation | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfcanny | system/generic/Mcanny.c | Canny-like edge detector. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfcascade | system/seismic/Mcascade.c | Velocity partitioning for cascaded migrations. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfcausint | system/generic/Mcausint.c | Causal integration on the first axis. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfcell2 | system/seismic/Mcell2.c | Second-order cell ray tracing with locally parabolic rays. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfcell3 | system/seismic/Mcell3.c | Second-order cell ray tracing with locally parabolic rays in 3-D. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfcgscan | system/seismic/Mcgscan.c | Hyperbolic Radon transform with conjugate-directions inversion | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfclip2 | system/generic/Mclip2.c | One- or two-sided data clipping. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfcmatmult | system/generic/Mcmatmult.c | Simple matrix multiplication for complex matrices | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfcmatmult2 | system/generic/Mcmatmult2.c | Multiplication of two complex matrices | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfcmp2shot | system/seismic/Mcmp2shot.c | Convert CMPs to shots for regular 2-D geometry. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfconstfdmig2 | system/seismic/Mconstfdmig2.c | 2-D implicit finite-difference migration in constant velocity. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfcos2ang | system/seismic/Mcos2ang.c | Inverse cos to angle transformation | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfcosft | system/generic/Mcosft.c | Multi-dimensional cosine transform. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfcostaper | system/generic/Mcostaper.c | Cosine taper around the borders (N-D). | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfcsmooth | system/generic/Mcsmooth.c | Multi-dimensional triangle smoothing for complex data. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfdepth2time | system/seismic/Mdepth2time.c | Conversion from depth to time in a V(z) medium. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfderiv | system/generic/Mderiv.c | First derivative with a maximally linear FIR differentiator. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfdiffoc | system/seismic/Mdiffoc.c | Diffraction focusing test. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfdiffraction | system/seismic/Mdiffraction.c | Generate diffractions in zero-offset data. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfdimag | system/seismic/Mdimag.c | Diffraction imaging in the plane-wave domain. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfdmo | system/seismic/Mdmo.c | Kirchhoff DMO with antialiasing by reparameterization. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfdsmooth | system/generic/Mdsmooth.c | Multi-dimensional triangle smoothing - derivative. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfdsr | system/seismic/Mdsr.c | Prestack 2-D VTI v(z) modeling/migration by DSR with angle gathers. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfdsr2 | system/seismic/Mdsr2.c (+1) | 2-D prestack modeling/migration with split-step DSR. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfdwt | system/generic/Mdwt.c | 1-D digital wavelet transform | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfenoint2 | system/generic/Menoint2.c (+1) | ENO interpolation in 2-D slices. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfenvelope | system/seismic/Menvelope.c | Compute data envelope or phase rotation. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfequal | system/generic/Mequal.c | Image enhancement by histogram equalization. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfexpl1 | system/generic/Mexpl1.c | 1-D anisotropic diffusion by explicit cascade. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfexpl2 | system/generic/Mexpl2.c | 2-D anisotropic diffusion by box cascade. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfextract | system/generic/Mextract.c | Forward interpolation in 2-D slices. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sffern | system/generic/Mfern.c | Generate fractal fern. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sffincon | system/seismic/Mfincon.c | Offset continuation by finite differences | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sffindmo | system/seismic/Mfindmo.c | DMO without stacking by finite-difference offset continuation. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sffinstack | system/seismic/Mfinstack.c | DMO and stack by finite-difference offset continuation. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sffkamo | system/seismic/Mfkamo.c | Computes Azimuth Move-Out (AMO) operator in the f-k log-stretch domain | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sffkdmo | system/seismic/Mfkdmo.c | Offset continuation by log-stretch F-K operator. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sffkgdmo | system/seismic/Mfkgdmo.c | FK-domain Gardner's DMO for regularly sampled 2-D data | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sffold | system/seismic/Mfold.c | Make a seismic foldplot/stacking chart. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sffourvc | system/seismic/Mfourvc.c | Prestack velocity continuation. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sffourvc0 | system/seismic/Mfourvc0.c | Velocity continuation after NMO. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sffourvc2 | system/seismic/Mfourvc2.c | Velocity continuation with semblance computation. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sffowler | system/seismic/Mfowler.c | 2-D velocity-domain imaging (Fowler DMO + Stolt migration). | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sffowler1 | system/seismic/Mfowler1.c | 2-D velocity-domain DMO (Fowler DMO). | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sffowler2 | system/seismic/Mfowler2.c | 2-D ensemble of Stolt migrations. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sffreqint | system/seismic/Mfreqint.c | 1-D data regularization using freqlet transform | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sffreqlet | system/seismic/Mfreqlet.c | 1-D seislet frame | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfgazdag | system/seismic/Mgazdag.c | Post-stack 2-D/3-D v(z) time modeling/migration with Gazdag phase-shift. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfgdmo | system/seismic/Mgdmo.c | Gardner's DMO for regularly sampled 2-D data (slow method) | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfgrad2 | system/generic/Mgrad2.c | 2-D smooth gradient. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfgrad3 | system/generic/Mgrad3.c | 3-D smooth gradient. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfhalfint | system/seismic/Mhalfint.c | Half-order integration or differentiation. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfheat | system/generic/Mheat.c | Finite-difference solution of 2-D heat-flow equation | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfhistogram | system/generic/Mhistogram.c | Compute a histogram of integer- or float-valued input data. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfhwt2d | system/seismic/Mhwt2d.c | 2-D Huygens wavefront tracing traveltimes | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfhwtex | system/seismic/Mhwtex.c | Huygens wavefront tracing traveltimes | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfigrad | system/generic/Migrad.c | Gradient on the first axis. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfimpl1 | system/generic/Mimpl1.c | 1-D anisotropic diffusion. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfimpl2 | system/generic/Mimpl2.c | 2-D anisotropic diffusion. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfimpl3 | system/generic/Mimpl3.c | 3-D anisotropic diffusion. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfinfill | system/seismic/Minfill.c | Shot interpolation. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfinmo | system/seismic/Minmo.c | Inverse normal moveout. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfinmo3 | system/seismic/Minmo3.c | 3-D Inverse normal moveout. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfinmo3gma | system/seismic/Minmo3gma.c | 3-D Inverse generalized normal moveout. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfintbin | system/seismic/Mintbin.c | Data binning by trace sorting. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfintbin3 | system/seismic/Mintbin3.c | 4-D data binning. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfintshow | system/generic/Mintshow.c | Output interpolation filter. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfinttest1 | system/generic/Minttest1.c | Interpolation from a regular grid in 1-D. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfinttest2 | system/generic/Minttest2.c | Interpolation from a regular grid in 2-D. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfinttest3 | system/generic/Minttest3.c | Interpolation from a regular grid in 3-D. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfisin2ang | system/seismic/Misin2ang.c | inverse sin to angle transformation | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfitaupmo | system/seismic/Mitaupmo.c | Inverse normal moveout in tau-p domain. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfitaupmo2 | system/seismic/Mitaupmo2.c | Inverse normal moveout in tau-p-x domain. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfitaupmo3 | system/seismic/Mitaupmo3.c | 3-D Inverse taup normal moveout. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfitxmo | system/seismic/Mitxmo.c | Forward and inverse normal moveout with interval velocity. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfitxmo3 | system/seismic/Mitxmo3.c | Forward and inverse normal moveout with interval velocity. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfiwarp | system/generic/Miwarp.c | Inverse 1-D warping. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfiwarp2 | system/seismic/Miwarp2.c | Inverse 2-D warping | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfiwarp3 | system/seismic/Miwarp3.c | Inverse 3-D warping | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfjacobi | system/generic/Mjacobi.c | Find eigenvalues of a symmetric matrix by Jacobi's iteration. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfjacobi2 | system/generic/Mjacobi2.c | Find eigenvalues of a general complex matrix by Jacobi-like iteration. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfkirchinv | system/seismic/Mkirchinv.c | Kirchhoff 2-D post-stack least-squares time migration with antialiasing. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfkirmod | system/seismic/Mkirmod.c | Kirchhoff 2-D/2.5-D modeling with analytical Green's functions. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfkirmod3 | system/seismic/Mkirmod3.c | Kirchhoff 3-D modeling with analytical Green's functions. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sflapfill | system/generic/Mlapfill.c | Missing data interpolation in 2-D by Laplacian regularization. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sflaplac | system/generic/Mlaplac.c | 2-D finite-difference Laplacian operation. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sflaplac3d | system/generic/Mlaplac3d.c | 3-D finite-difference Laplacian operation. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sflinefit | system/generic/Mlinefit.c | Fit a line to a set of points in 2-D. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sflineiko | system/seismic/Mlineiko.c | Iterative solution of the linearized eikonal equation. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sflinsincos | system/seismic/Mlinsincos.c (+1) | Solve for angle in equation vx*sin(d) + vy*cos(d) = 1/s0. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sflogwarp | system/generic/Mlogwarp.c | Log warping. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sflorenz | system/generic/Mlorenz.c | Generate Lorenz attractor. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sflpad | system/generic/Mlpad.c | Pad and interleave traces. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfmandelbrot | system/generic/Mmandelbrot.c | Generate Mandelbrot set. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfmap2coh | system/seismic/Mmap2coh.c | From parameter's attribute map (veltran) to coherency-like plots. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfmatch | system/generic/Mmatch.c | Simple matching filtering | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfmatmult | system/generic/Mmatmult.c | Simple matrix multiplication | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfmigsteep3 | system/seismic/Mmigsteep3.c | 3-D Kirchhoff time migration for antialiased steep dips. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfmiss2 | system/generic/Mmiss2.c | 2-D missing data interpolation. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfmodrefl | system/seismic/Mmodrefl.c | Normal reflectivity modeling. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfmodrefl2 | system/seismic/Mmodrefl2.c | Normal reflectivity modeling. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfmodrefl3 | system/seismic/Mmodrefl3.c | Normal reflectivity modeling. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfmonof | system/generic/Mmonof.c | Mono-frequency wavelet estimation. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfmonof2 | system/generic/Mmonof2.c | Gaussian wavelet estimation in 2-D. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfmoveout | system/seismic/Mmoveout.c | Put spikes at an arbitrary moveout | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfnmo3 | system/seismic/Mnmo3.c | 3-D Normal moveout. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfnmo3_ort | system/seismic/Mnmo3_ort.c | 3-D Normal moveout using orthogonal parametrization | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfnmo3gma_adj | system/seismic/Mnmo3gma_adj.c | Fwd-Adj of 3D NMO GMA for iterative LS coefficient solve | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfnmodips | system/seismic/Mnmodips.c | Slopes for constant-velocity normal moveout. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfnmov | system/seismic/Mnmov.c | Least-squares fitting of t^2-t_0^2 surfaces for isotropic V_{nmo}. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfnmow | system/seismic/Mnmow.c | Least-squares fitting of t^2-t_0^2 surfaces for elliptical slowness matrix, W. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfnmow_adj | system/seismic/Mnmow_adj.c | Adjoint flag | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfotsu | system/generic/Motsu.c | Compute a threshold value from histogram using Otsu's algorithm. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfovc | system/seismic/Movc.c | Oriented velocity continuation. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfovcco | system/seismic/Movcco.c | Prestack (common-offset) 2-D oriented velocity continuation. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfovczo | system/seismic/Movczo.c | Post-stack 2-D oriented velocity continuation. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfoway1 | system/seismic/Moway1.c | Oriented one-way wave equation. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfpmig | system/seismic/Mpmig.c | Slope-based prestack time migration. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfpnmo | system/seismic/Mpnmo.c | Slope-based normal moveout. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfpnmo3d | system/seismic/Mpnmo3d.c | Slope-based normal moveout for 3-D CMP geometry. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfpolymask | system/generic/Mpolymask.c | Mask a polygon. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfpostfilter2 | system/generic/Mpostfilter2.c | Convert B-spline coefficients to data in 2-D. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfpp2psang | system/seismic/Mpp2psang.c | Transform PP angle gathers to PS angle gathers. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfpp2psang2 | system/seismic/Mpp2psang2.c | Transform PP angle gathers to PS angle gathers. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfpp2pstsic | system/seismic/Mpp2pstsic.c | Compute angle gathers for time-shift imaging condition | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfpreconstkirch | system/seismic/Mpreconstkirch.c | Prestack Kirchhoff modeling/migration in constant velocity. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfprestolt | system/seismic/Mprestolt.c | Prestack Stolt modeling/migration. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfptaupmo | system/seismic/Mptaupmo.c | Slope-based tau-p moveout. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfptaupmo3 | system/seismic/Mptaupmo3.c | Slope-based tau-p 3D moveout. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfptaupmoVTI | system/seismic/MptaupmoVTI.c | Slope-based tau-p moveout in VTI. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfpveltran | system/seismic/Mpveltran.c | Slope-based velocity transform. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfpveltran3 | system/seismic/Mpveltran3.c | Slope-based tau-p 3D velocity transform for elliptical anisotropy. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfpveltranVTI | system/seismic/MpveltranVTI.c | Slope-based tau-p velocity transform for VTI media. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfpyramid | system/seismic/Mpyramid.c | Pyramid transform | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfradial | system/seismic/Mradial.c | Radial transform. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfradial2 | system/seismic/Mradial2.c | Another version of radial transform. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfradon | system/seismic/Mradon.c | High-resolution Radon transform. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfrandrefl | system/seismic/Mrandrefl.c | Simple synthetics with random reflectivity. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfrays2 | system/seismic/Mrays2.c | Ray tracing by a Runge-Kutta integrator. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfrays2a | system/seismic/Mrays2a.c | Ray tracing in VTI media by a Runge-Kutta integrator. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfrays3 | system/seismic/Mrays3.c | Ray tracing by a Runge-Kutta integrator in 3-D. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfrefer | system/seismic/Mrefer.c | Subtract a reference from a grid. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfrefl2ai | system/seismic/Mrefl2ai.c | Convert reflectivity to acoustic impedance. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfreg2tri | system/generic/Mreg2tri.c | Decimate a regular grid to triplets for triangulation. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfremap1 | system/generic/Mremap1.c | 1-D ENO interpolation. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfricker1 | system/seismic/Mricker1.c | Convolution with a Ricker wavelet. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfricker2 | system/seismic/Mricker2.c | Nonstationary convolution with a Ricker wavelet. Phase and Frequency can be time-varying. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfroots | system/generic/Mroots.c | Find roots of a complex polynomial. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfrweab | system/seismic/Mrweab.c | Riemannian Wavefield Extrapolation: a,b coefficients | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfrwesrmig | system/seismic/Mrwesrmig.c | Riemannian Wavefield Extrapolation: shot-record migration. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfrwezomig | system/seismic/Mrwezomig.c | Riemannian Wavefield Extrapolation: zero-offset modeling/migration | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfs2ofz | system/seismic/Ms2ofz.c | Analytical point-source traveltime in a linear slowness squared model. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfs2ofz2 | system/seismic/Ms2ofz2.c | Analytical plane-wave traveltime in a linear slowness squared model. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfshapebin | system/generic/Mshapebin.c | Data binning in 2-D slices by inverse interpolation. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfshapebin1 | system/generic/Mshapebin1.c | 1-D inverse interpolation with shaping regularization. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfsharpen | system/generic/Msharpen.c | Sharpening operator | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfshifts | system/seismic/Mshifts.c | Multiple shifts. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfshoot2 | system/seismic/Mshoot2.c | 2-D ray shooting. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfshot2cmp | system/seismic/Mshot2cmp.c | Convert shots to CMPs for regular 2-D geometry. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfshotconstkirch | system/seismic/Mshotconstkirch.c | Prestack shot-profile Kirchhoff migration in constant velocity. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfshotholes | system/seismic/Mshotholes.c | Remove random shot gathers from a 2-D dataset. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfshotprop | system/seismic/Mshotprop.c | Shot propagation. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfsimivscan | system/seismic/Msimivscan.c | Velocity analysis using similarity-weighted semblance. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfsin | system/seismic/Msin.c | Simple operations with complex sinusoids | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfsmoothder | system/generic/Msmoothder.c | Smooth first derivative on the first axis. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfsmoothreg2 | system/generic/Msmoothreg2.c | Smoothing in 2-D by simple regularization. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfspectra2 | system/generic/Mspectra2.c | Frequency spectra in 2-D. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfsplinefilter | system/generic/Msplinefilter.c | Convert data to B-spline coefficients. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfsrmva | system/seismic/Msrmva.c | 3-D S/R WEMVA with extended split-step | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfsrseidel | system/seismic/Msrseidel.c | Amplitude balancing of a 2-D amplitude map. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfsrsyn | system/seismic/Msrsyn.c | Synthesize shot/receiver wavefields for 3-D SR migration | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfsstep2 | system/seismic/Msstep2.c | 3-D post-stack modeling/migration with extended split step. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfstacks | system/seismic/Mstacks.c | Constant-velocity stacks. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfstolt | system/seismic/Mstolt.c | Post-stack Stolt modeling/migration. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfstolt2 | system/seismic/Mstolt2.c | Post-stack Stolt modeling/migration. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfstoltstretch | system/seismic/Mstoltstretch.c | Stolt stretch. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfstretch | system/seismic/Mstretch.c | Stretch of the time axis. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfstripes | system/seismic/Mstripes.c | Model the positions and dips of the constant offset, source, midpoint, and receiver strikes in a source vs. offset space. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfswtdenoise | system/generic/Mswtdenoise.c | Denoising using stationary wavelet transform. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sft2warp | system/generic/Mt2warp.c | Time-squared warping. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sftan2ang | system/seismic/Mtan2ang.c | tangent to angle transformation | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sftaupmo | system/seismic/Mtaupmo.c | Normal moveout in tau-p domain. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sftclip | system/generic/Mtclip.c | Clip to threshold. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfthreshold | system/generic/Mthreshold.c | Soft thresholding. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sftime2depth | system/seismic/Mtime2depth.c | Time-to-depth conversion in V(z). | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sftlagtoang2d | system/seismic/Mtlagtoang2d.c | SS(t-lag) to angle transformation (PP or PS waves) | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sftrapez | system/generic/Mtrapez.c | Convolution with a trapezoidal filter. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sftri2reg | system/generic/Mtri2reg.c | Interpolate triangulated triplets to a regular grid. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sftrirand | system/generic/Mtrirand.c | Edit points for triangulation by removing similar and randomizing. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sftrishape | system/generic/Mtrishape.c | 2-D irregular data interpolation using triangulation and shaping regularization. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sftshift | system/seismic/Mtshift.c | Compute angle gathers for time-shift imaging condition | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sftxpnmo | system/seismic/Mtxpnmo.c | Normal moveout in TXP domain. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sftxpscan | system/seismic/Mtxpscan.c | Velocity analysis using T-X-P domain. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfunif2 | system/generic/Munif2.c | Generate 2-D layered velocity model from specified interfaces. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfunif3 | system/generic/Munif3.c | Generate 3-D layered velocity model from specified interfaces. | no | - | - | no | no | P2 | medium | yes | optional later | no |
| sfvczo | system/seismic/Mvczo.c | Post-stack 2-D velocity continuation. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfvczo2 | system/seismic/Mvczo2.c | Post-stack 2-D velocity continuation in the time-stretch frequency domain. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfvczo3 | system/seismic/Mvczo3.c | Post-stack 3-D velocity continuation. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfvelmod | system/seismic/Mvelmod.c | Velocity transform. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfveltran | system/seismic/Mveltran.c | Hyperbolic Radon transform | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfvoft | system/seismic/Mvoft.c | V(t) function for a linear V(Z) profile. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfvofz | system/seismic/Mvofz.c | Analytical traveltime in a linear V(z) model. | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfvscancrs | system/seismic/Mvscancrs.c | Velocity analysis. | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfxlagtoang2d | system/seismic/Mxlagtoang2d.c | SS(x-lag) to angle transformation (PP or PS waves) | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfzoeppritz | system/seismic/Mzoeppritz.c | Testing Zoeppritz equation | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfzoeppritz2 | system/seismic/Mzoeppritz2.c | Generate angle gathers using the Zoeppritz equation | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfzomig | system/seismic/Mzomig.c | 3-D zero-offset modeling/migration with extended split-step | no | - | - | no | no | P2 | high | partial/prototype first | yes after baseline | no |
| sfzomva | system/seismic/Mzomva.c | 3-D zero-offset WEMVA | no | - | - | no | no | P2 | medium/high | yes for baseline | optional | no |
| sfangle | user/fomels/Mangle.c | Illustration of angle gathers. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfbargraph | plot/main/bargraph.c | Bar plot. | no | - | - | no | no | P3 | medium | yes as matplotlib substitute | no | partial |
| sfbox | plot/main/box.c | Draw a balloon-style label. | no | - | - | no | no | P3 | medium | yes as matplotlib substitute | no | partial |
| sfcabs | user/chenyk/Mcabs.c | Absolute value complex data. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfcomp | user/chen/Mcomp.c | Compare 2 data set | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfcontour | plot/main/contour.c | Contour plot. | no | - | - | no | no | P3 | medium | yes as matplotlib substitute | no | partial |
| sfcontour3 | plot/main/contour3.c | Generate 3-D contour plot. | no | - | - | no | no | P3 | medium | yes as matplotlib substitute | no | partial |
| sfcreate | user/ivlad/Mcreate.c | Creates just the ascii header from parameters | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfcube | user/gee/Mcube.c | Simple cube fault synthetic | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfdecon | user/gee/Mdecon.c | Deconvolution (N-dimensional). | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfdensity | user/jyan/Mdensity.c | Compute density | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfdiff | user/chenyk/Mdiff.c | Compare the difference of two rsf data sets with the same size. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfdifference | user/yliu/Mdifference.c | Difference profile of two data | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfdip | user/pwd/Mdip.c | 3-D dip estimation by plane wave destruction. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfdip2 | user/nobody/Mdip2.c (+1) | 2-D dip estimation by plane wave destruction. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfdips | user/pwd/Mdips.c | Estimate a number of constant dips using plane-wave destruction. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfdistance | user/fomels/Mdistance.c | Computing distance function by fast marching eikonal solver (3-D). | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfdix | user/fomels/Mdix.c | Convert RMS to interval velocity using LS and shaping regularization. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfdots | plot/main/dots.c | Plot signal with lollipops. | no | - | - | no | no | P3 | medium | yes as matplotlib substitute | no | partial |
| sfemd | user/chenyk/Memd.c | Empirical Mode Decomposition | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfflat | user/nobody/Mflat.c | Moveout flattening. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfframe | user/gee/Mframe.c | Create a frame for binning. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sffxdecon | user/chenyk/Mfxdecon.c | Random noise attenuation using f-x deconvolution | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfgradient | user/llisiw/Mgradient.c | Linearized complex eikonal equation | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfgraph3 | plot/main/graph3.c | Generate 3-D cube plot for surfaces. | no | - | - | no | no | P3 | medium | yes as matplotlib substitute | no | partial |
| sfgrey3 | plot/main/grey3.c | Generate 3-D cube plot. | no | - | - | no | no | P3 | medium | yes as matplotlib substitute | no | partial |
| sfgrey4 | plot/main/grey4.c | Generate movie of 3-D cube plots. | no | - | - | no | no | P3 | medium | yes as matplotlib substitute | no | partial |
| sfhelicon | user/gee/Mhelicon.c | Multidimensional convolution and deconvolution by helix transform. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfhole | user/gee/Mhole.c | Cut an elliptic hole in data (for interpolation tests). | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfhorizon | user/chen/Mhorizon.c | horizon extraction | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfic | user/psava/Mic.c | Imaging condition | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfinitial | user/yliu/Minitial.c | Initialize a data | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sflabel | user/fomels/Mlabel.c | Connected-component labeling | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sflayer | user/nobody/Mlayer.c | Ray tracing in a layered medium. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sflegacy | user/fomels/Mlegacy.c | Merging legacy and hires datasets | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sflow | user/chenyk/Mlow.c | Calculating local (signal-and-noise) orthogonalization weight (LOW) | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfltft | user/yliu/Mltft.c | Local time-frequency transform (LTFT). | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfmake | user/gee/Mmake.c | Simple 2-D synthetics with crossing plane waves. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfmax2 | user/fomels/Mmax2.c | Picking local maxima in 2-D | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfmean | user/yliu/Mmean.c | 1-D sliding-window mean filtering | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfmf | user/yliu/Mmf.c | 1D median filtering. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfmig3 | user/fomels/Mmig3.c | 3-D Kirchhoff time migration with antialiasing. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfnorm | user/chenyk/Mnorm.c | Normalize the data. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfortho | user/fomels/Mortho.c | Orthogonolize signal and noise. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfpatch | user/fomels/Mpatch.c | Patching (N-dimensional). | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfpick | user/fomels/Mpick.c | Automatic picking from semblance-like panels. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfplane | user/fomels/Mplane.c | Generating plane waves with steering filters. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfplas | plot/main/plas.c | Plot Assembler - convert ascii to vplot. | no | - | - | no | no | P3 | medium | yes as matplotlib substitute | no | partial |
| sfpldb | plot/main/pldb.c | Plot Debugger - convert vplot to ascii. | no | - | - | no | no | P3 | medium | yes as matplotlib substitute | no | partial |
| sfplotrays | plot/main/plotrays.c | Plot rays. | no | - | - | no | no | P3 | medium | yes as matplotlib substitute | no | partial |
| sfpocs | user/pyang/Mpocs.c | n-D POCS interpolation using a hard thresholding | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfpoly | user/fomels/Mpoly.c | From roots to polynomials | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfproj | user/gee/Mproj.c | Projection filter. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfpwd | user/pwd/Mpwd.c | 3-D plane wave destruction. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfqdome | user/gee/Mqdome.c | 3-D synthetic image from Jon Claerbout. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfradius | user/sgreer/Mradius.c | Estimate smoothing radius (min = 1) | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfrect1 | user/fomels/Mrect1.c | 1-D covariance estimator. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfrefl | user/zedong/Mrefl.c | Generate the reflector which will be used in PERM. The input is: | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfrms | user/luke/Mrms.c | Local RMS Determination for an array of arbitrary dimension.  The absolute value of a unit is used for indicies falling  between within the  | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfrtm | user/hpcss/Mrtm.c | Rice HPCSS reverse time migration. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfseislet | user/pwd/Mseislet.c | Seislet transform | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfsemblance | user/fomels/Msemblance.c | Semblance over the specified axis. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfshape | user/fomels/Mshape.c | Non-stationary smoothing by shaping regularization. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfshift | user/psava/Mshift.c | Fourier-domain shift in 1,2 and 3 dimensions | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfsigmoid | user/gee/Msigmoid.c | 2-D synthetic model from J.F.Claerbout. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfsignal | user/chen/Msignal.c | Generate signal series | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfsimilarity | user/fomels/Msimilarity.c | Local similarity measure between two datasets. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfsnr | user/yliu/Msnr.c | Display dataset signal-noise-ratio. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfsnr2 | user/chenyk/Msnr2.c | Compute signal-noise-ratio. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfsort | user/slim/Msort.c | Sort a float/complex vector by absolute values. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfss | user/chen/Mss.c | generate simultaneous sources grid from delay file | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfst | user/yliu/Mst.c | S transform | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfsvmf | user/chenyk/Msvmf.c | Space varying median filtering. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sftahsort | user/karl/Mtahsort.c | Read Trace And Header from separate files in sorted order, write to pipe | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sftahwrite | user/karl/Mtahwrite.c | Read Trace And Header (tah) from standard input, write to separate files | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfthplot | plot/main/thplot.c | Hidden-line surface plot. | no | - | - | no | no | P3 | medium | yes as matplotlib substitute | no | partial |
| sfthr | user/slim/Mthr.c | Threshold float/complex inputs given a constant/varying threshold level. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfthreshold1 | user/chenyk/Mthreshold1.c | Soft or hard thresholding using exact-value or percentile thresholding. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sftpow | user/nobody/Mtpow.c | Time-power gain; audit also records alias relation to sfpow. | yes | pymadagascar.generic.array_math.tpow_rsf | pymadagascar.cli.tpow | yes | yes | Done B-2 | medium | yes | no | subset differs: no xpow and local Axis coordinates |
| sfvplotdiff | plot/main/vplotdiff.c | Vplot diff - see if 2 vplot files represent "identical" plots. | no | - | - | no | no | P3 | medium | yes as matplotlib substitute | no | partial |
| sfwave | user/hpcss/Mwave.c | Rice HPCSS forward modeling. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfzero | user/fomels/Mzero.c | Zero crossings with sub-pixel resolution. | no | - | - | no | no | P3 | high/unknown | unknown | unknown | partial |
| sfaapwd | user/pwd/Maapwd.c | Amplitude-adjusted plane-wave destruction | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfaapwd1 | user/pwd/Maapwd1.c | Amplitude-adjusted PWD - linear operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfabalance | user/fomels/Mabalance.c | Amplitude balancing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfaborn | user/nobody/Maborn.c | Born modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfabsoffdip | user/nobody/Mabsoffdip.c | Apply dip correction for angle-gathers computed with absolute offset | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfaccumulate | user/psava/Maccumulate.c | Accumulate | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfacd2d | user/hpcss/Macd2d.c | time-domain acoustic FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfacoustic1D | user/carrot/Macoustic1D.c | 1-D acoustic wave propagation with CE absorbing boundary | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfacoustic1D_FWI_adj | user/carrot/Macoustic1D_FWI_adj.c | 1-D acoustic FWI with adjoint state method | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfacoustic1D_FWI_ptb | user/carrot/Macoustic1D_FWI_ptb.c | 1-D acoustic FWI with Perturbation method | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfacqgeo | user/jsun/Macqgeo.c | generating acquisition geometry file for sfmpicfftrtm | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfacurv | user/chen/Macurv.c | Azimuth CURVature | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfaddevent | user/chen/Maddevent.c | Add a dispersive event to a seismic profile | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfaddimag | user/zhiguang/Maddimag.c | Convert large-size (with n3=) real data to complex (by adding zero imaginary part) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfaddtrace | user/chenyk/Maddtrace.c | Add zero trace to original profile in order to improve lateral resolution | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfadiradon2 | user/jingwei/Madiradon2.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfadjgradient2d | user/jeff/Madjgradient2d.c | Gradient adjoint-state calculation for image-domain WET | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfadjgradient2d_coupled | user/jeff/Madjgradient2d_coupled.c | Gradient adjoint-state calculation for image-domain WET | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfadjtest | user/jingwei/Madjtest.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfadjtest1 | user/jingwei/Madjtest1.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfafac | user/gee/Mafac.c | Wilson-Burg factorization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfafd2d | user/chenyk/Mafd2d.c | 2D coustic time-domain FD modeling with different boundary conditions | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfafd2domp | user/chenyk/Mafd2domp.c | 2D coustic time-domain FD modeling with different boundary conditions using OpenMP | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfafdfwi3d_mpi | user/chenyk/Mafdfwi3d_mpi.c | 3D Visco-acoustic Forward Modeling, FWI, and RTM based on SLS model | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfafdm2d | user/nobody/Mafdm2d.c | Exploding reflector time-domain acoustic FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfafmod | user/nobody/Mafmod.c | Time-domain acoustic FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfahelicon | user/gee/Mahelicon.c | Apply multidimensional nonstationary filter on a helix. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfahpef | user/gee/Mahpef.c | Adaptive multidimensional nonstationary PEF. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfaimplfd1 | user/petsc/Maimplfd1.c | Implicit solution of 1-D acoustic wave equation. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfaimplfd2 | user/petsc/Maimplfd2.c | Implicit solution of 2-D acoustic wave equation. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfamp | user/luke/Mamp.c | Local mean amplitude Determination for an array of arbitrary dimension.  The initial value of a unit is used for indicies falling  between w | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfanalytical | user/fomels/Manalytical.c | First-arrival traveltime table using analytical traveltimes | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfangdip | user/nobody/Mangdip.c | Dip correction for kh/km from kh/kz | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfangle2 | user/fomels/Mangle2.c | Another illustration of angle gathers. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfangmig | user/luke/Mangmig.c | if y modeling, if n, migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfangmig2 | user/luke/Mangmig2.c | Angle-gather constant-velocity time migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfangmig2d | user/luke/Mangmig2d.c | 2D Angle-gather variable-velocity time migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfangmigM | user/luke/MangmigM.c | Angle-gather constant-velocity time migration with mask file. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfanifd2d | user/nobody/Manifd2d.c | 2D anisotropic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfanisodiffuse | user/dmerzlikin/Manisodiffuse.c | Anisotropic diffusion by regularized inversion. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfanisodiffuse2 | user/dmerzlikin/Manisodiffuse2.c | Anisotropic diffusion by regularized inversion. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfanisolr2 | user/fomels/Manisolr2.cc | q horizontal vs q vertical | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfapef | user/yliu/Mapef.c | Estimate adaptive nonstationary PEF on aliased traces. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfapef2 | user/yliu/Mapef2.c | 2D adaptive nonstationary PEF on aliased traces. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfapefsignoi | user/yliu/Mapefsignoi.c | Signal and noise separation using adaptive PEFs. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfapick | user/chen/Mapick.c | Automatic event PICKing | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfapprox | user/fomels/Mapprox.c | Illustrating non-hyperbolic approximations | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfapradon2 | user/jingwei/Mapradon2.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfaps3d | user/chenyk/Maps3d.c | 3D acoustic wavefield modeling using the pseudo-spectral method | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfarrival | user/fomels/Marrival.c | Multiple-arrival interpolation from down-marching. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfatm1 | user/yliu/Matm1.c | 1D alpha-trimmed-mean filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfatm2 | user/yliu/Matm2.c | 2D alpha-trimmed-mean filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfautocirc2 | user/browaeys/Mautocirc2.c | Circular statistics correlation for 2D data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfautocorr | user/gee/Mautocorr.c | Autocorrelation for helix filters. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfautofocusing | user/fbroggin/Mautofocusing.c | Marchenko-Wapenaar-Broggini iterative scheme | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfavvvdwe2d | user/fperrone/Mavvvdwe2d.c | 2D acoustic variable-velocity variable-density time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfavvvdwe3d | user/fperrone/Mavvvdwe3d.c | 3D acoustic variable-velocity variable-density time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawe | user/nobody/Mawe.c | Time-domain acoustic wave-equation FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawefd | user/nobody/Mawefd.c | acoustic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawefd1 | user/nobody/Mawefd1.c | Acoustic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawefd2d | user/cwp/Mawefd2d.c | 2D acoustic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawefd2d_fo | user/fbroggin/Mawefd2d_fo.c | Finite-difference time-domain (FDTD) wave propagation modeling in lossless acoustic 2D media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawefd2dds | user/tariq/Mawefd2dds.c | 2D acoustic time-domain FD modeling  for source perturbation -first order | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawefd2dds2nd | user/tariq/Mawefd2dds2nd.c | 2D acoustic time-domain FD modeling  for source perturbation- 2nd order approximation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawefd2dds2ndhomo | user/tariq/Mawefd2dds2ndhomo.c | 2D acoustic time-domain FD modeling  for source perturbation- 2nd order test | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawefd2dds2ndV | user/tariq/Mawefd2dds2ndV.c | 2D acoustic time-domain FD modeling  for source perturbation - 2nd order approximation for complex v | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawefd2ddshomo | user/tariq/Mawefd2ddshomo.c | 2D acoustic time-domain FD modeling  for source perturbation-1st order test | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawefd2ddsV | user/tariq/Mawefd2ddsV.c | 2D acoustic time-domain FD modeling  for source perturbation- 1st order approximation for complex v | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawefd2dOLD | user/psava/Mawefd2dOLD.c | 2D acoustic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawefd2dps | user/roman/Mawefd2dps.c | 2D acoustic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawefd3d | user/cwp/Mawefd3d.c | 3D acoustic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawefd3dOLD | user/psava/Mawefd3dOLD.c | 3D acoustic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfaweop2d | user/psava/Maweop2d.c | 2D AWE modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfaweop3d | user/psava/Maweop3d.c | 3D AWE modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfawesg | user/cwp/Mawesg.c | Acoustic staggered-gridded time-domain FD modeling, | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfaxplusy | user/jeff/Maxplusy.c | Computes a*x + y, where x and y are datasets, and a is scalar | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfazpwd | user/dmerzlikin/Mazpwd.c | Azimuthal Plane-Wave Destruction | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfAzsort | user/mehdi/MAzsort.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfazspr | user/dmerzlikin/Mazspr.c | Combining Sprays: Simply Input Sprays in In-line And Cross-line | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbackdire | user/parvaneh/Mbackdire.c | Background directivity(Dip). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbackdireazi | user/parvaneh/Mbackdireazi.c | Background directivity(Azimuth). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbackus | user/jeff/Mbackus.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbdix | user/fomels/Mbdix.c | Convert RMS to interval velocity using LS and shaping regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbeamform | user/pwd/Mbeamform.c | 2-D beam forming. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbeamform1 | user/fomels/Mbeamform1.c | Gaussian beam forming. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbeamsteer | user/browaeys/Mbeamsteer.c | Beam steering for 2D surface array. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbessel | user/nobody/Mbessel.c | Bessel functions | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbigmpiencode | user/cwp/Mbigmpiencode.c | shot encoding with arbitrary phase and amplitude weights using MPI on a distributed cluster | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfbigmpistack | user/cwp/Mbigmpistack.c | remap and stacks rsf files using mpi | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfbil1 | user/fomels/Mbil1.c | Bi-variate L1 regression | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbil1_new | user/lcasasan/Mbil1_new.c | L1 regression 0 ~= d - G * m | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbilat2 | user/fomels/Mbilat2.c | 2-D bilateral filtering | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbilstack | user/yliu/Mbilstack.c | Bilateral stacking. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbin2rsf | user/chenyk/Mbin2rsf.c | Binary file to RSF file | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfblend | user/chenyk/Mblend.c | Seismic blending operator. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfblindpick | user/nobody/Mblindpick.c | Automatic picking from semblance-like panels using shaping regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfblindpick2 | user/nobody/Mblindpick2.c | Automatic picking from semblance panels using shaping regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfblur | user/fomels/Mblur.c | 2-D blurring and deblurring | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbmcgauss | user/browaeys/Mbmcgauss.c | Correlated Gaussian joint probability distribution histogram generated with modified Box Mulller algorithm | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfboolcmp | user/slim/Mboolcmp.c | Element-wise boolean comparison of values. For int/float/complex data-sets. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfborn2d | user/nobody/Mborn2d.c | Born modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfboxcascade | user/fomels/Mboxcascade.c | Box filter cascade | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfboxfilter | user/psava/Mboxfilter.c | 3D convolution with arbitrary filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfboxsmooth2 | user/nobody/Mboxsmooth2.c | 2-D smoothing by box directional shaping. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbrfault | user/zhiguang/Mbrfault.c | Bridge fault zones with smooth transition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbspvel2 | user/cram/Mbspvel2.c | B-spline coefficients for a 2-D (an)isotropic velocity model. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbspvel3 | user/cram/Mbspvel3.c | B-spline coefficients for a 3-D (an)isotropic velocity model. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfburstnoise | user/gee/Mburstnoise.c | Synthetics with bursts of noise. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbvvvdwe2d | user/fperrone/Mbvvvdwe2d.c | Born variable-density variable-velocity acoustic 2D time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbvvvdwe3d | user/fperrone/Mbvvvdwe3d.c | Born variable-density variable-velocity acoustic 3D time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfbyte2rsf | user/nobody/Mbyte2rsf.c | Convert raw byte images to RSF. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfc1coh | user/yliu/Mc1coh.c | C1 coherency algorithm. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcameron | user/nobody/Mcameron.c | Convert Dix velocity to interval velocity (2-D). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcameron2d | user/kourkina/Mcameron2d.c | Convert Dix velocity to interval velocity. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcamig | user/nobody/Mcamig.c | 3-D common-azimuth modeling/migration with extended split-step | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcamig3 | user/psava/Mcamig3.c | 3-D common-azimuth modeling/migration with extended SSF | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcanisolr2 | user/jsun/Mcanisolr2.cc | q horizontal vs q vertical | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcanisolr2abc | user/jsun/Mcanisolr2abc.cc | from eta to q | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcarpet | user/fomels/Mcarpet.c | Carpet flattening. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcatan2 | user/browaeys/Mcatan2.c | Argument of complex data calculated by atan2. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcausinv | user/fomels/Mcausinv.c | Smooth derivative by regularized causint inversion | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcbeamform1 | user/fomels/Mcbeamform1.c | Gaussian beam forming for complex data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfccausint | user/fomels/Mccausint.c | Complex Causal integration on the first axis. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcchebyshevp | user/fomels/Mcchebyshevp.c | Chebyshev polynomial coefficients for complex functions | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcconjgradmpi | system/main/cconjgradmpi.c | Generic conjugate-gradient solver for linear inversion. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfcconst | user/llisiw/Mcconst.c | Gaussian beam and exact complex eikonal for constant velocity medium | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcconv | user/gee/Mcconv.c | 1-D convolution with complex numbers. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfccrsym | user/jsun/Mccrsym.c | determine symmetry using correlation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcdivdir | user/chenyk/Mcdivdir.c | Direct division for complex data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcdivn | user/fomels/Mcdivn.c | Smooth division for complex data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcdottestmpi | system/main/cdottestmpi.c | Generic dot-product test for complex linear operators with adjoints | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfcemd1 | user/chenyk/Mcemd1.c | Bivariate empirical mode decomposition using first algorithm. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcemd2 | user/chenyk/Mcemd2.c | Bivariate empirical mode decomposition using second algorithm. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcerf | user/dmerzlikin/Mcerf.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftexp2 | user/jsun/Mcfftexp2.c | 2-D FFT-based zero-offset exploding reflector modeling/migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftexp2test | user/jsun/Mcfftexp2test.c | 2-D FFT-based zero-offset exploding reflector modeling/migration (outputs time volume, not just last image; can be used to generate movie) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftexpa-dev | user/fomels/Mcfftexpa-dev.c | Development stage-2-D complex FFT-based zero-offset exploding reflector modeling/migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftexpmig2 | user/jsun/Mcfftexpmig2.c | Complex 2-D exploding reflector migration (read in initial complex wavefield in depth) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftrtm3 | user/jsun/Mcfftrtm3.cc | head files aumatically produced from C programs | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftwave1 | user/fomels/Mcfftwave1.c | 1-D complex lowrank FFT wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftwave1d | user/jsun/Mcfftwave1d.c | 1-D complex lowrank FFT wave extrapolation using complex to complex fft using initial condition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftwave1dd | user/jsun/Mcfftwave1dd.c | 1-D complex lowrank FFT wave extrapolation using complex to complex fft using initial condition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftwave1in | user/jsun/Mcfftwave1in.c | 1-D complex lowrank FFT wave extrapolation using complex to complex fft BY INJECTION | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftwave2 | user/jsun/Mcfftwave2.c | Complex 2-D wave propagation (with multi-threaded FFTW3) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftwave2d | user/jsun/Mcfftwave2d.c | Complex 2-D wave propagation (outputs real wavefield) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftwave2dd | user/jsun/Mcfftwave2dd.c | Complex 2-D wave propagation (outputs complex wavefield; with multi-threaded FFTW3) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftwave2mix | user/jsun/Mcfftwave2mix.c | Complex 2-D wave propagation (with kiss-fft) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftwave2mix2 | user/jsun/Mcfftwave2mix2.c | Complex 2-D wave propagation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftwave2nsps | user/jsun/Mcfftwave2nsps.c | Complex 2-D wave propagation (NSPS) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftwave2omp | user/jsun/Mcfftwave2omp.c | Complex 2-D wave propagation (with multi-threaded FFTW3) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftwave2taper | user/jsun/Mcfftwave2taper.c | Complex 2-D wave propagation (with multi-threaded FFTW3) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcfftwave3 | user/jsun/Mcfftwave3.c | Simple 3-D lowrank onestep wave propagation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcflow | user/fomels/Mcflow.c | Fast mean-curvature flow. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcgconst | user/llisiw/Mcgconst.c | Test Beam for constant velocity gradient | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfchain2dfft | user/fomels/Mchain2dfft.c | Find a symmetric chain of 2D-Fourier weighting and scaling with movies | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfchaindr | user/dmerzlikin/Mchaindr.c | chain diffraction extraction debug version | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfchebvc | user/fomels/Mchebvc.c | Post-stack 2-D velocity continuation by Chebyshev-tau method. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfchebyshev | user/fomels/Mchebyshev.c | Testing Chebyshev interpolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfchebyshevp | user/fomels/Mchebyshevp.c | Chebyshev polynomial coefficients | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcheckerboard | user/psava/Mcheckerboard.c | make a 2D/3D checkerboard model | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcheckptdemo | user/pyang/Mcheckptdemo.c | RTM with checkpointing in 2D acoustic media | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcic3d_ditthara | user/ditthara/Mcic3d_ditthara.c | Conventional IC 3D | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcicold2d | user/psava/Mcicold2d.c | Conventional IC 2D | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcicop2d | user/psava/Mcicop2d.c | Conventional IC 2D | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcicop3d | user/psava/Mcicop3d.c | Conventional IC 2D | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcigangle | user/roman/Mcigangle.c | src-receiver to angle gathers | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcij2moveout | user/zone/Mcij2moveout.c | Converting interval Cij to interval/effective moveout coefficients in 3D layered orthorhombic with possible phimuthal rotation (Sripanich an | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcipcut | user/cwp/Mcipcut.c | cut at CIPs | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcisolr1 | user/jsun/Mcisolr1.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcisolr2 | user/jsun/Mcisolr2.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcisolr2abc | user/jsun/Mcisolr2abc.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcisolr2abc1 | user/jsun/Mcisolr2abc1.cc | if (iz < nbt) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcisolr2grad | user/jsun/Mcisolr2grad.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcisolr2rev | user/jsun/Mcisolr2rev.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcisolr2testneg | user/jsun/Mcisolr2testneg.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcisolr3 | user/jsun/Mcisolr3.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfckolmog | user/gee/Mckolmog.c | complex Kolmogoroff spectral factorization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfclaplac | user/jsun/Mclaplac.c | 2-D finite-difference Laplacian operation for complex numbers. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfclfd1 | user/jsun/Mclfd1.c | 2-D Fourth-order Optimized Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfclfd2 | user/jsun/Mclfd2.c | 2-D Fourth-order Optimized Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfclfdc1 | user/jsun/Mclfdc1.cc | int count = 0; | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfclfdc1-bak | user/jsun/Mclfdc1-bak.cc | int nk=0; | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfclfdc1frac | user/jsun/Mclfdc1frac.cc | int count = 0; | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfclfdc2 | user/jsun/Mclfdc2.cc | Next | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfclipmef | user/mehdi/Mclipmef.c | Input and output files | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcloudbin3d | user/psava/Mcloudbin3d.c | point cloud binning | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcloudmerge3d | user/psava/Mcloudmerge3d.c | 3D CLoud DATA merge | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcloudspray | user/psava/Mcloudspray.c | point cloud spray | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcloudwin3d | user/psava/Mcloudwin3d.c | 3D CLoud WINdowing | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfclpf | user/fomels/Mclpf.c | Local prediction filter for complex numbers (n-dimensional). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfclrmatrix | user/lexing/Mclrmatrix.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcltft | user/fomels/Mcltft.c | Complex local time-frequency transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcltftfft | user/fomels/Mcltftfft.c | Complex local time-frequency transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcmatmult3 | user/gchliu/Mcmatmult3.c | Multiplication of two complex matrices for 3D data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcmatrix | user/jsun/Mcmatrix.c | multiply, for complex Matrix | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcnvd | user/fomels/Mcnvd.c | Residual from convection filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcnvdip | user/fomels/Mcnvdip.c | Dip estimation from convection | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcnvpaint | user/fomels/Mcnvpaint.c | Convection painting. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcoh | user/nobody/Mcoh.c | 3-D coherency estimation using plane wave destruction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcoherence | user/chen/Mcoherence.c | 3D Coherence Cube, C1, C2, C3 in one | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcohn | user/pyang/Mcohn.c | Coherence calculations in the presence of structural dip | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcomblist | user/browaeys/Mcomblist.c | Create masks to remove combinations of k elements out of n | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcompensate | user/jsun/Mcompensate.c | Complex-valued compensation (between two wavefields) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcompensatexf | user/jsun/Mcompensatexf.c | Complex-valued compensation (between two wavefields) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfconflict | user/gee/Mconflict.c | 2-D synthetic data of conflicting dips. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfconjgradmpi | system/main/conjgradmpi.c | Generic conjugate-gradient solver for linear inversion. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfconst2dangmig | user/luke/Mconst2dangmig.c | if y modeling, if n, migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfconst2dangmigsemb | user/luke/Mconst2dangmigsemb.c | Angle-gather constant-velocity time migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfconstperm | user/fomels/Mconstperm.c | Constant-velocity prestack exploding reflector. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfconstpermh | user/fomels/Mconstpermh.c | Constant-velocity prestack exploding reflector in offset. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfconstpermh1 | user/fomels/Mconstpermh1.c | Constant-velocity prestack exploding reflector in offset. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfconvection | user/fomels/Mconvection.c | Convection filter. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfconvert0eq | user/yliu/Mconvert0eq.c | Convert equivalent Q value from reference layer to t0 location. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfconverted | user/mehdi/Mconverted.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfconvf | user/gee/Mconvf.c | 1-D convolution, adjoint is the filter. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfconvft | user/saragiotis/Mconvft.c | Trace-by-trace or data-by-trace convolution using Fourier transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfconvkernel | user/ediazp/Mconvkernel.c | Applies a 1,2, or 3D convolution kernel or its adjoint | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfconvolve | user/luke/Mconvolve.c | convolve input 2D image by kernel | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfconvolve2 | user/jyan/Mconvolve2.c | 2D convolution with arbitrary filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcorral | user/rickettj/Mcorral.c | Cross-correlate every trace with every other in frequency domain. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcorrectwave2 | user/jsun/Mcorrectwave2.c | Complex 2-D wave propagation using initial condition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcorrft | user/saragiotis/Mcorrft.c | Trace-by-trace or data-by-trace correlation using Fourier transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcortholr3 | user/jsun/Mcortholr3.cc | from degrees to radians | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcosftwave1 | user/fomels/Mcosftwave1.c | 1-D FFT wave extrapolation using Cosine FT | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcovariance2d | user/luke/Mcovariance2d.c | determine covariance from 2d data of mean zero, output is n1xn1 array | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcpef | user/fomels/Mcpef.c | 1-D prediction-error filter estimation from complex data | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcpef1 | user/gee/Mcpef1.c | Estimate complex PEF on the first axis. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcplxatt | user/browaeys/Mcplxatt.c | Statistical attributes for circular data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcplxcoh | user/browaeys/Mcplxcoh.c | Coherency based on complex statistical correlation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcplxcor | user/browaeys/Mcplxcor.c | Statistical complex correlation for circular data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcplxloc | user/browaeys/Mcplxloc.c | Local coherency and dip based on trace-by-trace complex statistical correlation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcpxeikonal | user/llisiw/Mcpxeikonal.c | Iterative complex eikonal solver | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcr | user/fomels/Mcr.c | Column-row matrix decomposition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcram2 | user/cram/Mcram2.c | 2-D angle-domain Kirchhoff migration based on escape tables. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcram3 | user/cram/Mcram3.c | 3-D angle-domain Kirchhoff migration based on escape tables. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcramdd | user/cram/Mcramdd.c | Daemon for distributed storage of prestack data for angle migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcrazgathc3 | user/cram/Mcrazgathc3.c | Collapse/stack (partially) azimuthal axis of 3-D angle-domain migration angle gathers. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcrestack | user/dirack/Mcrestack.c | Common Reflection Element (CRE) stacking | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcretrajec | user/dirack/Mcretrajec.c | Calculate CRE trajectory on CMP x Offset plane given zero-offset CRS parameters (RN, RNIP, BETA) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcrssemb | user/aklokov/Mcrssemb.c | CRS-based semblance | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcrssemb3d | user/aklokov/Mcrssemb3d.c | CRS-based semblance for 3D | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcshifts2 | user/gchliu/Mcshifts2.c | Generate shifts for 2-D regularized autoregression in complex domain. From (x,y,f) to (x,y,s,f) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcsp2d | user/seisinv/Mcsp2d.c | 2-D common scattering-point gathers mapping and its adjoint | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcsqrtf | user/ivlad/Mcsqrtf.c | Complex square root. Good example of I/O loop for applying a function. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcstack2d | user/jsun/Mcstack2d.c | Stack multi-shots images with complex values | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfctf2dprec | user/fomels/Mctf2dprec.c | TF Weights Preconditioner for Complex input as linear operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfctilr2 | user/jsun/Mctilr2.cc | from degrees to radians | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfctmf | user/nobody/Mctmf.c | Constant-time 2D median filtering | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfctscigadj | user/zhiguang/Mctscigadj.c | Correcting time-shift gathers and its adjoint | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfctscigder | user/zhiguang/Mctscigder.c | Get the derivative of time-shift gathers | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfctshift | user/zhiguang/Mctshift.c | Correct time-shift gathers | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcube2list | user/nobody/Mcube2list.c | Maps a cube to a list, given a threshold (clip value). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcubesrc | user/jsun/Mcubesrc.c | Simple 2-D wave propagation with multi-threaded fftw3 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcurv | user/chen/Mcurv.c | Max/Min curvatures by azimuth curvature cube | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcurv2 | user/chen/Mcurv2.c | Joint estimation of curvature and slope | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfcurvature | user/parvaneh/Mcurvature.c | Curvature | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdagap | user/aklokov/Mdagap.c | Reflection event apex protector/removal for dip-angle gathers. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdagap3 | user/luke/Mdagap3.c | Reflection event apex protector/removal for dip-angle gathers. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdagap3a | user/luke/Mdagap3a.c | Reflection event apex protector/removal for dip-angle gathers. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdagap3e | user/luke/Mdagap3e.c | Reflection event apex protector/removal for dip-angle gathers. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdagapex | user/luke/Mdagapex.c | dip angle gathers | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdagtaper | user/aklokov/Mdagtaper.c | Edge tapering for dip-angle gathers | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdatasucjb2rsf2d | user/chengjb/Mdatasucjb2rsf2d.c | Convert 2D cjb-SU data to RSF format. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdatasucjb2rsf3d | user/chengjb/Mdatasucjb2rsf3d.c | Convert 3D cjb-SU data to RSF format. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdatasucjb2rsf3dnh | user/chengjb/Mdatasucjb2rsf3dnh.c | Convert 3D cjb-PC no head (x,y, z) data to RSF format. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdatshift | user/bash/Mdatshift.c | Calculate datum shift from elevation profile for 2-D shot gathers | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdbfmig | user/aklokov/Mdbfmig.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdblendseis | user/chenyk/Mdblendseis.c | Blending, or Deblending using seislet domain thresholding. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdcpanel | user/sujith/Mdcpanel.c | Phase velocity vs frequency panels for surface waves | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdealias | user/nobody/Mdealias.c (+1) | Trace interpolation to a denser XY grid using PWD. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdealias2 | user/pwd/Mdealias2.c | 2-D (inline) trace interpolation to a denser grid using PWD. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdeblur | user/fomels/Mdeblur.c | Non-stationary debluring by inversion | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdeburst | user/gee/Mdeburst.c | Remove bursty noise by IRLS. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdecibel | user/psava/Mdecibel.c | Decibel | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdeepchain1 | user/fomels/Mdeepchain1.c | Deep symmetric chain with 1D Fourier | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfderiv3 | user/ediazp/Mderiv3.c | Second order derivative along axis | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdespike | user/gee/Mdespike.c | Remove spikes in by sliding 1-D medians. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdespike1-ed | user/ediazp/Mdespike1-ed.c | Despike filter: | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdespike2 | user/gee/Mdespike2.c | Remove spikes in by sliding 2-D medians. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdespike2-ed | user/ediazp/Mdespike2-ed.c | Despike filter: | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdespike3 | user/gee/Mdespike3.c | Remove spikes in by sliding 3-D medians. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdiffcxx | user/chenyk/Mdiffcxx.cc | input parameters | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdifferr | user/browaeys/Mdifferr.c | Error by substituting numerical solution into equation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdiffuse2 | user/dmerzlikin/Mdiffuse2.c | Diffusion by regularized inversion. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdiiradon2 | user/jingwei/Mdiiradon2.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdijkstra | user/pwd/Mdijkstra.c | Dijkstra shortest-path algorithm in 2-D | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdip_fb | user/chenyk/Mdip_fb.c | 3-D dip estimation by plane wave destruction with forward and backward space derivative calculation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdiparti | user/aklokov/Mdiparti.cc | diparti | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdiparti3 | user/aklokov/Mdiparti3.cc | diparti | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdipcoh | user/chen/Mdipcoh.c | 3D Coherence cube | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdipflt | user/chen/Mdipflt.c | 2D dip filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdiphase | user/fomels/Mdiphase.c | Derivative of local frequency. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdipl | user/chenyk/Mdipl.c | large dip calculation via PWD | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdiplet | user/pwd/Mdiplet.c | 2-D Seislet frame | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdipln | user/chenyk/Mdipln.c | large dip calculation via non-stationary regularization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdipn | user/chenyk/Mdipn.c | 3-D robust dip estimation by plane wave destruction with non-stationary smoothing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdipn_fb | user/chenyk/Mdipn_fb.c | 3-D robust dip estimation by plane wave destruction with non-stationary smoothing and forward-backward space derivative calculation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdipp | user/luke/Mdipp.c | 3-D dip estimation by plane wave destruction with OpenMP parallelism. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdipspray | user/nobody/Mdipspray.c | $Id$ | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdiptaper | user/aklokov/Mdiptaper.c | Aperture optimization for migrated gathers in the dip-angle domain. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdiradon2 | user/jingwei/Mdiradon2.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdiradon3 | user/jingwei/Mdiradon3.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdiradon32 | user/jingwei/Mdiradon32.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdiradon34 | user/jingwei/Mdiradon34.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdispelem | user/chenyk/Mdispelem.c | Display element of rsf files. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdistmap | user/jyan/Mdistmap.c | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdistpaint | user/pwd/Mdistpaint.c | Geologic distance painting by plane-wave construction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdistpaint3D | user/pwd/Mdistpaint3D.c | 3-D painting by plane-wave construction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfditime2d | user/aklokov/Mditime2d.c | 2D Hybrid Radon transform for diffraction imaging in the time dip-angle domain | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfditime3d | user/aklokov/Mditime3d.c | 3D Hybrid Radon transform for diffraction imaging in the time dip-angle domain | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdivn | user/fomels/Mdivn.c | Smooth division. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdivn2d | user/chen/Mdivn2d.c | 2D divn | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdivnls | user/chen/Mdivnls.c | 2D divn by stationary LS | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdivnp | user/luke/Mdivnp.c | OpenMP Parallelized  Smooth division. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdixshape | user/pwd/Mdixshape.c | Convert RMS to interval velocity using LS and shaping regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdlct | user/pyang/Mdlct.c | discrete linear chirp transfrom (DLCT) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdmeig | user/mccowan/Mdmeig.c | Find eigenvalues and eigenvectors of an spd matrix. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdmigda | user/aklokov/Mdmigda.cc | 2D depth scattering-angle Kirchhoff migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdoeps | user/yliu/Mdoeps.c | 2D dip-oriented edge-preserving smoothing (DOEPS). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdomf | user/yliu/Mdomf.c | 2D dip-oriented median/mean filter (DOMF). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdominantf | user/yliu/Mdominantf.c | Calculate dominant frequency of amplitude spectra dataset. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdonf | user/yliu/Mdonf.c | 2D dip-oriented nonlocal (bilateral) smoothing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdonut | user/fomels/Mdonut.c | Donut filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdottestmpi | system/main/dottestmpi.c | Generic dot-product test for linear operators with adjoints | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfdowmf | user/yliu/Mdowmf.c | 2D dip-oriented weighted median filter (DOWMF). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdpeiko | user/fomels/Mdpeiko.c | 2-D eikonal solver based on dynamic programming. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdrayinte | user/llisiw/Mdrayinte.c | 2D Dynamic Ray Tracing | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdrays | user/llisiw/Mdrays.c | 2D dynamic ray tracing by a Runge-Kutta integrator. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdsreiko | user/llisiw/Mdsreiko.c | Double square-root eikonal solver (2D) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdsreiko0 | user/llisiw/Mdsreiko0.c | Double square-root eikonal solver (2D + explicit) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdsrstep1 | user/nobody/Mdsrstep1.c | 2-D prestack modeling/migration with split-step DSR. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdsrtomo | user/llisiw/Mdsrtomo.c | Prestack first-arrival traveltime tomography (DSR) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdsrtomo0 | user/llisiw/Mdsrtomo0.c | Prestack first-arrival traveltime tomography (DSR) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdtw | user/luke/Mdtw.c | program calculates the shifts to warp a matching trace (input) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdtw-accumulate | user/luke/Mdtw-accumulate.c | accumulates or smooths alignment errors in the | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdtw-apply | user/luke/Mdtw-apply.c | program applies integer shifts (stored as floats!) to warp a matching trace.  Can match 1d shifts to a 1,2, or 3d volume , or 2d shifts to a | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdtw-errors | user/luke/Mdtw-errors.c | program calculates the alignment errors | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdtw-flatten | user/luke/Mdtw-flatten.c | flattens a gather or similar object to its stack using dtw, optionally writes out shifts, currently set up for (time,gather,space) for 2d im | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdtw-interp | user/luke/Mdtw-interp.c | program takes traces sampled at arbitrary locations along a 1d line | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdtw-track | user/luke/Mdtw-track.c | problem finds the optimal trajectory | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdtw2 | user/luke/Mdtw2.c | program warps a 2D input image to a 2D reference image | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfduffing | user/yliu/Mduffing.c | Duffing differential equation solved by 4th order Runge-Kutta method. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfduffing1 | user/yliu/Mduffing1.c | 1D signal analysis by using Duffing differential equation solved by 4th order Runge-Kutta method. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfduffing2 | user/yliu/Mduffing2.c | 2D/3D Velocity analysis by using Duffing differential equation solved by 4th order Runge-Kutta method. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfduwt | user/yliu/Mduwt.c | 1-D digital undecimated (stationary) wavelet transform by lifting scheme | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdvscan2d | user/aklokov/Mdvscan2d.c | Diffraction velocity analysis | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdwt2 | user/yliu/Mdwt2.c | 1-D digital wavelet transform (another version) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdwt97 | user/yliu/Mdwt97.c | 1-D CDF 9/7 biorthogonal digital wavelet transform | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdwtdenoise | user/chenyk/Mdwtdenoise.c | 2D Digital Wavelet Transoform Denoising | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfdzest2d | user/zhiguang/Mdzest2d.c | Estimation of depth-delay of common-image gathers | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeacd2d | user/hpcss/Meacd2d.c | Extended time-domain acoustic FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeasypath | user/zgeng/Measypath.c | Finding the easy path | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfederiv | user/jyan/Mederiv.c | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfederiv2d | user/jyan/Mederiv2d.c | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfederiv3d | user/jyan/Mederiv3d.c | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfederiv3dfilters | user/jyan/Mederiv3dfilters.c | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfefd3dmt | user/chenyk/Mefd3dmt.c | 3D 8-th order elastic wave propagation with sponge ABC and moment tensor source | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeicold2d | user/psava/Meicold2d.c | Extended IC 3D | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeicop2d | user/psava/Meicop2d.c | Extended IC 2D | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeicop3d | user/psava/Meicop3d.c | Extended IC 2D | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeigen | user/luke/Meigen.c | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeikds | user/tariq/Meikds.c | Source differntial eikonal solver (3-D). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeikEta | user/tariq/MeikEta.c | Eta differential eikonal solver (3-D). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeikfswp | user/bash/Meikfswp.c | Fast sweeping eikonal solver (2-D/3-D). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeikods | user/llisiw/Meikods.c | Fast marching with source perturbation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeikonal | user/fomels/Meikonal.c | Fast marching eikonal solver (3-D). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeikonal_rtp | user/chenyk/Meikonal_rtp.c | Fast marching eikonal solver (3-D) in spherical coordinates. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeikonal_surf | user/chenyk/Meikonal_surf.c | Fast marching eikonal solver (3-D) and record the traveltimes on the surface. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeikonal_surf_dv1d | user/chenyk/Meikonal_surf_dv1d.c | Fast marching eikonal solver (3-D) and record the traveltimes on the surface. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeikonalvti | user/fomels/Meikonalvti.c | Fast marching eikonal solver in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeikvti | user/tariq/Meikvti.c | VTI eikonal solver (3-D). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfelipse | user/luke/Melipse.c | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfemfdm2d | user/psava/Memfdm2d.c | 2D EM FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfemfdm2d_p | user/ditthara/Memfdm2d_p.c | 2D EM FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfemfdm3d | user/ditthara/Memfdm3d.c | 3D Electromagnetic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfencode | user/psava/Mencode.c | shot encoding with arbitrary delays | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeno2 | user/fomels/Meno2.c | Convert velocity to slowness and compute gradient using ENO interpolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfenoder1 | user/nobody/Menoder1.c | Taking first derivative along the fast axis using ENO interpolation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfenvcorr | user/nobody/Menvcorr.c | Local correlation with the envelope. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfepfad | user/chen/Mepfad.c | ADaptive Eage Preserving Filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfepfbe | user/chen/Mepfbe.c | Bi-Exponential Edge Preserving Smoothing | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfepfbil | user/chen/Mepfbil.c | Bilateral filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfepfws | user/chen/Mepfws.c | Edge preserving (smoothing) filter by window selection | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfepisort | user/yunzhi/Mepisort.c | Sort microseismic surface array recording traces by their distances or azimuths to a given epicenter. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfepot | user/psava/Mepot.c | compute quasi-static electric potential | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfepsf | user/yliu/Mepsf.c | 1-D and 2-D edge-preserving smoothing (EPS) filter. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sferf | user/fomels/Merf.c | Bandpass filtering using erf function. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sferfdm | user/nobody/Merfdm.c | time-domain acoustic FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfescbsc3 | user/cram/Mescbsc3.c | Prepare supercells for stitching escape tables in 3-D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfescdiff | user/cram/Mescdiff.c | Compute distance and traveltime difference between two escape tables. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfescfgrid2 | user/cram/Mescfgrid2.c | Solution of escape equations by Gauss-Seidel solver on full grid for 2-D (an)isotropic media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfescnband2 | user/cram/Mescnband2.c | Solution of escape equations by hybrid solver with narrow band for 2-D (an)isotropic media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfescrt2 | user/cram/Mescrt2.c | Escape tables by ray tracing with escape equations in 2-D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfescrt3 | user/cram/Mescrt3.c | Escape tables by ray tracing with escape equations in 3-D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfescscd3 | user/cram/Mescscd3.c | Daemon for distributed computation of stitched escape solutions in supercells in 3-D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfescst3 | user/cram/Mescst3.c | Escape tables by stitching of escape solutions in supercells in 3-D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfesctbl2 | user/cram/Mesctbl2.c | Esctape tables from solution of escape equations by the hybrid solver with narrow band. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfesou | user/psava/Mesou.c | source for quasistatic electric potential | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewdlr3 | user/jsun/Mewdlr3.cc | Lowrank symbol approxiamtion for 3-D recursive integral time extrapolation of elastic waves | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewdlr3d | user/jsun/Mewdlr3d.c | 3D elastic recursive integral time extrapolation using KISS-FFT | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewedc3d | user/jsun/Mewedc3d.c | 3D elastic recursive integral time extrapolation of decomposed wave modes using shared-memory parallel FFT (decoupled formulation) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewedc3dgrad | user/jsun/Mewedc3dgrad.c | 3D elastic recursive integral time extrapolation of decomposed wave modes using KISS-FFT | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewedc3p | user/jsun/Mewedc3p.cc | Lowrank symbol approxiamtion for 3-D recursive integral time extrapolation of decomposed P wave mode | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewedc3pgrad | user/jsun/Mewedc3pgrad.cc | Lowrank symbol approxiamtion for 3-D recursive integral time extrapolation of elastic waves | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewedc3s | user/jsun/Mewedc3s.cc | Lowrank symbol approxiamtion for 3-D recursive integral time extrapolation of decomposed S wave modes | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewedc3sgrad | user/jsun/Mewedc3sgrad.cc | Lowrank symbol approxiamtion for 3-D recursive integral time extrapolation of elastic waves | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewefd | user/psava/Mewefd.c | elastic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewefd2 | user/jyan/Mewefd2.c | elastic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewefd2d | user/psava/Mewefd2d.c | 2D elastic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewefd2d_omp | user/jeff/Mewefd2d_omp.c | 2D elastic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewefd2dtti | user/jyan/Mewefd2dtti.c | elastic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewefd3d | user/psava/Mewefd3d.c | 3D elastic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewefd3d_omp | user/jeff/Mewefd3d_omp.c | 3D elastic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewefd3dtti | user/jyan/Mewefd3dtti.c | 3D elastic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewefdm | user/cwp/Mewefdm.c | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeweks3d | user/jsun/Meweks3d.c | 3D elastic time-domain pseudo-spectral (k-space) modeling using shared-memory parallel FFT | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfeweks3dsecd | user/jsun/Meweks3dsecd.c | 3D elastic time-domain pseudo-spectral (k-space) modeling using shared-memory parallel FFT (second-order equation) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewelr3 | user/jsun/Mewelr3.cc | Lowrank symbol approxiamtion for 3-D recursive integral time extrapolation of elastic waves | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewelr3d | user/jsun/Mewelr3d.c | 3D elastic recursive integral time extrapolation using shared-memory parallel FFT | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewelr3dgrad | user/jsun/Mewelr3dgrad.c | 3D elastic recursive integral time extrapolation using shared-memory parallel FFT (with gradient term) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfewelr3grad | user/jsun/Mewelr3grad.cc | Lowrank symbol approxiamtion for 3-D recursive integral time extrapolation of elastic waves | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfexcitationic | user/pyang/Mexcitationic.c | Demo for excitation imaging condition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfexgr | user/fomels/Mexgr.c | Exact group velocity in VTI media | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfexpand | user/fangg/Mexpand.c | Expand 2D data | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfexpand3 | user/zone/Mexpand3.c | Expand 3D data | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfexpd | user/chenyk/Mexpd.c | Expand 2D data corret version with true spatial cooridinates | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfexplanesignoi | user/pwd/Mexplanesignoi.c | Signal and noise separation using both frequency components and dips. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfexpsignoi | user/pwd/Mexpsignoi.c | Signal and noise separation using frequency components. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfexpsignoi3 | user/pwd/Mexpsignoi3.c | Signal and noise separation using frequency components. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffactorm | user/gee/Mfactorm.c | Plane-wave destruction with 3-D plane-wave filter. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffactorn | user/gee/Mfactorn.c | Missing data interpolation with 3-D plane-wave filter. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffacttieikonal | user/uwaheed/Mfacttieikonal.c | Fast sweeping factored TTI eikonal solver (2D) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffagrad | user/yliu/Mfagrad.c | Calculating frequency attenuation gradient. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffastft | user/mccowan/Mfastft.c | Fast Fourier Transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffastpwd | user/chen/Mfastpwd.c | 2-D dip estimation using analytical equation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffatomo | user/llisiw/Mfatomo.c | First-arrival Traveltime Tomography | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffatomoomp | user/llisiw/Mfatomoomp.c | First-arrival Traveltime Tomography (OMP) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffault | user/chen/Mfault.c | fault detection | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffaultrbf1d | user/yunzhi/Mfaultrbf1d.c | Compute RBF across fault using fault attribute computed by Sobel filter. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffbank1 | user/chen/Mfbank1.c | 1d filter bank | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffbank2 | user/chen/Mfbank2.c | 2d filter bank | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffbdip | user/chen/Mfbdip.c | omnidirectional dip estimation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffbfreq | user/chen/Mfbfreq.c | frequency response of linear phase filter bank | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffbgabor | user/chen/Mfbgabor.c | Gabor transform by linear phase filter bank | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffbpick | user/yliu/Mfbpick.c | First break picking from instantaneous traveltime attribute. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffbpwd | user/chen/Mfbpwd.c | omnidirectional plane-wave destruction | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffbrec2d | user/pyang/Mfbrec2d.c | 2-D forward modeling to generate shot records | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffcoh1 | user/chen/Mfcoh1.c | Fast C1 Coherence | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffcoh2 | user/chen/Mfcoh2.c | Fast C2 Coherence | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffd1 | user/songxl/Mfd1.c | 1-D Optimized finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffd1_5 | user/songxl/Mfd1_5.c | 1-D Optimized finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffd2_10 | user/songxl/Mfd2_10.c | 2-D Fourth-order Optimized Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffd2bs | user/songxl/Mfd2bs.c | 2-D Fourth-order Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffd2d | user/jsun/Mfd2d.c | 2-D Fourth-order Finite-difference wave extrapolation with ABC | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffdac2d | user/zdzhang/Mfdac2d.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffdb1 | user/songxl/Mfdb1.c | 1-D Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffdip | user/pwd/Mfdip.c | 3D fast dip estimation by plane wave destruction | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffdtacc | user/jsun/Mfdtacc.c | 2-D Fourth-order Finite-difference wave extrapolation with timing option (no ABC) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffedchain | user/fomels/Mfedchain.c | Fast explicit diffusion as a chain | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffedchain1 | user/fomels/Mfedchain1.c | Fast explicit diffusion using chains - linear operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffedchain2 | user/fomels/Mfedchain2.c | Fast explicit diffusion as a chain (2-D) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffedchain21 | user/fomels/Mfedchain21.c | Fast explicit diffusion using chains - linear operator (2-D) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffermatrecursion | user/zone/Mfermatrecursion.c | 2D traveltime derivatives computation with the recursion from Fermat's principle (Sripanich and Fomel, 2017) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffd0 | user/songxl/Mffd0.c | 2-D FFD zero-offset migration: MPI + OMP | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffd1 | user/songxl/Mffd1.c | 1-D Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffd2_den_omp | user/songxl/Mffd2_den_omp.c | 2-D Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffd2_ps | user/songxl/Mffd2_ps.c | 2-D Fourier finite-difference wave extrapolation, point source | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffd2b_smsr | user/songxl/Mffd2b_smsr.c | 2-D Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffd2dehf | user/songxl/Mffd2dehf.c | 2-D Fourier finite-difference wave extrapolation, smooth point source, depress high frequency | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffd3d | user/junyan/Mffd3d.c | 3-D Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffdantti4b | user/songxl/Mffdantti4b.c | 2-D Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffdantti4b_rvr | user/songxl/Mffdantti4b_rvr.c | 2-D Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffdantti4b_smsr | user/songxl/Mffdantti4b_smsr.c | 2-D Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffdcos2b | user/songxl/Mffdcos2b.c | 2-D Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffdrtm | user/songxl/Mffdrtm.c | 2-D FFD RTM: MPI + OMP | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffdrtms | user/songxl/Mffdrtms.c | 2-D FFD isotropic RTM: MPI + OMP | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffdtti2 | user/songxl/Mffdtti2.c | 2-D Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffdv0b1 | user/songxl/Mffdv0b1.c | 1-D Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffft2 | user/fomels/Mfft2.c (+1) | Test 2-D Fourier transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffft3d | user/psava/Mfft3d.c | 3D FFT with centering and Hermitian scaling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftexp0 | user/fomels/Mfftexp0.c | 2-D FFT-based zero-offset exploding reflector modeling/migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftexp0a | user/fomels/Mfftexp0a.c | Two-step Lowrank 2-D zero-offset exploding reflector modeling/migration with adjoint | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftexp0adj | user/jsun/Mfftexp0adj.c | 2-D FFT-based zero-offset exploding reflector modeling/migration with adj flag for dot product test | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftexp0test | user/jsun/Mfftexp0test.c | 2-D FFT-based zero-offset exploding reflector modeling/migration (outputs time volume; can be used to generate movies) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftexp1 | user/fomels/Mfftexp1.c | 2-D FFT-based prestack exploding reflector modeling/migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftexp3 | user/fomels/Mfftexp3.c | 3-D FFT-based zero-offset exploding reflector modeling/migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftexpa | user/fomels/Mfftexpa.c | 2-D FFT-based zero-offset exploding reflector modeling/migration with adjoint | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftfwi_sparse_2d | user/zhiguang/Mfftfwi_sparse_2d.c | 2D frequency domain full waveform inversion with sparsity regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftone | user/fomels/Mfftone.c | Test 1-D Fourier transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfffttest | user/fomels/Mffttest.c | Test 3-D Fourier transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftwave1 | user/fomels/Mfftwave1.c | 1-D FFT wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftwave1dd | user/jsun/Mfftwave1dd.c | 1-D lowrank FFT wave extrapolation using real to complex to real fft (with wavelet injection) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftwave2 | user/fomels/Mfftwave2.c | Simple 2-D wave propagation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftwave2omp | user/jsun/Mfftwave2omp.c | Simple 2-D wave propagation with multi-threaded Kiss-FFT | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftwave2p | user/jsun/Mfftwave2p.c | Simple 2-D wave propagation with multi-threaded fftw3 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftwave2taper | user/jsun/Mfftwave2taper.c | Simple 2-D wave propagation with multi-threaded fftw3 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftwave3 | user/fomels/Mfftwave3.c | Simple 3-D wave propagation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftwave3omp | user/jsun/Mfftwave3omp.c | Simple 3-D wave propagation with multi-threaded kiss-fft | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftwave3p | user/jsun/Mfftwave3p.c | Simple 3-D wave propagation with multi-threaded fftw3 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffftxcor | user/psava/Mfftxcor.c | Fourier domain cross-correlation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffiledims | user/ivlad/Mfiledims.c | Computes number of dimensions and their values | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffileflush | user/ivlad/Mfileflush.c | Creates just the ascii header from parameters | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffileheader | user/slim/Mfileheader.c | dumps header information to the standard output. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffindintval | user/lcasasan/Mfindintval.c | Find a certain integer value position in an array [n1] | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffindmax1 | user/lcasasan/Mfindmax1.c | Find max value and its sampled position along fast dimension | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffindmaximum | user/zdzhang/Mfindmaximum.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffindmin2 | user/fomels/Mfindmin2.c | Find minimum in 2-D | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffindrefmax1 | user/yliu/Mfindrefmax1.c | Find the sampled position of max value after reference point along fast dimension. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffindwellcoord | user/yliu/Mfindwellcoord.c | Find well location by using well coordinates. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffindzeroendt | user/yliu/Mfindzeroendt.c | Find the position of first non-zero value along time axis. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffint | user/tharit/Mfint.c | Forward interpolation (1-D). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffint1 | user/nobody/Mfint1.c | 1-D spline interpolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffir | user/chen/Mfir.c | FIR filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffitcrs | user/roman/Mfitcrs.c | Input: T[m][h][t] and its sf-file  m[], Nm h[], Nh | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffitcrspicks | user/roman/Mfitcrspicks.c | Compute fitting of Non-hyperbolic CRS to first-arrivals T[m][h]. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffitnonhcrspicks | user/roman/Mfitnonhcrspicks.c | Compute fitting of Non-hyperbolic CRS to first-arrivals T[m][h]. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffitSine | user/jyan/MfitSine.c | fit a shifted sine curve | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffixdensity | user/jeff/Mfixdensity.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffkamopaco | user/nobody/Mfkamopaco.c | Azimuth moveout by log-stretch F-K operator. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffkoclet | user/yliu/Mfkoclet.c | 1-D seislet transform using omega-wavenumber offset continuation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffkoclet3 | user/yliu/Mfkoclet3.c | 2-D seislet transform using frequency-wavenumber offset-azimuth continuation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfflat3 | user/nobody/Mflat3.c | 3-D flattening (without picking). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfflatlinpiwrapper | user/dmerzlikin/Mflatlinpiwrapper.c | pi operator building wrapping test function flat gaussian weighting smoothing after pi | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfflatlinpiwrapper2d | user/dmerzlikin/Mflatlinpiwrapper2d.c | pi operator building wrapping test function flat gaussian weighting smoothing after pi | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffocus | user/fomels/Mfocus.c | Focusing indicator. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffourbreg2 | user/yliu/Mfourbreg2.c | Missing data interpolation in 2-D using Fourier Bregman shaping iteration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffourmis2 | user/yliu/Mfourmis2.c | Missing data interpolation in 2-D using Fourier transform and compressive sensing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffourvcd | user/nobody/Mfourvcd.c | Velocity continuation with differential semblance computation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffpocs2d | user/pyang/Mfpocs2d.c | 2-D Two-step POCS interpolation using a general Lp-norm optimization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffpocs3d | user/pyang/Mfpocs3d.c | 3-D Two-step POCS interpolation using a general Lp-norm optimization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffpow | user/fomels/Mfpow.c | Time/frequency power estimation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffraclr2 | user/jsun/Mfraclr2.cc | viscoacoustic | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffraclr2test | user/jsun/Mfraclr2test.cc | viscoacoustic | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffreqest | user/fomels/Mfreqest.c | Local frequency estimation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffreqintpef | user/nobody/Mfreqintpef.c | 1-D data regularization using freqlet transform and PEF frequencies | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffreqlet97 | user/nobody/Mfreqlet97.c | 1-D 9/7 freqlet transform | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffreqmig0 | user/llisiw/Mfreqmig0.c | Image interpolation coefficients estimation (single-arrival) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffreqreg | user/yliu/Mfreqreg.c | Local frequency interpolation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffreshape | user/yliu/Mfreshape.c | Nonstationary spectral balancing in frequency domain. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffrog | user/gee/Mfrog.c | Simple 2-D wave propagation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffrt | user/chen/Mfrt.c | Frequency domain Radon transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfftoper | user/llisiw/Mftoper.c | First-arrival Traveltime Tomography (linear operator) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffwi2d | user/pyang/Mfwi2d.c | Time domain full waveform inversion | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffwidir | user/zhiguang/Mfwidir.c | Update the conjugate direction in full waveform inversion | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffwigrad | user/zhiguang/Mfwigrad.c | 2D Gradient Calculation in Full Waveform Inversion | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffwiobj | user/zhiguang/Mfwiobj.c | Calculate the misfit fuction  in Full Waveform Inversion | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffwipe | user/zhiguang/Mfwipe.c | Phase encoding | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffwiupdate | user/zhiguang/Mfwiupdate.c | Update model with search direction and step length in FWI | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffxrna | user/gchliu/Mfxrna.c | Local prediction filter for complex numbers (n-dimensional). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffxspfdenoise2 | user/yliu/Mfxspfdenoise2.c | Random noise attenuation using 2D f-x streaming prediction filter. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffxspfint2 | user/yliu/Mfxspfint2.c | 2D missing data interpolation using f-x streaming prediction filter. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffxynpre | user/chenyk/Mfxynpre.c | FXY non-stationary predictive filtering (with the option of local processing windows). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffxynpre2 | user/chenyk/Mfxynpre2.c | FXY non-stationary predictive filtering (with the option of local processing windows). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffxyspf | user/yliu/Mfxyspf.c | 3D f-x-y streaming prediction filter (SPF) for interpolation/denoising. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffxyspfdenoise3 | user/yliu/Mfxyspfdenoise3.c | Random noise attenuation using 3D f-x-y streaming prediction filter. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sffxyspfint3 | user/yliu/Mfxyspfint3.c | 3D missing data interpolation using f-x-y streaming prediction filter. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgammapick2d | user/aklokov/Mgammapick2d.c | 2D picking for gamma=Vm/V panels | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgauss | user/nobody/Mgauss.c | Add a Gaussian anomaly to the data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgaussmooth | user/fomels/Mgaussmooth.c | Recursive Gaussian smoothing on the fast axis. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgausssource | user/zone/Mgausssource.c | Generate grid disk with gaussain amplitude for shooting portion of a wavefield. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgazdagz | user/nobody/Mgazdagz.c | Post-stack 2-D v(z) time modeling/migration with curved-ray phase-shift. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgbeamform | user/fomels/Mgbeamform.c | 2-D lateral smoothing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgenheaderallreceiver | user/zedong/Mgenheaderallreceiver.c | Generate the header file for all shot and receiver. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgenshotscyk | user/chenyk/Mgenshotscyk.c | Generate shots for FWI test | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgeoconvert | user/yliu/Mgeoconvert.c | 2-D regular geometry conversion | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgetattr | user/psava/Mgetattr.c | Output dataset attributes. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgetcregather | user/dirack/Mgetcregather.c | Build CRE gather given CMP X Offset CRE trajectory coordinates and interpolated data cube | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgetcretimecurve | user/dirack/Mgetcretimecurve.c | Calculate CRE traveltime curve t(m,h) given CRS zero-offset parameters (RN, RNIP, BETA) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgettype | user/ivlad/Mgettype.c | Displays numerical type of a dataset | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgpi3dzo | user/dmerzlikin/Mgpi3dzo.c | Gaussian weighting for ZO 3D case | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgravcon | user/yliu/Mgravcon.c | Continuation for gravity data by using FFT or intergral iteration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgreen | user/nobody/Mgreen.c | Phase-space Green\'s function from down-marching. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgroll | user/yliu/Mgroll.c | Add linear-chirp ground-roll noise to the data | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgsray | user/browaeys/Mgsray.c | Gauss Seidel iterative solver for phase space escape positions, angle and traveltime | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgsray2rays2d | user/roman/Mgsray2rays2d.c | Oriented zero-offset migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfgsrayvti | user/roman/Mgsrayvti.c | Gauss Seidel iterative solver for phase space escape positions, angle and traveltime | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfh2warp | user/luke/Mh2warp.c | Distance From Midpoint-squared warping. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhale | user/nobody/Mhale.c | 2-D synthetic model for multiple-arrival generation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhalfthr | user/chenyk/Mhalfthr.c | Half thresholding using exact-value or percentile thresholding. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhcascade | user/gee/Mhcascade.c | Multidimensional convolution cascade. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhconv | user/gee/Mhconv.c | Convolution of two helix filters. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhdecon | user/gee/Mhdecon.c | Random noise removal by deconvolution on a helix | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhdefd | user/psava/Mhdefd.c | Heat diffusion equation FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhdtrace | user/nobody/Mhdtrace.c | Multiple arrivals by depth marching. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfheal | user/aklokov/Mheal.c | Heal empty traces ddd | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfheat3 | user/gee/Mheat3.c | Finite-difference 3-D heat-flow equation using helix | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfheatexplitest | user/chenyk/Mheatexplitest.c | Solving 1-D heat equation using explicit finite difference | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfheatgmres1 | user/petsc/Mheatgmres1.c | Solution of 1-D heat equation with GMRES. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfheatimplitest | user/chenyk/Mheatimplitest.c | Solving 1-D heat equation using implicit finite difference | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhelloworld | user/zdzhang/Mhelloworld.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhelm2D_bornsyn | user/hzhu/Mhelm2D_bornsyn.c | 2D Born synthetic based on Helmholtz forward solver. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhelm2D_forward | user/hzhu/Mhelm2D_forward.c | 2D Helmholtz forward solver by LU factorization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhelm2D_fwi | user/hzhu/Mhelm2D_fwi.c | 2D Frequency Domain Full Waveform Inversion. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhelm2D_genrec | user/hzhu/Mhelm2D_genrec.c | Generate receiver file for Helmholtz solver. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhelm2D_genshot | user/hzhu/Mhelm2D_genshot.c | Generate shot file for Helmholtz solver. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhelm2D_lsm | user/hzhu/Mhelm2D_lsm.c | 2D Frequency Domain Least Squares Reverse Time Migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhelm2D_rtm | user/hzhu/Mhelm2D_rtm.c | 2D Frequency Domain Reverse Time Migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhelmlu | user/sparse/Mhelmlu.c | 2D Helmholtz solver by LU factorization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhelmmig | user/sparse/Mhelmmig.c | 2D frequency-domain migration with space-lag imaging condition. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhelmrhs | user/sparse/Mhelmrhs.c | Reconstruct right-hand side from wavefield. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhic2ang | user/psava/Mhic2ang.c | angle decomposition of CIPs | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhilbert | user/chenyk/Mhilbert.c | Compute hilbert transform using different methods. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhist2 | user/ivlad/Mhist2.c | Compute a 2-D histogram of integer- or float-valued input data | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhmiss | user/nobody/Mhmiss.c | Multi-dimensional missing data interpolation with shaping regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhomo3dtti | user/chengjb/Mhomo3dtti.c | Create a 3-D tilted TI model. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhorwrite | user/chen/Mhorwrite.c | save rsf data into horizon ASCII format, eq to dd form=ascii | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhpef | user/gee/Mhpef.c | Multi-dimensional PEF (prediction error filter) estimation on a helix. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhradon | user/chenyk/Mhradon.c | Time domain high-resolution hyperbolic Radon transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhshape | user/gee/Mhshape.c (+1) | Helical autoregressive shaping | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhslice | user/nobody/Mhslice.c | Extract horizons from data | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhv2d | user/yliu/Mhv2d.c | Velocity with heterogeneity convert to dip. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhwt3d | user/psava/Mhwt3d.c | 3-D Huygens wavefront tracing traveltimes | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfhyperdif | user/chenyk/Mhyperdif.c | Solving 1-D transportation equation using finite difference algorithm | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sficor | user/psava/Micor.c | Interferometric cross-correlation of time series (zero-lag output) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sficsp2d | user/seisinv/Micsp2d.c | 2-D inversion to common scattering-point gathers | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfidempatch | user/gee/Midempatch.c | Patching test. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfimagsrc | user/jsun/Mimagsrc.c | Convolution with a Ricker wavelet. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfimospray | user/gee/Mimospray.c | Inversion of constant-velocity nearest-neighbor inverse NMO. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfimray | user/fomels/Mimray.c | 2-D image ray tracing using HWT | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinitwave2 | user/jsun/Minitwave2.c | Complex 2-D wave propagation using initial condition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinjop2d | user/psava/Minjop2d.c | inject/extract in/from 2D wavefield | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinjop3d | user/psava/Minjop3d.c | inject/extract in/from 3D wavefield | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinmo3_ort | user/jingwei/Minmo3_ort.c | 3-D Inverse normal moveout using orthogonal parametrization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinstattr | user/yliu/Minstattr.c | Estimate of instantaneous attributes. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinstsnr | user/yliu/Minstsnr.c | Instantaneous signal-to-noise ratio (SNR) estimation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfint3d | user/psava/Mint3d.c | 3-D traveltime interpolation (from rays to Cartesian cube) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfintbin4 | user/yliu/Mintbin4.c | 5-D data binning. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfintegral | user/songxl/Mintegral.c | 1-D finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfintegral1 | user/xuxin/Mintegral1.c | integration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinterf | user/fomels/Minterf.c | Create an interferometric matrix | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinternalmult | user/yliu/Minternalmult.c | Generate internal multiples by using virtual seismic data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinterp2 | user/fomels/Minterp2.c | Multiple-arrival interpolation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinterpt | user/fomels/Minterpt.c | Multiple-arrival interpolation (yet another). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfintervalVTI | user/lcasasan/MintervalVTI.c | Interval/Effective VTI parameters from Effective/Interval profiles | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfintv2avg | user/zdzhang/Mintv2avg.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfintv2rms | user/zdzhang/Mintv2rms.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinvbin | user/gee/Minvbin.c | Data interpolation in 2-D slices using helix preconditioning. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinvbin1 | user/gee/Minvbin1.c | 1-D inverse interpolation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinvqfilt | user/yliu/Minvqfilt.c | Inverse Q filtering by using equivalent Q value in time-frequency domain. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinvrec1 | user/gee/Minvrec1.c | 1-D inverse interpolation with recursive filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinvtest | user/jingwei/Minvtest.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinvtest1 | user/jingwei/Minvtest1.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfinvwarp | user/nobody/Minvwarp.c | Invert a warping function. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfiphase | user/fomels/Miphase.c | Smooth estimate of instantaneous frequency. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfiq2eq | user/yliu/Miq2eq.c | Convert interval Q value to equivalent Q value | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfirays | user/llisiw/Mirays.c | Fast marching for image rays | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfisaac0 | user/zone/Misaac0.c | Zero-offset bending ray tracing in one-layered media | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfisaac1 | user/zone/Misaac1.c | Pre-stack bending ray tracing in one-layered media | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfisaac2 | user/zone/Misaac2.c | 2D Bending ray tracing in multi-layered media | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfisaac3 | user/zone/Misaac3.c | 3D Bending ray tracing in Multi-layered media | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfisoimpulse | user/guojian/Misoimpulse.c | Impulse response for plane-wave migration in tilted coordinates | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfisolr2 | user/fomels/Misolr2.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfisolr25 | user/zedong/Misolr25.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfisolr2p | user/zedong/Misolr2p.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfisolr3 | user/fomels/Misolr3.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfisolrsg1 | user/fangg/Misolrsg1.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfisolrsg2 | user/fangg/Misolrsg2.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfisomod | user/nobody/Misomod.c | 2D isotropic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfisoonewaypsdmlr | user/chengjb/Misoonewaypsdmlr.cc | 2-D One-way nonstationary phase-shift PSDM using low-rank approximation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfistinterp | user/pyang/Mistinterp.c | n-D IST interpolation using a generalized shrinkage operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfistpad | user/pyang/Mistpad.c | n-D IST interpolation using a generalized shrinkage operator and zero-padding | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfistseislet | user/pyang/Mistseislet.c | Analysis-based IST interpolation using seislet (2d validation) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfitrace | user/aklokov/Mitrace.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfitrack2d | user/psava/Mitrack2d.c | Datuming by 2D Green functions in constant media | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfitrack3d | user/psava/Mitrack3d.c | Datuming by 3D Green functions in constant media | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfiwarpsh | user/zone/Miwarpsh.c | Inverse 1-D warping. with shifted-linear interpolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfiwigrad | user/sparse/Miwigrad.c | Image-domain waveform tomography (gradient). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfiwihess | user/sparse/Miwihess.c | Image-domain waveform tomography (approximate Hessian). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfiwiiter | user/sparse/Miwiiter.c | Image-domain waveform tomography. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfiwiiter0 | user/sparse/Miwiiter0.c | Image-domain waveform tomography. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfiwilbfgs | user/sparse/Miwilbfgs.c | Image-domain waveform tomography (L-BFGS). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfiwinlcg | user/sparse/Miwinlcg.c | Image-domain waveform tomography (Non-linear CG). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfiwioper | user/sparse/Miwioper.c | Image-domain waveform tomography (linear operator). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfiwioper0 | user/sparse/Miwioper0.c | Image-domain waveform tomography (linear operator). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfiwipert | user/llisiw/Miwipert.c | Image-domain waveform tomography (image perturbation). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfjoiner | user/lcasasan/Mjoiner.c | Join two selected points along the first dimension | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfjudgechaos | user/yliu/Mjudgechaos.c | Judgement of chaos | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkarlistinterp | user/karl/Mkarlistinterp.c | n-D IST interpolation using a general Lp-norm optimization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkarlpocs | user/karl/Mkarlpocs.c | n-D POCS interpolation using a general Lp-norm optimization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkarman | user/browaeys/Mkarman.c | Estimation of von Karman autocorrelation 1D spectrum. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkarman2 | user/browaeys/Mkarman2.c | Estimation of von Karman autocorrelation 2D spectrum by nonlinear separable least squares. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkarmans | user/browaeys/Mkarmans.c | Inversion for von Karman autocorrelation 1D spectrum. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkdsort | user/fomels/Mkdsort.c | Sort entries based on k-D tree. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkdtree | user/fomels/Mkdtree.c | Test k-D tree algorithm. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkernel | user/mccowan/Mkernel.c | Test migration kernel. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkgdmo | user/nobody/Mkgdmo.c | Wavenumber-domain Gardner's DMO for regularly sampled 2-D data | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkhshot | user/effsilva/Mkhshot.c | Kirchhoff shot migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkine2dvti | user/chengjb/Mkine2dvti.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkir33 | user/parvaneh/Mkir33.c | Kirchhoff 3-D modeling with analytical Green's functions. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkirch | user/luke/Mkirch.c | if n, modeling, if y, migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkirchinvs | user/seisinv/Mkirchinvs.c | Kirchhoff 2-D post-stack least-squares time migration with sparse constrains. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkirdat | user/llisiw/Mkirdat.c | 2-D Pre-stack Kirchhoff redatuming. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkirdat0 | user/llisiw/Mkirdat0.c | 2-D Post-stack Kirchhoff redatuming. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkirdatsr | user/llisiw/Mkirdatsr.c | 2-D Pre-stack Kirchhoff redatuming. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkirmig | user/llisiw/Mkirmig.c | 2-D Prestack Kirchhoff depth migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkirmig0 | user/llisiw/Mkirmig0.c | 2-D Post-stack Kirchhoff depth migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkirmigsr | user/llisiw/Mkirmigsr.c | 2-D Prestack Kirchhoff depth migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkirmod_newton | user/zone/Mkirmod_newton.c | Kirchhoff 2-D/2.5-D modeling in layered media with bending ray tracing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkirmodcmp | user/nobody/Mkirmodcmp.c | Kirchhoff 3-D modeling with analytical Green's functions. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkkirmig | user/llisiw/Mkkirmig.c | 2-D Prestack Kirchhoff depth migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkkirmig0 | user/llisiw/Mkkirmig0.c | 2-D Post-stack Kirchhoff depth migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkolmog | user/gee/Mkolmog.c | Kolmogoroff spectral factorization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkron | user/fomels/Mkron.c | Kroneker product with square matrices | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfktmig | user/bash/Mktmig.c | Prestack time migration (2-D/3-D) for irregular data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfkuwahara | user/yliu/Mkuwahara.c | 1-D and 2-D Kuwahara filter. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflagrange | user/chenyk/Mlagrange.c | A forward interpolation using Lagrange method. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflaplace | user/songxl/Mlaplace.c | 2-D finite-difference Laplacian | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflaplace2 | user/songxl/Mlaplace2.c | 2-D Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflaps2d | user/psava/Mlaps2d.c | OpenMP lagged-products in the time-domain | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflaps3d | user/psava/Mlaps3d.c | OpenMP lagged-products in the time-domain | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflcf | user/yliu/Mlcf.c | Estimate local centroid frequency. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflcfseq | user/yliu/Mlcfseq.c | Estimate equivalent Q value based on a reference layer by using Local centroid frequency shift (LCFS) method. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflcfsiq | user/yliu/Mlcfsiq.c | Estimate interval Q value between every two adjacent time sampling points by using Local centroid frequency shift (LCFS) method. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfldip | user/chen/Mldip.c | dip estimation by line interpolating pwd | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfleftsize | user/ivlad/Mleftsize.c | Computes Ni+1 x Ni+2 x ... | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflesolver | user/chenyk/Mlesolver.c | Linear equations solver using Gauss Elimination | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflevint | user/gee/Mlevint.c | Leveler inverse interpolation in 1-D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflevint2 | user/nobody/Mlevint2.c | Leveler inverse interpolation in 2-D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflfd2_25b | user/songxl/Mlfd2_25b.c | 2-D Fourth-order Optimized Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflfdanc2_25 | user/songxl/Mlfdanc2_25.cc | from eta to q | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflfdc1 | user/songxl/Mlfdc1.cc | Next | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflfdc2_25 | user/songxl/Mlfdc2_25.cc | Next | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflfdc2_7 | user/songxl/Mlfdc2_7.cc | Next | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflfdcsgm2 | user/fangg/Mlfdcsgm2.cc | using weighted least square | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflfdcsgm2_5 | user/fangg/Mlfdcsgm2_5.cc | using weighted least square | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflfdcsgm2_all | user/fangg/Mlfdcsgm2_all.cc | using weighted least square | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflfdcsgm2c | user/fangg/Mlfdcsgm2c.cc | using weighted least square | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflfdcsgm2s | user/fangg/Mlfdcsgm2s.cc | using weighted least square | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflfdp1 | user/songxl/Mlfdp1.cc | Next | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflfdp2 | user/songxl/Mlfdp2.cc | Next | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflfdsgm2 | user/fangg/Mlfdsgm2.c | 2-D Lowrank Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflffd1_10 | user/songxl/Mlffd1_10.c | 1-D Lowrank Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflffd2_an_25 | user/songxl/Mlffd2_an_25.c | 2-D Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflffd2an25 | user/songxl/Mlffd2an25.c | 2-D Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflffd2anc | user/songxl/Mlffd2anc.c | 2-D Fourier finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflffdan | user/songxl/Mlffdan.cc | from eta to q | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflffdanc | user/songxl/Mlffdanc.cc | for (int b=0; b<nc; b++) { | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflffdand | user/songxl/Mlffdand.cc | from eta to q | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflfftexp0 | user/fomels/Mlfftexp0.c | 2-D FFT-based zero-offset exploding reflector modeling/migration as linear operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflight | user/gee/Mlight.c | Apply 2-D directional high-pass to highlight data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflineslope | user/yliu/Mlineslope.c | Calculate the slope by fitting a line to a set of points in 2-D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflinmig2 | user/dmerzlikin/Mlinmig2.c | 2-D Kirchhoff time migration with antialiasing with adjoint flag. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflinmig3 | user/dmerzlikin/Mlinmig3.c | 3-D Kirchhoff time migration with antialiasing with adjoint flag. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflinpi | user/dmerzlikin/Mlinpi.c | 3D Path-Summation Integral Operator as a Linear Filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflinpipwd2d | user/dmerzlikin/Mlinpipwd2d.c | pi operator building wrapping test function flat gaussian weighting smoothing after pi | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflinpipwd2dca | user/dmerzlikin/Mlinpipwd2dca.c | pi operator building wrapping test function flat gaussian weighting smoothing after pi | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflinpwd | user/dmerzlikin/Mlinpwd.c | Chain of 3D Path Integral, Azimuthal Plane-Wave Destruction and Kirchhoff migration (based on sfmig3) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflint1 | user/gee/Mlint1.c | Linear interpolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflintshape2d | user/karl/Mlintshape2d.c | find grid that will Linearly INTerpolate the input.  Use SHAPEing in 2D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflistminmax | user/jennings/Mlistminmax.c | Construct incremental minimum or maximum lists from an RSF file. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfllpf | user/fomels/Mllpf.c | Local prediction filter (n-dimensional) with an adjoint flag. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflmo | user/ivlad/Mlmo.c | Linear move-out in the frequency domain | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflocalskew | user/fomels/Mlocalskew.c | Rotate phase and compute local skewness. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflocalsnr | user/yliu/Mlocalsnr.c | Local signal-to-noise ratio (SNR) estimation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfloconv | user/lcasasan/Mloconv.c | Local internal and transient convolution (N-dimensional). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflocorr | user/yliu/Mlocorr.c | Local correlation measure between two datasets. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflocov | user/fomels/Mlocov.c | Local covariance filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflomatch | user/lcasasan/Mlomatch.c | Local Matched filter for coherent noise removal (1-D, 2-D, and 3-D). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflopef | user/gee/Mlopef.c | Local Prediction-Error Filter (1-D, 2-D, and 3-D). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflosignoi | user/gee/Mlosignoi.c | Local signal and noise separation (N-dimensional). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflpad2 | user/yliu/Mlpad2.c | 2D pad and interleave traces. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflpef | user/gee/Mlpef.c | Find PEF on aliased traces. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflpf | user/fomels/Mlpf.c | Local prediction filter (n-dimensional). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflpf2 | user/yliu/Mlpf2.c | 2D Local prediction filter. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflpfdenoise1 | user/yliu/Mlpfdenoise1.c | 1D denoising using edge-preserving local polynomial fitting (ELPF). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflpfdenoise2 | user/yliu/Mlpfdenoise2.c | 2D denoising using edge-preserving local polynomial fitting (ELPF). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflpfL1 | user/lcasasan/MlpfL1.c | Local prediction filter (n-dimensional) in L1 norm. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflphcoef | user/chen/Mlphcoef.c | Linear PHase filter COEFficients | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflphfreq | user/chen/Mlphfreq.c | frequency response of linear phase approximators | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflr2invs | user/fomels/Mlr2invs.c | Post-stack 2D LSRTM Two-step Lowrank with preconditioning | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflrlsrtm2mpi | user/jsun/Mlrlsrtm2mpi.c | 2-D Low-rank One-step Least Pre-stack Reverse-Time-Migration in the complex domain (both img and data are complex valued) without MPI... | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sflrmatrix | user/lexing/Mlrmatrix.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflrmf | user/yliu/Mlrmf.c | Local radial median filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflrmig0 | user/fomels/Mlrmig0.c | Fast zero-offset time migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflroslsrtm2 | user/jsun/Mlroslsrtm2.c | 2-D Low-rank One-step Pre-stack Reverse-Time-Migration in the complex domain (both img and data are complex valued) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflrosrtm2 | user/jsun/Mlrosrtm2.c | 2-D Low-rank One-step Pre-stack Reverse-Time-Migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflrosrtm2dbg | user/jsun/Mlrosrtm2dbg.c | 2-D Low-rank One-step Pre-stack Reverse-Time-Migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflrtti2de | user/jsun/Mlrtti2de.c | 2-D two-components wavefield modeling using original elastic displacement wave equation in TTI media by lowrank method. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflrvc0 | user/fomels/Mlrvc0.cc | space index | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflrwave2 | user/jsun/Mlrwave2.c | 2-D FFT-based (point src) wave propagation and its adjoint | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflsdmo | user/seisinv/Mlsdmo.c | Kirchhoff least-squares DMO with antialiasing by reparameterization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflsfit | user/fomels/Mlsfit.c | Simple least-squares regression. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflsinterp2d | user/pyang/Mlsinterp2d.c | Least-squares interpolation for 2D validition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflskernel | user/luke/Mlskernel.c | find kernel for convolution in ls sense, this is assuming 3 dimensional data and a 2d kernel | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflslfdc1 | user/fangg/Mlslfdc1.cc | Weighted least square Lowrank FD coefficient on staggered grid (optimized) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflsLU | user/zhiguang/MlsLU.c | Local similarity filter (direct solving) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflsm_dsr2d | user/seisinv/Mlsm_dsr2d.c | 2-D prestack least-squares migration with split-step DSR. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflsmig3 | user/dmerzlikin/Mlsmig3.c | Least-Squares 3D Path-Summation Integral, Azimuthal Plane-Wave Destruction and Kirchhoff Modeling/Migration Chain of Operators | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflspiazpwdmig3 | user/dmerzlikin/Mlspiazpwdmig3.c | Least-Squares 3D Path-Summation Integral, Azimuthal Plane-Wave Destruction and Kirchhoff Modeling/Migration Chain of Operators | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflspiazpwdmig32 | user/dmerzlikin/Mlspiazpwdmig32.c | Least-Squares 3D Path-Summation Integral, Azimuthal Plane-Wave Destruction and Kirchhoff Modeling/Migration Chain of Operators. Shaping is p | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflsprtm2d | user/pyang/Mlsprtm2d.c | least-squares prestack RTM in 2-D | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflsrtm2d | user/pyang/Mlsrtm2d.c | 2-D zero-offset least-squares reverse time migration (LSRTM) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflstk | user/psava/Mlstk.c | Local slant stacks (2D) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflstri2d | user/jsun/Mlstri2d.c | 2-D passive seismic RTM and its adjoint | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfltftn | user/chenyk/Mltftn.c | Non-stationary local time-frequency transform (NLTFT). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfltfts | user/chenyk/Mltfts.c | Stationary local time-frequency transform (SLTFT). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflum | user/yliu/Mlum.c | 1D LUM filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflum2 | user/yliu/Mlum2.c | 2D LUM filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflumsharpener | user/yliu/Mlumsharpener.c | 1D LUM sharpener filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflumsmoother | user/yliu/Mlumsmoother.c | 1D LUM smoother filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflwefd1 | user/nobody/Mlwefd1.c | linearized acoustic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sflwefd2d | user/psava/Mlwefd2d.c | linearized acoustic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmake_ix_indx | user/karl/Mmake_ix_indx.c | MAKE Iline Xline INDX files for quick 3D data subsets (superbins) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmap2cloud2D | user/psava/Mmap2cloud2D.c | reformat gridded maps to point clouds | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmap2cloud3D | user/psava/Mmap2cloud3D.c | reformat gridded maps to point clouds | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmap2list | user/nobody/Mmap2list.c | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmarchenko | user/fbroggin/Mmarchenko.c | Marchenko-Wapenaar-Broggini iterative scheme | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmask2pick | user/ediazp/Mmask2pick.c | Hungs a 1d velocity function from the Water bottom. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmaskdag | user/mehdi/Mmaskdag.c | Mask design for dip angle gathers. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmaskdagmef | user/mehdi/Mmaskdagmef.c | Mask for Dip Angle Gathers | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmaskinv | user/gee/Mmaskinv.c | Missing data interpolation using one or two prediction-error filters. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmaskval | user/bash/Mmaskval.c | Mask values inside or outside of a range. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmatch1d | user/lcasasan/Mmatch1d.c | 1D Least-Sqaure Adaptive Matched-Filter for Multiple Suppression | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmatchoper | user/yliu/Mmatchoper.c | Local matching-radon operator. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmatlr | user/chenyk/Mmatlr.c | Flip a matrix | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmatoper | user/chenyk/Mmatoper.c | Matrix algebra operation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmatrix | user/fangg/Mmatrix.c | multiply, for Matrix | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmcaseislet | user/pyang/Mmcaseislet.c | Morphological component analysis using 2-D Seislet transform | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmcbmcgauss | user/browaeys/Mmcbmcgauss.c | Monte Carlo integration of cos(2t).P(x1,x2).P(y1,y2) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfMCCCnew | user/jeff/MMCCCnew.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmdfd4 | user/chen/Mmdfd4.c | 2D finite difference modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmdip | user/pwd/Mmdip.c | 2-D multiscale dip estimation by plane wave destruction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmedian | user/fomels/Mmedian.c | Compute median on the first axis. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmffit | user/fomels/Mmffit.c | Fitting multi-focusing approximations | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmflt | user/chen/Mmflt.c | 3D Recursive median filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmig2 | user/nobody/Mmig2.c (+1) | 2-D Kirchhoff time migration with antialiasing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmig2pwd | user/dmerzlikin/Mmig2pwd.c | combination of mig2 Kirchhoff migration nad PWD filtering | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmig2s | user/dmerzlikin/Mmig2s.c | 2-D Prestack Kirchhoff time migration with antialiasing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmig2semb | user/dmerzlikin/Mmig2semb.c | 2-D Prestack Kirchhoff time migration with antialiasing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmig45 | user/nobody/Mmig45.c | Finite-difference modeling/migration: 15- and 45-degree approximation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfminmax | user/jennings/Mminmax.c | Element by element minimum or maximum of two RSF files. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmisfit_warpscan | user/hzhu/Mmisfit_warpscan.c | Multicomponent data registration analysis. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmisfit_warpscan_deriv | user/hzhu/Mmisfit_warpscan_deriv.c | Derivatives of local similarity function. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmisif | user/gee/Mmisif.c | Find MISSing Input values and Filter in 1-D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmiss | user/gee/Mmiss.c | Multi-dimensional missing data interpolation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmiss1 | user/gee/Mmiss1.c | Missing data interpolation in 1-D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmiss3 | user/fomels/Mmiss3.c | Missing data interpolation (N-dimensional) using shaping regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmiss4 | user/yliu/Mmiss4.c | Missing data interpolation with adaptive PEFs. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmiss43 | user/yliu/Mmiss43.c | 3-D missing data interpolation with adaptive PEFs. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmkcmp | user/yliu/Mmkcmp.c | Make a synthtic two-layer CMP gather with known t0 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmkrcv | user/llisiw/Mmkrcv.c | Make topography mask / receiver list / record list for first-arrival traveltime tomography | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmlm | user/yliu/Mmlm.c | 2D Multistage median filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmlwm | user/yliu/Mmlwm.c | 2D Multistage weighted median filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmms1dexp | user/fangg/Mmms1dexp.c | 1D method of manufactured solution using Gaussian pulsa | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmmssrc | user/fangg/Mmmssrc.c | Source for the method of manufactured solution | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmmssrc1 | user/fangg/Mmmssrc1.c | 1D Source for the method of manufactured solution | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmodatten1 | user/yliu/Mmodatten1.c | 1D attenuation modeling according to modified Kolsky model. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmodelcreate | user/jeff/Mmodelcreate.c | Create a dipping layer model for HTI testing purposes.  Has fixed velocity structure, but can change dip of layer and degree of anisotropy. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmodeling2d | user/pyang/Mmodeling2d.c | 2-D forward modeling to generate shot records | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmodtraceq | user/yliu/Mmodtraceq.c | Generate single trace with Q attenuation for viscoelastic media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmorph | user/fomels/Mmorph.c | Morphological operations on binary images | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmpi | system/main/mpi.c | MPI wrapper for embarassingly parallel jobs. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpiafdfwi2d | user/chenyk/Mmpiafdfwi2d.c | 2D Visco-acoustic Forward Modeling, FWI, and RTM based on SLS model | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpiafdfwi3d | user/chenyk/Mmpiafdfwi3d.c | 3D Visco-acoustic Forward Modeling, FWI, and RTM based on SLS model | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpicfftrtm | user/jsun/Mmpicfftrtm.cc | head files aumatically produced from C programs | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpicfftrtm3 | user/jsun/Mmpicfftrtm3.cc | head files aumatically produced from C programs | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpictshiftlr | user/zhiguang/Mmpictshiftlr.c | Correct time-shift gathers with two-step lowrank propagator | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpidfwi | user/zhiguang/Mmpidfwi.c | Variable-density acoustic Forward Modeling, FWI, and RTM | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpidip2 | user/zhiguang/Mmpidip2.c | 2-D dip estimation by plane wave destruction with MPI parallelization. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpiencode | user/cwp/Mmpiencode.c | shot encoding with arbitrary phase and amplitude weights using MPI on a distributed cluster | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpiewertm | user/jsun/Mmpiewertm.c | 2-D two-components elastic wavefield modeling operators with lowrank approximation. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpifd2d | user/zhiguang/Mmpifd2d.c | Acoustic wave equation forward modeling with MPI and OpenMP | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpifdlsrtm | user/zhiguang/Mmpifdlsrtm.c | 2-D prestack reverse time migration and its adjoint with MPI for full coverage | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpiffdrtmto | user/songxl/Mmpiffdrtmto.c | 2-D FFD RTM: MPI + OMP | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpifftexp1 | user/jsun/Mmpifftexp1.c | 2-D FFT-based prestack exploding reflector modeling/migration | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpifftexp1kiss | user/jsun/Mmpifftexp1kiss.c | 2-D FFT-based prestack exploding reflector modeling/migration | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpifwi | user/pyang/Mmpifwi.c | Time domain full waveform inversion using MPI parallel programming | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpifwigrad | user/zhiguang/Mmpifwigrad.c | Calculate acoustic FWI gradient with the prepared adjoint source | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpifwigradlr | user/zhiguang/Mmpifwigradlr.c | Conventional FWI misfit and gradient calculation using one-step low-rank wave extrapolation | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpignfwi | user/zhiguang/Mmpignfwi.c | Acoustic FWI using Gauss-Newton optimization | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpihello | user/bash/Mmpihello.c | MPI example, summation of vectors c = a + b | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpikirmodnewton | user/zone/Mmpikirmodnewton.c | Kirchhoff 2-D/2.5-D modeling in layered media with bending ray tracing. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpilrmodel | user/zhiguang/Mmpilrmodel.c | One-step lowrank modeling | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpilrrtm | user/zhiguang/Mmpilrrtm.c | 2-D Low-rank One-step Reverse-Time-Migration (simultaneous sources data and incomplete data) | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpilrrtm_ts | user/zhiguang/Mmpilrrtm_ts.c | One-step lowrank RTM with time-shift imaging condition | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpilsLU | user/zhiguang/MmpilsLU.c | Local similarity filter (solving with band matrix LU decomposition and parallelization) | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpilsrtm | user/jsun/Mmpilsrtm.c | 2-D Low-rank One-step Least Pre-stack Reverse-Time-Migration in the complex domain (both img and data are complex valued) | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpilsrtmcg | user/jsun/Mmpilsrtmcg.c | 2-D Low-rank One-step Least-square Pre-stack Reverse-Time-Migration using CG in the complex domain (both img and data are complex valued) | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpilsrtmgmres | user/jsun/Mmpilsrtmgmres.c | 2-D Low-rank One-step Least Pre-stack Reverse-Time-Migration in the complex domain (both img and data are complex valued) | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpimatmul | user/sujith/Mmpimatmul.c | Matrix-vector multiplication using MPI | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpipaint2 | user/zhiguang/Mmpipaint2.c | 2-D painting by plane-wave construction with MPI parallelization. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpipfwi | user/jsun/Mmpipfwi.c | Visco-acoustic Forward Modeling, FWI, and RTM based on SLS model | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpiprertm2d | user/zhiguang/Mmpiprertm2d.c | 2-D prestack reverse-time migration and its adjoint with MPI | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpipsp | user/hzhu/Mmpipsp.cc (+1) | Parallel Sweeping Preconditioner (PSP): a distributed-memory implementation | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpiqfwi | user/zhiguang/Mmpiqfwi.c | Visco-acoustic (SLS) Forward Modeling, FWI, and RTM | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpiqrtm | user/jsun/Mmpiqrtm.c | 2-D Low-rank One-step Least Pre-stack Reverse-Time-Migration in the complex domain (both img and data are complex valued) | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpircvrtm | user/jsun/Mmpircvrtm.c | 2-D Low-rank One-step Least Pre-stack Reverse-Time-Migration in the complex domain (both img and data are complex valued) | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpirfwigrad | user/zhiguang/Mmpirfwigrad.c | Calculate acoustic Reflection FWI gradient with the prepared adjoint source (velocity-impedance scale separation) | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpirtmiso | user/xuxin/Mmpirtmiso.c | isotropic reverse-time migration | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpirtmop | user/jsun/Mmpirtmop.c | 2-D Low-rank One-step Least Pre-stack Reverse-Time-Migration in the complex domain (both img and data are complex valued) | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpirtmvti | user/xuxin/Mmpirtmvti.c | VTI reverse-time migration | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpisfwi | user/zhiguang/Mmpisfwi.c | Acoustic Forward Modeling, FWI, and RTM (FWI has the options of seislet regularization, smoothing kernels, simultaneous source, and static p | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpisglrrtm2 | user/zhiguang/Mmpisglrrtm2.c | Paralleled stagger-grid lowrank RTM modified based on sfsglfdrtm2 (serial program) | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpistack | user/cwp/Mmpistack.c | stacks rsf files of the same dimensionality using mpi | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpitransp | user/hwang/Mmpitransp.c | Large rectangular matrix in-place transpose with MPI | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpiwave2 | user/jsun/Mmpiwave2.c | Complex 2-D wave propagation (with multi-threaded FFTW3) | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpiwave2kiss | user/jsun/Mmpiwave2kiss.c | Complex 2-D wave propagation (with multi-threaded FFTW3) | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpiwave3 | user/jsun/Mmpiwave3.c | Simple 3-D lowrank onestep wave propagation | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmpiwave3kiss | user/jsun/Mmpiwave3kiss.c | Simple 3-D lowrank onestep wave propagation | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfmshots | user/pyang/Mmshots.c | 2-D prestack forward modeling using sponge ABC using 4-th order FD | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmsmiss | user/gee/Mmsmiss.c | Multiscale missing data interpolation (N-dimensional). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmspef | user/gee/Mmspef.c | Multi-scale PEF estimation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmtm | user/yliu/Mmtm.c | 1-D and 2-D modified-trimmed-mean (MTM) filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmtres | user/yliu/Mmtres.c | Calculate apparent resistivity and phase of MT data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmulawefd2d | user/chenyk/Mmulawefd2d.c | 2D multisource acoustic time-domain FD modeling for testing | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmulticheck | user/ivlad/Mmulticheck.c | Check whether all values in a dataset are a multiple of a factor or not | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmultiple | user/yliu/Mmultiple.c | 2-D shot gather multiple prediction (SRMP) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmultmask | user/lcasasan/Mmultmask.c | Create a data mask using multiple muting curve from MRKE | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmutter3 | user/chenyk/Mmutter3.c (+1) | 3D mutter (only linear). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmvo | user/yliu/Mmvo.c | Calculate MVO and PVO curve of CSEM data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmvo1 | user/yliu/Mmvo1.c | Calculate MVO and PVO curve of CSEM data (another version). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmwni2d | user/pyang/Mmwni2d.c | 2-D bandlimited minimum weighted-norm interpolation (MWNI) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmyradon2 | user/pyang/Mmyradon2.c | Linear/parabolic radon transform frequency domain implementation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmysnr | user/pyang/Mmysnr.c | print out signal-to-noise ratio in decibel (dB) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfmythresh | user/pyang/Mmythresh.c | Generalized thresholding operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnconv | user/fomels/Mnconv.c | Non-stationary convolution | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfndecon | user/yliu/Mndecon.c | Random noise removal by nonstationary deconvolution | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfndix | user/reem/Mndix.c | Convert RMS to interval velocity using LS and shaping regularization with non-stationary smoothing | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfndsmooth | user/reem/Mndsmooth.c | N-D non-stationary triangle smoothing derivative. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnfill | user/nobody/Mnfill.c | Fill holes (nearest-neighbor) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnfmiss | user/gchliu/Mnfmiss.c | Missing data interpolation in freq domain. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnhcrssurf | user/dirack/Mnhcrssurf.c | Version 1.0 - Build Non-Hyperbolic CRS approximation surface giver RN, RNIP and BETA parameters. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnhelicon | user/gee/Mnhelicon.c | Non-stationary helix convolution and deconvolution. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnlm1 | user/chenyk/Mnlm1.c | 1D non-local median filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnlm2 | user/chenyk/Mnlm2.c | 2D non-local median filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnmo3gmafit | user/zone/Mnmo3gmafit.c | 3D NMO GMA  linearized operator preparation for lsfit | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnmo3gmaprep | user/zone/Mnmo3gmaprep.c | 3D NMO GMA  linearized operator preparation for lsfit | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnmo3mcmc | user/zone/Mnmo3mcmc.c | 3D NMO GMA MCMC inversion with Metropolis rule (Mosegaard and Tarantola, 1995) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnmo3mcmcspiral | user/zone/Mnmo3mcmcspiral.c | 3D NMO GMA MCMC inversion for spiral sorted gather with Metropolis rule (Mosegaard and Tarantola, 1995) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnmopicks | user/sujith/Mnmopicks.c | Manual NMO picks pairs (ti, vi) are interpolated to 1D | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnmova2 | user/nobody/Mnmova2.c | Adjoint flag | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnmradon | user/yliu/Mnmradon.c | Nonstationary-matching Radon transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnmult | user/yliu/Mnmult.c | Multiplication with nonstationary filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnnint | user/fomels/Mnnint.c | Natural neighbor interpolation (2-D) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnnshape | user/fomels/Mnnshape.c | 2-D irregular data interpolation using natural neighbors and shaping regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnnshapet | user/fomels/Mnnshapet.c | 2-D irregular data interpolation of traces using natural neighbors and shaping regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnonloc | user/yliu/Mnonloc.c | Non-local (Bilateral) smoothing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnorm2 | user/jeff/Mnorm2.c | Computes square of L-2 norm in double precision. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnormalize | user/luke/Mnormalize.c | Normalization of data batches up to a given axis. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnorsar | user/urdaneta/Mnorsar.c | Traveltime and amplitude estimation using wavefront construction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnpef | user/gee/Mnpef.c | Estimate Non-stationary PEF in N dimensions. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnpef5 | user/chenyk/Mnpef5.c | Estimate adaptive nonstationary PEF on aliased traces (5D). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnpef5_recon | user/chenyk/Mnpef5_recon.c | 5-D missing data interpolation with non-stationary PEFs. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnshape | user/yliu/Mnshape.c | Nonstationary autoregressive shaping | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnsmooth | user/fomels/Mnsmooth.c | N-D non-stationary smoothing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnsmooth1 | user/fomels/Mnsmooth1.c | 1-D non-stationary smoothing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfnxtfftn | user/songxl/Mnxtfftn.c | Look For next FFT number | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfoclet | user/yliu/Moclet.c | Seislet transform in log-stretched frequency-offset-midpoint domain | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfocparcel | user/fomels/Mocparcel.c | Patching test for out-of-core patching. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfoctentwt | user/fomels/Moctentwt.c | Tent-like weight for out-of-core patching. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfodip | user/chen/Modip.c | omnidirectional dip estimation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfodip2 | user/nobody/Modip2.c (+1) | 2-D dip estimation by omnidirectional plane-wave destruction | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfofd1 | user/songxl/Mofd1.c | 1-D Optimized finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfofd1_5 | user/songxl/Mofd1_5.c | 1-D Optimized finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfofd2_10 | user/songxl/Mofd2_10.c | 2-D Fourth-order Optimized Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfofd2_13 | user/songxl/Mofd2_13.c | 2-D Fourth-order Optimized Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfofd2_25 | user/songxl/Mofd2_25.c | 2-D Fourth-order Optimized Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfofd2_5 | user/songxl/Mofd2_5.c | 2-D Fourth-order Optimized Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfofd2_7 | user/songxl/Mofd2_7.c | 2-D Fourth-order Optimized Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfofd2_test | user/jsun/Mofd2_test.c | 2-D Fourth-order Optimized Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfoff2abs | user/psava/Moff2abs.c | Transform vector-offset to absolute-offset | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfoff2abs2 | user/nobody/Moff2abs2.c | Transform vector-offset to absolute-offset | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfoff2abs3 | user/psava/Moff2abs3.c | Transform vector-offset to absolute-offset | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfofilp | user/fomels/Mofilp.c | 2-D missing data interpolation by differential offset continuation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfofpwd | user/pwd/Mofpwd.c | Objective function of dip estimation with PWD filters. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfofpwd2 | user/pwd/Mofpwd2.c | Objective function of two dips estimation with PWD filters. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfofsemb | user/fomels/Mofsemb.c | Objective function of dip estimation with semblance. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfoneapp | user/fangg/Moneapp.cc | Staggered grid Lowrank FD coefficient with sigma approximation to improve its stablility | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfopame2d | user/junyan/Mopame2d.c | 2-D opam for elastic wave modeling and vector field decompostion | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfopame2dckxx | user/junyan/Mopame2dckxx.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfopame2dckxz | user/junyan/Mopame2dckxz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfopame2dckzz | user/junyan/Mopame2dckzz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfopoti2d | user/junyan/Mopoti2d.c | Modeling of pure acoustic wave in 2-D transversely isotropic meida using optimized pseudo-Laplacian operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfopoti3d | user/junyan/Mopoti3d.c | Modeling of pure acoustic wave in 3-D transversely isotropic meida using optimized pseudo-Laplacian operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfopsmigrk | user/roman/Mopsmigrk.c | Shot-recorder Oriented prestack migration data is (shots x recs x time). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfopwd2 | user/nobody/Mopwd2.c (+1) | 2-D omnidirectional plane-wave destruction | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sforientation | user/chen/Morientation.c | orientation estimation by structural gradient tensor | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sformatrix | user/songxl/Mormatrix.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sforp | user/songxl/Morp.c | 2-D 10th-order Finite-difference dispersion | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfort3de | user/chengjb/Mort3de.c | 3-D three-components wavefield modeling using elastic wave equation in tilted ORT media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfort3delasticlrsep | user/chengjb/Mort3delasticlrsep.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfort3delrsep | user/chengjb/Mort3delrsep.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfort3devectorlrkspace_double | user/chengjb/Mort3devectorlrkspace_double.cc | 3-D two-components elastic wavefield extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfort3dhomodevcK | user/chengjb/Mort3dhomodevcK.c | Correct projection deviation in K-domian for 3-D pseudo-pure P-wave field in homogeneous ORT media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfort3dhomodevcTemp | user/chengjb/Mort3dhomodevcTemp.c | Correct projection deviation in K-domian for 3-D pseudo-pure P-wave field in homogeneous ORT media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfort3dhomodevcX | user/chengjb/Mort3dhomodevcX.c | Correct projection deviation in X-domian for 3-D pseudo-pure P-wave field in homogeneous ORT media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfort3dhomodevK | user/chengjb/Mort3dhomodevK.c | 3D three-components projection deviation correction operators calculation in | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfort3dhomodevX | user/chengjb/Mort3dhomodevX.c | 3D three-components projection deviation correction operators calculation in | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfort3dpseudop | user/chengjb/Mort3dpseudop.c | 3-D three-components wavefield modeling using pseudo-pure mode P-wave equation in tilted ORT media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfort3dpseudophomo | user/chengjb/Mort3dpseudophomo.c | 3-D three-components wavefield modeling using pseudo-pure mode P-wave equation in tilted ORT media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfort3dpseudoplrsep | user/chengjb/Mort3dpseudoplrsep.cc | 3-D three-components wavefield modeling based on pseudo-pure P-wave equation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfort3dseplr | user/chengjb/Mort3dseplr.c | Correct projection deviation for 3-D pseudo-pure P-wave field in ORT media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sforthoa | user/chenyk/Morthoa.c | Accelerated local orthogonalization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sforthoEPlr | user/jsun/MorthoEPlr.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sforthoES2lr | user/jsun/MorthoES2lr.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sforthoESlr | user/jsun/MorthoESlr.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sforthol | user/chenyk/Morthol.c | Local signal-and-noise orthogonalization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sforthollr | user/songxl/Morthollr.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfortholr | user/songxl/Mortholr.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfortholr3 | user/jsun/Mortholr3.cc | double x = cc1*(x0*cc2+y0*ss2)-ss1*z0; | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfortholrzone | user/jsun/Mortholrzone.cc | from degrees to radians | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sforthon | user/chenyk/Morthon.c | Non-stationary orthogonalization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sforthonc | user/chenyk/Morthonc.c | Non-stationary orthogonalization for complex value | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sforthowave | user/songxl/Morthowave.c | Simple 3-D wave propagation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfortiltEPlr | user/jsun/MortiltEPlr.cc | double x2=kx[j]*kx[j]; | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfortiltES2lr | user/jsun/MortiltES2lr.cc | from degrees to radians | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfortiltESlr | user/jsun/MortiltESlr.cc | from degrees to radians | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfortllr | user/songxl/Mortllr.cc | float x=kx[j]*kx[j]; | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfortlr | user/songxl/Mortlr.cc | from degrees to radians | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam2dckxx | user/junyan/Mosam2dckxx.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam2dckxxxx | user/junyan/Mosam2dckxxxx.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam2dckxxxz | user/junyan/Mosam2dckxxxz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam2dckxxzz | user/junyan/Mosam2dckxxzz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam2dckxzzz | user/junyan/Mosam2dckxzzz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam2dckzz | user/junyan/Mosam2dckzz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam2dckzzzz | user/junyan/Mosam2dckzzzz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckxx | user/junyan/Mosam3dckxx.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckxxxx | user/junyan/Mosam3dckxxxx.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckxxxy | user/junyan/Mosam3dckxxxy.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckxxxz | user/junyan/Mosam3dckxxxz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckxxyy | user/junyan/Mosam3dckxxyy.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckxxyz | user/junyan/Mosam3dckxxyz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckxxzz | user/junyan/Mosam3dckxxzz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckxy | user/junyan/Mosam3dckxy.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckxyyy | user/junyan/Mosam3dckxyyy.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckxyyz | user/junyan/Mosam3dckxyyz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckxyzz | user/junyan/Mosam3dckxyzz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckxz | user/junyan/Mosam3dckxz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckxzzz | user/junyan/Mosam3dckxzzz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckyy | user/junyan/Mosam3dckyy.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckyyyy | user/junyan/Mosam3dckyyyy.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckyyyz | user/junyan/Mosam3dckyyyz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckyyzz | user/junyan/Mosam3dckyyzz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckyz | user/junyan/Mosam3dckyz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckyzzz | user/junyan/Mosam3dckyzzz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckzz | user/junyan/Mosam3dckzz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfosam3dckzzzz | user/junyan/Mosam3dckzzzz.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfoshift1 | user/yliu/Moshift1.c | Generate shifts with offset for 1-D regularized autoregression. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfovczop | user/luke/Movczop.c | Post-stack 2-D oriented velocity continuation, with OpenMP Parallelism on frequency loop | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpad2 | user/zhiguang/Mpad2.c | Pad boundary | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpad2nextfastsize | user/ivlad/Mpad2nextfastsize.c | How much to pad to get to next fast c2c FFT size (factors: 2,3 and 5) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpadfault | user/zhiguang/Mpadfault.c | Horizontally pad fault | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpadzero | user/zhiguang/Mpadzero.c | Interpolation from a coarser grid to finer grid with zero padded | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpame2d | user/junyan/Mpame2d.c | 2-D elasitc wave modeling and vector field decompostion using pseudo-analytical method | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpame3d | user/junyan/Mpame3d.c | 3-D elasitc wave modeling and vector field decompostion using pseudo-analytical method | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpamti2d | user/junyan/Mpamti2d.c | Modeling of pure acoustic wave in 3-D transversely isotropic media with psuedo-analytic method | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpamti3d | user/junyan/Mpamti3d.c | Modeling of pure acoustic wave in 3-D transversely isotropic media with psuedo-analytic method | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfparadd | user/psava/Mparadd.c | Add, multiply, or divide  RSF datasets. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfparcel | user/gee/Mparcel.c | Patching test. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpassive2d | user/jsun/Mpassive2d.c | 2-D passive seismic RTM and its adjoint | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpathmin | user/luke/Mpathmin.c | Program for iteratively determining the optimal path through a cost function input array.  Input file's second dimension is a parameter that | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpathmin-mov | user/luke/Mpathmin-mov.c | Program for iteratively determining the optimal path through a cost function input array.  Input file's second dimension is a parameter that | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpathmin1 | user/luke/Mpathmin1.c | One dimensional path minimization for optimization input file has first coordinate parameter, second coordinate time | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpca | user/chen/Mpca.c | KL transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpchain | user/fomels/Mpchain.c | Nonstationary Prony by chain of PEFs | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpchain1 | user/fomels/Mpchain1.c | Nonstationary Prony by chain of PEFs - linear operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpclipc2 | user/chenyk/Mpclipc2.c | One-or Two-sided Percentile Data clipping (C language). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpcrdata2 | user/cram/Mpcrdata2.c | Prepare data for 2-D angle-domain migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpcrdata3 | user/cram/Mpcrdata3.c | Prepare data for 3-D angle-domain migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpcrsurv3 | user/cram/Mpcrsurv3.c | Prepare survey info for 3-D angle-domain migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpde2dadp | user/browaeys/Mpde2dadp.c | Numerical solution of linear pde 2-d (X-Z-a) for phase space escape positions, angle and traveltime | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpdr2d | user/aklokov/Mpdr2d.c | 2D Parametric Development of Reflections | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpdrscan2d | user/aklokov/Mpdrscan2d.c | Velocity Scan by 2D Parametric Development of Reflections | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpefdeburst | user/gee/Mpefdeburst.c | Burst noise removal using PEF. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpermlr1 | user/fomels/Mpermlr1.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpermlr2 | user/fomels/Mpermlr2.cc | number of offsets | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpermlr2ddti | user/hwang/Mpermlr2ddti.cc | This program is free software; you can redistribute it and/or modify | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpermlr3 | user/fomels/Mpermlr3.cc | smooth max function | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpermwave2d | user/hwang/Mpermwave2d.c | Wavefield Extrapolation for 2D PERM | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpetscawefd2d | user/petsc/Mpetscawefd2d.c | Implicit solution of 2-D acoustic wave equation, compatibility interface with sfawefd2d | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfpetsctest | user/chenyk/Mpetsctest.c | Solving 2D driven cavity problem in a velocity-vorticity formulation. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfpfactor2 | user/gee/Mpfactor2.c | Plane prediction filter on a helix. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpgen | user/nobody/Mpgen.c | Generate stereopicks from time-migration velocities and slopes. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfphaserot | user/fomels/Mphaserot.c | Non-stationary phase rotation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfphasescan | user/songxl/Mphasescan.c | Multicomponent data registration analysis. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfphmig | user/nobody/Mphmig.c | ------------------------------------------------------------ | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpiazpwdmig3 | user/dmerzlikin/Mpiazpwdmig3.c | Least-Squares 3D Path-Summation Integral, Azimuthal Plane-Wave Destruction and Kirchhoff Modeling/Migration Chain of Operators | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpick0 | user/nobody/Mpick0.c | Automatic traveltime picking | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpick2 | user/fomels/Mpick2.c (+1) | Automatic picking from semblance-like panels (3-D input). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpick2d | user/aklokov/Mpick2d.c | 2D picking | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpick3 | user/fomels/Mpick3.c | Automatic picking  from 3-D semblance-like panels. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpick31 | user/yliu/Mpick31.c | Automatic picking from 3D semblance-like panels plus additional axis. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpickd | user/nobody/Mpickd.c | Automatic traveltime picking (yet another) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpickmaxima | user/zhiguang/Mpickmaxima.c | Picking local maxima on the first axis with evenly spaced windows. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpickprint | user/zhiguang/Mpickprint.c | Write predictive painting result into a txt file | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpicks2rsf | user/ediazp/Mpicks2rsf.c | Creates a mask from horizons: | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpickvert | user/aklokov/Mpickvert.c | Automatic picking  from semblance-like panels. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpipwdmig2 | user/dmerzlikin/Mpipwdmig2.c | Chain of Path Integral, Plane-Wave Destruction and Kirchhoff migration (based on sfmig2) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfplanemis2 | user/pwd/Mplanemis2.c | Missing data interpolation in 2-D using plane-wave destruction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfplanemis3 | user/pwd/Mplanemis3.c | Missing data interpolation in 3-D using plane-wave destruction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfplanereg2 | user/pwd/Mplanereg2.c | Data regularization in 2-D using plane-wave destruction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfplanereg3 | user/pwd/Mplanereg3.c | Data regularization in 3-D using plane-wave destruction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfplanesig | user/pwd/Mplanesig.c | Signal separation using plane-wave destruction filters. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfplanesignoi | user/pwd/Mplanesignoi.c | Signal and noise separation using plane-wave destruction filters. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpmig1 | user/lcasasan/Mpmig1.c | Slope-based prestack (t,xs,h) time migration . | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpmod | user/rickettj/Mpmod.c | Random plane wave modeling. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpmshape2 | user/pwd/Mpmshape2.c | Missing data interpolation in 2-D using plane-wave destruction and shaping regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpnmomf | user/chenyk/Mpnmomf.c | Normal moveout. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpocs3d | user/pyang/Mpocs3d.c | POCS for 3D missing data interpolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpocsseislet | user/pyang/Mpocsseislet.c | Seislet-based POCS interpolation (2d validation) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpocssemb | user/chenyk/Mpocssemb.c | POCS using semblance thresholding or amplitude thresholding. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpolyfit | user/fomels/Mpolyfit.c | Fitting a polynomial by least-squares. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpostrtm2d | user/zhiguang/Mpostrtm2d.c | 2-D exploding-reflector RTM and its adjoint | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpradon | user/nobody/Mpradon.c | Phase-space Radon transform | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpredict | user/pwd/Mpredict.c | 2-D plane-wave prediction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpreerror | user/chenyk/Mpreerror.c | Prediction error | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfprekirch | user/chenyk/Mprekirch.c | 2-D Prestack Kirchhoff time migration with antialiasing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfprekirchsr | user/chenyk/Mprekirchsr.c | 2-D Prestack Kirchhoff time migration with antialiasing in source-receiver domain. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpremig | user/jsun/Mpremig.c | Pseudo-spectral pre-stack source-receiver source independent diffraction imaging | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpresr | user/chenyk/Mpresr.c | 2-D simplest-form post-stack Kirchhoff time modeling and migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpresum | user/psava/Mpresum.c | presum traces | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfps2d | user/pyang/Mps2d.c | 2-D attenuating wavefield simulation using Fourier Pseudo Spectral method | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpscefd | user/chen/Mpscefd.c | EFD phase shift wave extrapolation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpse2d | user/junyan/Mpse2d.c | Pseudo-spectral method for 2-D elastic wave modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpse3d | user/junyan/Mpse3d.c | 3-D elasitc wave modeling and vector field decompostion using pseudospectra method | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpsefd | user/chen/Mpsefd.c | EFD phase shift wave extrapolation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpseudo | user/jingwei/Mpseudo.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpseudodepth | user/xuxin/Mpseudodepth.c | depth to vertical-time interpolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpseudolrexp | user/jingwei/Mpseudolrexp.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpseudoprim | user/yliu/Mpseudoprim.c | Generate pseudoprimaries using multiples | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpsmig | user/chenyk/Mpsmig.c | 2-D Phase-shift modeling and migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpsmig2 | user/fomels/Mpsmig2.c | 2-D prestack Kirchhoff time migration with antialiasing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpsovc | user/dmerzlikin/Mpsovc.c | Pre-stack 2-D oriented velocity continuation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpsovcp | user/dmerzlikin/Mpsovcp.c | Pre-stack 2-D oriented velocity continuation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpsp | user/jsun/Mpsp.c | Pseudo-spectral wave extrapolation/migration using second-order two-way wave equation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpspfwi | user/llisiw/Mpspfwi.c | Full-waveform Inversion by Parallel Helmholtz Solver | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpspifcos2bs | user/songxl/Mpspifcos2bs.c | 1-D finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpspig | user/songxl/Mpspig.c | 1-D finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpspmig | user/jsun/Mpspmig.c | Pseudo-spectral migration/de-migration adjoint operators using second-order two-way wave equation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpspp | user/jsun/Mpspp.c | Pseudo-spectral wave extrapolation for second-order two-way wave equation using wavefield injection for passive imaging | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpsss | user/chen/Mpsss.c | phase shift wave extrapolation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpsti2d | user/junyan/Mpsti2d.c | Modeling of pure acoustic wave in 2-D transversely isotropic meida using psuedospectral method | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpsti3d | user/junyan/Mpsti3d.c | Modeling of pure acoustic wave in 3-D transversely isotropic meida using psuedospectral method | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpsvp | user/chen/Mpsvp.c | Ps to vplot | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwarp | user/pwd/Mpwarp.c | Shift estimation by amplitude-adjusted plane-wave destruction | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwcascade | user/pwd/Mpwcascade.c | Plane-wave smoothing by box cascade. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwcascade3 | user/pwd/Mpwcascade3.c | 3-D plane-wave smoothing by box cascade. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwcoh | user/pwd/Mpwcoh.c | Coherency by plane-wave construction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwcsemb | user/yliu/Mpwcsemb.c | Semblance from plane-wave construction datacube. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwd1 | user/pwd/Mpwd1.c | One side of plane wave destruction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwd2 | user/yliu/Mpwd2.c | 2-D plane wave destruction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwd2ani | user/lcasasan/Mpwd2ani.c | 2-D plane wave destruction + aniso coefficient. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwdchain | user/pwd/Mpwdchain.c | Multiple dip estimation by chain of PWDs | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwdchain1 | user/pwd/Mpwdchain1.c | Chain of PWDs - linear operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwdchain2 | user/pwd/Mpwdchain2.c | Chain of PWDs | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwddiffuse | user/dmerzlikin/Mpwddiffuse.c | Anisotropic diffusion by regularized inversion. Instead of a gradient PWDs in inline and crossline directions are used. 3D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwdecon | user/gchliu/Mpwdecon.c | Deconvolution with known wavelelt using pwc to control sparsity. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwdfreq | user/chen/Mpwdfreq.c | frequency response of PWD operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwdix | user/pwd/Mpwdix.c | Convert RMS to interval velocity using LS and plane-wave construction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwdnorm | user/lcasasan/Mpwdnorm.c | 3-D plane wave destruction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwdsigk | user/pwd/Mpwdsigk.c | Signal component separation using plane-wave destruction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwdsmooth2 | user/pwd/Mpwdsmooth2.c | 2-D smoothing by triangle plane-wave construction shaping. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwdtensor | user/dmerzlikin/Mpwdtensor.c | structure tensor estimation based on plane wave destruction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwdtensorh | user/dmerzlikin/Mpwdtensorh.c | structure tensor estimation based on plane wave destruction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwic | user/gchliu/Mpwic.c | Least square imaging condition with pwc regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwpaint | user/pwd/Mpwpaint.c | Painting by plane-wave construction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwpaint2 | user/pwd/Mpwpaint2.c | 3-D painting by plane-wave construction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwpaint3 | user/pwd/Mpwpaint3.c | 3-D painting by plane-wave construction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwsfault | user/yliu/Mpwsfault.c | Fault detection from plane-wave spray. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwsfault3 | user/yliu/Mpwsfault3.c | 3-D fault detection from plane-wave spray. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwshapeic | user/gchliu/Mpwshapeic.c | Least Square Imaging condition using structure-based shaping regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwsmooth | user/pwd/Mpwsmooth.c (+1) | 2-D structure-enhancing filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwsmooth2 | user/pwd/Mpwsmooth2.c | 2-D structure-enhancing filtering: two slopes. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwsmooth3 | user/yliu/Mpwsmooth3.c | 3-D structural-oriented smoothing using plane-wave spray and weighted stacking. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwspray | user/pwd/Mpwspray.c | Plane-wave spray. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwspray2 | user/pwd/Mpwspray2.c | Plane-wave spray in 3-D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwspray3 | user/pwd/Mpwspray3.c | Plane-wave spray in 3-D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfpwstack | user/pwd/Mpwstack.c | Recursive stacking by plane-wave construction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfquantile | user/ivlad/Mquantile.c | Computes what clip value corresponds to a given pclip. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfquarticlayer | user/zone/Mquarticlayer.c | Interval quartic coefficients estimation by layer for general 3D anisotropic media | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfR2to3 | user/mehdi/MR2to3.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfradialhlin | user/zone/Mradialhlin.c | Radial transform.with shifted-linear interpolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfradon2 | user/jingwei/Mradon2.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfradon3 | user/jingwei/Mradon3.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfradon32 | user/jingwei/Mradon32.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfradon34 | user/jingwei/Mradon34.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfradonoper | user/yliu/Mradonoper.c | Linear Radon operator. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfradonslope2 | user/browaeys/Mradonslope2.c | Directional angle transform for 3-D time image cube I(x,z,t) into G(x,z,d) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrandcut | user/psava/Mrandcut.c | cut a random dataset from a 3D cube | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrandline | user/gee/Mrandline.c | Construct data from random lines | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrankonetest | user/jingwei/Mrankonetest.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrays3a | user/zone/Mrays3a.c | Ray tracing in general anisotropic media by a Runge-Kutta integrator in 3-D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrdiv | user/fomels/Mrdiv.c | Rough division. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfreadsample | user/roman/Mreadsample.c | Oriented zero-offset migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfreadsampleref | user/roman/Mreadsampleref.c | Oriented zero-offset migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrec2ps | user/jeff/Mrec2ps.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfreciprocity | user/jeff/Mreciprocity.c | Create a dipping layer model for HTI testing purposes.  Has fixed velocity structure, but can change dip of layer and degree of anisotropy. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrecoverfulleq | user/yliu/Mrecoverfulleq.c | Recover all equivalent Q values according to reference point and non-zero point. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfregr | user/fomels/Mregr.c | Linear regression | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfregrid1d | user/psava/Mregrid1d.c | 1-D ENO interpolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfregrid2d | user/psava/Mregrid2d.c | 2-D ENO interpolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfregrid3d | user/psava/Mregrid3d.c | 3-D ENO interpolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfreorder | user/zgeng/Mreorder.c | Reorder the data according to the path | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfresamp | user/chengjb/Mresamp.c | 2D data resampling. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfresample | user/chen/Mresample.c | 2D data resampling. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfresamplextnd | user/luke/Mresamplextnd.c | 2D data resampling with ability to extrapolate. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrevent | user/aklokov/Mrevent.c | Compute reflection event | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfreversval | user/yliu/Mreversval.c | Reverse data value | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrfccp | user/jeff/Mrfccp.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrfspecdiv | user/jeff/Mrfspecdiv.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrfxrna | user/gchliu/Mrfxrna.c | Local prediction filter for complex numbers (n-dimensional). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrickback | user/tsai/Mrickback.c | None linear Ricker wavelet spectral fit. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrickerfit | user/tsai/Mrickerfit.c | Model wavelet spectrum by fitting spectral components of ricker wavelet. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfriesz | user/fomels/Mriesz.c | Compute 2-D Riesz transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrkawefd2d | user/roman/Mrkawefd2d.c | 2D acoustic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrmtrace | user/chenyk/Mrmtrace.c | Remove part of traces (resample) in order to make aliasing | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrotater | user/zone/Mrotater.c | Roatation with Interpolation from a regular grid in 2-D. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrotvol | user/aklokov/Mrotvol.c | 3D volume rotation about a vertical axis | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrpslow2 | user/cram/Mrpslow2.c | Full angle-dependent slowness volume for 3-D reduced phase space. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrrt3d | user/psava/Mrrt3d.c | 3-D ray tracing w/ random shooting directions | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrsf2bin | user/chenyk/Mrsf2bin.c | RSF file to Binary file | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrsf2handvel | user/salah/Mrsf2handvel.c | Convert RSF to velocity picks | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrsf2txt | user/chenyk/Mrsf2txt.c | RSF file to Text (ASCII) file (as a matrix) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrsin | user/fomels/Mrsin.c | Simple operations with real sinusoids | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrtft | user/yliu/Mrtft.c | Ricker time-frequency transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrtm2d | user/pyang/Mrtm2d.c | 2-D zero-offset reverse-time migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrtmadcig | user/pyang/Mrtmadcig.c | RTM and angle gather (ADCIG) extraction using poynting vector | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrtmgeom | user/roman/Mrtmgeom.c | Rice HPCSS reverse time migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrtmgeompetsc | user/petsc/Mrtmgeompetsc.c | Rice HPCSS reverse time migration. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfrtmodcig | user/pyang/Mrtmodcig.c | RTM output ODCIG with extended images | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrtmpar | user/parvaneh/Mrtmpar.c | RTM | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrtmva2d | user/pyang/Mrtmva2d.c | RTM with checkpointing in 2D acoustic media | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrtseislet | user/zgeng/Mrtseislet.c | Seislet transform using relative time | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrwe2d | user/jeff/Mrwe2d.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfrwemete2d | user/nobody/Mrwemete2d.c | 2-D metric tensor | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfs2plane | user/nobody/Ms2plane.c | plane reflector: z = z0 + (x-x0)*tan(a) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsag | user/nobody/Msag.c | Simple v(z) synthetic. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsaltpepper | user/yliu/Msaltpepper.c | Add salt and pepper noise to the data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsamplowmat | user/jingwei/Msamplowmat.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsampmat | user/jingwei/Msampmat.cc | //--------construct cin = delta(x-x0) for all x------------ | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsamptest | user/jingwei/Msamptest.cc | //--------construct cin in a different way----------------- | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsamptestlrexp | user/jingwei/Msamptestlrexp.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsbd | user/songxl/Msbd.c | 1-D finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsc | user/fomels/Msc.c | Surface-consistent decomposition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfScanCoef | user/tariq/MScanCoef.c | Coeffecients of the eta expansion eikonal solver (3-D). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsclet | user/yliu/Msclet.c | 2-D SC-seislet: Seislet transform with differential shot continuation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfseekwin | user/ivlad/Mseekwin.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsegy2rsf | user/nobody/Msegy2rsf.c | Convert a SEG-Y dataset to RSF. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfseisavf | user/yliu/Mseisavf.c | 1-D amplitude versus frequency (AVF) analysis with 1-D seislet frames | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfseisbreg2 | user/yliu/Mseisbreg2.c | Missing data interpolation in 2D using seislet and Bregman shaping iteration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfseiscut | user/chenyk/Mseiscut.c | Seislet Transform Denoising using Mask Operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfseishrink | user/yliu/Mseishrink.c | 2-D Seislet shrinkage denoising. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfseisigk | user/pwd/Mseisigk.c | Signal component separation using seislet transforms. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfseislet1 | user/fomels/Mseislet1.c | 1-D seislet transform | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfseislet97 | user/nobody/Mseislet97.c | CDF 9/7 biorthogonal seislet transform | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfseismis2 | user/yliu/Mseismis2.c | Missing data interpolation in 2-D using seislet transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfseispocs | user/yliu/Mseispocs.c | Missing data interpolation using POCS added 2-D seislet transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfseisreg2 | user/yliu/Mseisreg2.c | Data regularization in 2-D using seislet transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfseisthr | user/chenyk/Mseisthr.c | Seislet Transform Denoising using Thresholding | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfseisxwell | user/yliu/Mseisxwell.c | Select seismic data cross well position. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfselfblend | user/chenyk/Mselfblend.c | Self blending for simple test. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsemblancew | user/fomels/Msemblancew.c | Semblance over the specified axis. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsensitivity | user/rickettj/Msensitivity.c | Traveltime sensitivity kernels. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfset2zero | user/slim/Mset2zero.c | replaces content of RSF file with zeros | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsgelfd2dpml | user/junyan/Msgelfd2dpml.c | A k-space staggered-grid lowrank finite-difference for elastic and viscoelastic seismic-wave modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsgelfd2dpml2 | user/junyan/Msgelfd2dpml2.c | A k-space staggered-grid lowrank finite-difference for elastic and viscoelastic seismic-wave modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsgfd1 | user/fangg/Msgfd1.c | 1-D staggered Grid Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsgfdco1 | user/fangg/Msgfdco1.cc | Lowrank FD coefficients | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsgfdewe2d | user/zhiguang/Msgfdewe2d.c | 2-D staggered-grid elastic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfd1pml | user/fangg/Msglfd1pml.c | 1-D Lowrank Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfd2 | user/fangg/Msglfd2.c | 2-D Low Rank Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfd2_tfd | user/fangg/Msglfd2_tfd.c | 2-D 4th-order Staggered Grid Finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfd2pml | user/fangg/Msglfd2pml.c | 2-D Lowrank Finite-difference wave extrapolation on staggered grid | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfdc1 | user/fangg/Msglfdc1.cc | // ks: 0 --- fn,-fn --- 0 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfdc1a | user/fangg/Msglfdc1a.cc | // ks: 0 --- fn,-fn --- 0 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfdc1opt | user/fangg/Msglfdc1opt.cc | // ks: 0 --- fn,-fn --- 0 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfdc1sigma | user/fangg/Msglfdc1sigma.cc | Staggered grid Lowrank FD coefficient with sigma approximation to improve its stablility | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfdco1 | user/fangg/Msglfdco1.cc | Lowrank FD coefficients | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfdcp1 | user/fangg/Msglfdcp1.cc | int fdx32(vector<int>& cs, DblNumMat& res) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfdcsgm2x | user/fangg/Msglfdcsgm2x.cc | using weighted least square | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfdcsgm2z | user/fangg/Msglfdcsgm2z.cc | using weighted least square | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfdcx1 | user/fangg/Msglfdcx1.cc | FD coefficient | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfdcx1a | user/fangg/Msglfdcx1a.cc | 1D  Lowrank FD coefficient of d/dx on staggered grid | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfdcx2_7 | user/fangg/Msglfdcx2_7.cc | Low rank decomposition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfdcz2_7 | user/fangg/Msglfdcz2_7.cc | Low rank decomposition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglfdrtm2 | user/fangg/Msglfdrtm2.c | 2-D Staggered Grid Lowrank Finite-difference RTM | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglr1 | user/fangg/Msglr1.c | 1-D lowrank wave propagation on staggered grid | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsglr2 | user/fangg/Msglr2.c | Simple 2-D wave propagation on staggered grid | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsgtwoapp | user/fangg/Msgtwoapp.cc | using weighted least square | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsh1 | user/fomels/Msh1.c | Generate 1D shifts for regularized regression. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsh2 | user/fomels/Msh2.c | Generate 2D shifts for regularized regression. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshapeagc | user/fomels/Mshapeagc.c | Automatic gain control by shaping regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshapefill | user/fomels/Mshapefill.c | Missing data interpolation in 2-D by Laplacian regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshapesigk | user/pwd/Mshapesigk.c | Signal component separation using plane-wave shaping. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsharpsimi | user/yliu/Msharpsimi.c | Sharpen similarity measure between two datasets. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshearer | user/fomels/Mshearer.c | Preconditioning for traveltime picking. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshift1 | user/fomels/Mshift1.c | Generate shifts for 1-D regularized autoregression. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshiftd1 | user/gchliu/Mshiftd1.c | Generate shifts for 1-D regularized autoregression double sides (not include the trace self). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshiftd2 | user/gchliu/Mshiftd2.c | Generate shifts for 1-D regularized autoregression double sides (include the trace self for 3D shifts). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshifts2 | user/gchliu/Mshifts2.c (+1) | Generate shifts for 2-D regularized autoregression in complex domain. From (x,y,f) to (x,y,s,f) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshot2cmp3 | user/nobody/Mshot2cmp3.c | Convert shots to CMPs for regular 3-D geometry. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshot2grid | user/psava/Mshot2grid.c | Synthesize shot/receiver wavefields for 3-D SR migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshotequal | user/salah/Mshotequal.c | sfshotequal projects amplitudes of each shot to Z-score distribution | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshplanemis2 | user/pwd/Mshplanemis2.c | Missing data interpolation in 2-D using plane-wave shaping regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshplanemis3 | user/pwd/Mshplanemis3.c | Missing data interpolation in 3-D using plane-wave shaping regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshpwstack | user/kregimbal/Mshpwstack.c | Recursive stacking by plane-wave construction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshstack | user/kregimbal/Mshstack.c | Shaping stack. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfshuffle2 | user/parvaneh/Mshuffle2.c | Shuffling an array | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsic | user/psava/Msic.c | Local slant stacks I.C. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsic3d | user/psava/Msic3d.c | Local slant stacks I.C. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsignoi | user/gee/Msignoi.c | Signal and noise separation (N-dimensional). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsimenv | user/fomels/Msimenv.c | Rotate phase and compute similarity with enevelope. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsimidenoise | user/chenyk/Msimidenoise.c | Random noise attenuation using local similarity | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsimidenoise1 | user/chenyk/Msimidenoise1.c | Random noise attenuation using local similarity (different weighting approach) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsimilarity2 | user/fomels/Msimilarity2.c | Local similarity measure between two datasets (alternative form). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsimpostkirch | user/chenyk/Msimpostkirch.c | 2-D simplest-form post-stack Kirchhoff time modeling and migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsint2 | user/chenyk/Msint2.c | Interpolation for sparse data in 2D, e.g., well logs | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsint3 | user/chenyk/Msint3.c | Interpolation for sparse data in 3D, e.g., well logs | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsizes | user/jennings/Msizes.c | Display the size of RSF files. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfslantopt | user/jsun/Mslantopt.c | Time-space-domain Radon transform (slant stack) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfslopescan | user/chen/Mslopescan.c | slope estimation by stack scan | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfslowft | user/nobody/Mslowft.c | Slow FT transform on the first axis. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfslschain2d | user/fomels/Mslschain2d.c | Separable LS - Find a symmetric chain of 2D-Fourier weighting and scaling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsltft | user/yliu/Msltft.c | Adaptive time-frequency pseudo transform using streaming algorithm. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsmiss | user/gee/Msmiss.c | Multi-dimensional missing data interpolation using shaping. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsmooth2 | user/nobody/Msmooth2.c | 2-D smoothing by Gaussian filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsmoothcur | user/lcasasan/Msmoothcur.c | Convert input slope and time derivative | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsmoothder1 | user/lcasasan/Msmoothder1.c | Convert input to its derivative using LS and shaping regularization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsmoothder2 | user/lcasasan/Msmoothder2.c | Convert input to its derivative using LS and shaping regularization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsmoothderLS | user/lcasasan/MsmoothderLS.c | Convert input to its derivative using LS and shaping regularization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsmoothderw | user/fomels/Msmoothderw.c | Convert input to its derivative using LS and shaping regularization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsmoothdiv | user/nobody/Msmoothdiv.c | Smooth signal division. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsmoothn | user/chenyk/Msmoothn.c | N-D non-stationary smoothing (fixed version of sfnsmooth.) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsmoothreg | user/fomels/Msmoothreg.c | Smoothing in 1-D by simple regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsmspray | user/fomels/Msmspray.c | Smoothing by spraying | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsmstack | user/gchliu/Msmstack.c | Stack a dataset over the second dimensions by smart stacking. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsnr3 | user/chenyk/Msnr3.c | Compute signal-noise-ratio. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsnrcyk | user/chenyk/Msnrcyk.c | Compute signal-noise-ratio. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsnrstack | user/gchliu/Msnrstack.c | Stack a dataset over the second dimensions by SNR weighted method. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsoftclip | user/luke/Msoftclip.c | Soft clip the data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsortdensity | user/jyan/Msortdensity.c | sort density | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsp | user/songxl/Msp.c | 2-D Pseudo-spectral wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsparsify | user/ivlad/Msparsify.c | Transforms regular 2-D array to sparse array | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfspecfac | user/ridder/Mspecfac.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfspefcstep | user/yliu/Mspefcstep.c | Streaming prediction-error filter with constant step. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfspefvstep | user/yliu/Mspefvstep.c | Streaming prediction-error filter with variable step. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsphase | user/yliu/Msphase.c | Smooth estimate of instantaneous phase. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsphere | user/nobody/Msphere.c | Creates a simple spherical surface. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfspicks | user/nobody/Mspicks.c | Generate stereotomography picks from time migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfspiral | user/kourkina/Mspiral.c | Spiral function | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfspiralsort | user/yunzhi/Mspiralsort.c | Sort microseismic surface array recording traces with a given epicenter along a spiral shape R = r0 + d(a-a0). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfspitz | user/lcasasan/Mspitz.c | Missing data interpolation in 2-D using F-X Prediction Error Filters | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfspitzbl | user/lcasasan/Mspitzbl.c | Missing data interpolation in 2-D using F-X Prediction Error Filters | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfspitzblns | user/lcasasan/Mspitzblns.c | Missing data interpolation in 2-D using F-X Prediction Error Filters | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfspitzns | user/lcasasan/Mspitzns.c | Missing data interpolation in 2-D using F-X Prediction Error Filters | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsplinebank | user/gee/Msplinebank.c | Prepare a filter bank for B-spline plane wave filters | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsplineplane | user/gee/Msplineplane.c | B-spline plane-wave filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsqsanaly | user/browaeys/Msqsanaly.c | Analytic escape solutions in phase space for constant gradient of slowness squared | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsrbin3d | user/psava/Msrbin3d.c | 4-D data binning from traces at irregular coordinates | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsrmig | user/nobody/Msrmig.c | 3-D S/R migration with extended split-step | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsrmig2 | user/nobody/Msrmig2.c | 3-D S/R migration with extended split-step | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsrmig3 | user/psava/Msrmig3.c | 3-D S/R migration with extended SSF | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsrmod | user/nobody/Msrmod.c | 3-D S/R modeling with extended split-step | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsrmod3 | user/psava/Msrmod3.c | 3-D S/R modeling with extended split-step | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfssblend | user/chen/Mssblend.c | blend reciever gathers (T-S-R) to generate simultaneous data | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsscrg | user/chen/Msscrg.c | Extract common reciever gathers from simultaneous data | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsstep1 | user/nobody/Msstep1.c | 2-D post-stack modeling/migration with split step. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsstep3 | user/nobody/Msstep3.c | 3-D post-stack modeling/migration with split step. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstack2d | user/jsun/Mstack2d.c | Stack multi-shots images | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstack3 | user/psava/Mstack3.c | OpenMP stack on axis 1,2 or 3 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstackimg | user/fangg/Mstackimg.c | Stack multi-shots images | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstackn | user/saragiotis/Mstackn.c | Stack prespecified values. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstcontrib | user/fomels/Mstcontrib.c | Contribution weighting using streaming attributes. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstcurvature | user/parvaneh/Mstcurvature.c | Curvature in stratigraphic coordinates | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstf2telewfld | user/jeff/Mstf2telewfld.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstfchain | user/fomels/Mstfchain.c | Find a symmetric chain of Fourier weighting and scaling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstfchain2 | user/fomels/Mstfchain2.c | Find a symmetric chain of 1-D Fourier weighting and scaling with movies | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstft | user/yliu/Mstft.c | Short-time Fourier transform (STFT). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstft2 | user/yliu/Mstft2.c | Another version of Short-time Fourier transform (STFT) with overlap windows. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsthres | user/jingwei/Msthres.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstiff3d | user/jyan/Mstiff3d.c | stiffness tensor for 3D TTI models | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstltft | user/fomels/Mstltft.c | Streaming time-frequency transform (LTFT). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstolt2hlin | user/zone/Mstolt2hlin.c | Post-stack Stolt modeling/migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstpf | user/fomels/Mstpf.c | Streaming prediction filter | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstphase | user/fomels/Mstphase.c | Streaming estimate of instantaneous frequency. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstransp | user/psava/Mstransp.c | in-memory transpose 12 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstream | user/fomels/Mstream.c | Streaming PEF | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstreamh | user/gee/Mstreamh.c | Streaming PEF on a helix | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstreamiss | user/fomels/Mstreamiss.c | Missing data interpolation using streaming PEF | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstreamissh | user/gee/Mstreamissh.c | Missing data interpolating using streaming PEF on a helix | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfstretch2 | user/nobody/Mstretch2.c | Smooth inverse interpolation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsttimefreq | user/fomels/Msttimefreq.c | Time-frequency analysis using streaming attributes. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsu2rsf | user/nobody/Msu2rsf.c | Convert a SU dataset to RSF. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsu2rsf3dladcig | user/chengjb/Msu2rsf3dladcig.c | Convert 3D Azimuth-IncidentAngle-Domain CIGs (x,y,azimuth,angle,tau) data to RSF format. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsum | user/jingwei/Msum.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsum3 | user/jingwei/Msum3.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsumamp | user/aklokov/Msumamp.c | Stack energy between two input horizons | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsuplane | user/chenyk/Msuplane.c | Create common offset data file with up to 3 planes | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsurface-consistent | user/luke/Msurface-consistent.c | Surface-consistent decomposition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsv2d | user/yliu/Msv2d.c | Velocity and heterogeneity parameter convert to dip. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsvd | user/yliu/Msvd.c | Singular value decomposition (SVD) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsvddenoise | user/yliu/Msvddenoise.c | SVD denoising | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsvdtest | user/jingwei/Msvdtest.cc | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfswapbyte | user/xuxin/Mswapbyte.c | endianness conversion | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfswell | user/yliu/Mswell.c | Add swell noise to the data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfswnorm | user/jsun/Mswnorm.c | Sliding window normalization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfswvarimax | user/jsun/Mswvarimax.c | Sliding window varimax | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsymes | user/nobody/Msymes.c | 2-D synthetic model for multiple-arrival generation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsymposolver | user/chenyk/Msymposolver.c | Symmetric positive definite matrix equation solver using square root method (cholesky decomposition method) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsynmarine | user/gee/Msynmarine.c | Simple synthetic marine data example. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfsyntop | user/gee/Msyntop.c | Make synthetic topography map. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sft2diter | user/llisiw/Mt2diter.c | Time-to-depth conversion (linear operator) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftah5dinterp | user/karl/Mtah5dinterp.c | Trace And Header GET Header Word prints trace headers. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahagc | user/karl/Mtahagc.c | Read Trace And Header (tah) from standard input, MUTE | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahfilter | user/karl/Mtahfilter.c | Read Trace And Header (tah) from standard input and FILTER | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahgain | user/karl/Mtahgain.c | Read Trace And Header (tah) from standard input and apply GAIN | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahgethw | user/karl/Mtahgethw.c | Trace And Header GET Header Word prints trace headers. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahheadermath | user/karl/Mtahheadermath.c | Trace And Header MEADER MATH | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahmakeevent | user/karl/Mtahmakeevent.c | Trace And Header MAKEEVENT makes constant velocity dipping event synthetic. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahmakeskey | user/karl/Mtahmakeskey.c | Trace And Header MAKE Secondary KEY. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahmakesloc | user/karl/Mtahmakesloc.c | Trace And Header MAKE SLOC KEY. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahmute | user/karl/Mtahmute.c | Read Trace And Header (tah) from standard input, MUTE. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahnmo | user/karl/Mtahnmo.c | Trace And Header Normal MoveOut | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahpef | user/karl/Mtahpef.c | Trace And Header Prediction Error Filtering | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahread | user/karl/Mtahread.c | Read Trace And Header from separate files, combine, write to pipe | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahremoveclick | user/karl/Mtahremoveclick.c | Trace And Header REMOVE electricl CLICK. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahscdecon | user/karl/Mtahscdecon.c | Trace And Header Surface Consistant Decon. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahscscale | user/karl/Mtahscscale.c | Surface Consistant SCALE - Compute & apply surface consistant scale | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahspecbal | user/karl/Mtahspecbal.c | Read Trace And Header (tah) from standard input, SPECtral BALance | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahstack | user/karl/Mtahstack.c | Read Trace And Header (tah) from STDIN, stack matching header keys | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahstatic | user/karl/Mtahstatic.c | Trace And Header STATIC | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftahwindow | user/karl/Mtahwindow.c | Trace And Header WINDOW | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftan2dang | user/browaeys/Mtan2dang.c | 2-D slowness vector to angle transformation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftaperedge | user/aklokov/Mtaperedge.c | Taper based on data parameters | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftaupfit | user/fomels/Mtaupfit.c | Fitting tau-p approximations | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftcor | user/psava/Mtcor.c | Interferometric cross-correlation of time series (zero-lag output) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftdconvert | user/llisiw/Mtdconvert.c | Iterative time-to-depth velocity conversion | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftelemig2d | user/jeff/Mtelemig2d.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftentwt | user/gee/Mtentwt.c | Tent-like weight for patching. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftest1_matchl1 | user/lcasasan/Mtest1_matchl1.c | L1 1D matched filter | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sftest2_matchl1 | user/lcasasan/Mtest2_matchl1.c | L1 1D matched filter | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sftestanal | user/llisiw/Mtestanal.c | Test Analytical for constant velocity background | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfTestaniso | user/pyang/MTestaniso.c | A 2D demo of elliptically-anisotropic wave propagation (4th order) | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sftestapef | user/yliu/Mtestapef.c | Test linear adaptive PEF operator. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sftestcasoper | user/yliu/Mtestcasoper.c | Test linear cascading matching-Radon operator. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfTestcdstep | user/lcasasan/MTestcdstep.c | unknown | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sftestcg | user/harlan/Mtestcg.cc | See Cg.h for documentation of this class | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfTesteb | user/pyang/MTesteb.c | Demo for effective boundary saving in regular grid | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfTestelastic2d | user/pyang/MTestelastic2d.c | 2D 8-th order elastic wave propagation using sponge ABC | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfTestfd2d | user/pyang/MTestfd2d.c | A demo of 2D FD test | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfTestfd3d | user/pyang/MTestfd3d.c | 3D acoustic time-domain FD modeling | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sftestmatch | user/yliu/Mtestmatch.c | Test linear matching operator. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sftestomp | user/zone/Mtestomp.c | unknown | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfTestsolver | user/chenyk/MTestsolver.c | Test for conjugate gradient, steepest descent, jacobi iteration, gauss-seidel iteration, successive over relaxation (SOR) iteration | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfTestsolver1 | user/chenyk/MTestsolver1.c | Test for conjugate gradient, steepest descent, jacobi iteration, gauss-seidel iteration, successive over relaxation (SOR) iteration | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfTestspml | user/pyang/MTestspml.c | 2D acoustic FD using Split PML (SPML) absorbing boundary condition | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sftestthr | user/dmerzlikin/Mtestthr.c | Threshold float/complex inputs given a constant/varying threshold level. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sftf2dprec | user/fomels/Mtf2dprec.c | TF Weights Preconditioner for Real input as linear operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftfchain | user/fomels/Mtfchain.c | Find a chain of Fourier weighting and scaling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftheoreqiq | user/yliu/Mtheoreqiq.c | Output theoretical interval Q value and equivalent Q value. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfthickat | user/mehdi/Mthickat.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfthin | user/fomels/Mthin.c | Sparse deconvolution. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfthreads | user/mccowan/Mthreads.c | Testing Posix threads | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfthreecolumn2dti | user/chengjb/Mthreecolumn2dti.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfthreshold2 | user/yliu/Mthreshold2.c | 2-D Soft thresholding. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfthreshold3 | user/yliu/Mthreshold3.c | Automatic soft or hard thresholding. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftilr2 | user/jsun/Mtilr2.cc | from degrees to radians | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftilrzone | user/jsun/Mtilrzone.cc | from degrees to radians | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftime2depthweak | user/zone/Mtime2depthweak.c | Time-to-depth conversion in media with weak lateral variations 2D (Sripanich and Fomel, 2017). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftimecont | user/fomels/Mtimecont.c | Forward or reverse time continuation using fast marching. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftimefreq | user/fomels/Mtimefreq.c | Time-frequency analysis using local attributes. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftimerev2d | user/jsun/Mtimerev2d.c | 2-D correlative time reversal imaging of passive seismic data | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftimeshift | user/pwd/Mtimeshift.c | Apply variable time shifts using plane-wave construction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftinterp | user/llisiw/Mtinterp.c | Traveltime interpolation by cubic Hermite spline | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftkirinv | user/seisinv/Mtkirinv.c | 2-D least-squares Kirchhoff pre-stack time migration with different regul.. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftkirmig | user/seisinv/Mtkirmig.c | 2-D Kirchhoff pre-stack time migration/demigration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftmigda | user/aklokov/Mtmigda.cc | 3D time scattering-angle Kirchhoff migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftomo | user/fomels/Mtomo.c | Simple tomography test. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftrace2 | user/fomels/Mtrace2.c | 2-D multiple arrivals by cell ray tracing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftracealign | user/jeff/Mtracealign.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftransconv | user/luke/Mtransconv.c | program translates a 2D image then convolves it with arbitrary kernel | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftranslate | user/luke/Mtranslate.c | program translates a 2D image | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftransp12 | user/psava/Mtransp12.c | Transpose 1-2 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftrapepass | user/chenyk/Mtrapepass.c | Trapezoid bandpass filter in the frequency domain. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftraveltime2d | user/roman/Mtraveltime2d.c | Oriented zero-offset migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftraveltimelen | user/roman/Mtraveltimelen.c | Oriented zero-offset migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftraveltimelen3d | user/roman/Mtraveltimelen3d.c | Oriented zero-offset migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftree | user/fomels/Mtree.c | Multiple arrivals with a fast algorithm. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftricascade | user/fomels/Mtricascade.c | Triangle filter cascade | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfTriMeshLinearWts2d | user/jyan/MTriMeshLinearWts2d.c | 3D elastic time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftrismooth2 | user/pwd/Mtrismooth2.c | 2-D smoothing by triangle directional shaping. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftrisolver | user/chenyk/Mtrisolver.c | Tridiagonal matrix solver using chasing method | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftristack | user/fomels/Mtristack.c | Resampling with triangle weights. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftristack2 | user/fomels/Mtristack2.c | 2-D resampling with triangle weights. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftshiftcos | user/nobody/Mtshiftcos.c | Compute cos(theta) from 1/\|pm\| for time-shift imaging condition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftslread | user/yliu/Mtslread.c | Convert a TSL (MT, V5-2000 of Phoenix Geophysics) dataset to RSF. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftsmf | user/chenyk/Mtsmf.c | Two-step space varying median filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftspline | user/gee/Mtspline.c | Helix filters for spline in tension | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfTTAni | user/mehdi/MTTAni.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2de | user/chengjb/Mtti2de.c (+1) | 2-D two-components wavefield modeling using original elastic displacement wave equation in TTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2dedivcurl | user/chengjb/Mtti2dedivcurl.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2dekspacelr | user/chengjb/Mtti2dekspacelr.cc | 2-D two-components wavefield modeling using low-rank approximate k-space solution on the base of | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2dekspacelrsource | user/chengjb/Mtti2dekspacelrsource.cc | 2-D two-components wavefield modeling using low-rank approximate k-space solution on the base of | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delasticlrdecomp | user/chengjb/Mtti2delasticlrdecomp.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delasticlrdecomp1p | user/chengjb/Mtti2delasticlrdecomp1p.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delasticlrdecomp2p | user/chengjb/Mtti2delasticlrdecomp2p.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delasticlrsep | user/chengjb/Mtti2delasticlrsep.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delasticlrsep1p | user/chengjb/Mtti2delasticlrsep1p.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delasticlrsep2p | user/chengjb/Mtti2delasticlrsep2p.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delasticlrsep2ps | user/chengjb/Mtti2delasticlrsep2ps.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delasticsep | user/chengjb/Mtti2delasticsep.c | 2-D two-components wavefield modeling using original elastic displacement wave equation in TTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delr | user/chengjb/Mtti2delr.cc | 2-D two-components elastic wavefield extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delrdec | user/chengjb/Mtti2delrdec.cc | vector decomposition of the inputed elastic wavefields based on lowrank approximation in TTI media | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delrdecomp | user/chengjb/Mtti2delrdecomp.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delrdecomp1p | user/chengjb/Mtti2delrdecomp1p.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delrdecomp2p | user/chengjb/Mtti2delrdecomp2p.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delrsep | user/chengjb/Mtti2delrsep.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delrsep1p | user/chengjb/Mtti2delrsep1p.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delrsep2p | user/chengjb/Mtti2delrsep2p.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delrsep2ps | user/chengjb/Mtti2delrsep2ps.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delrsep2pTrueAmp | user/chengjb/Mtti2delrsep2pTrueAmp.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delrseparation | user/chengjb/Mtti2delrseparation.c | 2-D two-components elastic displacement wavefield snapshot modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delrseparators | user/chengjb/Mtti2delrseparators.cc | Construct low-rank approximate wave mode separators | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2delrsepwcl | user/chengjb/Mtti2delrsepwcl.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2desep | user/chengjb/Mtti2desep.c | 2-D two-components wavefield modeling using original elastic displacement wave equation in TTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2devectorlrsvd | user/chengjb/Mtti2devectorlrsvd.cc | 2-D two-components elastic wavefield extrapolation and vector decomposition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2devectorlrsvd_double | user/chengjb/Mtti2devectorlrsvd_double.cc | 2-D two-components elastic wavefield extrapolation and vector decomposition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2devectorlrsvdkspace_double | user/chengjb/Mtti2devectorlrsvdkspace_double.cc | 2-D two-components elastic wavefield extrapolation and vector decomposition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2devectorlrsvdkspace_double_stiffness | user/chengjb/Mtti2devectorlrsvdkspace_double_stiffness.cc | 2-D two-components elastic wavefield extrapolation and vector decomposition | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2dpseudop | user/chengjb/Mtti2dpseudop.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in TTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2dpseudop1 | user/chengjb/Mtti2dpseudop1.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in TTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2dpseudop2 | user/chengjb/Mtti2dpseudop2.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in TTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2dpseudoplrsep | user/chengjb/Mtti2dpseudoplrsep.cc | 2-D two-components wavefield modeling based on pseudo-pure mode P-wave equation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2dpseudoplrsep1 | user/chengjb/Mtti2dpseudoplrsep1.cc | 2-D two-components wavefield modeling based on pseudo-pure mode P-wave equation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti2dpseudosvlrsep | user/chengjb/Mtti2dpseudosvlrsep.cc | 2-D two-components wavefield modeling based on pseudo-pure mode P-wave equation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti3de | user/chengjb/Mtti3de.c | 3-D three-components wavefield modeling using elasic wave equation in tilted TI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti3dehomo | user/chengjb/Mtti3dehomo.c | 3-D three-components wavefield modeling using elasic wave equation in TTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti3delastic | user/chengjb/Mtti3delastic.c | 3-D three-components wavefield modeling using elasic wave equation in tilted TI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti3delasticlrdecomp | user/chengjb/Mtti3delasticlrdecomp.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti3delasticlrsep | user/chengjb/Mtti3delasticlrsep.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti3delrdecompP | user/chengjb/Mtti3delrdecompP.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti3delrdecompSV | user/chengjb/Mtti3delrdecompSV.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti3delrsep | user/chengjb/Mtti3delrsep.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti3delrsep1 | user/chengjb/Mtti3delrsep1.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti3delrseparators1 | user/chengjb/Mtti3delrseparators1.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti3delrsephomo | user/chengjb/Mtti3delrsephomo.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti3delrsepP | user/chengjb/Mtti3delrsepP.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti3delrsepSH | user/chengjb/Mtti3delrsepSH.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti3delrsepSV | user/chengjb/Mtti3delrsepSV.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftti4rtm | user/songxl/Mtti4rtm.c | 2-D Fourier finite-difference wave extrapolation: MPI + OMP | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfttieikonal | user/uwaheed/Mttieikonal.c | Fast sweeping TTI eikonal solver (2D) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfttifd2d | user/psava/Mttifd2d.c | 2D TTI time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfttifd3d | user/psava/Mttifd3d.c | 3D TTI time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfttimod | user/nobody/Mttimod.c | 2D TTI time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfTTinv | user/mehdi/MTTinv.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfttirtmsa | user/songxl/Mttirtmsa.c | 2-D TTI FFD RTM: MPI + OMP | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftvmf | user/yliu/Mtvmf.c | 1D Time-varying median filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftwoapp | user/fangg/Mtwoapp.cc | using weighted least square | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftwoapps | user/fangg/Mtwoapps.cc | using weighted least square | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftwodip2 | user/pwd/Mtwodip2.c | 2-D two dip estimation by plane wave destruction. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftwofreq2 | user/fomels/Mtwofreq2.c | 2-D two spectral component estimation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftwofreq3 | user/fomels/Mtwofreq3.c | 2-D two spectral component estimation. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftwolayer2dti | user/chengjb/Mtwolayer2dti.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftwolayer3dort | user/chengjb/Mtwolayer3dort.c | 3-D three-components wavefield modeling using general anisotropy | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftwolayer3dti | user/chengjb/Mtwolayer3dti.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftxrna | user/yliu/Mtxrna.c | Causal t-x or t-x-y nonstationary regularized autoregression. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftxrna2 | user/yliu/Mtxrna2.c | 2D space-noncausal t-x nonstationary regularized autoregression. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftxrna3 | user/yliu/Mtxrna3.c | 3D space-noncausal t-x-y nonstationary regularized autoregression. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftxsorth | user/yliu/Mtxsorth.c | Streaming orthogonalize signal and noise in t-x domain. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftxspf | user/yliu/Mtxspf.c | Streaming prediction filter in t-x domain. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftxspfint2 | user/yliu/Mtxspfint2.c | Missing data interpolation using t-x streaming prediction filter with causal structure. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftxspfvsint2 | user/yliu/Mtxspfvsint2.c | Missing data interpolation using t-x streaming prediction filter with varying smoothness and noncausal structure. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftxt2rsf | user/chenyk/Mtxt2rsf.c | Text (ASCII) file (like a matrix) to RSF file | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftxyspfint3 | user/yliu/Mtxyspfint3.c | Missing data interpolation using t-x-y streaming prediction filter with x-axis causal structure. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sftxyspfvsint3 | user/yliu/Mtxyspfvsint3.c | Missing data interpolation using t-x-y streaming prediction filter with varying smoothness and noncausal structure. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfucor | user/psava/Mucor.c | Interferometric cross-correlation of time series (zero-lag output) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfunfault | user/zhiguang/Munfault.c | Unfault image | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfungrad | user/gee/Mungrad.c | Phase unwrapping by least squares. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfunique | user/sujith/Munique.c | Unique values in trace | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfupgrad | user/fomels/Mupgrad.c | Causal gradient operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfupsamp1 | user/zhiguang/Mupsamp1.c | 1-D linear interpolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfv2d | user/yliu/Mv2d.c | Velocity convert to dip. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvam | user/hpcss/Mvam.c | Create a layered model. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvar2 | user/fomels/Mvar2.c | Variogram from irregular 2-D data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvariogram | user/yliu/Mvariogram.c | Compute a variogram of data values. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvariogram2 | user/yliu/Mvariogram2.c | Compute a horizontal variogram of data slice. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvconvert | user/yliu/Mvconvert.c | 2-D velocity mapping from manual picking to rsf RMS format. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfve2d | user/kourkina/Mve2d.c | Convert interval velocity to Dix velocity | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvel1d | user/ediazp/Mvel1d.c | Hungs a 1d velocity function from the Water bottom. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvelcon | user/fomels/Mvelcon.c | Post-stack velocity continuation by implicit finite differences | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvelcon3 | user/gee/Mvelcon3.c | 3-D finite-difference velocity continuation on a helix | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvelinv | user/fomels/Mvelinv.c | Velocity transform for generating velocity spectra and its corresponding hyperbolic modeling. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvelinvnew | user/seisinv/Mvelinvnew.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvelinvww | user/jun/Mvelinvww.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvelmap | user/browaeys/Mvelmap.c | 2-D mapping from moving-object velocity to plane-wave slowness | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvelsteer | user/browaeys/Mvelsteer.c | Velocity steering for 2D receivers array. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvelxf | user/jun/Mvelxf.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvelxf3 | user/seisinv/Mvelxf3.f90 | unknown | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvfsacrsnh | user/dirack/Mvfsacrsnh.c | Version 2.0 - Zero offset CRS parameters inversion (RN, RNIP, BETA) with Very Fast Simulated Aneeling (VFSA) Global Optimization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvidattr | user/fomels/Mvidattr.c | Slope-based velocity-independent data attributes. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvipmig0 | user/fomels/Mvipmig0.c | Velocity-independent phase-space zero-offset migration. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvirtualdata | user/yliu/Mvirtualdata.c | Construction of virtual seismic data. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfviscoa2d | user/pyang/Mviscoa2d.c | 2D visco-acoustic modeling with 8th order staggered-grid FD | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfviscoe2d | user/pyang/Mviscoe2d.c | 2D 4-th order visco-elastic wave propagation using sponge ABC | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvofzperm | user/fomels/Mvofzperm.c | V(z) prestack exploditing reflector. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvr | user/dellinger/Mvr.c | Plot impulse responses in 2 dimensions | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvr3d | user/dellinger/Mvr3d.c | Plot impulse responses in 3 dimensions | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvrtest | user/dellinger/Mvrtest.c | Plot impulse responses in 2 dimensions | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvsptmigda | user/aklokov/Mvsptmigda.cc | 3D time scattering-angle Kirchhoff migration for VSP data | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2de | user/chengjb/Mvti2de.c | 2-D two-components wavefield modeling using original elastic displacement wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2delasticlrsep | user/chengjb/Mvti2delasticlrsep.cc | 2-D two-components wavefield modeling using original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2delasticlrsep2ps | user/chengjb/Mvti2delasticlrsep2ps.cc | 2-D two-components wavefield modeling using original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2delasticsep | user/chengjb/Mvti2delasticsep.c | 2-D two-components wavefield modeling using original elastic displacement wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2delasticsepupdown | user/chengjb/Mvti2delasticsepupdown.c | 2-D two-components wavefield modeling using original elastic displacement wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2delrsep | user/chengjb/Mvti2delrsep.cc | 2-D two-components wavefield modeling using original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2delrsep2p | user/chengjb/Mvti2delrsep2p.cc | 2-D two-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2delrsep2ps | user/chengjb/Mvti2delrsep2ps.cc | 2-D two-components wavefield modeling using original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2delrseparation | user/chengjb/Mvti2delrseparation.c | 2-D two-components elastic displacement wavefield snapshot modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2delrseparators | user/chengjb/Mvti2delrseparators.cc | Construct low-rank approximate wave mode separators | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2delrsepTrueAmp | user/chengjb/Mvti2delrsepTrueAmp.cc | 2-D two-components wavefield modeling using original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2desep | user/chengjb/Mvti2desep.c | 2-D two-components wavefield modeling using original elastic displacement wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2desepupdown | user/chengjb/Mvti2desepupdown.c | 2-D two-components wavefield modeling using original elastic displacement wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2dpseudohomops | user/chengjb/Mvti2dpseudohomops.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2dpseudop | user/chengjb/Mvti2dpseudop.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2dpseudop1 | user/chengjb/Mvti2dpseudop1.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2dpseudopfvs0 | user/chengjb/Mvti2dpseudopfvs0.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2dpseudoplrsep | user/chengjb/Mvti2dpseudoplrsep.cc | 2-D two-components wavefield modeling based on pseudo-pure mode P-wave equation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2dpseudoplrsep1 | user/chengjb/Mvti2dpseudoplrsep1.cc | 2-D two-components wavefield modeling based on pseudo-pure mode P-wave equation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2dpseudoplrseprtm | user/chengjb/Mvti2dpseudoplrseprtm.cc | 2-D two-components wavefield modeling based on pseudo-pure mode P-wave equation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2dpseudosv | user/chengjb/Mvti2dpseudosv.c | 2-D two-components wavefield modeling using pseudo-pure mode qSV-wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti2dpseudosvlrsep | user/chengjb/Mvti2dpseudosvlrsep.cc | 2-D two-components wavefield modeling based on pseudo-pure mode SV-wave equation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti3de | user/chengjb/Mvti3de.c | 3-D three-components wavefield modeling using elasic wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti3dedivcurl | user/chengjb/Mvti3dedivcurl.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti3dedivcurlD | user/chengjb/Mvti3dedivcurlD.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti3dehomo | user/chengjb/Mvti3dehomo.c | 3-D three-components wavefield modeling using elasic wave equation in homogeneous VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti3delrdecompP | user/chengjb/Mvti3delrdecompP.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti3delrsep | user/chengjb/Mvti3delrsep.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti3delrsephomo | user/chengjb/Mvti3delrsephomo.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti3delrsephomoP | user/chengjb/Mvti3delrsephomoP.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti3delrsepomp | user/chengjb/Mvti3delrsepomp.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti3delrsepP | user/chengjb/Mvti3delrsepP.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti3delrsepSH | user/chengjb/Mvti3delrsepSH.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti3delrsepSV | user/chengjb/Mvti3delrsepSV.cc | 3-D three-components wavefield modeling based on original elastic anisotropic displacement | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti3dpseudosh | user/chengjb/Mvti3dpseudosh.c | 3-D three-components wavefield modeling using pure mode SH-wave equation in 3D VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvti3dpseudosv | user/chengjb/Mvti3dpseudosv.c | 3-D three-components wavefield modeling using pseudo-pure mode SV-wave equation in 3D VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvtihti2ort | user/zone/Mvtihti2ort.c | Combining VTI and HTI parameters to orthorhombic according to Schoenberg & Sayer (1995) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvtimod | user/nobody/Mvtimod.c | 2D VTI time-domain FD modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvweks3d | user/jsun/Mvweks3d.c | 3D visco-elastic time-domain pseudo-spectral (k-space) modeling using shared-memory parallel FFT | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfvwelr3 | user/jsun/Mvwelr3.cc | Lowrank symbol approxiamtion for 3-D recursive integral time extrapolation of visco-elastic waves (this program is deprecated) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwarp1 | user/fomels/Mwarp1.c | Multicomponent data registration by 1-D warping. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwarp2gamma | user/nobody/Mwarp2gamma.c | Convert warping function to gamma=Vp/Vs using LS and shaping regularization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwarpadd | user/fomels/Mwarpadd.c | Add a perturbation to the warping function. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwarpscan | user/fomels/Mwarpscan.c | Multicomponent data registration analysis. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwarpscann | user/chenyk/Mwarpscann.c | Multicomponent data registration analysis with non-stationary model smoothing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwarpscanw | user/sbader/Mwarpscanw.c | Multicomponent data registration analysis. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwave1 | user/songxl/Mwave1.c | 1-D finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwave124 | user/songxl/Mwave124.c | 1-D finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwave24 | user/hpcss/Mwave24.c | Rice HPCSS forward modeling. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwave2d | user/songxl/Mwave2d.c | 1-D finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwave2dss | user/songxl/Mwave2dss.c | 1-D finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwave4 | user/songxl/Mwave4.c | 1-D finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwaveab | user/songxl/Mwaveab.c | 1-D finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwaveadjtest | user/jsun/Mwaveadjtest.c | Complex 2-D wave propagation (with kiss-fft) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwavefft1 | user/songxl/Mwavefft1.c | 1-D finite-difference wave extrapolation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwavefrontamp | user/chengjb/Mwavefrontamp.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwavefrontamp360 | user/chengjb/Mwavefrontamp360.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwavefrontampReflect | user/chengjb/MwavefrontampReflect.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwavefrontampTransmit | user/chengjb/MwavefrontampTransmit.c | 2-D two-components wavefield modeling using pseudo-pure mode P-wave equation in VTI media. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwavegeom | user/roman/Mwavegeom.c | Rice HPCSS forward modeling. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwavegeompetsc | user/petsc/Mwavegeompetsc.c | Rice HPCSS forward modeling. | no | - | - | no | no | P4 | very high/unknown | no | unknown | yes |
| sfwavemis2 | user/yliu/Mwavemis2.c | Missing data interpolation in 2-D using wavelet transform and compressive sensing. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwavemixop | user/jsun/Mwavemixop.c | Complex 2-D wave propagation (with kiss-fft) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwavemovie | user/gee/Mwavemovie.c | Helmholtz factorization | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwavmod | user/chen/Mwavmod.c | 1-2-3D finite difference modeling | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwcfftexp2 | user/jsun/Mwcfftexp2.c | 2-D FFT-based zero-offset exploding reflector modeling/migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwcfftexp2adj | user/jsun/Mwcfftexp2adj.c | 2-D FFT-based zero-offset exploding reflector modeling/migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwcorr | user/gchliu/Mwcorr.c | Stack a dataset over the second dimensions by SNR weighted method. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwdf | user/psava/Mwdf.c | Assymptotic Wigner distribution | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfweas1 | user/fangg/Mweas1.c | 1-D analytic solution for acoustic wave equation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfweas2 | user/fangg/Mweas2.c | 2-D analytic solution for acoustic wave equation | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwefic | user/nobody/Mwefic.c | verbosity | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwei | user/psava/Mwei.c | 3-D modeling/migration with extended SSF | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfweiajs | user/psava/Mweiajs.c | Adjoint source construction for image-domain waveform tomography | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfweiajw | user/psava/Mweiajw.c | 3-D wave-equation wavefield continuation with adjoint-source | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfweigwf | user/psava/Mweigwf.c | 3-D wave-equation wavefield continuation with adjoint-source | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfweimc | user/nobody/Mweimc.c | 3-D imaging conditions for shot-profile WE migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwem2d_iso | user/jeff/Mwem2d_iso.c | 2D ISOTROPIC wave-equation finite-difference migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwex | user/psava/Mwex.c | 3-D modeling/migration with extended SSF | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwexic | user/cwp/Mwexic.c | Imaging Condition for WEXMIG | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfweximg | user/cwp/Mweximg.c | 3-D modeling/migration with extended SSF | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwexmig | user/cwp/Mwexmig.c (+1) | 3-D modeling/migration with extended SSF | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwexmva | user/cwp/Mwexmva.c (+1) | 3-D S/R WEMVA with extended split-step | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwexnmig | user/cwp/Mwexnmig.c | 3-D modeling/migration with extended SSF | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwexwfl | user/cwp/Mwexwfl.c (+1) | 3-D wavefield extrapolation with extended SSF | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwexzoimg | user/cwp/Mwexzoimg.c | 3-D zero-offset modeling/migration with extended SSF | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwexzomva | user/cwp/Mwexzomva.c | 3-D S/R WEMVA with extended split-step | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwigner | user/psava/Mwigner.c | Assymptotic Wigner distribution in space-time | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwile | user/bash/Mwile.c | Process data with GIMP 2.0. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwilson | user/gee/Mwilson.c | Wilson-Burg spectral factorization. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwindow1 | user/nobody/Mwindow1.c | Divide a dataset into smooth overlapping windows. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwindow2 | user/nobody/Mwindow2.c | Divide a dataset into 2-D smooth overlapping windows. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwindow3 | user/nobody/Mwindow3.c | Divide a dataset into 3-D smooth overlapping windows. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwinscan | user/yliu/Mwinscan.c | Picking scanned data window trace by trace with fixed t0 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwkbjTI | user/tariq/MwkbjTI.c | VTI eikonal solver (3-D). | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwlslfdc1 | user/fangg/Mwlslfdc1.cc | Weighted least square Lowrank FD coefficient on staggered grid (optimized) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwlslfdc1tw2 | user/fangg/Mwlslfdc1tw2.cc | Weighted least square Lowrank FD coefficient on staggered grid (optimized) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwlslfdc1ww | user/fangg/Mwlslfdc1ww.cc | Weighted least square Lowrank FD coefficient on staggered grid (optimized) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfwmf | user/yliu/Mwmf.c | 1D weighted median filtering. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfxcor2 | user/jsun/Mxcor2.c | OpenMP time- or freq-domain cross-correlation on axes 1,2,3 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfxcor2d | user/psava/Mxcor2d.c | OpenMP time- or freq-domain cross-correlation on axes 1,2,3 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfxcor3 | user/jsun/Mxcor3.c | OpenMP time- or freq-domain cross-correlation on axes 1,2,3,4 | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfxcor3d | user/jsun/Mxcor3d.c | OpenMP time- or freq-domain reversed cross-correlation on the fourth axes, read entire cube into memory | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfxcorr1 | user/nobody/Mxcorr1.c | Cross-correlation analysis. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfxtomo | user/gee/Mxtomo.c | Kjartansson-style tomography | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfycvelinvww | user/chenyk/Mycvelinvww.c | Inverse velocity spectrum with interpolation by modeling from inversion result (C version) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfycvelxf | user/chenyk/Mycvelxf.c | Velocity transform for generating velocity spectra and its corresponding hyperbolic modeling (C version) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzanisolr2 | user/jsun/Mzanisolr2.cc | q horizontal vs q vertical | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzanisolr2abc | user/jsun/Mzanisolr2abc.cc | from eta to q | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzcwt | user/yliu/Mzcwt.c | Improve signal resolution using zero-crossing of wavelet transform. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzerocross | user/saragiotis/Mzerocross.c | Zero crossings. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzerotrace | user/chenyk/Mzerotrace.c | Zero part of traces in order to make aliasing | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzfraclr2 | user/jsun/Mzfraclr2.cc | viscoacoustic | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzisolr2abc | user/jsun/Mzisolr2abc.cc | absorbing boundary | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzmarch | user/fomels/Mzmarch.c | Phase-space traveltime (marching in z) | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzoimg3 | user/nobody/Mzoimg3.c | 3-D zero-offset modeling/migration with extended SSF with time images | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzolsrtm2 | user/jsun/Mzolsrtm2.c | 2-D FFT-based zero-offset exploding reflector modeling/migration linear operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzomig3 | user/psava/Mzomig3.c | 3-D zero-offset modeling/migration with extended SSF | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzomiso | user/xuxin/Mzomiso.c | zero-offset isotropic reverse-time migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzomvti | user/xuxin/Mzomvti.c | acoustic VTI wavefield | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzortholr3 | user/jsun/Mzortholr3.cc | from degrees to radians | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzortmgmres | user/jsun/Mzortmgmres.c | 2-D FFT-based zero-offset exploding reflector modeling/migration linear operator | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfzowei | user/psava/Mzowei.c | 3-D zero-offset modeling/migration | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfztrace | user/fomels/Mztrace.c | Multiple arrivals by depth marching. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfztrace2 | user/nobody/Mztrace2.c | Multiple arrivals by depth marching. | no | - | - | no | no | P4 | unknown | unknown | unknown | yes |
| sfadd | system/main/add.c | Add, multiply, or divide  RSF datasets. | yes | pymadagascar.generic.array_math.add_rsf | pymadagascar.cli.add | yes | no | covered | done | yes | optional | no |
| sfagc | system/generic/Magc.c | Automatic gain control. | yes | pymadagascar.seismic.agc.agc_rsf | pymadagascar.cli.agc | yes | no | covered | done | yes | optional | no |
| sfattr | system/main/attr.c | Display dataset attributes. | yes | pymadagascar.generic.attr.attr_rsf | pymadagascar.cli.attr | yes | yes | covered | done | yes | optional | no |
| sfbandpass | system/generic/Mbandpass.c | Bandpass filtering. | yes | pymadagascar.signal.filter.bandpass_rsf/lowpass_rsf/highpass_rsf | pymadagascar.cli.bandpass/lowpass/highpass | yes | yes | covered | done | yes | optional | no |
| sfcat | system/main/cat.c | Concatenate datasets. | yes | pymadagascar.generic.cat.cat_rsf | pymadagascar.cli.cat | yes | yes | covered | done | yes | optional | no |
| sfclip | book/rsf/school/clip_test/Mclip.c (+1) | Clip the data. | yes | pymadagascar.generic.array_math.clip_rsf | pymadagascar.cli.clip | yes | no | covered | done | yes | optional | no |
| sfconv | user/gee/Mconv.c | 1-D convolution. | yes | pymadagascar.signal.convolution.convolve_rsf | pymadagascar.cli.conv | yes | yes | covered | done | yes | optional | no |
| sfdd | system/main/dd.c | Convert between different formats. | yes | pymadagascar.generic.dd.convert_dtype_rsf | pymadagascar.cli.dd | yes | yes | covered | done | yes | optional | no |
| sfdipfilter | system/generic/Mdipfilter.c | Filter data based on dip in 2-D or 3-D. | yes | pymadagascar.seismic.fk.fk_filter | pymadagascar.cli.fkfilter | yes | yes | covered | done | yes | optional | no |
| sffft1 | system/generic/Mfft1.c | Fast Fourier Transform along the first axis. | yes | pymadagascar.signal.fft.fft_rsf/ifft_rsf/rfft_rsf | pymadagascar.cli.fft/ifft/rfft | yes | yes | covered | done | yes | optional | no |
| sfgraph | plot/main/graph.c | Graph plot. | yes | pymadagascar.plot.graph.graph | pymadagascar.cli.graph | yes | no | covered | done | yes | optional | no |
| sfgrey | plot/main/grey.c | Generate raster plot. | yes | pymadagascar.plot.grey.grey | pymadagascar.cli.grey | yes | no | covered | done | yes | optional | no |
| sfin | system/main/in.c | Display basic information about RSF files. | yes | pymadagascar.generic.info.info_rsf | pymadagascar.cli.info | yes | yes | covered | done | yes | optional | no |
| sfkirchnew | system/seismic/Mkirchnew.c | Kirchhoff 2-D post-stack time migration and modeling with antialiasing. | yes | pymadagascar.imaging.kirchhoff.kirchhoff_time_migration | pymadagascar.cli.kirchhoff | yes | yes | covered | done | yes | optional | no |
| sfmath | system/main/math.c | Mathematical operations on data files. | yes | pymadagascar.generic.math.math_rsf | pymadagascar.cli.math | yes | yes | covered | done | yes | optional | no |
| sfmute | user/dmerzlikin/Mmute.c | Mute a triangle region | yes | pymadagascar.seismic.mute.mute_rsf | pymadagascar.cli.mute | yes | no | covered | done | yes | optional | no |
| sfnmo | system/seismic/Mnmo.c | Normal moveout. | yes | pymadagascar.seismic.nmo.nmo_correct | pymadagascar.cli.nmo | yes | yes | covered | done | yes | optional | no |
| sfpad | system/main/pad.c | Pad a dataset with zeros. | yes | pymadagascar.generic.pad.pad_rsf | pymadagascar.cli.pad | yes | yes | covered | done | yes | optional | no |
| sfpow | system/generic/Mpow.c | Apply power gain. | yes | pymadagascar.seismic.gain.gain_rsf | pymadagascar.cli.gain | yes | yes | covered | done | yes | optional | no |
| sfput | system/main/put.c | Input parameters into a header. | yes | pymadagascar.generic.put.put_header | pymadagascar.cli.put | yes | yes | covered | done | yes | optional | no |
| sfreshape | user/fomels/Mreshape.c | Non-stationary spectral balancing. | yes | pymadagascar.generic.transp.reshape_rsf | pymadagascar.cli.reshape | yes | no | covered | done | yes | optional | no |
| sfscale | system/main/scale.c | Scale data. | yes | pymadagascar.generic.array_math.scale_rsf | pymadagascar.cli.scale | yes | yes | covered | done | yes | optional | no |
| sfsegyread | system/seismic/Msegyread.c | Convert a SEG-Y or SU dataset to RSF. | yes | pymadagascar.io.segy.segy_to_rsf | pymadagascar.cli.segyread | yes | yes | covered | done | yes | optional | no |
| sfsegywrite | system/seismic/Msegywrite.c | Convert an RSF dataset to SEGY or SU. | yes | pymadagascar.io.segy.rsf_to_segy | pymadagascar.cli.segywrite | yes | no | covered | done | yes | optional | no |
| sfslant | system/seismic/Mslant.c | Time-space-domain Radon transform (slant stack) | yes | pymadagascar.seismic.radon.linear_radon/inverse_linear_radon | pymadagascar.cli.radon/iradon | yes | yes | covered | done | yes | optional | no |
| sfspike | system/main/spike.c | Generate simple data: spikes, boxes, planes, constants. | yes | pymadagascar.generic.spike.spike | pymadagascar.cli.spike | yes | yes | covered | done | yes | optional | no |
| sfspray | system/main/spray.c | Extend a dataset by duplicating in the specified axis dimension. | yes | pymadagascar.generic.spray.spray_rsf | pymadagascar.cli.spray | yes | yes | covered | done | yes | optional | no |
| sfstack | system/main/stack.c | Stack a dataset over one of the dimensions. | yes | pymadagascar.seismic.stack.stack_rsf | pymadagascar.cli.stack | yes | yes | covered | done | yes | optional | no |
| sftransp | system/main/transp.c | Transpose two axes in a dataset. | yes | pymadagascar.generic.transp.transpose_rsf | pymadagascar.cli.transp | yes | yes | covered | done | yes | optional | no |
| sfvscan | system/seismic/Mvscan.c | Velocity analysis. | yes | pymadagascar.seismic.semblance.semblance_scan | pymadagascar.cli.semblance | yes | yes | covered | done | yes | optional | no |
| sfwiggle | plot/main/wiggle.c | Plot data with wiggly traces. | yes | pymadagascar.plot.wiggle.wiggle | pymadagascar.cli.wiggle | yes | no | covered | done | yes | optional | no |
| sfwindow | system/main/window.c | Window a portion of a dataset. | yes | pymadagascar.generic.window.window_rsf | pymadagascar.cli.window | yes | yes | covered | done | yes | optional | no |
| sfxcorr | user/chenyk/Mxcorr.c | Cross-correlation function | yes | pymadagascar.signal.convolution.xcorr_rsf | pymadagascar.cli.xcorr | yes | no | covered | done | yes | optional | no |
| sfdatstretch | alias:sfstretch | alias of sfstretch | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sfdiv | alias:sfadd | alias of sfadd divide mode | yes | pymadagascar.generic.array_math.divide_rsf | pymadagascar.cli.div | yes | yes | Done B-2 | low | yes | no | subset differs: explicit zero_policy |
| sfimag | alias:sfreal | alias of sfreal | yes | pymadagascar.generic.complex_tools.imag_rsf | pymadagascar.cli.imag | yes | yes | covered | done | yes | no | no |
| sflmostretch | alias:sfstretch | alias of sfstretch | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sflogstretch | alias:sfstretch | alias of sfstretch | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sfmax | alias:sfstack | alias of sfstack | yes | `max_rsf` | `python -m pymadagascar.cli.max` | yes | yes | Done B-1 | low | yes | no | subset differs: text statistics |
| sfmerge | alias:sfcat | alias of sfcat | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sfmin | alias:sfstack | alias of sfstack | yes | `min_rsf` | `python -m pymadagascar.cli.min` | yes | yes | Done B-1 | low | yes | no | subset differs: text statistics |
| sfmul | alias:sfadd | alias of sfadd multiply mode | yes | pymadagascar.generic.array_math.multiply_rsf | pymadagascar.cli.mul | yes | yes | Done B-2 | low | yes | no | subset: one other RSF or scalar |
| sfmv | alias:sfcp | alias of sfcp | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sfnmomcmctrans | book/tccs/timewarp/mcmc2D/Mnmomcmctrans.c | 2D NMO GMA MCMC transdimensional inversion with Metropolis rule (Mosegaard and Tarantola, 1995) | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sfnmostretch | alias:sfstretch | alias of sfstretch | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sfnonlocal | book/geo384s/hw0/Mnonlocal.c (+2) | Non-local smoothing. | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sfprod | alias:sfstack | alias of sfstack | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sfradstretch | alias:sfstretch | alias of sfstretch | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sfrcat | alias:sfcat | alias of sfcat | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sfscalestretch | alias:sfstretch | alias of sfstretch | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sfsuread | alias:sfsegyread | alias of sfsegyread | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sfsuwrite | alias:sfsegywrite | alias of sfsegywrite | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sft2chebstretch | alias:sfstretch | alias of sfstretch | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |
| sft2stretch | alias:sfstretch | alias of sfstretch | no | - | - | no | no | unknown | unknown | unknown | unknown | unknown |

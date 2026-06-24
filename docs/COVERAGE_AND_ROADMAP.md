# Coverage and Roadmap

## Coverage Summary

| Scope | Current value | Notes |
| --- | ---: | --- |
| Full Madagascar/alias command surface | `129 / 2114 = 6.10%` | Conservative denominator including `user/*` and aliases; M3-6 changes numerator only. |
| Core `system/` + `plot/main` command surface | `116 / 301 = 38.54%` | Better near-term project signal; denominator unchanged. |
| Direct `system/main` source-backed commands | `37 / 39 = 94.87%` | Includes B-1, B-2, B-3-1, `sfheadersort`, B-4, M0-1 `sfscale`/`sfrotate`, M0-2 `sfstack`, and M0-3 `sfpad`/`sfspray`. |
| `user/*` command surface | about `12 / 1792 = 0.67%` | Not a near-term target. |

Coverage is a command-surface audit, not a promise of full upstream parameter
compatibility.

## G4-1 Source Reading Pass

G4-1 intentionally adds no command coverage. It pauses source-gap batches after
M3-6 and records a read-only Original Madagascar source architecture review in
`docs/MADAGASCAR_SOURCE_READING.md`. Future implementation passes should use
that risk map plus `docs/CODE_COMMENT_GUIDE.md` before counting any new
source-backed command.

## Learning Roadmap Index

`docs/PYMADAGASCAR_LEARNING_GUIDE.ipynb` presents a study-oriented index for
interfaces, maturity boundaries, completed stages, deferred topics, and selected
operator/inversion formulas. It is a navigation aid rather than a second
coverage source: the table above and the source mappings below remain
authoritative. Future user-visible capabilities, algorithm topics, important
workflows, or formula explanations may update the notebook when that adds
learning value.

## Completed Stage B and C Batches

Stage B-1:

- `sfcp`: safe file-backed RSF copy subset.
- `sfrm`: safe file-backed RSF remove subset with explicit confirmation.
- `sfmin` and `sfmax`: script-friendly text statistics; upstream commands are
  `sfstack` aliases, so these are not full alias clones.

Stage B-2:

- `sfmul` and `sfdiv`: RSF/scalar and RSF/RSF array math subsets.
- `sftpow`: coordinate-based `t ** power` gain subset.
- `sfinterleave`: same-shape interleave subset.

Stage B-3-1:

- `sfheaderwindow`: ordinary-RSF mask/header continuous-window subset.
- `sfheadercut`: ordinary-RSF mask/header cut subset.

Stage B-3-2:

- Minimal RSF-backed header table model: numeric two-dimensional RSF table,
  `n1=key count`, `n2=row/trace count`, key names in `key1/key2/...` and
  `header_keys=`.
- `sfheaderattr`: module-only statistics subset for selected table keys.
- `sfheadermath`: module-only safe-expression subset for creating or replacing
  table keys.
- `sfheadersort`: module-only stable row-sort subset for the header table
  itself.

Stage B-4:

- Minimal pure-Python linear-operator model with forward/adjoint methods,
  dense `MatrixOperator`, callable toy operators, and identity test support.
- `sfdottest`: module-only real matrix-backed dot-product test subset.
- `sfcdottest`: module-only complex matrix-backed dot-product test subset using
  Hermitian adjoints.
- `sfconjgrad`: module-only small real SPD/normal-equation CG subset.
- `sfcconjgrad`: module-only small complex Hermitian/normal-equation CG subset.

Stage C-1:

- `sfcostaper`: module-only 1D/2D/3D boundary cosine taper subset.
- `sfthreshold`: module-only hard/soft explicit-value threshold subset.
- `sfspectra`: module-only simple RFFT amplitude/power spectrum subset.
- `sfenvelope`: module-only FFT Hilbert analytic-signal envelope subset.
- RSFData convenience methods: `costaper`, `threshold`, `spectra`, and
  `envelope`.

Stage C-2:

- `sflinear`: module-only regular-axis linear resampling subset.
- `sfbin`: module-only small table-to-2D-grid binning subset.
- `sfslice`: module-only fixed-index axis slicing subset.
- `sfmax1`: module-only maximum value/index/coordinate picking subset.
- RSFData convenience methods: `linear`, `slice`, and `max1`.

Stage C-3:

- `sfautocorr`: module-only trace autocorrelation subset.
- `sfconvolve`: module-only explicit two-input convolution subset.
- `sfcconv`: module-only circular convolution subset.
- `sfenvcorr`: module-only envelope cross-correlation subset.
- `sfshifts`: module-only integer sample-shift subset.
- `sfstacks`: module-only statistical stack subset.
- RSFData convenience methods: `autocorr`, `convolve`, `cconv`, `envcorr`,
  `shifts`, and `stacks`.

Stage C-4:

- `sfderiv`: module-only first finite-difference derivative subset.
- `sfcausint`: module-only forward causal cumulative-integration subset.
- `sfintegral`: module-only cumsum/trapezoid numerical-integration subset.
- `sfclip2`: module-only explicit/percentile amplitude-clipping subset.
- `sfmutter`: module-only regular-axis linear above/below mute subset.
- `sfdiff`: module-only whole-dataset difference-metric subset, selected in
  place of trace-header-driven `sffold`.
- RSFData convenience methods: `deriv`, `causint`, `integral`, `clip2`,
  `mutter`, and `diff`.

Stage C-5:

- Module-only `abs`, `sign`, `sqrt`, `log`, `exp`, and `pow` convenience
  transforms sharing one NumPy-backed implementation.
- `sfhistogram`: module-only finite-sample histogram table subset.
- `sfquantile`: module-only global/axis quantile RSF subset.
- RSFData convenience methods: `abs`, `sign`, `sqrt`, `log`, `exp`, `pow`,
  `histogram`, and `quantile`.
- Added eight CLI modules but only two command-surface entries: the first five
  unary names are `sfmath` functions rather than upstream executables, and
  `pow` intentionally does not duplicate the already-counted upstream axis-gain
  `sfpow`/`sftpow` surface.

Stage C-6:

- Module-only `mean`, `rms`, `var`, `std`, `median`, and `range` global/axis
  statistics with explicit NaN policy and float64 output.
- Module-only `isnan` finite/non-finite int32 masks and `fillnan` replacement.
- RSFData convenience methods for all eight functions; the min/max method is
  named `range_stats`.
- Added eight CLI modules but only one command-surface entry. The audited
  `sfmedian` directly reduces axis 1. Upstream `sfmean` and `sfrms` are local
  filters with different semantics, and the remaining names have no matching
  standalone program in the audited tree.

Stage C-7:

- Module-only `demean`, `detrend`, `decimate`, `bandstop`, `notch`, and
  `localrms` signal/small-gather QC conveniences.
- Shared NumPy APIs, file-backed RSF wrappers, RSFData chain methods, focused
  API/CLI tests, and `examples/signal_qc_foundation_demo.py`.
- No standalone upstream programs were found for the first five names.
  `../src-master/user/luke/Mrms.c` is related to local RMS but has a
  multidimensional `rect#` and different boundary contract.
- All six are conservatively uncounted. Full, core, and direct-system/main
  coverage therefore remain unchanged.

Stage C-8:

- Module-only `windowfunc`, `psd`, `csd`, `coherence`, `spectrogram`, and
  `snr` spectral-QC conveniences.
- Shared NumPy APIs, RSF wrappers, RSFData chain methods, focused API/CLI
  tests, and `examples/spectral_qc_demo.py`.
- Upstream `Mspectra.c` is amplitude spectrum, `Mcostaper.c` is a border
  taper, `user/chen/Mcoherence.c` is local spatial coherence, and
  `user/yliu/Mstft.c`/`Msnr.c` have different names and contracts.
- All six are conservatively uncounted. Full, core, and direct-system/main
  coverage remain unchanged.

Stage C-9:

- Module-only `welch`, `welchcsd`, `transfer`, `whiten`, `specnorm`, and
  `freqattr` spectral averaging, response, conditioning, and attribute
  conveniences.
- Shared NumPy APIs, RSF wrappers, RSFData chain methods, focused API/CLI
  tests, and `examples/spectral_averaging_attributes_demo.py`.
- The upstream audit found related `Mspectra.c`, user STFT,
  `user/yliu/Mdominantf.c`, `user/fomels/Mabalance.c`, and
  `user/karl/Mtahspecbal.c` programs, but no matching standalone contracts for
  the six C-9 names.
- All six are conservatively uncounted. Full, core, and direct-system/main
  coverage remain unchanged.

Stage C-10:

- Module-only `firwin`, `firfilter`, `filtfilt`, `freqz`, `bandenergy`, and
  `filterbank` FIR design, application, response, and frequency-band QC
  conveniences.
- Shared NumPy APIs, RSF wrappers, four RSFData chain methods, focused API/CLI
  tests, and `examples/fir_filter_design_demo.py`.
- Core `system/generic/Mbandpass.c` is Butterworth-based.
  `user/chen/Mfir.c` applies an existing integer-origin FIR, and
  `Mfbank1.c`/`Mfbank2.c` are interpolation filter banks rather than explicit
  frequency-band decomposition.
- No C-10 name has a matching standalone upstream contract, so all six remain
  conservatively uncounted and all coverage values remain unchanged.

Quality Pass Q1:

- Audited 204 exported package names, 47 public `RSFData` attributes/methods,
  94 CLI modules, 25 registered console scripts, 28 top-level examples, five
  workflow scripts, release tools, current docs, and related tests.
- Kept stable names intact while documenting mute/mutter, stack/stacks,
  clip/clip2/threshold, convolution/correlation families, dd/diff, and
  get/info/attr/headerattr.
- Unified the internal second-operand path for `RSFData.convolve`, `cconv`,
  `envcorr`, and `diff`.
- Added shape/header/dtype and inplace behavior contracts, full top-level
  example smoke tests, and `tools/check_examples_inventory.py`.

Release Quality Pass Q2:

- Fixed default editable installation so pure Python wheels skip CMake and do
  not require Ninja or a compiler.
- Added a root package README, public version metadata, optional `cpp` build
  extra, and ignored-output policy.
- Validated all 102 CLI modules with `python -m ... --help` and all 25
  installed console scripts with `--help`.
- Strengthened release tools and tests for package metadata, CLI runtime
  targets, authoritative docs, examples, fallback behavior, and optional WSL.
- Command-surface coverage is unchanged because Q2 adds no commands.

Roadmap Reassessment R1:

- Reclassified the current APIs, CLIs, examples, and workflows by technical
  topic and maturity.
- Added the capability matrix and ranked route options below.
- Added no command, API, console script, test file, or example.
- Command-surface coverage remains `86 / 2114`, core coverage remains
  `73 / 301`, and direct `system/main` coverage remains `32 / 39`.

M0-1:

- Resumes source-aligned Madagascar command coverage after the F0 forward
  modeling loop and explicitly pauses further Forward Modeling expansion.
- The small source audit covered only `../src-master/system/main`,
  `../src-master/system/generic`, and `../src-master/system/seismic`.
- Adds `sfrotate` from `../src-master/system/main/rotate.c` as a pure NumPy
  cyclic-axis rotation subset with Python API, RSFData method, CLI module,
  console script, and focused tests.
- Promotes the existing scalar `sfscale` subset from
  `../src-master/system/main/scale.c` to registered console-script coverage
  with a focused CLI/help smoke path.
- Counts both `sfrotate` and `sfscale` in command-surface coverage because
  they correspond to direct `system/main` source files. No Pythonic-only
  convenience is counted in M0-1.
- Coverage numerator changes to `88 / 2114`, core coverage to `75 / 301`, and
  direct `system/main` coverage to `34 / 39`; all denominators remain
  unchanged.

M0-2:

- Continues source-aligned direct `system/main` command coverage and does not
  continue Forward Modeling, DAS, Localization, solver, notebook, or CI-known
  issue work.
- The small source audit covered only `../src-master/system/main`. Covered
  direct commands include stable subsets for spike/math/window/info/get/disfil/
  attr/put/dd/cat/transp/complex tools, cp/rm, mask/cut/reverse, add-family
  aliases, interleave, scale, rotate, headerwindow/headercut/headersort,
  dottest/cdottest, conjgrad/cconjgrad, and the M0-2 `sfstack` registration.
- Remaining direct `system/main` gaps are deferred: `in.c` is mostly an
  install/path diagnostic, `mpi.c` and `omp.c` are environment diagnostics,
  `pad.c` and `spray.c` still need a separate direct source-alignment pass,
  and the `*mpi.c` variants require MPI/external execution.
- Registers the existing `sfstack` bounded subset from
  `../src-master/system/main/stack.c` as `pymada-stack` and confirms
  `pymadagascar.seismic.stack.stack_rsf`, `RSFData.stack(...)`, and
  `python -m pymadagascar.cli.stack`.
- Counts `sfstack` in command-surface coverage because it maps to a direct
  `system/main` source file. No Pythonic-only convenience is counted in M0-2.
- Coverage numerator changes to `89 / 2114`, core coverage to `76 / 301`, and
  direct `system/main` coverage to `35 / 39`; all denominators remain
  unchanged.

M0-3:

- Continues source-aligned direct `system/main` command coverage and does not
  continue Forward Modeling, DAS, Localization, solver, notebook, or
  Windows-only CI known-issue work.
- The source audit covered only `../src-master/system/main/pad.c` and
  `../src-master/system/main/spray.c`. `pad.c` pads RSF axes with zeros using
  `beg#`, `end#`, and `n#`/`n#out` output-length requests, updating `n#` and
  shifting `o#` when leading samples are inserted. `spray.c` inserts a new axis
  at `axis=` and duplicates each input block `n=` times while writing optional
  `o=`, `d=`, `label=`, and `unit=` metadata.
- Registers the existing bounded `sfpad` and `sfspray` subsets from
  `../src-master/system/main/pad.c` and
  `../src-master/system/main/spray.c` as `pymada-pad` and `pymada-spray`, and
  adds `RSFData.pad(...)` / `RSFData.spray(...)` chain methods.
- `sfpad` supports in-memory constant-value padding with `beg#`, `end#`,
  `n#`/`n#out`, including safe extension to new singleton-derived axes.
  `sfspray` supports in-memory new-axis insertion with `axis=`, `n=`, `o=`,
  `d=`, `label=`, and `unit=`.
- M0-3 does not implement streaming/out-of-core execution, byte-level native
  trace copying, arbitrary `sfput` passthrough, non-constant border modes, or
  any `in.c`, `mpi.c`, `omp.c`, or MPI-variant command.
- Counts both commands in command-surface coverage because they map to direct
  `system/main` source files. No Pythonic-only convenience is counted in M0-3.
- Coverage numerator changes to `91 / 2114`, core coverage to `78 / 301`, and
  direct `system/main` coverage to `37 / 39`; all denominators remain
  unchanged.

M1-1:

- Starts the post-M0 `system/generic` command migration batch and does not
  continue Forward Modeling, DAS, Localization, solver, notebook, or
  Windows-only CI known-issue work.
- The source audit covered only
  `../src-master/system/generic/Mclip.c`,
  `../src-master/system/generic/Mboxsmooth.c`,
  `../src-master/system/generic/Msmooth.c`,
  `../src-master/system/generic/Mlaplac.c`,
  `../src-master/system/generic/Mtrapez.c`, and
  `../src-master/system/generic/Mnoise.c`.
- Counts `sfclip`, `sfnoise`, and `sfboxsmooth` because they map directly to
  `system/generic` source files and now have Python API, RSFData chain method,
  CLI/module or console-script surface, focused tests, and documented bounded
  behavior.
- `sfclip` supports `clip=` plus optional `value=` and source-aligned
  non-finite replacement. `sfnoise` supports small deterministic add/replace
  normal/uniform noise. `sfboxsmooth` supports centered in-memory box kernels
  with `rect#`, `axis=`, and `repeat=`.
- Defers `sfsmooth` because upstream includes triangle, box, adjoint, and
  differentiation modes; `sflaplac` because it is a separate finite-difference
  operator; and `sftrapez` because upstream is an FFT trapezoidal frequency
  filter rather than a simple spatial taper.
- Coverage numerator changes to `94 / 2114` and core coverage to `81 / 301`.
  Direct `system/main` coverage remains `37 / 39`; all denominators remain
  unchanged.

M1-2:

- Continues source-aligned `system/generic` command migration with the
  operator/filter group deferred in M1-1. It does not continue Forward
  Modeling, DAS, Localization, solver, notebook, or Windows-only CI
  known-issue work.
- The source audit covered only
  `../src-master/system/generic/Mlaplac.c`,
  `../src-master/system/generic/Msmooth.c`, and
  `../src-master/system/generic/Mtrapez.c`, plus their small helper sources
  where needed to identify stencil and frequency-response behavior.
- Counts `sflaplac`, `sfsmooth`, and `sftrapez` because they map directly to
  `system/generic` source files and now have Python API, RSFData chain method,
  CLI/module or console-script surface, focused tests, and documented bounded
  behavior.
- `sflaplac` supports a real-valued in-memory graph-Laplacian subset using
  the source-aligned `center - neighbor` sign, optional selected axes, and
  `d#` spacing. `sfsmooth` supports centered triangle smoothing with `rect#`,
  `axis=`, and `repeat=` while leaving upstream adjoint/differentiation modes
  out of scope. `sftrapez` supports one-axis real-input RFFT trapezoidal
  filtering with `frequency=f1,f2,f3,f4` or `f1/f2/f3/f4`.
- M1-2 does not implement streaming/out-of-core execution, complex input,
  `sfsmooth adj=`/`diff#` modes, `sftrapez` byte-identical FFT rounding, or
  a Laplacian coefficient field/inverse solver.
- Coverage numerator changes to `97 / 2114` and core coverage to `84 / 301`.
  Direct `system/main` coverage remains `37 / 39`; all denominators remain
  unchanged.

M1-3:

- Continues source-aligned `system/generic` command migration with the
  spectral/transform group after M1-2 and does not continue Forward Modeling,
  DAS, Localization, solver, notebook, or Windows-only CI known-issue work.
- The source audit covered only
  `../src-master/system/generic/Mfft1.c`,
  `../src-master/system/generic/Mfft3.c`,
  `../src-master/system/generic/Mcosft.c`,
  `../src-master/system/generic/Mspectra.c`,
  `../src-master/system/generic/Mspectra2.c`, and
  `../src-master/system/generic/Mcostaper.c`.
- Counts `sffft1`, `sfcosft`, and `sfspectra2` because they map directly to
  `system/generic` source files and now have Python API, RSFData chain method,
  CLI module, console-script surface, focused tests, and documented bounded
  behavior.
- `sffft1` supports one-axis real-to-complex RFFT and complex-to-real inverse
  with ordinary `fft_n#` metadata restoration. `sfcosft` supports one-axis
  real-valued orthonormal DCT-II/DCT-III transforms. `sfspectra2` supports an
  in-memory 2-D amplitude/power spectrum over two selected RSF axes, with
  optional averaging over remaining planes.
- Existing `sfcostaper` and `sfspectra` were audited against
  `Mcostaper.c` and `Mspectra.c`, but they were already counted in Stage C-1
  and are not counted again. `sffft3` is deferred because upstream is a
  complex-input padded extra-axis FFT with centering/sign behavior that is
  larger than this bounded batch.
- Coverage numerator changes to `100 / 2114` and core coverage to `87 / 301`.
  Direct `system/main` coverage remains `37 / 39`; all denominators remain
  unchanged.

M1-4:

- Continues source-aligned `system/generic` command migration with the
  interpolation/remap group after M1-3 and does not continue Forward Modeling,
  DAS, Localization, solver, notebook, or Windows-only CI known-issue work.
- The source audit covered only
  `../src-master/system/generic/Mlinear.c`,
  `../src-master/system/generic/Mremap1.c`,
  `../src-master/system/generic/Menoint2.c`,
  `../src-master/system/generic/Mspline.c`,
  `../src-master/system/generic/Msplinefilter.c`,
  `../src-master/system/generic/Mt2warp.c`, and
  `../src-master/system/generic/Mlogwarp.c`.
- Counts `sfremap1`, `sfspline`, and `sft2warp` because they map directly to
  `system/generic` source files and now have Python API, RSFData chain method,
  CLI module, console-script surface, focused tests, and documented bounded
  behavior.
- `sfremap1` supports one-axis regular-grid linear remapping with `axis=`,
  `n=`, `o=`, `d=`, and `fill_value=`. `sfspline` supports one-axis
  natural-cubic interpolation without SciPy. `sft2warp` supports a one-axis
  linear-interpolation time-squared warp and inverse using `n#_t2warp`
  metadata.
- Existing `sflinear` was audited against `Mlinear.c`, but it was already
  counted in Stage C-2 and is not counted again. `sfenoint2` is deferred
  because it depends on an external header-coordinate file and 2-D ENO
  interpolation ecology; `sfsplinefilter` is deferred because it is a
  B-spline coefficient prefilter; `sflogwarp` is deferred to avoid expanding a
  larger warp family in this batch.
- Coverage numerator changes to `103 / 2114` and core coverage to `90 / 301`.
  Direct `system/main` coverage remains `37 / 39`; all denominators remain
  unchanged.

M1-5:

- Continues source-aligned `system/generic` command migration with the array
  algebra / selection group after M1-4 and does not continue Forward Modeling,
  DAS, Localization, solver, notebook, or Windows-only CI known-issue work.
- The source audit covered only
  `../src-master/system/generic/Mmatmult.c`,
  `../src-master/system/generic/Mcmatmult.c`,
  `../src-master/system/generic/Mcmatmult2.c`,
  `../src-master/system/generic/Mequal.c`,
  `../src-master/system/generic/Mextract.c`,
  `../src-master/system/generic/Mmatch.c`,
  `../src-master/system/generic/Mlinefit.c`, and
  `../src-master/system/generic/Mmax1.c`.
- Counts `sfmatmult`, `sfmatch`, and `sflinefit` because they map directly to
  `system/generic` source files and now have Python API, RSFData chain method,
  CLI module, console-script surface, focused tests, and documented bounded
  behavior.
- `sfmatmult` supports real in-memory matrix-vector multiplication with
  optional `adj=`. `sfmatch` supports the source symmetric zero-boundary
  matching-filter loop in forward and adjoint forms. `sflinefit` supports
  ordinary least-squares `y=a*x+b` fitting from an `n1=2` table and evaluates a
  regular output grid.
- `sfmax1` was audited but already counted in Stage C-2. `sfequal` is upstream
  uchar histogram equalization rather than scalar equality and is deferred
  until byte/uchar RSF support is designed. `sfextract` depends on external
  header-coordinate 2D interpolation, `sfmatch` is kept to a small loop subset,
  and `sfcmatmult`/`sfcmatmult2` are deferred until complex matrix workflows
  are separately scoped.
- Coverage numerator changes to `106 / 2114` and core coverage to `93 / 301`.
  Direct `system/main` coverage remains `37 / 39`; all denominators remain
  unchanged.

M2-1:

- Starts source-aligned `system/seismic` command migration after the M1 generic
  coverage batches and does not continue Forward Modeling, DAS, Localization,
  solver, notebook, or Windows-only CI known-issue work.
- The source audit covered
  `../src-master/system/seismic/Menvelope.c`,
  `../src-master/system/seismic/Mfold.c`,
  `../src-master/system/seismic/Mfreqint.c`,
  `../src-master/system/seismic/Mc2r.c`,
  `../src-master/system/seismic/Mai2refl.c`,
  and `../src-master/system/seismic/Mavo.c`; requested optional names
  `Mi2refl.c`, `Mpick.c`, `Mmask.c`, and `Msemblance.c` were not present under
  those exact names in `system/seismic`.
- Counts `sfavo`, `sffold`, and `sfai2refl` because they map directly to
  `system/seismic` source files and now have Python API, RSFData chain method,
  CLI module, console-script surface, focused tests, and documented bounded
  behavior.
- `sfavo` supports in-memory real CMP gathers with RSF axis 1 as time and axis
  2 as offset, using ordinary least squares to output intercept and gradient.
  `sffold` supports numeric header-table 3D histograms with explicit
  `n/o/d/label` bins and zero-based column selection. `sfai2refl` supports
  one-axis acoustic impedance to reflectivity conversion with the last sample
  set to zero.
- `sfenvelope` was audited but already counted in Stage C-1. `sffreqint` is a
  complex freqlet regularization/inversion tool and `sfc2r` is Cartesian to
  Riemannian coordinate interpolation with ray fields, so both are deferred.
  `sffold` intentionally omits the SEG-Y key lookup ecology and uses numeric
  table columns only.
- Coverage numerator changes to `109 / 2114` and core coverage to `96 / 301`.
  Direct `system/main` coverage remains `37 / 39`; all denominators remain
  unchanged.

M2-2:

- Continues source-aligned `system/seismic` command migration with the
  moveout / trace-transform group after M2-1 and does not continue Forward
  Modeling, DAS, Localization, solver, notebook, Windows-only CI known-issue,
  migration, RTM, DMO, Kirchhoff, Gazdag, or wave-equation imaging work.
- The source audit covered
  `../src-master/system/seismic/Mnmo.c`,
  `../src-master/system/seismic/Mmoveout.c`,
  `../src-master/system/seismic/Mhalfint.c`,
  `../src-master/system/seismic/Mcos2ang.c`,
  `../src-master/system/seismic/Misin2ang.c`,
  `../src-master/system/seismic/Mmodrefl.c`,
  `../src-master/system/seismic/Mmodrefl2.c`,
  `../src-master/system/seismic/Mmap2coh.c`,
  `../src-master/system/seismic/Mlinsincos.c`, and
  `../src-master/system/seismic/Movc.c`.
- Counts `sfnmo`, `sfhalfint`, and `sfmoveout` because they map directly to
  `system/seismic` source files and now have Python API, RSFData chain method,
  CLI module, console-script surface, focused tests, and documented bounded
  behavior.
- `sfnmo` supports bounded hyperbolic NMO over regular time/offset gathers
  with scalar, 1-D, or per-gather velocity and optional explicit offsets.
  `sfhalfint` supports one-axis real FFT half-order integration or
  differentiation with `axis=`, `inv=`, `adj=`, and `rho=` metadata.
  `sfmoveout` supports the source-aligned moveout-time-table to unit-spike
  trace generator with `n1/o1/d1`, `eps=`, `nw=`, and bounded nearest/linear
  spike placement.
- `sfcos2ang` and `sfisin2ang` are stack-panel-to-angle resamplers, not simple
  arccos/arcsin converters. `sfmodrefl`/`sfmodrefl2` require elastic
  reflectivity modeling over Vp/Vs/rho, `sfmap2coh` uses parameter-map
  interpolation into coherency-like plots, `sflinsincos` solves a
  velocity-grid angle problem, and `sfovc` is oriented velocity continuation;
  all are deferred.
- Coverage numerator changes to `112 / 2114` and core coverage to `99 / 301`.
  Direct `system/main` coverage remains `37 / 39`; all denominators remain
  unchanged.

M2-3:

- Continues source-aligned `system/seismic` command migration with the
  angle / reflectivity / coherence utility group after M2-2 and does not
  continue Forward Modeling, DAS, Localization, solver, notebook,
  Windows-only CI known-issue, migration, RTM, DMO, Kirchhoff, Gazdag, or
  wave-equation imaging work.
- The source audit covered
  `../src-master/system/seismic/Mcos2ang.c`,
  `../src-master/system/seismic/Misin2ang.c`,
  `../src-master/system/seismic/Mmodrefl.c`,
  `../src-master/system/seismic/Mmodrefl2.c`,
  `../src-master/system/seismic/Mmap2coh.c`,
  `../src-master/system/seismic/Mlinsincos.c`,
  `../src-master/system/seismic/Movc.c`,
  `../src-master/system/seismic/Movcco.c`, and
  `../src-master/system/seismic/Movczo.c`.
- Counts `sfcos2ang`, `sfisin2ang`, and `sfmap2coh` because they map directly
  to `system/seismic` source files and now have Python API, RSFData chain
  method, CLI module, console-script surface, focused tests, and documented
  bounded behavior.
- `sfcos2ang` and `sfisin2ang` support bounded stack-panel-to-angle linear
  resampling. They replace one inverse-trig coordinate axis with a degree
  angle axis using `axis=`, `na=`, `a0=`, `da=`, and `fill=`; they are not
  simple elementwise `acos` or `asin` converters and do not implement the
  upstream `top=` velocity scaling.
- `sfmap2coh` supports bounded in-memory parameter-map accumulation into a
  velocity/coherence axis with same-shape input/map panels, `nv/v0/dv`,
  `axis_time=`, `axis_map=`, and optional `min2/max2`. It does not implement a
  production coherence workflow or local similarity stack.
- `sfmodrefl` and `sfmodrefl2` require elastic reflectivity modeling over
  Vp/Vs/rho with interpolation, `sflinsincos` solves a velocity-grid angle
  fitting problem, and `sfovc`/`sfovcco`/`sfovczo` are oriented velocity
  continuation utilities; all are deferred.
- Coverage numerator changes to `115 / 2114` and core coverage to `102 / 301`.
  Direct `system/main` coverage remains `37 / 39`; all denominators remain
  unchanged.

M2-4:

- Continues source-aligned `system/seismic` command migration with the gather
  organization / stacking utility group after M2-3 and does not continue
  Forward Modeling, DAS, Localization, solver, notebook, Windows-only CI
  known-issue, production binning/reconstruction, migration, RTM, DMO,
  Kirchhoff, Gazdag, or wave-equation imaging work.
- The source audit covered
  `../src-master/system/seismic/Maastack.c`,
  `../src-master/system/seismic/Mfinstack.c`,
  `../src-master/system/seismic/Mcmp2shot.c`,
  `../src-master/system/seismic/Mbeamspray.c`,
  `../src-master/system/seismic/Mintbin.c`,
  `../src-master/system/seismic/Mintbin3.c`,
  `../src-master/system/seismic/Minfill.c`,
  `../src-master/system/seismic/Mradial.c`,
  `../src-master/system/seismic/Mradial2.c`, and
  `../src-master/system/seismic/Moway1.c`.
- Counts `sfcmp2shot`, `sfintbin`, and `sfintbin3` because they map directly
  to `system/seismic` source files and now have Python API, RSFData chain
  method, CLI module, console-script surface, focused tests, and documented
  bounded behavior.
- `sfcmp2shot` supports regular 2D CMP-to-shot trace reorganization for
  finite 3D RSF arrays with axes `n1=time`, `n2=offset`, `n3=CMP` and integer
  `d2/d3` geometry ratio. It does not reconstruct irregular field geometry or
  read SEG-Y trace headers.
- `sfintbin` and `sfintbin3` support numeric integer-valued header tables and
  sort trace rows into 2D or 3D regular bin grids with optional integer bounds.
  They omit SEG-Y key-name lookup, inverse unbinning, map/mask side outputs,
  duplicate-trace accumulation policies, and production acquisition binning.
- `sfaastack` uses antialias stretch operators, `sffinstack` is finite-
  difference DMO/offset continuation, `sfinfill` is complex frequency-domain
  shot interpolation, `sfbeamspray` uses dip/curvature beam spreading,
  `sfradial`/`sfradial2` are radial stretch transforms, and `sfoway1` is an
  oriented one-way wave-equation propagator; all are deferred.
- Coverage numerator changes to `118 / 2114` and core coverage to `105 / 301`.
  Direct `system/main` coverage remains `37 / 39`; all denominators remain
  unchanged.

M3-4:

- Performs an official source gap second pass after M3-3/M3-3A and does not
  continue GitHub Actions Windows-only diagnostics, Forward Modeling, DAS,
  Localization, solver, workflow, migration/RTM/DMO/Kirchhoff/Gazdag, large
  system, original-source, SciPy-dependency, or coverage-denominator work.
- The source audit covered
  `../src-master/system/generic/Mgrad2.c`,
  `../src-master/system/generic/Mgrad3.c`,
  `../src-master/system/generic/Mlpad.c`,
  `../src-master/system/seismic/Mshot2cmp.c`,
  `../src-master/system/seismic/Mcmp2shot.c`,
  `../src-master/system/seismic/Mmodrefl.c`,
  `../src-master/system/seismic/Mmodrefl2.c`,
  `../src-master/system/seismic/Mlinsincos.c`, and
  `../src-master/system/seismic/Mricker1.c`.
- Counts `sfgrad2`, `sfgrad3`, and `sflpad` because they map directly to small
  `system/generic` source files and now have Python topic APIs, RSFData chain
  methods, CLI modules, console-script surface, focused tests, docs, and
  coverage mapping.
- `sfgrad2` supports the fixed 2D Sobel gradient-squared stencil from
  `../src-master/api/c/edge.c`, applied independently to each extra slice and
  zeroing edge samples. `sfgrad3` supports the fixed 3D Sobel gradient-squared
  mode plus `dim=1/2/3` component modes, also zeroing edge samples. These are
  not scale-normalized physical derivatives and do not add smoothing/filter
  ecology beyond the upstream stencil.
- `sflpad` supports regular in-memory trace/plane interleaving with `jump=`
  along RSF axes 2 and 3 and optional mask output. It updates `n2/n3` and
  `d2/d3` like `Mlpad.c`, but does not implement streaming, pipe-specific
  output behavior, non-regular geometry, or SEG-Y trace headers.
- `sfcmp2shot` was already counted in M2-4; `sfshot2cmp` is source-clear but
  deferred because the regular-geometry inverse needs a dedicated paired
  geometry validation pass. `sfmodrefl`/`sfmodrefl2` require elastic
  reflectivity modeling with spline interpolation, `sflinsincos` solves an
  angle/velocity-grid integration problem, and `sfricker1` is an input-trace
  convolution filter unlike the existing Pythonic Ricker wavelet generator.
- Coverage numerator changes to `127 / 2114` and core coverage to `114 / 301`.
  Direct `system/main` coverage remains `37 / 39`; all denominators remain
  unchanged.

M3-5:

- Performs a stricter official source gap third pass and does not continue
  GitHub Actions Windows-only diagnostics, Forward Modeling, DAS,
  Localization, solver, workflow, migration/RTM/DMO/Kirchhoff/Gazdag, large
  system, original-source, SciPy-dependency, or coverage-denominator work.
- The source audit covered
  `../src-master/system/generic/Mbandpass.c`,
  `../src-master/system/generic/Mmutter.c`,
  `../src-master/system/seismic/Mshot2cmp.c`,
  `../src-master/system/seismic/Mcmp2shot.c`,
  `../src-master/system/seismic/Mmodrefl.c`,
  `../src-master/system/seismic/Mmodrefl2.c`,
  `../src-master/system/seismic/Mlinsincos.c`,
  `../src-master/system/seismic/Mricker1.c`, and related Ricker/filter
  conveniences already present in Python.
- Counts `sfshot2cmp` because it maps directly to
  `../src-master/system/seismic/Mshot2cmp.c` and now has Python topic API,
  RSFData chain method, CLI module, console-script surface, focused tests,
  docs, and coverage mapping.
- `sfshot2cmp` supports regular in-memory 2D shot-to-CMP trace
  reorganization for finite 3D RSF arrays with axes `n1=time`, `n2=offset`,
  `n3=shot`, integer `d3/d2` geometry ratio, default `half=y`, and
  `positive=` orientation. It does not implement mask side output,
  streaming/native-byte pipe behavior, `half=n`, irregular geometry, SEG-Y
  trace headers, or production reconstruction.
- `sfcmp2shot` was already counted in M2-4. `sfbandpass` remains a Pythonic
  FFT taper convenience because upstream `Mbandpass.c` is Butterworth-based;
  `sfricker1` is trace convolution unlike the existing Ricker generator;
  `sfmodrefl`/`sfmodrefl2` require elastic reflectivity modeling with
  interpolation; `sflinsincos` is an angle/velocity-grid integration problem;
  and `sfmutter` was already source-counted in Stage C-4.
- Coverage numerator changes to `128 / 2114` and core coverage to `115 / 301`.
  Direct `system/main` coverage remains `37 / 39`; all denominators remain
  unchanged.

M3-6:

- Performs an audit-first official source gap fourth pass and does not
  continue GitHub Actions Windows-only diagnostics, Forward Modeling, DAS,
  Localization, solver, workflow, migration/RTM/DMO/Kirchhoff/Gazdag, large
  system, original-source, SciPy-dependency, or coverage-denominator work.
- The source audit covered
  `../src-master/system/generic/Mbandpass.c`,
  `../src-master/system/generic/Mmutter.c`,
  `../src-master/system/generic/Mpolymask.c`,
  `../src-master/system/generic/Mpow.c`,
  `../src-master/system/generic/Mintshow.c`,
  `../src-master/system/seismic/Mricker1.c`,
  `../src-master/system/seismic/Mmodrefl.c`,
  `../src-master/system/seismic/Mmodrefl2.c`,
  `../src-master/system/seismic/Mlinsincos.c`,
  `../src-master/system/seismic/Mstretch.c`,
  `../src-master/system/seismic/Mshifts.c`, and plot/main rendering commands.
- Counts `sfpolymask` because it maps directly to
  `../src-master/system/generic/Mpolymask.c` and now has Python topic API,
  RSFData chain method, CLI module, console-script surface, focused tests,
  docs, and coverage mapping.
- `sfpolymask` supports regular in-memory 2D point-in-polygon masking for
  finite 2D RSF grids using input axes `n1/n2/o1/o2/d1/d2` and a floating
  point `poly=` vertex table with `n1=2`, `n2=nv`. It outputs an `int32` 0/1
  mask and records `polymask_source=../src-master/system/generic/Mpolymask.c`.
  It does not implement multi-dimensional masks, polygon repair, plotting,
  non-RSF vertex formats, or boundary-specialized geometry semantics beyond
  the source point-in-polygon test.
- `sfbandpass` remains a Pythonic FFT taper convenience because upstream
  `Mbandpass.c` is Butterworth-based; `sfricker1` is trace convolution unlike
  the existing Ricker generator; `sfmodrefl`/`sfmodrefl2` require elastic
  reflectivity modeling with interpolation; `sflinsincos` is an angle/
  velocity-grid integration problem; `sfstretch` is a larger interpolation
  stretch family; `sfshifts` was already counted in Stage C-3; `sfmutter` was
  already source-counted in Stage C-4; `sfpow`/`sftpow` were already covered
  through the axis-gain surface; and plot/main commands remain VPlot rendering
  surfaces.
- Coverage numerator changes to `129 / 2114` and core coverage to `116 / 301`.
  Direct `system/main` coverage remains `37 / 39`; all denominators remain
  unchanged.

Stage D-1:

- Added `examples/my_workflows/das_void_diffraction_workflow.py`.
- The workflow uses a kinematic direct-Rayleigh plus void-diffraction model,
  the existing Ricker wavelet, RSF I/O, FK fan filtering, Matplotlib quicklook,
  simulated picks, and a workflow-only NumPy least-squares inversion.
- The synthesis array is `data[time, channel]`; RSF storage follows project
  convention as `(channel, time)` with time on RSF axis 1.
- No reusable modeling or inversion API was promoted from the workflow.
- No CLI, console script, upstream command surface, or coverage value changed.

## Topic Architecture Pass T1

T1 ends automatic Stage C feature-batch continuation at C-10. The repository
can enter topic-oriented development, with seismic data signal analysis and
processing first. Its first batch is a contract-and-fixture pass using existing
APIs, not C-11 and not another convenience-command list.

Every topic must define three contracts before broad implementation:

- **Data:** array rank/layout, RSF axis mapping, dtype, units, missing-value
  policy, regular versus explicit coordinates, and shape-changing behavior.
- **Geometry:** coordinate frame, origin and sign conventions, source/receiver
  or channel ownership, regular-grid assumptions, and physical-to-index rules.
- **Validation:** analytic or independently computed reference, tolerances,
  invariants, negative cases, reproducible fixtures, and workflow-level
  acceptance metrics.

### 1. Seismic Data Signal Analysis and Processing

- **Existing:** C-1 through C-10 signal, spectral, FIR, and QC subsets; stable
  gain/AGC/mute/stack subsets; prototype NMO, semblance, FK, and Radon.
- **Maturity / entry:** stable subset overall, with prototype gather operators;
  yes, this is the first implementation topic after its contract pass.
- **Missing:** canonical trace/panel/small-gather fixtures, offset and velocity
  semantics, multi-gather cases, and end-to-end pipeline regressions.
- **Data contract:** finite real trace or panel; time on RSF axis 1 with
  `label1=Time` and explicit time unit; NumPy panel layout `(ntrace, ntime)`;
  optional RSF axis 3 owns gather/shot/CMP identity.
- **Geometry contract:** regular trace axis may use `o2/d2`; irregular offsets
  or receiver positions require an explicit coordinate array and must not be
  inferred from trace order.
- **Validation contract:** known-tone attenuation and phase, Ricker arrival and
  shift recovery, hyperbolic-event flattening, FK fan selectivity, shape/header/
  dtype invariants, and invalid sampling/geometry cases.
- **First batch:** define fixtures and acceptance metrics, then add one
  existing-API pipeline regression spanning conditioning, spectral QC, and
  small-gather processing. Add implementation only for a demonstrated gap.
- **Do not:** add C-11 commands, broad IIR/multitaper/system-identification
  lists, production geometry claims, or streaming work without a fixture.
- **Docs:** update existing authority docs and examples; no new architecture
  document is required.

### 2. DAS / Engineering Workflows

- **Existing:** the D-1 kinematic road-void diffraction workflow, existing FK
  and plotting reuse, simulated picks, and workflow-only variable-projection
  least squares.
- **Maturity / entry:** workflow-only; retain workflow-first, but do not enter
  adapter or D-2 implementation.
- **Missing:** field fixtures, domain I/O, channel coordinates and orientation,
  gauge-length/strain response, chunking, real picking, and uncertainty.
- **Data contract:** time-by-channel regular arrays with explicit units,
  channel identity, missing-channel policy, and future chunk boundaries.
- **Geometry contract:** channel coordinates, fiber orientation, source
  position, gauge length, sign convention, and local coordinate frame.
- **Validation contract:** synthetic truth recovery, geometry perturbation,
  missing-channel behavior, and later field-like fixtures with documented
  expected trends rather than a detection claim.
- **First batch:** design workflow metadata and geometry schemas and strengthen
  synthetic acceptance criteria without promoting helpers to public API.
- **Do not:** implement HDF5/TDMS/DAT I/O, a DAS adapter, D-2, automatic picks,
  gauge response, or field-performance claims.
- **Docs:** update existing workflow and authority docs only.

### 3. Localization

- **Existing:** `max1` picking, synthetic arrival tests, receiver metadata in
  acoustic2d, D-1 workflow-only travel-time/least-squares helpers, L0-1
  pure-Python direct-module 2D travel-time/fixed-velocity grid-search
  primitives, and L0-2 homogeneous variable-velocity point-diffraction
  grid-search primitives in `pymadagascar.localization.traveltime`.
- **Maturity / entry:** prototype. L0-1/L0-2 provide reusable
  localization-topic primitives without promoting a stable/root API, CLI, or
  production workflow.
- **Missing:** pick records, uncertainty/quality metadata, richer coordinate
  frames, travel-time provider interfaces, identifiability rules, solver
  reporting, automatic picking, and field-scale validation.
- **Data contract:** event/pick ID, receiver ID and coordinates, observed time,
  uncertainty or weight, quality flag, units, and reference-time convention.
- **Geometry contract:** source unknown vector, receiver coordinates,
  dimensionality, local frame or CRS, velocity model, and travel-time
  parameter ownership.
- **Validation contract:** analytic homogeneous travel times, noise and
  outliers, rank/identifiability failures, residual/Jacobian checks, and an
  independently computed least-squares reference.
- **First batch:** L0-1 implements finite homogeneous 2D direct and
  source-diffractor-receiver kinematic travel times, observed-minus-predicted
  residuals with optional positive weights, and deterministic x-z grid-search
  point localization. It is a pure-Python prototype for small local fixtures,
  not a full Madagascar command clone.
- **Second batch:** L0-2 adds
  `grid_search_point_location_velocity_2d`, a pure-Python variable-velocity
  grid-search prototype for the same source-diffractor-receiver kinematic
  model. It estimates homogeneous velocity with either bounded closed-form
  slowness or an explicit positive velocity grid, returns 2D objective and
  selected-velocity grids, and remains uncounted command-surface work.
- **Do not:** build event catalogs, tomography, automatic production picking,
  real-data readers, waveform modeling, imaging, uncertainty/covariance, field
  claims, or coupling to SEG-Y headers.
- **Docs:** record prototype boundaries in roadmap/API/limitations docs; do not
  change command coverage denominators unless a true command-surface mapping is
  added later.

### 4. Inversion / Operators

- **Existing:** matrix/callable/identity `LinearOperator`, real and complex dot
  tests, CG/CGNR with scalar damping, and a Radon forward/adjoint pair.
- **Maturity / entry:** partial operator foundation and prototype domain
  operator; only foundation design is ready.
- **Missing:** composition/sum/scale algebra, reusable identity/diagonal/
  difference regularizers, objective/residual/history contracts, stopping
  diagnostics, and preconditioning.
- **Data contract:** explicit model/data spaces, shapes, dtypes, weights,
  regularization parameters, and solver result/history records.
- **Geometry contract:** operators must own or receive domain geometry
  explicitly; flattened vectors cannot erase grid or acquisition meaning.
- **Validation contract:** dot tests, finite-difference objective gradients,
  dense-matrix references, monotonic residual checks, stopping reasons, and
  regularized recovery fixtures.
- **First batch:** design operator composition, regularization, objective, and
  diagnostics; then implement only a toy least-squares foundation.
- **Do not:** implement FWI, arbitrary shell operators, large/out-of-core
  solvers, or domain inversion before the foundation is validated.
- **Docs:** update existing API and roadmap docs when contracts are selected.

### 5. Forward Modeling

- **Existing:** a one-shot 2D scalar acoustic finite-difference simplified
  prototype with integer source/receiver indices, sponge damping, snapshots,
  and a basic arrival test; F0-1 adds a pure-Python regular local-2D
  model/acquisition geometry contract in pymadagascar.modeling.geometry, and
  F0-2/F0-3 add single-shot and sequential multi-shot acquisition-driven
  wrappers in pymadagascar.modeling.shot. F0-4 adds explicit survey tensor
  conversion and summary helpers while preserving the list-of-shots survey
  contract. F0-5 adds pymadagascar.modeling.models synthetic acoustic velocity
  model builders for constant, layered, rectangular-anomaly, and circular-
  anomaly small models. F0-6 adds a deterministic geometry-driven validation
  workflow that connects those pieces and emits JSON-safe acceptance metrics.
- **Maturity / entry:** simplified prototype with topic-level geometry and shot
  helpers plus synthetic model builders and a smoke validation workflow; no
  root/stable API.
- **Missing:** physical-coordinate interpolation, component support,
  smoothing/random/geologic model building, production survey tensor formats,
  padding/interpolation policies, boundary studies, convergence, dispersion,
  validation workflows, and reference solutions.
- **Data contract:** velocity/density model grids, source wavelet and time
  sampling, shot gathers, component names, units, and snapshot ownership.
- **Geometry contract:** physical grid origin/spacing, source and receiver
  coordinates, interpolation and out-of-bounds policy, and shot identity.
- **Validation contract:** CFL rejection, homogeneous analytic arrivals,
  grid-refinement convergence, dispersion and boundary-reflection metrics, and
  deterministic tiny fixtures.
- **First batch:** F0-1 specifies model and acquisition geometry and converts
  point-source/receiver coordinates to the existing acoustic2d integer-index
  contract without changing the solver. F0-2 uses that contract to run one
  acoustic2d shot from physical source/receiver coordinates and return a
  path-free Pythonic record plus metadata. F0-3 loops over an input-ordered
  sequence of AcousticAcquisition2D objects, reuses the F0-2 shot wrapper, and
  returns a list-backed AcousticSurveyRecord2D without adding a new solver,
  parallelism, caching, interpolation, or a committed default survey tensor
  layout. F0-4 keeps that default list-of-shots design and adds an explicit
  acoustic_survey_to_tensor helper with shot_receiver_time layout for surveys
  with consistent receiver counts and matching time axes, plus a JSON-safe
  summarize_acoustic_survey helper; it performs no padding, interpolation, or
  trace dropping. F0-5 adds deterministic AcousticVelocityModel2D builders that
  return positive finite (nx, nz) velocity arrays compatible with the existing
  acoustic2d wrappers, with JSON-safe metadata and no smoothing, random model,
  geologic GUI, solver change, CLI, root/stable API, command coverage, or
  coverage denominator change. F0-6 adds
  acoustic_modeling_validation_workflow.py as a smoke-level workflow connecting
  geometry, velocity models, survey execution, survey summary, and tensor
  conversion; it records deterministic shape/count/time/finite/nonzero/path-free
  checks, not accuracy, convergence, dispersion, interpolation, or imaging
  claims.
- **Do not:** add new wave-equation algorithms, production boundaries,
  multi-physics, C++ kernels, or performance claims.
- **Docs:** existing API/roadmap/limitations docs record the prototype
  boundary; notebook updates are deferred.

### 6. Imaging

- **Existing:** 2D post-stack zero-offset Kirchhoff time migration with scalar
  or time velocity, aperture/normalization options, and diffraction focusing.
- **Maturity / entry:** simplified prototype; defer.
- **Missing:** shared acquisition and velocity contracts, amplitude and
  anti-alias treatment, adjoint evidence, prestack geometry, and a reference
  workflow.
- **Data contract:** migrated image, input time section, velocity model,
  aperture/normalization metadata, units, and axis ownership.
- **Geometry contract:** acquisition coordinates, image grid, time/depth
  convention, and velocity sampling/interpolation.
- **Validation contract:** impulse/diffraction focusing, positioning error,
  amplitude sensitivity, adjoint checks where applicable, and independent
  reference images.
- **First batch:** none until geometry, forward-modeling design, and operator
  validation are available.
- **Do not:** add migration algorithms, RTM, prestack imaging, or imaging
  performance claims.
- **Docs:** update existing docs only when the defer gate changes.

### 7. SEG-Y / Headers

- **Existing:** stable ordinary RSF metadata, a partial numeric header-table
  model, and a fixed-layout 2D SEG-Y read/write and trace-word prototype.
- **Maturity / entry:** stable RSF / partial headers / prototype SEG-Y;
  independent and deferred.
- **Missing:** unified trace ownership, data/header synchronized reorder,
  coordinate scalar and unit policy, trace identity/order, revision/extension
  handling, variable-length support, and a round-trip corpus.
- **Data contract:** keep ordinary RSF metadata, numeric header tables, and
  SEG-Y trace bytes as distinct models with an explicit trace-row link.
- **Geometry contract:** source/receiver/CDP coordinates, scalar application,
  units, coordinate system, trace ordering, and missing-word policy.
- **Validation contract:** byte-level header fixtures, data/header round trips,
  scalar/unit cases, synchronized sort/filter tests, malformed files, and
  independent-reader comparison.
- **First batch:** design trace ownership and round-trip fixtures only.
- **Do not:** implement `sfsegyheader`, a broad trace-header ecology, or fold
  the topic into ordinary RSF header tools.
- **Docs:** existing API/limitations/roadmap docs are sufficient for design.

### 8. Plot / Visualization

- **Existing:** Matplotlib Agg graph, grey, and wiggle quicklooks with PNG/PDF
  output, clipping, transpose, and workflow figures.
- **Maturity / entry:** partial quicklook substitute; support work only.
- **Missing:** reusable multi-panel composition, overlays, consistent domain
  labels/orientation, and richer QC presentation.
- **Data contract:** plottable array plus explicit axes, units, orientation,
  clipping/color limits, and output format.
- **Geometry contract:** display coordinates must follow the source data
  contract; overlays must declare their coordinate frame.
- **Validation contract:** output creation, dimensions, labels, limits, and
  artist/metadata assertions rather than brittle pixel identity.
- **First batch:** only overlays or multi-panel support directly required by
  the first seismic topic workflow.
- **Do not:** pursue VPlot compatibility, dashboards, GUI applications, or a
  standalone visualization roadmap.
- **Docs:** update the existing user guide or workflow text only as needed.

### 9. General RSF / Data Processing

- **Existing:** stable RSF header/sidecar I/O, core axes/hypercubes/parameters,
  RSFData, and broad stable or stable-subset generic array processing.
- **Maturity / entry:** stable / stable subset; freeze except topic-driven gaps.
- **Missing:** broader streaming, out-of-core, pipe, and format support, none
  of which blocks the first in-memory topic.
- **Data contract:** preserve current NumPy/RSF axis reversal, `n/o/d`,
  label/unit, dtype, sidecar, and explicit shape-change rules.
- **Geometry contract:** generic code preserves metadata and does not invent
  domain coordinates.
- **Validation contract:** round trip, shape/header/dtype, axis transforms,
  file isolation, malformed headers, and optional upstream subset comparisons.
- **First batch:** no broad batch; add only a regression or helper required by
  an accepted topic contract.
- **Do not:** resume utility accumulation, redesign stable APIs, or promise full
  pipe/out-of-core compatibility.
- **Docs:** maintain existing authority docs only.

### 10. Statistics QC / Spectral QC

- **Existing:** global and axis statistics, robust median/range, finite masks
  and filling, histogram/quantile, difference metrics, PSD/CSD/coherence/
  Welch, transfer estimates, frequency attributes, SNR, and band energy.
- **Maturity / entry:** stable subset; use as cross-cutting validation support
  rather than an independent broad implementation topic.
- **Missing:** weighted/grouped statistics, confidence intervals, robust local
  estimators, streaming accumulation, and multi-taper/AR methods.
- **Data contract:** explicit reduction axis, finite-value policy, weighting,
  units, output table/axis layout, and averaging semantics.
- **Geometry contract:** QC results retain or remove domain axes explicitly and
  never infer geometry from array position.
- **Validation contract:** analytic moments and spectra, deterministic random
  seeds, estimator scaling, confidence/weight behavior when added, and
  pipeline acceptance thresholds.
- **First batch:** define seismic-topic acceptance metrics with existing APIs.
- **Do not:** add another general statistics or spectral convenience list.
- **Docs:** update current workflow/roadmap docs; no separate QC document.

## T1 Route Order

1. Seismic data signal analysis and processing: contract, fixtures, one
   existing-API pipeline regression, metrics/QC reporting, and bounded
   prototype hardening when S1/S2 evidence demonstrates a gap.
2. Localization design and inversion/operator foundation design after the
   shared geometry vocabulary is explicit.
3. DAS remains workflow-first and may consume those contracts later without
   adding adapters.
4. Forward modeling remains design-only; implementation requires its
   acquisition and validation gates.
5. Imaging and SEG-Y/header remain deferred independent topics.

General RSF/data processing, statistics/spectral QC, and plotting are support
tracks. They should change only when the active topic demonstrates a concrete
gap.

## Seismic Topic S1: Contract and Fixture Foundation

S1 formally starts the first topic. It adds internal/testing fixtures, one
workflow regression, and focused tests without adding a feature command, CLI
module, console script, stable public API, or command-surface coverage entry.
Coverage remains `86 / 2114`, core coverage remains `73 / 301`, and direct
`system/main` coverage remains `32 / 39`.

### Trace Contract

- Data are finite real `float32` or `float64` with NumPy shape `(ntime,)`.
- RSF axis 1 is time: `n1=ntime`, finite `o1`, positive `d1`,
  `label1=Time`, and `unit1=s`.
- Amplitude units are explicit custom metadata such as
  `amplitude_unit=relative`; they are not axis units.
- Optional metadata may record fixture kind, seed, event time, peak frequency,
  or known interference frequency.
- Shape-preserving conditioning, filtering, gain, and QC must retain the time
  axis and finite values. Spectral transforms and reductions must document
  their changed axes.

### Panel Contract

- A logical time-by-channel panel is stored as NumPy
  `(nchannel, ntime)` because RSF axis 1 is the last NumPy dimension.
- RSF dimensions are `(n1=ntime, n2=nchannel)`; axis 1 remains time.
- Axis 2 is one regular channel/trace coordinate with finite `o2`, positive
  `d2`, explicit `label2/unit2`, `axis2_role`, and
  `coordinate_sampling=regular`.
- S1 does not embed a non-regular coordinate vector in an ordinary RSF header.
  An existing API may accept a separate length-matched coordinate RSF only
  when that input is explicit in its contract.
- Shape-preserving operations retain both axes. Stack removes the selected
  trace axis; PSD replaces the selected time axis with frequency.

### Gather Contract

- A CMP-like gather specializes the panel with `label2=Offset`, `unit2=m`, and
  `axis2_role=signed_offset`.
- Offset is `receiver_x - source_x`: negative receivers are on the negative
  source side and positive receivers are on the positive side.
- The S1 canonical gather is regular and uses `o2/d2`; `d2` must be positive.
  Hyperbolic travel time is
  `sqrt(t0**2 + (offset / velocity)**2)`.
- Full source/receiver coordinates, CRS, azimuth, elevation, components, and
  trace ownership are not encoded.
- Ordinary RSF headers, the minimal numeric header table, and SEG-Y trace
  headers remain distinct. S1 does not add or synchronize either trace-header
  model.

### Processing Pipeline Contract

`examples/my_workflows/seismic_signal_contract_workflow.py` composes only
existing APIs:

```text
deterministic hyperbolic gather
-> demean(axis=1, nan_policy=raise)
-> detrend(axis=1, linear)
-> bandpass(8-45 Hz)
-> AGC(0.080 s)
-> regular signed-offset mutter
-> mean stack(axis=2)
-> stack PSD
-> RSF, PNG, and JSON regression outputs
```

The workflow defaults to a system temporary directory, accepts an explicit
output directory, and does not require original Madagascar or C++.

### Validation Contract

- Trace/panel/gather shapes, RSF dimensions, labels, units, dtype, and finite
  values are asserted.
- Ricker peak time, hyperbolic arrivals, and plane-wave signed slope are known
  within one time sample.
- The 24 Hz passband amplitude ratio must remain between `0.75` and `1.05`;
  the 70 Hz stopband ratio must be below `0.02`.
- Samples before the regular mute boundary must be zero to absolute tolerance
  `1e-8`.
- Mean-stack tail-noise RMS must be below `0.45` of the processed trace-panel
  tail RMS.
- Fixed seeds and float operations must produce identical arrays and JSON
  metrics across repeated runs on the same platform.
- Negative coverage includes invalid axes, coincident time/offset axes,
  non-positive sampling or velocity, non-finite parameters, unsupported dtype,
  out-of-range event times, and invalid offset spacing.
- Workflow tests snapshot repository example files before and after execution
  to prevent output pollution.

The fixture module is deliberately not re-exported from stable package or
testing namespace entry points. S1 does not change prototype maturity.

## Seismic Topic S2: Pipeline Metrics and QC Report Foundation

S2 adds one internal metrics helper, one workflow regression, and focused tests
without adding a feature command, CLI module, console script, stable public
API, or command-surface coverage entry. Coverage remains `86 / 2114`, core
coverage remains `73 / 301`, and direct `system/main` coverage remains
`32 / 39`.

### Pipeline Metrics Contract

- `input_rms` describes the raw gather; `output_rms` describes the final
  AGC/mutter gather.
- Signal/noise RMS, SNR, dominant frequency, and target/reject band energy
  compare the detrended gather before and after the existing 8-45 Hz bandpass.
  This comparison intentionally occurs before AGC amplitude normalization.
- The S2 fixture uses signal samples `[100,163)`, noise samples `[300,450)`,
  target band 15-35 Hz, and reject band 60-80 Hz.
- Stack metrics include the largest absolute stack sample inside the declared
  signal window, its physical time/amplitude, signal/noise RMS, SNR, and tail
  noise relative to the final processed panel.
- `muted_fraction` is the fraction of the full regular gather before
  `0.080 + abs(offset)/4000`; `mute_zero_fraction` verifies those samples are
  zero within `1e-8`.
- `finite_fraction` spans raw, pre/post-filter, final processed, and stack
  arrays. `header_axis_ok` verifies the regular gather axes and reduced stack
  time axis.

### QC Report Contract

`examples/my_workflows/seismic_signal_metrics_workflow.py` writes
`s2_qc_report.json` with stable S2 keys:

- workflow, stage, status, fixture, metric scope, sample windows, and frequency
  bands;
- scalar metrics for RMS, SNR, frequency, band energy, mute, stack, finite
  values, and headers;
- boolean checks for SNR improvement, target-band preservation,
  reject-band attenuation, stack-noise reduction, mute application, finite
  values, header axes, and overall pass.

The JSON is deterministic, sorted, finite, and contains no output directory or
local absolute path. It is an internal workflow/testing contract, not a public
file-format guarantee.

### S2 Validation Contract

- SNR improvement must be at least 6 dB.
- Target-band energy ratio must stay between `0.75` and `1.10`.
- Reject-band energy ratio must be at most `0.02`.
- Stack noise RMS must be at most `0.45` of final processed-panel noise RMS.
- The regular mute must cover a nonzero fraction and at least `99.9%` of the
  geometrically muted samples must be zero within the fixed tolerance.
- All samples must be finite and all trace/panel/gather/stack axes must satisfy
  the S1 contract.
- Repeated runs must produce identical metrics and JSON on the same platform.
- Negative tests reject NaN, invalid or overlapping windows, invalid frequency
  bands, unsupported JSON values, and corrupted header labels.

The helper is deliberately not re-exported from stable package or testing
namespace entry points. S2 does not change prototype maturity.

## Seismic Topic S3: NMO Prototype Contract Hardening with S1/S2 Fixtures

S3 hardens the existing NMO prototype against the S1 regular signed-offset
gather and S2 metric foundation. It adds one workflow regression and focused
tests without adding a feature command, CLI module, console script, stable
public API, or command-surface coverage entry. Coverage remains `86 / 2114`,
core coverage remains `73 / 301`, and direct `system/main` coverage remains
`32 / 39`. NMO remains a prototype.

### NMO Data Contract

- Input is a finite real, small, in-memory CMP-like gather or gather volume.
- The canonical S1 shape is NumPy `(ntrace, ntime)` with RSF dimensions
  `(n1=ntime, n2=ntrace)`. Axis 1 is time; axis 2 is signed offset.
- The time axis must have finite `o1`, positive finite `d1`, and at least two
  samples.
- If `offset=` is not provided, the regular offset axis must have finite `o2`
  and positive finite `d2`. If `offset=` is provided, it must be finite and have
  one, `ntrace`, or per-gather `ngather*ntrace` samples.
- Velocity may be scalar, a time function, or one time function per gather. It
  must be finite and strictly positive.
- NaN/Inf samples, non-finite velocity/offset/reference/stretch parameters, and
  incompatible offset vectors are rejected before output is written.

### NMO Geometry Contract

- S3 inherits the S1 offset sign convention:
  `receiver_minus_source`.
- The NMO equation uses `abs(offset)` and interprets `half=yes` as half-offset
  input, matching the existing prototype option. The S1 contract workflow uses
  full signed offsets, so it runs with `half=no`.
- Velocity units must be consistent with offset units and time units; S1 uses
  meters and seconds.
- `h0` is a finite reference offset; time origin is the RSF time-axis origin.
- Only regular signed-offset axes or explicit length-matched offset vectors are
  covered. Full source/receiver coordinates, trace-header tables, SEG-Y trace
  headers, azimuth, elevation, anisotropy, nonhyperbolic moveout, residual NMO,
  velocity scan, semblance expansion, and production stretch-mute policy remain
  outside S3.

### NMO Validation Contract

`examples/my_workflows/seismic_nmo_contract_workflow.py` writes raw and NMO
corrected gathers, pre/post/wrong-velocity stacks, a quicklook PNG, and
`s3_nmo_qc_report.json` in a system temporary directory by default. The JSON is
deterministic, finite, path-free, and internal to the workflow/testing contract.

The S3 checks assert that, for the S1 hyperbolic fixture and the correct
velocity:

- event pick standard deviation after NMO is at most `0.003 s`;
- flattening improves by at least a broad factor relative to the raw gather;
- correct velocity beats a wrong velocity in both flattening and stack peak;
- post-NMO stack peak amplitude is at least twice the pre-NMO peak;
- post-NMO stack peak time is within `1.5*d1` of the known zero-offset time;
- noise-window RMS is not amplified above `1.2x`;
- finite fraction remains `1.0`;
- time and offset headers are preserved, with prototype NMO metadata recording
  direction, interpolation, stretch, half-offset mode, and offset source.

Negative tests cover non-positive and non-finite velocity, invalid time axis,
invalid regular offset axis, non-finite input samples, non-finite explicit
offsets, offset-vector shape mismatch, invalid `h0` or `stretch`, existing CLI
execution, temp-output isolation, absence of original-Madagascar/C++
dependencies, and path-free deterministic JSON.

## Seismic Topic S4-0: Madagascar Source Alignment and Bounded Selection

S4-0 is a documentation-only source-alignment audit. It adds no feature
command, CLI module, console script, stable public API, test, example, workflow,
or command-surface coverage entry. Coverage remains `86 / 2114`, core coverage
remains `73 / 301`, and direct `system/main` coverage remains `32 / 39`.
XMind remains frozen at the Stage C-10 / M1 snapshot.

The new rule for seismic prototype work is: if a classic Madagascar source is
present in `../src-master`, audit it before hardening the Python prototype.
Pythonic implementations may intentionally differ, but the difference must be
recorded and backed by deterministic fixture tests before maturity is raised.

| Prototype | Current pymadagascar surface | Located Madagascar source | Upstream algorithm and key parameters | Main current difference and risk | S4-0 decision |
| --- | --- | --- | --- | --- | --- |
| NMO | `pymadagascar/seismic/nmo.py`, `pymadagascar/cli/nmo.py`; S3 workflow and `tests/test_seismic_nmo_contract.py` | `../src-master/system/seismic/Mnmo.c`; inverse reference `Minmo.c` | `sfnmo` reads `velocity=`, optional `offset=`, `mask=`, `half=`, `str=`, `mute=`, `slowness=`, `squared=`, `h0=`, and `extend=`; applies stretch interpolation per trace and supports CDP-type offset shifts. `sfinmo` supplies the inverse side with stretch regularization. | Python NMO is an in-memory small-gather prototype with scalar/time-function velocity, explicit or regular offset vectors, linear interpolation, finite-input validation, and simplified stretch mute. It does not clone mask, slowness/squared velocity, CDPtype, heterogeneous parameters, or production stretch behavior. S3 already reduced the largest fixture-level risk. | Do not choose NMO again immediately. Keep it prototype and use it as the foundation for Semblance validation. |
| Semblance | `pymadagascar/seismic/semblance.py`, `pymadagascar/cli/semblance.py`; light coverage in `tests/test_nmo_semblance.py` plus S4-1 contract coverage | `../src-master/system/seismic/Mvscan.c`; related but not primary: `Msimivscan.c`, `Mvscancrs.c`, `user/fomels/Msemblance.c`, `user/fomels/Msemblancew.c`, `user/yliu/semblance.c` | `sfvscan` scans `v0/dv/nv`, supports `semblance=`, `diffsemblance=`, `avosemblance=`, `type=`, `nb=`, `weight=`, `half=`, optional `offset=`, `mask=`, `slowness=`, `squared=`, `v1=`, `smax=`, `ns=`, `str=`, and `mute=`. It NMO-stretches each trace for each trial velocity, stacks numerator/denominator terms, and writes a time x velocity panel. | Python Semblance is a minimal velocity scan over `vmin/vmax/dv` using the Python NMO helper and a simple `sum^2/(fold*sum2)` panel with optional time smoothing. S4-1 hardens finite/header/axis checks, explicit offset handling, velocity-panel metadata, and S1 true-vs-wrong velocity validation, but it still lacks full `sfvscan` type modes, weighting, masks, slowness/squared velocity, and nontrivial scan families. | S4-1 completed as a bounded prototype contract hardening pass. Keep Semblance prototype; do not expand into velocity picking or full `sfvscan` without a new explicit task. |
| FK / FK filter | `pymadagascar/seismic/fk.py`, `pymadagascar/cli/fk.py`, `pymadagascar/cli/fkfilter.py`; `tests/test_fk.py` plus S4-3 contract coverage | No single `system/seismic/Mfk.c` equivalent found. Closest current comparator is `../src-master/system/generic/Mdipfilter.c`; related FK migration/DMO sources include `Mfkamo.c`, `Mfkdmo.c`, and `Mfkgdmo.c`. Search used recursive filename matching for `*fk*.c`, `Mfk*.c`, and `Mdipfilter.c`. | `sfdipfilter` filters already transformed 2D/3D FK-domain data by velocity or angle gates using `v1/v2/v3/v4`, `pass=`, `angle=`, `v=`, and axis frequency/wavenumber headers. | Python `fk_spectrum` computes a centered NumPy FFT spectrum; Python `fk_filter` applies a raw-gather zero-phase fan mask with `vmin/vmax/taper/reject`. S4-3 hardens finite data/axis/parameter checks, records source-reference metadata, and validates analytic plane-wave peaks plus target/reject fan filtering. It remains a Pythonic prototype, not a direct `sfdipfilter` clone. | S4-3 completed as a bounded prototype validation pass. Keep FK prototype; do not expand into full `sfdipfilter`, irregular geometry, or new FK algorithms without a separate task. |
| Radon / inverse Radon | `pymadagascar/seismic/radon.py`, `pymadagascar/cli/radon.py`, `pymadagascar/cli/iradon.py`; `tests/test_radon.py` plus S6-2 contract coverage | `../src-master/system/seismic/Mslant.c` and `slant.c`; high-resolution reference `Mradon.c` and `radon.c`; user variants also exist but are not the current primary comparator. | `sfslant` is a time-space slant-stack operator with `adj=`, `rho=`, `anti=`, `np=`, `dp=`, `p0=`, `p1=`, and inverse-side `x0/dx/nx`. `sfradon` is a frequency-domain high-resolution Radon transform with complex FFT, `adj=`, `inv=`, `spk=`, `np/dp/p0`, optional `offset=`, `parab=`, `x0=`, and inversion controls such as `eps`, `tol`, and `niter`. | Python Radon remains a small direct time-domain linear/parabolic operator pair. S6-2 hardens the shared small slant-stack subset with finite data/model checks, regular time/offset/p-axis validation, explicit-offset length checks, operator-direction metadata, dot-test validation, analytic slant-event focusing, and a path-free workflow JSON report. It is still not a clone of `sfslant` and is not high-resolution `sfradon`. | S6-2 completed as a bounded prototype hardening pass. Do not add least-squares/high-resolution Radon, velocity picking, or production Radon without a new design pass and inversion/operator foundations. |

## Seismic Topic S4-1: Semblance Prototype Contract Hardening

S4-1 hardens the existing Semblance prototype against the S1/S2/S3 fixture
base and the Madagascar source-audit target
`../src-master/system/seismic/Mvscan.c`. It adds no feature command, CLI
module, console script, stable public API, or command-surface coverage entry.
Coverage remains `86 / 2114`, core coverage remains `73 / 301`, and direct
`system/main` coverage remains `32 / 39`. XMind remains frozen at the Stage
C-10 / M1 snapshot.

### Semblance Data Contract

- Input is a finite real small CMP-like gather with NumPy layout inherited from
  S1/S3: time on RSF axis 1 and signed offset on RSF axis 2.
- `o1` must be finite, `d1` must be finite and positive, and at least two time
  samples are required.
- Without explicit `offset=`, regular offset metadata must provide finite `o2`
  and positive finite `d2`. With explicit `offset=`, values must be finite and
  length-compatible with the offset axis.
- Velocity samples from `vmin/vmax/dv` must be finite, positive, monotonic
  through positive `dv`, and nonempty.
- Non-finite input samples, invalid axes, invalid velocity ranges, invalid
  `h0`/`stretch`/`smooth`, and offset-vector length mismatches raise
  `SemblanceError`.

### Semblance Geometry Contract

- Offset sign convention inherits S1:
  `offset_sign_convention=receiver_minus_source`.
- Semblance uses `abs(offset)` through the existing NMO helper; S1 fixtures
  therefore run with `half=n` because their axis stores full signed offsets.
- Velocity units are derived from offset/time units when both are available.
- The output panel has RSF axis 1 as time and axis 2 as velocity with
  `axis2_role=velocity`; input offset provenance is recorded in
  `semblance_input_*` metadata.
- Full source/receiver geometry, SEG-Y trace headers, anisotropy,
  nonhyperbolic moveout, mask/weight tables, slowness/squared-velocity modes,
  and field-scale velocity analysis remain outside S4-1.

### Semblance Validation Contract

`examples/my_workflows/seismic_semblance_contract_workflow.py` writes the S1
hyperbolic gather, a Semblance velocity panel, true-velocity and wrong-velocity
NMO stacks, a quicklook PNG, and `s4_semblance_qc_report.json` to a system
temporary directory by default. The JSON is deterministic, finite, path-free,
and internal to workflow/testing.

The regression checks that the velocity-panel peak near the event falls within
one velocity step of the fixture velocity, true-velocity semblance beats wrong
velocity by a broad ratio, true-velocity NMO stack peak beats wrong velocity,
finite fraction is 1, and velocity/time/input-offset metadata are explicit.

S4-1 does not implement full `sfvscan`: no velocity picking, differential or
AVO semblance, scan-mode expansion, masks, weights, slowness/squared velocity
mode, production stretch policy, Radon/FK algorithms, SEG-Y/header coupling,
field data, localization, inversion, modeling, or imaging.

## Seismic Topic S4-2: Small-Gather Geometry Adapter Design

S4-2 is an internal/testing contract pass. It adds
`pymadagascar.testing.seismic_geometry`,
`tests/test_seismic_geometry_contract.py`, and
`examples/my_workflows/seismic_geometry_contract_workflow.py`, but no feature
command, CLI module, console script, stable public API, or command-surface
coverage entry. Coverage remains `86 / 2114`, core coverage remains
`73 / 301`, and direct `system/main` coverage remains `32 / 39`. XMind remains
frozen at the Stage C-10 / M1 snapshot.

### S4-2 Source Boundary

The geometry design is informed by located Madagascar source boundaries rather
than implemented as a clone. `../src-master/system/seismic/Mnmo.c` and
`Mvscan.c` accept either regular offset metadata from `o2/d2` or an explicit
`offset=` file. `../src-master/system/seismic/Mslant.c` and `Mradon.c` provide
slant/Radon references that may consume offset-like axes or files, while
`../src-master/system/seismic/Mheaderattr.c`,
`../src-master/system/seismic/Mheadermath.c`, and
`../src-master/system/main/headersort.c` show the separate numeric header-table
family. `../src-master/system/seismic/Msegyheader.c` remains a separate SEG-Y
trace-header reference and is explicitly outside S4-2.

### Regular Offset Contract

- Inherits S1/S3/S4-1: NumPy storage is `(ntrace, ntime)`, RSF axis 1 is time,
  and RSF axis 2 is signed offset.
- Offset is represented by ordinary RSF `o2/d2/n2` with
  `label2=Offset`, `unit2=m`, `axis2_role=signed_offset`,
  `coordinate_sampling=regular`, and
  `offset_sign_convention=receiver_minus_source`.
- `d1` and `d2` must be finite and positive. Velocity units are interpreted as
  `offset_unit/time_unit`, so the current fixture contract is `m/s`.
- This contract is suitable for current NMO and Semblance prototypes. It is not
  a complete source/receiver geometry model.

### Explicit Offset Contract

- Offset may be supplied as a separate 1D RSF or NumPy vector.
- The vector must be finite, trace-length compatible, unit-tagged, and use the
  same `receiver_minus_source` sign convention.
- Irregular offset is allowed only through this explicit vector. It must not be
  inferred from trace order or from an ordinary RSF header with a fake regular
  axis.
- This is the smallest future entry point for Radon, localization, and
  irregular-gather design, but it is still internal/testing.

### Minimal Source/Receiver Table Contract

S4-2 defines a deterministic internal fixture table with numeric fields
`trace`, `source_x`, `receiver_x`, `offset`, `midpoint`, `channel`,
`source_id`, and `receiver_id`. The validation contract checks finite values,
trace/channel sequence, `offset = receiver_x - source_x`, and
`midpoint = 0.5 * (source_x + receiver_x)`.

The table is a minimal numeric header table, not a SEG-Y trace header and not a
survey database. It has no CRS, scalar policy, station catalog, shot/receiver
line model, field-scale missing-coordinate policy, or synchronized seismic
data/header reorder contract.

### Header Boundary Contract

- Ordinary RSF headers express regular axes and should remain the preferred
  route for regular time/offset fixtures.
- Explicit offset vectors express the minimal irregular trace coordinate.
- Minimal numeric header tables express trace-wise numeric attributes for
  deterministic tests.
- SEG-Y trace headers remain independent and deferred. S4-2 does not implement
  `sfsegyheader` or a trace-header ecosystem.

### S4-2 Validation Contract

`examples/my_workflows/seismic_geometry_contract_workflow.py` writes an
S1-compatible hyperbolic gather, an explicit offset-vector RSF, a minimal
source/receiver table RSF, and `s4_geometry_report.json` to a system temporary
directory by default. The JSON is deterministic, finite, path-free, and
internal to workflow/testing.

`tests/test_seismic_geometry_contract.py` covers located Madagascar source
paths, regular offset metadata, explicit offset vector shape and unit checks,
source/receiver table determinism and formulas, ordinary-RSF/header-table/SEG-Y
boundaries, no public API export, no CLI or console script, workflow
subprocess/default-temp behavior, output isolation, and absence of
original-Madagascar/C++ dependencies.

S4-2 does not implement SEG-Y trace headers, field-scale geometry, source/
receiver survey databases, FK/Radon algorithms, velocity picking, localization,
inversion, modeling, imaging, DAS adapters, or C++ kernels.

## Seismic Topic S4-3: FK Prototype Source-Aligned Validation

S4-3 hardens the existing FK/FK-filter prototype against the S1/S4-2 regular
panel geometry and the Madagascar source-audit boundary. It adds
`tests/test_seismic_fk_contract.py` and
`examples/my_workflows/seismic_fk_contract_workflow.py`, but no feature
command, CLI module, console script, stable public API, command-surface
coverage entry, or XMind update.

### S4-3 Source Boundary

Recursive source search found no direct `../src-master/**/Mfk.c` generic FK
transform source. `../src-master/system/generic/Mdipfilter.c` is the nearest
dip/f-k/fan-filter comparator: it consumes already frequency-wavenumber-domain
input, reads `n1/n2/o1/o2/d1/d2`, supports 2D/3D filtering, and gates velocity
or angle with `v1/v2/v3/v4`, `pass=`, `angle=`, and sine taper edges. Related
`../src-master/system/seismic/Mfkamo.c`, `Mfkdmo.c`, and `Mfkgdmo.c` are
FK-domain AMO/DMO/GDMO operators, not generic FK spectrum programs.

The Python implementation intentionally keeps two separate conveniences:
`fk_spectrum` builds a centered NumPy FFT spectrum from a regular time-space
panel, and `fk_filter` applies a zero-phase raw-gather fan mask using
`vmin/vmax/taper/reject`. This is not a `sfdipfilter` clone.

### FK Data Contract

- Input is a finite 2D real or complex panel, NumPy shape `(nspace, ntime)`.
- RSF axis 1 is time and RSF axis 2 is a regular channel/offset/spatial
  coordinate.
- `o1/o2` must be finite and `d1/d2` must be finite and positive.
- `fk_spectrum` writes `float32` amplitude spectra by default or `complex64`
  spectra when complex output is requested.
- `fk_filter` writes time-space output with the existing input-compatible dtype
  policy.
- NaN/Inf samples, non-finite frequency/wavenumber arrays, and non-finite or
  negative fan-filter parameters are rejected.

### FK Geometry Contract

- S4-3 supports regular spatial axes only.
- Axis 2 may be a regular channel coordinate or a regular signed-offset axis.
- Explicit offset vectors and S4-2 source/receiver tables are not consumed by
  the current FK transform.
- Irregular geometry must not be inferred from trace order.
- Ordinary RSF headers, minimal numeric header tables, and SEG-Y trace headers
  remain separate models.

### FK Validation Contract

The S4-3 tests and workflow use deterministic plane-wave panels. Validation
checks that the FK peak is near the analytic frequency/wavenumber, positive
and negative slopes separate by wavenumber sign, target apparent velocity is
preserved by the fan filter, reject apparent velocity is suppressed, output
shape/header/dtype and frequency/wavenumber metadata are explicit, finite
values are preserved, invalid axes and parameters raise clear `FKError`
messages, existing `fk`/`fkfilter` CLIs still work, and the workflow JSON is
deterministic, temporary-output only, path-free, and independent of original
Madagascar and C++.

S4-3 does not implement full `sfdipfilter`, FK-domain input filtering,
angle-mode compatibility, 3D fan filtering, irregular geometry, Radon, velocity
picking, localization, inversion, modeling, imaging, SEG-Y trace headers, DAS
adapters, or C++ kernels.

## Seismic Topic S5: Integrated Small-Gather Processing Workflow v0

S5 stops single-point prototype boundary expansion and combines existing
S1/S2/S3/S4 fixture, metric, geometry, NMO, Semblance, FK, stack, and
quicklook pieces into one deterministic small-gather workflow. It adds
`tests/test_seismic_integrated_workflow.py` and
`examples/my_workflows/seismic_small_gather_processing_workflow.py`, but no new
algorithm, feature command, CLI module, console script, stable public API,
command-surface coverage entry, or XMind update. Coverage remains
`86 / 2114`, core coverage remains `73 / 301`, and direct `system/main`
coverage remains `32 / 39`.

### S5 Workflow Contract

The workflow uses the S1 hyperbolic signed-offset gather and S4-2 geometry
helper to write a regular-offset contract, explicit offset vector, and minimal
source/receiver table. It then runs the existing S2 preprocessing chain
`demean -> detrend -> bandpass -> AGC -> mutter -> stack`, the existing NMO
prototype with true and wrong velocities, the existing Semblance prototype over
the same bounded velocity grid, and the existing FK spectrum/filter prototype
on the regular processed gather. All outputs default to a newly created system
temporary directory and may be redirected with an explicit output directory.

### S5 JSON Report Contract

`s5_integrated_qc_report.json` is a deterministic workflow/internal regression
artifact with these top-level sections: `inputs`, `geometry`, `pipeline`,
`nmo`, `semblance`, `fk`, `stack`, and `checks`. It records fixture and
parameter choices, regular/explicit/small-table geometry checks, S2-style SNR
and band-energy metrics, NMO true-vs-wrong behavior, Semblance peak behavior,
FK finite/header/energy-bounds checks, stack peak ratios, and a boolean rollup.
The report is sorted, finite, path-free, and not a public file-format
guarantee.

### S5 Validation Contract

S5 tests verify that the workflow runs in-process and by subprocess, defaults
to a system temporary directory, writes RSF/PNG/JSON outputs without polluting
the repository, preserves finite values, keeps geometry checks true, makes true
NMO velocity outperform wrong velocity, places the Semblance peak near the
known velocity, keeps FK output finite and bounded, makes stack metrics
meaningful, and depends on neither original Madagascar nor C++.

S5 does not implement Radon/slant, velocity picking, full velocity analysis,
full `sfvscan`, full `sfdipfilter`, SEG-Y trace headers, DAS adapters,
localization, inversion, forward modeling, imaging, or C++ kernels. NMO,
Semblance, and FK remain prototypes.

## Seismic Topic S6-0: Topic v0 Summary and Next-Route Decision

S6-0 is a documentation-only decision pass. It adds no algorithm, feature
command, CLI module, console script, stable public API, workflow, test,
command-surface coverage entry, or XMind update. Coverage remains
`86 / 2114`, core coverage remains `73 / 301`, and direct `system/main`
coverage remains `32 / 39`.

### Current Seismic Topic v0 Capability

The v0 seismic topic is locally useful for small deterministic experiments and
regression checks. It supports internal trace/panel/gather fixtures, regular
signed-offset gathers, explicit offset vectors and minimal source/receiver
tables for fixture geometry, existing preprocessing and QC metrics, NMO
true-versus-wrong velocity comparison, Semblance velocity panels, FK spectrum
and fan-filter checks, stack metrics, quicklook PNGs, path-free JSON reports,
and temporary-output workflow execution independent of original Madagascar and
C++.

This is enough to serve as a fixture-backed local Python RSF/geophysics
processing harness. It is not enough to claim production velocity analysis,
field processing, or broad Madagascar compatibility.

### Current Seismic Topic v0 Limits

The v0 loop still excludes non-regular complex acquisition geometry,
field-scale data, streaming/out-of-core execution, production velocity
analysis, automatic velocity picking, Radon/slant validation, SEG-Y trace
headers, DAS adapters, localization, inversion, forward modeling, and imaging.
NMO, Semblance, FK, and Radon remain prototypes.

### Route Ranking After S6-0

1. **A. Continue seismic with Radon/slant source-aligned design.** This is the
   recommended next bounded task if seismic work continues. The repository has
   a current Radon prototype plus located references at
   `../src-master/system/seismic/Mslant.c`, `slant.c`, `Mradon.c`, and
   `radon.c`. A design pass can choose whether the next contract should align
   with `sfslant`-style time-space slant-stack validation, keep the current
   direct time-domain operator pair, or define a separate `sfradon` high-
   resolution boundary before changing behavior.
2. **B. Continue seismic with minimal velocity-picking design.** This is useful
   but should follow the Radon/slant boundary or stay strictly design-only.
   Picking before the scan/operator semantics are settled would overfit the
   S1 hyperbolic fixture and blur the line between regression checks and
   production velocity analysis.
3. **C. Pause seismic and enter inversion/operator topic.** This is the best
   non-seismic route because the project already has dot tests, CG/CGNR, and a
   Radon operator pair, but it needs operator composition, regularization,
   objective/history, and diagnostics before implementation.
4. **F. Pause seismic and enter SEG-Y/header topic.** Important, but high
   blast radius. It should wait for trace ownership, scalar/unit semantics,
   synchronized data/header reorder, and round-trip fixture design.
5. **E. Pause seismic and enter DAS/engineering workflow topic.** D-1 remains
   useful, but adapters, gauge response, automatic picks, and field claims
   should stay paused until shared geometry and validation contracts mature.
6. **D. Pause seismic and enter forward modeling topic.** This should remain a
   design-only route until model/acquisition geometry and accuracy validation
   are stronger; it is less directly connected to the S5 gap than Radon/slant
   or inversion/operator foundations.

### XMind Decision

Do not update XMind for S6-0. The workbook is still a Stage C-10/M1 visual
index, while the eight Markdown files are the authority for topic decisions.
Updating it for a documentation-only route decision would add maintenance churn
without adding navigational value. The better update point is after the next
substantive topic milestone, such as a completed Radon/slant design plus
validation contract or an explicit switch to another topic.

## Seismic Topic S6-1: Radon/slant Source-Aligned Design

S6-1 is a documentation-only source audit and route decision. It adds no
algorithm, feature command, CLI module, console script, stable public API,
workflow, test, command-surface coverage entry, or XMind update. Coverage
remains `86 / 2114`, core coverage remains `73 / 301`, and direct
`system/main` coverage remains `32 / 39`.

### Current Python Radon Boundary

`pymadagascar/seismic/radon.py` currently implements a small direct
time-domain Radon pair:

- `linear_radon` and `parabolic_radon` apply the adjoint transform
  `m = A^T d`.
- `inverse_linear_radon` and `inverse_parabolic_radon` apply modeling
  `d = A m`; this is an algebraic inverse side, not a solved least-squares
  inverse.
- `radon_adjoint_array` and `radon_model_array` expose the same small
  forward/adjoint pair for deterministic array tests.
- The implementation uses time-domain interpolation for linear moveout
  `tau + p*x` and parabolic moveout `tau + q*(x/x0)^2`, supports regular or
  explicit offset vectors, and rejects the reserved `least_squares=True`
  placeholder.
- Existing tests include a linear adjoint dot product, synthetic linear and
  parabolic event peaks, header updates, CLI execution, 3D rejection, missing
  p-axis rejection, and optional original `sfslant` shape comparison when that
  binary is available.

This boundary is useful as a small Pythonic operator prototype, but it is not
a Madagascar clone and should not be promoted to stable maturity.

### `sfslant` Source Boundary

The source-alignment reference for a small slant-stack direction is
`../src-master/system/seismic/Mslant.c` plus
`../src-master/system/seismic/slant.c`.

`sfslant` is a time-space slant-stack/modeling operator. Its key parameters
include `adj=`, `rho=`, `anti=`, `np=`, `dp=`, `p0=`, `p1=`, and inverse-side
`x0=`, `dx=`, `nx=`. The source reads time axis metadata from `n1/o1/d1`,
uses regular offset or slope axis metadata depending on `adj`, and calls
`slant_lop`. The lower-level operator uses anti-aliased stretch and optional
rho filtering through half-integration/half-derivative logic.

The current Python Radon pair is related in spirit because it is a
time-domain forward/adjoint slant/Radon operator for small data, but it omits
`sfslant` anti-alias stretch, rho filtering, reference-slope behavior, and
multi-panel batching. S6-1 therefore chooses source-aligned validation against
a deliberately smaller `sfslant`-style contract, not a claim of equivalence.

### `sfradon` Source Boundary

The high-resolution Radon reference is
`../src-master/system/seismic/Mradon.c` plus
`../src-master/system/seismic/radon.c`.

`sfradon` is a frequency-domain complex Radon transform and inversion family.
Its key parameters include `adj=`, `inv=`, `spk=`, `np=`, `dp=`, `p0=`,
optional `offset=`, `parab=`, `x0=`, and inversion controls such as `eps=`,
`tol=`, and `niter=`. The source FFTs traces, applies a complex phase operator
through `radon_lop`, and for inverse/high-resolution modes uses Toeplitz
solves, sharpening, and complex conjugate-gradient machinery.

The current Python implementation is not `sfradon`: it does not use a
frequency-domain phase operator, does not solve Toeplitz or conjugate-gradient
systems, does not implement spiking/high-resolution inversion, and does not
provide production sparsity controls.

### S6-1 Route Decision

Recommended route: split Radon/slant into two stages.

1. **Next bounded implementation, if requested:** small `sfslant`-style
   slant-stack contract hardening and validation. This should reuse S1-S5
   deterministic fixtures, S4-2 explicit-offset/geometry contracts, analytic
   slant events, dot-test validation, header/axis checks, and optional original
   `sfslant` comparison only for a clearly shared subset.
2. **Later design only:** high-resolution `sfradon` alignment. This should wait
   until the inversion/operator topic has clearer composition, regularization,
   objective/history, preconditioning, and solver-diagnostic contracts.

The current Python forward/adjoint Radon pair should be retained as a separate
prototype boundary. It may support the small slant-stack contract, but it
should not be described as `sfslant`, `sfradon`, or solved Radon inversion.

### Minimum Next Contract

If the next pass implements validation, its smallest acceptable contract is:

- **Data:** finite real small 2D gather/model, RSF axis 1 as time/tau with
  positive `d1`, axis 2 as regular signed offset or a length-compatible
  explicit offset vector, finite regular p/slowness axis, and no SEG-Y trace
  header coupling.
- **Geometry:** signed offsets follow the S4-2 `receiver_minus_source`
  convention; irregular offsets must be explicit, not inferred from trace
  order; source/receiver tables remain internal/testing.
- **Validation:** dot-test agreement for `A` and `A^T`, analytic slant-event
  peak near true slowness, `A m -> A^T A m` recovery of a known tiny model peak,
  finite outputs, path-free temporary artifacts if a workflow is added, clear
  rejection of invalid `d1`, offset vectors, p-axis sampling, non-finite values,
  and reserved least-squares requests.

Do not implement high-resolution Radon inversion, velocity picking, production
Radon, SEG-Y/header integration, DAS adapters, localization, inversion,
forward modeling, imaging, streaming, or C++ kernels in that next bounded pass.

## Seismic Topic S6-2: Small Slant-Stack Contract Hardening and Validation

S6-2 implements the bounded pass selected by S6-1. It adds focused tests and a
workflow regression without adding a feature command, CLI module, console
script, stable public API, or command-surface coverage entry. Coverage remains
`86 / 2114`, core coverage remains `73 / 301`, and direct `system/main`
coverage remains `32 / 39`. XMind remains frozen at the Stage C-10 / M1
snapshot.

### Small Slant-Stack Data Contract

- Data are finite real small 2D gathers with NumPy layout `(ntrace, ntime)`.
- RSF axis 1 is time/tau and must have finite `o1` plus positive finite `d1`.
- RSF axis 2 is a regular signed offset/spatial or slowness axis and must have
  finite origin plus positive finite sampling.
- Explicit offset vectors are allowed only when finite and length-compatible
  with the trace axis or requested modeled `nx`.
- The p/slowness axis must be finite, strictly increasing, and regularly
  sampled. Invalid `pmin`, `pmax`, `dp`, non-finite p values, and reversed p
  axes are rejected.
- NaN/Inf input gathers or Radon models are rejected before transform output is
  written.

### Operator Direction Contract

- `linear_radon` / CLI `radon` apply the adjoint slant-stack direction
  `m = A^T d`.
- `inverse_linear_radon` / CLI `iradon` apply deterministic modeling
  `d = A m`.
- The names remain historical Python prototype names. `iradon` is not a solved
  inverse, not least-squares inversion, and not high-resolution `sfradon`.
- Output headers now record `radon_direction`, `radon_operator_form`,
  `axis2_role`, `radon_madagascar_reference`, and
  `radon_sfradon_equivalence` to make the prototype boundary explicit.

### Validation Contract

`tests/test_seismic_slant_stack_contract.py` and
`examples/my_workflows/seismic_slant_stack_contract_workflow.py` validate:

- Madagascar source-audit paths for `Mslant.c` and `slant.c`;
- dot-test consistency for the `A` / `A^T` pair;
- analytic linear/slant event focusing at the true slope and weaker wrong-slope
  response;
- deterministic modeling of a predictable linear event;
- `radon` then `iradon` shape/header/finiteness invariants;
- regular offset and explicit offset-vector equivalence on the small fixture;
- negative cases for invalid time/offset axes, invalid slope range, non-finite
  input/model samples, reversed/non-finite p axes, and explicit-offset shape
  mismatch;
- existing `radon` and `iradon` CLIs still run;
- workflow outputs stay in a temporary or caller-provided directory, are
  deterministic, path-free, and do not pollute the repository.

### Madagascar Relationship

S6-2 is source-aligned with the small `sfslant` direction in
`../src-master/system/seismic/Mslant.c` and `slant.c`, but it remains a
Pythonic direct time-domain subset. It does not implement `sfslant` rho
filtering, anti-aliased stretch, `p1` reference-slope behavior, multi-panel
batching, or full parameter compatibility.

S6-2 is explicitly not `sfradon`: no frequency-domain phase operator, no
Toeplitz solve, no conjugate-gradient inversion, no spiking/sharpening, no
least-squares solution, and no production Radon claims.

## Seismic Topic S7-0: Closeout and Handoff to Inversion/Operator Topic

S7-0 is a documentation-only closeout. It adds no algorithm, feature command,
CLI module, console script, stable public API, workflow, test, example, or
command-surface coverage entry. Coverage remains `86 / 2114`, core coverage
remains `73 / 301`, and direct `system/main` coverage remains `32 / 39`.
XMind remains frozen at the Stage C-10 / M1 snapshot.

Seismic Topic v0 is now a small, deterministic, fixture-backed regression
harness. It can generate trace/panel/gather fixtures, regular signed-offset
gathers, minimal geometry reports, preprocessing/QC metrics, NMO true-vs-wrong
velocity checks, Semblance velocity panels, FK spectra and fan-filter checks,
small slant-stack/Radon adjoint/modeling checks, stacks, quicklook PNGs,
path-free JSON reports, and integrated temporary-output workflow regressions.

Seismic Topic v0 is not a production seismic processing framework. It still
does not support field-scale data, production velocity analysis, velocity
picking, non-regular complex acquisition geometry, high-resolution `sfradon`,
least-squares or CG Radon inversion, SEG-Y trace headers, DAS adapters,
streaming/out-of-core execution, or production modeling/inversion/imaging.

S7-0 recommends pausing seismic signal-topic expansion before S6-3. Immediate
high-resolution `sfradon` is deferred because the project lacks reusable
operator composition, regularization, objective/residual history, stopping
diagnostics, and preconditioning contracts. Velocity picking is deferred
because it would turn the current fixture evidence into a production-style
decision workflow before Semblance/Radon uncertainty and acceptance semantics
are mature. SEG-Y/header work remains separate because trace ownership,
coordinate scalars, and row-to-trace synchronization are not part of ordinary
RSF headers or S4-2 minimal geometry fixtures.

The next recommended topic is **Inversion / Operator Foundation**. The route
order after S7-0 is:

1. Inversion / Operator Foundation.
2. Minimal velocity-picking design.
3. High-resolution `sfradon` design.
4. SEG-Y/header topic.
5. DAS/engineering workflow topic.
6. Forward modeling topic.
7. Imaging topic.

## Inversion / Operator Foundation I0-0: Current Capability Audit and Contract Design

I0-0 opens the Inversion / Operator Foundation topic as an audit/design pass
only. It adds no algorithm, solver, feature command, CLI module, console
script, stable public API, workflow, test, example, or command-surface coverage
entry. Coverage remains `86 / 2114`, core coverage remains `73 / 301`, and
direct `system/main` coverage remains `32 / 39`. XMind remains frozen at the
Stage C-10 / M1 snapshot.

Current operator capability:

- `pymadagascar.generic.linear_operator` provides an abstract
  `LinearOperator`, dense `MatrixOperator`, `IdentityOperator`, and
  `CallableLinearOperator` for small in-memory arrays.
- Real `dot_test` and complex `complex_dot_test` check adjoint consistency with
  NumPy real-dot and Hermitian `vdot` conventions.
- Real and complex conjugate-gradient helpers cover small SPD/Hermitian systems
  and normal equations, with scalar damping in normal-equation mode.
- Result objects report final solution, residual norm, iteration count, and a
  convergence flag, but not per-iteration history or a named stopping reason.
- The current Radon/slant pair contributes a domain forward/adjoint example:
  `radon` is `m=A^T d` and `iradon` is modeling `d=A m`, not solved inversion.
- The D-1 DAS road-void workflow contains a workflow-only least-squares grid
  search/variable-projection helper; it is not reusable package inversion API.
- Acoustic2d and Kirchhoff are forward/direct geophysical prototypes. They do
  not yet provide reusable adjoint `LinearOperator` objects or dot-tested
  inversion contracts.

Madagascar source alignment for I0-0 is limited to capability audit, not
migration. `../src-master/system/main/dottest.c` and `cdottest.c` implement
external-operator dot tests using Madagascar stream parameters such as
`adj=`, `mod=`, and `dat=`. `../src-master/system/main/conjgrad.c` and
`cconjgrad.c` are generic external-operator inversion drivers with pipe/
tempfile execution and options such as model weights, known masks, initial
models, and iteration controls. The current Python B-4 subset is intentionally
matrix/callable-object backed; it does not clone that external command
protocol, stream out-of-core data, or implement upstream weighting/masking
semantics.

Main gaps before reusable inversion work:

- operator composition, sums, scaling, block operators, and stacked operators;
- reusable identity, diagonal, finite-difference, and smoothing regularization
  operators beyond scalar damping;
- objective, residual, and per-iteration history schema;
- stopping diagnostics with explicit stopping reasons;
- preconditioner contracts;
- reusable inversion-problem/result objects;
- public API boundary for future operator algebra and solver records;
- domain-specific inversion workflows that consume those contracts without
  bypassing dot-test and metadata discipline.

I0-0 data contract design:

- Model and data may be flat vectors or shaped arrays, but every operator must
  declare model shape, data shape, dtype policy, and finite-value policy.
- Real and complex arrays are both allowed when the operator and solver declare
  the correct adjoint convention.
- RSF flatten/unflatten must preserve axis metadata, labels, units, and any
  domain geometry needed to interpret the vector.
- Residual vectors live in data space and must be shape-compatible with the
  observed data.
- Solver-history JSON, when added later, should be an internal regression
  artifact until promoted deliberately; it must not contain local absolute
  paths or random non-deterministic fields.

I0-0 operator contract design:

- Forward applies `y = A x`; adjoint applies `x = A^T y` for real operators or
  `x = A^H y` for complex operators.
- Every operator owns explicit domain/range shapes and must reject
  shape-incompatible, non-finite, or dtype-incompatible inputs with clear
  errors.
- Dot tests remain the entry gate: small deterministic references should pass
  documented absolute/relative tolerances before an operator is used in a
  solver.
- Future composition must preserve shape/domain/range metadata through scale,
  sum, chain, stack, and block operations.
- Future regularization operators should start with identity, diagonal, and
  finite-difference subsets before any domain inversion claim.

I0-0 solver contract design:

- Existing CG/CGNR helpers remain small in-memory solver subsets; they are not
  production inversion drivers.
- Future solver calls should accept an operator, right-hand side, optional
  initial model, iteration limit, tolerance, and explicit damping/
  regularization ownership.
- Future result records should include final model, residual norm, objective
  value when defined, convergence flag, stopping reason, iteration count, and
  per-iteration history.
- Preconditioning is deferred until its shape, adjoint, and diagnostics
  contracts are explicit.
- High-resolution Radon, imaging inversion, DAS inversion, velocity inversion,
  CGLS/LSQR, and production least-squares workflows stay deferred until these
  foundation contracts exist.

I0-0 next-route ranking:

1. Operator composition and history contract.
2. Regularization operator subset.
3. CGLS / LSQR design.
4. Radon least-squares inversion.
5. Imaging adjoint test design.
6. DAS inversion workflow hardening.

The recommended first bounded task is operator composition and history
contract because it reduces risk for all later inversion work without adding a
new solver. Regularization, CGLS/LSQR, Radon least-squares, imaging adjoint
tests, and DAS inversion hardening should wait until that metadata and
diagnostic spine is clear.

## Inversion / Operator Foundation I0-1: Operator Composition and History Contract Foundation

I0-1 is the first bounded implementation pass in the Inversion / Operator
Foundation topic. It adds small in-memory operator algebra and an
internal/prototype diagnostics container only. It adds no geophysical
algorithm, solver, CLI module, console script, stable root/API export,
workflow, example, original Madagascar dependency, C++ dependency, or
command-surface coverage entry. Coverage remains `86 / 2114`, core coverage
remains `73 / 301`, and direct `system/main` coverage remains `32 / 39`.

I0-1 operator-composition contract:

- `ScaledOperator` represents `alpha * A`; forward scales `A x`, and adjoint
  scales `A^H y` by `conj(alpha)` for complex operators.
- `SumOperator` represents `A + B` and requires identical model and data
  shapes.
- `ComposedOperator` represents `A @ B`, meaning `A(Bx)`, and requires
  `B.data_shape == A.model_shape`.
- `StackedOperator` represents a vertical stack `[A; B; ...]`, requires a
  shared model shape, concatenates flattened data-space outputs, and sums
  component adjoints.
- All composition helpers preserve model/data shape metadata, reject
  shape-incompatible requests, and reject non-finite input/output values.
- Real dot tests and complex Hermitian dot tests are expected to pass for
  scaled, summed, composed, and stacked operators before they are used in a
  solver or domain workflow.

I0-1 history/result contract:

- `SolverIterationRecord` records iteration, residual norm, optional
  objective, optional gradient norm, optional step length, and metadata.
- `SolverHistory` records ordered iteration records, convergence flag, stopping
  reason, and metadata.
- `SolverResult` records a finite final model, convergence flag, iteration
  count, residual norm, optional objective, optional history, stopping reason,
  and metadata.
- `to_summary()` outputs are deterministic and JSON-serializable, including
  complex values as explicit real/imag dictionaries.
- These records are internal/prototype diagnostics. They are not a stable JSON
  schema and are not yet wired into the existing CG/CGNR helpers.

I0-1 backward-compatibility boundary:

- Existing `conjugate_gradient`, `conjugate_gradient_normal`,
  `conjgrad_solve`, and `complex_conjgrad_solve` keep their current return
  contract and do not gain a `history` field in this pass.
- New composition and history classes are available from the implementation
  module for prototype/testing use, but are not imported from
  `pymadagascar.__init__` or `pymadagascar.api`.

I0-1 remaining gaps before I0-2:

- No reusable identity/diagonal/finite-difference/smoothing regularization
  operator subset yet.
- No objective/residual integration into solver calls.
- No CGLS, LSQR, preconditioner contract, block operator family, or reusable
  inversion-problem object.
- No high-resolution `sfradon`, Radon least-squares inversion, imaging
  inversion, DAS inversion, velocity inversion, or production inversion claim.

The recommended next bounded task is a regularization-operator subset:
identity, diagonal, and first-difference prototypes with dot tests and shape/
metadata contracts. CGLS/LSQR design, high-resolution `sfradon`, and domain
inversions should wait until that regularization layer exists.

## Inversion / Operator Foundation I0-2: Regularization Operator Subset

I0-2 is the second bounded implementation pass in the Inversion / Operator
Foundation topic. It adds small in-memory regularization operators compatible
with the existing `LinearOperator` contract and I0-1 composition helpers. It
adds no geophysical algorithm, solver, CLI module, console script, stable
root/API export, workflow, example, original Madagascar dependency, C++
dependency, XMind update, or command-surface coverage entry. Coverage remains
`86 / 2114`, core coverage remains `73 / 301`, and direct `system/main`
coverage remains `32 / 39`.

I0-2 regularization contract:

- Identity/damping regularization reuses `IdentityOperator` and
  `ScaledOperator`; `lambda * IdentityOperator(shape)` expresses `lambda I`.
- `DiagonalRegularization` represents `Lx = w * x`, requires finite weights
  compatible with the model shape, and uses conjugated weights in the complex
  adjoint.
- `FirstDifferenceRegularization` applies a flattened valid-boundary stencil
  `x[i + 1] - x[i]`. Its range length is `model_size - 1`, and its adjoint is
  the exact transpose/Hermitian-adjoint accumulation for that stencil.
- `SecondDifferenceRegularization` applies a flattened valid-boundary stencil
  `x[i] - 2*x[i + 1] + x[i + 2]`. Its range length is `model_size - 2`, and
  its adjoint is the exact matching accumulation.
- All operators reject shape-incompatible or non-finite inputs and pass real or
  complex dot tests within the documented small-data tolerance.
- `[A; lambda L]` is expressible with `StackedOperator([A, lambda * L])`; I0-2
  validates forward/adjoint shapes and dot-test readiness but does not solve a
  least-squares problem.

I0-2 backward-compatibility boundary:

- Existing `conjugate_gradient`, `conjugate_gradient_normal`,
  `conjgrad_solve`, and `complex_conjgrad_solve` keep their current return
  contract and are not wired to regularization or `SolverHistory`.
- New regularization classes are direct-module prototype/testing surfaces only
  and are not imported from `pymadagascar.__init__` or `pymadagascar.api`.
- The subset is flattened and in-memory. It is not axis-aware multidimensional
  smoothing, not total variation, not constrained inversion, not a
  preconditioner framework, and not production inversion.

I0-2 remaining gaps:

- No objective/residual integration into solver calls.
- No solver-attached history, named stopping diagnostics, or convergence
  report schema.
- No CGLS, LSQR, preconditioner contract, block operator family, or reusable
  inversion-problem object.
- No high-resolution `sfradon`, Radon least-squares inversion, imaging
  inversion, DAS inversion, velocity inversion, or production inversion claim.

The recommended next bounded task is an objective/residual and solver
diagnostics contract: define how `[A; lambda L]` residuals, objective terms,
history records, stopping reasons, and JSON summaries should be represented
before adding CGLS/LSQR or any domain inversion.

## Inversion / Operator Foundation I0-3: Objective / Residual / Diagnostics Problem Layer

I0-3 is the third bounded implementation pass in the Inversion / Operator
Foundation topic. It connects the I0-1 operator algebra/history containers and
I0-2 regularization operators through a small in-memory least-squares
problem/objective/diagnostics layer. It adds no geophysical algorithm, solver,
CLI module, console script, stable root/API export, workflow, example,
original Madagascar dependency, C++ dependency, XMind update, or
command-surface coverage entry. Coverage remains `86 / 2114`, core coverage
remains `73 / 301`, and direct `system/main` coverage remains `32 / 39`.

I0-3 problem contract:

- `LeastSquaresProblem(A, b, regularization=None, reg_weight=0.0)` accepts a
  `LinearOperator`-compatible data operator, finite data vector in the data
  space, an optional `LinearOperator`-compatible regularization operator, and a
  finite non-negative regularization weight.
- The regularization operator domain must match `A.model_shape`.
- `data_residual(x)` returns `A x - b` with shape `A.data_shape`.
- `regularization_residual(x)` returns `lambda L x`, or an empty vector when
  regularization is inactive or `reg_weight == 0`.
- `total_residual(x)` returns the flattened concatenation of data and active
  regularization residuals.
- `objective(x)` returns
  `0.5 ||A x - b||^2 + 0.5 ||lambda L x||^2`, using Hermitian norms for
  complex arrays.
- `gradient(x)` returns the normal-equation gradient
  `A^H(Ax-b) + lambda^2 L^H Lx` for the small in-memory problem. It is a
  diagnostics building block, not a solver step implementation.

I0-3 diagnostics contract:

- `ObjectiveDiagnostics` records objective, data objective, regularization
  objective, data/regularization/total residual norms, optional gradient norm,
  iteration, convergence flag, stopping reason, and metadata.
- `StoppingDiagnostics.from_thresholds(...)` classifies small solver states
  with `residual_tolerance`, `objective_tolerance`, `gradient_tolerance`,
  `max_iterations`, `not_converged`, and `invalid_state`.
- `LeastSquaresProblem.iteration_record(...)` and `solver_result(...)` bridge
  objective diagnostics into the existing `SolverIterationRecord`,
  `SolverHistory`, and `SolverResult` containers without changing existing
  CG/CGNR return contracts.
- All summaries are deterministic and JSON-safe internal/prototype artifacts,
  not public report schemas.

I0-3 remaining gaps:

- Existing CG/CGNR helpers are still not wired to `LeastSquaresProblem`,
  `SolverHistory`, or `StoppingDiagnostics`.
- No CGLS, LSQR, preconditioner contract, block operator family, or reusable
  production inversion driver exists.
- No high-resolution `sfradon`, Radon least-squares inversion, imaging
  inversion, DAS inversion, velocity inversion, or production inversion claim.

The recommended next bounded task is CGLS/LSQR design or a preconditioner
contract, still before any domain inversion implementation. The project should
not jump directly from I0-3 into Radon LS, DAS inversion, or imaging inversion.

## Inversion / Operator Foundation I0-4: Solver Diagnostics Integration and CGLS/LSQR Design

I0-4 optionally connects the existing CG iteration core to the I0-1/I0-3
diagnostics containers without changing established solver functions or CLI
behavior. It adds no new solver algorithm, CLI module, console script, stable
root/API export, workflow, example, XMind update, or command-surface coverage.

I0-4 history contract:

- `run_cg_with_history` returns a prototype `SolverResult` whose history starts
  at iteration zero. Residuals are linear-system residuals; objective is
  explicitly residual energy `0.5 ||r||^2`.
- `run_cgnr_with_history` executes the existing CGNR normal-equation core but
  uses `LeastSquaresProblem` for augmented data/regularization residuals,
  objective, and gradient diagnostics. Its stopping tolerance remains based on
  the normal-equation residual and records that distinction in metadata.
- Real and complex operators use the same contract. Completed iterations may
  record step length. Summary metadata includes iteration limit, tolerance,
  damping, residual-space ownership, and JSON-safe caller metadata.
- Stopping reasons are `residual_tolerance`, `max_iterations`, and
  `invalid_state`. The tracked helper captures zero-curvature breakdown as
  `invalid_state`; the unchanged default CG path retains its prior exception.
- `conjugate_gradient`, `conjugate_gradient_normal`, complex aliases,
  dispatch helpers, `ConjugateGradientResult`, and CLI text remain unchanged.

I0-4 CGLS/LSQR source audit:

- `../src-master/system/main/conjgrad.c` and `cconjgrad.c` drive external
  forward/adjoint commands through pipes and temporary files; they are not the
  in-memory Python solver contract.
- `../src-master/api/c/conjgrad.c` and `cconjgrad.c` implement shaping and
  optional preconditioning contracts that are broader and structurally
  different from the current scalar-damping CGNR subset.
- `../src-master/user/pyang/Mmwni2d.c` contains a domain-specific CGLS loop.
  No generic `system/main` CGLS implementation was located.
- LSQR was located as the book MATLAB file
  `../src-master/book/slim/geo2008NewInsightsPareto/Matfcts/private/lsqr.m` and
  RVL C++ support under `../src-master/trip/rvl/umin/include/lsqr.hh`; no
  pure-C generic `system/main` LSQR solver was located.

I0-4 design decision:

- CGLS should not be an alias for current CGNR. It should consume
  `LeastSquaresProblem`, call `A`/`A^H` directly, and expose data residual,
  gradient norm, objective, stopping reason, and optional history.
- General regularization should use the augmented system `[A; lambda L]` with
  right-hand side `[b; 0]`, reusing `StackedOperator`; scalar damping remains a
  compatibility subset.
- The first bounded CGLS implementation may be unpreconditioned. Any later
  preconditioned path requires a separate model/data-space contract.
- LSQR remains a separate later solver based on Golub-Kahan bidiagonalization
  and needs condition/residual stopping diagnostics not provided by CGNR.
- Neither CGLS nor LSQR is implemented in I0-4. Radon LS, high-resolution
  `sfradon`, DAS inversion, imaging inversion, and production inversion remain
  deferred.

The next bounded task may implement the minimal unpreconditioned CGLS contract
against dense references and `[A; lambda L]` fixtures. LSQR and production
preconditioning should remain separate later passes.

## Inversion / Operator Foundation I0-5: Bounded Unpreconditioned CGLS

I0-5 implements the first reusable bounded least-squares solver as two
direct-module prototypes: `run_cgls(A, b, ...)` and
`run_cgls_problem(problem, ...)`. It adds no CLI module, console script,
stable root/API export, workflow, example, XMind update, or command-surface
coverage.

CGLS contract:

- Inputs are a finite `LinearOperator`-compatible `A` and finite data `b`, or
  an existing `LeastSquaresProblem`; optional finite `x0`; positive `maxiter`;
  finite nonnegative `tol`; and optional/default-on history.
- The data residual is `b - A x`; the normal residual is `A^H(b - A x)`.
  Active regularization reuses `[A; lambda L] x ~= [b; 0]` through
  `StackedOperator`, so the recurrence residual becomes
  `[b - A x; -lambda L x]` without a second regularization system.
- Convergence is relative to the initial augmented normal-residual norm with a
  unit floor. Stopping reasons are `gradient_tolerance`, `max_iterations`, and
  `invalid_state`.
- `LeastSquaresProblem` owns objective/data/regularization diagnostics;
  `SolverHistory` records iteration zero and completed steps; `SolverResult`
  owns the final model and JSON-safe summary.
- Real and complex operators share the implementation; complex problems use
  Hermitian adjoints and `vdot` norms.

I0-5 remains small, in-memory, and unpreconditioned. It does not implement
LSQR, a preconditioner contract, constraints, Radon LS, DAS/imaging/velocity
inversion, streaming, or production inversion workflows. The next bounded
route is preconditioner contract design or a separate LSQR implementation.

## Inversion / Operator Foundation I0-6: Preconditioner Contract Design

I0-6 defines, but does not consume, an explicit preconditioner contract. The
selected next-solver direction is right/model-space preconditioning:

```text
x = M z
minimize ||A M z - b||
regularized: [A; lambda L] M z ~= [b; 0]
```

`Preconditioner` requires forward and Hermitian-adjoint actions because it is
a semantic `LinearOperator` transform. Identity and invertible diagonal
variants support real/complex small in-memory arrays. Diagnostics record kind,
domain/range shapes, identity/diagonal flags, scale range, diagonal condition
hint, and complex support. Zero diagonal weights are rejected: masks and
constraints are distinct future contracts.

Preconditioning changes variables/scaling and intended convergence behavior;
regularization changes the least-squares objective. `as_preconditioner`
therefore rejects ordinary operators, including regularization operators,
unless they are wrapped in an explicit future preconditioner type. Left/data-
space weighting `W(Ax-b)` is separate and deferred.

I0-6 does not modify `run_cgls`, implement preconditioned CGLS/CGNR/LSQR, add
a CLI/stable export, change coverage, update XMind, or enter domain inversion.
Before solver integration, the now-large `linear_operator.py` should be split
into operator, least-squares, solver, and preconditioner modules while
preserving direct-module compatibility.

## Inversion / Operator Foundation I0-9B1: Bounded Unpreconditioned / Regularized LSQR

I0-9B1 adds a bounded pure-Python LSQR prototype as direct-module helpers
`run_lsqr` and `run_lsqr_problem`. The implementation targets small
deterministic in-memory least-squares problems, uses a Golub-Kahan
bidiagonalization recurrence, and reuses the existing `LeastSquaresProblem`
diagnostics containers rather than adding a stable/root solver API.

Supported scope:

- unpreconditioned `min_x 0.5 * ||A x - b||^2`;
- regularized `LeastSquaresProblem` through the existing `[A; lambda L] x ~= [b; 0]`
  augmented system;
- model-space nonzero `x0` through a shifted residual correction solve;
- small real dense/callable operators and a small complex smoke path;
- `SolverResult` / optional `SolverHistory` metadata for residual convention,
  convergence residual space, normal residual, objective kind, and API boundary.

I0-9B1 deliberately does not add CLI coverage, console scripts, root/stable API
exports, right-preconditioned LSQR, left/data-space weighting, constraints,
masks, domain inversion, production-scale/out-of-core behavior, or a coverage
denominator change. Passing a preconditioner is an explicit unsupported boundary
instead of a silent no-op.

## R1 Topic Capability Matrix

This earlier grouping remains as implementation inventory. The T1 topic
decisions and entry contracts above supersede its route recommendations.

| Topic | Core modules and CLI families | Examples/workflows | Maturity | Main shortfall | Recommended next step | Start now? | Foundation first? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| General RSF and data handling | `io.rsf`, core axes/hypercubes, `window/put/get/info/dd/cat/transp/reshape/mask/cut/reverse`, file ops, minimal header table | I/O, quickstart, window, format, header demos; basic RSF and spike/math workflows | stable / stable subset | Basic pipes and out-of-core processing remain limited; header-table and SEG-Y trace-header models are separate and incomplete | Freeze the stable core except for use-case-driven gaps and regression fixes | Yes, but only targeted work | No for ordinary RSF; yes for trace-header work |
| Array math, statistics, and QC | `math/add/mul/div/scale/normalize/clip/clip2/threshold`, unary transforms, histogram/quantile, robust statistics, non-finite QC, `attr/min/max/diff/byte` | unary, robust-statistics, math, byte, amplitude-conditioning demos | stable subset; several Pythonic conveniences | No weighted/grouped/local statistics, streaming accumulation, or broad complex statistics | Treat as locally usable; add only gaps exposed by workflows | Not as a broad topic | Usually no |
| Signal processing | FFT family, filters, smoothing, taper, spectra, envelope, correlation/convolution, shifts, calculus, Ricker, demean/detrend, decimation, band-stop/notch, local RMS, standard windows, PSD/CSD/coherence, spectrogram/SNR, Welch averaging, transfer estimates, whitening, attributes, windowed-sinc FIR, response QC, and band decomposition | preprocessing, correlation, calculus, smooth/noise/Ricker, signal-QC, spectral-QC, spectral-averaging, and FIR-design demos; FFT-bandpass workflow | stable subset | No IIR design, advanced windows, multi-taper/AR estimation, arbitrary-axis STFT, full system identification, multirate/polyphase processing, or streaming | Enter the seismic signal topic through contracts, fixtures, and one existing-API pipeline regression | Yes, as the first topic | Yes, shared data and validation fixtures |
| Seismic processing | gain, AGC, mute/mutter, stack/stacks; NMO, semblance, FK, Radon; bin/linear/slice/max1 helpers | gather-QC demo and AGC/mute/stack workflow plus S1/S2/S3/S4-1/S4-2/S4-3/S6-2 contract workflows and the S5 integrated small-gather workflow | stable subset for basic QC; prototype for NMO/Semblance/FK/Radon | Field-scale/non-regular geometry, velocity picking, high-resolution Radon/inversion foundations, multi-gather tests, and trace-header integration | Pause after S7-0 by default; resume only through an explicit bounded design or source-aligned task | No, unless a narrow follow-up is explicitly selected | Yes, geometry and deterministic validation fixtures |
| Forward modeling | `modeling.acoustic2d`, `modeling.geometry`, `modeling.shot`, `modeling.models`, Ricker, RSF model grids | acquisition-driven single-shot and multi-shot wrappers, explicit survey tensor conversion helper, synthetic constant/layered/anomaly velocity builders, F0-6 geometry-driven validation workflow, component tests, and Ricker demo | simplified prototype | No interpolation, smoothing/random/geologic model building, production tensor/padding policy, accuracy/convergence/dispersion study, or production scale | Defer new solver algorithms; next add validation evidence only through bounded smoke/fixture workflows | Not yet | Yes |
| Inversion and operators | `LinearOperator`, matrix/callable operators, composition helpers, regularization operators, least-squares problem diagnostics, optional CG/CGNR history adapters, bounded CGLS, bounded unpreconditioned/regularized LSQR, right/model-space preconditioner contract, dot tests, CG/CGNR; Radon operator pair | linear-operator demo | partial / prototype | No preconditioned LSQR, stable/root solver API, constraints/masks, or domain inversion workflow | Continue only through bounded solver-contract passes, with right-preconditioned LSQR as a separate future task | Yes, current topic | Yes |
| Imaging | simplified Kirchhoff, plus FK/Radon/acoustic2d building blocks | Kirchhoff diffraction demo | simplified prototype | No acquisition model, amplitude/anti-alias treatment, migration adjoint test, velocity workflow, or reference suite | Postpone algorithm expansion; improve synthetic validation before adding methods | No | Yes |
| DAS and engineering workflows | Existing RSF, signal, QC, picking, FK, and plotting tools can process small regular arrays | D-1 kinematic road-void diffraction workflow | workflow-only | No HDF5/TDMS/DAT adapters, gauge-length/strain response, automatic picks, channel geometry contract, chunking, or field fixtures | Retain D-1 as workflow-first; pause D-2 and all adapter work | Later, by explicit decision | Geometry and validation design |
| Data formats, SEG-Y, and headers | stable RSF I/O; 2D SEG-Y read/write and trace-word extraction; minimal header table tools | header-table demos; no SEG-Y workflow | stable RSF / prototype SEG-Y / partial header table | No unified trace-header data model, synchronized data/header reorder, scalar/unit policy, or broad SEG-Y round trip | Keep `sfsegyheader` as a separate B-3-3 design task | Not immediately | Yes, explicit data model |
| Plot and quicklook | Matplotlib `graph/grey/wiggle` | plot demo and grey/graph workflow | partial quicklook substitute | Not VPlot, limited styling/composition, no domain dashboard | Keep lightweight; improve only when workflows need clearer QC output | Yes, as support work | No |

The stable center of the project is ordinary RSF I/O, axis metadata, generic
array processing, statistics/QC, and the small-data signal toolkit. NMO,
semblance, FK, Radon, SEG-Y, linear-operator inversion, acoustic modeling, and
Kirchhoff migration remain deliberately bounded prototype areas even though
they have tests and CLI surfaces.

## Ranked Route Options

1. **Minimal unpreconditioned CGLS implementation.** Consume
   `LeastSquaresProblem`, preserve augmented `[A; lambda L]` semantics, and
   validate against dense references before any domain inversion.
2. **Preconditioner contract.** Define model/data space, scaling, diagnostics,
   and interaction with `[A; lambda L]` before any production inversion claim.
3. **Right-preconditioned LSQR design.** Keep Golub-Kahan state, latent/model
   diagnostics, and stopping behavior separate from CGNR/CGLS; do not infer
   preconditioner support from the unpreconditioned LSQR prototype.
4. **Localization follow-up design.** L0-1/L0-2 supply only homogeneous 2D
   travel-time and fixed/variable-velocity grid-search point-location
   primitives. A later pass should design pick records, uncertainty/weights,
   identifiability reporting, and interfaces to DAS/seismic geometry before
   adding automatic picking or production location workflows.
5. **Minimal velocity-picking design.** Keep this design-only; do not add
   automatic picking or production velocity analysis until uncertainty,
   acceptance metrics, and Semblance/Radon semantics are mature.
6. **High-resolution `sfradon` design.** Defer implementation until the
   inversion/operator foundation can carry Toeplitz/CG, objective,
   regularization, and diagnostics contracts.
7. **SEG-Y / header topic.** Defer until trace ownership, scalar/coordinate
   semantics, row-to-trace synchronization, and round-trip fixtures are
   designed. `sfsegyheader` remains a separate task.
8. **DAS / engineering workflow.** Retain D-1 as a synthetic workflow and
   consume shared contracts later. D-2, adapters, gauge response, automatic
   picking, and uncertainty implementation remain paused.
9. **Forward modeling validation.** F0-1 defines model/acquisition geometry,
   F0-2 connects it to one acoustic2d shot wrapper, F0-3 adds sequential
   multi-shot survey execution, F0-4 adds explicit tensor/summary helpers, and
   F0-5 adds deterministic synthetic velocity model builders. F0-6 adds the
   first tiny geometry-driven validation workflow; a later pass should add an
   accuracy-validation matrix only as a separate bounded task and without adding
   a new solver or kernel.
10. **Imaging topic.** Defer until geometry, forward, operator, and reference
   validation foundations exist.

Stage D-1 remains intact, but the route stops before D-2. Stages C-7 through
C-10 already supply the conditioning, spectral-QC, and FIR foundations.
Topic-oriented work replaces the Stage C sequence; there is no recommended
C-11.

## Source Mapping for Recent Batches

| Command | Upstream source | pymadagascar status |
| --- | --- | --- |
| `sfcp` | `../src-master/system/main/cp.c` | stable subset |
| `sfrm` | `../src-master/system/main/rm.c` | stable subset |
| `sfmin` | alias of upstream `sfstack` | text-stat subset |
| `sfmax` | alias of upstream `sfstack` | text-stat subset |
| `sfmul` | alias backed by `../src-master/system/main/add.c` | stable subset |
| `sfdiv` | alias backed by `../src-master/system/main/add.c` | stable subset |
| `sftpow` | `../src-master/user/nobody/Mtpow.c` | stable subset, not core coverage |
| `sfinterleave` | `../src-master/system/main/interleave.c` | stable subset |
| `sfpad` | `../src-master/system/main/pad.c` | bounded constant-value axis padding with `beg#`, `end#`, `n#`/`n#out`; no streaming, `sfput` passthrough, or native byte-copy path |
| `sfspray` | `../src-master/system/main/spray.c` | bounded new-axis duplication with `axis=`, `n=`, `o=`, `d=`, `label=`, and `unit=`; no streaming/out-of-core execution |
| `sfscale` | `../src-master/system/main/scale.c` | scalar `scale=`/`dscale=` subset; registered console script in M0-1 |
| `sfrotate` | `../src-master/system/main/rotate.c` | cyclic `rot#` axis-rotation subset; no out-of-core streaming |
| `sfstack` | `../src-master/system/main/stack.c` | bounded axis stack subset with `axis=`, `mode=mean/sum/rms`, and `nonzero=` fold behavior; no `axis=0`, scale vector, min/max/prod aliases, or streaming |
| `sfheaderwindow` | `../src-master/system/main/headerwindow.c` | ordinary-RSF mask subset |
| `sfheadercut` | `../src-master/system/main/headercut.c` | ordinary-RSF mask subset |
| `sfheaderattr` | `../src-master/system/seismic/Mheaderattr.c` | minimal header table statistics subset |
| `sfheadermath` | `../src-master/system/seismic/Mheadermath.c` | minimal header table safe-expression subset |
| `sfheadersort` | `../src-master/system/main/headersort.c` | minimal header table row-sort subset |
| `sfdottest` | `../src-master/system/main/dottest.c` | matrix/identity-backed real dot-test subset; no external command operator |
| `sfcdottest` | `../src-master/system/main/cdottest.c` | matrix/identity-backed complex dot-test subset; no external command operator |
| `sfconjgrad` | `../src-master/system/main/conjgrad.c` | small real matrix-backed SPD/normal CG subset |
| `sfcconjgrad` | `../src-master/system/main/cconjgrad.c` | small complex matrix-backed Hermitian/normal CG subset |
| `sfcostaper` | `../src-master/system/generic/Mcostaper.c` | small axis-aware cosine taper subset |
| `sfthreshold` | `../src-master/system/generic/Mthreshold.c` | explicit hard/soft threshold subset; not pclip-only clone |
| `sfspectra` | `../src-master/system/generic/Mspectra.c` | simple RFFT amplitude/power spectrum subset |
| `sfclip` | `../src-master/system/generic/Mclip.c` | bounded `clip=`/`value=` amplitude clipping subset with source-aligned non-finite replacement; no streaming or complex input |
| `sfnoise` | `../src-master/system/generic/Mnoise.c` | bounded deterministic NumPy normal/uniform add-or-replace subset; no byte-identical upstream RNG promise |
| `sfboxsmooth` | `../src-master/system/generic/Mboxsmooth.c` | centered in-memory box smoothing subset with `rect#`, `axis=`, and `repeat=`; no streaming |
| `sflaplac` | `../src-master/system/generic/Mlaplac.c` with `laplac2.c` | bounded real graph-Laplacian subset with selected axes and optional header spacing; no `adj=`, coefficient field, inverse solve, or streaming |
| `sfsmooth` | `../src-master/system/generic/Msmooth.c` | centered triangle smoothing subset with `rect#`, selected axes, and `repeat=`; no `adj=`, `diff#`, per-axis `box#`, complex input, or streaming |
| `sftrapez` | `../src-master/system/generic/Mtrapez.c` with `trapez.c` | one-axis real-input RFFT trapezoidal frequency-filter subset with `frequency=` or `f1/f2/f3/f4`; no complex input or byte-identical FFT rounding promise |
| `sffft1` | `../src-master/system/generic/Mfft1.c` | one-axis real-to-complex RFFT and complex-to-real inverse subset with ordinary `fft_n#` metadata; no FFTW planning, `opt=`, `ot=`, `sym=`, streaming, or byte-identical scaling |
| `sfcosft` | `../src-master/system/generic/Mcosft.c` | one-axis real orthonormal DCT-II/DCT-III subset; no multi-axis `sign#` dispatch, streaming, or byte-identical kiss_fft normalization |
| `sfspectra2` | `../src-master/system/generic/Mspectra2.c` | in-memory two-axis amplitude/power spectrum subset with optional plane averaging; no FFTW optimal padding, plotting, streaming, or byte-identical FFT rounding |
| `sfenvelope` | `../src-master/system/seismic/Menvelope.c` | FFT Hilbert envelope subset; no phase-rotation mode |
| `sflinear` | `../src-master/system/generic/Mlinear.c` | regular-axis resampling subset; upstream is irregular coordinate/value-table interpolation |
| `sfremap1` | `../src-master/system/generic/Mremap1.c` | bounded one-axis regular-grid linear remap subset; no ENO orders above 1, `pattern=`, or streaming |
| `sfspline` | `../src-master/system/generic/Mspline.c` | bounded one-axis natural-cubic regular-axis interpolation subset; no irregular table mode, `fp=`, `pattern=`, or SciPy dependency |
| `sft2warp` | `../src-master/system/generic/Mt2warp.c` | bounded one-axis linear-interpolation time-squared warp and inverse; no adjoint modes, stretch regularization, logwarp, or byte-identical `sf_stretch4` behavior |
| `sfmatmult` | `../src-master/system/generic/Mmatmult.c` | bounded real matrix-vector multiplication subset with optional `adj=`; no complex, sparse, batched, solver, or out-of-core behavior |
| `sfmatch` | `../src-master/system/generic/Mmatch.c` | bounded real symmetric matching-filter loop subset; no shaping-filter solver, frequency-domain matching, or streaming |
| `sflinefit` | `../src-master/system/generic/Mlinefit.c` | bounded ordinary least-squares line fit from an `n1=2` table; no pattern files, multi-trace batches, or robust regression |
| `sfagc` | `../src-master/system/generic/Magc.c` | bounded one-axis local-RMS AGC with physical `rect=` conversion; upstream smooths absolute amplitudes with multi-axis triangle filtering and `repeat=` |
| `sfavo` | `../src-master/system/seismic/Mavo.c` | bounded real CMP-gather AVO intercept/gradient least-squares subset over RSF axis 2; no CDPtype shifts, SEG-Y gather handling, or production AVO workflow |
| `sffold` | `../src-master/system/seismic/Mfold.c` | bounded numeric header-table 3D fold histogram subset; no SEG-Y key lookup layer or trace-header ecology |
| `sfai2refl` | `../src-master/system/seismic/Mai2refl.c` | bounded one-axis acoustic impedance to reflectivity conversion; no angle-dependent or elastic reflectivity modeling |
| `sfslant` | `../src-master/system/seismic/Mslant.c` with `slant.c` | bounded adjoint linear slant-stack wrapper over the existing direct time-domain Radon pair; no rho filter, anti-alias stretch, `p1=`, modeling direction, or high-resolution Radon |
| `sfvscan` | `../src-master/system/seismic/Mvscan.c` | bounded velocity-panel semblance wrapper over the existing small-gather semblance implementation; no differential/AVO semblance, masks, weighting, slowness/squared velocity, or velocity picking |
| `sfcos2ang` | `../src-master/system/seismic/Mcos2ang.c` | bounded inverse-cosine stack-panel-to-angle linear resampling; no `top=` velocity scaling or ray-parameter model |
| `sfisin2ang` | `../src-master/system/seismic/Misin2ang.c` | bounded inverse-sine stack-panel-to-angle linear resampling; no anisotropic angle transform or ray-parameter model |
| `sfmap2coh` | `../src-master/system/seismic/Mmap2coh.c` | bounded parameter-map accumulation into a velocity/coherence axis; no production coherence or local-similarity workflow |
| `sfcmp2shot` | `../src-master/system/seismic/Mcmp2shot.c` | bounded regular 2D CMP-to-shot trace reorganization; no SEG-Y trace headers or irregular geometry reconstruction |
| `sfshot2cmp` | `../src-master/system/seismic/Mshot2cmp.c` | bounded regular 2D shot-to-CMP trace reorganization with default `half=y`; no mask side output, SEG-Y trace headers, irregular geometry, or streaming pipe semantics |
| `sfintbin` | `../src-master/system/seismic/Mintbin.c` | bounded numeric integer-header trace sorting into a 2D bin grid; no SEG-Y key-name lookup, inverse mode, map/mask outputs, or production binning |
| `sfintbin3` | `../src-master/system/seismic/Mintbin3.c` | bounded numeric integer-header trace sorting into a 3D bin grid; no SEG-Y key-name lookup, mask output, or production 3D survey binning |
| `sfpolymask` | `../src-master/system/generic/Mpolymask.c` | bounded regular 2D point-in-polygon mask from float RSF `poly=` vertex table; no multidimensional masks, polygon repair, plotting, or non-RSF vertex formats |
| `sfgrad2` | `../src-master/system/generic/Mgrad2.c` with `../src-master/api/c/edge.c` | bounded 2D Sobel gradient-squared stencil over each n1,n2 slice; no physical spacing normalization or alternative edge modes |
| `sfgrad3` | `../src-master/system/generic/Mgrad3.c` with `../src-master/api/c/edge.c` | bounded 3D Sobel gradient-squared/component stencil with `dim=0/1/2/3`; no physical spacing normalization or alternative smoothing |
| `sflpad` | `../src-master/system/generic/Mlpad.c` | bounded regular trace/plane interleaving with `jump=` and optional mask output; no streaming pipe semantics or irregular geometry |
| `sfbin` | `../src-master/system/generic/Mbin.c` | table-to-grid mean/sum/count subset; no separate `head=`, fold, median, or interpolation modes |
| `sfslice` | `../src-master/system/generic/Mslice.c` | fixed-index slice subset; upstream uses a picked surface and interpolation |
| `sfmax1` | `../src-master/system/generic/Mmax1.c` | maximum value/index/coordinate subset; upstream emits complex local-maxima picks |
| Localization L0-1/L0-2 primitives | related sources include `../src-master/system/seismic/araytrace.c`, `raytrace.c`, `celltrace3.c`, `Mlineiko.c`, `Mdiffraction.c`, `Mdiffoc.c`, and book traveltime examples under `../src-master/book/geo384w/hw2/cmp/` | pure-Python prototype fixed- and homogeneous variable-velocity travel-time/grid-search helpers; not a command clone and not counted as command coverage |
| `sfautocorr` | `../src-master/user/gee/Mautocorr.c` | trace autocorrelation subset; upstream is a helix-filter autocorrelation tool |
| `sfconvolve` | `../src-master/user/luke/Mconvolve.c` | one-axis two-input convolution subset; upstream is a 2D image kernel tool with adjoint/wrap modes |
| `sfcconv` | `../src-master/user/gee/Mcconv.c` | circular convolution subset; upstream uses complex internal filter/operator parameters |
| `sfenvcorr` | `../src-master/user/nobody/Menvcorr.c` | envelope cross-correlation subset; upstream performs local envelope-correlation inversion |
| `sfshifts` | `../src-master/system/seismic/Mshifts.c` | integer sample-shift subset; upstream performs multiple interpolated shifts/slopes |
| `sfstacks` | `../src-master/system/seismic/Mstacks.c` | statistical stack subset; upstream is constant-velocity NMO stack/scan |
| `sfderiv` | `../src-master/system/generic/Mderiv.c` | arbitrary-axis first finite differences; no maximally linear FIR `order=` |
| `sfcausint` | `../src-master/system/generic/Mcausint.c` | arbitrary-axis forward cumulative integration; no `adj=y` |
| `sfintegral` | `../src-master/user/songxl/Mintegral.c` | arbitrary-axis cumsum/trapezoid subset; not core coverage |
| `sfclip2` | `../src-master/system/generic/Mclip2.c` | explicit and percentile clipping subset; no streaming or complex input |
| `sfmutter` | `../src-master/system/generic/Mmutter.c` | regular-axis linear above/below mute; no offset header, hyperbolic, half-offset, or multi-slope modes |
| `sfdiff` | `../src-master/user/chenyk/Mdiff.c` | scalar sum-square/RMS/max-absolute QC metrics; not core coverage |
| `sfabs` | no standalone program; function in `../src-master/system/main/math.c` | direct convenience subset; not counted as a new upstream command |
| `sfsign` | no standalone program; function in `../src-master/system/main/math.c` | direct convenience subset; not counted as a new upstream command |
| `sfsqrt` | no standalone program; function in `../src-master/system/main/math.c` | direct convenience subset; not counted as a new upstream command |
| `sflog` | no standalone program; function in `../src-master/system/main/math.c` | direct convenience subset; not counted as a new upstream command |
| `sfexp` | no standalone program; function in `../src-master/system/main/math.c` | direct convenience subset; not counted as a new upstream command |
| `sfpow` | `../src-master/system/generic/Mpow.c`, alias also installed as `sftpow` | upstream is coordinate-axis gain and was already counted; Stage C-5 `pow` is an uncounted `sfmath`-style sample-power convenience |
| `sfhistogram` | `../src-master/system/generic/Mhistogram.c` | two-column center/count-or-density table subset; counted in core coverage |
| `sfquantile` | `../src-master/user/ivlad/Mquantile.c` with `../src-master/api/c/quantile.c` | global/axis multi-q RSF subset; counted in full and `user/*` coverage |
| `sfmean` | `../src-master/user/yliu/Mmean.c` | upstream is a 1D sliding-window filter; Stage C-6 global/axis mean is an uncounted convenience |
| `sfrms` | `../src-master/user/luke/Mrms.c` | upstream is a local rectangular RMS attribute; Stage C-6 global/axis RMS is an uncounted convenience |
| `sfvar` | no standalone program; global variance is reported by `../src-master/system/main/attr.c` | uncounted convenience with optional axis and `ddof=` |
| `sfstd` | no standalone program; global standard deviation is reported by `../src-master/system/main/attr.c` | uncounted convenience with optional axis and `ddof=` |
| `sfmedian` | `../src-master/user/fomels/Mmedian.c` | first-axis reduction subset; counted in full and `user/*` coverage |
| `sfrange` | no matching standalone program found | uncounted `[min,max]` convenience |
| `sfisnan` | no matching standalone program found | uncounted finite/non-finite mask convenience |
| `sffillnan` | no matching standalone program found | uncounted non-finite replacement convenience |
| `sfdemean` | no matching standalone program found | uncounted global/axis mean-removal convenience |
| `sfdetrend` | no matching standalone program found | uncounted constant/linear least-squares convenience |
| `sfdecimate` | no matching standalone program found; `system/generic/Mreg2tri.c` only describes triangulation decimation | uncounted integer-axis decimation convenience |
| `sfbandstop` | no matching standalone program found | uncounted zero-phase FFT band-stop convenience |
| `sfnotch` | no matching standalone program found; SEG-Y header words named `nofilf/nofils` are metadata only | uncounted notch convenience |
| `sflocalrms` / `sfrms` | `../src-master/user/luke/Mrms.c` | related single-axis local-RMS convenience with intentionally different window/edge semantics; not counted |
| `windowfunc` | no standalone standard-window generator; `../src-master/system/generic/Mcostaper.c` is an N-D border taper and `system/main/window.c` is data subsetting | uncounted standard-window convenience |
| `psd` | related `../src-master/system/generic/Mspectra.c` emits amplitude spectra | uncounted periodogram density/spectrum convenience |
| `csd` | no matching standalone program found | uncounted cross-periodogram convenience |
| `coherence` | `../src-master/user/chen/Mcoherence.c` computes local spatial coherence cubes, not spectral coherence | uncounted magnitude-squared spectral coherence convenience |
| `spectrogram` | related `../src-master/user/yliu/Mstft.c` and `Mstft2.c` use `sfstft`-style local transforms and different output contracts | uncounted STFT magnitude/power convenience |
| `snr` | related `../src-master/user/yliu/Msnr.c` and other user SNR programs print stack-energy metrics | uncounted explicit-window RMS SNR convenience |
| `welch` | no matching standalone program; `../src-master/system/generic/Mspectra.c` is a single amplitude spectrum and user STFT tools have different contracts | uncounted segment-averaged PSD convenience |
| `welchcsd` | no matching standalone program found | uncounted segment-averaged cross-spectrum convenience |
| `transfer` | no matching standalone H1/H2 response-estimator program found | uncounted frequency-response convenience |
| `whiten` | related `../src-master/user/fomels/Mabalance.c` and `../src-master/user/karl/Mtahspecbal.c` use different envelope/TAH balance models | uncounted phase-preserving whitening convenience |
| `specnorm` | no matching standalone scalar spectral-normalization program found | uncounted unit-RMS/unit-maximum convenience |
| `freqattr` | related `../src-master/user/yliu/Mdominantf.c` prints a weighted frequency centroid only | uncounted dominant/centroid/bandwidth RSF convenience |
| `firwin` | no matching standalone program; window generation and filtering are separate upstream concepts | uncounted windowed-sinc design convenience |
| `firfilter` | related `../src-master/user/chen/Mfir.c` installs as `sfir` and consumes a `fir=` file with integer `o1` delay | uncounted centered same-length FIR convenience |
| `filtfilt` | related `../src-master/system/generic/Mbandpass.c` can apply Butterworth sections forward/reverse when `phase=n` | uncounted generic FIR forward/reverse convenience |
| `freqz` | no matching standalone response-diagnostic program found | uncounted FIR response convenience |
| `bandenergy` | no matching standalone explicit-band energy table program found; `sfspectra` emits amplitude spectra | uncounted energy/power/RMS convenience |
| `filterbank` | related `../src-master/user/chen/Mfbank1.c` and `Mfbank2.c` are interpolation filter banks | uncounted explicit frequency-band FIR bank convenience |

Stage C-4 audit-only decisions:

- `sffold` at `../src-master/system/seismic/Mfold.c` is a SEG-Y trace-header
  3D histogram/foldplot program. It remains unimplemented and is not counted.
- `sfzero` at `../src-master/user/fomels/Mzero.c` detects zero crossings with
  ENO interpolation. It is not a zero-filled-data command and was not used as
  a replacement.

## Next Recommended Work

S1, S2, S3, S4-0, S4-1, S4-2, S4-3, S5, S6-0, S6-1, S6-2, S7-0, I0-0, I0-1,
I0-2, I0-3, I0-4, I0-5, I0-6, I0-8A/I0-8B, I0-9B1/I0-9C, D-2A, L0-1/L0-2,
and F0-1/F0-2 are complete. The next pass should not start by adding a feature command, broad
domain inversion, or production workflow. Recommended follow-ups are either a
bounded localization design pass for pick records/uncertainty/identifiability,
a right-preconditioned LSQR design/implementation pass, or a separate
topic-driven workflow pass with explicit fixtures.

Do not jump directly to high-resolution `sfradon`, solved Radon inversion, or
velocity picking. The seismic v0 harness is useful local infrastructure, and
I0-1 now supplies the first operator algebra/history spine, I0-2 supplies a
small regularization subset, and I0-3 supplies a small problem diagnostics
layer. I0-4 supplies optional diagnostics integration and a source-backed
CGLS/LSQR design; I0-5 supplies bounded unpreconditioned CGLS; I0-6 supplies
only the preconditioner contract. Later Radon, inversion, imaging, and more
complex geophysical workflows still need solver integration and domain
contracts first; I0-9B1 supplies bounded unpreconditioned/regularized LSQR,
while preconditioned LSQR remains separate.

Do not add a feature merely because it is absent. Production non-regular
acquisition geometry, trace-header integration, field-scale data, streaming,
SEG-Y, DAS adapters, new velocity-picking or production velocity-scan workflow,
broad Radon/FK algorithm expansion, production localization, modeling,
production inversion, and imaging remain outside the next pass.

Stage D-1 remains retained without further API, CLI, console-script, or
coverage changes. WSL-1 remains validation infrastructure, not a reason to
count Pythonic conveniences or expand `user/*`. After M3-6, coverage is
`129 / 2114`, core coverage is `116 / 301`, and direct `system/main` coverage is
`37 / 39`; denominators remain unchanged.

Keep hybrid benchmarking evidence-driven and separate. If SEG-Y trace-header
support becomes urgent, handle B-3-3 `sfsegyheader` as its own design task
rather than folding it into ordinary RSF or the minimal header-table subset.
Public release, licensing, and version tagging remain deferred.

Do not jump to C++, large imaging/modeling,
VPlot/SCons/book, or `user/*`.

## Near-Term Non-Goals

- Full Madagascar clone.
- Full `user/*` coverage.
- Full VPlot/pens/vppen compatibility.
- SCons/book documentation system.
- IWAVE/RVL, MPI/CUDA/PETSc stacks.
- Complete SEG-Y trace header ecosystem.
- C++ acceleration without Python fallback, benchmark, and tests.

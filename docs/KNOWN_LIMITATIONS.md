# Known Limitations

This file is intentionally concise. Broader status, compatibility, coverage, and
testing details live in the other current docs.

## Scope

- pymadagascar is not a complete Madagascar clone.
- Full command-surface coverage remains low: `118 / 2114 = 5.58%`.
- Core `system/` + `plot/main` coverage is `105 / 301 = 34.88%`.
- `user/*`, VPlot, SCons/book, IWAVE/RVL, MPI/CUDA/PETSc, and large research
  program families are not near-term targets.
- `PYMADAGASCAR_LEARNING_GUIDE.ipynb` is a concise learning notebook. It
  intentionally compresses parameter, dtype, geometry, and compatibility
  details; the eight Markdown documents remain authoritative.

## Topic Entry Gates

- Stage C ends at C-10. C-11 is not the default next batch; new implementation
  must be justified by a topic fixture or workflow gap.
- The seismic signal/processing topic now has S1/S2/S3/S4-1/S4-3/S6-2 regular
  small-gather contracts, metrics, NMO/Semblance/FK/Radon prototype
  regressions, and an S5 integrated workflow regression. S7-0 closes Seismic
  Topic v0 as a fixture-backed regression harness and recommends pausing the
  seismic topic by default. The topic still leaves non-regular acquisition
  geometry, production velocity analysis, velocity picking, high-resolution
  `sfradon`, field-scale fixtures, and SEG-Y/header integration unresolved.
- Localization has only the L0-1/L0-2 direct-module prototype primitives for
  small homogeneous 2D local-coordinate travel times plus exhaustive x-z
  fixed-velocity and homogeneous variable-velocity point-location grid search.
  It is not a root/stable API, command clone, CLI, automatic picker,
  uncertainty estimator, tomography tool, production locator, or field claim.
  Pick records, uncertainty/quality metadata, identifiability reporting,
  general velocity-model interfaces, and workflow integration remain future
  work.
- Inversion / Operator Foundation I0-1 through I0-6 have added small
  in-memory operator composition, internal/prototype history/result containers,
  a minimal regularization-operator subset, and a direct-module
  least-squares problem/objective/diagnostics layer. I0-4 optionally records
  existing CG/CGNR histories without changing default solver behavior. I0-5
  adds bounded CGLS for small real/complex in-memory problems. I0-6 defines
  identity/diagonal right-preconditioner semantics and diagnostics, and
  I0-8A/I0-8B connect them to the CGLS prototype with explicit latent/model
  metadata. I0-9B1 adds bounded unpreconditioned/regularized LSQR as a
  direct-module prototype. Inversion still lacks preconditioned LSQR, stable
  solver APIs, constraints, production scaling, and domain inversion workflows.
- Forward modeling has the F0-1 regular local-2D model/acquisition geometry
  contract, the F0-2 acquisition-driven single-shot wrapper, the F0-3
  sequential multi-shot survey wrapper, the F0-4 explicit survey tensor
  conversion and summary helpers, F0-5 deterministic synthetic acoustic
  velocity model builders, the F0-6 deterministic geometry-driven validation
  workflow, and the existing acoustic2d finite-difference prototype. The default
  survey record remains list-of-shots; tensor stacking is opt-in, uses
  shot_receiver_time layout, and requires consistent receiver/time axes with no
  padding or interpolation. The velocity builders cover constant, layered,
  rectangular-anomaly, and circular-anomaly small models only; they do not
  provide smoothing, random models, geologic model GUIs, or field model
  construction. The F0-6 workflow provides smoke-level acceptance evidence only;
  it is not an accuracy, convergence, dispersion, boundary, imaging, or
  production validation study. Forward modeling still lacks physical-coordinate
  interpolation, production tensor/padding policy, convergence or dispersion
  evidence, production boundary studies, parallel/cached survey execution, and
  field-scale claims.
- Imaging lacks a shared acquisition model, amplitude/anti-alias treatment,
  adjoint validation, and a reference velocity workflow; implementation is
  deferred.
- DAS remains workflow-first. No HDF5/TDMS/DAT adapter, gauge-length response,
  field-data claim, or D-2 continuation is part of the current route.
- SEG-Y and trace-header work remains independent and deferred until trace
  ownership, scalar/unit semantics, row synchronization, and round-trip
  fixtures are designed.

## Seismic Topic S1 Limits

- S1 fixtures are small deterministic internal/testing arrays, not field-scale
  data, production processing defaults, or public data-model classes.
- Trace and panel fixtures require finite real `float32` or `float64` samples.
  Missing samples, NaN/Inf repair, integer amplitudes, and complex seismic
  acquisition are outside the S1 canonical fixture contract.
- Panels and gathers use regular axis-2 coordinates with positive spacing.
  Non-regular receiver or offset coordinates are not embedded in ordinary RSF
  metadata by S1.
- The gather contract records signed offset only. It does not provide complete
  source/receiver coordinates, CRS, azimuth, elevation, component, fold, or
  acquisition ownership.
- Ordinary RSF metadata is not a SEG-Y trace-header model. S1 does not add
  header tables, synchronized trace headers, `sfsegyheader`, or SEG-Y I/O.
- The S1 demean/detrend/bandpass/AGC/mute/stack/PSD workflow is a deterministic
  regression recipe. It is not a recommended field-processing sequence and
  does not validate production velocity, mute, amplitude, or noise choices.

## Seismic Topic S2 Limits

- S2 metrics and thresholds are calibrated only for the small deterministic S1
  regular signed-offset fixture. They are not field-scale automatic QC or
  production processing acceptance criteria.
- SNR uses explicit fixed sample windows. S2 does not pick signal/noise windows,
  estimate uncertainty, classify events, or adapt thresholds to acquisition
  conditions.
- Frequency metrics use existing periodogram and explicit band-energy
  conveniences. They do not provide confidence intervals, multi-taper
  estimates, statistical significance, or automatic band selection.
- Mute coverage assumes the S1 regular `t0 + abs(offset)/v` geometry. Complex,
  irregular, trace-header-driven, or SEG-Y geometry is not supported.
- The JSON report is an internal regression artifact, not a stable interchange
  schema, regulatory QC record, or production processing report.

## I/O and Data Size

- RSF header + sidecar I/O is the main supported path.
- `ascii_float` support is a small stable subset for float data.
- Not all Madagascar `data_format` combinations are implemented.
- Large out-of-core and streaming workflows are limited; most tools read arrays
  into memory.
- stdin/stdout pipe behavior is basic and not a full clone of upstream `sf*`.

## CLI and Compatibility

- Only 54 commands are registered as `pymada-*` console scripts.
- Other CLI modules must be called with `python -m pymadagascar.cli.<name>`.
- Text output and floating-point details are not byte-identical to Madagascar.
- Optional original Madagascar comparisons skip when upstream commands are not
  installed. WSL `ubuntu2204` is validated, but command availability and
  designed subset semantics still vary across upstream versions.
- Original comparisons validate the documented common subset, not byte-level
  identity. Upstream history keys, singleton-axis retention, text formatting,
  and order-statistic conventions may differ and are handled explicitly in
  focused tests.

## Packaging and Local Outputs

- The distribution name is `pymadagascar-hybrid` while the import package is
  `pymadagascar`.
- The repository does not yet declare a license. Choose one before public
  redistribution or package-index release.
- Optional C++ builds require explicit opt-in, Ninja/pybind11, and a working
  compiler; only the NumPy fallback is part of the current baseline.
- Historical `_tmp_linear_operator_demo` and `examples/_output` directories may
  exist locally. They are ignored legacy output, not release inputs.

## High-Level API

- `RSFData` transforms are in-memory convenience wrappers. `inplace=True`
  replaces the current object's data and header even when an operation removes
  an axis or returns the one-sample `diff` metric.
- Array/list second operands for `convolve`, `cconv`, `envcorr`, and `diff`
  receive minimal synthesized RSF metadata. Use an `RSFData` or RSF path when
  the operand's origin, labels, or other metadata matter.
- The compatibility names documented in the naming guide remain intentionally
  distinct; Q1 did not remove or rename stable APIs.

## Recent Stable Subsets

- `sfcp/sfrm` are safe file-level subsets; `sfrm` requires explicit
  confirmation for deletion.
- `sfmin/sfmax` are script-friendly text-statistic subsets, not full upstream
  `sfstack` alias clones.
- `sfmul/sfdiv` implement simple elementwise math only; `sfdiv` defaults to
  `zero_policy=raise`.
- `sftpow` uses project axis coordinates and has explicit non-positive time
  behavior.
- `sfinterleave` requires matching input shapes except for the interleave axis.
- M0-1 `sfscale` is the scalar `scale=`/`dscale=` subset only; it does not
  implement upstream percentile-driven `pclip`/axis local scaling. `sfrotate`
  implements in-memory `rot#` cyclic axis rotation and preserves headers; it
  does not implement upstream out-of-core random-access behavior.
- M0-2 `sfstack` implements one-axis `axis=`, `mode=mean/sum/rms`, and
  `nonzero=` fold behavior only. It does not implement upstream `axis=0`,
  `scale=` vectors, `min=`, `max=`, `prod=`, program-name aliases, complex RMS,
  or streaming/out-of-core behavior.
- M0-3 `sfpad` implements in-memory constant-value `beg#`/`end#`/`n#` padding
  only. It does not implement streaming/out-of-core native byte copying,
  arbitrary `sfput` command-line passthrough, or non-constant border modes.
  M0-3 `sfspray` implements in-memory new-axis duplication with regular
  metadata only; it does not implement streaming/out-of-core behavior.
- M1-1 `sfclip` implements the `system/generic/Mclip.c` `clip=`/`value=`
  amplitude replacement subset and rejects complex input. `sfnoise` keeps a
  deterministic NumPy RNG contract rather than byte-identical Madagascar random
  streams. `sfboxsmooth` is centered, in-memory, and edge-padded; it does not
  implement streaming/out-of-core behavior.
- M1-2 `sflaplac` implements the real-valued `center - neighbor`
  graph-Laplacian subset only; it does not implement upstream `adj=`,
  coefficient fields, inverse solves, complex input, or streaming.
  `sfsmooth` is the centered triangle subset and does not implement upstream
  `adj=`, `diff#`, per-axis `box#`, complex input, or streaming. `sftrapez`
  is a one-axis real-input RFFT trapezoidal frequency filter and does not
  promise byte-identical upstream FFT rounding.
- M1-3 `sffft1` implements a one-axis real-to-complex RFFT and complex-to-real
  inverse subset only; it does not implement upstream FFTW planning,
  `opt=` padding, `ot=` shift files, `sym=` scaling, or streaming. `sfcosft`
  is a one-axis orthonormal DCT-II/DCT-III subset and does not implement
  upstream multi-axis `sign#` dispatch. `sfspectra2` is an in-memory 2-D
  amplitude/power spectrum subset and does not implement FFTW optimal padding,
  plotting, streaming, or byte-identical FFT rounding. `sffft3` remains
  deferred.
- M1-4 `sfremap1` implements one-axis regular-grid linear remapping only; it
  does not implement ENO orders above 1, `pattern=` files, or streaming.
  `sfspline` is a NumPy-only natural cubic regular-axis subset and does not
  implement irregular coordinate/value tables, endpoint derivative `fp=`, or
  spline prefiltering. `sft2warp` is a one-axis linear-interpolation
  time-squared warp and does not implement adjoint modes, stretch
  regularization, logwarp, or byte-identical `sf_stretch4` behavior.
- M1-5 `sfmatmult` implements real in-memory matrix-vector multiplication
  only; it does not implement complex, sparse, batched, solver, or
  out-of-core behavior. `sfmatch` implements the source symmetric
  zero-boundary loop only and does not implement shaping-filter solvers,
  frequency-domain matching, or streaming. `sflinefit` fits one ordinary
  least-squares line from an `n1=2` table; it does not implement pattern files,
  multi-trace batches, or robust regression. `sfequal`, `sfextract`, and
  complex matrix multiplication remain deferred.
- M2-1 `sfavo` implements a real in-memory AVO intercept/gradient least-squares
  subset over RSF axis 2; it does not implement CDPtype offset shifts,
  irregular SEG-Y gather handling, or a production AVO workflow. `sffold`
  implements only numeric header-table 3D histograms and does not implement
  Madagascar's SEG-Y key lookup layer. `sfai2refl` implements one-axis acoustic
  impedance reflectivity only and does not implement angle-dependent or elastic
  reflectivity modeling. `sffreqint` and `sfc2r` remain deferred.
- M2-2 `sfnmo` implements bounded regular hyperbolic NMO only; it does not
  implement anisotropic NMO, masks, heterogeneous shift/taner parameters,
  full production stretch/mute handling, 3D NMO, or SEG-Y trace-header
  workflows. `sfhalfint` uses a bounded FFT fractional transform and is not
  byte-identical to Madagascar's `sf_halfint` helper. `sfmoveout` generates
  spike traces from a moveout-time table; it is not a generic moveout
  correction, DMO, migration, or imaging command.
- M2-3 `sfcos2ang` and `sfisin2ang` implement bounded stack-panel-to-angle
  linear resampling only; they are not elementwise trigonometric converters
  and do not implement upstream `top=` velocity scaling. `sfmap2coh`
  implements same-shape in-memory parameter-map accumulation into a velocity
  axis; it is not a production coherence, local-similarity, elastic
  reflectivity, migration, DMO, or imaging workflow.
- M2-4 `sfcmp2shot` implements regular 2D CMP-to-shot trace reorganization
  only and does not reconstruct irregular geometry or use SEG-Y trace headers.
  `sfintbin` and `sfintbin3` sort by numeric integer header tables only; they
  do not implement SEG-Y key-name lookup, inverse mode, map/mask side outputs,
  duplicate-trace stacking policy, production binning, reconstruction, DMO,
  migration, or imaging.
- `sfheaderwindow/sfheadercut` are ordinary-RSF mask/header subsets. They do
  not support full header tables or SEG-Y trace headers. `sfheaderwindow`
  requires continuous mask selections.
- `sfheaderattr/sfheadermath/sfheadersort` use a minimal RSF-backed header
  table model with numeric columns, `n1=key count`, `n2=row count`, and key
  names in `key1/key2/...` plus `header_keys=`. They are not full Madagascar
  header table clones.
- `sfheadersort` currently sorts the header table rows only; it does not reorder
  a separate seismic data volume.
- Full trace-header and SEG-Y header-table ecology, including `sfsegyheader`,
  remains outside this subset.
- `sfdottest/sfcdottest` are matrix/identity-backed dot-test subsets. They do
  not run arbitrary external operator commands and do not clone Madagascar's
  pipe-based operator protocol.
- `sfconjgrad/sfcconjgrad` are small in-memory matrix-backed CG subsets for
  SPD/Hermitian systems and normal equations. They do not support
  preconditioners, shaping regularization, streaming, or out-of-core solves.
- `sfcostaper/sfthreshold/sfspectra/sfenvelope` are small in-memory signal
  preprocessing subsets. `sfthreshold` uses explicit `value=` thresholding
  instead of the full upstream pclip ecosystem; `sfspectra` is a simple RFFT
  QC spectrum, not a full spectral-estimation suite; `sfenvelope` computes
  envelope amplitude only and does not implement upstream phase-rotation modes.
- `sflinear/sfbin/sfslice/sfmax1` are small in-memory generic sampling and
  picking subsets. `sflinear` is regular-axis linear resampling, not upstream
  irregular coordinate/value-table interpolation with regularization. `sfbin`
  bins a table-like point RSF to a 2D grid with mean/sum/count only; it is not
  the full upstream header-file/fold/interpolation binning workflow. `sfslice`
  is fixed-index axis slicing, not picked-surface interpolation. `sfmax1`
  returns maximum value/index/coordinate picks, not upstream complex local
  maxima lists with `np=` and `sorted=`.
- Stage C-2 tools do not implement spline/ENO/stretch/remap frameworks,
  pandas-backed tables, streaming, or out-of-core processing.
- `sfautocorr/sfconvolve/sfcconv/sfenvcorr/sfshifts/sfstacks` are small
  in-memory signal correlation and conditioning subsets. They do not implement
  upstream helix-filter autocorrelation, 2D adjoint/wrap convolution,
  complex filter-operator circular convolution, local envelope-correlation
  inversion, interpolated multi-slope shifts, or constant-velocity NMO stack
  scans.
- Stage C-3 tools do not implement full filter/correlation/stacking parameter
  ecosystems, streaming, or out-of-core processing.
- `sfderiv/sfcausint/sfintegral/sfclip2/sfmutter/sfdiff` are small in-memory
  axis-calculus, amplitude-conditioning, and QC subsets. They do not implement
  the upstream FIR derivative order, anti-causal adjoint integration,
  wave-extrapolation-specific integral behavior, external offset/header mute
  geometry, hyperbolic/multi-slope muting, or streaming.
- `sffold` remains unimplemented because upstream is a SEG-Y trace-header 3D
  histogram/foldplot tool. `sfzero` was not used as a zero-filled-data
  replacement because its audited upstream program is an ENO zero-crossing
  detector.
- Stage C-4 does not provide high-order quadrature, trace-header fold maps,
  complex clip2 input, or out-of-core processing.
- Stage C-5 unary CLIs are small direct conveniences. `sfabs`, `sfsign`,
  `sfsqrt`, `sflog`, and `sfexp` are not standalone programs in the audited
  source tree, while this batch's sample-wise `pow` is intentionally different
  from upstream coordinate-axis-gain `sfpow`/`sftpow`.
- `sfhistogram` outputs a two-column float64 center/value table rather than the
  upstream one-dimensional integer grid. `sfquantile` writes one or more
  q-values and optionally replaces an axis, rather than printing one
  `pclip=` value.
- Stage C-5 does not support complex sign/transcendental/power operations,
  weighted quantiles, full histogram parameter ecology, streaming, or
  out-of-core processing. Histogram omits non-finite values; quantile NaNs
  propagate unless explicitly omitted.
- Stage C-6 statistics are real-input, in-memory NumPy reductions. They do not
  implement weighted/grouped estimators, streaming accumulation, or the
  unrelated upstream sliding-window `sfmean` and local-RMS `sfrms` programs.
- `nan_policy=omit` omits NaNs, not infinities. Use `isnan mode=nonfinite` and
  `fillnan mode=nonfinite` to inspect or replace both. Complex statistics are
  rejected; complex masks/filling operate on the whole sample when either
  component is non-finite.
- Stage C-7 tools are in-memory conveniences rather than standalone upstream
  clones. Detrending is constant/linear only; decimation uses a moving-average
  anti-alias option rather than polyphase/designable filtering; band-stop and
  notch are zero-phase FFT tapers rather than IIR filters; local RMS is
  single-axis with clipped boundary windows.
- Stage C-7 does not provide streaming/out-of-core execution, high-order or
  local polynomial detrending, designed FIR/IIR phase controls, or the full
  multidimensional `rect#` and edge behavior of upstream `user/luke/Mrms.c`.
- Stage C-8 spectral tools are in-memory NumPy conveniences. PSD/CSD use a
  single periodogram; coherence uses simple segment averaging; spectrogram is
  limited to RSF axis 1; SNR requires explicit sample windows.
- Stage C-8 does not provide Kaiser/DPSS or arbitrary window families,
  arbitrary-axis STFT, IIR/AR spectral estimation, automatic signal/noise
  picking, streaming, or out-of-core processing. The upstream user
  coherence/STFT/SNR programs have different semantics and are not cloned.
- Stage C-9 Welch/transfer/conditioning/attribute tools are finite real-input,
  in-memory NumPy conveniences. Welch averaging is arithmetic-mean only;
  transfer estimation is limited to stabilized H1/H2; whitening preserves
  phase and uses optional moving-average amplitude smoothing; spectral
  normalization applies one scalar per trace; bandwidth is the power-weighted
  frequency standard deviation.
- Stage C-9 does not provide confidence intervals, median Welch averaging,
  multi-taper or AR spectral estimation, advanced system identification,
  predictive deconvolution, target-spectrum matching, complex input,
  streaming, or out-of-core processing.
- Stage C-10 is a small in-memory FIR toolkit, not a filter-design toolbox. It
  does not provide IIR, Kaiser/remez/equiripple design, polyphase or multirate
  processing, SciPy-compatible filtfilt initial conditions, automatic bands,
  wavelet packets, streaming, or out-of-core execution.

## Prototype Areas

- SEG-Y is a small 2D prototype.
- NMO, Semblance, FK, and Radon are prototypes.
- S3 hardens NMO only for small finite regular CMP-like gathers with RSF axis 1
  as time and axis 2 as signed offset, or with an explicit length-compatible
  finite offset vector. It is not production NMO.
- The NMO prototype still has no velocity scan, no semblance-panel expansion,
  no residual NMO, no anisotropy, no nonhyperbolic moveout, no production
  stretch-mute policy, no source/receiver geometry model, no SEG-Y trace-header
  coupling, no streaming, and no field-scale validation.
- S3 JSON metrics are deterministic fixture-regression reports only. They are
  not field-data acceptance criteria or a public file-format guarantee.
- S4-0 is a source-alignment audit, not an implementation pass. It does not
  make any prototype a Madagascar clone or production-grade tool.
- S4-1 hardens the Semblance prototype only for finite small regular CMP-like
  signed-offset gathers or length-compatible explicit offsets. It validates a
  true-velocity peak on the S1 hyperbolic fixture and records velocity-axis and
  input-offset metadata, but it is not production velocity analysis.
- The current Semblance prototype has only a bounded velocity-panel subset. It
  does not implement full `sfvscan` scan modes, differential/AVO semblance,
  weighting, masks, slowness/squared-velocity modes, production stretch/mute
  policy, production velocity picking, non-regular source/receiver geometry,
  SEG-Y trace headers, streaming, or field-scale velocity analysis.
- S4-2 adds only an internal/testing small-gather geometry contract. Regular
  signed-offset axis metadata, explicit offset vectors, and the minimal
  numeric source/receiver table are deterministic fixture models, not a
  production survey geometry layer.
- The S4-2 minimal source/receiver table is not a SEG-Y trace-header model, not
  `sfsegyheader`, not a field acquisition database, and not synchronized
  data/header reorder support. It has no CRS/scalar policy, no 3D geometry, no
  receiver/source station catalog, no shot/receiver line model, no missing
  coordinate policy beyond finite-value rejection, and no field-scale
  validation.
- S4-3 validates FK only for finite 2D panels with RSF axis 1 as time and axis
  2 as a regular spatial/channel/offset coordinate. Explicit offset vectors,
  irregular geometry, source/receiver tables, and SEG-Y trace headers are not
  consumed by the current FK transform.
- The current FK prototype remains a raw-gather Pythonic fan filter, not a
  full `sfdipfilter` implementation. It does not consume already FK-domain
  input, does not implement `v1/v2/v3/v4` compatibility, angle-mode filtering,
  3D fan filtering, production taper semantics, or field-scale streaming. It
  records `Mdipfilter.c` as the nearest source reference and also records that
  no direct `Mfk.c` generic transform source was found.
- S5 integrates existing small-gather fixtures, metrics, geometry, NMO,
  Semblance, FK, stack, and quicklook outputs into one deterministic workflow
  regression only. It is not a new algorithm, not production velocity analysis,
  not field-scale processing, and not a public report schema.
- S5 still uses the same small regular signed-offset fixture assumptions. It
  does not support non-regular acquisition geometry, automatic velocity
  picking, Radon/slant, production FK filtering, SEG-Y trace headers, DAS
  adapters, localization, inversion, forward modeling, imaging, streaming, or
  C++ kernels.
- S6-0 is a summary and next-route decision only. It recommends Radon/slant
  source-aligned design as the next bounded seismic task, but does not add
  Radon/slant validation, velocity picking, a new workflow, a new API, or any
  implementation.
- The current Radon pair is a small direct time-domain operator prototype.
  S6-2 clarifies that `radon` is the adjoint slant stack `m=A^T d` and
  `iradon` is deterministic modeling `d=A m`. It is not high-resolution
  frequency-domain `sfradon`, does not solve least-squares inversion, and has
  no production sparsity, rho filter, or anti-aliased stretch policy.
- S6-1 audits `../src-master/system/seismic/Mslant.c`, `slant.c`,
  `Mradon.c`, and `radon.c`; S6-2 validates only a small shared slant-stack
  subset with deterministic fixtures. The project still does not implement
  full `sfslant` anti-aliased stretch/rho behavior, reference-slope behavior,
  multi-panel batching, high-resolution `sfradon` frequency-domain Radon
  inversion, Toeplitz solves, spiking/sharpening, production CG inversion, or
  field-scale Radon workflows.
- S7-0 is a closeout and handoff decision only. It does not add S6-3,
  high-resolution `sfradon`, velocity picking, SEG-Y/header work, DAS adapters,
  forward modeling, imaging, or inversion implementation. The recommended next
  topic is Inversion / Operator Foundation because later Radon inversion,
  inversion workflows, and imaging need operator composition, regularization,
  objective/residual history, stopping diagnostics, and preconditioning
  contracts first.
- I0-1 adds only small in-memory scale/sum/composition/vertical-stack operators
  and standalone internal/prototype history/result containers. I0-2 adds only
  a small flattened in-memory regularization subset: diagonal weights,
  first-difference, second-difference, and damping via scaled identity. I0-3
  adds only a small in-memory problem/objective/diagnostics layer for evaluating
  residuals, objective terms, normal-equation gradients, stopping summaries,
  and SolverHistory/SolverResult-compatible records. I0-4 adds only optional
  direct-module CG/CGNR history adapters and CGLS/LSQR design. I0-5 adds only
  bounded unpreconditioned direct-module CGLS. I0-6 adds only the
  right/model-space preconditioner contract; zero diagonal entries, left
  weighting, solver integration, constraints, and masks remain unsupported.
  CG history uses
  linear-system residual energy; CGNR history reports augmented least-squares
  residual/objective values while convergence still uses the normal-equation
  residual. The current B-4/I0 tools
  still do not clone Madagascar's external pipe/tempfile operator protocol, do
  not stream out-of-core, and do not support axis-aware multidimensional
  derivatives, smoothing regularization, total variation, model masks,
  constraints, preconditioned solvers, broad block-operator families, LSQR, or
  domain inversion workflows. CGLS is not a production or out-of-core solver.
- D-1 least-squares recovery remains workflow-only; Radon `least_squares=True`
  remains a reserved rejection path; acoustic2d and Kirchhoff remain forward or
  direct prototypes without reusable adjoint-operator inversion workflows.
- Kirchhoff and acoustic2d are simplified prototypes.
- Plotting is Matplotlib quicklook output, not VPlot compatibility.
- Forward modeling, inversion, and imaging do not yet share a production-ready
  geometry, objective, regularization, or reference-validation framework.
- DAS/engineering usage currently reuses generic RSF/signal/QC tools; dedicated
  HDF5/TDMS/DAT adapters, channel geometry contracts, gauge-length response,
  and chunked processing are not yet implemented.
- The Stage D-1 road-void workflow is a kinematic synthetic model with a direct
  Rayleigh event and a prescribed diffraction travel-time curve. It is not
  elastic-wave forward modeling, does not model fiber coupling or strain-rate
  response, uses simulated picks, and is not a production DAS void-detection
  claim.
- D-1 is retained as a prototype, but D-2 adapters, gauge-length/strain
  response, automatic picking, and uncertainty QC are intentionally not the
  current development route.
- Localization L0-1/L0-2 are kinematic only: they use homogeneous 2D Euclidean
  source-diffractor-receiver paths and brute-force grid objectives. L0-2 can
  estimate one homogeneous velocity with bounded slowness or an explicit
  positive velocity grid, but it does not model amplitudes, waveforms,
  anisotropy, velocity heterogeneity, gauge-length/strain response, source-time
  uncertainty, outliers, covariance, or field-data I/O.
- SEG-Y trace headers must not be conflated with ordinary RSF metadata or the
  minimal numeric header table. `sfsegyheader` remains a separate design task.

## Hybrid

- The C++ extension is not compiled in the current Windows environment.
- NumPy fallback is the supported baseline.
- New hybrid kernels must have Python fallback, tests, benchmark, and precision
  notes before being treated as useful acceleration.

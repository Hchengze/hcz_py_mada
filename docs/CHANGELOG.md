# Changelog

All notable local-baseline changes are recorded here. This project is not a
complete Madagascar clone; it is a Python-friendly RSF/geophysics toolkit with
optional compatibility checks.

## [0.1.0-dev] - Unreleased / local baseline

### Added

- M1-2 continues source-aligned `system/generic` command migration with
  `sflaplac`, `sfsmooth`, and `sftrapez`, aligned to
  `../src-master/system/generic/Mlaplac.c`,
  `../src-master/system/generic/Msmooth.c`, and
  `../src-master/system/generic/Mtrapez.c`. It adds
  `pymadagascar.generic.laplac.laplac_rsf`,
  `pymadagascar.signal.trapez.trapez_rsf`, `pymada-laplac`,
  `pymada-trapez`, and `RSFData.laplac(...)`, `RSFData.smooth(...)`, and
  `RSFData.trapez(...)` without adding new root exports.
- M1-2 command-surface coverage increases the numerator only:
  full coverage is `97 / 2114`, core `system/` + `plot/main` coverage is
  `84 / 301`, and direct `system/main` coverage remains `37 / 39`. Coverage
  denominators are unchanged. No Forward Modeling, DAS/Localization/solver
  branch, large system, notebook, original Madagascar source, tag, release, or
  force-push work is included.
- M1-1 starts source-aligned `system/generic` command batch migration with
  `sfclip`, `sfnoise`, and `sfboxsmooth`, aligned to
  `../src-master/system/generic/Mclip.c`,
  `../src-master/system/generic/Mnoise.c`, and
  `../src-master/system/generic/Mboxsmooth.c`. It registers `pymada-clip`,
  source-aligns `clip_rsf(..., value=...)` non-finite replacement behavior,
  and adds `RSFData.noise(...)` plus `RSFData.boxsmooth(...)` chain methods
  without adding new root exports.
- M1-1 command-surface coverage increases the numerator only:
  full coverage is `94 / 2114`, core `system/` + `plot/main` coverage is
  `81 / 301`, and direct `system/main` coverage remains `37 / 39`. Coverage
  denominators are unchanged. No Forward Modeling, DAS/Localization/solver
  branch, large system, notebook, original Madagascar source, tag, release, or
  force-push work is included.
- M0-3 continues source-aligned direct `system/main` command coverage with
  `sfpad` and `sfspray`, aligned to `../src-master/system/main/pad.c` and
  `../src-master/system/main/spray.c`. It registers `pymada-pad` and
  `pymada-spray`, adds `RSFData.pad(...)` and `RSFData.spray(...)`, and keeps
  the Python APIs at `pymadagascar.generic.pad.pad_rsf` and
  `pymadagascar.generic.spray.spray_rsf` without adding new root exports.
- M0-3 command-surface coverage increases the numerator only:
  full coverage is `91 / 2114`, core `system/` + `plot/main` coverage is
  `78 / 301`, and direct `system/main` coverage is `37 / 39`. Coverage
  denominators are unchanged. No Forward Modeling, DAS/Localization/solver
  branch, large system, notebook, original Madagascar source, tag, release, or
  force-push work is included.
- M0-2 continues source-aligned direct `system/main` command coverage with the
  existing `sfstack` bounded subset aligned to
  `../src-master/system/main/stack.c`. It registers `pymada-stack`, confirms
  the existing `RSFData.stack(...)` chain method, and keeps the Python API at
  `pymadagascar.seismic.stack.stack_rsf` without adding new root/stable
  exports.
- M0-2 command-surface coverage increases the numerator only:
  full coverage is `89 / 2114`, core `system/` + `plot/main` coverage is
  `76 / 301`, and direct `system/main` coverage is `35 / 39`. Coverage
  denominators are unchanged. No Forward Modeling, DAS/Localization/solver
  branch, large system, notebook, original Madagascar source, tag, release, or
  force-push work is included.
- M0-1 resumes source-aligned Madagascar command coverage after pausing further
  Forward Modeling work. It audits only `../src-master/system/main`,
  `../src-master/system/generic`, and `../src-master/system/seismic` for the
  small batch decision, adds a pure NumPy `sfrotate` subset aligned to
  `../src-master/system/main/rotate.c`, and promotes the existing scalar
  `sfscale` subset aligned to `../src-master/system/main/scale.c` to registered
  console-script coverage.
- `pymadagascar.generic.rotate.rotate_rsf`, `RotateError`,
  `RSFData.rotate`, `pymadagascar.cli.rotate`, and `pymada-rotate` provide
  cyclic `rot#` axis rotation. `pymada-scale` is now registered for the
  existing scalar scaling subset. Tests cover API, RSFData, CLI subprocess,
  help smoke, invalid rotations, header preservation, and optional upstream
  `sfrotate` comparison when available.
- M0-1 command-surface coverage increases the numerator only:
  full coverage is `88 / 2114`, core `system/` + `plot/main` coverage is
  `75 / 301`, and direct `system/main` coverage is `34 / 39`. Coverage
  denominators are unchanged. No Forward Modeling, DAS/Localization/solver
  branch, large system, notebook, original Madagascar source, tag, release, or
  force-push work is included.
- Forward Modeling Topic F0-6 geometry-driven acoustic modeling validation
  workflow:
  examples/my_workflows/acoustic_modeling_validation_workflow.py connects
  AcousticModelGrid2D, synthetic velocity model builders, PointSource2D /
  ReceiverArray2D / AcousticAcquisition2D, run_acoustic2d_survey,
  summarize_acoustic_survey, and acoustic_survey_to_tensor into a deterministic
  smoke-level validation report. The workflow writes a JSON-safe/path-free
  summary with grid, velocity-model, acquisition, survey, tensor, and acceptance
  metrics.
- tests/test_acoustic_modeling_validation_workflow.py covers subprocess
  execution, JSON schema, velocity/survey/tensor summaries, all-true acceptance
  flags, path-free metadata, and no repository pollution. F0-6 adds no new
  wave-equation solver, interpolation, padding, imaging, CLI, root/stable API,
  command coverage, or coverage denominator change.
- Forward Modeling Topic F0-5 synthetic acoustic velocity model builders:
  pymadagascar.modeling.models adds AcousticVelocityModel2D,
  constant_velocity_model_2d, layered_velocity_model_2d,
  add_rectangular_velocity_anomaly_2d, add_circular_velocity_anomaly_2d, and
  velocity_model_summary. The builders produce positive finite velocity arrays
  shaped (nx, nz) for AcousticModelGrid2D, preserve the local_2d_x_z
  convention, and provide JSON-safe/path-free metadata for constant, layered,
  rectangular-anomaly, and circular-anomaly synthetic models.
- tests/test_modeling_velocity_models_contract.py covers model shape/value
  contracts, z_top layer ordering, inclusive physical-coordinate anomaly masks,
  copy/no-in-place behavior, final positive-velocity validation, JSON-safe
  metadata, modeling-topic exports, and unchanged root/stable API boundaries.
  F0-5 adds no new wave-equation solver, smoothing, random model, geologic GUI,
  CLI, root/stable API, command coverage, or coverage denominator change.
- Forward Modeling Topic F0-4 acoustic survey tensor helpers:
  pymadagascar.modeling.shot adds AcousticSurveyTensor2D,
  acoustic_survey_to_tensor, and summarize_acoustic_survey. The default
  AcousticSurveyRecord2D contract remains a list of AcousticShotRecord2D
  objects; tensor stacking is explicit only, uses shot_receiver_time layout
  with shape (shot, receiver, time), and requires consistent receiver counts
  plus matching time axes.
- tests/test_acoustic2d_survey_contract.py now covers explicit tensor
  conversion, tensor coordinate/time metadata, copy behavior, variable
  receiver-count rejection, stackability summaries, JSON-safe/path-free
  metadata, modeling-topic exports, and unchanged root/stable API boundaries.
  F0-4 adds no new wave-equation solver, padding, interpolation, parallelism,
  cache, CLI, root/stable API, command coverage, or coverage denominator
  change.
- Forward Modeling Topic F0-3 multi-shot acoustic survey wrapper:
  pymadagascar.modeling.shot adds AcousticSurveyRecord2D and
  run_acoustic2d_survey, a pure-Python topic-level wrapper that accepts a
  non-empty input-ordered sequence of AcousticAcquisition2D objects, reuses
  run_acoustic2d_shot for each shot, and returns a list of AcousticShotRecord2D
  records plus JSON-safe path-free survey metadata documenting shot count,
  receiver counts per shot, input-order semantics, no parallel execution, no
  cache, and no committed survey tensor layout.
- tests/test_acoustic2d_survey_contract.py covers multi-shot execution, shot
  order, per-shot data shapes, JSON-safe/path-free metadata, empty/invalid
  acquisition rejection, velocity-shape rejection, modeling-topic exports, and
  unchanged root/stable API boundaries. F0-3 adds no new wave-equation solver,
  parallelism, cache, source/receiver interpolation, CLI, root/stable API,
  command coverage, or coverage denominator change.
- Forward Modeling Topic F0-2 acquisition-driven acoustic shot wrapper:
  pymadagascar.modeling.shot adds AcousticShotRecord2D and
  run_acoustic2d_shot, a pure-Python topic-level wrapper that accepts a NumPy
  velocity model, AcousticModelGrid2D, and AcousticAcquisition2D, converts
  physical source/receiver coordinates to the existing acoustic2d integer
  indices, calls the unchanged acoustic2d_forward numerical core through
  temporary RSF inputs, and returns a receiver-time shot record with a time
  axis, source/receiver coordinates, and JSON-safe path-free metadata.
- tests/test_acoustic2d_shot_contract.py covers geometry-driven shot
  execution, output shape/time-axis contracts, acquisition coordinate
  preservation, metadata boundaries, velocity-shape and out-of-bounds
  rejection, modeling-topic exports, and unchanged root/stable API boundaries.
  F0-2 adds no new wave-equation solver, multi-shot survey loop,
  source/receiver interpolation, CLI, root/stable API, command coverage, or
  coverage denominator change.
- Forward Modeling Topic F0-1 geometry contract:
  `pymadagascar.modeling.geometry` adds pure-Python topic-level helpers for
  regular 2D acoustic model grids, point sources, receiver arrays, regular
  receiver lines, acoustic acquisition metadata, and conversion to the existing
  `acoustic2d_forward` integer-index signature. The contract documents the
  current acoustic2d convention (`x,z` coordinates, velocity arrays shaped
  `(nx, nz)`, RSF `n1=z,n2=x`, and `(x_index,z_index)` source/receiver
  samples) without changing the finite-difference numerical core.
- `tests/test_modeling_geometry_contract.py` covers grid validation,
  coordinate/index conversion, out-of-bounds rejection, source/receiver
  index conversion, receiver-line generation, JSON-safe/path-free metadata,
  modeling-topic exports, and unchanged root/stable API boundaries. F0-1 adds
  no new wave-equation solver, multi-shot simulation, interpolation, CLI,
  root/stable API, command coverage, or coverage denominator change.
- DAS workflow D-2B integration: `das_void_diffraction_workflow.py` now routes
  its kinematic diffraction curve and variable-velocity grid-search inversion
  through `pymadagascar.localization.traveltime` instead of keeping the core
  localization math only in workflow-private helpers. The output JSON records
  `localization_algorithm` metadata for
  `grid_search_point_location_velocity_2d`, closed-form slowness velocity mode,
  and observed-minus-predicted residuals. D-2B remains workflow-only and adds no
  DAS file adapter, real-data reader, automatic picking, gauge response, CLI,
  root/stable API, command coverage, or coverage denominator change.
- `tests/test_das_void_diffraction_workflow.py` now verifies the workflow
  calls the package-level localization grid-search, preserves the D-2A
  `das_geometry` JSON contract, records JSON-safe localization metadata, and
  keeps synthetic `void_x`, `void_depth`, and velocity recovery within the
  existing tolerances.
- Localization Topic L0-2 variable-velocity grid-search prototype:
  `grid_search_point_location_velocity_2d` and
  `VariableVelocityLocalizationGridSearchResult` extend
  `pymadagascar.localization.traveltime` for finite small 2D
  source-diffractor-receiver localization when homogeneous velocity is unknown.
  The prototype supports bounded closed-form slowness estimation or explicit
  positive velocity-grid search, returns 2D objective and selected-velocity
  grids, and keeps the observed-minus-predicted residual convention.
- `tests/test_localization_traveltime_contract.py` now covers L0-2 known
  x/z/velocity recovery, weighted objectives, bounds clipping, explicit
  velocity-grid mode, JSON-safe metadata, invalid velocity modes, shape
  mismatches, invalid weights, and root/API export boundaries. L0-2 adds no
  CLI, root/stable API, automatic picking, real-data reader, uncertainty,
  imaging, field-performance claim, command coverage, or coverage denominator
  change.
- Localization Topic L0-1 travel-time/grid-search prototype:
  `pymadagascar.localization.traveltime` adds finite small 2D local-coordinate
  helpers for Euclidean distance, direct homogeneous travel time,
  source-diffractor-receiver kinematic diffraction travel time,
  observed-minus-predicted residuals with optional positive weights, and
  deterministic x-z grid-search point localization.
- `tests/test_localization_traveltime_contract.py` covers hand-calculated
  direct/diffraction travel times, multi-receiver shapes, finite/positive input
  validation, residual convention, weighted objectives, known-diffractor grid
  recovery, JSON-safe metadata, and root/API export boundaries. L0-1 adds no
  CLI, root/stable API, automatic picking, real-data reader, uncertainty,
  imaging, field-performance claim, command coverage, or coverage denominator
  change.
- Inversion / Operator Foundation I0-9C LSQR learning/example closure:
  `examples/my_workflows/lsqr_minimal_example.py` demonstrates the bounded
  direct-module LSQR prototype against dense least squares, `LeastSquaresProblem`
  usage, regularization, and model-space `x0` shifted-residual semantics without
  writing files or calling a CLI.
- `docs/PYMADAGASCAR_LEARNING_GUIDE.ipynb` now includes a small CGLS/LSQR
  learning section covering least squares, augmented regularization, current
  CGLS preconditioning support, current unpreconditioned LSQR boundaries, and
  why preconditioned LSQR remains deferred. I0-9C adds no solver implementation
  change, CLI, root/stable API export, command coverage, or coverage denominator
  change.
- Inversion / Operator Foundation I0-9B1 bounded LSQR prototype:
  direct-module `run_lsqr` and `run_lsqr_problem` for small deterministic
  unpreconditioned least-squares problems, including regularized
  `LeastSquaresProblem` objects through the existing augmented-system path and
  nonzero model-space `x0` through a shifted residual correction solve.
- `tests/test_lsqr_contract.py` covers dense references, regularization,
  nonzero `x0`, complex smoke behavior, metadata/history fields, invalid
  inputs, explicit preconditioner rejection, and direct-module export
  boundaries. I0-9B1 adds no CLI, root/stable API, preconditioned LSQR, left
  weighting, command coverage, or coverage denominator change.
- Documentation Baseline D0-1: `docs/PYMADAGASCAR_LEARNING_GUIDE.ipynb` as
  the study-oriented notebook replacing the former XMind visual index, plus
  `tools/check_learning_notebook.py` for lightweight static validation.
- Risk-based testing policy in `docs/TESTING_AND_ENVIRONMENT.md`, requiring
  targeted/affected tests for small low-risk changes and full testing for
  cross-cutting, tooling, release, or phase-closeout changes.
- Inversion / Operator Foundation I0-8A/I0-8B prototype integration: optional
  right/model-space preconditioner support for `run_cgls` and
  `run_cgls_problem`, preserving default unpreconditioned behavior while
  returning model-space solutions and diagnostics; I0-8B makes latent
  convergence residuals, model-space gradients, and preconditioner diagnostics
  explicit in solver metadata/history.
- Inversion / Operator Foundation I0-6 direct-module right/model-space
  preconditioner contract: `Preconditioner`, `IdentityPreconditioner`,
  `DiagonalPreconditioner`, `PreconditionerDiagnostics`, and
  `as_preconditioner`. This was introduced as contract/design infrastructure;
  I0-8A later connects it to the CGLS prototype only, not CGNR or LSQR.
- `tests/test_preconditioner_contract.py` with 13 deterministic contract tests.
- Inversion / Operator Foundation I0-5 bounded unpreconditioned CGLS:
  direct-module `run_cgls` and `run_cgls_problem` for small real/complex
  in-memory least-squares problems, reusing `LeastSquaresProblem`,
  `StackedOperator`, existing regularization operators, `SolverHistory`, and
  `SolverResult`.
- `tests/test_cgls_contract.py` with 18 deterministic solver contract tests.
- Mindmap Documentation Pass M1 previously introduced a visual feature map
  through Stage C-10; D0-1 supersedes that artifact with the learning notebook
  and static notebook validation while preserving the historical record.
- RSF header + sidecar I/O with native binary support.
- `ascii_float` text sidecar subset for 1D/2D/3D float RSF data.
- `key=value` CLI parameter handling and stable `par=file` subset.
- `Axis`, `Hypercube`, and `RSFParams` core metadata helpers.
- 134 `pymadagascar.cli` modules and 25 stable `pymada-*` console_scripts.
- CLI inventory documentation and subprocess smoke coverage.
- Optional original Madagascar comparison test infrastructure.
- Generic foundation commands: spike, math, window, info/get/disfil/attr/put,
  cat/transp/reshape, dd, complex tools, array math, pad/spray/tile, noise.
- Byte scaling Python substitute, plus mask/cut/reverse generic array tools.
- Signal foundation commands: FFT/IFFT/RFFT/IRFFT, bandpass/lowpass/highpass,
  convolution/correlation/xcorr, Ricker wavelet, smooth/boxsmooth.
- Basic seismic processing: gain, AGC, mute, stack.
- Prototype modules for SEG-Y 2D, NMO/Semblance, FK/Radon, Kirchhoff migration,
  and acoustic2d modeling.
- `RSFData` high-level Pythonic convenience wrapper.
- Workflow examples under `examples/my_workflows/`.
- Optional hybrid wrappers with NumPy fallback for array add/scale and batch
  cross-correlation.
- Stage 0 master handoff and Stage A release checklist.
- Release consistency tools: `tools/check_release.py`,
  `tools/check_cli_inventory.py`, and `tools/check_docs_commands.py`.
- Quality Pass Q1 examples inventory tool:
  `tools/check_examples_inventory.py`.
- Stage B-1 small utility batch: safe `sfcp` subset, safe `sfrm` subset, and
  script-friendly `sfmin/sfmax` statistic subsets.
- Module-only CLIs for `cp`, `rm`, `min`, and `max`.
- Stage B-2 array batch: `sfmul`, `sfdiv`, `sftpow`, and `sfinterleave`
  stable Python subsets.
- Module-only CLIs for `mul`, `div`, `tpow`, and `interleave`.
- Stage B-3-1 header/metadata batch: `sfheaderwindow` and `sfheadercut`
  Python mask/header subsets for ordinary RSF files.
- Module-only CLIs for `headerwindow` and `headercut`.
- Stage B-3-2 header table batch: minimal RSF-backed header table model plus
  `sfheaderattr`, `sfheadermath`, and `sfheadersort` Python subsets.
- Module-only CLIs for `headerattr`, `headermath`, and `headersort`.
- Stage B-4 linear-operator batch: minimal pure-Python `LinearOperator`,
  `MatrixOperator`, `CallableLinearOperator`, dot-test helpers, and
  conjugate-gradient solvers.
- Module-only CLIs for `dottest`, `cdottest`, `conjgrad`, and `cconjgrad`.
- Stage C-1 signal/preprocessing batch: `sfcostaper`, `sfthreshold`,
  `sfspectra`, and `sfenvelope` Python subsets.
- Module-only CLIs for `costaper`, `threshold`, `spectra`, and `envelope`.
- RSFData convenience methods for `costaper`, `threshold`, `spectra`, and
  `envelope`.
- Stage C-2 generic/sampling batch: `sflinear`, `sfbin`, `sfslice`, and
  `sfmax1` Python subsets.
- Module-only CLIs for `linear`, `bin`, `slice`, and `max1`.
- RSFData convenience methods for `linear`, `slice`, and `max1`.
- Stage C-3 signal/correlation batch: `sfautocorr`, `sfconvolve`, `sfcconv`,
  `sfenvcorr`, `sfshifts`, and `sfstacks` Python subsets.
- Module-only CLIs for `autocorr`, `convolve`, `cconv`, `envcorr`, `shifts`,
  and `stacks`.
- RSFData convenience methods for `autocorr`, `convolve`, `cconv`, `envcorr`,
  `shifts`, and `stacks`.
- Stage C-4 axis-calculus/amplitude-conditioning/QC batch: `sfderiv`,
  `sfcausint`, `sfintegral`, `sfclip2`, `sfmutter`, and `sfdiff` Python
  subsets.
- Module-only CLIs for `deriv`, `causint`, `integral`, `clip2`, `mutter`, and
  `diff`.
- RSFData convenience methods for `deriv`, `causint`, `integral`, `clip2`,
  `mutter`, and `diff`.
- Stage C-4 workflow examples for axis calculus/amplitude conditioning and
  seismic gather QC.
- Quality Pass Q1 consistency coverage for RSFData contracts and all 28
  top-level examples.
- Stage C-5 unary/distribution-QC batch: shared `absolute`, `sign`, `sqrt`,
  `log`, `exp`, `power`, `histogram`, and `quantile` APIs plus RSF wrappers.
- Module-only CLIs for `abs`, `sign`, `sqrt`, `log`, `exp`, `pow`,
  `histogram`, and `quantile`.
- RSFData convenience methods for all eight Stage C-5 operations and
  `examples/unary_distribution_qc_demo.py`.
- Stage C-6 robust-statistics/non-finite-QC batch: shared `mean`, `rms`,
  `variance`, `std`, `median`, `range_stats`, `isnan_mask`, `finite_mask`, and
  `fillnan` APIs plus RSF wrappers.
- Module-only CLIs for `mean`, `rms`, `var`, `std`, `median`, `range`, `isnan`,
  and `fillnan`; RSFData methods for the same operations, with
  `range_stats()` as the unambiguous chain name.
- `examples/robust_statistics_nan_qc_demo.py`.
- Roadmap Reassessment R1 topic capability matrix covering general RSF,
  math/QC, signal, seismic, modeling, inversion, imaging, DAS/engineering,
  SEG-Y/header, and plotting areas.
- Ranked next-route assessment for workflow-first DAS/engineering work,
  signal/seismic development, targeted Stage C-7 utilities, inversion,
  SEG-Y/header design, and deferred forward/imaging expansion.
- Stage D-1 DAS engineering skeleton:
  `examples/my_workflows/das_void_diffraction_workflow.py`.
- The D-1 workflow generates direct Rayleigh and road-void diffraction events,
  applies the existing FK prototype, writes RSF/PNG/pick/JSON outputs, and
  performs a workflow-only variable-projection least-squares inversion.
- Stage D-2A adds a workflow-only DAS geometry metadata contract to the D-1
  JSON output. The new `das_geometry` object records regular-linear local-2D
  channel geometry, units, fiber orientation, synthetic source/void positions,
  sample timing, receiver-coordinate convention, and explicit
  `gauge_length_status: not_modeled`.
- `tests/test_das_void_diffraction_workflow.py` for travel-time/inversion
  recovery, subprocess execution, output/header checks, geometry metadata
  fields, JSON safety, local-path absence, and repository output isolation.
- D-2A adds no DAS HDF5/TDMS/DAT adapter, field fixture, automatic picking,
  gauge response, stable API, CLI, command coverage, or field-performance
  claim.
- Stage C-7 signal/small-gather QC foundation: shared `demean`, `detrend`,
  `decimate`, `bandstop`, `notch`, and `local_rms` NumPy APIs with file-backed
  RSF wrappers.
- Module-only CLIs for `demean`, `detrend`, `decimate`, `bandstop`, `notch`,
  and `localrms`; corresponding RSFData methods; and
  `examples/signal_qc_foundation_demo.py`.
- Stage C-8 spectral-QC foundation: standard window generation/application,
  periodogram PSD/CSD, short-segment magnitude-squared coherence, axis-1
  spectrogram magnitude/power, and explicit-window RMS SNR APIs and RSF
  wrappers.
- Module-only CLIs for `windowfunc`, `psd`, `csd`, `coherence`,
  `spectrogram`, and `snr`; corresponding RSFData methods; and
  `examples/spectral_qc_demo.py`.
- Stage C-9 spectral averaging and attributes: Welch PSD/CSD, H1/H2 transfer
  estimates, phase-preserving whitening, unit-RMS/unit-maximum spectral
  normalization, and dominant/centroid/bandwidth frequency attributes.
- Module-only CLIs for `welch`, `welchcsd`, `transfer`, `whiten`, `specnorm`,
  and `freqattr`; corresponding RSFData methods; and
  `examples/spectral_averaging_attributes_demo.py`.
- Stage C-10 FIR/filter-design foundation: windowed-sinc low/high/band-pass
  and band-stop design, centered FIR filtering, forward/reverse FIR filtering,
  FIR response diagnostics, explicit band energy, and a small filter bank.
- Module-only CLIs for `firwin`, `firfilter`, `filtfilt`, `freqz`,
  `bandenergy`, and `filterbank`; RSFData methods for filtering and band QC;
  and `examples/fir_filter_design_demo.py`.
- WSL-1 comparison infrastructure: binary-safe original Madagascar command
  execution with explicit stdin/stdout paths, opt-in text decoding, local
  DATAPATH sidecars, structured parameters, and readable command failures.
- `tests/test_wsl_probe.py` for WSL output parsing, shell selection, base64
  script transport, and strict/non-strict behavior.
- Release Quality Pass Q2 package metadata coverage:
  `tests/test_package_metadata.py` and `tests/test_cli_entrypoints.py`.
- Root `README.md`, public `pymadagascar.__version__`, optional `cpp` build
  extra, and repository output/cache ignore policy.
- Topic Architecture Pass T1: a repository-backed ten-topic architecture
  decision covering current capability, maturity, entry gates, data contracts,
  geometry contracts, validation contracts, first batches, non-goals, and
  documentation ownership.
- Seismic Topic S1 internal/testing fixture module with deterministic mixed
  traces, coherent regular panels, Ricker events, plane-wave panels, and
  regular signed-offset hyperbolic gathers.
- `tests/test_seismic_signal_contracts.py` and
  `examples/my_workflows/seismic_signal_contract_workflow.py` for the S1
  contract and existing-API pipeline regression.
- Seismic Topic S2 internal/testing metrics helper for trace, panel, and
  regular-gather pipeline RMS, SNR, frequency-band, mute, stack, finite-value,
  and header-axis checks.
- `tests/test_seismic_signal_metrics.py` and
  `examples/my_workflows/seismic_signal_metrics_workflow.py` for deterministic
  S2 QC reports and regression thresholds.
- Seismic Topic S3 hardening for the existing NMO prototype: finite-input,
  positive-velocity, time-axis, regular/explicit-offset, `h0`, and `stretch`
  validation plus deterministic prototype metadata preservation.
- `tests/test_seismic_nmo_contract.py` and
  `examples/my_workflows/seismic_nmo_contract_workflow.py` for S1/S2-backed NMO
  flattening, correct-vs-wrong velocity, stack, finite-value, header-axis, CLI,
  JSON report, default-temp, and output-isolation regression.
- Seismic Topic S4-0 documentation-only source-alignment audit for existing
  NMO, Semblance, FK/FK-filter, and Radon prototypes against located
  Madagascar sources under `../src-master`.
- S4-0 bounded-task selection: the next recommended pass is Semblance prototype
  contract hardening with S1/S2/S3 fixtures, not a new command, broad velocity
  analysis feature, Radon/FK expansion, or production workflow.
- Seismic Topic S4-1 Semblance prototype contract hardening against
  `../src-master/system/seismic/Mvscan.c`, including finite-input, velocity
  axis, time-axis, regular/explicit-offset, `h0`, `stretch`, and `smooth`
  validation plus output velocity-panel metadata and input-offset provenance.
- `tests/test_seismic_semblance_contract.py` and
  `examples/my_workflows/seismic_semblance_contract_workflow.py` for S1/S2/S3-
  backed Semblance true-velocity peak, wrong-velocity contrast, stack
  comparison, header-axis, CLI, JSON report, default-temp, and output-isolation
  regression.
- Seismic Topic S4-2 internal/testing small-gather geometry contract helper
  `pymadagascar.testing.seismic_geometry` for regular signed-offset RSF axes,
  explicit offset vectors, and deterministic minimal source/receiver tables.
- `tests/test_seismic_geometry_contract.py` and
  `examples/my_workflows/seismic_geometry_contract_workflow.py` for S4-2
  geometry source-boundary audit, offset-vector/table validation, path-free
  JSON, default-temp, and output-isolation regression.
- Seismic Topic S4-3 FK prototype source-aligned validation against the absence
  of a direct `Mfk.c` and the nearest
  `../src-master/system/generic/Mdipfilter.c` dip/f-k/fan-filter reference,
  including finite-input, axis-sampling, parameter, and source-reference
  metadata hardening.
- `tests/test_seismic_fk_contract.py` and
  `examples/my_workflows/seismic_fk_contract_workflow.py` for S4-3 analytic
  plane-wave FK peak validation, positive/negative slope separation,
  target/reject apparent-velocity fan-filter checks, path-free JSON,
  default-temp, and output-isolation regression.
- Seismic Topic S5 integrated small-gather workflow v0:
  `examples/my_workflows/seismic_small_gather_processing_workflow.py`, combining
  existing S1/S2/S3/S4 fixture, metrics, geometry, NMO, Semblance, FK, stack,
  quicklook, and path-free JSON-report contracts.
- `tests/test_seismic_integrated_workflow.py` for S5 workflow report fields,
  RSF/PNG/JSON outputs, geometry checks, NMO true-vs-wrong behavior, Semblance
  peak behavior, FK finite/header/energy checks, stack ratios, default-temp
  output, repository-output isolation, and no original-Madagascar/C++ dependency.
- Seismic Topic S6-0 documentation-only v0 summary and next-route decision,
  recording the current S1-S5 small-gather capability, remaining limitations,
  route ranking, XMind decision, and recommendation to do Radon/slant
  source-aligned design before any implementation or velocity-picking work.
- Seismic Topic S6-1 documentation-only Radon/slant source-aligned design,
  auditing the current Python direct time-domain Radon forward/adjoint
  prototype against `../src-master/system/seismic/Mslant.c`, `slant.c`,
  `Mradon.c`, and `radon.c`.
- S6-1 route decision: keep the current Python Radon pair as a distinct
  prototype, do the next bounded implementation as small `sfslant`-style
  slant-stack contract hardening/validation if seismic work continues, and
  defer high-resolution `sfradon` inversion design until operator/inversion
  foundations are ready.
- Seismic Topic S6-2 small slant-stack contract hardening for the existing
  Radon/slant prototype: finite data/model checks, positive finite time/offset
  axis checks, finite regularly sampled p/slowness-axis validation,
  length-compatible explicit offset checks, clearer `radon` / `iradon`
  operator-direction metadata, and explicit `not_sfradon` boundary metadata.
- `tests/test_seismic_slant_stack_contract.py` for S6-2 Madagascar
  `Mslant.c`/`slant.c` source-boundary audit, dot-test consistency, analytic
  true-slope focusing, wrong-slope contrast, modeling predictability,
  regular/explicit offset equivalence, shape/header/finiteness invariants,
  negative axis/p/finite/offset cases, existing CLI execution, workflow
  default-temp behavior, output isolation, and no original-Madagascar/C++
  dependency.
- `examples/my_workflows/seismic_slant_stack_contract_workflow.py` for an S6-2
  deterministic slant-stack regression with analytic gather/model RSFs, slant
  panel RSF, modeled gather RSF, quicklook PNG, and path-free internal JSON
  report.
- Seismic Topic S7-0 documentation-only closeout and handoff, recording
  Seismic Topic v0 as a fixture-backed small-gather regression harness and
  selecting Inversion / Operator Foundation as the next recommended topic.
- Inversion / Operator Foundation I0-0 documentation-only current capability
  audit and contract design, recording the existing B-4 operator/dot-test/CG
  subset, Radon forward/adjoint pair, D-1 workflow-only least-squares helper,
  acoustic2d/Kirchhoff boundaries, Madagascar dottest/conjgrad source
  references, initial data/operator/solver contracts, and the next bounded
  route of operator composition plus history contracts.
- Inversion / Operator Foundation I0-1 small in-memory operator composition:
  `ScaledOperator`, `SumOperator`, `ComposedOperator`, and `StackedOperator`
  in `pymadagascar.generic.linear_operator`.
- I0-1 internal/prototype solver diagnostics containers:
  `SolverIterationRecord`, `SolverHistory`, and `SolverResult` with
  deterministic JSON-serializable summaries.
- `tests/test_operator_composition_contract.py` and
  `tests/test_solver_history_contract.py` for I0-1 composition, dot-test,
  finite-value, export-boundary, JSON-summary, and backward-compatibility
  coverage.
- Inversion / Operator Foundation I0-2 small in-memory regularization
  operators: `DiagonalRegularization`, `FirstDifferenceRegularization`, and
  `SecondDifferenceRegularization` in
  `pymadagascar.generic.linear_operator`; damping regularization reuses
  `ScaledOperator` plus `IdentityOperator`.
- `tests/test_regularization_operator_contract.py` for I0-2 regularization
  forward/adjoint behavior, real and complex dot tests, valid-boundary
  difference stencils, finite-value rejection, stacked `[A; lambda L]`
  readiness, composition compatibility, export boundaries, and no CLI
  addition.
- Inversion / Operator Foundation I0-3 small in-memory objective/residual/
  diagnostics problem layer: `LeastSquaresProblem`, `ObjectiveDiagnostics`, and
  `StoppingDiagnostics` in `pymadagascar.generic.linear_operator`.
- `tests/test_inversion_problem_contract.py` and
  `tests/test_objective_diagnostics_contract.py` for I0-3 unregularized and
  regularized residuals, objective terms, stacked residual consistency,
  normal-equation gradients, real/complex behavior, diagnostics summaries,
  SolverHistory/SolverResult compatibility, export boundaries, and no CLI
  addition.
- Inversion / Operator Foundation I0-4 optional solver diagnostics adapters:
  `run_cg_with_history` records linear-system CG residual energy, while
  `run_cgnr_with_history` records I0-3 augmented least-squares residual,
  objective, gradient, and normal-equation stopping metadata. Both reuse the
  existing CG iteration core and support real/complex operators.
- `tests/test_solver_history_integration.py` and
  `tests/test_cgls_lsqr_design_contract.py` for unchanged default solver
  contracts, optional histories, stopping reasons, invalid-state capture,
  JSON summaries, CGNR/problem consistency, source-audit paths, CGLS/LSQR
  design, export boundaries, and explicit CGLS/LSQR non-implementation.
- Header/metadata design document, now archived after the docs slimming pass.
- Documentation slimming pass with current authority docs:
  `README.md`, `PROJECT_STATUS.md`, `USER_GUIDE.md`,
  `API_AND_COMPATIBILITY.md`, `COVERAGE_AND_ROADMAP.md`,
  `TESTING_AND_ENVIRONMENT.md`, and a shortened `KNOWN_LIMITATIONS.md`.
- Stage B batch plan, now summarized in `docs/COVERAGE_AND_ROADMAP.md`.

### Changed

- Release-light checks now validate the learning notebook with
  `tools/check_learning_notebook.py` instead of validating a frozen XMind
  workbook. The notebook is not executed by release tooling and is not a
  coverage authority.
- The automatic Stage C small-batch sequence now ends at C-10; C-11 is not
  recommended. Seismic data signal analysis and processing is the first topic,
  beginning with contracts and fixtures rather than new commands.
- DAS remains workflow-first without D-2 or adapters. Localization and forward
  modeling are design-only, inversion is limited to operator/regularization/
  objective foundations, and imaging plus SEG-Y/header expansion are deferred.
- T1 changes only the eight authority Markdown files. It does not change
  features, CLI modules, console scripts, stable APIs, coverage, examples,
  tests, or the XMind artifact.
- S1 starts the first topic without adding feature commands, CLI modules,
  console scripts, stable public APIs, or command-surface coverage. Its fixture
  helpers remain under `pymadagascar.testing` and are not re-exported.
- S2 adds no feature command, CLI module, console script, stable public API, or
  command-surface coverage. Its metrics helper and JSON report remain internal
  testing/workflow contracts, and no NMO/FK/Radon/prototype maturity changes.
- S3 adds no feature command, CLI module, console script, stable public API, or
  command-surface coverage. NMO remains a prototype; S3 only hardens the
  existing prototype for the S1 small regular CMP-like signed-offset fixture and
  S2-style metric validation.
- S4-0 adds no feature command, CLI module, console script, stable public API,
  test, example, workflow, command-surface coverage, or XMind update. It does
  not promote NMO, Semblance, FK, or Radon maturity.
- S4-1 adds no feature command, CLI module, console script, stable public API,
  command-surface coverage, or XMind update. Semblance remains a prototype;
  S4-1 only hardens the existing velocity-panel subset for the S1 small regular
  CMP-like signed-offset fixture and explicit-offset negative cases.
- S4-2 adds no feature command, CLI module, console script, stable public API,
  command-surface coverage, or XMind update. The new geometry helper remains
  internal/testing and does not implement SEG-Y trace headers, `sfsegyheader`,
  field-scale geometry, survey databases, FK/Radon algorithms, localization,
  inversion, modeling, imaging, DAS adapters, or C++ kernels.
- S4-3 adds no feature command, CLI module, console script, stable public API,
  command-surface coverage, or XMind update. FK remains a prototype; S4-3 only
  hardens and validates the existing regular-panel Python FK/FK-filter subset
  and documents that it is not a full `sfdipfilter` clone.
- S5 adds no algorithm, feature command, CLI module, console script, stable
  public API, command-surface coverage, or XMind update. NMO, Semblance, FK,
  and Radon remain prototypes; S5 only integrates existing bounded contracts
  into a deterministic small-gather workflow regression.
- S6-0 adds no algorithm, feature command, CLI module, console script, stable
  public API, workflow, test, command-surface coverage, or XMind update. It
  closes Seismic Topic v0 as a documentation-only decision point and does not
  promote NMO, Semblance, FK, Radon, S1-S5 helpers, or workflow reports.
- S6-1 adds no algorithm, feature command, CLI module, console script, stable
  public API, workflow, test, command-surface coverage, or XMind update. It
  does not modify `pymadagascar/seismic/radon.py`, `pymadagascar/cli/radon.py`,
  or `pymadagascar/cli/iradon.py`, and it does not promote the Radon prototype
  to `sfslant`, high-resolution `sfradon`, or solved least-squares inversion.
- S6-2 keeps Radon/slant prototype maturity unchanged while making the small
  operator directions explicit: `radon` is `m=A^T d`, `iradon` is `d=A m`, and
  neither is high-resolution `sfradon` or solved inversion.
- S6-2 adds no new algorithm, feature command, CLI module, console script,
  stable public API, command-surface coverage, XMind update, original
  Madagascar dependency, or C++ dependency.
- S7-0 adds no algorithm, feature command, CLI module, console script, stable
  public API, workflow, test, command-surface coverage, or XMind update. It
  closes Seismic Topic v0, pauses further seismic work by default, defers
  high-resolution `sfradon`, velocity picking, and SEG-Y/header work, and
  recommends Inversion / Operator Foundation as the next topic.
- I0-0 adds no algorithm, solver, feature command, CLI module, console script,
  stable public API, workflow, test, command-surface coverage, or XMind update.
  It starts the Inversion / Operator Foundation topic as audit/design only,
  keeps B-4 as a small in-memory operator/CG subset, and defers operator
  composition implementation, regularization, CGLS/LSQR, high-resolution
  Radon, imaging inversion, DAS inversion, and velocity inversion.
- I0-1 adds no geophysical algorithm, solver, feature command, CLI module,
  console script, stable root/API export, workflow, command-surface coverage,
  or XMind update. It keeps the new operator algebra and solver-history/result
  containers as direct-module prototype/testing surfaces and leaves existing
  `conjugate_gradient` / `conjugate_gradient_normal` result contracts
  unchanged.
- I0-2 adds no geophysical algorithm, solver, CGLS/LSQR, feature command, CLI
  module, console script, stable root/API export, workflow, command-surface
  coverage, or XMind update. It keeps regularization operators as
  direct-module prototype/testing surfaces and does not wire them into the
  existing CG helpers.
- I0-3 adds no geophysical algorithm, solver, CGLS/LSQR, feature command, CLI
  module, console script, stable root/API export, workflow, example,
  command-surface coverage, or XMind update. It keeps the new
  LeastSquaresProblem/objective/stopping diagnostics structures as direct-
  module prototype/testing surfaces and does not wire them into the existing
  CG helpers.
- I0-4 adds no new solver algorithm, CGLS/LSQR implementation, feature command,
  CLI module, console script, stable root/API export, workflow, example,
  command-surface coverage, or XMind update. Existing CG/CGNR functions,
  complex aliases, `ConjugateGradientResult`, and CLI output remain unchanged;
  diagnostics are opt-in through direct-module prototype helpers.
- The XMind workbook remains frozen at the Stage C-10/M1 snapshot. Mindmap
  validation distinguishes that frozen artifact inventory from current
  S1/S2/S3/S4-0/S4-1/S4-2/S4-3/S5/S6-0/S6-1/S6-2/S7-0/I0-0/I0-1/I0-2/I0-3/I0-4
  Markdown and repository counts.
- `tools/check_release.py` now requires and validates the feature mindmap.
  M1 changes no feature command, CLI module, console script, stable API,
  example, workflow, or command-surface coverage value.
- Documentation now separates full Madagascar coverage from core
  `system/` + `plot/main` coverage.
- Stable `pymada-*` names are documented separately from module-only CLI entry
  points.
- `RSFData` is documented as a convenience wrapper over lower-level stable APIs,
  with non-mutating transforms by default.
- Historical handoff docs are preserved as history rather than treated as the
  current source of truth.
- Historical and duplicated docs were moved outside `docs/` to
  `archive_docs/docs_before_slimming_2026-06-09/`; release docs checks scan only
  current `docs/` and `examples/`.
- Coverage docs now count Stage B-1 command-surface additions while noting that
  `sfmin/sfmax` are upstream `sfstack` aliases rather than standalone source
  programs.
- Coverage docs now count Stage B-2 command-surface additions while noting that
  `sfmul/sfdiv` are `sfadd` aliases and `sftpow` is from `user/nobody`.
- Coverage docs now count Stage B-3-1 command-surface additions while noting
  that `sfheaderwindow/sfheadercut` are Python mask/header subsets, not full
  Madagascar header table clones.
- Coverage docs now count Stage B-3-2 command-surface additions while noting
  that `sfheaderattr/sfheadermath` are `system/seismic` header-table tools and
  `sfheadersort` is a `system/main` source-backed command.
- Coverage docs now count Stage B-4 command-surface additions while noting that
  the Python implementation is matrix/operator-object backed, not the full
  Madagascar external command framework.
- Coverage docs now count Stage C-1 signal/preprocessing additions while noting
  their small-data, NumPy-backed, partial parameter scope.
- Coverage docs now count Stage C-2 generic/sampling additions while noting
  where the Python subset differs from upstream irregular interpolation,
  header-file binning, picked-surface slicing, and complex local-maxima output.
- Coverage docs now count Stage C-3 signal/correlation additions while noting
  where the Python subset differs from upstream helix filters, local
  envelope-correlation inversion, multi-slope shifts, and NMO stack scans.
- Coverage docs now count Stage C-4 additions while distinguishing four
  `system/generic` commands from the two selected `user/*` utilities.
- `sffold` remains audit-only because it requires SEG-Y trace headers;
  `sfdiff` was selected as the sixth QC function after confirming that upstream
  `sfzero` is an ENO zero-crossing detector rather than a zero-data generator.
- Quality Pass Q1 keeps stable names intact and documents the intended
  differences between mute/mutter, stack/stacks, clip/clip2/threshold,
  convolution/correlation families, dd/diff, and header-query/statistic tools.
- `RSFData.convolve`, `cconv`, `envcorr`, and `diff` now share one internal
  second-operand adapter with consistent RSFData/path/array/list handling and
  clear errors for missing paths or scalar operands.
- Older top-level examples now accept an optional output directory, allowing
  the full example set to run under pytest temporary directories without
  writing new outputs into the repository.
- Stage C-5 records the audited distinction between `sfmath` unary functions,
  upstream coordinate-gain `sfpow`, the new sample-wise `pow` convenience,
  core `sfhistogram`, and `user/ivlad` `sfquantile`. Coverage increases only
  for the two genuinely new upstream command surfaces.
- Release Quality Pass Q2 makes pure Python the actual default build:
  `wheel.cmake=false`, no Ninja/pybind11 default build requirement, and an
  explicit C++ opt-in path.
- At Release Quality Pass Q2, CLI inventory checks parsed TOML structurally,
  imported all then-current 102 modules,
  verify their runtime entry contract, and resolve all 25 console-script
  targets.
- Workflow examples now default to system temporary directories; explicit
  output paths remain supported.
- Stage C-6 keeps coverage conservative: only the directly corresponding
  `user/fomels/Mmedian.c` axis-1 reduction is newly counted. The other seven
  CLI names are conveniences over NumPy, `sfattr`, or `sfstack`-like behavior,
  or have no matching standalone upstream program.
- Roadmap Reassessment R1 changes documentation and maturity classification
  only. It adds no command or stable API and keeps coverage at
  `86 / 2114`, core coverage at `73 / 301`, and direct `system/main` coverage
  at `32 / 39`.
- Route realignment keeps D-1 intact as a workflow prototype, stops before
  D-2 adapters/picking expansion, and returns the active main line to the
  Stage C signal/small-gather foundation.
- Stage D-1 keeps its synthetic model and inversion helpers inside the workflow
  instead of promoting them to stable APIs. It adds no CLI, console script, or
  command-surface coverage.
- Stage C-7 keeps coverage conservative. No matching standalone upstream
  program was found for demean/detrend/decimate/bandstop/notch, while
  `user/luke/Mrms.c` differs from the project local-RMS window and boundary
  contract. All six new module CLIs are therefore uncounted conveniences.
- Stage C-8 keeps coverage conservative. Related upstream amplitude-spectrum,
  border-taper, user coherence-cube, STFT, and SNR programs do not match the
  new Pythonic spectral-QC names or contracts. No new command surface is
  counted and no console scripts are registered.
- Stage C-9 keeps coverage conservative. Related upstream spectrum, STFT,
  dominant-frequency printout, envelope-balance, and TAH spectral-balance
  programs have different names and contracts. All six module-only CLIs are
  Pythonic conveniences; no command surface or console script is added.
- WSL-1 changes validation infrastructure only. It adds no feature command,
  console script, stable processing API, or command-surface coverage.

### Fixed

- Updated stale console_scripts, example, docs, and pytest counts in current-use
  documentation.
- Clarified that `sfbyte`-style behavior is a Python byte scaling substitute,
  not a VPlot byte stream or confirmed original `sfbyte` clone.
- Clarified prototype status for SEG-Y, NMO/Semblance, FK/Radon, Kirchhoff, and
  acoustic2d.
- Clarified that `sfcp/sfrm` are safe file-level subsets and `sfmin/sfmax` are
  text-statistic utilities, not full upstream `sfstack` alias clones.
- Clarified B-2 subset limits, including `sfdiv zero_policy`, `sftpow`
  non-positive coordinate handling, and `sfinterleave` same-shape input rules.
- Clarified B-3-1 subset limits, including one-dimensional masks, continuous
  mask requirement for `sfheaderwindow`, no `inv=` support, and no full
  header-table or SEG-Y trace-header compatibility.
- Added explicit RSFData non-mutating/inplace, double-input, and
  shape/header/dtype contracts.
- Fixed editable installation on the current Windows environment, where the
  previous forced Ninja generator caused a build failure even with C++ disabled.
- Made the optional WSL probe non-blocking by default while retaining
  `--strict` diagnostics.
- Repaired original comparison calls to follow Madagascar stdin/stdout stream
  conventions instead of assuming every program accepts `in=`/`out=`.
- Prevented UTF-8 decoding of binary RSF stdout; text tools now opt into
  decoding and stderr is decoded with replacement for diagnostics.
- Repaired Windows-to-WSL probe execution by using `wsl.exe`, loading the
  selected login shell/Conda prefix, and transporting the probe script as
  base64 to avoid command-line quoting damage.

### Documentation

- The former XMind visual index is replaced by
  `docs/PYMADAGASCAR_LEARNING_GUIDE.ipynb`, a study-oriented notebook. The
  eight Markdown files remain the authoritative API, compatibility, testing,
  status, and coverage sources.
- `docs/PROJECT_STATUS.md` records the current state, counts, test baseline,
  and stage progress.
- `docs/USER_GUIDE.md` records install, CLI inventory, Python API entry points,
  examples, and release tool usage.
- `docs/API_AND_COMPATIBILITY.md` records stability levels and compatibility
  boundaries.
- `docs/COVERAGE_AND_ROADMAP.md` records coverage, recent source mappings, and
  the R1 topic capability matrix, route ranking, and next migration guidance.
- `docs/TESTING_AND_ENVIRONMENT.md` records pytest, optional original
  Madagascar, WSL, hybrid, and release-check notes.
- Pre-slimming detailed docs are archived under
  `archive_docs/docs_before_slimming_2026-06-09/`.

### Testing

- I0-6 adds 13 deterministic preconditioner contract tests. Windows suite:
  `996 passed, 94 skipped`; WSL suite: `1062 passed, 28 skipped`; WSL original
  marker remains `66 passed, 27 skipped`. Release, CLI inventory,
  docs-command, examples inventory, mindmap, and strict WSL checks pass.
- I0-5 adds 18 deterministic CGLS contract tests. Windows suite:
  `983 passed, 94 skipped`; WSL suite: `1049 passed, 28 skipped`; WSL original
  marker remains `66 passed, 27 skipped`. Release, CLI inventory,
  docs-command, examples inventory, mindmap, and strict WSL checks pass.
- I0-4 adds 13 deterministic solver-history integration and CGLS/LSQR design
  contract tests. Windows suite: `965 passed, 94 skipped`; WSL suite:
  `1031 passed, 28 skipped`; WSL original marker: `66 passed, 27 skipped`.
  Release, CLI inventory, docs-command, examples inventory, mindmap, and
  strict WSL Madagascar checks pass.
- I0-3 adds 17 deterministic objective/residual/diagnostics contract tests.
  Windows suite: `952 passed, 94 skipped`; WSL suite:
  `1018 passed, 28 skipped`; WSL original marker: `66 passed, 27 skipped`.
  Release, CLI inventory, docs-command, examples inventory, mindmap, and
  strict WSL Madagascar checks pass.
- I0-2 adds 12 deterministic regularization-operator contract tests. Windows
  suite: `935 passed, 94 skipped`; WSL suite: `1001 passed, 28 skipped`; WSL
  original marker: `66 passed, 27 skipped`. Release, CLI inventory,
  docs-command, examples inventory, mindmap, and strict WSL Madagascar checks
  pass.
- I0-1 adds 16 deterministic operator-foundation contract tests. Windows
  suite: `923 passed, 94 skipped`; WSL suite: `989 passed, 28 skipped`; WSL
  original marker: `66 passed, 27 skipped`. Release, CLI inventory,
  docs-command, examples inventory, mindmap, and strict WSL Madagascar checks
  pass.
- I0-0 adds no tests. It is validated by rerunning the existing Windows and WSL
  suites plus release, CLI inventory, docs-command, examples inventory,
  mindmap, and strict WSL Madagascar checks; expected counts remain unchanged
  from S7-0.
- S7-0 adds no tests. It is validated by rerunning the existing Windows and WSL
  suites plus release, CLI inventory, docs-command, examples inventory,
  mindmap, and strict WSL Madagascar checks; expected counts remain unchanged
  from S6-2.
- S6-0 adds no tests. It is validated by rerunning the existing Windows and WSL
  suites plus release, CLI inventory, docs-command, examples inventory,
  mindmap, and strict WSL Madagascar checks; expected counts remain unchanged
  from S5.
- S6-1 adds no tests. It is validated by rerunning the existing Windows and WSL
  suites plus release, CLI inventory, docs-command, examples inventory,
  mindmap, and strict WSL Madagascar checks; expected counts remain unchanged
  from S6-0.
- S6-2 adds 29 deterministic small slant-stack contract tests. Windows suite:
  `907 passed, 94 skipped`; WSL suite: `973 passed, 28 skipped`; WSL original
  marker remains `66 passed, 27 skipped`.
- S5 adds 7 deterministic integrated small-gather workflow tests. Windows
  suite: `878 passed, 94 skipped`; WSL suite: `944 passed, 28 skipped`; WSL
  original marker remains `66 passed, 27 skipped`.
- S4-3 adds 30 deterministic FK prototype contract tests. Windows suite:
  `871 passed, 94 skipped`; WSL suite: `937 passed, 28 skipped`; WSL original
  marker remains `66 passed, 27 skipped`.
- S4-2 adds 25 deterministic small-gather geometry contract tests. Windows
  suite: `841 passed, 94 skipped`; WSL suite: `907 passed, 28 skipped`; WSL
  original marker remains `66 passed, 27 skipped`.
- S4-1 adds 28 deterministic Semblance contract tests. Windows suite:
  `816 passed, 94 skipped`; WSL suite: `882 passed, 28 skipped`; WSL original
  marker remains `66 passed, 27 skipped`.
- S3 adds 28 deterministic NMO contract tests. Windows suite:
  `786 passed, 94 skipped`; WSL suite: `852 passed, 28 skipped`; WSL original
  marker remains `66 passed, 27 skipped`.
- S2 adds 16 deterministic metrics/QC tests. Windows suite:
  `758 passed, 94 skipped`; WSL suite: `824 passed, 28 skipped`; WSL original
  marker remains `66 passed, 27 skipped`.
- S1 adds 17 deterministic contract tests. Windows suite:
  `742 passed, 94 skipped`; WSL suite: `808 passed, 28 skipped`; WSL original
  marker remains `66 passed, 27 skipped`.
- Mindmap Documentation Pass M1 adds standard-library XML parsing, required
  branch checks, exact 25/109 CLI entrypoint inventories, live repository
  counts, and `check_release.py` integration without requiring mind-map GUI
  software or network access.
- M1 Windows suite: `725 passed, 94 skipped`; WSL suite:
  `791 passed, 28 skipped`; WSL original marker remains
  `66 passed, 27 skipped`.
- Stage B-1 added `tests/test_cp_rm_min_max.py` for API, CLI subprocess, and
  optional original comparison coverage.
- Stage B-2 added `tests/test_mul_div_tpow_interleave.py` for API, CLI
  subprocess, error-policy, header, and optional original comparison coverage.
- Stage B-3-1 added `tests/test_header_window_cut.py` for API, CLI subprocess,
  mask semantics, header update, and optional original comparison coverage.
- Stage B-3-2 added `tests/test_header_table_tools.py` for minimal header table
  read/write, attr/math/sort API, CLI subprocess, metadata preservation, error
  handling, and optional original comparison coverage.
- Stage B-4 added `tests/test_linear_operator_tools.py` for
  `LinearOperator`/`MatrixOperator`, real and complex dot tests, real and
  complex CG modes, CLI subprocesses, shape/mode errors, and optional original
  comparison skips.
- Stage C-1 added `tests/test_signal_preprocessing_tools.py` for costaper,
  threshold, spectra, envelope, RSFData chaining, CLI subprocesses,
  shape/header behavior, invalid parameters, and optional original comparison
  coverage.
- Stage C-2 added `tests/test_generic_sampling_tools.py` for linear resampling,
  table binning, fixed-index slicing, max1 picking, RSFData chaining, CLI
  subprocesses, shape/header behavior, invalid parameters, and optional
  original comparison skips.
- Stage C-3 added `tests/test_signal_correlation_conditioning_tools.py` for
  autocorrelation, convolution, circular convolution, envelope correlation,
  integer shifts, statistical stacks, RSFData chaining, CLI subprocesses,
  shape/header behavior, invalid parameters, and optional original comparison
  skips.
- Stage C-4 added `tests/test_axis_calculus_conditioning_tools.py` for finite
  differences, causal and trapezoid integration, clip2, regular-axis mutter,
  dataset difference metrics, RSFData chaining, CLI subprocesses, header/error
  behavior, and optional original comparison coverage.
- Quality Pass Q1 added `tests/test_rsfdata_api_consistency.py`,
  `tests/test_examples_inventory.py`, and release-tool coverage for
  `check_examples_inventory.py`.
- Stage C-5 added `tests/test_unary_distribution_qc_tools.py` for array/file
  APIs, eight subprocess CLIs, RSFData contracts, invalid/complex/non-finite
  behavior, and optional original comparisons.
- Stage C-6 added `tests/test_robust_statistics_nan_tools.py` for global and
  axis statistics, all eight subprocess CLIs, NaN/Inf and complex behavior,
  RSFData/header/dtype contracts, four optional `sfattr` comparisons, and one
  optional `sfmedian` comparison.
- Stage C-6 full suite: `619 passed, 88 skipped`; all 110 module CLIs and all
  30 top-level examples remain covered by inventory/smoke tests.
- Roadmap Reassessment R1 adds no tests; the full regression and release tools
  were rerun successfully: `619 passed, 88 skipped in 60.79s`, followed by all
  four release/inventory checks.
- Stage D-1 adds two focused workflow tests and updates release-tool coverage
  for the required workflow path and six-script workflow inventory.
- Stage D-1 full suite: `621 passed, 88 skipped in 64.38s`; skip composition
  remains 87 optional original Madagascar comparisons plus one optional C++
  extension test.
- Stage C-7 adds `tests/test_signal_qc_foundation_tools.py`, six module-only
  CLI subprocess paths, RSFData contract coverage, and one top-level example
  smoke target. Full suite: `638 passed, 94 skipped in 69.80s`; skip composition is 93
  optional original comparisons plus one optional C++ extension.
- WSL-1 Windows suite: `650 passed, 94 skipped in 73.43s`; skip composition is
  93 optional original comparisons plus one optional C++ extension.
- WSL-1 `ubuntu2204` suite: `716 passed, 28 skipped in 84.25s`.
- WSL-1 original marker: `66 passed, 27 skipped`; the previous 61 comparison
  failures were reduced to zero. Remaining skips are explicit unavailable
  commands or designed subsets that are not directly comparable.
- Stage C-8 adds `tests/test_spectral_qc_tools.py`, six CLI subprocess paths,
  RSFData spectral/binary-operand contracts, and one top-level example smoke
  target. Windows suite: `674 passed, 94 skipped`; WSL suite:
  `740 passed, 28 skipped`; original marker remains `66 passed, 27 skipped`.
- Stage C-9 adds `tests/test_spectral_averaging_attributes_tools.py`, six CLI
  subprocess paths, RSFData binary-operand/inplace contracts, frequency-axis
  and complex-output checks, known transfer/frequency tests, whitening and
  normalization checks, and one top-level example smoke target. No original
  marker is added because the audited upstream contracts do not match.
- Stage C-9 Windows suite: `699 passed, 94 skipped`; WSL suite:
  `765 passed, 28 skipped`; original marker remains `66 passed, 27 skipped`.
- Stage C-10 adds `tests/test_fir_filter_design_tools.py` for FIR design,
  filtering, response, band-energy/filter-bank contracts, six subprocess CLIs,
  RSFData operands/inplace behavior, and invalid/finite/complex cases. No
  original marker is added because related upstream contracts differ.
- Stage C-10 Windows suite: `721 passed, 94 skipped`; WSL suite:
  `787 passed, 28 skipped`; WSL original marker remains
  `66 passed, 27 skipped`. The strict WSL probe and all release/inventory
  checks pass.
- Release Quality Pass Q2 full suite: `600 passed, 83 skipped`; all 102
  module CLIs and all 25 installed console-script launchers pass `--help`.
- At Release Quality Pass Q2, all then-current 29 top-level examples were
  subprocess-smoke-tested with temporary output directories and no new writes
  into `examples/`.
- Current stage A baseline was `434 passed, 38 skipped`; Stage B-1 full-suite
  result was `446 passed, 42 skipped`.
- Stage B-1 full-suite result: `446 passed, 42 skipped`.
- Stage B-2 final pytest status was `455 passed, 46 skipped`.
- Stage B-3-1 final pytest status is recorded in `docs/PROJECT_STATUS.md` and
  `docs/TESTING_AND_ENVIRONMENT.md`.
- Stage B-3-2 final pytest status is recorded in `docs/PROJECT_STATUS.md` and
  `docs/TESTING_AND_ENVIRONMENT.md`.
- Stage B-4 final pytest status is recorded in `docs/PROJECT_STATUS.md` and
  `docs/TESTING_AND_ENVIRONMENT.md`.
- Stage C-1 final pytest status is recorded in `docs/PROJECT_STATUS.md` and
  `docs/TESTING_AND_ENVIRONMENT.md`.
- Stage C-2 final pytest status is recorded in `docs/PROJECT_STATUS.md` and
  `docs/TESTING_AND_ENVIRONMENT.md`.
- Stage C-3 final pytest status is recorded in `docs/PROJECT_STATUS.md` and
  `docs/TESTING_AND_ENVIRONMENT.md`.
- Stage C-4 final pytest status is recorded in `docs/PROJECT_STATUS.md` and
  `docs/TESTING_AND_ENVIRONMENT.md`.
- Optional comparison skips are expected when upstream `sf*`
  commands are not installed or not on PATH on this machine.
- 1 skip is the optional C++ backend test because `pymadagascar._core` is not
  compiled in the current environment.
- Pure Python tests do not depend on original Madagascar or C++ extension.
- Release tools pass: `check_release.py`, `check_cli_inventory.py`,
  `check_docs_commands.py`, and `check_examples_inventory.py`.

### Known limitations

- This is not a complete Madagascar clone.
- Full Madagascar/alias command-surface coverage remains low:
  `97 / 2114 = 4.59%`.
- Core `system/` + `plot/main` command-surface coverage is
  `84 / 301 = 27.91%`.
- Stage C-7 does not implement polyphase decimation, designed FIR/IIR notch
  filters, arbitrary polynomial detrending, multidimensional upstream RMS
  windows, streaming, or out-of-core processing.
- Stage C-8's baseline periodogram path does not perform Welch averaging.
  Advanced window families, arbitrary-axis STFT, IIR/AR spectral estimation,
  automatic SNR windows, streaming, and out-of-core processing remain absent.
- Stage C-9 does not implement confidence intervals, median Welch averaging,
  multi-taper/AR estimation, advanced system identification, predictive
  deconvolution, complex-input spectral conditioning, streaming, or
  out-of-core processing.
- Stage C-10 does not implement IIR filters, polyphase/multirate processing,
  full filter-design families, SciPy-compatible filtfilt initial conditions,
  wavelet packets, automatic bands, streaming, or out-of-core processing.
- `sfmv` is not implemented. `sfmin/sfmax` are text-statistic subsets, not full
  upstream `sfstack` alias RSF-output clones.
- `sfmul/sfdiv` do not implement the full upstream `sfadd` preprocessing
  parameter set; `sftpow` does not implement `xpow=`; `sfinterleave` does not
  support unequal target-axis lengths or streaming/out-of-core.
- M0-1 `sfscale` is scalar-only and lacks upstream percentile/axis local
  scaling. `sfrotate` is in-memory and does not implement upstream out-of-core
  random-access behavior.
- M0-2 `sfstack` is a bounded in-memory one-axis stack subset only. It does
  not implement upstream `axis=0`, `scale=` vectors, min/max/prod modes,
  program-name aliases, complex RMS, or streaming/out-of-core behavior.
- M0-3 `sfpad` is a bounded in-memory constant-padding subset and `sfspray`
  is a bounded in-memory new-axis duplication subset. They do not implement
  streaming/out-of-core execution, byte-level native trace copying, arbitrary
  `sfput` passthrough, or non-constant border modes.
- `sfheaderwindow/sfheadercut` operate on ordinary RSF data with a mask RSF.
  They do not implement full Madagascar header table semantics, SEG-Y trace
  headers, `sfheaderwindow inv=`, or non-contiguous window selections.
- `sfheaderattr/sfheadermath/sfheadersort` operate on the new minimal numeric
  RSF header table subset only. They do not implement full Madagascar
  header-table parameters, SEG-Y trace headers, or synchronized sorting of a
  separate seismic data volume.
- `sfdottest/sfcdottest/sfconjgrad/sfcconjgrad` operate on the new small-data
  linear-operator subset only. They do not execute arbitrary external operator
  commands, clone the upstream pipe/tempfile framework, support
  preconditioners, or stream out-of-core datasets.
- `sfcostaper/sfthreshold/sfspectra/sfenvelope` operate on the new small-data
  signal preprocessing subset only. They do not implement streaming, full
  upstream threshold pclip ecology, multi-window spectral estimation, or
  envelope phase-rotation modes.
- `sflinear/sfbin/sfslice/sfmax1` operate on the new small-data generic
  sampling subset only. They do not implement upstream irregular table
  interpolation, full header-file/fold binning, picked-surface slicing, complex
  local-maxima lists, spline/ENO/stretch/remap frameworks, pandas tables, or
  out-of-core processing.
- `sfautocorr/sfconvolve/sfcconv/sfenvcorr/sfshifts/sfstacks` operate on the
  new small-data signal correlation and conditioning subset only. They do not
  implement upstream helix-filter autocorrelation, full 2D adjoint/wrap image
  convolution, complex internal filter-operator circular convolution, local
  envelope-correlation inversion, interpolated multi-slope shifts, constant
  velocity NMO stack scans, streaming, or out-of-core processing.
- `sfderiv/sfcausint/sfintegral/sfclip2/sfmutter/sfdiff` operate on the new
  small-data axis-calculus, amplitude-conditioning, and QC subset only. They do
  not implement high-order FIR calculus, anti-causal integration, full
  upstream mutter geometry, trace-header fold maps, streaming, or out-of-core
  processing.
- Stage C-5 unary/distribution tools are in-memory NumPy subsets. Complex
  transcendental transforms, weighted quantiles, streaming histograms, and
  full upstream parameter/output compatibility are not implemented.
- Stage C-6 robust statistics are real-input, in-memory reductions without
  weighted/grouped estimators or streaming. `nan_policy=omit` omits NaNs only;
  non-finite masks/filling handle Inf explicitly.
- NMO/Semblance/FK/Radon remain prototypes.
- Kirchhoff and acoustic2d remain simplified prototypes.
- SEG-Y support is limited to small 2D prototype fixtures.
- Original Madagascar comparisons did not run on this machine because no
  upstream `sf*` commands were found.
- The C++ extension is currently not compiled; hybrid wrappers use NumPy
  fallback.

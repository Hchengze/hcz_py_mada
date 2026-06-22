# Project Status

Generated on 2026-06-19 from the current repository.

## Project Identity

pymadagascar is a Python-friendly local RSF/geophysics toolkit. It supports RSF
I/O, selected Madagascar-style CLI workflows, Pythonic `RSFData` processing,
small-data geophysical processing examples, tests, and documentation.

It is not a complete Madagascar clone. Full `user/*`, VPlot, SCons/book,
IWAVE/RVL, MPI/CUDA/PETSc, and large imaging/modeling systems are not near-term
targets.

Pure Python is the main line. The hybrid C++ layer is optional acceleration only
and must never be a hard dependency.

## Current Counts

| Item | Current value |
| --- | ---: |
| User-facing CLI modules | 135 |
| Registered `pymada-*` console scripts | 28 |
| Pytest files | 88 |
| Top-level example scripts | 34 |
| Workflow scripts under `examples/my_workflows/` | 14 plus 1 helper |
| Current docs markdown files | 8 |
| Learning notebooks | 1 |

## Current Coverage

| Coverage scope | Current value |
| --- | ---: |
| Full Madagascar/alias command surface | `89 / 2114 = 4.21%` |
| Core `system/` + `plot/main` command surface | `76 / 301 = 25.25%` |
| Direct `system/main` source-backed commands | `35 / 39 = 89.74%` |
| `user/*` command surface | about `12 / 1792 = 0.67%` |

Full coverage and core coverage are different denominators and must not be
mixed.

## Current Test Baseline

Recommended local interpreter:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe
```

Latest Windows full-suite result:

```text
1006 passed, 94 skipped
```

Skip summary:

- 93 skips are optional original Madagascar comparison tests because upstream
  `sf*` commands are not available on the current Windows PATH.
- 1 skip is the optional C++ extension test because `pymadagascar._core` is not
  compiled.

Plain `python` is not available on the current PowerShell PATH; use the explicit
interpreter above for local status checks.

The validated WSL `ubuntu2204` environment uses
`/home/hcz/Software/Anaconda/envs/pymadagascar-dev` with Python 3.11 and
Madagascar 4.2-git. Its current full-suite result is:

```text
1006 passed, 94 skipped, 1 warning
```

The warning is the known mounted-drive `.pytest_cache` permission warning when
running from `/mnt/e`; pytest exits successfully. The last dedicated WSL
`original_madagascar` marker baseline is `66 passed, 27 skipped`. The remaining
marker skips are explicit unavailable-command or designed-subset cases; there
are no remaining comparison bridge failures.

## Stage Progress

- Stage 0: handoff and baseline audit completed.
- Stage A: release stabilization docs, checks, and release tools completed.
- Stage B-1: `sfcp`, `sfrm`, `sfmin`, and `sfmax` subsets completed.
- Stage B-2: `sfmul`, `sfdiv`, `sftpow`, and `sfinterleave` subsets completed.
- Stage B-3-1: `sfheaderwindow` and `sfheadercut` ordinary-RSF mask/header
  subsets completed.
- Stage B-3-2: minimal RSF header table model plus `sfheaderattr`,
  `sfheadermath`, and `sfheadersort` Python subsets completed.
- Stage B-4: minimal linear-operator model plus `sfdottest`, `sfcdottest`,
  `sfconjgrad`, and `sfcconjgrad` Python subsets completed.
- Stage C-1: signal/preprocessing small batch with `sfcostaper`,
  `sfthreshold`, `sfspectra`, and `sfenvelope` Python subsets completed.
- Stage C-2: generic/sampling small batch with `sflinear`, `sfbin`,
  `sfslice`, and `sfmax1` Python subsets completed.
- Stage C-3: signal/correlation/data-conditioning batch with `sfautocorr`,
  `sfconvolve`, `sfcconv`, `sfenvcorr`, `sfshifts`, and `sfstacks` Python
  subsets completed.
- Stage C-4: axis calculus/amplitude conditioning/seismic QC batch with
  `sfderiv`, `sfcausint`, `sfintegral`, `sfclip2`, `sfmutter`, and `sfdiff`
  Python subsets completed.
- Stage C-5: unary amplitude transforms and distribution QC with module-only
  `abs`, `sign`, `sqrt`, `log`, `exp`, `pow`, `histogram`, and `quantile`
  Python subsets completed. The first six are explicit convenience surfaces;
  only histogram and quantile add previously uncovered upstream commands.
- Stage C-6: robust statistics and non-finite QC with module-only `mean`, `rms`,
  `var`, `std`, `median`, `range`, `isnan`, and `fillnan` completed. Only the
  `sfmedian` axis-1 reduction is counted as a newly covered upstream command;
  the other entry points are documented Pythonic conveniences over NumPy,
  `sfattr`, or `sfstack`-like capabilities.
- Quality Pass Q1: public API/CLI/examples inventory, RSFData double-input and
  inplace contracts, shape/header/dtype documentation, all-example smoke
  coverage, and release-tool consistency checks completed.
- Release Quality Pass Q2: pure-Python editable-install metadata, all-CLI help
  smoke, console-script target validation, package/version checks, optional WSL
  probe behavior, example output policy, and release-tool checks completed.
- Roadmap Reassessment R1: current APIs, CLIs, examples, workflows, and
  prototype modules classified into ten technical topics; capability matrix,
  maturity boundaries, shortfalls, and six candidate routes documented.
  R1 adds no commands and does not change command-surface coverage.
- M0-1: source-aligned Madagascar command coverage resumes after the F0-1
  through F0-6 forward-modeling loop. M0-1 adds `sfrotate` from
  `../src-master/system/main/rotate.c` and promotes the existing scalar
  `sfscale` subset from `../src-master/system/main/scale.c` to registered
  console-script coverage. It does not continue Forward Modeling, DAS,
  Localization, solver, workflow, large-system, original-source, or coverage
  denominator work.
- M0-2: direct `system/main` command coverage continues with the existing
  `sfstack` bounded subset aligned to `../src-master/system/main/stack.c`.
  M0-2 registers `pymada-stack`, confirms the existing `RSFData.stack(...)`
  chain method, and counts `sfstack` as source-backed command coverage without
  adding a root API, changing denominators, expanding Forward Modeling, or
  touching Original Madagascar source.
- Stage D-1: DAS engineering workflow skeleton completed. The new
  `das_void_diffraction_workflow.py` generates a small kinematic
  time-by-channel shot gather, applies the existing FK prototype, overlays
  theoretical and fitted void-diffraction curves, and inverts simulated picks
  for `void_x`, `void_depth`, and Rayleigh velocity. It adds no public API,
  CLI, console script, or command-surface coverage.
- Stage D-2A: DAS workflow geometry metadata contract completed. The D-1
  workflow JSON now carries a workflow-only `das_geometry` object for regular
  linear local-2D DAS geometry, including channel spacing/start/stop, fiber
  orientation, source/void coordinates, units, receiver-coordinate convention,
  sample timing, and explicit `gauge_length_status: not_modeled`. This adds no
  DAS file adapter, field fixture, automatic picking, gauge response, stable
  API, CLI, command coverage, or field-performance claim.
- Stage D-2B: DAS/localization workflow integration completed. The void
  diffraction workflow now uses the package-level
  `pymadagascar.localization.traveltime` kinematic diffraction travel-time and
  variable-velocity grid-search prototype while keeping only thin
  workflow-specific coordinate adapters. Its JSON adds
  `localization_algorithm` metadata documenting
  `grid_search_point_location_velocity_2d`, closed-form slowness velocity
  mode, observed-minus-predicted residuals, and prototype/non-field-ready
  boundaries. This adds no DAS adapter, real-data reader, automatic picking,
  gauge response, stable/root API, CLI, command coverage, or coverage
  denominator change.
- Forward Modeling Topic F0-1: model/acquisition geometry contract completed.
  The new pymadagascar.modeling.geometry topic module defines a regular
  local-2D acoustic model grid, point-source and receiver-array geometry,
  regular receiver-line construction, JSON-safe acquisition metadata, and
  conversion to the existing acoustic2d_forward integer-index signature.
  It documents the current acoustic2d conventions: physical x,z coordinates,
  depth positive downward, NumPy velocity shape (nx, nz), RSF n1=z,n2=x,
  and source/receiver indices in (x_index,z_index) order. F0-1 changes no
  finite-difference numerical core and adds no wave-equation solver,
  multi-shot simulation, interpolation, CLI, root/stable API, command
  coverage, or coverage denominator change.
- Forward Modeling Topic F0-2: acquisition-driven acoustic2d shot wrapper
  completed. The new pymadagascar.modeling.shot topic module adds
  AcousticShotRecord2D and run_acoustic2d_shot, which accept a NumPy velocity
  model, AcousticModelGrid2D, and AcousticAcquisition2D, convert physical
  source/receiver coordinates to the existing acoustic2d_forward integer-index
  contract, run the unchanged finite-difference core through temporary RSF
  inputs, and return a Pythonic shot record with time axis, receiver/source
  coordinates, and JSON-safe modeling metadata. F0-2 adds no new wave-equation
  solver, multi-shot survey loop, source/receiver interpolation, CLI,
  root/stable API, command coverage, or coverage denominator change.
- Forward Modeling Topic F0-3: multi-shot acoustic survey wrapper completed.
  The pymadagascar.modeling.shot topic module now adds AcousticSurveyRecord2D
  and run_acoustic2d_survey, which execute a non-empty input-ordered sequence
  of AcousticAcquisition2D objects by reusing run_acoustic2d_shot for each
  shot. The survey result keeps a list of AcousticShotRecord2D objects plus
  JSON-safe path-free survey metadata documenting shot count, receiver counts
  per shot, input-order semantics, no parallelism, no cache, and no committed
  survey tensor layout. F0-3 changes no finite-difference numerical core and
  adds no new wave-equation solver, interpolation, CLI, root/stable API,
  command coverage, or coverage denominator change.
- Forward Modeling Topic F0-4: acoustic survey tensor conversion and summary
  helpers completed. The pymadagascar.modeling.shot topic module now adds
  AcousticSurveyTensor2D, acoustic_survey_to_tensor, and
  summarize_acoustic_survey. The default AcousticSurveyRecord2D contract remains
  list-backed; tensor stacking is available only through the explicit helper,
  uses the documented shot_receiver_time layout, and requires consistent
  receiver counts plus matching time axes. The helper does not pad, interpolate,
  or drop receivers, and F0-4 changes no acoustic2d numerical core, default
  survey return type, CLI, root/stable API, command coverage, or coverage
  denominator.
- Forward Modeling Topic F0-5: synthetic acoustic velocity model builders
  completed. The new pymadagascar.modeling.models topic module adds
  AcousticVelocityModel2D plus constant, layered, rectangular-anomaly, circular-
  anomaly, and summary helpers. These builders return positive finite velocity
  arrays shaped (nx, nz) for AcousticModelGrid2D, keep the local_2d_x_z
  coordinate convention with depth positive downward, and provide JSON-safe
  path-free metadata compatible with the existing acoustic2d shot/survey
  wrappers. F0-5 adds no smoothing, random model, geologic GUI, wave-equation
  solver, CLI, root/stable API, command coverage, or coverage denominator
  change.
- Forward Modeling Topic F0-6: geometry-driven acoustic modeling validation
  workflow completed. The new
  examples/my_workflows/acoustic_modeling_validation_workflow.py connects the
  F0-1 geometry contract, F0-2/F0-3 shot/survey wrappers, F0-4 survey tensor
  helpers, and F0-5 synthetic velocity model builders into a deterministic
  smoke-level JSON validation report. It verifies shape/count/time/tensor,
  finite-data, nonzero-data, stackability, and JSON/path-free acceptance checks.
  F0-6 is not a production modeling accuracy, convergence, dispersion, or
  imaging study and adds no solver, interpolation, padding, CLI, root/stable
  API, command coverage, or coverage denominator change.
- Stage C-7: signal and small-gather QC foundation completed with module-only
  `demean`, `detrend`, `decimate`, `bandstop`, `notch`, and `localrms` CLIs,
  shared NumPy APIs, RSF wrappers, RSFData methods, and a focused demo.
  Source audit found no matching standalone upstream programs for the first
  five names. `user/luke/Mrms.c` is related but has different multidimensional
  window and boundary semantics, so all six remain uncounted conveniences.
- Stage C-8: spectral QC and window-function foundation completed with
  `windowfunc`, `psd`, `csd`, `coherence`, `spectrogram`, and `snr`
  module-only CLIs, shared NumPy APIs, RSFData methods, and a focused demo.
  These are explicit Pythonic conveniences: upstream `sfspectra` is an
  amplitude-spectrum tool, `user/chen/Mcoherence.c` is a local coherence cube,
  and `user/yliu/Mstft.c`/`Msnr.c` have different command names and contracts.
  Coverage is unchanged.
- Stage C-9: spectral averaging, response estimation, conditioning, and
  attributes completed with module-only `welch`, `welchcsd`, `transfer`,
  `whiten`, `specnorm`, and `freqattr` CLIs, shared NumPy APIs, RSFData
  methods, and a focused demo. The upstream audit found related amplitude
  spectrum, STFT, dominant-frequency printout, and spectral-balance programs,
  but no matching standalone contracts. All six remain uncounted Pythonic
  conveniences and coverage is unchanged.
- Stage C-10: FIR design, filter application, response diagnostics, and
  frequency-band QC completed with module-only `firwin`, `firfilter`,
  `filtfilt`, `freqz`, `bandenergy`, and `filterbank` CLIs, shared NumPy
  APIs, RSF wrappers, four RSFData methods, and a focused demo. Core
  `sfbandpass` is a Butterworth implementation; `user/chen/sfir` consumes an
  existing FIR and `user/chen/sffbank1/sffbank2` are interpolation filter
  banks with different contracts. All six C-10 names remain uncounted
  Pythonic conveniences and coverage is unchanged.
- WSL-1: original Madagascar comparison infrastructure repaired. The runner
  now uses binary-safe subprocess capture, explicit stdin/stdout file
  redirection, text decoding only when requested, local DATAPATH sidecars, and
  readable failure diagnostics. The WSL probe now supports distro/user/shell/
  Conda selection plus strict and non-strict modes. No command, stable API, or
  coverage count changed.
- Mindmap Documentation Pass M1 previously added a visual index through Stage
  C-10. D0-1 supersedes that artifact with
  `docs/PYMADAGASCAR_LEARNING_GUIDE.ipynb` and
  `tools/check_learning_notebook.py`; neither M1 nor D0-1 adds a command,
  stable API, or coverage entry.
- Topic Architecture Pass T1: repository-only reassessment of ten technical
  topics completed. The continuous Stage C feature-batch sequence ends at
  C-10, C-11 is not recommended, and seismic data signal analysis and
  processing is selected as the first topic. T1 changes documentation only:
  no feature, CLI, console script, stable API, coverage value, test, example,
  or learning-notebook artifact changes.
- Seismic Topic S1: Contract and Fixture Foundation completed. It adds
  `pymadagascar.testing.seismic_fixtures` as an internal/testing module,
  `tests/test_seismic_signal_contracts.py`, and
  `examples/my_workflows/seismic_signal_contract_workflow.py`. The pass defines
  trace, regular panel, regular signed-offset gather, processing pipeline, and
  validation contracts using existing APIs. It adds no feature command, CLI
  module, console script, stable public API, command-surface coverage, original
  Madagascar dependency, or C++ dependency.
- Seismic Topic S2: Pipeline Metrics and QC Report Foundation completed. It
  adds the internal `pymadagascar.testing.seismic_metrics` module,
  `tests/test_seismic_signal_metrics.py`, and
  `examples/my_workflows/seismic_signal_metrics_workflow.py`. S2 measures
  explicit-window SNR, target/reject frequency-band energy, dominant frequency,
  mute coverage, stack noise reduction, finite values, and header/axis
  preservation. Its deterministic JSON report is a workflow/testing contract,
  not a stable public format. S2 adds no feature command, CLI module, console
  script, stable public API, command-surface coverage, original Madagascar
  dependency, or C++ dependency.
- Seismic Topic S3: NMO Prototype Contract Hardening with S1/S2 Fixtures
  completed. It hardens the existing NMO prototype for finite small regular
  CMP-like signed-offset gathers, explicit or regular offset geometry, positive
  velocity, positive time sampling, finite parameters, deterministic linear
  interpolation, and metadata preservation. It adds
  `tests/test_seismic_nmo_contract.py` and
  `examples/my_workflows/seismic_nmo_contract_workflow.py` for correct-vs-wrong
  velocity, flattening, stack, finite-value, header-axis, CLI, JSON report, and
  output-isolation checks. It adds no feature command, CLI module, console
  script, stable public API, command-surface coverage, original Madagascar
  dependency, or C++ dependency.
- Seismic Topic S4-0: Madagascar Source Alignment and Bounded Selection
  completed as a documentation-only source audit. It aligns the existing NMO,
  Semblance, FK/FK-filter, and Radon prototypes with located Madagascar sources
  under `../src-master`, records the current differences and risks, and selects
  Semblance prototype contract hardening as the next bounded task. It adds no
  feature command, CLI module, console script, stable public API, test,
  example, workflow, command-surface coverage, XMind update, original
  Madagascar dependency, or C++ dependency.
- Seismic Topic S4-1: Semblance Prototype Contract Hardening completed. It
  audits `../src-master/system/seismic/Mvscan.c`, hardens the existing
  Semblance prototype for finite small regular CMP-like signed-offset gathers
  or length-compatible explicit offsets, records velocity-panel metadata and
  input-offset provenance, rejects invalid velocity/time/offset/finite-value
  cases, and validates true-velocity versus wrong-velocity behavior on the
  S1/S2/S3 fixture base. It adds
  `tests/test_seismic_semblance_contract.py` and
  `examples/my_workflows/seismic_semblance_contract_workflow.py`, but no
  feature command, CLI module, console script, stable public API,
  command-surface coverage, XMind update, original Madagascar dependency, or
  C++ dependency.
- Seismic Topic S4-2: Small-Gather Geometry Adapter Design completed. It adds
  the internal/testing `pymadagascar.testing.seismic_geometry` module,
  `tests/test_seismic_geometry_contract.py`, and
  `examples/my_workflows/seismic_geometry_contract_workflow.py`. S4-2 defines
  the boundary between regular signed-offset RSF axis metadata, explicit
  trace-compatible offset vectors, and a minimal numeric source/receiver table
  for deterministic small fixtures. It is not SEG-Y trace-header support, not
  a production survey geometry database, and adds no feature command, CLI
  module, console script, stable public API, command-surface coverage, XMind
  update, original Madagascar dependency, or C++ dependency.
- Seismic Topic S4-3: FK Prototype Source-Aligned Validation completed. It
  audits the absence of a direct `Mfk.c` transform source, records
  `../src-master/system/generic/Mdipfilter.c` as the nearest dip/f-k/fan filter
  reference, hardens the existing FK prototype for finite small regular
  time-space panels, finite positive axis sampling, and finite fan-filter
  parameters, and validates analytic plane-wave FK peaks plus target/reject
  slope fan filtering. It adds `tests/test_seismic_fk_contract.py` and
  `examples/my_workflows/seismic_fk_contract_workflow.py`, but no feature
  command, CLI module, console script, stable public API, command-surface
  coverage, XMind update, original Madagascar dependency, or C++ dependency.
- Seismic Topic S5: Integrated Small-Gather Processing Workflow v0 completed.
  It adds `tests/test_seismic_integrated_workflow.py` and
  `examples/my_workflows/seismic_small_gather_processing_workflow.py` to combine
  existing S1/S2/S3/S4 fixture, metric, geometry, NMO, Semblance, FK, stack,
  quicklook, and path-free JSON-report contracts into one deterministic
  workflow-level regression. It adds no new algorithm, feature command, CLI
  module, console script, stable public API, command-surface coverage, XMind
  update, original Madagascar dependency, or C++ dependency.
- Seismic Topic S6-0: Topic v0 Summary and Next-Route Decision completed as a
  documentation-only route decision. It summarizes the S1-S5 small-gather v0
  capability, confirms the remaining limits, and recommends the next bounded
  pass as Radon/slant source-aligned design before any implementation or
  velocity-picking work. It adds no algorithm, feature command, CLI module,
  console script, stable public API, workflow, test, command-surface coverage,
  XMind update, original Madagascar dependency, or C++ dependency.
- Seismic Topic S6-1: Radon/slant Source-Aligned Design completed as a
  documentation-only source audit and route decision. It audits the current
  direct time-domain Radon forward/adjoint prototype against
  `../src-master/system/seismic/Mslant.c`, `slant.c`, `Mradon.c`, and
  `radon.c`, then selects a two-stage route: first an `sfslant`-style small
  slant-stack contract/validation pass, later a separate high-resolution
  `sfradon` design only after operator/inversion foundations are ready. It
  adds no algorithm, feature command, CLI module, console script, stable public
  API, workflow, test, command-surface coverage, XMind update, original
  Madagascar dependency, or C++ dependency.
- Seismic Topic S6-2: Small Slant-Stack Contract Hardening and Validation
  completed. It hardens the existing direct time-domain Radon/slant prototype
  for finite small gathers, positive finite time/offset/p-axis sampling,
  length-compatible explicit offset vectors, finite model/data samples, and
  clearer operator metadata. `radon` remains the adjoint slant-stack direction
  `m=A^T d`; `iradon` remains deterministic modeling `d=A m`, not a solved
  inverse. S6-2 adds `tests/test_seismic_slant_stack_contract.py` and
  `examples/my_workflows/seismic_slant_stack_contract_workflow.py`, but no new
  algorithm, feature command, CLI module, console script, stable public API,
  command-surface coverage, XMind update, original Madagascar dependency, or
  C++ dependency.
- Seismic Topic S7-0: Closeout and Handoff to Inversion/Operator Topic
  completed as a documentation-only route decision. It closes Seismic Topic v0
  as a fixture-backed small-gather regression harness, recommends pausing
  seismic work before S6-3/high-resolution `sfradon`/velocity picking, and
  selects Inversion / Operator Foundation as the next topic. It adds no
  algorithm, feature command, CLI module, console script, stable public API,
  workflow, test, example, command-surface coverage, XMind update, original
  Madagascar dependency, or C++ dependency.
- Inversion / Operator Foundation I0-0: Current Capability Audit and Contract
  Design completed as a documentation-only pass. It audits the existing B-4
  `LinearOperator`, `MatrixOperator`, `CallableLinearOperator`, real/complex
  dot tests, real/complex conjugate-gradient and normal-equation helpers,
  Radon forward/adjoint pair, D-1 workflow-only least-squares helper,
  acoustic2d/Kirchhoff prototype boundaries, and Madagascar dottest/conjgrad
  source references. It defines initial inversion data/operator/solver
  contracts and selects operator composition plus history contracts as the next
  bounded task. It adds no algorithm, solver, feature command, CLI module,
  console script, stable public API, workflow, test, example, command-surface
  coverage, XMind update, original Madagascar dependency, or C++ dependency.
- Inversion / Operator Foundation I0-1: Operator Composition and History
  Contract Foundation completed. It adds small in-memory `ScaledOperator`,
  `SumOperator`, `ComposedOperator`, and `StackedOperator` composition
  primitives plus internal/prototype `SolverIterationRecord`, `SolverHistory`,
  and `SolverResult` diagnostics containers in
  `pymadagascar.generic.linear_operator`. Existing CG helpers keep their
  return contract and are not wired to the new history containers. I0-1 adds
  `tests/test_operator_composition_contract.py` and
  `tests/test_solver_history_contract.py`, but no geophysical algorithm,
  solver, feature command, CLI module, console script, stable root/API export,
  workflow, command-surface coverage, XMind update, original Madagascar
  dependency, or C++ dependency.
- Inversion / Operator Foundation I0-2: Regularization Operator Subset
  completed. It adds small in-memory `DiagonalRegularization`,
  `FirstDifferenceRegularization`, and `SecondDifferenceRegularization`
  operators in `pymadagascar.generic.linear_operator`; damping continues to be
  expressed as a scaled `IdentityOperator`. The first- and second-difference
  operators use flattened valid-boundary stencils and exact matching adjoints.
  I0-2 adds `tests/test_regularization_operator_contract.py`, but no
  geophysical algorithm, solver, CGLS/LSQR, feature command, CLI module,
  console script, stable root/API export, workflow, command-surface coverage,
  XMind update, original Madagascar dependency, or C++ dependency.
- Inversion / Operator Foundation I0-3: Objective / Residual / Diagnostics
  Problem Layer completed. It adds small in-memory `LeastSquaresProblem`,
  `ObjectiveDiagnostics`, and `StoppingDiagnostics` prototype structures in
  `pymadagascar.generic.linear_operator`. The problem layer evaluates
  unregularized and regularized residuals, objective terms, total residuals,
  normal-equation gradients, stopping diagnostics, and
  SolverHistory/SolverResult-compatible summaries. I0-3 adds
  `tests/test_inversion_problem_contract.py` and
  `tests/test_objective_diagnostics_contract.py`, but no geophysical
  algorithm, solver, CGLS/LSQR, feature command, CLI module, console script,
  stable root/API export, workflow, example, command-surface coverage, XMind
  update, original Madagascar dependency, or C++ dependency.
- Inversion / Operator Foundation I0-4: Solver Diagnostics Integration and
  CGLS/LSQR Design completed. It adds direct-module prototype helpers
  `run_cg_with_history` and `run_cgnr_with_history` over the existing CG core.
  Ordinary CG records linear-system residual energy; CGNR records augmented
  least-squares residual/objective diagnostics through `LeastSquaresProblem`
  while retaining normal-equation residual stopping. Existing solver
  functions, `ConjugateGradientResult`, and CLI output remain unchanged. I0-4
  audits and designs, but does not implement, CGLS or LSQR. It adds no solver
  algorithm, CLI module, console script, stable root/API export, workflow,
  example, command-surface coverage, XMind update, original Madagascar
  dependency, or C++ dependency.
- Inversion / Operator Foundation I0-5: Bounded Unpreconditioned CGLS
  completed. Direct-module prototypes `run_cgls` and `run_cgls_problem`
  consume `LinearOperator`-compatible inputs or an existing
  `LeastSquaresProblem`, return the existing `SolverResult`/`SolverHistory`
  contract, support real and complex Hermitian-adjoint problems, and stop on a
  relative initial normal-residual threshold. Active regularization is the
  existing augmented system `[A; lambda L] x ~= [b; 0]` through
  `StackedOperator`; no second regularization path is introduced. I0-5 adds no
  CLI, console script, stable root/API export, LSQR, preconditioner, workflow,
  domain inversion, coverage entry, XMind update, original Madagascar
  dependency, or C++ dependency.
- Inversion / Operator Foundation I0-6: Preconditioner Contract Design
  completed. Direct-module prototypes `Preconditioner`,
  `IdentityPreconditioner`, `DiagonalPreconditioner`,
  `PreconditionerDiagnostics`, and `as_preconditioner` define an explicit
  right/model-space transform `x = M z` with required forward/Hermitian-
  adjoint actions, shape/finite checks, nonzero diagonal scaling, and JSON-safe
  diagnostics. Preconditioning changes variables/scaling, while
  regularization changes the objective. At introduction, no solver consumed
  this contract and `run_cgls` was unchanged. I0-6 adds no solver, LSQR, CLI,
  stable export, coverage entry, learning-notebook update, constraint/mask, or
  domain inversion.
- Inversion / Operator Foundation I0-8A/I0-8B: Right-preconditioned CGLS
  prototype integration completed. `run_cgls` and `run_cgls_problem` now accept
  optional right/model-space preconditioners and solve `min_z 0.5 ||A M z -
  b||^2`, with active regularization using `[A M; lambda L M] z ~= [b; 0]`.
  Results remain model-space `final_model = M z_final`; diagnostics/objective
  remain owned by `LeastSquaresProblem`. I0-8B clarifies metadata by separating
  latent-space convergence normal residuals from model-space gradients and by
  carrying preconditioner diagnostics into solver metadata/history. This remains
  a direct-module prototype with no LSQR, CLI, stable root/API export,
  constraint/mask, production scaling, or domain inversion.
- Inversion / Operator Foundation I0-9B1: Bounded unpreconditioned /
  regularized LSQR prototype completed. `run_lsqr` and `run_lsqr_problem` are
  pure-Python direct-module helpers for small deterministic least-squares
  problems. They use a Golub-Kahan bidiagonalization recurrence, reuse the same
  `[A; lambda L] x ~= [b; 0]` augmented regularization path as CGLS, and keep
  nonzero `x0` as a model-space initial model through a shifted residual
  correction solve. This adds no CLI, console script, stable root/API export,
  right-preconditioned LSQR, left weighting, constraints/masks, production
  scaling, coverage denominator change, or domain inversion.
- Inversion / Operator Foundation I0-9C: LSQR learning guide and minimal example
  closure completed. `examples/my_workflows/lsqr_minimal_example.py` now gives a
  tiny in-memory comparison between bounded LSQR and dense least squares,
  including `LeastSquaresProblem` and regularized shifted-`x0` usage. The
  learning notebook now explains the small-problem CGLS/LSQR relationship,
  augmented regularization, shifted residual semantics, and the current
  preconditioned-LSQR boundary. This adds no solver implementation change, CLI,
  stable root/API export, right-preconditioned LSQR, command coverage, coverage
  denominator change, original Madagascar dependency, or production inversion
  claim.
- Localization Topic L0-1: Travel-time primitives and grid-search prototype
  completed. It starts the localization topic with
  `pymadagascar.localization.traveltime`, a pure-Python prototype module for
  finite small 2D local-coordinate problems. It provides direct and
  source-diffractor-receiver kinematic travel times, observed-minus-predicted
  residuals, and a deterministic x-z grid-search point-location result
  contract. The source audit found related Madagascar raytrace/eikonal/
  diffraction/traveltime sources, but L0-1 is not a complete Madagascar command
  clone. It adds no CLI, root/stable API export, automatic picking, real-data
  reader, uncertainty, imaging, field-performance claim, command coverage, or
  coverage denominator change.
- Localization Topic L0-2: Variable-velocity grid-search prototype completed.
  It extends `pymadagascar.localization.traveltime` with
  `grid_search_point_location_velocity_2d` and
  `VariableVelocityLocalizationGridSearchResult` for finite small 2D
  source-diffractor-receiver localization when homogeneous velocity is also
  unknown. The prototype supports either bounded closed-form slowness
  estimation or an explicit positive velocity grid, returning 2D
  `objective_grid` and selected-velocity grids with observed-minus-predicted
  residuals. It remains a direct-module pure-Python prototype with no CLI,
  root/stable API export, automatic picking, uncertainty, real-data reader,
  imaging, field-performance claim, command coverage, or coverage denominator
  change.

The route is now topic-oriented. D-1 stays as a bounded workflow prototype and
D-2A adds a workflow-only geometry metadata contract without starting DAS file
adapters. S1 establishes canonical trace/panel/gather data and
regular geometry; S2 establishes deterministic pipeline metrics and QC-report
acceptance using existing functionality; S3 hardens the existing NMO prototype
inside those boundaries. S4-0 adds the source-alignment rule: when a
Madagascar classic source exists, audit it before hardening the Python
prototype. S4-1 applies that rule to Semblance while keeping it a bounded
prototype, not a full `sfvscan` clone. S4-2 adds the small-gather geometry
adapter contract needed before broader FK/Radon/localization/imaging/inversion
work, while still excluding SEG-Y trace headers and production survey geometry.
S4-3 applies the source-alignment rule to the current Python FK/FK-filter
prototype without claiming a full `sfdipfilter` clone. S5 closes the first
small-gather loop by combining the existing contracts into one integrated
workflow, without adding algorithms or promoting prototype maturity. S6-0
closes Seismic Topic v0 as a documentation-only decision point: the first
recommended next pass is Radon/slant source-aligned design, followed by a
minimal velocity-picking design only after the Radon/slant boundary is clear.
S6-1 completes that Radon/slant design pass and keeps the current Pythonic
Radon pair separate from both `sfslant` and high-resolution `sfradon`. S6-2
then hardens the small `sfslant`-style shared subset with analytic slant-event
validation, dot-test consistency, regular/explicit offset checks, path-free
workflow JSON, and clear failure behavior. S7-0 formally closes Seismic Topic
v0 and hands off the next route to Inversion / Operator Foundation. I0-0 starts
that topic as audit/design only. I0-1 implements the first bounded foundation:
shape-checked in-memory scale/sum/composition/vertical-stack operators and an
internal/prototype solver-history/result schema. I0-2 adds the first reusable
small in-memory regularization subset. I0-3 adds the small objective/residual/
diagnostics problem layer. I0-4 optionally connects that layer to the existing
CG core and completes CGLS/LSQR design. I0-5 implements bounded
unpreconditioned CGLS. I0-6 defines right/model-space preconditioning,
I0-8A/I0-8B connect that contract to the CGLS prototype with explicit
latent/model-space diagnostics, and I0-9B1 adds bounded unpreconditioned /
regularized LSQR. I0-9C adds the minimal LSQR learning example and notebook
section while leaving right-preconditioned LSQR, stable solver APIs, and domain
inversions for later passes. Broad
velocity picking, high-resolution or solved Radon inversion, FK algorithm
expansion, production localization, modeling solver expansion, and imaging remain
outside the current pass. Localization now has L0-1/L0-2 small travel-time and
fixed/variable-velocity grid-search primitives only; forward modeling now has
F0-1 through F0-6 geometry, shot/survey, tensor, synthetic velocity-model
helpers, and a deterministic validation workflow only, and imaging and
SEG-Y/header expansion remain deferred. Hybrid
benchmarking, B-3-3 `sfsegyheader`, release, licensing, and tagging remain
separate.

## Topic Capability Overview

| Topic | Current maturity | T1 decision | Largest shortfall |
| --- | --- | --- | --- |
| Seismic data signal analysis and processing | stable subset, with prototype NMO/Semblance/FK/Radon | S1 contracts, S2 metrics/QC, S3 NMO hardening, S4-0 source alignment, S4-1 Semblance hardening, S4-2 small-gather geometry design, S4-3 FK validation, S5 integrated workflow, S6-0/S6-1 route decisions, S6-2 small slant-stack hardening, and S7-0 closeout complete; pause by default | field-scale/non-regular geometry, multi-gather validation, velocity picking, high-resolution Radon, and production processing |
| DAS / engineering workflows | workflow-only | D-1 kinematic road-void workflow, D-2A workflow-only geometry metadata contract, and D-2B package-level localization grid-search integration complete; no adapter | DAS file adapters, field fixtures, gauge response, automatic picking, uncertainty, and field-performance validation |
| Localization | prototype | L0-1 pure-Python 2D travel-time/fixed-velocity grid-search primitives and L0-2 homogeneous variable-velocity grid-search prototype complete; no CLI/root API | pick records, uncertainty, identifiability, richer velocity-model interfaces, and production workflows |
| Inversion / operators | partial / prototype | I0-1 composition/history, I0-2 regularization, I0-3 problem diagnostics, I0-4 diagnostics/design, I0-5 bounded CGLS, I0-6 right/model-space preconditioner contract, I0-7 module split, I0-8A/I0-8B right-preconditioned CGLS diagnostics, I0-9B1 bounded unpreconditioned/regularized LSQR, and I0-9C LSQR learning example/notebook closure complete | Right-preconditioned LSQR, stable/root solver API, constraints/masks, and domain inversion workflows |
| Forward modeling | simplified prototype | F0-1 through F0-6 geometry, shot/survey, tensor, synthetic velocity-model helpers, and smoke validation workflow complete; no solver-core change or root API | physical-coordinate interpolation, smoothing/random/geologic model building, convergence/dispersion accuracy evidence, production workflows, and production-scale modeling |
| Imaging | simplified prototype | defer | acquisition, adjoint, amplitude, and reference validation |
| SEG-Y / headers | stable RSF / partial headers / prototype SEG-Y | independent defer | trace ownership, scalars/units, synchronized reorder |
| Plot / visualization | partial quicklook substitute | support work only | composition, overlays, and domain QC presentation |
| General RSF / data processing | stable / stable subset | freeze except topic-driven gaps | streaming and out-of-core execution |
| Statistics QC / spectral QC | stable subset | cross-cutting validation support | grouped/weighted/confidence and streaming behavior |

The full per-topic data, geometry, validation, first-batch, non-goal, and
documentation contracts are maintained in `COVERAGE_AND_ROADMAP.md`.

## Module Overview

- `pymadagascar/io`: RSF header/sidecar I/O and small SEG-Y 2D prototype.
- `pymadagascar/core`: `Axis`, `Hypercube`, and `RSFParams`.
- `pymadagascar/cli`: 135 module entry points, 28 registered console scripts.
- `pymadagascar/generic`: spike/math/window/info/put/attr, file ops, stats,
  array math, interleave, header mask/window/cut, byte, mask/cut/reverse/rotate,
  minimal header table attr/math/sort, linear operators, composition helpers,
  regularization operators, least-squares problem diagnostics, optional
  CG/CGNR history adapters, internal solver-history containers, dottest/conjgrad,
  generic sampling/bin/slice/max1 tools, whole-dataset difference metrics,
  unary transforms, histogram/quantile QC, robust statistics, non-finite
  masks/filling, complex tools, dd, pad/spray/tile, cat/transp.
- `pymadagascar/signal`: FFT, filters, smoothing, convolution/correlation,
  circular/envelope correlation, shifts, axis calculus, amplitude clipping,
  wavelets, signal preprocessing, demean/detrend, integer decimation,
  band-stop/notch filtering, local-RMS QC, standard windows, periodogram
  PSD/CSD, short-segment coherence, spectrogram, SNR, Welch PSD/CSD, H1/H2
  transfer estimates, spectral whitening/normalization, and frequency
  attributes, plus FIR design/filtering, response QC, band energy, and filter
  banks.
- `pymadagascar/seismic`: gain, AGC, mute/mutter, stack, NMO, semblance, FK,
  Radon.
- `pymadagascar/localization`: L0-1/L0-2 pure-Python prototype travel-time
  primitives plus deterministic 2D x-z fixed-velocity and homogeneous
  variable-velocity grid-search point localization for small local-coordinate
  fixtures; not a root/stable API or CLI surface.
- `pymadagascar/imaging`: simplified Kirchhoff prototype.
- `pymadagascar/modeling`: simplified acoustic2d prototype with topic-level
  geometry, shot/survey, tensor, synthetic velocity-model helpers, and a
  workflow-level validation example.
- `pymadagascar/plot`: Matplotlib quicklook replacements.
- `pymadagascar/hybrid`: optional C++ wrappers with NumPy fallback.
- `pymadagascar/testing`: fixtures, internal seismic regression metrics,
  internal small-gather geometry helpers, RSF comparisons, and the optional
  binary-safe original Madagascar command runner.
- `tools`: package/release, CLI runtime/docs command, live examples inventory,
  learning-notebook inventory, and optional WSL checks; live checks
  intentionally exclude `archive_docs`.

## Learning Notebook

`docs/PYMADAGASCAR_LEARNING_GUIDE.ipynb` is the study-oriented learning entry
point, not a replacement for the eight authoritative Markdown documents and
not a coverage authority. It replaces the former XMind visual index so the
project has a text-reviewable, gradually extensible guide. Codex should
consider updating it when a future change adds a user-visible capability,
algorithm topic, important workflow, usage pattern, or formula explanation.
Small internal refactors do not need notebook churn.
`tools/check_learning_notebook.py` validates the notebook with lightweight
static JSON checks and does not execute notebook cells.

## Hybrid Status

The current machine has no compiled C++ extension. `pymadagascar.hybrid`
reports the NumPy fallback backend. C++ sources exist, but compiling and
benchmarking C++ is not part of the current baseline. Default editable install
builds a pure-Python wheel and does not invoke CMake; C++ requires an explicit
opt-in build.

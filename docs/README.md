# pymadagascar Documentation

This directory is the current documentation entry point for pymadagascar.

pymadagascar is a Python-friendly local RSF/geophysics toolkit. It is not a
complete Madagascar clone. The current direction is to keep pure Python usable,
tested, and documented while developing selected capabilities through bounded
technical topics.

## Current Authority

Read these files first:

- `PROJECT_STATUS.md`: current project state, counts, test result, hybrid
  status, and stage progress.
- `USER_GUIDE.md`: local install, CLI usage, Python API usage, examples, and
  release tools.
- `API_SURFACE.md`: public surface inventory for root APIs, topic APIs,
  `RSFData` chains, CLIs, console scripts, workflows, and coverage boundaries.
- `API_AND_COMPATIBILITY.md`: API stability levels and compatibility notes.
- `COVERAGE_AND_ROADMAP.md`: coverage summary, completed batches, and next
  migration direction.
- `TESTING_AND_ENVIRONMENT.md`: pytest, optional original Madagascar
  comparisons, WSL notes, hybrid build notes, and release checks.
- `KNOWN_LIMITATIONS.md`: concise list of important current limitations.
- `CHANGELOG.md`: local baseline change history.

The learning entry point is `PYMADAGASCAR_LEARNING_GUIDE.ipynb`. It is a
Jupyter Notebook for study and usage orientation, not an authority for API or
coverage. The nine Markdown files above remain the authoritative written
documentation.

## Archived Documents

Older handoff files, long audit snapshots, batch-plan snapshots, and pre-slimming
compatibility documents were moved outside `docs/` to:

```text
archive_docs/docs_before_slimming_2026-06-09/
```

Those archived files are historical reference only. The release and docs command
checks scan current `docs/` plus `examples/`; they do not scan `archive_docs/`.

## Current Baseline

- CLI modules: 167.
- Registered `pymada-*` console scripts: 65.
- Full command-surface coverage: `129 / 2114 = 6.10%`.
- Core `system/` + `plot/main` coverage: `116 / 301 = 38.54%`.
- Direct `system/main` source-backed count: `37 / 39 = 94.87%`.
- Pytest files: 100.
- Top-level examples: 34, plus 16 workflow scripts and 1 workflow helper.
- Learning notebook: `PYMADAGASCAR_LEARNING_GUIDE.ipynb`, maintained as a
  study-oriented guide rather than an API or coverage authority.
- Windows pytest: `1185 passed, 95 skipped`.
- Skips: 94 optional original Madagascar comparisons and 1 optional C++
  extension test.
- WSL `ubuntu2204` pytest: `1006 passed, 94 skipped, 1 warning`.
- Last dedicated WSL original marker baseline: `66 passed, 27 skipped`; no
  comparison bridge failures.
- Quality Pass Q1: completed with RSFData contract tests, full top-level
  example smoke coverage, naming/compatibility notes, and examples inventory
  release checks.
- Stage C-5: completed with unary transform conveniences plus histogram and
  quantile distribution-QC subsets.
- Release Quality Pass Q2: completed with a successful pure-Python editable
  install, package metadata checks, all-CLI help smoke, output policy, and
  strengthened release tooling.
- Stage C-6: completed with robust global/axis statistics and explicit
  NaN/Inf mask/fill utilities; only the directly corresponding `sfmedian`
  surface changes command coverage.
- Roadmap Reassessment R1: completed with a ten-topic capability matrix,
  explicit stable-subset/prototype boundaries, and ranked next-route options.
  No commands or coverage entries were added.
- Stage D-1: completed with a kinematic DAS road-void diffraction workflow,
  existing FK/plot reuse, simulated-pick least-squares inversion, and focused
  temporary-output tests. Coverage remains unchanged.
- Stage C-7: completed with demean/detrend, integer decimation, zero-phase
  band-stop/notch filtering, and centered local-RMS QC conveniences. Six
  module-only CLIs and one focused demo were added; conservative command
  coverage remains unchanged.
- Stage C-8: completed with standard windows, periodogram PSD/CSD,
  short-segment spectral coherence, axis-1 spectrogram, and explicit-window
  RMS SNR conveniences. Six module-only CLIs and one focused demo were added;
  conservative command coverage remains unchanged.
- Stage C-9: completed with Welch PSD/CSD, H1/H2 transfer estimates, spectral
  whitening/normalization, and dominant/centroid/bandwidth attributes. Six
  module-only CLIs and one focused demo were added; conservative command
  coverage remains unchanged.
- Stage C-10: completed with windowed-sinc FIR design, centered FIR and
  forward/reverse filtering, FIR response QC, explicit band-energy QC, and a
  small FIR filter bank. Six module-only CLIs and one focused demo were added;
  conservative command coverage remains unchanged.
- Mindmap Documentation Pass M1: added an XMind feature map plus repository
  inventory validation. No command, API, example, or coverage value changed.
- Topic Architecture Pass T1: ended automatic Stage C batch continuation,
  selected seismic data signal analysis and processing as the first topic, and
  defined data, geometry, validation, and non-goal boundaries for ten topics.
  No command, API, example, mindmap, or coverage value changed.
- Seismic Topic S1: added internal deterministic trace/panel/gather fixtures,
  a regular signed-offset contract workflow, and pipeline regression tests
  using existing processing APIs. No feature command, CLI module, console
  script, stable API, XMind content, or coverage value changed.
- Seismic Topic S2: added internal deterministic pipeline metrics, a structured
  QC report workflow, and focused validation for SNR, frequency bands, mute,
  stack noise, finite values, and axis/header preservation. It adds no feature
  command, CLI module, console script, stable API, XMind content, or coverage
  value.
- Seismic Topic S3: hardened the existing NMO prototype against the S1/S2
  regular signed-offset fixture and metrics, added deterministic correct-vs-
  wrong velocity regression, and documented NMO data/geometry/validation
  limits. It adds no feature command, CLI module, console script, stable API,
  XMind content, or coverage value.
- Seismic Topic S4-0: completed a Madagascar source-alignment audit for NMO,
  Semblance, FK/FK-filter, and Radon, and selected Semblance as the next
  bounded hardening target. It adds no feature command, CLI module, console
  script, stable API, test, example, workflow, XMind content, or coverage value.
- Seismic Topic S4-1: hardened the existing Semblance prototype against
  `../src-master/system/seismic/Mvscan.c` and the S1/S2/S3 fixture base,
  added deterministic velocity-panel/true-vs-wrong regression, and documented
  data/geometry/validation limits. It adds no feature command, CLI module,
  console script, stable API, XMind content, or coverage value.
- Seismic Topic S4-2: added an internal/testing small-gather geometry contract
  helper, deterministic tests, and a workflow covering regular signed-offset
  RSF axes, explicit offset vectors, and a minimal numeric source/receiver
  table. It adds no feature command, CLI module, console script, stable API,
  XMind content, or coverage value.
- Seismic Topic S4-3: source-aligned the existing FK prototype against the
  absence of a direct `Mfk.c` and the nearest `Mdipfilter.c` dip/f-k/fan-filter
  reference, hardened finite axis/data/parameter checks, and added plane-wave
  FK peak plus fan-filter regression. It adds no feature command, CLI module,
  console script, stable API, XMind content, or coverage value.
- Seismic Topic S5: added an integrated small-gather processing workflow and
  tests that combine existing S1/S2/S3/S4 fixture, metrics, geometry, NMO,
  Semblance, and FK prototype contracts into one deterministic internal JSON
  regression. It adds no algorithm, feature command, CLI module, console
  script, stable API, XMind content, or coverage value.
- Seismic Topic S6-0 and S6-1: summarized Seismic Topic v0, audited current
  Radon/slant against `Mslant.c`/`slant.c` and `Mradon.c`/`radon.c`, and chose
  the small `sfslant`-style slant-stack contract before any high-resolution
  `sfradon` or velocity-picking work. These passes add no command, workflow,
  test, stable API, XMind content, or coverage value.
- Seismic Topic S6-2: hardened the existing Radon/slant prototype for the
  small slant-stack subset, clarified `radon` as `m=A^T d` and `iradon` as
  `d=A m`, added deterministic slant-stack tests and a workflow JSON report,
  and kept high-resolution `sfradon` and solved inversion out of scope. It adds
  no algorithm, feature command, CLI module, console script, stable API, XMind
  content, or coverage value.
- Seismic Topic S7-0 and Inversion / Operator Foundation I0-0: closed Seismic
  Topic v0 as a fixture-backed small-gather regression harness, selected
  Inversion / Operator Foundation as the next topic, and recorded the initial
  operator/data/solver contracts. These passes add no command, solver,
  workflow, stable API, XMind content, or coverage value.
- Inversion / Operator Foundation I0-1: added small in-memory operator
  composition and internal/prototype solver history/result contracts in the
  existing `pymadagascar.generic.linear_operator` module. It adds no CLI,
  console script, new solver, XMind content, or command-surface coverage.
- Inversion / Operator Foundation I0-2: added a small in-memory
  regularization-operator subset in the same direct module: diagonal,
  first-difference, and second-difference operators, while damping reuses the
  existing scaled identity operator. It adds no CLI, console script, new
  solver, root/API export, XMind content, or command-surface coverage.
- Inversion / Operator Foundation I0-3: added a small in-memory least-squares
  problem/objective/diagnostics layer in the same direct module, connecting
  operators, regularization residuals, objective terms, gradient diagnostics,
  stopping diagnostics, and SolverHistory/SolverResult-compatible summaries.
  It adds no CLI, console script, new solver, root/API export, XMind content,
  or command-surface coverage.
- Inversion / Operator Foundation I0-4: added optional direct-module
  `run_cg_with_history` and `run_cgnr_with_history` adapters over the existing
  CG core, while preserving every default solver/CLI return contract. It also
  records a source-backed CGLS/LSQR design without implementing either solver.
  No CLI, console script, stable root/API export, XMind content, or
  command-surface coverage was added.
- Inversion / Operator Foundation I0-5: added bounded unpreconditioned
  `run_cgls` and `run_cgls_problem` direct-module prototypes for small real or
  complex in-memory least-squares problems. They reuse `LeastSquaresProblem`,
  `StackedOperator`, existing regularization operators, `SolverHistory`, and
  `SolverResult`. No CLI, stable root/API export, LSQR, preconditioner, domain
  inversion, XMind content, or command-surface coverage was added.
- Inversion / Operator Foundation I0-6: added only a direct-module
  right/model-space preconditioner contract: semantic base and diagnostics,
  identity and invertible diagonal transforms, and explicit normalization.
  It does not change `run_cgls`, implement a preconditioned solver or LSQR,
  export a stable API, add a CLI, update XMind, or change coverage.

The D-1 workflow remains a prototype, and D-2 is not the current route. The
continuous Stage C small-batch sequence ends at C-10; C-11 is not recommended.
The first topic is seismic data signal analysis and processing, beginning with
trace/panel/gather contracts, geometry fixtures, and pipeline validation rather
than new commands. SEG-Y trace-header work, DAS adapters, forward algorithms,
general inversion, and imaging remain separate later topics.

S1, S2, S3, S4-0, S4-1, S4-2, S4-3, S5, S6-0, S6-1, S6-2, S7-0, I0-0, I0-1,
I0-2, I0-3, I0-4, I0-5, I0-6, and I0-8A are complete. Current topic inventory
and contracts are maintained in the Markdown authorities; the learning notebook
is a guided study layer.

WSL-1 validated `ubuntu2204`, the `pymadagascar-dev` Conda environment, and
Madagascar 4.2-git. Original comparisons remain optional compatibility checks:
they skip on Windows without upstream commands and run in WSL when requested.

# Testing and Environment

## Local Interpreter

Use:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe
```

This is the validated local baseline path, not a portable requirement. On
another machine, substitute the Python interpreter from that machine's project
environment.

Plain `python` is not available on the current PowerShell PATH in this Codex
session.

## Required Checks

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q -rs
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_release.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_cli_inventory.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_docs_commands.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_examples_inventory.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_learning_notebook.py
```

Latest result:

```text
1006 passed, 94 skipped
```

## Skip Reasons

- 93 optional original Madagascar comparison tests skip because required
  upstream `sf*` commands are not installed or not on Windows PATH.
- 1 optional C++ extension test skips because `pymadagascar._core` is not
  compiled.

Pure Python tests must not depend on original Madagascar, WSL, or C++.

## Original Madagascar Comparisons

Tests marked `original_madagascar` are optional. Run only the marker with:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q -rs -m original_madagascar
```

Current Windows/Codex result:

```text
93 skipped
```

Use these tests on a machine where upstream `sf*` programs are available through
`PATH` or `$RSFROOT/bin`. The runner uses upstream pipe semantics with explicit
`stdin_path` and `stdout_path`. Binary stdout is bytes by default; text-only
commands request decoding explicitly. Redirected RSF sidecars are written
beside the pytest output header instead of leaking into a global DATAPATH.
Older upstream behavior should be recorded as a version or designed-subset
difference, not used to weaken pure Python tests.

## WSL ubuntu2204

The validated WSL distribution is `ubuntu2204`, user `hcz`, Ubuntu 22.04.3
LTS/WSL2. The project environment is
`/home/hcz/Software/Anaconda/envs/pymadagascar-dev` with Python 3.11, and
Madagascar 4.2-git is installed under `/home/hcz/Software/Madagascar`.

PowerShell checks:

```powershell
wsl -l -v
wsl -d ubuntu2204
```

Inside WSL:

```bash
conda activate pymadagascar-dev
cd /mnt/e/HczDocument/BaiduDisk/BaiduSyncdisk/HCZ_work/CodexProject/HCZ_madagascar/hcz_mada
python -m pytest -q
python -m pytest -q -rs -m original_madagascar
python -m pytest -q -rs
python tools/check_release.py
python tools/check_cli_inventory.py
python tools/check_docs_commands.py
python tools/check_examples_inventory.py
python tools/check_learning_notebook.py
python tools/check_wsl_madagascar.py --strict
```

Windows-side probe:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_wsl_madagascar.py
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_wsl_madagascar.py --strict
```

The probe supports `--distro`, `--user`, `--shell auto|bash|zsh`,
`--conda-env`, and `--strict`. Auto mode detects the login shell; this matters
because RSFROOT is currently loaded by zsh. The probe transports its script as
base64 so Windows-to-WSL quoting cannot corrupt shell variables. The recurring
localhost proxy warning is informational and does not invalidate the probe.
`PYMADAGASCAR_WSL_USER` and `PYMADAGASCAR_WSL_CONDA_ENV` can provide local
defaults without editing the tracked script; command-line options take
precedence.

Current WSL results:

```text
full suite:                 1006 passed, 94 skipped, 1 warning
original_madagascar only:   66 passed, 27 skipped (last dedicated marker baseline)
```

The full-suite warning is the known mounted-drive `.pytest_cache` permission
warning when running from `/mnt/e`; pytest exits successfully. Marker skips are
explicit unavailable-command or intentionally non-comparable subset cases.
There are no remaining bridge failures or real comparison mismatches.

## Hybrid C++

Hybrid is optional. Default install uses `wheel.cmake=false` and keeps
`PYMADAGASCAR_BUILD_CPP=OFF`, so editable install does not run CMake or require
Ninja/a compiler.

Validated pure-Python install:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install -e ".[test]" --no-build-isolation
```

The resulting editable wheel is `py3-none-any`. Optional C++ compilation must
explicitly install the `cpp` extra and enable both CMake wheel building and the
C++ define; it is outside the release baseline.

Fallback state:

- `pymadagascar.hybrid.cpp_available()` is `False` on the current machine.
- Backend is NumPy fallback.
- Existing C++ kernels are for array add/scale and batch cross-correlation.

Do not add or require C++ without a Python fallback, benchmark, and tests.

## Release Tool Scope

- `tools/check_release.py`: package metadata, import/public API, all CLI
  targets, docs/examples, output policy, and fallback smoke.
- `tools/check_cli_inventory.py`: checks docs inventory and imports all 134 CLI
  modules, verifies callable `main()` functions and `__main__` guards, and
  resolves all 25 console-script targets.
- `tools/check_docs_commands.py`: scans current `docs/` and `examples/` for
  unregistered `pymada-*` names. It intentionally does not scan `archive_docs/`.
- `tools/check_examples_inventory.py`: checks all 34 top-level examples and
  fourteen workflows for syntax, main guards, pymadagascar import targets,
  output-directory/tempfile behavior, absolute path literals, and live-doc
  inventory agreement. It does not scan `archive_docs/`.
- `tools/check_learning_notebook.py`: validates
  `docs/PYMADAGASCAR_LEARNING_GUIDE.ipynb` with lightweight static JSON
  checks. It verifies notebook presence, nbformat metadata, Markdown-heavy
  structure, required learning topics, absence of local absolute paths, no
  saved outputs, and current `PROJECT_STATUS.md` learning-notebook inventory.
  It does not execute notebook cells.
- `tools/check_wsl_madagascar.py`: optional Windows-side WSL Madagascar probe.
  Unavailable WSL or missing upstream commands return success by default;
  `--strict` makes the probe fail for environment diagnostics. Distro, user,
  shell, and Conda prefix are configurable.

## Risk-Based Testing Policy

Default testing level should match the risk of the change.

Small focused changes:

- run targeted pytest files for changed modules;
- run directly affected neighboring tests;
- run relevant release-light checks;
- run `git diff --check`.

Cross-cutting changes must still run full tests:

- operator foundation;
- RSF I/O;
- CLI registry;
- packaging / `pyproject.toml`;
- release tools;
- docs inventory;
- test infrastructure;
- CI workflow;
- module split / refactor;
- changes touching shared base classes or common utilities.

Topic completion / phase closure:

- run full Windows pytest;
- run full WSL pytest;
- run release-light tools;
- run `git diff --check`;
- optionally check GitHub Actions status.

Before commit/push:

- for low-risk narrow tasks, targeted tests may be accepted if explicitly justified;
- for medium/high-risk tasks, full local pytest is required;
- for release/tooling/doc-inventory changes, full local pytest and release-light
  checks are required.

Never silently skip failing tests. If a test is truly optional/external, skip
logic must be explicit and justified. Do not hide real failures by broad marker
exclusion.

Future Codex reports should include:

```text
Testing level used:
- targeted / affected / full

Reason:
- ...
```

Quality Pass Q1 adds:

- `tests/test_rsfdata_api_consistency.py` for method presence, non-mutating and
  inplace behavior, double-input operand types, and shape/header/dtype
  contracts.
- `tests/test_examples_inventory.py` for all 34 top-level examples. Every
  script runs in a subprocess with a pytest temporary output directory, and
  the test verifies that no new file is written into `examples/`.
- `tests/test_release_tools.py` coverage for the examples inventory tool.

Stage C-5 adds `tests/test_unary_distribution_qc_tools.py` for eight APIs,
eight subprocess CLIs, RSFData chaining/inplace behavior, shape/header/dtype
contracts, invalid/complex/non-finite behavior, and eight optional original
comparisons. The all-example smoke test now includes
`examples/unary_distribution_qc_demo.py`.

Release Quality Pass Q2 adds:

- `tests/test_package_metadata.py` for project identity, version, pure-Python
  default build, console-script metadata, authority docs, and ignore policy.
- `tests/test_cli_entrypoints.py` for all 102 imports and all-module
  `python -m ... --help` smoke.
- Installed-entrypoint smoke confirming all 25 generated `pymada-*.exe`
  launchers return success for `--help`.
- Optional WSL probe tests confirming default non-blocking and strict modes.

Stage C-6 adds `tests/test_robust_statistics_nan_tools.py` for global and
axis-wise mean/RMS/variance/std/median/range APIs, all eight subprocess CLIs,
NaN policy, complex mask/fill behavior, shape/header/dtype contracts, RSFData
inplace behavior, four optional `sfattr` comparisons, and one optional
`sfmedian` comparison. The all-example smoke test now includes
`examples/robust_statistics_nan_qc_demo.py`.

Roadmap Reassessment R1 changes documentation and roadmap classification only.
It adds no command, API, test, example, or coverage entry. The full regression
suite and all four release/inventory tools are still required after the docs
update; R1 verification completed with `619 passed, 88 skipped in 60.79s`.

Stage D-1 adds `tests/test_das_void_diffraction_workflow.py`. It verifies the
workflow-only travel-time and least-squares helpers, runs the workflow in a
pytest temporary directory, checks RSF/PNG/CSV/JSON outputs and geometry
metadata, requires less than 10% depth error, and confirms no new files are
written under `examples/`. The examples inventory now covers six workflows
plus one helper. The D-1 full-suite result is
`621 passed, 88 skipped in 64.38s`.

Stage C-7 adds `tests/test_signal_qc_foundation_tools.py` for demean/detrend,
integer decimation, band-stop/notch frequency behavior, local RMS, all six
subprocess CLIs, RSFData chaining/inplace behavior, metadata and dtype
contracts, invalid parameters, and six optional upstream markers. The
all-example smoke inventory now includes
`examples/signal_qc_foundation_demo.py`. D-1 remains covered, while D-2 is not
part of this test baseline.

WSL-1 adds binary/text/redirection/failure coverage to
`tests/test_testing_runner.py` and adds `tests/test_wsl_probe.py` for parser,
shell selection, base64 transport, strict/non-strict behavior, and direct-probe
success without requiring real WSL in ordinary unit tests.

Stage C-8 adds `tests/test_spectral_qc_tools.py` for six NumPy/file APIs, six
module-only CLIs, frequency/time-axis metadata, complex CSD, segment-averaged
coherence, explicit-window SNR, RSFData binary operands/inplace behavior, and
invalid/non-finite contracts. No original marker was added because the audited
upstream commands have different names or semantics. The all-example smoke
inventory now includes `examples/spectral_qc_demo.py`.

Stage C-9 adds `tests/test_spectral_averaging_attributes_tools.py` for Welch
PSD/CSD, H1/H2 transfer estimates, spectral whitening/normalization, frequency
attributes, all six module-only CLIs, RSFData second-operand/inplace behavior,
frequency-axis and complex-output metadata, and invalid/non-finite contracts.
No original marker was added because the audited upstream tools have different
names, input models, or output semantics. The all-example smoke inventory now
includes `examples/spectral_averaging_attributes_demo.py`.

Stage C-9 validation: Windows `699 passed, 94 skipped`; WSL
`765 passed, 28 skipped`; WSL original marker `66 passed, 27 skipped`. The
marker count is unchanged because all six C-9 surfaces are documented
Pythonic conveniences rather than forced upstream comparisons.

Stage C-10 adds `tests/test_fir_filter_design_tools.py` for four windowed-sinc
filter types, FIR and forward/reverse filtering, response metadata, explicit
band energy, filter-bank axes, six module-only CLIs, RSFData taps operand
forms/inplace behavior, finite/complex contracts, and invalid parameters. No
original marker is added because the related upstream Butterworth, `sfir`, and
interpolation-filter-bank contracts do not match these six conveniences.

Stage C-10 validation: Windows `721 passed, 94 skipped`; WSL
`787 passed, 28 skipped`; WSL original marker `66 passed, 27 skipped`. The
strict WSL probe and all four release/inventory tools pass in the validated
environment.

Mindmap Documentation Pass M1 adds `tests/test_mindmap_inventory.py` and a
release-tool subprocess check. Validation uses Python's standard-library XML
parser and repository inventory only; XMind, FreeMind, MindMaster, network
access, and GUI automation are not test dependencies. M1 validation results:
Windows `725 passed, 94 skipped`; WSL `791 passed, 28 skipped`; WSL original
marker `66 passed, 27 skipped`.

Topic Architecture Pass T1 is documentation-only. It adds no test or skip,
does not change coverage, and did not update the then-current visual index.
At that time, the full Windows and WSL suites, original marker,
release/inventory checks, visual-index check, and strict WSL probe remained the
required validation set.

Seismic Topic S1 adds `tests/test_seismic_signal_contracts.py` with 17 tests
covering trace/panel/gather headers, deterministic seeds, known hyperbolic and
plane-wave arrivals, Ricker peak time, finite values, invalid axes and regular
geometry, the existing-API pipeline, output isolation, and the absence of
original-Madagascar/C++ dependencies. Current validation results are Windows
`742 passed, 94 skipped`, WSL `808 passed, 28 skipped`, and WSL original marker
`66 passed, 27 skipped`. XMind is unchanged and its frozen-snapshot check
passes.

Seismic Topic S2 adds `tests/test_seismic_signal_metrics.py` with 16 tests
covering internal-only exports, deterministic trace/panel/pipeline metrics,
explicit windows and bands, SNR and frequency-band checks, mute and stack
effects, finite values, header-axis preservation, deterministic path-free JSON,
subprocess/default-temp behavior, negative inputs, output isolation, and the
absence of original-Madagascar/C++ dependencies. Current validation results are
Windows `758 passed, 94 skipped`, WSL `824 passed, 28 skipped`, and WSL original
marker `66 passed, 27 skipped`. XMind is unchanged and the frozen-snapshot/live
inventory check passes.

Inversion / Operator Foundation I0-5 adds `tests/test_cgls_contract.py` with
18 deterministic tests covering real/complex overdetermined systems, NumPy
least-squares agreement, zero/nonzero initial models, objective history,
`LeastSquaresProblem`, first-difference regularization through the augmented
system, JSON-safe summaries, tolerance/max-iteration stopping, invalid inputs,
optional history, no CLI/stable export, and continued LSQR/preconditioner
non-implementation. Current validation results are Windows
`983 passed, 94 skipped`, WSL `1049 passed, 28 skipped`, and WSL original
marker `66 passed, 27 skipped`. XMind and command coverage are unchanged.

Inversion / Operator Foundation I0-6 adds
`tests/test_preconditioner_contract.py` with 13 deterministic tests covering
identity and diagonal transforms, complex Hermitian adjoints, shape/finite/
nonzero-weight checks, semantic separation from regularization, right-
preconditioned operator/problem construction without solving, JSON-safe
diagnostics, conversion helpers, direct-module export boundaries, unchanged
`run_cgls`, and continued LSQR/preconditioned-solver non-implementation.
Current validation results are Windows `996 passed, 94 skipped`, WSL
`1062 passed, 28 skipped`, and WSL original marker `66 passed, 27 skipped`.
XMind and command coverage are unchanged.

Seismic Topic S3 adds `tests/test_seismic_nmo_contract.py` with 28 tests
covering the existing NMO prototype on the S1 hyperbolic signed-offset fixture,
correct-vs-wrong velocity behavior, event flattening, stack peak/timing, header
preservation, finite samples, invalid velocity/time/offset/stretch cases,
explicit offset vectors, existing CLI execution, deterministic path-free JSON,
workflow default-temp behavior, output isolation, and the absence of
original-Madagascar/C++ dependencies. Current validation results are Windows
`786 passed, 94 skipped`, WSL `852 passed, 28 skipped`, and WSL original marker
`66 passed, 27 skipped`. XMind is unchanged and the frozen-snapshot/live
inventory check passes.

Seismic Topic S4-0 is documentation-only and adds no tests, examples,
workflows, CLI modules, console scripts, stable APIs, coverage entries, or
XMind updates. It records a Madagascar source-alignment audit for NMO,
Semblance, FK/FK-filter, and Radon, and selects Semblance prototype contract
hardening as the next bounded task. Current validation results remain Windows
`786 passed, 94 skipped`, WSL `852 passed, 28 skipped`, and WSL original marker
`66 passed, 27 skipped`. Release, CLI inventory, docs-command, examples
inventory, mindmap, and strict WSL Madagascar checks pass.

Seismic Topic S4-1 adds `tests/test_seismic_semblance_contract.py` with 28
tests covering the `../src-master/system/seismic/Mvscan.c` source-audit path,
the existing Semblance prototype on the S1 signed-offset fixture, true-velocity
versus wrong-velocity behavior, velocity-panel shape/header metadata, finite
input/output, invalid velocity/time/offset/auxiliary parameters, existing CLI
execution, deterministic path-free JSON, workflow default-temp behavior, output
isolation, and the absence of original-Madagascar/C++ dependencies. Current
validation results are Windows `816 passed, 94 skipped`, WSL
`882 passed, 28 skipped`, and WSL original marker `66 passed, 27 skipped`.
XMind is unchanged and the frozen-snapshot/live inventory check passes.

Seismic Topic S4-2 adds `tests/test_seismic_geometry_contract.py` with 25
tests covering Madagascar geometry/source-boundary paths, regular signed-offset
axis metadata, explicit offset-vector shape and unit checks, deterministic
minimal source/receiver tables, ordinary-RSF/header-table/SEG-Y boundaries,
internal-only exports, no CLI/console-script addition, workflow subprocess and
default-temp behavior, output isolation, and the absence of
original-Madagascar/C++ dependencies. Current validation results are Windows
`841 passed, 94 skipped`, WSL `907 passed, 28 skipped`, and WSL original marker
`66 passed, 27 skipped`. XMind is unchanged and the frozen-snapshot/live
inventory check passes.

Seismic Topic S4-3 adds `tests/test_seismic_fk_contract.py` with 30 tests
covering Madagascar FK/dipfilter source-boundary paths, absence of a direct
`Mfk.c`, S1/S4-2-style regular plane-wave panels, analytic FK peak location,
positive/negative slope separation, fan-filter target preservation and reject
suppression, output shape/header/dtype metadata, finite input/output, invalid
time/spatial axes and parameters, existing FK/FK-filter CLI execution,
deterministic path-free JSON, workflow default-temp behavior, output
isolation, and the absence of original-Madagascar/C++ dependencies. Current
validation results are Windows `871 passed, 94 skipped`, WSL
`937 passed, 28 skipped`, and WSL original marker `66 passed, 27 skipped`.
XMind is unchanged and the frozen-snapshot/live inventory check passes.

Seismic Topic S5 adds `tests/test_seismic_integrated_workflow.py` with 7 tests
covering the integrated small-gather workflow report, RSF/PNG/JSON outputs,
geometry checks, S2-style pipeline metrics, S3 NMO true-vs-wrong behavior,
S4-1 Semblance peak behavior, S4-3 FK finite/header/energy checks, stack
metrics, subprocess/default-temp behavior, output isolation, no CLI/console
script addition, and the absence of original-Madagascar/C++ dependencies.
Current validation results are Windows `878 passed, 94 skipped`, WSL
`944 passed, 28 skipped`, and WSL original marker `66 passed, 27 skipped`.
XMind is unchanged and the frozen-snapshot/live inventory check passes.

Seismic Topic S6-0 and S6-1 are documentation-only and add no tests, examples,
workflows, CLI modules, console scripts, stable APIs, coverage entries, or
XMind updates. S6-0 records the Seismic Topic v0 route decision; S6-1 records
the Radon/slant source audit and selects the small `sfslant`-style slant-stack
contract before any high-resolution `sfradon` work.

Seismic Topic S6-2 adds `tests/test_seismic_slant_stack_contract.py` with 29
tests covering Madagascar `Mslant.c`/`slant.c` source-boundary paths, the
existing Radon/slant prototype as `A^T d` and `A m`, dot-test consistency,
analytic true-slope focusing, wrong-slope contrast, modeling predictability,
regular/explicit offset equivalence, shape/header/finiteness invariants,
invalid time/offset/p axes, non-finite data/model samples, explicit-offset
shape mismatch, existing `radon`/`iradon` CLI execution, deterministic
path-free JSON, workflow default-temp behavior, output isolation, and the
absence of original-Madagascar/C++ dependencies. Current validation results are
Windows `907 passed, 94 skipped`, WSL `973 passed, 28 skipped`, and WSL
original marker `66 passed, 27 skipped`. XMind is unchanged and the
frozen-snapshot/live inventory check passes.

Seismic Topic S7-0 and Inversion / Operator Foundation I0-0 are
documentation-only passes and add no tests, examples, workflows, CLI modules,
console scripts, stable APIs, coverage entries, or XMind updates. Their
validation counts remain unchanged from S6-2.

Inversion / Operator Foundation I0-1 adds
`tests/test_operator_composition_contract.py` and
`tests/test_solver_history_contract.py` with 16 tests covering scaled, summed,
composed, and stacked operators; real and complex dot tests; shape mismatch and
finite-value failures; identity composition; internal-only export boundaries;
no CLI addition; deterministic JSON-safe solver history/result summaries; and
unchanged existing CG result behavior. Current validation results are Windows
`923 passed, 94 skipped`, WSL `989 passed, 28 skipped`, and WSL original marker
`66 passed, 27 skipped`. XMind is unchanged and the frozen-snapshot/live
inventory check passes.

Inversion / Operator Foundation I0-2 adds
`tests/test_regularization_operator_contract.py` with 12 tests covering
scaled-identity damping, diagonal regularization, first- and second-difference
valid-boundary stencils, real and complex dot tests, shape and finite-value
failures, stacked `[A; lambda L]` readiness, composition with existing
operators, no root/API export, and no CLI addition. Current validation results
are Windows `935 passed, 94 skipped`, WSL `1001 passed, 28 skipped`, and WSL
original marker `66 passed, 27 skipped`. XMind is unchanged and the
frozen-snapshot/live inventory check passes.

Inversion / Operator Foundation I0-3 adds
`tests/test_inversion_problem_contract.py` and
`tests/test_objective_diagnostics_contract.py` with 17 tests covering
unregularized and regularized residuals, objective terms, zero-weight
regularization equivalence, stacked `[A; lambda L]` residual consistency,
normal-equation gradients, real and complex Hermitian objectives, shape and
finite-value failures, JSON-safe objective/stopping diagnostics,
SolverHistory/SolverResult summary compatibility, unchanged existing CG result
behavior, no root/API export, and no CLI addition. Current validation results
are Windows `952 passed, 94 skipped`, WSL `1018 passed, 28 skipped`, and WSL
original marker `66 passed, 27 skipped`. XMind is unchanged and the
frozen-snapshot/live inventory check passes.

Inversion / Operator Foundation I0-4 adds
`tests/test_solver_history_integration.py` and
`tests/test_cgls_lsqr_design_contract.py` with 13 tests covering unchanged
default CG/CGNR result contracts, optional initial/per-iteration history,
residual-tolerance/max-iteration/invalid-state stopping reasons, CG residual
energy, CGNR `LeastSquaresProblem` objective diagnostics, real/complex
behavior, deterministic JSON-safe summaries, direct-module export boundaries,
no CLI addition, source-audit paths, documented CGLS/LSQR design, and explicit
non-implementation of CGLS/LSQR. Current validation results are Windows
`965 passed, 94 skipped`, WSL `1031 passed, 28 skipped`, and WSL original
marker `66 passed, 27 skipped`. XMind is unchanged and the frozen-snapshot/live
inventory check passes.

# Session Handoff After P1-07

> Historical document note, 2026-06-09: this file is a preserved snapshot from
> the P0/P1 handoff audit. It intentionally contains counts and next-step
> recommendations that were true at that time. For the current baseline, use
> `docs/MASTER_HANDOFF_BEFORE_BATCH_MIGRATION.md`, `docs/TEST_STATUS.md`,
> `docs/CLI_INVENTORY.md`, and `docs/MADAGASCAR_FULL_COVERAGE_AUDIT.md`.

Date: 2026-06-08.

This file records the true repository state after auditing the requested P0-01
through P1-07 sequence. It is based on files in `hcz_mada/`, current docs,
source modules, tests, `pyproject.toml`, and the local `src-master/` audit docs.
No new algorithmic feature was implemented during this handoff audit.

## Files Reviewed

- `AGENTS.md`
- `docs/PROJECT_HANDOFF.md`
- `docs/TEST_STATUS.md`
- `docs/API_STABILITY.md`
- `docs/COVERAGE_MATRIX.md`
- `docs/MADAGASCAR_FULL_COVERAGE_AUDIT.md`
- `docs/NEXT_100_TASKS.md`
- `docs/NEXT_MIGRATION_BACKLOG.md`
- `docs/CLI_INVENTORY.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/MADAGASCAR_COMPATIBILITY.md`
- `docs/LOCAL_INSTALL_AND_USAGE.md`
- `docs/ORIGINAL_MADAGASCAR_COMPARISON.md`
- Relevant `pymadagascar/`, `tests/`, `examples/`, and `pyproject.toml` files.

## True Completed Tasks

P0-01 is complete. The package has stable `console_scripts`, CLI inventory,
local quickstart docs, examples, and subprocess smoke tests for core local use.

P0-02 is complete. Original Madagascar comparison tests are optional, marker
policy is documented, markers are registered in `pytest.ini`, and missing
upstream `sf*` programs skip only optional comparison tests.

P0-03 is complete. Coverage denominator docs distinguish full Madagascar
coverage from core `system/` + `plot/main` coverage. Prototype warnings are
present for NMO, Semblance, FK/Radon, Kirchhoff, acoustic2d, plotting, and
SEG-Y 2D.

P0-04 is complete. `examples/my_workflows/` exists with five workflow scripts,
a README, a helper module, and workflow smoke tests.

P1-01 is complete. `sfget` subset is implemented through
`pymadagascar.generic.info.get_header_value/get_header_values`,
`pymadagascar.cli.get`, tests, docs, example, and optional original comparison.

P1-02 is complete. `sfdisfil` small-data text dump subset is implemented through
`disfil_array/disfil_rsf`, `pymadagascar.cli.disfil`, tests, docs, example, and
optional original comparison.

P1-03 is complete. `sfreal`, `sfimag`, `sfcmplx`, and `sfrtoc` file-backed
complex tools are implemented through `pymadagascar.generic.complex_tools`,
CLI modules, tests, docs, example, and optional original comparisons.

P1-04 is complete. `sfnoise` seeded normal/uniform subset is implemented through
`pymadagascar.generic.noise`, `pymadagascar.cli.noise`, tests, docs, example,
and an optional original comparison using a deterministic zero-variance path.

P1-05 is complete. Direct time-domain Ricker wavelet tools are implemented in
`pymadagascar.signal.wavelet`; acoustic2d reuses the signal wavelet API; CLI,
tests, docs, example, and related optional original smoke coverage exist.

## True Pending Tasks

P1-06 was pending at the time of this handoff audit. It was completed later by
P1-11 with `pymadagascar.signal.smooth`, `pymadagascar.cli.smooth`,
`pymadagascar.cli.boxsmooth`, tests, docs, an example, and console scripts.

P1-07 was pending at the time of this handoff audit. It was completed later by
P1-12 with `mask_rsf`, `cut_rsf`, `reverse_rsf`, CLI modules, tests, docs, an
example, and console scripts.

P1-08 was not implemented at the time of this handoff audit. It was completed
later with enhanced `par=file` parsing, tests, and docs.

## P0/P1 Completed Checklist

- CLI local usability baseline: complete.
- Original Madagascar optional comparison docs and markers: complete.
- Documentation consistency pass for coverage denominator and prototypes:
  complete.
- Local workflow examples: complete.
- `sfget`: complete stable subset.
- `sfdisfil`: complete stable subset.
- `sfreal/sfimag/sfcmplx/sfrtoc`: complete stable subsets.
- `sfnoise`: complete stable subset.
- Direct Ricker wavelet utility: complete stable subset.

## P1/P2 Next Recommendations

1. Completed later: P1-06 `sfsmooth`/`sfboxsmooth` as a small pure Python/NumPy
   smoothing module with API, CLI, tests, docs, example, and optional original
   comparison.
2. Completed later: P1-07 `sfmask`/`sfcut`/`sfreverse` as generic array tools.
3. Completed later: P1-08 parameter-file parser enhancement.
4. Continue only after each task lands with pytest passing.
5. Do not start P2 seismic/hybrid expansion until these P1 foundations are
   either completed or explicitly deferred.

## Current CLI Registration State

There are 51 user-facing CLI modules excluding `base.py` and `__init__.py`.
There are 19 registered `console_scripts` in `pyproject.toml`:

- `pymada-info`
- `pymada-get`
- `pymada-disfil`
- `pymada-real`
- `pymada-imag`
- `pymada-cmplx`
- `pymada-rtoc`
- `pymada-noise`
- `pymada-ricker`
- `pymada-spike`
- `pymada-math`
- `pymada-window`
- `pymada-attr`
- `pymada-put`
- `pymada-dd`
- `pymada-cat`
- `pymada-transp`
- `pymada-fft`
- `pymada-bandpass`

All other CLI modules should be invoked with
`python -m pymadagascar.cli.<name>`. Do not document unregistered `pymada-*`
names as available.

## Current API Stable State

Stable APIs are listed in `docs/API_STABILITY.md`. The stable group includes
RSF I/O, `Axis`/`Hypercube`, `RSFParams`, CLI base helpers, core generic tools,
complex tools, noise, direct Ricker wavelet generation, signal FFT/filter/
convolution subsets, testing helpers, and hybrid wrappers with fallback.

Prototype or partial APIs remain unstable: SEG-Y 2D, plotting substitutes, NMO,
Semblance, FK, Radon, Kirchhoff, acoustic2d, and any future smoothing or generic
array tools until they are actually implemented and documented.

## Current Test Results

Plain `python` is not available on the current PowerShell PATH. The documented
project interpreter was used instead:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q
```

Result:

```text
367 passed, 33 skipped in 11.32s
```

Skip-reason run:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q -rs
```

Result:

```text
367 passed, 33 skipped in 10.37s
```

The 33 skips are expected: 32 original Madagascar comparison tests skip because
upstream `sf*` commands are not installed or not on PATH, and one optional C++
extension test skips because the extension is not built.

## Optional Original Madagascar Comparison State

Optional comparison tests use `original_madagascar` marker conventions and skip
when required upstream commands are unavailable. Current machine status:
original Madagascar command-line programs are not installed or not discoverable.
Pure Python tests pass without original Madagascar.

## Hybrid C++ State

Hybrid wrappers exist for array operations and batch cross-correlation. The C++
extension is not built in the current environment, so wrappers use Python/NumPy
fallbacks. This is expected. C++ must remain optional and must not become a hard
runtime dependency.

## New Codex Conversation First Message

Suggested first message:

```text
请从 hcz_mada 继续 pymadagascar。先阅读 AGENTS.md、docs/SESSION_HANDOFF_AFTER_P1_07.md、docs/PROJECT_HANDOFF.md、docs/TEST_STATUS.md、docs/NEXT_MIGRATION_BACKLOG.md。不要依赖旧聊天记录。P1-06 和 P1-07 目前只是分析过、未实现；请从我指定的下一个小任务开始，保持 pure Python 可用，完成后运行 pytest。
```

## New Conversation Must Not Do

- Do not modify, format, delete, or move `../src-master`.
- Do not treat P1-06 or P1-07 as implemented.
- Do not add P2/P3 features before the user explicitly asks.
- Do not add C++ kernels or make C++ a hard dependency.
- Do not silently skip failing pure Python tests.
- Do not document unregistered `pymada-*` names as runnable commands.
- Do not migrate large imaging, VPlot, SCons/book, IWAVE/RVL, MPI/CUDA/PETSc,
  or broad `user/*` programs in one step.

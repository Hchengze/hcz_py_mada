# API Surface Inventory

This document records the current public surface boundaries for pymadagascar.
It is a hygiene guide for future development, not a new compatibility promise.

pymadagascar is not a complete clone of Madagascar's 2000+ commands, and it is
not a standalone forward-modeling, DAS, localization, or seismic-demo library.
The near-term target is a locally durable, Pythonic RSF/geophysics toolkit that
supports Madagascar-style command workflows. RSF I/O, axis/header handling,
`RSFData` chains, CLI modules, console scripts, tests, docs, and conservative
coverage mapping remain the main line.

## Surface Layers

### Stable root API

The root package, `pymadagascar.__init__`, exposes the oldest stable and
stable-subset entry points: `RSFData`, `read`, `write`, RSF I/O types, core
axis/hypercube helpers, selected generic/signal/seismic functions, plotting
helpers, and optional hybrid status helpers. Root exports are intentionally
more conservative than topic modules. New source-aligned command batches should
not automatically add root exports.

Root imports are checked by `tools/check_release.py`, but root importability is
not the same thing as full Madagascar compatibility. A root-exported function
can still be a stable subset, partial implementation, or prototype according
to `API_AND_COMPATIBILITY.md`.

### Topic APIs

Topic packages expose broader surfaces than the root package:

- `pymadagascar.generic`: array math, file/header helpers, sampling,
  statistics, operators, and source-aligned `system/generic` subsets.
- `pymadagascar.signal`: FFT, filtering, spectral QC, transforms, calculus,
  conditioning, convolution, and Pythonic signal conveniences.
- `pymadagascar.seismic`: bounded source-aligned seismic command subsets plus
  older small-gather prototypes such as NMO, semblance, FK, and Radon.
- `pymadagascar.io`: RSF I/O and small SEG-Y prototype support.
- `pymadagascar.plot`: lightweight quicklook replacements for selected plot
  workflows, not VPlot compatibility.
- `pymadagascar.modeling`, `pymadagascar.localization`, `pymadagascar.imaging`,
  and some `pymadagascar.generic` solver/operator helpers: bounded prototype
  or partial foundations, not production domain systems.
- `pymadagascar.testing`: test and optional-comparison helpers. These are not
  stable processing APIs unless explicitly documented elsewhere.

Topic-level importability does not imply command coverage. A function counts
as command coverage only when the coverage roadmap records a corresponding
Madagascar command or an explicit accepted source mapping.

### RSFData chain API

`pymadagascar.api.RSFData` is the high-level chainable wrapper over NumPy data
and RSF metadata. It centralizes chain methods, but algorithm bodies should
live in topic modules such as `generic`, `signal`, or `seismic`.

Current chain-method rules:

- Chain transforms return a new `RSFData` object by default.
- Methods with `inplace=True` make mutation explicit; non-in-place behavior is
  the default contract.
- Methods that use secondary operands should accept documented operand forms
  consistently, such as `RSFData`, RSF path, NumPy array, or list when supported.
- New chain methods must be covered by `tests/test_rsfdata_api_consistency.py`
  or a focused command batch test.
- New chain methods should wrap an existing topic function or source-backed
  command subset. Do not put new algorithm implementations directly into
  `api.py`.
- Adding a chain method does not automatically add a root export or command
  coverage entry.

`api.py` is intentionally a large registration and dispatch layer. If it grows
further, prefer non-behavioral grouping or a documented inventory pass before
considering a code split.

### CLI modules

User-facing CLI modules live under `pymadagascar.cli` and are runnable as:

```text
python -m pymadagascar.cli.<name>
```

The CLI inventory currently contains 162 user-facing modules. Every module is
expected to import cleanly, expose `main()`, and provide a `__main__` guard.
`tools/check_cli_inventory.py` is the authority for the module inventory check.

A CLI module can be module-only. Module-only CLIs do not automatically become
registered console scripts, and they do not automatically count as
source-backed Madagascar command coverage.

### Console scripts

Registered console scripts use the `pymada-<name>` convention and are declared
in `pyproject.toml`. The current registered inventory is 60 scripts.

Console scripts are checked by package metadata tests and release tools. A
registered `pymada-*` command should have a matching CLI module and help smoke
coverage. Registering a console script does not by itself determine whether a
command is source-backed; the coverage roadmap does.

### Workflow and prototype surfaces

`examples/my_workflows` contains examples, validation workflows, and retained
prototype workflows. It is not an API authority and is not a coverage
authority. Workflow outputs and JSON reports are useful regression artifacts,
but they are not stable file-format contracts unless a separate document says
so.

Forward modeling, DAS, localization, imaging, inversion/operator helpers,
SEG-Y, NMO, semblance, FK, and Radon remain bounded prototype, partial, or
workflow surfaces where documented. They may support command development, but
they do not replace the Madagascar-style command-surface main line.

## Coverage Boundary

The authority for command coverage is `docs/COVERAGE_AND_ROADMAP.md`, with
release and inventory tools acting as consistency checks. `docs/README.md` is
an entry summary. The learning notebook is a study guide and is not an API or
coverage authority.

Coverage rules:

- Full command-surface denominator remains `2114`.
- Core `system/` + `plot/main` denominator remains `301`.
- Direct `system/main` denominator remains `39`.
- Source-backed or source-aligned commands must identify the corresponding
  official Madagascar source file, or explicitly explain the selected source
  relationship.
- Pythonic conveniences are not automatically counted as source-backed command
  coverage.
- Workflow/prototype surfaces do not increase command coverage.
- Denominators must not be changed as part of ordinary feature work.

At the M3-3 baseline, conservative coverage is:

- Full Madagascar/alias command surface: `124 / 2114 = 5.87%`.
- Core `system/` + `plot/main`: `111 / 301 = 36.88%`.
- Direct `system/main`: `37 / 39 = 94.87%`.

## Rules For New API Surface

Future additions should follow these rules:

- Prefer source-aligned command work or clearly labeled Pythonic conveniences.
- Keep root exports conservative; prefer topic APIs plus `RSFData` chain methods
  for small command batches.
- Keep algorithm implementations in topic modules, not in `api.py`.
- Add CLI modules and console scripts only when the command surface warrants
  them and tests/docs/release inventory are updated.
- Update source mapping, docs, and coverage only when the command qualifies
  under the coverage roadmap.
- Keep prototype topics bounded and explicitly non-field-ready unless a later
  task deliberately changes their maturity.
- Do not add large migration, RTM, DMO, Kirchhoff, Gazdag, FWI, MPI, CUDA,
  PETSc, or solver systems through an API hygiene pass.

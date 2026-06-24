# Source-Backed Command Admission Checklist

G4-3 turns the post-M3 source-reading lessons into an admission gate for future
source-backed command work. This document must be read before implementing a new
Madagascar-aligned command. It is not a backlog approval, not a coverage
authority, and not a compatibility promise. `COVERAGE_AND_ROADMAP.md` remains
the command-coverage authority.

pymadagascar is not a complete clone of Madagascar's 2000+ commands, and it is
not a standalone forward-modeling, DAS, localization, or seismic-demo library.
The near-term target is a locally durable, Pythonic toolkit for RSF data and
Madagascar-style command workflows.

Main-line work remains RSF I/O, axis/header handling, `RSFData` chains, CLI
modules, console scripts, tests, docs, and conservative coverage mapping.
Source-backed commands must be source-aligned. Pythonic conveniences,
workflows, and prototypes must not be counted as source-backed command
coverage. Original Madagascar source files and coverage denominators must not
be modified.

## Command Admission Checklist

Before any new source-backed command is implemented, the implementation pass
must answer these questions in the work log, tests, and docs as appropriate:

1. What is the Official Madagascar source file path?
2. Does it materially depend on an `api/c` helper? If yes, what helper path?
3. Can the upstream core semantics be described in five lines or fewer?
4. Does pymadagascar already have a same-name or nearby Pythonic convenience?
5. Is the command already source-counted, or could this duplicate an alias?
6. What is the input RSF axis/header contract?
7. How do NumPy shape dimensions map to RSF `n1`, `n2`, `n3`, and higher axes?
8. How does the output RSF axis/header change?
9. Does the command need side input such as `poly=`, `a0=`, `mask=`, or
   `velocity=`?
10. Does it produce side output such as a mask, weights file, or report?
11. Which bounded-subset parameters are supported?
12. Which upstream behaviors are explicitly unsupported?
13. Does upstream rely on streaming, native-byte copying, or pipe behavior, and
   how is the Python subset downgraded?
14. Does the source involve SEG-Y headers, irregular geometry, VPlot,
   solvers, migration, or imaging?
15. Is a Python topic API needed?
16. Is an `RSFData` chain method semantically appropriate?
17. Is a CLI module appropriate?
18. Is a registered console script appropriate?
19. Are root exports being added? The default answer should be no.
20. What is the focused test plan?
21. What Chinese comment plan explains source mapping, RSF axes, NumPy shape,
   bounded subset limits, and test scenarios?
22. Should the command count toward command coverage, and why?

If any answer is unknown, the pass should remain an audit pass. A command should
not be implemented just to increase the numerator.

## Risk Classification

### Low Risk

Low-risk candidates are small unary, binary, mask, statistic, metadata, or axis
transforms with:

- a clear source file and helper mapping;
- few parameters;
- no SEG-Y trace-header dependency;
- no solver, inversion, migration, or imaging dependency;
- no VPlot or pen/rendering backend dependency;
- an ordinary NumPy in-memory implementation path;
- a clear RSF axis/header and NumPy shape contract.

Low risk still means "eligible for a fresh source audit"; it does not mean
"approved to implement."

### Medium Risk

Medium-risk families require a design pass before command coding:

- DSP filters, including Butterworth and bandpass families;
- convolution, recursive filters, and trace filters;
- shot/CMP/gather geometry transforms;
- interpolation, stretch, remap, and spline families;
- velocity, semblance, and scan families;
- reflectivity, AVO, and small elastic-modeling subsets;
- plot display commands that may look data-like but depend on VPlot behavior.

These families often hide helper-level behavior, boundary conditions, side
files, geometry assumptions, or physical-mode switches. They should not be
handled by opportunistic source-gap coding.

### High Risk

High-risk systems are deferred unless a later project-level decision creates a
bounded design:

- migration, RTM, DMO, Kirchhoff, Gazdag, and wave-equation imaging;
- FWI, inversion systems, production solvers, and solver-heavy workflows;
- VPlot, pens, and rendering backend compatibility;
- SCons, book, and reproducible-paper infrastructure;
- MPI, CUDA, PETSc, IWAVE, RVL, and external execution ecosystems;
- `user/*` large module families and user-specific research systems.

## Required Implementation Surfaces

An accepted source-backed command should usually close these surfaces in one
small pass:

1. topic API;
2. `RSFData` chain method when the command has ordinary single-output data
   semantics;
3. CLI module runnable as `python -m pymadagascar.cli.<name>`;
4. registered console script when the command is user-facing and stable enough;
5. focused tests;
6. docs and coverage mapping;
7. release inventory updates;
8. source mapping metadata in output headers when useful;
9. Chinese comments for non-obvious source mapping, RSF axes, NumPy shape,
   bounded subset boundaries, side inputs, and test fixtures.

Exceptions are allowed for scalar/text commands, side-output-only commands, or
module-only utilities, but the exception must be documented.

## Required Tests

At minimum, a new accepted command needs tests for:

1. numeric results on a small deterministic fixture;
2. RSF header and axis contract, including shape-changing behavior;
3. source metadata or documented source mapping;
4. no-in-place behavior and explicit `inplace=True` behavior if supported;
5. invalid parameters and invalid axis/header conditions;
6. CLI help smoke;
7. CLI subprocess execution on a small RSF fixture;
8. `RSFData` consistency when a chain method exists;
9. side input or side output behavior when present;
10. Pythonic convenience boundaries when a nearby convenience name exists.

Tests must not silently skip or xfail failures to make a batch pass. Optional
Original Madagascar comparisons may remain explicit optional checks, but local
Python behavior must still be tested directly.

## Coverage Admission Rule

A feature counts as source-backed command coverage only when:

- the command source file mapping is explicit;
- helper-level mapping is explicit where relevant;
- the bounded subset is source-aligned;
- Pythonic conveniences are not being relabeled;
- duplicate aliases or already-counted commands are excluded;
- docs and tests describe supported and unsupported upstream behavior;
- denominators remain unchanged.

When in doubt, do not count it. A useful Pythonic convenience can remain useful
without being counted as a source-backed Madagascar command.

# Source-Backed Command Admission Checklist

## Purpose

G4-4 hardens the G4-3 admission gate into a readable checklist for future
source-backed command work.

Read this document before implementing a new Madagascar-aligned command. It is
not a backlog approval, not a coverage authority, and not a compatibility
promise. `COVERAGE_AND_ROADMAP.md` remains the command-coverage authority.

The practical goal is simple: make future command batches slower, clearer, and
less likely to miscount Pythonic conveniences or ambiguous source gaps.

## Project Boundary

pymadagascar is not a complete clone of Madagascar's 2000+ commands.

It is also not a standalone forward-modeling, DAS, localization, or seismic-demo
algorithm library.

The near-term target is a locally durable, Pythonic toolkit for RSF data and
Madagascar-style command workflows. Main-line work remains:

- RSF I/O;
- axis/header handling;
- `RSFData` chains;
- CLI modules;
- registered console scripts;
- tests;
- docs;
- conservative coverage mapping.

Source-backed commands must be source-aligned. Pythonic conveniences,
workflows, and prototypes must not be counted as source-backed command
coverage. Original Madagascar source files and coverage denominators must not
be modified.

## When This Checklist Is Required

Use this checklist before any pass that may:

- add a new source-backed command;
- promote an existing Python function to source-backed command coverage;
- register a new `pymada-*` console script for command coverage;
- add a new `RSFData` chain method for a source-backed command;
- revise docs in a way that could affect source mapping or coverage.

Do not use this checklist to justify opportunistic implementation. If the
source audit is incomplete, stop at audit notes.

For a fillable proposal template, use `SOURCE_COMMAND_TEMPLATE.md`. For a
read-only audit worksheet, use `SOURCE_AUDIT_WORKSHEET.md`.

## Command Admission Checklist

Before any new source-backed command is implemented, answer each question in
the work log, tests, and docs as appropriate.

1. What is the Official Madagascar source file path?

2. Does it materially depend on an `api/c` helper, and if so what is the helper
   source path?

3. Can the upstream core semantics be described in five lines or fewer?

4. Does pymadagascar already have a same-name or nearby Pythonic convenience,
   and is that convenience truly source-aligned?

5. Is the command already source-counted, or could this duplicate an alias or an
   already-counted command?

6. What is the input RSF axis/header contract?

7. How do NumPy dimensions map to RSF `n1`, `n2`, `n3`, and higher axes?

8. How does the output RSF axis/header change?

9. Does the command need side input such as `poly=`, `a0=`, `mask=`, or
   `velocity=`?

10. Does it produce side output such as a mask, weights file, report, or side
    table?

11. Which bounded-subset parameters are supported?

12. Which upstream behaviors are explicitly unsupported?

13. Does upstream rely on streaming, native-byte copying, pipe behavior, or
    out-of-core execution, and how is the Python subset downgraded?

14. Does the source involve SEG-Y headers, irregular geometry, VPlot, solvers,
    migration, imaging, or large external systems?

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

Low-risk candidates are eligible for a fresh source audit. They are not
automatically approved for implementation.

Typical low-risk signals:

- small unary, binary, mask, statistic, metadata, or axis transform;
- clear command source file;
- clear helper-level source mapping when a helper is used;
- few parameters;
- ordinary NumPy in-memory implementation path;
- clear RSF axis/header contract;
- clear NumPy shape contract.

Low-risk candidates should not require:

- SEG-Y trace headers;
- irregular acquisition geometry;
- solver, inversion, migration, or imaging machinery;
- VPlot, pens, or rendering backend behavior;
- MPI, CUDA, PETSc, IWAVE, RVL, or other external execution systems.

### Medium Risk

Medium-risk families require a design pass before command coding.

Common medium-risk families:

- DSP filters, including Butterworth and bandpass families;
- convolution, recursive filters, and trace filters;
- shot/CMP/gather geometry transforms;
- interpolation, stretch, remap, and spline families;
- velocity, semblance, and scan families;
- reflectivity, AVO, and small elastic-modeling subsets;
- plot display commands that may look data-like but depend on VPlot behavior.

Why they are medium risk:

- source behavior may be hidden in `api/c` helpers;
- boundary conditions can dominate test expectations;
- side files and side outputs may be part of the real contract;
- geometry assumptions may not fit ordinary RSF axes;
- physical modes can change semantics under the same command name.

### High Risk

High-risk systems are deferred unless a later project-level decision creates a
bounded design.

Deferred high-risk areas:

- migration, RTM, DMO, Kirchhoff, Gazdag, and wave-equation imaging;
- FWI, inversion systems, production solvers, and solver-heavy workflows;
- VPlot, pens, and rendering backend compatibility;
- SCons, book, and reproducible-paper infrastructure;
- MPI, CUDA, PETSc, IWAVE, RVL, and external execution ecosystems;
- `user/*` large module families and user-specific research systems.

## Required Implementation Surfaces

An accepted source-backed command should usually close these surfaces in one
small pass.

1. Topic API.

2. `RSFData` chain method when the command has ordinary single-output data
   semantics.

3. CLI module runnable as `python -m pymadagascar.cli.<name>`.

4. Registered console script when the command is user-facing and stable enough.

5. Focused tests.

6. Docs and coverage mapping.

7. Release inventory updates.

8. Source mapping metadata in output headers when useful.

9. Chinese comments for non-obvious source mapping, RSF axes, NumPy shape,
   bounded subset boundaries, side inputs, side outputs, and test fixtures.

Exceptions are allowed for scalar/text commands, side-output-only commands, or
module-only utilities, but the exception must be documented.

## Required Tests

At minimum, a new accepted command needs tests for the following.

1. Numeric results on a small deterministic fixture.

2. RSF header and axis contract, including shape-changing behavior.

3. Source metadata or documented source mapping.

4. No-in-place behavior.

5. Explicit `inplace=True` behavior if supported.

6. Invalid parameters.

7. Invalid axis/header conditions.

8. CLI help smoke.

9. CLI subprocess execution on a small RSF fixture.

10. `RSFData` consistency when a chain method exists.

11. Side input or side output behavior when present.

12. Pythonic convenience boundaries when a nearby convenience name exists.

Tests must not silently skip or xfail failures to make a batch pass. Optional
Original Madagascar comparisons may remain explicit optional checks, but local
Python behavior must still be tested directly.

## Coverage Admission Rule

A feature counts as source-backed command coverage only when all of these are
true:

- the command source file mapping is explicit;
- helper-level mapping is explicit where relevant;
- the bounded subset is source-aligned;
- Pythonic conveniences are not being relabeled;
- duplicate aliases or already-counted commands are excluded;
- docs and tests describe supported upstream behavior;
- docs and tests describe unsupported upstream behavior;
- denominators remain unchanged.

When in doubt, do not count it. A useful Pythonic convenience can remain useful
without being counted as a source-backed Madagascar command.

## Chinese Comment Requirements

Future source-backed command code should follow `CODE_COMMENT_GUIDE.md`.

Use Chinese comments to explain:

- Original Madagascar source mapping;
- helper-level source mapping;
- RSF `n#`, `o#`, `d#`, label, unit, and dtype assumptions;
- NumPy shape order and how it maps to RSF axes;
- bounded subset support and upstream behavior left out of scope;
- side inputs, side outputs, masks, gather axes, and geometry assumptions;
- coordinate origins, sample intervals, units, and index directions;
- no-in-place and `inplace=True` behavior;
- geophysical or RSF meaning of non-obvious test fixtures.

Do not add mechanical comments that restate obvious assignments.

## Stop Conditions

Stop the implementation pass and return an audit conclusion when any of these
conditions applies.

1. Official source path is unclear.

2. Helper-level dependency is material but not understood.

3. Upstream semantics cannot be explained concisely.

4. The current project has a same-name Pythonic convenience with different
   semantics.

5. The command may already be source-counted.

6. The candidate may duplicate an alias or already-counted command.

7. The implementation would require SEG-Y headers.

8. The implementation would require irregular acquisition geometry.

9. The implementation would require a solver, inversion, migration, imaging, or
   large external execution system.

10. The implementation would require VPlot, pens, or rendering backend
    compatibility.

11. The bounded subset cannot be stated clearly.

12. The RSF axis/header contract cannot be stated clearly.

13. The NumPy shape contract cannot be stated clearly.

14. The test plan cannot be stated clearly.

15. The Chinese comment plan cannot be stated clearly.

16. The only reason to proceed is increasing the numerator.

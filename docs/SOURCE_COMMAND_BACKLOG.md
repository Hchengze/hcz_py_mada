# Source-Backed Command Candidate Backlog

## Purpose

G4-4 hardens the G4-3 backlog into a readable candidate map for future
source-backed command audits.

This backlog is not approval to implement anything. Every candidate needs a
fresh source audit, the checklist in `SOURCE_COMMAND_ADMISSION.md`, and an
explicit proceed/stop decision before any code is changed.

`COVERAGE_AND_ROADMAP.md` remains the command-coverage authority. This file
does not change the numerator, denominator, CLI inventory, console-script
inventory, API surface, or compatibility promise.

## How To Use This Backlog

Use this file as a starting point for future planning, not as a task list to
execute mechanically.

For each candidate:

1. Read the official source again.

2. Fill `SOURCE_AUDIT_WORKSHEET.md`.

3. Fill `SOURCE_COMMAND_TEMPLATE.md` only if the audit looks safe.

4. Check duplicate counting and Pythonic convenience conflicts.

5. Decide whether to stop, defer, design first, or implement a bounded subset.

6. Update `COVERAGE_AND_ROADMAP.md` only after implementation and tests prove
   the source-backed mapping.

## Ready For Future Low-Risk Audit

These candidates appear suitable for later low-risk audits, but none is
approved by this list. Each item still needs source reading, duplicate-count
checks, RSF axis/header contracts, bounded-subset design, tests, and docs.

### `sfmask`

- Candidate: `sfmask`
- Official source path: `../src-master/system/main/mask.c`
- Family: mask / selection
- Risk: low
- Why possibly suitable: direct metadata-aware mask/cut behavior is central to
  RSF workflows.
- Required pre-check: verify current mask, headerwindow, headercut, and alias
  coverage.
- Notes: do not duplicate B-3 coverage.

### `sfreverse`

- Candidate: `sfreverse`
- Official source path: `../src-master/system/main/reverse.c`
- Family: axis transform
- Risk: low
- Why possibly suitable: axis reversal can likely be implemented as a NumPy
  in-memory subset.
- Required pre-check: audit origin/header update rules and any existing reverse
  convenience.
- Notes: count only if it is a true uncovered direct `system/main` command.

### `sfwindow`

- Candidate: `sfwindow`
- Official source path: `../src-master/system/main/window.c`
- Family: axis slicing
- Risk: low
- Why possibly suitable: regular axis slicing is core RSF behavior.
- Required pre-check: verify existing window, headerwindow, and slice coverage.
- Notes: avoid re-counting Python slicing convenience.

### `sfput`

- Candidate: `sfput`
- Official source path: `../src-master/system/main/put.c`
- Family: metadata
- Risk: low
- Why possibly suitable: a safe metadata update subset may be useful.
- Required pre-check: define key/value safety rules and passthrough limits.
- Notes: arbitrary header editing can become too broad.

### `sfdd`

- Candidate: `sfdd`
- Official source path: `../src-master/system/main/dd.c`
- Family: format / copy
- Risk: low-medium
- Why possibly suitable: bounded form conversion may be small.
- Required pre-check: audit native, ASCII, XDR, dtype, and streaming behavior.
- Notes: likely in-memory or file-backed subset only.

### `sfpow`

- Candidate: `sfpow`
- Official source path: `../src-master/system/generic/Mpow.c`
- Family: unary / axis gain
- Risk: low
- Why possibly suitable: source is small enough to audit.
- Required pre-check: verify existing `sftpow` and `pow` coverage.
- Notes: likely already covered through the axis-gain surface.

### `sfintshow`

- Candidate: `sfintshow`
- Official source path: `../src-master/system/generic/Mintshow.c`
- Family: table / display text
- Risk: low
- Why possibly suitable: may be metadata or text oriented.
- Required pre-check: audit output type and whether behavior is display-only.
- Notes: may not suit an `RSFData` chain method.

### `sftclip` extensions

- Candidate: `sftclip` extensions
- Official source path: `../src-master/system/generic/Mtclip.c`
- Family: amplitude clip
- Risk: low
- Why possibly suitable: source already mapped in M3-3.
- Required pre-check: identify unimplemented modes without creating a new
  numerator entry.
- Notes: extension only; do not count as a new command.

### `sfotsu` extensions

- Candidate: `sfotsu` extensions
- Official source path: `../src-master/system/generic/Motsu.c`
- Family: threshold / statistic
- Risk: low
- Why possibly suitable: source already mapped in M3-3.
- Required pre-check: confirm scalar/text output and no chain method.
- Notes: extension only; no duplicate count.

### `sfgrad` adjacent edge utilities

- Candidate: `sfgrad` adjacent edge utilities
- Official source path: `../src-master/system/generic/Mgrad2.c`,
  `../src-master/system/generic/Mgrad3.c`, and
  `../src-master/api/c/edge.c`
- Family: edge / mask
- Risk: low
- Why possibly suitable: helper mapping is understood.
- Required pre-check: find a distinct uncounted source before coding.
- Notes: `sfgrad2` and `sfgrad3` are already counted.

### `sflpad` extensions

- Candidate: `sflpad` extensions
- Official source path: `../src-master/system/generic/Mlpad.c`
- Family: axis / mask output
- Risk: low
- Why possibly suitable: source already mapped in M3-4.
- Required pre-check: isolate mask or axis behaviors not yet supported.
- Notes: extension only; no new numerator.

### `sfpolymask` extensions

- Candidate: `sfpolymask` extensions
- Official source path: `../src-master/system/generic/Mpolymask.c`
- Family: polygon mask
- Risk: low
- Why possibly suitable: source already mapped in M3-6.
- Required pre-check: define multidimensional or boundary behavior carefully.
- Notes: extension only; no new command count.

### `sfhistogram` extensions

- Candidate: `sfhistogram` extensions
- Official source path: `../src-master/system/generic/Mhistogram.c`
- Family: statistic
- Risk: low
- Why possibly suitable: existing bounded histogram behavior exists.
- Required pre-check: verify source alignment and current coverage state.
- Notes: avoid counting convenience behavior twice.

### `sfslice` extensions

- Candidate: `sfslice` extensions
- Official source path: `../src-master/system/generic/Mslice.c`
- Family: axis slicing
- Risk: low
- Why possibly suitable: small fixed-index slicing may be bounded.
- Required pre-check: verify existing Stage C-2 slice coverage.
- Notes: likely already counted or extension-only.

### `sfintbin` extensions

- Candidate: `sfintbin` extensions
- Official source path: `../src-master/system/seismic/Mintbin.c`
- Family: gather / binning
- Risk: low-medium
- Why possibly suitable: existing subset has a regular numeric table basis.
- Required pre-check: audit side outputs, duplicate policy, and SEG-Y lookup.
- Notes: extension only; geometry risk remains.

### `sfintbin3` extensions

- Candidate: `sfintbin3` extensions
- Official source path: `../src-master/system/seismic/Mintbin3.c`
- Family: gather / 3D binning
- Risk: low-medium
- Why possibly suitable: existing subset has a bounded numeric table basis.
- Required pre-check: audit map/mask outputs and inverse modes.
- Notes: extension only; no duplicate count.

### `sfai2refl` / `sfrefl2ai` extensions

- Candidate: `sfai2refl` / `sfrefl2ai` extensions
- Official source path: `../src-master/system/seismic/Mai2refl.c` and
  `../src-master/system/seismic/Mrefl2ai.c`
- Family: impedance / reflectivity
- Risk: low-medium
- Why possibly suitable: the acoustic pair is already bounded.
- Required pre-check: audit edge sample and side-input impedance behavior.
- Notes: do not expand into elastic reflectivity.

## Design-First Medium-Risk Families

These families should start with a design document or targeted audit pass, not
source-gap coding.

| Family | Why Medium Risk | Design Needed Before Coding | Minimum Test Direction |
| --- | --- | --- | --- |
| Butterworth / bandpass / DSP filters | Upstream `Mbandpass.c` uses recursive Butterworth helpers, not FFT taper convenience. | Filter state, phase, boundaries, axis metadata, and helper mapping. | Impulse/step responses, invalid bands, axis metadata, convenience no-miscount. |
| Ricker trace convolution | Upstream `Mricker1.c` is trace filtering/convolution, not only a wavelet generator. | Generator vs filter semantics, delay, normalization, and boundary modes. | Trace convolution fixture, source metadata, generator no-miscount. |
| Shot/CMP/gather geometry | Gather transforms depend on regular geometry, offsets, masks, and side outputs. | Axis roles, half/full offset, positive orientation, mask side output, SEG-Y exclusion. | Inverse-pair fixtures, header axes, invalid geometry, side-output behavior. |
| Reflectivity / AVO / elastic modeling | Sources combine physical models, interpolation, Vp/Vs/rho, and angle behavior. | Physical parameter contract, units, interpolation, and bounded equations. | Normal-incidence fixtures, invalid units, unsupported elastic modes. |
| Interpolation / stretch / remap | Many sources share interpolation helpers, adjoints, stretch mutes, and side files. | Shared interpolation contract and axis update rules. | Endpoint/fill tests, adjoint exclusions, side-file validation. |
| Velocity / semblance / scan | Scan tools mix geometry, velocities, masks, weights, stretch, and picking. | Regular-gather contract, velocity axis, masks, stretch policy, output panels. | True/wrong velocity fixtures, mask/weight tests, invalid axis tests. |
| Plot display family | Plot sources emit VPlot operations through pens/rendering state. | Separate P-series display strategy and compatibility target. | Metadata-only tests if any; VPlot syntax tests only if deliberately supported. |

## Deferred High-Risk Systems

These systems are not near-term source-backed command targets:

- migration, RTM, DMO, Kirchhoff, Gazdag, and wave-equation imaging;
- FWI, inversion systems, production solvers, and solver-heavy workflows;
- VPlot, pens, and rendering backend compatibility;
- SCons, book, and reproducible-paper infrastructure;
- MPI, CUDA, PETSc, IWAVE, RVL, and external execution ecosystems;
- `user/*` large command families and user-specific research codes.

## Already Completed M3 Commands

These commands are already mapped and must not be counted again.

| Command | Source Mapping | Batch | Repeat-Count Rule |
| --- | --- | --- | --- |
| `sftclip` | `../src-master/system/generic/Mtclip.c` | M3-3 | extensions only |
| `sfotsu` | `../src-master/system/generic/Motsu.c` | M3-3 | extensions only |
| `sfrefl2ai` | `../src-master/system/seismic/Mrefl2ai.c` | M3-3 | extensions only |
| `sfgrad2` | `../src-master/system/generic/Mgrad2.c` plus `../src-master/api/c/edge.c` | M3-4 | already counted |
| `sfgrad3` | `../src-master/system/generic/Mgrad3.c` plus `../src-master/api/c/edge.c` | M3-4 | already counted |
| `sflpad` | `../src-master/system/generic/Mlpad.c` | M3-4 | extensions only |
| `sfshot2cmp` | `../src-master/system/seismic/Mshot2cmp.c` | M3-5 | already counted |
| `sfpolymask` | `../src-master/system/generic/Mpolymask.c` | M3-6 | extensions only |

Extensions to these commands can improve behavior, tests, or docs, but they do
not create new command-surface numerator entries.

## Pythonic Convenience Not To Miscount

These names are useful Python-facing capabilities, but they must not be counted
as source-backed commands unless a future source audit proves command-level
alignment:

- `mean`;
- `rms`;
- `var`;
- `std`;
- `median`;
- `range`;
- `isnan`;
- `fillnan`;
- convenience-style `quantile` behavior when it differs from the audited source
  contract;
- current Ricker wavelet generator;
- current FFT-taper `bandpass` convenience;
- `demean`;
- `detrend`;
- `decimate`;
- `bandstop`;
- `notch`;
- `localrms`;
- `welch`;
- `welchcsd`;
- `transfer`;
- `whiten`;
- `specnorm`;
- `freqattr`;
- `firwin`;
- `firfilter`;
- `filtfilt`;
- `freqz`;
- `bandenergy`;
- `filterbank`;
- plotting quicklooks and workflow visualizations that do not implement VPlot or
  pen behavior.

The rule is simple: Pythonic convenience can be documented, tested, and useful
without increasing source-backed command coverage.

## Do-Not-Count / Do-Not-Repeat List

Do not count these categories as new command coverage:

- any already-counted M3 command listed above;
- aliases whose source surface was already counted;
- extensions to an existing counted command;
- Pythonic conveniences with related but different semantics;
- prototype workflow behavior;
- plotting quicklooks that do not implement VPlot;
- source audit notes without implementation;
- docs-only planning templates;
- release inventory updates;
- tests that only harden an existing counted command.

## Next Recommended Development Pattern

Use this pattern when source-backed command work resumes.

1. Start with read-only source audit.

2. Fill `SOURCE_AUDIT_WORKSHEET.md`.

3. Fill `SOURCE_COMMAND_TEMPLATE.md` for each candidate that still looks safe.

4. Default to implementing one command per pass.

5. Implement two commands only when both are extremely low risk, source mapping
   is clear, parameters are few, tests are easy, and duplicate-count risk is
   absent.

6. Do not default to implementing three commands.

7. After every two or three command passes, run a local release/coverage gate.

8. Treat medium-risk families as design-first work.

9. Stop with an audit conclusion when the source mapping, bounded subset, test
   plan, or Chinese comment plan is unclear.

# Source-Backed Command Candidate Backlog

G4-3 records a conservative candidate pool for future source-backed command
audits. This backlog is not approval to implement anything. Every candidate
needs a fresh source audit, the checklist in `SOURCE_COMMAND_ADMISSION.md`, and
an explicit decision before any code is changed.

`COVERAGE_AND_ROADMAP.md` remains the command-coverage authority. This file
does not change the numerator, denominator, CLI inventory, console-script
inventory, API surface, or compatibility promise.

## Ready For Future Low-Risk Audit

These candidates appear suitable for later low-risk audits, but none is
approved by this list. Each row still needs source reading, duplicate-count
checks, RSF axis/header contracts, bounded-subset design, tests, and docs.

| Candidate | Official source path | Family | Risk | Why possibly suitable | Required pre-check | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `sfmask` | `../src-master/system/main/mask.c` | mask / selection | low | direct metadata-aware mask/cut family is central RSF workflow | verify current mask/headerwindow/headercut coverage and alias counting | do not duplicate B-3 coverage |
| `sfreverse` | `../src-master/system/main/reverse.c` | axis transform | low | axis reversal can be NumPy in-memory | audit origin/header update rules and existing reverse convenience | likely direct `system/main` gap only if not already counted |
| `sfwindow` | `../src-master/system/main/window.c` | axis slicing | low | regular axis slicing is core RSF behavior | verify existing window/headerwindow/slice coverage and alias status | avoid re-counting Python slice convenience |
| `sfput` | `../src-master/system/main/put.c` | metadata | low | small metadata update subset may be useful | define safe key/value subset and passthrough limits | arbitrary header editing can become too broad |
| `sfdd` | `../src-master/system/main/dd.c` | format / copy | low-medium | bounded form conversion may be small | audit native/ASCII/XDR behavior and dtype contract | likely in-memory subset only |
| `sfpow` | `../src-master/system/generic/Mpow.c` | unary / axis gain | low | source is small enough to audit | verify existing `sftpow`/`pow` coverage and duplicate risk | likely already covered through axis-gain surface |
| `sfintshow` | `../src-master/system/generic/Mintshow.c` | table / display text | low | may be metadata/text-only | audit output type and whether it is display-only | may not suit `RSFData` chain |
| `sftclip` extensions | `../src-master/system/generic/Mtclip.c` | amplitude clip | low | source already mapped in M3-3 | identify unimplemented modes without new numerator | extension only; do not count as new command |
| `sfotsu` extensions | `../src-master/system/generic/Motsu.c` | threshold / statistic | low | source already mapped in M3-3 | confirm scalar/text output and no chain method | extension only; no duplicate count |
| `sfgrad` adjacent edge utilities | `../src-master/system/generic/Mgrad2.c`, `Mgrad3.c`, `../src-master/api/c/edge.c` | edge / mask | low | helper mapping is understood | find a distinct uncounted source before coding | `sfgrad2`/`sfgrad3` are already counted |
| `sflpad` extensions | `../src-master/system/generic/Mlpad.c` | axis / mask output | low | source already mapped in M3-4 | isolate mask/axis behaviors not yet supported | extension only; no new numerator |
| `sfpolymask` extensions | `../src-master/system/generic/Mpolymask.c` | polygon mask | low | source already mapped in M3-6 | define multidimensional or boundary behavior carefully | extension only; no new command count |
| `sfhistogram` extensions | `../src-master/system/generic/Mhistogram.c` | statistic | low | existing bounded histogram exists | verify source alignment and current coverage state | avoid counting convenience behavior twice |
| `sfslice` extensions | `../src-master/system/generic/Mslice.c` | axis slicing | low | small fixed-index slicing may be bounded | verify existing Stage C-2 slice coverage | likely already counted or extension-only |
| `sfintbin` extensions | `../src-master/system/seismic/Mintbin.c` | gather / binning | low-medium | existing subset has regular numeric table basis | audit side outputs, duplicate policy, SEG-Y lookup | extension only; geometry risk remains |
| `sfintbin3` extensions | `../src-master/system/seismic/Mintbin3.c` | gather / 3D binning | low-medium | existing subset has bounded numeric table basis | audit map/mask outputs and inverse modes | extension only; no duplicate count |
| `sfai2refl` / `sfrefl2ai` extensions | `../src-master/system/seismic/Mai2refl.c`, `Mrefl2ai.c` | impedance / reflectivity | low-medium | acoustic pair is already bounded | audit edge sample and side-input impedance behavior | do not expand into elastic reflectivity |

## Design-First Medium-Risk Families

These families should start with a design document or targeted audit pass, not
source-gap coding.

| Family | Why medium risk | Why not direct source-gap coding | Needed design | Needed tests |
| --- | --- | --- | --- | --- |
| Butterworth / bandpass / DSP filters | upstream `Mbandpass.c` uses recursive Butterworth helpers, not FFT taper convenience | current `bandpass` convenience is semantically different | filter state, phase, boundaries, axis metadata, and helper mapping | impulse/step responses, axis metadata, invalid bands, convenience no-miscount |
| Ricker trace convolution | upstream `Mricker1.c` is trace filtering/convolution, not only a wavelet generator | existing Ricker generator has a different contract | distinguish generator, filter, delay, normalization, and boundary modes | trace convolution fixture, source metadata, generator no-miscount |
| Shot/CMP/gather geometry | gather transforms depend on regular geometry, offset conventions, masks, and side outputs | already-counted `sfcmp2shot`/`sfshot2cmp` must not be duplicated | axis roles, half/full offset, positive orientation, mask side output, SEG-Y exclusion | inverse-pair fixtures, header axes, invalid geometry, side-output behavior |
| Reflectivity / AVO / elastic modeling | sources combine physical models, interpolation, Vp/Vs/rho, and angle behavior | small acoustic pairs should not imply elastic modeling support | physical parameter contract, units, interpolation, and bounded equations | normal-incidence fixtures, invalid units, unsupported elastic modes |
| Interpolation / stretch / remap | many sources share interpolation helpers, adjoints, stretch mutes, and side files | one-off commands risk inconsistent boundary and fill behavior | shared interpolation contract and axis update rules | endpoint/fill tests, adjoint exclusions, side-file validation |
| Velocity / semblance / scan | scan tools mix geometry, velocities, masks, weights, stretch, and picking | prototypes do not equal full `sfvscan` or NMO ecosystems | regular-gather contract, velocity axis, masks, stretch policy, output panels | true/wrong velocity fixtures, mask/weight tests, invalid axis tests |
| Plot display family | plot sources emit VPlot operations through pens/rendering state | Matplotlib quicklooks are Pythonic replacements, not VPlot clones | separate P-series display strategy and compatibility target | metadata-only tests if any, VPlot syntax tests only if deliberately supported |

## Deferred High-Risk Systems

These systems are not near-term source-backed command targets:

- migration, RTM, DMO, Kirchhoff, Gazdag, and wave-equation imaging;
- FWI, inversion systems, production solvers, and solver-heavy workflows;
- VPlot, pens, and rendering backend compatibility;
- SCons, book, and reproducible-paper infrastructure;
- MPI, CUDA, PETSc, IWAVE, RVL, and external execution ecosystems;
- `user/*` large command families and user-specific research codes.

## Already Completed M3 Commands

These commands are already mapped and must not be counted again:

| Command | Source mapping | Batch |
| --- | --- | --- |
| `sftclip` | `../src-master/system/generic/Mtclip.c` | M3-3 |
| `sfotsu` | `../src-master/system/generic/Motsu.c` | M3-3 |
| `sfrefl2ai` | `../src-master/system/seismic/Mrefl2ai.c` | M3-3 |
| `sfgrad2` | `../src-master/system/generic/Mgrad2.c` plus `../src-master/api/c/edge.c` | M3-4 |
| `sfgrad3` | `../src-master/system/generic/Mgrad3.c` plus `../src-master/api/c/edge.c` | M3-4 |
| `sflpad` | `../src-master/system/generic/Mlpad.c` | M3-4 |
| `sfshot2cmp` | `../src-master/system/seismic/Mshot2cmp.c` | M3-5 |
| `sfpolymask` | `../src-master/system/generic/Mpolymask.c` | M3-6 |

Extensions to these commands can improve behavior, tests, or docs, but they do
not create new command-surface numerator entries.

## Pythonic Convenience Not To Miscount

These names are useful Python-facing capabilities, but they must not be counted
as source-backed commands unless a future source audit proves command-level
alignment:

- statistics and non-finite conveniences: `mean`, `rms`, `var`, `std`,
  `median`, `range`, `isnan`, `fillnan`, and convenience-style `quantile`
  behavior when it differs from the audited source contract;
- current Ricker wavelet generator, which is not upstream trace-convolution
  `sfricker1`;
- current FFT-taper `bandpass` convenience, which is not Butterworth
  `Mbandpass.c`;
- signal and spectral conveniences from recent C-series batches: `demean`,
  `detrend`, `decimate`, `bandstop`, `notch`, `localrms`, `welch`,
  `welchcsd`, `transfer`, `whiten`, `specnorm`, `freqattr`, `firwin`,
  `firfilter`, `filtfilt`, `freqz`, `bandenergy`, and `filterbank`;
- plotting quicklooks and workflow visualizations that do not implement VPlot
  or pen behavior.

The rule is simple: Pythonic convenience can be documented, tested, and useful
without increasing source-backed command coverage.

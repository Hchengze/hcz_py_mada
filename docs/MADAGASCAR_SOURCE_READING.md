# Madagascar Source Reading Guide

G4-1 pauses command growth and records a source-architecture reading pass. It
is a planning document, not a compatibility promise and not a coverage
authority. `docs/COVERAGE_AND_ROADMAP.md` remains the command coverage
authority.

## Project Direction

pymadagascar is not a complete clone of Madagascar's 2000+ commands, and it is
not a standalone forward-modeling, DAS, localization, or seismic-demo library.

The near-term target is a locally durable, Pythonic toolkit for RSF data and
Madagascar-style command workflows. RSF I/O, axis/header handling, `RSFData`
chains, CLI modules, console scripts, tests, docs, and conservative coverage
mapping remain the main line. Source-backed commands must stay source-aligned;
Pythonic conveniences, workflows, and prototypes must not be counted as
source-backed command coverage.

## Source Tree Overview

The local Original Madagascar source tree at `../src-master` is broad:

- `system/main`: core RSF command-line utilities, including file operations,
  axis transforms, stack/spray/pad, scalar math, metadata, and direct
  stream-oriented tools.
- `system/generic`: general array, transform, filter, mask, interpolation,
  statistics, and numerical utilities. Many files are single-command `M*.c`
  programs, but several depend on helper code in `api/c`.
- `system/seismic`: seismic trace, gather, velocity, reflectivity, and
  geometry commands. This directory ranges from small trace transforms to
  high-risk modeling, interpolation, and velocity-analysis systems.
- `api/c`: shared C library routines for RSF I/O, axes, allocation,
  interpolation, triangle smoothing, Butterworth filters, Hilbert transforms,
  edge/Sobel operators, splines, operators, and numerical kernels.
- `plot/main` and `plot/lib`: VPlot-backed plotting commands. These are mostly
  rendering programs, not simple data transforms.
- `pens`, `book`, `scons`, `trip`, `su`, and `user/*`: plotting backends,
  reproducible-paper infrastructure, build systems, wave-equation or external
  solver ecosystems, Seismic Unix bridges, and user-contributed command
  families. These are not near-term command-surface targets.

## system/main Reading

Representative files read in G4-1: `scale.c`, `stack.c`, `pad.c`, and
`spray.c`.

Observed implementation pattern:

- Commands call `sf_init`, open `sf_input("in")` and `sf_output("out")`, read
  parameters with `sf_get*`, and read header values with `sf_hist*`.
- Axis numbers are 1-based in RSF metadata. `axis=2` means RSF axis 2, not
  NumPy dimension 2.
- Shape changes are expressed through `n#`, `o#`, `d#`, labels, and units.
  `pad.c` updates `n#` and shifts `o#` when leading samples are inserted.
  `spray.c` inserts a new axis and shifts higher axes.
- Several commands use streaming or native-byte copying. `pad.c` and
  `spray.c` work on `esize` bytes and preserve arbitrary data forms by copying
  native traces, not by interpreting every sample as float.
- Some commands expose multiple behaviors through executable aliases or
  program-name checks. `stack.c` can act as stack/min/max/product/RMS depending
  on parameters and program name.

Python migration guidance:

- Direct `system/main` work should preserve the RSF axis/header contract first.
- In-memory NumPy subsets are acceptable only when the bounded subset states
  what streaming/native-byte behavior is not implemented.
- Shape-changing commands need explicit tests for `n#`, `o#`, `d#`, label/unit
  preservation, no-in-place behavior, and NumPy shape order.

## system/generic Reading

Representative files read in G4-1: `Mclip.c`, `Mthreshold.c`, `Mcostaper.c`,
`Magc.c`, `Mgrad2.c`, and `Mpolymask.c`.

Observed implementation pattern:

- Simple unary commands such as `Mclip.c` are good low-risk candidates when
  dtype, parameter defaults, and non-finite behavior are clear.
- Quantile/stat commands often use whole-file behavior through `sf_filesize`
  and `sf_quantile`; they may be simple numerically but need clear axis/global
  semantics.
- Border filters such as `Mcostaper.c` read dimension arrays and use
  `sf_first_index` stride logic. They are still reasonable in NumPy if axis
  contracts are explicit.
- Smoothing and gain commands such as `Magc.c` depend on `api/c/triangle.c`.
  They are source-alignable only when the helper behavior is understood and
  documented.
- Edge commands such as `Mgrad2.c` depend on `api/c/edge.c`; helper-level
  source mapping is part of the command mapping.
- Mask commands such as `Mpolymask.c` are low-risk only when the input axis and
  side-input table contract are narrow and unambiguous.

Migration risks:

- Some generic commands look small but hide DSP, recursive filtering,
  interpolation, or adjoint behavior in `api/c`.
- Existing Pythonic conveniences with similar names must not be promoted to
  source-backed coverage unless their upstream semantics match.
- Streamed C behavior rarely needs byte identity in pymadagascar, but the
  bounded subset must say when it is in-memory and NumPy-backed.

## system/seismic Reading

Representative files read in G4-1: `Mnmo.c`, `Mslant.c`, `Mvscan.c`,
`Mshot2cmp.c`, `Mmodrefl.c`, and `Mlinsincos.c`.

Observed implementation pattern:

- Some seismic commands are bounded trace/gather transforms with regular axes,
  for example a small NMO subset, slant adjoint, or shot/CMP reorganization.
- Many seismic commands require side inputs such as velocity panels, offset
  vectors, masks, gradients, heterogeneity parameters, or model files.
- Velocity and semblance commands often combine geometry, interpolation,
  stretch mute, scan axes, optional masks, and alternative physical modes.
- Reflectivity/modeling commands such as `Mmodrefl.c` require multiple physical
  property inputs and interpolation kernels.
- Angle/velocity-grid programs such as `Mlinsincos.c` are numerical integration
  or model-domain transforms, not simple array utilities.

Migration guidance:

- Seismic additions need stricter axis comments than generic array utilities:
  `n1=time`, `n2=offset`, `n3=shot/CMP/panel` must be stated in code, tests,
  and docs.
- Regular small-gather subsets can be useful, but they must not grow into a
  separate production seismic-processing library.
- SEG-Y trace headers, irregular geometry, velocity picking, elastic modeling,
  and solver-style imaging remain deferred unless a later design pass narrows
  the scope.

## api/c Helper Reading

Representative files read in G4-1: `edge.c`, `triangle.c`, `butter.c`,
`hilbert.c`, and `interp.c`.

Observed implementation pattern:

- `edge.c` defines source-level Sobel and gradient stencils used by `Mgrad2.c`
  and `Mgrad3.c`; commands that use it should cite both the command source and
  the helper source.
- `triangle.c` implements reflected-boundary triangle/box smoothing with
  forward and adjoint variants. Python replacements must document boundary and
  adjoint limitations.
- `butter.c` implements recursive Butterworth low/high filters, including pole
  sections and in-place forward filtering. FFT taper conveniences are not the
  same behavior.
- `hilbert.c` implements FIR Hilbert transforms through iterative finite
  differences; an FFT analytic-signal convenience is related but not identical.
- `interp.c` contains small interpolation weight builders, but full commands
  often combine these with stretch, spline, regularization, or adjoint logic.

Helper mapping rule:

When a command depends materially on `api/c`, the source mapping should include
both the command file and the helper file. Tests should target the observable
bounded subset, not claim byte identity unless that has been explicitly
verified.

## plot/main Reading

Representative files read in G4-1: `graph.c`, `grey.c`, `wiggle.c`,
`vplotdiff.c`, and `bargraph.c`.

Observed implementation pattern:

- Most plot commands initialize VPlot through `rsfplot.h`, compute display
  scaling, and emit VPlot drawing operations.
- `grey.c` has special modes for byte/bar output, color tables, scalebars,
  clipping, gain power, orientation, and panel handling.
- `graph.c`, `bargraph.c`, and `wiggle.c` read RSF axes but then enter a VPlot
  rendering model rather than producing ordinary transformed RSF arrays.
- `vplotdiff.c` is a VPlot syntax/state comparator and depends on pen/VPlot
  internals.

Migration guidance:

- Existing `pymadagascar.plot` quicklooks are Pythonic/prototype replacements,
  not VPlot compatibility.
- Future plot work should be a separate P-series design, not mixed into M
  source-gap batches.
- A plot command should count as source-backed only if the implementation and
  tests deliberately cover the VPlot or metadata behavior being claimed.

## Current pymadagascar Implementation Map

Current main surfaces:

- Root package: conservative stable imports such as `RSFData`, RSF I/O types,
  axis/hypercube helpers, selected stable subsets, and optional hybrid helpers.
- Topic APIs: `generic`, `signal`, `seismic`, `io`, `plot`, `modeling`,
  `localization`, `imaging`, and `testing`.
- `RSFData`: chainable facade over NumPy arrays plus RSF metadata. Algorithm
  bodies should stay in topic modules.
- CLI modules: 167 runnable `python -m pymadagascar.cli.<name>` entry points.
- Console scripts: 65 registered `pymada-*` commands.
- Coverage authority: `docs/COVERAGE_AND_ROADMAP.md`, with release/inventory
  tools as consistency checks.

Covered source areas through M3-6:

- Most direct `system/main` command surface currently targeted by this project.
- Many `system/generic` array math, sampling, smoothing, transform, mask,
  interpolation, and statistics subsets.
- Several bounded `system/seismic` trace/gather/attribute transforms.
- Selected helper-level mappings in `api/c`, especially edge and smoothing
  helpers.

Pythonic convenience / prototype boundaries:

- Signal QC, spectral QC, FIR utilities, wavelet generation, FK/Radon/NMO
  prototypes, plotting quicklooks, modeling, localization, imaging, and
  operator/solver helpers may be useful, but they are not automatically
  source-backed commands.
- Existing convenience names such as bandpass, Ricker, mean/RMS/std/variance,
  plot quicklooks, and many spectral helpers must remain uncounted unless a
  later source audit proves command-level alignment.

## Why M3-Style Gap Hunting Must Slow Down

M3-3 through M3-6 successfully added a small set of low-risk source-backed
commands. The remaining gaps are more often ambiguous:

- Some names already exist as Pythonic conveniences with different semantics.
- Some sources depend on recursive filters, interpolation, velocity analysis,
  VPlot, or side-file geometry.
- Some apparent single commands are entry points into a larger family.
- Some commands are already counted through aliases or prior batches.

The next phase should be design-first. A candidate should be implemented only
after the source mapping, RSF axis/header contract, bounded subset, unsupported
upstream modes, tests, docs, and coverage effect are all clear.

## A. Low-Risk Source-Backed Candidates To Audit Later

These are not approved for immediate implementation; they are candidates for
future read-only audits and must still pass the usual source-alignment gate.

| Candidate | Area | Initial reason to audit | Key risk to check |
| --- | --- | --- | --- |
| `Mmask.c` / related mask utilities | generic | integer/float mask transforms may be small | avoid duplicating existing `sfmask` coverage |
| `Mbyte.c` | generic/plot-adjacent | byte scaling may be bounded | plotting/colorbar side behavior |
| `Mwindow.c` / direct window variants | main/generic | axis slicing is central RSF behavior | aliases and existing window coverage |
| `Mreverse.c` / direct reverse variants | main/generic | axis reversal is simple | axis origin/header update details |
| `Mput.c` small metadata subset | main | metadata-only behavior | command passthrough and arbitrary params |
| `Mdd.c` small form conversion subset | main | file-format utility | native/ASCII/xdr semantics |
| `Madd.c` uncovered aliases, if any | main | array add family is known | avoid alias double counting |
| `Mscale.c` remaining percentile modes | main | source already understood | current subset may not cover rscale/pclip |
| `Mstack.c` min/max/product aliases | main | same source family is understood | avoid duplicate numerator mistakes |
| `Mspike.c` remaining bounded options | main/generic | deterministic synthetic RSF | many parameters and header modes |
| `Mpolymask.c` extensions | generic | already implemented narrowly | do not count extensions as new commands |
| `Motsu.c` adjacent threshold helpers | generic | low-dimensional statistics | avoid duplicate threshold/otsu counting |
| `Mtclip.c` adjacent clipping modes | generic | simple amplitude behavior | source defaults and non-finite handling |
| `Mgrad*.c` adjacent edge utilities | generic | helper mapping understood | avoid duplicate grad2/grad3 counting |
| `Mintbin.c` / `Mintbin3.c` extensions | seismic | current regular integer binning exists | geometry and header assumptions |
| `Mai2refl.c` / `Mrefl2ai.c` extensions | seismic | simple acoustic impedance pair | edge samples and axis metadata |

## B. Medium-Risk Families Requiring Design First

- Butterworth/filter family: `Mbandpass.c` uses `api/c/butter.c` recursive
  filters. It is not equivalent to FFT taper `bandpass` convenience.
- Ricker family: upstream `Mricker1.c` is trace convolution/filter behavior,
  not just a wavelet generator.
- Shot/CMP/gather geometry family: `Mshot2cmp.c` and `Mcmp2shot.c` require
  regular geometry, mask side outputs, orientation, half/full offset, and
  byte-position behavior.
- Reflectivity and AVO modeling: `Mmodrefl.c`, `Mmodrefl2.c`, and related
  files combine physical property models, interpolation, and elastic formulas.
- Interpolation/stretch family: `stretch`, `fint1`, spline, and remap sources
  need a shared axis/interpolation design before more commands are added.
- Velocity/semblance/scan family: NMO, vscan, semblance, heterogeneity, masks,
  gradients, and velocity picking need bounded topic contracts.
- Plot data-to-display family: graph/grey/wiggle quicklooks need a separate
  plot strategy if they are ever to claim VPlot alignment.

## C. High-Risk Systems Deferred For Now

- Migration, RTM, DMO, Kirchhoff, Gazdag, wave-equation imaging.
- FWI, inversion, production solvers, IWAVE/RVL/TRIP, PETSc, MPI, CUDA.
- VPlot/pens/rendering backend compatibility.
- SCons/book/reproducible-paper systems.
- SEG-Y production trace-header workflows beyond current prototypes.
- `user/*` large command families and user-specific research codes.
- Full elastic modeling, anisotropy, angle-domain imaging, and velocity
  picking systems.

## D. Internal Project Cleanup Priorities

- Keep `api.py` as a dispatch layer. If it grows further, add grouping comments
  or an inventory pass before any behavior split.
- Keep `docs/COVERAGE_AND_ROADMAP.md` as the only coverage authority.
- Consider a machine-readable source mapping inventory only after the docs
  format stabilizes.
- Keep CLI/console-script drift guarded by `tools/check_cli_inventory.py`,
  `tests/test_cli_entrypoints.py`, and package metadata tests.
- Apply the Chinese comment guide to future core code, especially RSF
  axis/header transforms and source-backed bounded subsets.
- Continue using small command batches. A later M3-7 should start with a
  read-only audit and may choose zero commands.

## Recommended Next Route

1. Do not immediately resume blind source-gap coding.
2. If source-backed command work resumes, choose one family per pass and audit
   source, helper dependencies, existing Pythonic conveniences, and tests
   before editing.
3. Prefer low-risk metadata/axis/table/mask utilities over DSP, geometry,
   modeling, and rendering.
4. Treat medium-risk families as design tasks with explicit source maps and
   boundary docs before implementation.
5. Keep GitHub Actions Windows-only known issue paused unless local full pytest
   fails, both Ubuntu/Windows fail, or CI exposes a readable traceback.

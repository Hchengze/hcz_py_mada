# API and Compatibility

## Stability Levels

- `stable`: project-level API expected to remain usable with only compatible
  changes.
- `stable subset`: intentionally smaller Python subset of a Madagascar command
  or concept.
- `partial`: useful implementation with known missing parameters or modes.
- `prototype`: experimental geophysical or plotting behavior, tested on small
  fixtures but not production-grade.
- `simplified prototype`: intentionally simplified algorithmic model.
- `workflow-only`: route-level capability retained inside an example workflow;
  it is not a reusable or stable package API.
- `internal`: helpers used by APIs/CLIs, not public contract.
- `optional`: hybrid or original-comparison behavior that may be unavailable.

## Learning Notebook Status

`docs/PYMADAGASCAR_LEARNING_GUIDE.ipynb` is a learning and usage notebook for
the current feature families and their maturity labels. It is intentionally
concise and is not an API stability source or coverage source. This document
remains authoritative for stable, stable-subset, partial, prototype,
simplified-prototype, optional, and Pythonic-convenience boundaries.

## Topic Architecture T1 Boundary

Topic Architecture Pass T1 changes roadmap classification only. It adds no
public function, class, method, CLI module, console script, command-surface
coverage entry, or compatibility promise.

Future topic work must preserve the existing RSF contract: Madagascar axis
numbers are 1-based, NumPy storage reverses RSF axis order, and `n#/o#/d#`,
labels, units, dtype, and shape-changing behavior remain explicit. A topic data
or geometry contract may narrow accepted inputs for a workflow or fixture, but
must not silently reinterpret an existing stable API.

The first topic, seismic data signal analysis and processing, starts with
documented trace/panel/gather fixtures, pipeline validation, internal QC
metrics, bounded prototype hardening, and an integrated small-gather workflow
using existing APIs. Localization now has L0-1/L0-2 direct-module prototype
travel-time and fixed/variable-velocity grid-search primitives in
`pymadagascar.localization`, but no root/stable API, CLI, automatic picking,
uncertainty, or production location workflow. Forward modeling now has F0-1
geometry helpers, an F0-2 acquisition-driven single-shot wrapper, an F0-3
sequential multi-shot survey wrapper, and F0-4 explicit tensor/summary helpers,
F0-5 synthetic velocity model builders, and an F0-6 workflow-level validation
example, but no root/stable API, CLI, interpolation,
smoothing/random/geologic model builder, default survey tensor return, padding
policy, or production modeling claim.
Imaging remains a simplified prototype.
Inversion may first design operator composition, regularization, objective,
residual, and history contracts without promoting a domain inversion API. DAS
travel-time and least-squares helpers remain workflow-only, and SEG-Y trace
headers remain separate from ordinary RSF metadata and the minimal numeric
header table.

## Seismic Topic S1 Internal Contracts

`pymadagascar.testing.seismic_fixtures` is internal testing infrastructure. Its
fixture functions are not imported by `pymadagascar`, `pymadagascar.api`, or
`pymadagascar.testing.__init__`, and are not stable public processing APIs.
S1 does not promote NMO, semblance, FK, Radon, modeling, imaging, or inversion
maturity.

The S1 trace contract is a finite real `float32` or `float64` array with NumPy
shape `(ntime,)`. RSF axis 1 is time: `n1=ntime`, finite `o1`, positive `d1`,
`label1=Time`, and `unit1=s`. Amplitude units are recorded separately by
`amplitude_unit`; optional fixture metadata may describe frequencies, event
times, seed, and fixture kind. Existing trace-preserving signal/QC operations
retain shape and time metadata unless their documented contract changes an
axis.

The S1 panel contract uses NumPy shape `(nchannel, ntime)` and RSF dimensions
`(n1=ntime, n2=nchannel)`. Axis 1 is time. Axis 2 is one regularly sampled
channel/trace coordinate with positive `d2`, explicit `label2/unit2`, and an
`axis2_role`. S1 fixtures do not encode non-regular coordinates in an ordinary
RSF header.

The S1 gather contract specializes the panel as a regular signed-offset
CMP-like gather: `label2=Offset`, `unit2=m`, and
`offset_sign_convention=receiver_minus_source`. Negative offsets are receivers
on the negative side of the source and positive offsets are on the positive
side. Full source/receiver geometry is not encoded. An explicit offset RSF may
be used only by an existing API that explicitly accepts it and remains a
separate length-matched input. Ordinary RSF metadata, the minimal numeric
header table, and SEG-Y trace headers remain separate models.

The S1 workflow is an internal contract regression that composes existing
demean, detrend, bandpass, AGC, mutter, stack, PSD, RSF I/O, and plotting APIs.
It does not create a new processing API or compatibility promise.

## Seismic Topic S2 Internal Metrics Contract

`pymadagascar.testing.seismic_metrics` is internal testing infrastructure. Its
trace, panel, gather-pipeline, comparison, and JSON-writing helpers are not
imported by `pymadagascar`, `pymadagascar.api`, or
`pymadagascar.testing.__init__`. They are not stable public processing or QC
APIs.

S2 metrics use explicit sample windows and physical frequency bands. For the
S2 workflow, SNR and frequency metrics compare the detrended gather immediately
before and after the existing bandpass operation. Final output RMS and mute
coverage describe the AGC/mutter result, while stack peak and noise-reduction
metrics describe the final mean stack. This stage ownership prevents AGC
amplitude scaling from being misreported as filter SNR improvement.

The `s2_qc_report.json` structure is deterministic and path-free, but it is an
internal workflow/testing contract rather than a public file-format guarantee.
Fields or thresholds may change in a later topic pass when supported by new
fixtures and validation evidence. S2 does not promote NMO, semblance, FK,
Radon, localization, inversion, modeling, or imaging maturity.

## Seismic Topic S3 NMO Prototype Contract

S3 does not add a new public API and does not reclassify NMO as stable. The
existing `pymadagascar.seismic.nmo_correct` / `inverse_nmo` and `nmo` CLI
remain prototype surfaces. This pass narrows and documents their supported
fixture-backed behavior for small regular CMP-like gathers.

The S3 data contract accepts finite real gathers with RSF axis 1 as time and
axis 2 as signed offset. Time sampling must have finite `o1`, positive finite
`d1`, and at least two samples. Without explicit `offset=`, the regular offset
axis must have finite `o2` and positive finite `d2`; with explicit `offset=`,
the offset vector must be finite and length-compatible. Velocity must be finite
and strictly positive. Non-finite input samples, non-finite velocity or offset
values, invalid axis spacing, and invalid `h0`/`stretch` parameters are rejected.

The S3 geometry contract inherits S1's
`offset_sign_convention=receiver_minus_source` and uses `abs(offset)` in the NMO
equation. S1 fixtures store full signed offsets, so the S3 workflow runs the
existing prototype with `half=no`; `half=yes` remains the existing half-offset
option. S3 does not add velocity scan, semblance expansion, residual NMO,
anisotropic/nonhyperbolic moveout, trace-header tables, SEG-Y trace-header
coupling, or production stretch-mute behavior.

The `s3_nmo_qc_report.json` structure is deterministic and path-free, but it is
an internal workflow/testing report rather than a public file-format guarantee.
It records flattening, correct-vs-wrong velocity behavior, stack peak, noise,
finite-value, and header-axis checks for the S1 fixture. S1/S2 testing helpers
remain internal and are still not imported by `pymadagascar`,
`pymadagascar.api`, or `pymadagascar.testing.__init__`.

## Seismic Topic S4-0 Source Alignment

S4-0 adds no API and does not change any maturity label. It is a
documentation-only audit rule for seismic prototypes: when a classic
Madagascar source exists under `../src-master`, that source must be inspected
before a Python prototype is hardened or advertised as aligned behavior.

The audit records these boundaries:

- NMO remains a prototype even after S3. It is validated for small regular
  fixture-backed gathers, but it is not a full `sfnmo`/`sfinmo` clone.
- Semblance remains a prototype. S4-1 hardens its bounded S1/S2/S3-backed
  contract, but it is still not a full `sfvscan` implementation.
- FK and FK-filter remain prototypes / Pythonic conveniences. The current
  implementation is not a direct clone of `sfdipfilter`, and no single
  `system/seismic/Mfk.c` equivalent was located.
- Radon remains a prototype. The current direct time-domain operator pair is
  not high-resolution `sfradon` and does not implement solved least-squares
  inversion.

Pythonic implementations may intentionally differ from Madagascar, but the
difference must be documented and backed by deterministic tests before any
boundary is narrowed or maturity is raised.

## Seismic Topic S4-1 Semblance Prototype Contract

S4-1 adds no stable public API and does not reclassify Semblance as stable. The
existing `pymadagascar.seismic.semblance_scan` function and `semblance` CLI
remain prototype surfaces. This pass only hardens their behavior for the
documented S1/S2/S3 small-gather contract and records source alignment against
`../src-master/system/seismic/Mvscan.c`.

The S4-1 data contract accepts finite real CMP-like gathers with RSF axis 1 as
time and RSF axis 2 as signed offset. Time sampling must have finite `o1`,
positive finite `d1`, and at least two samples. Without explicit `offset=`, the
regular offset axis must have finite `o2` and positive finite `d2`; with
explicit `offset=`, the offset vector must be finite and length-compatible.
Velocity scan values from `vmin/vmax/dv` must be finite and strictly positive.
Non-finite input samples, invalid velocity ranges, invalid time/offset axes,
invalid `h0`/`stretch`/`smooth` values, and offset length mismatches are
rejected with `SemblanceError`.

The S4-1 geometry contract inherits S1's
`offset_sign_convention=receiver_minus_source` and uses `abs(offset)` through
the existing NMO helper. Velocity units are derived from offset/time metadata
when both units are present. The output panel has RSF axis 1 as time and axis 2
as velocity with `axis2_role=velocity`; input-offset provenance is recorded in
`semblance_input_*` metadata. Full source/receiver geometry, non-hyperbolic
moveout, anisotropy, SEG-Y trace headers, mask/weight handling, and field-scale
velocity analysis are not part of the contract.

The S4-1 validation contract uses the S1 hyperbolic gather to check that the
semblance response peaks near the true velocity, that wrong velocity is weaker,
that velocity-axis and input-offset metadata are explicit, that finite values
are preserved, and that the workflow JSON is deterministic and path-free. The
`s4_semblance_qc_report.json` structure is an internal workflow/testing report,
not a public file-format guarantee. S1/S2 internal helpers remain internal and
are not imported by `pymadagascar`, `pymadagascar.api`, or
`pymadagascar.testing.__init__`.

The current Python implementation is not a full `sfvscan` clone. Upstream
`Mvscan.c` supports additional modes and parameters such as differential and
AVO semblance, weights, masks, slowness/squared-velocity conventions, stretch
controls, and optional offset files. S4-1 documents those differences and tests
the bounded Pythonic subset instead of claiming full compatibility.

## Seismic Topic S4-2 Small-Gather Geometry Contract

S4-2 adds no stable public API. The new
`pymadagascar.testing.seismic_geometry` module is internal testing
infrastructure and is not imported by `pymadagascar`, `pymadagascar.api`, or
`pymadagascar.testing.__init__`. Its helpers may change as later topic
fixtures mature.

The regular offset contract keeps the S1/S3/S4-1 layout: finite small gather
data, NumPy shape `(ntrace, ntime)`, RSF axis 1 as time, and RSF axis 2 as
signed offset represented by `o2/d2/n2`. The offset sign convention is
`receiver_minus_source`, offset units are meters, time units are seconds, and
velocity units are checked as meters per second for the current fixtures.

The explicit offset-vector contract is a separate 1D trace-compatible
coordinate input. It must be finite, length-compatible with the trace count,
and carry unit/sign-convention metadata. Irregular offsets must enter through
that explicit vector; they are not inferred from trace order or hidden in an
ordinary RSF axis.

The minimal source/receiver table contract is a small deterministic numeric
fixture with fields `trace`, `source_x`, `receiver_x`, `offset`, `midpoint`,
`channel`, `source_id`, and `receiver_id`. It validates
`offset = receiver_x - source_x` and
`midpoint = 0.5 * (source_x + receiver_x)`. It is not a SEG-Y trace-header
model, not a synchronized production header-table/data-volume system, and not a
survey database.

The `s4_geometry_report.json` structure is deterministic and path-free, but it
is an internal workflow/testing report rather than a public file-format
guarantee. S4-2 does not promote NMO, Semblance, FK, Radon, localization,
inversion, modeling, imaging, SEG-Y, or header-table maturity.

## Seismic Topic S4-3 FK Prototype Contract

S4-3 adds no stable public API and does not reclassify FK as stable. The
existing `pymadagascar.seismic.fk_spectrum` / `fk_filter` functions and the
existing `fk` / `fkfilter` CLI modules remain prototype surfaces. This pass
hardens their bounded small-panel behavior and records source alignment:
recursive source search found no direct `../src-master/**/Mfk.c`; the nearest
filter reference is `../src-master/system/generic/Mdipfilter.c`, while
`Mfkamo.c`, `Mfkdmo.c`, and `Mfkgdmo.c` are FK-domain AMO/DMO/GDMO programs,
not generic FK spectrum equivalents.

The S4-3 data contract accepts finite real or complex 2D panels with NumPy
shape `(nspace, ntime)`, RSF axis 1 as time, and RSF axis 2 as a regular
channel/offset/spatial coordinate. Axis origins must be finite and axis
spacings must be finite and positive. `fk_spectrum` writes either `float32`
amplitude spectra or `complex64` spectra; `fk_filter` writes time-space data
with the input-compatible real or complex dtype policy. Non-finite samples,
non-finite frequency/wavenumber vectors, and non-finite fan-filter parameters
are rejected with `FKError`.

The S4-3 geometry contract is regular-spatial-axis only. Axis 2 may represent
regular channel spacing or regular signed-offset spacing, but explicit offset
vectors from S4-2 are not consumed by the current FK transform. Irregular
geometry must not be inferred from trace order. SEG-Y trace headers and
minimal numeric header tables do not participate in FK operations.

The validation contract uses deterministic plane-wave panels to check that the
FK peak lands near the analytic frequency/wavenumber, that positive and
negative slopes occupy opposite wavenumber signs, that the raw-gather fan
filter preserves a target apparent velocity and suppresses a reject velocity,
that frequency/wavenumber metadata are explicit, and that the workflow JSON is
deterministic and path-free. The `s4_fk_qc_report.json` structure is an
internal workflow/testing report, not a public file-format guarantee.

The current Python implementation is not a full `sfdipfilter` clone.
`Mdipfilter.c` filters already FK-domain data with `v1/v2/v3/v4`, `pass=`,
`angle=`, optional 3D behavior, and sine-taper edges. The Python `fk_filter`
keeps a raw-gather convenience contract with `vmin/vmax/taper/reject` and an
internal centered FFT/IFFT. That difference is intentional and tested, but it
does not imply Madagascar compatibility beyond the documented fixture subset.

## Seismic Topic S5 Integrated Workflow Boundary

S5 adds no stable public API and does not reclassify NMO, Semblance, FK, Radon,
localization, inversion, modeling, or imaging. The new
`examples/my_workflows/seismic_small_gather_processing_workflow.py` is an
example workflow that composes existing S1/S2/S3/S4 internal/testing contracts
and existing prototype calls. It is not imported by `pymadagascar`,
`pymadagascar.api`, or `pymadagascar.testing.__init__`.

The `s5_integrated_qc_report.json` structure is deterministic and path-free,
but it is an internal workflow/testing report rather than a public file-format
guarantee. It records geometry, preprocessing metrics, NMO true-vs-wrong
velocity behavior, Semblance peak behavior, FK finite/header/energy checks, and
stack ratios for the S1 small-gather fixture only.

S5 intentionally avoids new algorithms. It does not add velocity picking, full
velocity analysis, Radon/slant, full `sfvscan`, full `sfdipfilter`, SEG-Y trace
headers, DAS adapters, production survey geometry, field-scale processing,
localization, inversion, forward modeling, imaging, or C++ kernels.

## Seismic Topic S6-0 Summary Boundary

S6-0 is a documentation-only Seismic Topic v0 summary and next-route decision.
It adds no stable public API, no internal helper, no workflow, no CLI surface,
and no command-surface coverage. It does not re-export or promote any S1-S5
testing helper, workflow JSON report, NMO/Semblance/FK/Radon prototype, or
geometry fixture contract.

The recommended next seismic task is Radon/slant source-aligned design before
implementation. That recommendation is an API boundary, not a new guarantee:
the current Radon pair remains a prototype direct time-domain forward/adjoint
operator, not `sfslant`, not high-resolution `sfradon`, and not a solved
least-squares inversion framework.

## Seismic Topic S6-1 Radon/slant Design Boundary

S6-1 is a documentation-only Radon/slant source audit and route decision. It
adds no stable public API, no internal helper, no workflow, no CLI surface, and
no command-surface coverage. It does not change or re-export
`pymadagascar.seismic.radon`, `pymadagascar.cli.radon`, or
`pymadagascar.cli.iradon`.

The current Radon implementation remains a Pythonic direct time-domain
forward/adjoint prototype. `radon` writes `A^T d`; `iradon` models `A m`; the
reserved `least_squares=True` path is still not implemented. This prototype is
not `sfslant`, not high-resolution `sfradon`, not a sparse or spiking Radon
inversion, and not a stable production velocity-analysis component.

S6-1 selects a staged route, not a new guarantee: first pursue a bounded
`sfslant`-style small slant-stack contract/validation pass if implementation
continues; defer high-resolution `sfradon` alignment until operator and
inversion foundations are mature enough to carry Toeplitz/CG, objective,
regularization, and diagnostics contracts.

## Seismic Topic S6-2 Small Slant-Stack Contract

S6-2 adds no stable public API and does not reclassify Radon/slant as stable.
The existing `pymadagascar.seismic.radon` functions and `radon` / `iradon` CLI
modules remain prototype surfaces. This pass hardens their small deterministic
slant-stack behavior and documents the operator direction:

- `linear_radon` / CLI `radon` apply the adjoint slant stack `m = A^T d`.
- `inverse_linear_radon` / CLI `iradon` apply modeling `d = A m`.
- `iradon` is not a solved inverse, not a least-squares solver, and not a
  high-resolution Radon inversion.

The S6-2 supported subset is finite real 2D data or model arrays, positive
finite time-axis sampling, positive finite regular offset or p-axis sampling,
finite length-compatible explicit offsets, finite regularly sampled p/slowness
values, and deterministic linear interpolation for small fixtures. Invalid
axes, non-finite samples, invalid p ranges, reversed p axes, explicit-offset
length mismatches, and reserved least-squares requests are rejected with
explicit errors.

S6-2 adds prototype header metadata such as `radon_direction`,
`radon_operator_form`, `axis2_role`, `radon_madagascar_reference`, and
`radon_sfradon_equivalence`. These keys clarify workflow/testing behavior; they
are not a stable public file-format guarantee.

The `s6_slant_stack_qc_report.json` structure is deterministic and path-free,
but it is an internal workflow/testing report. S6-2 is source-aligned with
`../src-master/system/seismic/Mslant.c` and `slant.c` only as a small shared
slant-stack subset. It is not a full `sfslant` clone and does not implement rho
filtering, anti-aliased stretch, reference-slope behavior, or multi-panel
batching. It is also not `sfradon`, not frequency-domain high-resolution
Radon, and not Toeplitz/CG/spiking inversion.

## Seismic Topic S7-0 Closeout Boundary

S7-0 adds no stable public API, internal helper, workflow, CLI surface, test,
or command-surface coverage. It does not re-export or promote any S1-S6-2
testing helper, workflow JSON report, NMO/Semblance/FK/Radon prototype, or
geometry fixture contract.

Seismic Topic v0 is now a small fixture-backed regression harness, not a
stable seismic processing framework. NMO, Semblance, FK, and Radon remain
prototype surfaces. The S1/S2/S4-2 helper modules remain internal/testing; S5
and S6-2 JSON reports remain workflow/internal artifacts rather than public
file-format guarantees.

The recommended next topic is Inversion / Operator Foundation, but S7-0 does
not add an inversion API. The next topic should first define contracts for
operator composition, regularization, objective/residual/history records,
stopping diagnostics, and preconditioning before adding reusable inversion
implementation or high-resolution `sfradon`.

## Inversion / Operator Foundation I0-0 Boundary

I0-0 adds no public API, stable API, CLI surface, workflow, solver, or command
coverage. It is an audit/design pass over existing B-4 operator tools,
Radon/slant operator direction, workflow-only D-1 least-squares helpers, and
forward/direct geophysical prototypes.

The existing `LinearOperator`, `MatrixOperator`, `CallableLinearOperator`,
`IdentityOperator`, real/complex dot-test helpers, and real/complex
conjugate-gradient helpers remain the current small-data operator subset. I0-0
does not add operator composition, block operators, stacked operators,
regularization operators, CGLS, LSQR, preconditioners, or a reusable inversion
problem object.

The I0-0 data/operator/solver contracts are roadmap boundaries, not new API
guarantees. They require future work to make model/data shapes, dtype policy,
finite-value policy, RSF flatten/unflatten metadata, forward/adjoint direction,
dot-test tolerance, residual vectors, stopping diagnostics, and solver-history
records explicit before any domain inversion is promoted.

Future history JSON should remain internal/testing until a later pass
deliberately promotes a schema. I0-0 does not promote high-resolution Radon,
imaging inversion, velocity inversion, DAS inversion, acoustic2d, Kirchhoff, or
workflow-only least-squares helpers to stable public APIs.

## Inversion / Operator Foundation I0-1 Boundary

I0-1 adds no stable public API, CLI surface, console script, solver, workflow,
or command-surface coverage. It adds prototype/testing operator algebra and
diagnostic containers inside `pymadagascar.generic.linear_operator` only.

The I0-1 direct-module prototype classes are:

- `ScaledOperator`: `alpha * A`, with complex adjoint scaling by
  `conj(alpha)`.
- `SumOperator`: `A + B`, requiring identical model and data shapes.
- `ComposedOperator`: `A @ B`, meaning `A(Bx)`, requiring the inner range to
  match the outer domain.
- `StackedOperator`: vertical `[A; B; ...]`, requiring a shared domain and
  concatenating flattened data-space outputs.
- `SolverIterationRecord`, `SolverHistory`, and `SolverResult`: internal/
  prototype solver diagnostics with deterministic JSON-serializable
  summaries.

These names are not imported by `pymadagascar.__init__` or
`pymadagascar.api`. Their summaries are internal/testing artifacts, not a
public JSON schema. Existing `conjugate_gradient`,
`conjugate_gradient_normal`, `conjgrad_solve`, and `complex_conjgrad_solve`
keep their current return contracts and are not wired to the new history
containers in this pass.

I0-1 also tightens finite-value checks in the small in-memory operator path.
Matrix-backed and callable operators are still small-data Python objects, not
Madagascar external pipe operators. The project still lacks reusable
regularization operators, objective/residual integration, CGLS/LSQR,
preconditioners, and a reusable inversion-problem API.

## Inversion / Operator Foundation I0-2 Boundary

I0-2 adds no stable public API, CLI surface, console script, solver, workflow,
or command-surface coverage. It adds only small in-memory regularization
operators inside `pymadagascar.generic.linear_operator`.

The I0-2 direct-module prototype classes are:

- `DiagonalRegularization`: `Lx = w * x`, requiring finite weights compatible
  with the model shape. Complex weights are allowed, and the adjoint uses
  `conj(w) * y`.
- `FirstDifferenceRegularization`: flattened valid-boundary forward
  difference, `x[i + 1] - x[i]`, returning `model_size - 1` samples with an
  exact matching adjoint.
- `SecondDifferenceRegularization`: flattened valid-boundary second
  difference, `x[i] - 2*x[i + 1] + x[i + 2]`, returning `model_size - 2`
  samples with an exact matching adjoint.

Damping regularization is represented by the existing scaled identity pattern,
for example `lambda * IdentityOperator(shape)`, rather than a new solver or
special damping API. These classes are not imported by `pymadagascar.__init__`
or `pymadagascar.api`. They are prototype/testing building blocks for later
least-squares problem formulation, not a production inversion framework.

I0-2 does not wire regularization into `conjugate_gradient`,
`conjugate_gradient_normal`, `conjgrad_solve`, or `complex_conjgrad_solve`.
It does not add CGLS, LSQR, high-resolution Radon inversion, DAS inversion,
imaging inversion, velocity inversion, preconditioners, constraints, masks,
or a reusable inversion-problem object.

## Inversion / Operator Foundation I0-3 Boundary

I0-3 adds no stable public API, CLI surface, console script, solver, workflow,
example, or command-surface coverage. It adds only small in-memory
least-squares problem/objective/diagnostics structures inside
`pymadagascar.generic.linear_operator`.

The I0-3 direct-module prototype classes are:

- `LeastSquaresProblem`: evaluates `A x - b`, optional `lambda L x`, the
  concatenated residual, objective terms, and the normal-equation gradient for
  small in-memory `LinearOperator`-compatible operators.
- `ObjectiveDiagnostics`: records objective, data and regularization objective
  terms, residual norms, optional gradient norm, iteration, convergence flag,
  stopping reason, and JSON-safe metadata.
- `StoppingDiagnostics`: records or classifies a small stopping state with
  `residual_tolerance`, `objective_tolerance`, `gradient_tolerance`,
  `max_iterations`, `not_converged`, and `invalid_state` reasons.

These names are not imported by `pymadagascar.__init__` or
`pymadagascar.api`. Their JSON summaries are internal/prototype diagnostics,
not a public report schema. Complex problems are supported for in-memory
operators whose forward/adjoint methods obey the Hermitian dot-test contract;
objectives use `0.5 * vdot(r, r).real`.

I0-3 does not run or modify a solver. Existing `conjugate_gradient`,
`conjugate_gradient_normal`, `conjgrad_solve`, and `complex_conjgrad_solve`
keep their current return contracts and are not wired to the problem layer,
regularization layer, `SolverHistory`, or `StoppingDiagnostics`.

## Inversion / Operator Foundation I0-4 Boundary

I0-4 adds no stable public API, CLI surface, console script, new solver,
workflow, example, or command-surface coverage. It adds two direct-module
prototype adapters in `pymadagascar.generic.linear_operator`:

- `run_cg_with_history` runs the existing SPD/Hermitian CG iteration core and
  returns `SolverResult` plus `SolverHistory`. Record `residual_norm` is the
  linear-system residual, `objective` is explicitly residual energy
  `0.5 * ||r||^2`, and `gradient_norm` equals that residual norm.
- `run_cgnr_with_history` runs the existing normal-equation CG core. It uses
  `LeastSquaresProblem` to record data/regularization residuals and objective;
  record `residual_norm` is the augmented least-squares residual. Convergence
  remains governed by the normal-equation residual, which is preserved in
  record/result metadata.

Both adapters record iteration zero, completed iteration residuals, optional
step lengths, `max_iterations`, tolerance, convergence, and one of
`residual_tolerance`, `max_iterations`, or `invalid_state`. The tracked path
turns zero-curvature breakdown into an `invalid_state` result; the established
default CG function still raises the original `LinearOperatorError`. Real and
complex operators share the same history contract and use Hermitian products
where appropriate.

The existing `conjugate_gradient`, `conjugate_gradient_normal`, complex
aliases, dispatch helpers, `ConjugateGradientResult`, and CLI output remain
unchanged. The new adapters are not imported by `pymadagascar.__init__` or
`pymadagascar.api`; their JSON summaries remain internal/prototype schemas.

I0-4 CGLS/LSQR design conclusion:

- Current CGNR applies CG to `A^H A x = A^H b` (plus scalar damping). CGLS is
  closely related in exact arithmetic but should iterate with `A` and `A^H`
  directly, report data/gradient residuals explicitly, and consume
  `LeastSquaresProblem` rather than being presented as an alias for CGNR.
- A bounded CGLS implementation should accept `LeastSquaresProblem`, initial
  model, iteration limit, tolerance, and optional history. General
  regularization should be represented by the augmented operator/data pair
  `[A; lambda L]` and `[b; 0]`, reusing `StackedOperator`.
- Preconditioning requires a separate model/data-space and adjoint contract.
  It is not part of the first unpreconditioned CGLS subset.
- LSQR should remain a separate later implementation based on Golub-Kahan
  bidiagonalization, with its own condition/residual stopping diagnostics. It
  must not be a name alias for CGNR or CGLS.
- CGLS and LSQR are not implemented in I0-4. Radon LS, DAS inversion, imaging
  inversion, and production inversion remain deferred.

Source alignment records `../src-master/system/main/conjgrad.c` and
`cconjgrad.c` as external-command drivers and `../src-master/api/c/conjgrad.c`
and `cconjgrad.c` as shaping/preconditioning library solvers. A domain-specific
CGLS implementation exists in `../src-master/user/pyang/Mmwni2d.c`; no generic
`system/main` CGLS program was located. LSQR references were located in the
book MATLAB file `../src-master/book/slim/geo2008NewInsightsPareto/Matfcts/private/lsqr.m`
and RVL C++ header `../src-master/trip/rvl/umin/include/lsqr.hh`, not as a
pure-C core `system/main` solver suitable for direct cloning.

## Inversion / Operator Foundation I0-5 Boundary

I0-5 adds bounded unpreconditioned CGLS only as a direct-module prototype in
`pymadagascar.generic.linear_operator`:

- `run_cgls(A, b, ...)` constructs an unregularized `LeastSquaresProblem`.
- `run_cgls_problem(problem, ...)` consumes an existing problem and reuses
  `[A; lambda L]` / `[b; 0]` through `StackedOperator` when regularization is
  active.
- The iterative data residual is `b - A x`; a regularized recurrence uses the
  augmented residual `[b - A x; -lambda L x]`. Objective and displayed
  residual terms remain owned by `LeastSquaresProblem`.
- Convergence uses `||A_aug^H r_aug|| <= tol * max(||g0||, 1)`. Stopping
  reasons are `gradient_tolerance`, `max_iterations`, and `invalid_state`.
- Real and complex operators share the same implementation; complex adjoints
  remain Hermitian and norms use `vdot`.
- Results reuse `SolverResult` and optional/default-on `SolverHistory`.

These functions are not imported by `pymadagascar.__init__` or
`pymadagascar.api`. I0-5 adds no CLI, console script, coverage entry, LSQR,
preconditioner, constraints, production scaling, or domain inversion.

## Inversion / Operator Foundation I0-6 Boundary

I0-6 defines a preconditioner contract. It was introduced before solver
integration, and I0-8A/I0-8B now consume it from the CGLS prototype:

- `Preconditioner` is a semantic `LinearOperator` subclass. Its required
  `forward` and Hermitian `adjoint` make the transform composable with future
  CGLS/LSQR operator recurrences.
- `IdentityPreconditioner` preserves the latent model. `DiagonalPreconditioner`
  applies real or complex model-space scaling; zero weights are rejected
  because this contract is invertible scaling, not a mask or constraint.
- `as_preconditioner` accepts only explicit preconditioner instances, diagonal
  arrays, or `None` plus a model shape. It deliberately rejects ordinary
  `LinearOperator` objects so a regularization operator cannot silently change
  semantic role.
- `PreconditionerDiagnostics` reports kind, domain/range shapes, identity/
  diagonal flags, scale range, a diagonal condition hint, complex support, and
  JSON-safe metadata.

The selected direction is right/model-space preconditioning: `x = M z`, solve
with `A @ M`, and reconstruct with `M.forward(z)`. For a regularized problem,
the latent system is `[A; lambda L] @ M z ~= [b; 0]`. Regularization
changes the objective; preconditioning changes variables/scaling and intended
convergence behavior. Left/data-space weighting `W(Ax-b)` is documented as a
different future contract and is not implemented here.

I0-8A/I0-8B extend `run_cgls` and `run_cgls_problem` with an optional
`preconditioner=` argument. The solver minimizes `0.5 * ||A M z - b||**2`,
or `[A M; lambda L M] z ~= [b; 0]` for active regularization, but returns the
model-space solution `M z_final`. Result metadata distinguishes the latent
normal residual used for convergence from the model-space gradient/objective
reported by `LeastSquaresProblem`, and carries preconditioner diagnostics such
as kind, identity/diagonal flags, condition hint, and scale range. This remains
a direct-module prototype with no root/API export, CLI, LSQR, constraints,
masks, or domain inversion.

## Inversion / Operator Foundation I0-9B1 Boundary

I0-9B1 adds bounded unpreconditioned LSQR only as a direct-module prototype in
`pymadagascar.generic.solvers` and the compatibility re-export layer
`pymadagascar.generic.linear_operator`:

- `run_lsqr(A, b, ...)` constructs an unregularized `LeastSquaresProblem`.
- `run_lsqr_problem(problem, ...)` consumes an existing problem and reuses the
  same `[A; lambda L]` / `[b; 0]` augmented regularization path as CGLS.
- The recurrence is a small pure-Python Golub-Kahan bidiagonalization loop for
  deterministic in-memory problems. It is not a full Madagascar command port.
- Nonzero `x0` remains a model-space initial model. The implementation solves a
  shifted correction problem with `r0 = b_aug - A_aug x0` and returns
  `x0 + dx`.
- Residual diagnostics use the `b - A x` convention. Objective, data residual,
  regularization residual, and model-gradient diagnostics remain owned by
  `LeastSquaresProblem`; convergence residual metadata names the data or
  augmented least-squares space explicitly.

These functions are not imported by `pymadagascar.__init__` or
`pymadagascar.api`. I0-9B1 adds no CLI, console script, command-surface coverage,
stable root/API export, right-preconditioned LSQR, left/data-space weighting,
constraints, masks, domain inversion, production scaling, or coverage denominator
change. Passing `preconditioner=` to LSQR raises an explicit prototype-boundary
error instead of silently ignoring it.

## Localization Topic Prototype Boundary

L0-1 starts the localization topic with a small pure-Python prototype module,
`pymadagascar.localization.traveltime`; L0-2 extends that module with
homogeneous variable-velocity grid search. The module is importable directly
from the localization package but is not imported by `pymadagascar.__init__`
or `pymadagascar.api`, and it does not add a CLI, console script, or
command-surface coverage entry.

The supported contract is deliberately narrow:

- `euclidean_distance_2d(points, origin)`: finite local 2D distances for
  arrays shaped `(..., 2)`.
- `direct_travel_time_2d(source_xy, receiver_xy, velocity)`:
  `||receiver - source|| / velocity` for positive finite homogeneous velocity.
- `diffraction_travel_time_2d(source_xy, receiver_xy, diffractor_xy, velocity)`:
  `(||diffractor - source|| + ||receiver - diffractor||) / velocity`.
- `travel_time_residuals(predicted, observed, weights=None)`: residuals use the
  `observed_minus_predicted` convention; positive finite weights return
  square-root-weighted residuals for least-squares use.
- `grid_search_point_location_2d(...)`: deterministic exhaustive x-z search for
  a point diffractor/target. Coordinates use `local_2d_x_z`: x is horizontal,
  z is depth positive downward. The objective grid shape is
  `(len(z_grid), len(x_grid))`.
- `grid_search_point_location_velocity_2d(...)`: deterministic exhaustive x-z
  search for a point diffractor/target while estimating homogeneous velocity.
  Exactly one of `velocity_bounds=(vmin, vmax)` or `velocity_grid=` must be
  supplied. Bounds mode estimates weighted least-squares slowness and clips the
  implied velocity to the requested interval; explicit-grid mode scans positive
  finite velocities. The returned `objective_grid` and selected
  `velocity_grid` both have shape `(len(z_grid), len(x_grid))`.

The `LocalizationGridSearchResult` metadata records method, travel-time model,
residual convention, coordinate frame, units, grid shape/order, receiver count,
weighting, and prototype/non-field flags. The
`VariableVelocityLocalizationGridSearchResult` adds `best_velocity`, a 2D
selected-velocity grid, and velocity-mode metadata. L0-1/L0-2 do not implement
automatic picking, pick records, uncertainty/covariance, tomography, waveform
modeling, imaging, DAS/SEG-Y readers, field-scale validation, or
field-performance claims. A small source audit found related Madagascar
raytrace, eikonal, diffraction, and book traveltime sources, but this module is
not a full Madagascar command clone.

## Forward Modeling Geometry and Shot Prototype Boundary

F0-1 starts the forward-modeling topic implementation path with
`pymadagascar.modeling.geometry`, a pure-Python topic-level geometry contract
for the existing acoustic2d prototype. It is importable from
`pymadagascar.modeling` but is not imported by `pymadagascar.__init__` or
`pymadagascar.api`, and it adds no CLI, console script, command-surface
coverage entry, or coverage-denominator change.

The contract is deliberately limited to regular local 2D acoustic geometry:

- `AcousticModelGrid2D` validates positive `nx/nz/dx/dz`, finite `ox/oz`,
  coordinate frame `local_2d_x_z`, and depth-positive-down semantics.
- Coordinates follow `x = ox + ix * dx` and `z = oz + iz * dz`.
- `index_to_coordinate` and `coordinate_to_nearest_index` provide explicit
  integer-sample conversion. Nearest-index conversion does not interpolate and
  rejects out-of-bounds coordinates.
- `PointSource2D`, `ReceiverArray2D`, `receiver_line_2d`, and
  `AcousticAcquisition2D` provide point-source/receiver geometry and
  JSON-safe metadata for small deterministic fixtures.
- `acquisition_to_acoustic2d_indices(grid, acquisition)` returns
  `sx, sz, receivers`, where `receivers` is a list of
  `(x_index, z_index)` pairs accepted by the existing `acoustic2d_forward`
  signature.

F0-2 adds pymadagascar.modeling.shot, a topic-level single-shot wrapper around
the same acoustic2d prototype. run_acoustic2d_shot accepts a NumPy velocity
array, AcousticModelGrid2D, and AcousticAcquisition2D, converts physical
source/receiver coordinates through acquisition_to_acoustic2d_indices, writes
a temporary RSF velocity input, calls the existing acoustic2d_forward
numerical core, and returns AcousticShotRecord2D.

AcousticShotRecord2D.data preserves the existing core layout (receiver, time)
with shape (nr, nt). The record also carries a 1D time axis, source and
receiver coordinates in x,z order, and JSON-safe path-free metadata documenting
the numerical core, grid, source/receiver indices, receiver-time data layout,
units, and prototype/non-field-ready boundaries.

F0-3 extends the same topic-level module with AcousticSurveyRecord2D and
run_acoustic2d_survey. The survey wrapper accepts a non-empty sequence of
AcousticAcquisition2D objects, calls run_acoustic2d_shot sequentially in input
order, annotates each shot with shot_index metadata, and returns a list of
AcousticShotRecord2D records plus JSON-safe path-free survey metadata. It does
not stack shots into a 3D tensor because receiver counts may vary by shot and
shot-level metadata remains part of the contract.

F0-4 adds AcousticSurveyTensor2D, acoustic_survey_to_tensor, and
summarize_acoustic_survey. The default survey contract remains
AcousticSurveyRecord2D.shots as list[AcousticShotRecord2D]; tensor conversion
is opt-in only. The tensor helper returns copy-backed data with layout
shot_receiver_time, shape (shot, receiver, time), source coordinates shaped
(shot, 2), and receiver coordinates shaped (shot, receiver, 2). It requires
constant receiver counts, constant time counts, and identical time axes. It
does not pad, interpolate, silently drop receivers, or modify the source survey.
The summary helper returns JSON-safe path-free metadata describing stackability,
receiver/time consistency, source coordinate bounds, and the tensor layout that
would be used if stacking is valid.

F0-1/F0-2/F0-3/F0-4 document the current acoustic2d axis contract: velocity RSF
is interpreted as n1=z and n2=x, while the NumPy velocity array shape is
(nx, nz). They do not change the acoustic finite-difference numerical core, add
a new wave-equation solver, add parallelism or caching, implement
source/receiver interpolation or padding, add production validation, make tensor
the default survey return, or promote modeling to a stable root API.

## Stable and Stable-Subset APIs

- RSF I/O: `read_rsf`, `write_rsf`, `read_header`, `write_header`.
- Public convenience API: `read`, `write`, `RSFData`.
- Package version: `pymadagascar.__version__`, synchronized with
  `pyproject.toml`.
- Core metadata: `Axis`, `Hypercube`, `RSFParams`.
- CLI parameter parsing: `key=value` and stable `par=file` subset.
- Generic stable subsets: spike, math, window, info/get/disfil/attr/put, dd,
  cat/transp, complex tools, byte scaling, smooth/boxsmooth, mask/cut/reverse,
  file ops, min/max statistics, add/scale/clip/normalize, mul/div/tpow,
  interleave, headerwindow/headercut, minimal header table attr/math/sort,
  minimal linear operator dot-test/conjgrad tools, generic sampling/bin/slice
  and max1 picking tools, whole-dataset difference metrics, unary transforms,
  histogram/quantile distribution QC, robust statistics, and non-finite
  masks/filling.
- Signal stable subsets: FFT/IFFT/RFFT/IRFFT, source-aligned FFT1/cosft/
  spectra2 bounded transforms, bandpass/lowpass/highpass,
  convolution/correlation/xcorr, autocorr, circular convolution, envelope
  correlation, shifts, first-order axis calculus, clip2 amplitude conditioning,
  Ricker wavelet, costaper, threshold, spectra, envelope, demean/detrend,
  integer decimation, band-stop/notch filtering, local RMS, standard windows,
  periodogram PSD/CSD, short-segment spectral coherence, axis-1 spectrograms,
  explicit-window RMS SNR, Welch PSD/CSD, H1/H2 transfer estimates, spectral
  whitening/normalization, basic frequency attributes, windowed-sinc FIR
  design/application, FIR response QC, band energy, and small filter banks.

## Package and Install Contract

- Distribution name: `pymadagascar-hybrid`; import package:
  `pymadagascar`.
- Python requirement: 3.10 or newer; NumPy is the only required runtime
  dependency.
- The default wheel is pure Python and has `wheel.cmake=false`. Editable
  install must work without Ninja, CMake execution, or a compiler.
- Existing C++ kernels remain optional. Building them requires the `cpp` extra,
  an explicit `wheel.cmake=true` setting, and
  `PYMADAGASCAR_BUILD_CPP=ON`.
- The 42 `pymada-*` names are installed entry points. The other CLI modules are
  supported through `python -m pymadagascar.cli.<name>`.
- No license metadata is declared yet. Choose and add a license before any
  public redistribution or package-index release.

## Prototype Areas

- SEG-Y support is a small 2D prototype.
- NMO, Semblance, FK, and Radon are prototypes.
- Kirchhoff migration and acoustic2d modeling are simplified prototypes.
- Matplotlib `grey/graph/wiggle` are quicklook replacements, not VPlot clones.

## Topic Maturity Boundaries

Roadmap Reassessment R1 groups the public surface by technical ownership:

| Topic | Current boundary |
| --- | --- |
| Ordinary RSF, axes, generic transforms, statistics/QC | stable or stable subset for in-memory local work |
| Signal processing | stable subset for small NumPy-backed traces and panels |
| Basic seismic QC | stable subset for gain, AGC, regular-axis mute, and stack |
| Header tables | partial numeric RSF table model, separate from SEG-Y trace headers |
| Linear operators and CG | partial reusable small-data foundation with prototype composition/history helpers, not an external operator framework |
| NMO, semblance, FK, Radon | prototype |
| SEG-Y | small fixed-length 2D prototype |
| Acoustic2d and Kirchhoff | simplified prototype |
| Plotting | partial Matplotlib quicklook substitute |
| DAS/engineering workflows | D-1 is a retained workflow prototype; no domain adapter or current D-2 commitment |

The existence of a public import, CLI module, test, or example does not by
itself promote an area to `stable`. Prototype geophysical modules remain
bounded by their documented geometry, dimensionality, numerical method, and
small-data assumptions. Pythonic convenience CLIs also do not imply a matching
upstream Madagascar command or increase conservative command-surface coverage.

## RSFData

`RSFData` is a high-level convenience wrapper for Python workflows. It is not a
replacement for every low-level API and does not wrap prototype imaging/modeling
commands. Default high-level transforms should be treated as non-mutating unless
explicitly documented otherwise.

Stage C-1 adds RSFData convenience methods for signal preprocessing:

- `RSFData.costaper(widths=..., axes=None)`.
- `RSFData.threshold(value=..., mode="hard", substitute=0.0)`.
- `RSFData.spectra(axis=1, mode="amplitude", average=True)`.
- `RSFData.envelope(axis=1)`.

These methods return new `RSFData` objects by default and support
`inplace=True`, matching the existing high-level API convention. `spectra`
returns a frequency-domain RSFData with a frequency axis.

Stage C-2 adds RSFData convenience methods for regular sampling and picking:

- `RSFData.linear(axis=1, n=None, o=None, d=None, fill=0.0)`.
- `RSFData.remap1(axis=1, n=None, o=None, d=None, fill_value=0.0,
  order=1)`.
- `RSFData.spline(axis=1, n=None, o=None, d=None, fill_value=0.0)`.
- `RSFData.t2warp(axis=1, inverse=False, pad=None, fill_value=0.0)`.
- `RSFData.slice(axis=3, index=0)`.
- `RSFData.max1(axis=1, mode="value", abs_search=False,
  nan_policy="propagate")`.

These methods also return new `RSFData` objects by default and support
`inplace=True`. `linear` updates the selected regular axis; `slice` and `max1`
remove the selected axis. `bin` is a table-to-grid function/CLI rather than an
`RSFData` chain method because its input is a point table, not a regular data
volume.

Stage C-3 adds RSFData convenience methods for signal correlation and data
conditioning:

- `RSFData.autocorr(axis=1, mode="full", normalize=False, max_lag=None)`.
- `RSFData.convolve(kernel, axis=1, mode="same")`.
- `RSFData.cconv(kernel, axis=1)`.
- `RSFData.envcorr(other, axis=1, mode="same", normalize=True)`.
- `RSFData.shifts(shift=..., axis=1, fill=0.0, circular=False)`.
- `RSFData.stacks(axis=1, statistic="sum", nonzero=False)`.

For `convolve`, `cconv`, and `envcorr`, the second operand may be an
`RSFData`, a path, or an array-like 1D template/compatible array. These are
small in-memory convenience wrappers, not streaming operator pipelines.

Stage C-4 adds RSFData convenience methods for axis calculus, amplitude
conditioning, and gather QC:

- `RSFData.deriv(axis=1, method="central", scale_by_d=True)`.
- `RSFData.causint(axis=1, scale_by_d=False)`.
- `RSFData.integral(axis=1, method="trapezoid", scale_by_d=True)`.
- `RSFData.clip2(min_value=None, max_value=None, pclip=None,
  symmetric=False)`.
- `RSFData.mutter(time_axis=1, offset_axis=2, v=..., t0=0, side="above",
  taper=0)`.
- `RSFData.diff(match, metric="sum_square")`.

These methods return new objects by default and support `inplace=True`.
`diff` intentionally returns a one-sample RSFData metric rather than a
sample-by-sample residual volume.

Stage C-5 adds RSFData convenience methods for unary transforms and
distribution QC:

- `RSFData.abs()` and `RSFData.sign()`.
- `RSFData.sqrt(invalid="nan")`.
- `RSFData.log(base="e", invalid="nan")`.
- `RSFData.exp()` and `RSFData.pow(exponent)`.
- `RSFData.histogram(bins=10, min_value=None, max_value=None, density=False)`.
- `RSFData.quantile(q, axis=None, nan_policy="propagate")`.

All support `inplace=True`, although non-mutating use is recommended for
shape-changing histogram and quantile results.

Stage C-6 adds RSFData convenience methods for robust statistics and
non-finite QC:

- `RSFData.mean(axis=None, nan_policy="propagate")`.
- `RSFData.rms(axis=None, nan_policy="propagate")`.
- `RSFData.var(axis=None, ddof=0, nan_policy="propagate")`.
- `RSFData.std(axis=None, ddof=0, nan_policy="propagate")`.
- `RSFData.median(axis=None, nan_policy="propagate")`.
- `RSFData.range_stats(axis=None, nan_policy="propagate")`.
- `RSFData.isnan(mode="nan")`.
- `RSFData.fillnan(value=0.0, mode="nan")`.

`range_stats()` is used instead of `range()` to avoid ambiguity with Python's
built-in range constructor. These methods follow the same default
non-mutating/optional-inplace contract.

Stage C-7 adds RSFData convenience methods for signal and small-gather QC:

- `RSFData.demean(axis=None, nan_policy="propagate")`.
- `RSFData.detrend(axis=1, type="linear", nan_policy="propagate")`.
- `RSFData.decimate(factor, axis=1, anti_alias=True, filter="moving_average")`.
- `RSFData.bandstop(fmin=..., fmax=..., axis=1, taper=0.0)`.
- `RSFData.notch(f0=..., width=None, q=None, axis=1, taper=0.0)`.
- `RSFData.localrms(rect=..., axis=1)`.

These methods are stable small-data conveniences, not claims of complete
Madagascar command compatibility. They follow the same default
non-mutating/optional-inplace contract.

M1-1 adds RSFData convenience methods for source-aligned `system/generic`
utilities:

- `RSFData.noise(seed=None, mean=0.0, std=1.0, distribution="normal",
  var=None, noise_range=None, replace=False)`.
- `RSFData.boxsmooth(rect, axes=None, repeat=1)`.

Both methods return new objects by default and support `inplace=True`. Existing
`RSFData.clip(clip, value=None)` is source-aligned to `sfclip` and now accepts
optional `value=` while preserving the same high-level method name.

M1-2 adds RSFData convenience methods for source-aligned `system/generic`
operator/filter utilities:

- `RSFData.laplac(axes=None, spacing_from_header=True, boundary="edge")`.
- `RSFData.smooth(rect, axes=None, repeat=1)`.
- `RSFData.trapez(axis=1, frequency=None, f1=None, f2=None, f3=None,
  f4=None, dt=None)`.

All three return new objects by default and support `inplace=True`.
`smooth(...)` is the triangle-smoothing `sfsmooth` subset; `boxsmooth(...)`
remains the boxcar `sfboxsmooth` subset.

Stage C-8 adds RSFData convenience methods for spectral QC:

- `RSFData.windowfunc(kind="hann", axis=1, periodic=False, normalize=False)`.
- `RSFData.psd(axis=1, nfft=None, window="hann", average=False,
  scaling="density")`.
- `RSFData.csd(other, axis=1, nfft=None, window="hann",
  scaling="density")`.
- `RSFData.coherence(other, axis=1, nfft=None, window="hann",
  nperseg=None, noverlap=None)`.
- `RSFData.spectrogram(axis=1, nperseg=64, noverlap=None,
  window="hann", mode="power")`.
- `RSFData.snr(axis=1, signal_window=None, noise_window=None,
  mode="rms", unit="db")`.

`csd` and `coherence` use the shared second-operand adapter. Spectrogram is
currently axis-1 only, and SNR requires an explicit noise window or a signal
window whose complement can serve as noise.

Stage C-9 adds RSFData convenience methods for spectral averaging,
conditioning, and attributes:

- `RSFData.welch(axis=1, nperseg=128, noverlap=None, window="hann",
  nfft=None, scaling="density", average=True)`.
- `RSFData.welchcsd(other, axis=1, nperseg=128, noverlap=None,
  window="hann", nfft=None, scaling="density", average=True)`.
- `RSFData.transfer(response, axis=1, nperseg=128, noverlap=None,
  window="hann", method="H1", eps=1e-12)`.
- `RSFData.whiten(axis=1, floor=1e-6, smooth=0, phase="preserve")`.
- `RSFData.specnorm(axis=1, mode="unit_rms", fmin=None, fmax=None,
  eps=1e-12)`.
- `RSFData.freqattr(axis=1, input_kind="signal",
  attrs=("dominant", "centroid", "bandwidth"), fmin=None, fmax=None)`.

`welchcsd` and `transfer` use the shared second-operand adapter. All six
methods are small-data NumPy conveniences and support the standard
non-mutating/optional-inplace contract.

Stage C-10 adds RSFData convenience methods for FIR filtering and band QC:

- `RSFData.firfilter(taps, axis=1, mode="same")`.
- `RSFData.filtfilt(taps, axis=1, pad=True)`.
- `RSFData.bandenergy(axis=1, bands=..., mode="rms", average=True)`.
- `RSFData.filterbank(axis=1, bands=..., numtaps=101, window="hann")`.

The two FIR methods use the shared second-operand adapter for taps.
`firwin` and `freq_response` are deliberately not RSFData methods because they
generate or diagnose filters independently of the current dataset.

M0-1 resumes source-aligned Madagascar command coverage and adds:

- `pymadagascar.generic.rotate.rotate_rsf(input, output, rotations={axis: rot})`
  for the `../src-master/system/main/rotate.c` `sfrotate` subset. Positive
  `rot#` moves the first samples of a 1-based RSF axis to the end; negative
  values wrap by `n#`; headers are preserved.
- `RSFData.rotate({axis: rot})`, a chainable wrapper over `rotate_rsf`.
- `pymada-rotate` / `python -m pymadagascar.cli.rotate`.
- `pymada-scale` as the console-script surface for the existing scalar
  `scale_rsf` / `RSFData.scale` subset aligned to
  `../src-master/system/main/scale.c`.

These are counted command-surface entries because they map to direct
`system/main` source files. M0-1 adds no Pythonic-only counted convenience, no
Forward Modeling expansion, no DAS/Localization/solver branch, and no coverage
denominator change.

M0-2 continues source-aligned direct `system/main` command coverage and adds:

- `pymada-stack` as the console-script surface for the existing
  `pymadagascar.seismic.stack.stack_rsf` subset aligned to
  `../src-master/system/main/stack.c`.
- `RSFData.stack(axis=2, mode="mean", nonzero=True)`, already present before
  M0-2, remains the chainable wrapper over `stack_rsf` and is now covered by a
  direct command-surface test.
- The bounded subset supports one-axis stacking with `axis=`, `mode=mean`,
  `mode=sum`, `mode=rms` for real input, and `nonzero=` fold selection.

M0-2 does not add root/stable exports. It does not implement upstream
`sfstack axis=0`, `scale=` vectors, `min=`, `max=`, `prod=`, complex RMS,
program-name aliases, or streaming/out-of-core execution. `sfstack` is counted
because it maps to a direct `system/main` source file; denominators remain
unchanged and no Pythonic-only convenience is counted.

M0-3 continues source-aligned direct `system/main` command coverage and adds:

- `pymada-pad` as the console-script surface for
  `pymadagascar.generic.pad.pad_rsf`, aligned to
  `../src-master/system/main/pad.c`.
- `pymada-spray` as the console-script surface for
  `pymadagascar.generic.spray.spray_rsf`, aligned to
  `../src-master/system/main/spray.c`.
- `RSFData.pad(n=None, beg=None, end=None, value=0.0)` and
  `RSFData.spray(axis=2, n=..., o=0.0, d=1.0, label=None, unit=None)` as
  chainable wrappers over the file-backed RSF APIs.

The bounded `sfpad` subset supports constant-value in-memory axis padding with
`beg#`, `end#`, and `n#`/`n#out` output-length requests. The bounded `sfspray`
subset supports new-axis insertion with `axis=`, `n=`, `o=`, `d=`, `label=`,
and `unit=`. M0-3 does not add root/stable exports and does not implement
streaming/out-of-core execution, arbitrary `sfput` parameter passthrough,
non-constant border modes, or byte-level native trace copying. Both commands
are counted because they map to direct `system/main` source files;
denominators remain unchanged.

M1-1 starts the post-M0 source-aligned `system/generic` command migration and
adds:

- `pymada-clip` as the console-script surface for
  `pymadagascar.generic.array_math.clip_rsf`, aligned to
  `../src-master/system/generic/Mclip.c`.
- `RSFData.noise(seed=None, mean=0.0, std=1.0, distribution="normal",
  var=None, noise_range=None, replace=False)`, a chainable wrapper over the
  existing `sfnoise` subset aligned to
  `../src-master/system/generic/Mnoise.c`.
- `RSFData.boxsmooth(rect, axes=None, repeat=1)`, a chainable wrapper over
  the existing box-smoothing subset aligned to
  `../src-master/system/generic/Mboxsmooth.c`.

The bounded `sfclip` subset supports `clip=` and optional `value=`; values
outside `[-clip, clip]` are replaced by signed `value`, and non-finite samples
are replaced by signed `value` according to the source-backed behavior. The
bounded `sfnoise` subset supports small in-memory normal/uniform add-or-replace
noise with deterministic NumPy seeds but does not promise byte-identical
Madagascar RNG streams. The bounded `sfboxsmooth` subset supports centered
box smoothing with `rect#`, optional selected axes, and `repeat=` using edge
padding. M1-1 does not add root exports, does not implement streaming,
out-of-core processing, `sfsmooth` adjoint/differentiation modes, `sflaplac`,
or `sftrapez`, and does not change coverage denominators.

M1-2 continues source-aligned `system/generic` command migration and adds:

- `pymada-laplac` / `python -m pymadagascar.cli.laplac`, backed by
  `pymadagascar.generic.laplac.laplac_rsf` and aligned to
  `../src-master/system/generic/Mlaplac.c`.
- `RSFData.smooth(...)` as the chainable surface for the existing
  `pymadagascar.signal.smooth.smooth_rsf` triangle subset aligned to
  `../src-master/system/generic/Msmooth.c`; `pymada-smooth` was already
  registered.
- `pymada-trapez` / `python -m pymadagascar.cli.trapez`, backed by
  `pymadagascar.signal.trapez.trapez_rsf` and aligned to
  `../src-master/system/generic/Mtrapez.c`.

The bounded `sflaplac` subset applies the source-aligned graph Laplacian sign
`center - neighbor`, preserves shape/header, supports selected RSF axes, and
optionally scales by header `d#`. The bounded `sfsmooth` subset applies
centered triangle smoothing with `rect#`, selected axes, and `repeat=`.
The bounded `sftrapez` subset applies a one-axis real-input RFFT trapezoidal
frequency response from `frequency=f1,f2,f3,f4` or `f1/f2/f3/f4`. M1-2 does
not add root exports, does not implement streaming/out-of-core behavior,
complex input, `sfsmooth adj=`/`diff#`/per-axis `box#`, `sflaplac adj=`,
coefficient fields, inverse solvers, or byte-identical FFT rounding.

M1-3 continues source-aligned `system/generic` spectral/transform migration and
adds:

- `pymada-fft1` / `python -m pymadagascar.cli.fft1`, backed by
  `pymadagascar.signal.transforms.fft1_rsf` and aligned to
  `../src-master/system/generic/Mfft1.c`.
- `pymada-cosft` / `python -m pymadagascar.cli.cosft`, backed by
  `pymadagascar.signal.transforms.cosft_rsf` and aligned to
  `../src-master/system/generic/Mcosft.c`.
- `pymada-spectra2` / `python -m pymadagascar.cli.spectra2`, backed by
  `pymadagascar.signal.transforms.spectra2_rsf` and aligned to
  `../src-master/system/generic/Mspectra2.c`.
- `RSFData.fft1(...)`, `RSFData.cosft(...)`, and `RSFData.spectra2(...)`.

The bounded `sffft1` subset is a one-axis real-to-complex RFFT and
complex-to-real inverse wrapper with ordinary `fft_n#` restoration. The bounded
`sfcosft` subset is one-axis real-valued orthonormal DCT-II/DCT-III. The
bounded `sfspectra2` subset computes an in-memory 2-D amplitude or power
spectrum over two selected axes, with optional averaging over remaining planes.
Existing `sfcostaper` and `sfspectra` were audited against `Mcostaper.c` and
  `Mspectra.c` but were already counted in Stage C-1, so M1-3 does not count them
again. M1-3 does not add root exports, does not implement `sffft3`, streaming,
FFTW planning, `sffft1 opt=`/`ot=`/`sym=`, `sfcosft` multi-axis `sign#`
dispatch, or byte-identical FFT/DCT rounding.

M1-4 continues source-aligned `system/generic` interpolation/remap migration
and adds:

- `pymada-remap1` / `python -m pymadagascar.cli.remap1`, backed by
  `pymadagascar.generic.remap.remap1_rsf` and aligned to
  `../src-master/system/generic/Mremap1.c`.
- `pymada-spline` / `python -m pymadagascar.cli.spline`, backed by
  `pymadagascar.generic.remap.spline_rsf` and aligned to
  `../src-master/system/generic/Mspline.c`.
- `pymada-t2warp` / `python -m pymadagascar.cli.t2warp`, backed by
  `pymadagascar.generic.remap.t2warp_rsf` and aligned to
  `../src-master/system/generic/Mt2warp.c`.
- `RSFData.remap1(...)`, `RSFData.spline(...)`, and `RSFData.t2warp(...)`.

The bounded `sfremap1` subset uses one-axis regular-grid linear interpolation
with explicit output `n/o/d` and fill value. The bounded `sfspline` subset uses
one-axis natural cubic interpolation implemented with NumPy only. The bounded
`sft2warp` subset maps one regular axis between time and squared-time
coordinates with linear interpolation and restores `n#_t2warp` metadata on the
inverse path. Existing `sflinear` was audited against `Mlinear.c` but was
already counted in Stage C-2; M1-4 does not count it again. M1-4 does not add
root exports, does not add SciPy, and does not implement upstream ENO orders
above 1, irregular coordinate/value tables, `sfspline fp=`, `pattern=`, spline
prefiltering, `sft2warp adj=`, stretch regularization, `sflogwarp`, streaming,
or byte-identical interpolation rounding.

M1-5 continues source-aligned `system/generic` array algebra / selection
migration and adds:

- `pymada-matmult` / `python -m pymadagascar.cli.matmult`, backed by
  `pymadagascar.generic.array_algebra.matmult_rsf` and aligned to
  `../src-master/system/generic/Mmatmult.c`.
- `pymada-match` / `python -m pymadagascar.cli.match`, backed by
  `pymadagascar.generic.array_algebra.match_rsf` and aligned to
  `../src-master/system/generic/Mmatch.c`.
- `pymada-linefit` / `python -m pymadagascar.cli.linefit`, backed by
  `pymadagascar.generic.array_algebra.linefit_rsf` and aligned to
  `../src-master/system/generic/Mlinefit.c`.
- `RSFData.matmult(...)`, `RSFData.match(...)`, and `RSFData.linefit(...)`.

The bounded `sfmatmult` subset is a real-valued matrix-vector multiplication
wrapper with optional `adj=`. The bounded `sfmatch` subset implements the
source symmetric zero-boundary matching-filter loop in forward and adjoint
forms without turning it into a solver framework. The bounded `sflinefit`
subset fits `y=a*x+b` from an `n1=2` coordinate/value table and evaluates a
regular output grid. M1-5 does not add root exports, does not add SciPy, and
does not implement complex matrix multiplication, sparse/batched matmul,
histogram equalization `sfequal`, header-coordinate `sfextract`, robust
regression, shaping-filter solvers, streaming, or out-of-core processing.

M2-1 starts source-aligned `system/seismic` command migration and adds:

- `pymada-avo` / `python -m pymadagascar.cli.avo`, backed by
  `pymadagascar.seismic.avo.avo_rsf` and aligned to
  `../src-master/system/seismic/Mavo.c`.
- `pymada-fold` / `python -m pymadagascar.cli.fold`, backed by
  `pymadagascar.seismic.fold.fold_rsf` and aligned to
  `../src-master/system/seismic/Mfold.c`.
- `pymada-ai2refl` / `python -m pymadagascar.cli.ai2refl`, backed by
  `pymadagascar.seismic.ai2refl.ai2refl_rsf` and aligned to
  `../src-master/system/seismic/Mai2refl.c`.
- `RSFData.avo(...)`, `RSFData.fold(...)`, and `RSFData.ai2refl(...)`.

The bounded `sfavo` subset computes intercept and gradient by ordinary least
squares along RSF axis 2, using `o2/d2` or an explicit `offset=` file in the
file API. The bounded `sffold` subset builds a 3D histogram from numeric
header-table columns with explicit `n/o/d/label` output bins. The bounded
`sfai2refl` subset computes `(ai[i+1]-ai[i])/(ai[i+1]+ai[i]+eps)` along one
axis and writes zero at the last sample. M2-1 does not add root exports, does
not add SciPy, and does not implement `sfenvelope` phase rotation, `sffreqint`
freqlet inversion, `sfc2r` ray-field coordinate interpolation, SEG-Y key
lookup in `sffold`, CDPtype offset shifts in `sfavo`, streaming, or out-of-core
processing.

## RSFData Behavior Contract

- Transform methods return a new in-memory `RSFData` by default and leave the
  source object unchanged.
- `inplace=True` returns the original object after replacing data and metadata,
  including for axis-removing and one-sample scalar outputs.
- In-memory transform results have `path is None`; `write(...)` returns a new
  file-backed `RSFData` whose path is the written header path.
- `header` and `numpy()` return defensive copies by default.
- `convolve`, `cconv`, `envcorr`, `csd`, `coherence`, `welchcsd`, `transfer`,
  `firfilter`, `filtfilt`, `diff`, `matmult`, and `match` accept a second operand as
  `RSFData`, RSF path, NumPy array, or Python list. RSF paths preserve operand
  metadata. A 1D array/list receives minimal template metadata using the
  selected source-axis spacing; its origin is `0`.
- Invalid second-operand paths and scalar operands fail before the lower-level
  operation is run. Shape and sampling compatibility remain operation-specific.

## Shape / Header / Dtype Contract

| Operation family | Shape and header | Dtype |
| --- | --- | --- |
| `costaper`, `threshold`, `envelope`, `shifts`, `deriv`, `causint`, `integral`, `clip2`, `mute`, `mutter` | Preserve shape and ordinary axis metadata. | Float32 normally remains float32 and float64 remains float64. `threshold` supports complex64 by magnitude; `envelope`, `spectra`, `clip`, and `clip2` require real input. |
| `linear` | Changes only selected-axis `n/o/d`; other axes are preserved. | Real float output following supported input precision. |
| `spectra` | Replaces the selected axis with one-sided frequency sampling; `average=True` returns a 1D frequency axis. Label is `Frequency`, and seconds map to `Hz`. | Real float amplitude/power output. |
| `autocorr`, `convolve`, `envcorr` | May change selected-axis length and origin according to mode; other axes remain. | Supported real/complex convolution precision; `envcorr` requires real input. |
| `cconv`, `shifts` | Preserve input shape and header. | Preserve supported real/complex family. |
| `slice`, `max1`, `stack`, `stacks` | Remove one RSF axis and shift later axis metadata down. A scalar reduction is represented as one sample. | Picking/stacking returns the implementation's supported numeric output dtype. |
| `pad`, `spray` | `pad` changes selected axis lengths and shifts origins for leading padding. `spray` inserts a new axis and shifts later axis metadata up. | Preserve the input numeric dtype after constant padding or duplication. |
| `diff` | Always returns one sample with `label1=Difference` and `difference_metric=`. | Float64 scalar metric, including complex-input comparisons by magnitude. |
| `abs`, `sign`, `sqrt`, `log`, `exp`, `pow` | Preserve shape and ordinary header metadata. | Float32 remains float32 and float64 remains float64. `abs` converts complex64 magnitude to float32; the other five reject complex input. |
| `histogram` | Returns a `(bins, 2)` NumPy table / RSF with `n1=2`, `n2=bins`; fields are `center,value`. | Float64 table; non-finite samples are omitted. |
| `quantile` | Global mode returns a 1D q array. Axis mode replaces the selected 1-based RSF axis with the q axis and records exact values in `quantiles=`. | Float64 output; NaNs propagate by default or may be omitted. |
| `mean`, `rms`, `var`, `std`, `median` | Global mode returns one sample. Axis mode removes the selected 1-based RSF axis and shifts later metadata down. | Float64 output. Real input only; `nan_policy=propagate|omit|raise`. |
| `range_stats` | Global mode returns `[min,max]`. Axis mode removes the selected source axis and adds RSF axis 1 with two fields recorded as `range_fields=min,max`. | Float64 output. Real input only. |
| `isnan`, `fillnan` | Preserve shape and ordinary axis metadata. Mask mode records `mask_mode=`; fill mode records `fill_mode=` and `fill_value=`. | Mask output is int32 0/1. Fill preserves supported real or complex input dtype. |
| `demean`, `detrend` | Preserve shape and ordinary axis metadata; axes are 1-based and `axis=None` is global for demean. | Float32/complex64 and float64/complex128 precision families are preserved; integer input becomes float32. NaN policy is explicit. |
| `decimate` | Shortens only the selected axis, multiplies `d#` by the integer factor, and preserves `o#` and other axes. | Preserves supported float/complex precision family; optional moving-average anti-aliasing is in-memory. |
| `bandstop`, `notch`, `localrms` | Preserve shape and ordinary axis metadata. Filter sampling comes from selected-axis `d#`; local RMS uses clipped boundary windows. | Filters require real input and preserve float precision. Local RMS accepts real/complex input and returns real magnitude RMS. |
| `windowfunc` | Preserves shape/header when applied; direct generation returns a 1D window. | Preserves float/complex precision family when applied; generated windows are float32. |
| `psd`, `csd`, `coherence` | Replace the selected axis with one-sided frequency sampling. `psd(average=True)` returns one frequency axis. | PSD/coherence are real float. CSD is complex and file-backed RSF output is complex64. Inputs are finite real arrays. |
| `spectrogram` | Axis 1 becomes frequency axis 1 plus window-time axis 2; original axes 2+ shift upward. | Magnitude/power output is real float. |
| `snr` | Removes the selected axis; a 1D input becomes one sample. Remaining axes retain metadata. | Float64 dB or ratio output; real and complex magnitude RMS are supported. |
| `welch`, `welchcsd`, `transfer` | Replace the selected axis with one-sided frequency sampling. `average=True` removes all non-frequency axes. | Welch PSD is real float; Welch CSD and transfer output complex values and file-backed RSF uses complex64. Inputs must be finite real arrays. |
| `whiten`, `specnorm` | Preserve shape and ordinary axis metadata; selected-axis `d#` supplies frequency sampling. | Preserve float32/float64 precision. Complex and non-finite input are rejected. |
| `freqattr` | Removes the analyzed axis and adds leading axis 1 for the requested attributes. Bandwidth is the power-weighted frequency standard deviation. | Float64 attribute output from finite real signal or PSD input. |
| `firfilter`, `filtfilt` | Preserve input shape and ordinary axes. Taps are 1D and must match selected-axis sampling in file-backed use. | Finite real or complex array input is supported; float64 taps promote real output, while file-backed complex output uses complex64. |
| `freqz` | Returns one-sided frequency response with `Frequency` axis; mode is complex, amplitude, or power. | Complex mode is complex64 in RSF; amplitude/power are real float. |
| `bandenergy` | Removes the analyzed axis and adds RSF axis 1 for explicit frequency bands; `average=True` returns only that axis. | Finite real input; real float energy/power/RMS output. |
| `filterbank` | Preserves all source axes and adds a highest RSF `Frequency band` axis. | Finite real input; output follows float32/float64 input precision. |

## Naming Compatibility Notes

- `mute` remains the earlier top-mute subset with a physical-time taper;
  `mutter` is the 2D above/below regular-axis subset with a sample-count taper.
- `stack` is the classic nonzero-fold seismic mean/sum/rms subset; `stacks` and
  `stack_along_axis` are the generic statistical variants.
- `clip` is symmetric explicit clipping, `clip2` adds asymmetric/percentile
  limits, and `threshold` suppresses amplitudes below a magnitude.
- CLI `conv` and `convolve` share one implementation. `corr` is two-input
  cross-correlation, `xcorr` is the older trace-autocorrelation entry point,
  `autocorr` adds normalization/max-lag controls, `envcorr` works on envelopes,
  and `cconv` is circular convolution.
- `dd` is format/dtype/endian conversion; `diff` is a scalar dataset metric.
- `get` queries ordinary header keys, `info` reports file layout, `attr`
  summarizes array values, and `headerattr` summarizes minimal header-table
  columns.
- Lower-level `absolute()` avoids shadowing Python's built-in `abs`;
  `RSFData.abs()` is the chainable convenience name. Stage C-5 `pow` is an
  `sfmath`-style sample-wise scalar power convenience, not upstream `sfpow`
  coordinate-axis gain; use `tpow` for the latter subset.

## Madagascar Compatibility

The project follows useful Madagascar conventions where they fit Python:

- RSF header + sidecar layout.
- `n#`, `o#`, `d#`, `label#`, `unit#` axis metadata.
- CLI axes use Madagascar-style 1-based numbering.
- `key=value` and `par=file` style arguments.
- Optional original Madagascar comparison tests for selected commands.

The project does not promise byte-level output identity. Differences are
expected in text formatting, random number sequences, FFT normalization/frequency
metadata, plotting output, prototype geophysical algorithms, and simplified
header/SEG-Y behavior.

## Signal Compatibility

FFT and filters use NumPy conventions. `sffft1`-style support is exposed through
split APIs such as `fft_rsf`, `ifft_rsf`, `rfft_rsf`, and `irfft_rsf`. The
current `sfbandpass` subset is an FFT-domain zero-phase taper style filter and
does not fully reproduce all upstream Butterworth or phase options.

Stage C-1 signal preprocessing APIs:

- `cosine_taper` / `costaper_rsf`: 1D/2D/3D separable sin-squared boundary
  taper using 1-based RSF axes. CLI accepts `width#=` and upstream-style
  `nw#=` aliases.
- `threshold` / `threshold_rsf`: explicit hard or soft threshold by
  `value=`, with complex data thresholded by magnitude.
- `spectra` / `spectra_rsf`: simple NumPy RFFT amplitude or power spectrum,
  with optional averaging over non-frequency axes and frequency-axis metadata.
- `envelope` / `envelope_rsf`: analytic-signal envelope from a NumPy FFT
  Hilbert transform.

These are practical preprocessing/QC subsets. They are not full Madagascar
parameter clones. `sfthreshold` upstream is pclip-driven; this project exposes
explicit `value=` thresholding. `sfspectra` here is not a multi-window spectral
estimator. `sfenvelope` here outputs envelope amplitude only and does not expose
upstream phase-rotation parameters such as `hilb=`, `phase=`, `order=`, or
`ref=`.

Stage C-7 signal-QC APIs:

- `demean` / `demean_rsf`: subtract a global or 1-based-axis mean with
  `nan_policy=propagate|omit|raise`.
- `detrend` / `detrend_rsf`: constant or least-squares linear detrending along
  one axis.
- `decimate` / `decimate_rsf`: integer stride downsampling with an optional
  centered moving-average anti-alias prefilter.
- `bandstop` / `bandstop_rsf`: real-input zero-phase RFFT band rejection using
  the existing cosine frequency-taper convention.
- `notch` / `notch_rsf`: convenience band-stop centered on `f0`, configured by
  total `width` or `q`.
- `local_rms` / `localrms_rsf`: centered single-axis sliding RMS with clipped
  windows at boundaries.

No standalone `demean`, `detrend`, `decimate`, `bandstop`, or `notch` program
was found in the audited upstream tree. `user/luke/Mrms.c` is a real local-RMS
program, but it supports multidimensional `rect#` windows and different edge
semantics. The project therefore documents all six Stage C-7 CLIs as Pythonic
conveniences and does not add command-surface coverage. They do not implement
polyphase decimation, designed FIR/IIR filters, phase options, arbitrary
polynomial detrending, streaming, or out-of-core processing.

## Generic Sampling and Picking Compatibility

Stage C-2 generic sampling APIs:

- `linear_resample` / `linear_rsf`: regular-grid linear interpolation along one
  1-based RSF axis. Output `n/o/d` update the selected axis. Samples outside
  the input coordinate range are filled with `fill` (default `0.0`). This is
  not the full upstream `sflinear` irregular coordinate/value-table tool with
  `sort=`, `niter=`, `rect=`, `nw=`, or `pattern=`.
- `bin_1d`, `bin_2d`, and `bin_rsf`: small in-memory binning. `bin_rsf`
  expects a 2D table-like RSF with one point per NumPy row and x/y/value
  columns on the last axis using zero-based column indices. It supports
  `mean`, `sum`, and `count` statistics plus configurable empty-bin fill. It
  does not support upstream `sfbin`'s separate `head=` file, `fold=` output,
  median mode, nearest/linear interpolation modes, normalization clips, or
  multi-slice streaming.
- `slice_array` / `slice_rsf`: fixed zero-based index slicing along a 1-based
  RSF axis, with that axis removed and later header axes shifted down. This is
  not the full upstream `sfslice` picked-surface interpolation tool with
  `pick=`.
- `max1` / `max1_rsf`: maximum picking along one 1-based RSF axis with
  `mode=value`, `mode=index`, or `mode=coord`, optional absolute-amplitude
  search, and `nan_policy=propagate|omit`. It does not emit upstream
  `sfmax1`'s complex `(coordinate, amplitude)` list of local maxima, `np=`, or
  `sorted=` behavior.

All Stage C-2 tools are pure NumPy, small-data, in-memory subsets. They do not
implement spline/ENO/stretch/remap frameworks, pandas-backed tables, or
streaming/out-of-core processing.

## Signal Correlation and Conditioning Compatibility

Stage C-3 signal APIs:

- `autocorr` / `autocorr_rsf`: trace autocorrelation along one 1-based RSF axis,
  `mode=full|same`, optional zero-lag normalization, and optional `max_lag`
  sample window. This is not upstream `sfautocorr`'s helix-filter lag-file
  tool.
- `convolve` / `convolve_rsf`: explicit two-input convolution with a 1D or
  compatible per-trace kernel, `mode=full|same|valid`, and direct/FFT method
  selection. The module-only `convolve` CLI is an `sfconvolve`-style alias over
  the existing small convolution subset, not the 2D adjoint/wrap kernel program
  from `user/luke`.
- `circular_convolve` / `cconv_rsf`: FFT-backed circular convolution with a 1D
  kernel, preserving input shape and header. This is not the upstream complex
  internal-convolution operator with `lag=` and `single=` semantics.
- `envelope_correlation` / `envcorr_rsf`: compute analytic-signal envelopes
  first, then correlate them with optional norm normalization. This is not the
  upstream local envelope-correlation solver with `rect#=` and `niter=`.
- `shift` / `shifts_rsf`: integer sample shifts with optional circular wrapping
  and fill value. This is not upstream `sfshifts`' multiple-slope interpolation
  output.
- `stack_along_axis` / `stacks_rsf`: small statistical stacks over one axis
  with `sum`, `mean`, `rms`, or `count_nonzero`. This is not upstream
  `sfstacks`' constant-velocity NMO stack/velocity-scan workflow.

All Stage C-3 tools are pure NumPy, small-data, in-memory subsets. They do not
implement full upstream filter/correlation/stacking ecosystems, weighted
stacks, local smoothing solvers, slope interpolation families, streaming, or
out-of-core processing.

Stage C-8 spectral-QC APIs:

- `window_function` and `apply_window`: Hann, Hamming, Blackman, Bartlett,
  boxcar, and cosine windows, with optional periodic generation and unit-mean
  coherent-gain normalization when applying.
- `psd` / `psd_rsf`: one-sided single-periodogram density or spectrum.
- `csd` / `csd_rsf`: shape-matched two-input cross periodogram using
  `conj(A) * B`.
- `coherence` / `coherence_rsf`: magnitude-squared coherence with simple
  overlapping short-segment averaging.
- `spectrogram` / `spectrogram_rsf`: axis-1 STFT magnitude or power for 1D
  signals and trace panels.
- `snr` / `snr_rsf`: global or per-trace RMS ratio/dB from explicit sample
  windows.

The only directly related core upstream program is
`system/generic/Mspectra.c`, which emits amplitude spectra rather than PSD.
`system/generic/Mcostaper.c` is a border taper, not a standard window
generator. `user/chen/Mcoherence.c` computes a local spatial coherence cube,
while `user/yliu/Mstft.c` and `Msnr.c` use different command names, output
contracts, and algorithms. C-8 therefore remains a Pythonic convenience batch
and adds no conservative command-surface coverage. C-8 itself is limited to
single periodograms and simple segment-averaged coherence; C-9 adds Welch
PSD/CSD. Advanced windows, arbitrary-axis STFT, IIR/AR spectral estimation,
automatic noise-window picking, streaming, and out-of-core work remain absent.

Stage C-9 spectral averaging and attribute APIs:

- `welch_psd` / `welch_rsf`: overlapping-window one-sided PSD with
  `density|spectrum` scaling and optional averaging across remaining axes.
- `welch_csd` / `welchcsd_rsf`: paired, shape-matched Welch cross spectrum
  using `conj(A) * B`.
- `transfer_function` / `transfer_rsf`: H1=`Pxy/Pxx` and
  H2=`Pyy/Pyx` frequency-response estimates with stabilized division.
- `spectral_whiten` / `whiten_rsf`: phase-preserving RFFT amplitude whitening
  with a relative floor and optional moving-average spectrum smoothing.
- `spectral_normalize` / `specnorm_rsf`: trace-wise unit-RMS or unit-maximum
  spectral scaling over all frequencies or an explicit frequency band.
- `frequency_attributes` / `freqattr_rsf`: dominant-bin frequency,
  power-weighted centroid, and power-weighted standard-deviation bandwidth
  from a signal periodogram or an input PSD.

No matching standalone upstream Welch, Welch-CSD, H1/H2 transfer, whitening,
spectral-normalization, or three-attribute RSF command was found. Related
sources are `system/generic/Mspectra.c`, user STFT tools,
`user/yliu/Mdominantf.c`, `user/fomels/Mabalance.c`, and
`user/karl/Mtahspecbal.c`, but their names, input models, and output contracts
differ. C-9 is therefore an uncounted Pythonic convenience batch.

C-9 does not implement median Welch averaging, confidence intervals,
multi-taper or AR estimation, advanced transfer-function/system-identification
estimators, predictive deconvolution, target-spectrum matching, complex input,
streaming, or out-of-core processing.

Stage C-10 FIR/filter-design APIs:

- `firwin` / `firwin_rsf`: low-pass, high-pass, band-pass, or band-stop
  windowed-sinc coefficients with Hann, Hamming, Blackman, Bartlett, or boxcar
  windows. Frequencies are physical when `fs` is supplied and Nyquist
  normalized otherwise.
- `fir_filter` / `firfilter_rsf`: centered same-length convolution along a
  1-based RSF axis.
- `zero_phase_fir_filter` / `filtfilt_rsf`: forward/reverse FIR passes with
  optional bounded reflection padding. This is not SciPy's complete initial
  condition algorithm.
- `freq_response` / `freqz_rsf`: one-sided complex, amplitude, or power
  response.
- `band_energy` / `bandenergy_rsf`: explicit-band energy, mean power, or RMS.
- `filter_bank` / `filterbank_rsf`: explicit FIR band-pass bank with a new
  highest RSF band axis.

No matching core upstream command contracts were found. Core
`system/generic/Mbandpass.c` is a Butterworth filter with optional
forward/reverse application. `user/chen/Mfir.c` (`sfir`) applies supplied
coefficients using an integer filter origin, while `Mfbank1.c`/`Mfbank2.c`
build interpolation filter banks rather than frequency bands. C-10 is
therefore an uncounted Pythonic convenience batch.

C-10 does not implement IIR design/application, arbitrary full/valid FIR
geometry, SciPy-compatible filtfilt initial states, polyphase/multirate
filtering, Kaiser/remez/equiripple design, automatic band selection, wavelet
packets, streaming, or out-of-core processing.

## Axis Calculus, Amplitude Conditioning, and Gather QC

Stage C-4 APIs:

- `deriv` / `deriv_rsf`: first finite differences along any 1-based RSF axis,
  with `central`, `forward`, or `backward` methods and optional `d#` scaling.
  Boundaries use the nearest one-sided first difference. This is not upstream
  `sfderiv`'s maximally linear FIR differentiator and does not implement
  `order=`.
- `causal_integrate` / `causint_rsf`: forward cumulative sums along any axis,
  optionally multiplied by `d#`. Upstream `sfcausint adj=y` anti-causal
  adjoint integration is not included.
- `integral` / `integral_rsf`: cumulative trapezoid or cumsum integration along
  any regular axis. The upstream `user/songxl/Mintegral.c` is a small
  first-axis wave-extrapolation helper; this project exposes a general
  Pythonic numerical-integration subset instead.
- `clip2` / `clip2_rsf`: explicit one- or two-sided clipping plus optional
  central-percentile or symmetric absolute-amplitude clipping. Complex input
  is rejected. Upstream `sfclip2` supports only explicit `lower=`/`upper=`.
- `mutter` / `mutter_rsf`: regular-axis 2D linear mute with
  `t_mute=t0+abs(offset)/v`, `side=above|below`, and taper width in time-axis
  samples. It does not read external offset/header files or implement
  `half=`, `inner=`, `hyper=`, `slope0=`, or `slopep=`.
- `difference_metric` / `diff_rsf`: same-shape whole-dataset QC metrics
  `sum_square`, `rms`, or `max_abs`. Upstream `user/chenyk/Mdiff.c` provides
  only a float sum-of-squared-differences scalar.

The audited upstream `sffold` at `system/seismic/Mfold.c` is a SEG-Y
trace-header-driven 3D histogram/foldplot program and was not implemented in
this batch. The audited `user/fomels/Mzero.c` is an ENO zero-crossing detector,
not a zero-filled-data generator, so it was not used as a misleading
replacement. `sfdiff` was selected as the small QC replacement.

All Stage C-4 tools are pure NumPy, small-data, in-memory subsets. They do not
provide high-order calculus, complex mute geometry, trace-header fold maps,
streaming, or out-of-core processing.

## Unary Math and Distribution QC

Stage C-5 APIs:

- `absolute` / `abs_rsf`: real absolute value and complex magnitude.
- `sign` / `sign_rsf`: real `-1/0/1` signs.
- `sqrt` / `sqrt_rsf` and `log` / `log_rsf`: real-domain transforms with
  `invalid=nan|raise`; logarithm supports natural or numeric bases.
- `exp` / `exp_rsf` and `power` / `pow_rsf`: real sample-wise transforms.
- `histogram` / `histogram_rsf`: finite-sample count/density histogram,
  represented as a two-column bin-center/value table.
- `quantile` / `quantile_rsf`: one or more global or axis-wise quantiles with
  `nan_policy=propagate|omit`.

The audited source tree has no standalone `sfabs`, `sfsign`, `sfsqrt`, `sflog`,
or `sfexp` programs; those operations are functions of
`system/main/math.c`. Their module-only CLIs are direct conveniences, not new
expression engines. Upstream `system/generic/Mpow.c` applies coordinate-axis
gain and is already represented by `tpow`; Stage C-5 `pow` instead provides
the requested sample-wise `input**exponent` convenience. Upstream
`sfhistogram` emits a one-dimensional integer histogram using explicit
`n1/o1/d1`; this subset emits a self-describing two-column float64 table.
Upstream `user/ivlad/Mquantile.c` prints one percentage clip value; this subset
writes one or more q values to RSF and supports an axis mode.

Real NaN/Inf behavior follows NumPy except where specified: `sqrt` negatives
and `log` negatives become NaN or raise, `log(0)` is `-inf`, exponential
overflow is `inf`, histogram omits all non-finite samples, and quantile
propagates NaN unless `nan_policy=omit`. These are in-memory small-data tools;
weighted quantiles, streaming histograms, complex transcendental transforms,
and out-of-core processing are not included.

## Robust Statistics and Non-Finite QC

Stage C-6 APIs:

- `mean` / `mean_rsf`, `rms` / `rms_rsf`, `variance` / `var_rsf`,
  `std` / `std_rsf`, and `median` / `median_rsf`.
- `range_stats` / `range_rsf`, represented by an explicit `[min,max]` field
  axis.
- `isnan_mask`, `finite_mask`, and `isnan_rsf` with
  `mode=nan|inf|nonfinite|finite`.
- `fillnan` / `fillnan_rsf` with `mode=nan|inf|nonfinite`.

Statistics accept real numeric arrays and produce float64 results. Global
statistics are one-sample RSFs; axis statistics remove one Madagascar-style
1-based axis. `nan_policy=propagate` follows NumPy, `omit` ignores NaNs, and
`raise` rejects input containing NaNs. Inf is not silently omitted and should
be inspected or replaced with the non-finite tools. Statistics reject complex
input; mask operations mark a complex sample when either component is
non-finite, and filling replaces the whole sample while preserving complex64.

The audited standalone `user/yliu/Mmean.c` is a sliding-window mean filter and
`user/luke/Mrms.c` is a local RMS attribute, so the Stage C-6 global/axis
`mean` and `rms` CLIs are Pythonic conveniences rather than those command
clones. Global mean/RMS/variance/std are also available as text from
`system/main/attr.c`, while `system/main/stack.c` provides related axis stack
and RMS behavior. `user/fomels/Mmedian.c` is the one directly matched command:
the `axis=1` median subset follows its first-axis reduction. No standalone
`sfvar`, `sfstd`, `sfrange`, `sfisnan`, or `sffillnan` programs were found in
the audited tree.

These tools are in-memory NumPy subsets. Weighted/robust estimators beyond
median, grouped statistics, streaming accumulation, and out-of-core processing
are not included.

## Header and Metadata Compatibility

Ordinary RSF headers are supported through `RSFHeader`, `Axis`, `Hypercube`, and
I/O helpers. Stage B-3-1 adds ordinary-RSF mask/header subsets:

- `header_window_rsf`: one-dimensional mask, continuous selection only, updates
  selected-axis `n#` and `o#`.
- `header_cut_rsf`: one-dimensional mask, shape/header preserved, configurable
  cut side.

These are not full Madagascar header table clones and do not support SEG-Y trace
headers.

Stage B-3-2 adds a minimal RSF-backed header table subset:

- `read_header_table` and `write_header_table`: read/write a numeric two-
  dimensional RSF table where `n1` is the number of keys and `n2` is the number
  of rows/traces.
- Key names are represented by `key1=`, `key2=`, ... and mirrored in
  `header_keys=offset,cdp,...`.
- `header_table_attr` / `header_attr_table`: count/min/max/mean per selected
  key.
- `header_table_math` / `header_math_table`: safe expression over existing
  keys to create a new key or replace an existing key with `overwrite=True`.
- `header_table_sort` / `header_sort_table`: stable row sort by one key.

This subset is intentionally smaller than Madagascar's full header table and
trace-header ecosystem. It does not parse SEG-Y trace bytes, does not provide
`sfsegyheader`, and does not synchronize row sorting with a separate seismic
data volume.

## Linear Operator Compatibility

Stage B-4 adds a minimal pure-Python, small-data linear-operator subset:

- `LinearOperator`: abstract base with `forward(model)` and `adjoint(data)`.
- `MatrixOperator`: dense matrix-backed operator with matrix shape
  `(data_size, model_size)`, forward `A @ model`, and adjoint
  `A.conj().T @ data`.
- `CallableLinearOperator`: Python-callable wrapper for tested toy operators and
  future prototypes.
- `ScaledOperator`, `SumOperator`, `ComposedOperator`, and `StackedOperator`:
  I0-1 prototype composition helpers for small in-memory operators. They are
  direct-module prototype/testing surfaces, not root/API stable exports.
- `DiagonalRegularization`, `FirstDifferenceRegularization`, and
  `SecondDifferenceRegularization`: I0-2 prototype regularization operators
  for small in-memory least-squares foundations. Identity/damping
  regularization reuses `IdentityOperator` and `ScaledOperator`.
- `LeastSquaresProblem`, `ObjectiveDiagnostics`, and `StoppingDiagnostics`:
  I0-3 prototype objective/residual/diagnostics structures. They evaluate
  residuals, objective terms, normal-equation gradients, stopping summaries,
  and SolverHistory/SolverResult-compatible records without running a solver.
- `run_cg_with_history` and `run_cgnr_with_history`: I0-4 optional
  direct-module diagnostics adapters over the existing CG iteration core. They
  do not change default solver or CLI behavior and are not stable root exports.
- `run_cgls` and `run_cgls_problem`: I0-5 bounded CGLS direct-module
  prototypes returning existing solver diagnostics contracts; I0-8A/I0-8B add
  optional right/model-space preconditioner support and clearer latent/model
  diagnostics.
- `run_lsqr` and `run_lsqr_problem`: I0-9B1 bounded unpreconditioned LSQR
  direct-module prototypes for small deterministic least-squares problems,
  including regularized `LeastSquaresProblem` objects through the existing
  augmented system. They reject preconditioners in this first LSQR pass.
- `Preconditioner`, `IdentityPreconditioner`, `DiagonalPreconditioner`,
  `PreconditionerDiagnostics`, and `as_preconditioner`: I0-6 direct-module
  right/model-space preconditioner contract used by the CGLS prototype.
- `SolverIterationRecord`, `SolverHistory`, and `SolverResult`: I0-1
  internal/prototype diagnostics containers. They are not a stable public
  solver-result schema and are not wired into the existing CG helpers yet.
- `dot_test` / `complex_dot_test`: real and complex adjoint dot-product checks.
- `conjugate_gradient`: small SPD or Hermitian system solver.
- `conjugate_gradient_normal`: small least-squares normal-equation solver with
  optional Tikhonov damping.
- `conjgrad_solve` / `complex_conjgrad_solve`: small mode dispatch helpers for
  `mode=normal`, `mode=spd`, and `mode=hermitian`.

Real dot tests check `<A x, y> == <x, A^T y>` with NumPy dot semantics. Complex
dot tests use NumPy `vdot` semantics and check the Hermitian adjoint
`<A x, y> == <x, A^H y>`.

This is not Madagascar's full external operator framework. The module-only CLIs
`dottest`, `cdottest`, `conjgrad`, and `cconjgrad` support matrix-backed RSF
operators and a toy identity dot-test operator. They do not execute arbitrary
shell commands, do not reproduce the upstream pipe/tempfile operator protocol,
do not support preconditioners, and do not stream large out-of-core datasets.
After I0-9B1 they provide small composition algebra, a regularization subset, a
small objective/residual/diagnostics problem layer, standalone diagnostics
containers, optional CG/CGNR history adapters, bounded CGLS with optional
right/model-space preconditioning, and bounded unpreconditioned/regularized
LSQR. They still do not provide preconditioned LSQR, a stable solver API,
constraints/masks, or domain inversion.

## Optional Compatibility Tests

Tests marked `original_madagascar` run only when the corresponding upstream
`sf*` command is available. They must skip cleanly on machines without
Madagascar. The comparison runner follows upstream RSF stream conventions:
primary input/output may be passed with explicit `stdin_path`/`stdout_path`,
binary stdout remains bytes by default, and text-only tools opt into decoding.
Legacy test calls containing `in=`/`out=` are translated for compatibility,
but new comparisons should use explicit stream paths.

These checks are optional validation, not part of the stable public processing
API. A comparison must distinguish bridge failure, intentional subset
difference, and real implementation mismatch. Only the shared documented
subset is asserted; differing history keys, singleton-axis retention, text
formatting, or quantile rank rules are not treated as byte-level compatibility.

# Module 23 Imaging Prototype Design

## Source Scan Summary

Madagascar contains many imaging programs. The table lists representative
programs found in the current source tree and how they relate to a Python
prototype.

| Program | Source path | Algorithm type | Input data | Velocity model | Output data | Migration difficulty | Python prototype | Keep C/C++ |
|---|---|---|---|---|---|---|---|---|
| `sfkirchnew` | `src-master/system/seismic/Mkirchnew.c`, `kirchnew.c` | 2D post-stack Kirchhoff time migration/modeling with antialiasing | 2D zero-offset/post-stack section, optional extra panels | constant `v0=` or 1D `velocity=` RMS velocity | migrated/modelled 2D section | medium | yes, as a simplified prototype | yes, for antialiasing and large loops |
| `sfkirchinv` | `src-master/system/seismic/Mkirchinv.c` | Kirchhoff inverse/least-squares style workflow | post-stack section | velocity information | image/model | high | no for M23 | yes |
| `sfpreconstkirch` | `src-master/system/seismic/Mpreconstkirch.c` | prestack constant-velocity Kirchhoff | `(time, cmp x, cmp y, offset)` | constant `vel=` | prestack migrated image or modeled gathers | high | no for M23 | yes |
| `sfshotconstkirch` | `src-master/system/seismic/Mshotconstkirch.c` | shot-profile Kirchhoff | `(time, offset, shot)` | constant `vel=` | image over output x, optionally offset gathers | high | no for M23 | yes |
| `sfstolt` | `src-master/system/seismic/Mstolt.c` | post-stack Stolt migration/modeling | laterally cosine-transformed data | constant `vel=` plus stretch | migrated/modelled section | medium-high | possible later | yes for interpolation/FFT |
| `sfprestolt` | `src-master/system/seismic/Mprestolt.c` | prestack Stolt migration/modeling | prestack frequency/cosine style data | constant `vel=` | stacked image or prestack output | high | no for M23 | yes |
| `sfgazdag` | `src-master/system/seismic/Mgazdag.c`, `gazdag.c` | Gazdag phase-shift migration/modeling | wavenumber-domain traces | constant or 1D velocity, optional VTI terms | time/depth migrated output | high | no for M23 | yes |
| `sfpmig` | `src-master/system/seismic/Mpmig.c` | slope-based prestack time migration | CMP gathers plus slope fields | implicit through slopes | migrated gathers/images | high | no for M23 | yes |
| `sfzomig` | `src-master/system/seismic/Mzomig.c`, `zomig.c` | zero-offset wave-equation migration | frequency/wavenumber wavefield style input | velocity model | image | high | no for M23 | yes |
| `sfmigsteep3` | `src-master/system/seismic/Mmigsteep3.c` | 3D steep-dip migration | 3D seismic volume | velocity parameters/model | 3D migrated image | very high | no | yes |

## Selected Prototype

The first imaging prototype is a simplified 2D post-stack zero-offset
Kirchhoff time migration. This corresponds most closely to `sfkirchnew`, but
does not attempt to reproduce its half-derivative filter, pseudo-unitary
weights, antialiasing branches, or exact amplitude behavior.

This choice is intentional:

- The input is a plain 2D RSF section with axes `n1=time` and `n2=midpoint`.
- A single diffraction point has a closed-form travel-time curve, so tests are
  small and deterministic.
- The core loop is easy to validate before moving performance-sensitive parts
  to C++.

## Mathematical Principle

For a migrated image point at midpoint `x_i` and vertical two-way time `tau`,
the zero-offset diffraction travel time at surface midpoint `x_s` is

```text
t(x_s; x_i, tau) = sqrt(tau^2 + (2 * (x_s - x_i) / v(tau))^2)
```

The migrated image is the sum of input amplitudes sampled along this hyperbola:

```text
image(x_i, tau) = sum_s data(x_s, t(x_s; x_i, tau))
```

Sampling in `t` uses linear interpolation. A constant velocity or a 1D velocity
function sampled on the time axis is supported. The optional normalization
divides by the number of contributing traces.

## Input And Output

Input RSF:

- 2D real-valued data.
- Axis 1: time, usually `label1=Time`, `unit1=s`.
- Axis 2: midpoint or lateral coordinate, usually `label2=Midpoint` or
  `label2=Offset`, `unit2=m`.

Velocity:

- scalar `velocity=2000`, or
- 1D RSF file with `n1` equal to the input time axis length.

Output RSF:

- same shape as the input by default: `(n2, n1)` in NumPy storage,
  `(n1, n2)` in RSF header order.
- Axis 1 label becomes `Migrated Time`.
- Axis 2 label becomes `Image X`.
- Header stores `kirchhoff_velocity`, `kirchhoff_normalize`, and
  `kirchhoff_algorithm=poststack_time`.

## Header Convention

The prototype keeps the same `n1/o1/d1` and `n2/o2/d2` sampling as the input.
This means migrated vertical time samples are sampled like input time samples.
For a future depth-migration variant, axis 1 should become depth and require
explicit `dz=`/`z0=` or a velocity-depth model.

## Correspondence To Madagascar

`src-master/system/seismic/Mkirchnew.c` calls `kirchnew_lop(adj,...)`:

- `adj=y`: migration.
- `adj=n`: modeling.
- `v0=` or `velocity=` controls RMS velocity.
- `hd=` enables a half-derivative filter.
- `sw=` selects antialiasing branches.

The Python prototype implements only the central zero-offset summation geometry
used by that family of Kirchhoff methods. It is a correctness and testing
scaffold, not a full replacement for `sfkirchnew`.

## Synthetic Test Data

A single diffraction point is synthesized by choosing an image point
`(x0, tau0)` and drawing a Gaussian event on the input section:

```text
data(x, t) = exp(-0.5 * ((t - sqrt(tau0^2 + (2*(x-x0)/v)^2)) / sigma)^2)
```

Migrating this section should produce a maximum near `(x0, tau0)`.

## Error Verification

The tests verify:

- output shape and dtype;
- header axis updates;
- single-diffraction peak location within one or two samples;
- CLI execution;
- parameter validation.

Exact amplitude equality with Madagascar is not expected in M23 because the
prototype omits antialiasing, half-derivative filtering, and pseudo-unitary
weights.

## Performance Bottlenecks

The naive implementation is `O(nt * nx_image * nx_data)` and uses nested Python
loops over image time and image midpoint. It is suitable for small tests but
not production-scale sections.

Hybrid/C++ acceleration should target:

- hyperbola traversal and interpolation loops;
- aperture pruning;
- vectorized or threaded image-point accumulation;
- optional amplitude weights;
- antialiasing stretch/filter logic compatible with `kirchnew.c`.


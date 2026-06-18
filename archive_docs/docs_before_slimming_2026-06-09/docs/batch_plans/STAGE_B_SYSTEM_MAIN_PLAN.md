# Stage B System/Main Batch Plan

Date: 2026-06-09

This document tracks Stage B after the Stage A release baseline. Stage B is
split into small batches so each command gets API, CLI, pytest, docs, examples,
and optional original Madagascar comparison coverage before the next batch
starts.

## Project Position

`pymadagascar` remains a Python-friendly local RSF/geophysics toolkit, not a
complete Madagascar clone. Pure Python must remain usable. Hybrid C++ remains
optional and is not part of Stage B-1 or B-2.

## B-1: Completed

Implemented low-risk system/main basics:

- `sfcp` via `copy_rsf_dataset`
- `sfrm` via `remove_rsf_dataset`
- `sfmin` via `min_rsf`/`minmax_rsf`
- `sfmax` via `max_rsf`/`minmax_rsf`
- Module-only CLIs:
  - `python -m pymadagascar.cli.cp`
  - `python -m pymadagascar.cli.rm`
  - `python -m pymadagascar.cli.min`
  - `python -m pymadagascar.cli.max`

No `pymada-*` console scripts were added in B-1.

## B-2: Completed

B-2 only covers these four commands:

- `sfmul`
- `sfdiv`
- `sftpow`
- `sfinterleave`

### B-2 Source Mapping

| Madagascar command | Original source path | Upstream behavior summary | Current pymadagascar subset | Direct source-backed? | Optional original comparison? |
| --- | --- | --- | --- | --- | --- |
| `sfmul` | `alias:sfadd`, implemented by `../src-master/system/main/add.c` | Program-name alias selects multiply mode in `sfadd`; upstream also supports preprocessing parameters such as `abs=`, `add=`, `log=`, `sqrt=`, `scale=`, and `exp=`. | `multiply_rsf`: one RSF times one compatible RSF, or one RSF times `scalar=`. | alias source-backed | yes, when upstream `sfmul` exists |
| `sfdiv` | `alias:sfadd`, implemented by `../src-master/system/main/add.c` | Program-name alias selects divide mode in `sfadd`; upstream skips division when a denominator sample is zero. | `divide_rsf`: one RSF divided by one compatible RSF, or one RSF divided by `scalar=`, with explicit `zero_policy=raise|warn|nan|inf`. | alias source-backed | yes, when upstream `sfdiv` exists |
| `sftpow` | `../src-master/user/nobody/Mtpow.c` | Time-power gain; original accepts float input and `tpow=`/`xpow=` on axes 1/2, using `o+(i+1)d` coordinates. The audit also records it as an alias-related `sfpow` entry. | `tpow_rsf`: `t ** power` gain along any 1-based RSF axis using local Axis coordinates `o+i*d`; `abs_time=` handles absolute coordinates. | source-backed, but from `user/nobody` not system/main | yes, constrained comparison when upstream `sftpow` exists |
| `sfinterleave` | `../src-master/system/main/interleave.c` | Interleave several same-size datasets along `axis=` and set output `n#` to input `n# * nin`. | `interleave_rsf`: two or more same-shape RSF files, 1-based `axis=`, inherited first header with updated `n#`. | direct system/main source-backed | yes, when upstream `sfinterleave` exists |

### B-2 Implemented APIs

- `pymadagascar.generic.array_math.multiply_rsf`
- `pymadagascar.generic.array_math.divide_rsf`
- `pymadagascar.generic.array_math.tpow_rsf`
- `pymadagascar.generic.interleave.interleave_rsf`

### B-2 Module-Only CLIs

- `python -m pymadagascar.cli.mul`
- `python -m pymadagascar.cli.div`
- `python -m pymadagascar.cli.tpow`
- `python -m pymadagascar.cli.interleave`

No new `pymada-*` console scripts are registered in B-2. Existing console script
count remains 25; user-facing CLI module count becomes 65.

### B-2 Unsupported Original Parameters

- `sfmul`/`sfdiv`: no multi-input reduction beyond one second RSF, no upstream
  `abs=`, `add=`, `log=`, `sqrt=`, `scale=`, `exp=`, or streaming behavior.
- `sfdiv`: zero denominators use explicit Python policies instead of upstream
  silent skip behavior.
- `sftpow`: no `xpow=`, no automatic estimation, no float-only restriction, and
  no promise to match original `o+(i+1)d` coordinates for all cases.
- `sfinterleave`: all inputs must have equal full shape; unequal target-axis
  lengths are not supported.

## B-3: Header / Metadata Batch

B-3 handles header-oriented commands cautiously because Madagascar uses several
different concepts that can be confused easily: ordinary RSF file headers,
file-backed data sidecars, trace/header tables, mask RSF files, and SEG-Y trace
headers.

### B-3 Goal

- Audit header / metadata command source before implementation.
- Establish a minimal `pymadagascar` model for header-mask window/cut behavior.
- Implement only `sfheaderwindow` and `sfheadercut` in B-3-1.
- Defer complex header table expression/stat/sort behavior and SEG-Y trace
  header generation to later batches.

### B-3 Command Layers

B-3-1 current implementation:

- `sfheaderwindow`
- `sfheadercut`

B-3-2 later implementation candidates:

- `sfheaderattr`
- `sfheadermath`
- `sfheadersort`

B-3-3 separate design:

- `sfsegyheader`

### B-3 Source Audit

| Madagascar command | Original source path | Upstream behavior summary | Current decision |
| --- | --- | --- | --- |
| `sfheaderwindow` | `../src-master/system/main/headerwindow.c` | Reads integer `mask=` of trace count `n2`; selects nonzero traces or `inv=` expands selected traces with zero-filled gaps. Writes ordinary RSF output and updates `n2`, while higher axes are collapsed to 1. | Implement B-3-1 Python mask subset: one-dimensional mask along a selected 1-based RSF axis; continuous selections only. |
| `sfheadercut` | `../src-master/system/main/headercut.c` | Reads integer `mask=` of trace count `n2`; writes original traces where mask is nonzero and zero traces where mask is zero. Shape and header are preserved. | Implement B-3-1 Python mask subset with explicit `cut_nonzero=`; default zeros nonzero mask samples, `cut_nonzero=n` matches upstream keep-nonzero behavior. |
| `sfheaderattr` | `../src-master/system/seismic/Mheaderattr.c` | Reads int/float header table and prints min/max/mean by key; uses SEG-Y keyword mapping by default. | Defer to B-3-2; current project lacks full header table model. |
| `sfheadermath` | `../src-master/system/seismic/Mheadermath.c` | Applies mathematical expressions to int/float header table rows, optionally replacing a key; uses SEG-Y/other key mapping. | Defer to B-3-2; requires header table expression design. |
| `sfheadersort` | `../src-master/system/main/headersort.c` | Sorts traces according to int/float header key file from `head=` or input `head=` history. | Defer to B-3-2; needs stable sort and header-table metadata model. |
| `sfsegyheader` | `../src-master/system/seismic/Msegyheader.c` | Builds integer SEG-Y trace header table for `sfsegywrite`, optionally merging `tfile=` and per-key files. | Defer to B-3-3; belongs to SEG-Y trace header design, not ordinary RSF header editing. |

### B-3 Key Semantics

- Ordinary RSF header: the key=value metadata in the `.rsf` header file.
- Sidecar data: the binary/ascii payload referenced by `in=`.
- Trace/header table: a data file whose samples represent per-trace keys; not
  equivalent to ordinary RSF header keys.
- Mask RSF: a small int/float RSF whose nonzero samples select or cut data along
  one RSF axis in the B-3-1 Python subset.
- Axis rules: CLI/API use Madagascar-style 1-based axis numbers; NumPy axis
  conversion is explicit.
- Shape update: `headerwindow` reduces `n#` on the selected axis; `headercut`
  preserves shape.
- Not supported in B-3-1: complete header table semantics, SEG-Y trace header
  generation, `inv=` reconstruction, non-contiguous `headerwindow` selections,
  streaming/out-of-core, and byte-level identity with upstream.

### B-3 Acceptance Criteria

- Source audit exists before implementation.
- Design doc exists: `docs/design/HEADER_METADATA_COMMANDS_DESIGN.md`.
- Each implemented command has Python API, module-only CLI, pytest, CLI
  subprocess coverage, optional original comparison hook, example, and docs.
- Coverage, CLI inventory, API stability, known limitations, compatibility,
  changelog, handoff, and test status are synchronized.
- Release/check tools pass.

## B-4: Deferred Operator/Optimization Batch

B-4 or later may handle:

- `sfdottest`
- `sfcdottest`
- `sfconjgrad`
- `sfcconjgrad`

These are explicitly out of scope for B-2.

## Stage B Non-Goals

- Do not add C++ kernels.
- Do not edit `../src-master`.
- Do not implement large imaging/modeling algorithms.
- Do not migrate `user/*` as a broad target.
- Do not register new `pymada-*` console scripts without a release policy.
- Do not move into Stage C during B-2.

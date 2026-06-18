# Header / Metadata Commands Design

Date: 2026-06-09

This design records the Stage B-3 source audit and the first safe Python subset
for `sfheaderwindow` and `sfheadercut`. It intentionally does not claim full
Madagascar header table or SEG-Y trace header compatibility.

## Current pymadagascar Header Capabilities

- `RSFHeader` stores ordinary RSF key=value metadata.
- `Axis` and `Hypercube` represent regular sampled axes from `n#`, `o#`, `d#`,
  `label#`, and `unit#`.
- `read_header` / `write_header` parse and write RSF text headers.
- `read_rsf` / `write_rsf` read and write file-backed RSF header + sidecar data.
- `info`, `get`, `put`, and `attr` operate on ordinary RSF file headers and
  deterministic metadata/statistics.
- `window`, `cut`, and `mask` already cover ordinary array windowing, zeroing,
  and value-based masks.

## Madagascar Header Semantics

Madagascar uses several related but distinct concepts:

- Ordinary RSF header: key=value fields attached to an RSF data file.
- Header table: an int/float RSF data file where samples encode per-trace keys.
- Trace header: per-trace metadata, commonly represented through header tables.
- SEG-Y header: SEG-Y trace header keys and binary layout used by SEG-Y I/O.
- Mask RSF: an int/float array whose samples can select traces.

Stage B-3-1 supports only ordinary RSF data plus a one-dimensional mask RSF. It
does not implement a general header table object, SEG-Y trace header generation,
or trace-header expression language.

## Source Audit Summary

| Command | Source path | Input type | Header table? | Trace header? | Ordinary RSF output? | Shape/data/header effect | Parameters seen in source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `sfheaderwindow` | `system/main/headerwindow.c` | ordinary RSF data + integer `mask=` RSF | mask file only | no full table | yes | selects traces; updates `n2`; collapses higher axes to 1; data content copied/zeroed for `inv=` | `mask=`, `inv=` |
| `sfheadercut` | `system/main/headercut.c` | ordinary RSF data + integer `mask=` RSF | mask file only | no full table | yes | preserves shape/header; zeroes traces where mask is zero | `mask=` |
| `sfheaderattr` | `system/seismic/Mheaderattr.c` | int/float header table | yes | SEG-Y key mapping by default | no, text output | reports min/max/mean by key | `segy=`, `desc=` |
| `sfheadermath` | `system/seismic/Mheadermath.c` | int/float header table | yes | SEG-Y or other key mapping | yes, header table output | may reduce to one key or replace a key | `segy=`, `key=`, `nkey=`, `output=`, `memsize=`, key aliases |
| `sfheadersort` | `system/main/headersort.c` | ordinary RSF data + int/float header key file | key file | trace order implied | yes | reorders traces; header mostly inherited | `head=` |
| `sfsegyheader` | `system/seismic/Msegyheader.c` | ordinary RSF data plus optional int key files | yes | SEG-Y trace header table | yes, int header table | creates or updates SEG-Y trace header table | `n1=`, `d1=`, `o1=`, `tfile=`, SEG-Y key names |

## `sfheaderwindow` Design

### Inputs

- `input_path`: file-backed ordinary RSF data.
- `mask_path`: one-dimensional or flattenable RSF mask with sample count equal
  to the selected axis length.
- `axis`: 1-based RSF axis. Default is 2 to mirror trace selection, but callers
  may use axis 1 for 1D data.
- `keep_nonzero`: if true, keep nonzero mask samples; if false, keep zero mask
  samples.

### Output

The output is ordinary RSF. It contains only the selected continuous window on
the selected axis.

### Mask And Axis Rules

- Mask values are converted to boolean with `mask != 0`.
- The B-3-1 subset requires the selected mask samples to form one continuous
  interval.
- Non-contiguous selections raise an error because ordinary RSF axes are regular
  and the current `Axis` model cannot represent arbitrary irregular trace
  selections.

### Shape And Header Rules

- Output shape is reduced only on the selected axis.
- `n#` is set to the selected count.
- `o#` is advanced by `first_selected_index * d#`.
- `d#`, labels, units, data format, and other metadata are inherited.

### Difference From `sfwindow`

`sfwindow` uses explicit `f#`, `n#`, `j#`, or coordinate bounds. `sfheaderwindow`
uses a mask/header RSF to derive the window.

### Unsupported Parameters

- Upstream `inv=` reconstruction.
- Non-contiguous trace selections.
- Header table key expressions.
- SEG-Y trace headers.
- Streaming/out-of-core.

## `sfheadercut` Design

### Inputs

- `input_path`: file-backed ordinary RSF data.
- `mask_path`: one-dimensional or flattenable RSF mask with sample count equal
  to the selected axis length.
- `axis`: 1-based RSF axis. Default is 2.
- `cut_nonzero`: if true, mask nonzero samples are zeroed. If false, mask zero
  samples are zeroed.

### Output

The output is ordinary RSF with the same shape and header as the input.

### Mask/Cut Rules

- `cut_nonzero=True` is the Python default and means "mask marks samples to
  remove".
- `cut_nonzero=False` matches the upstream `headercut.c` keep-nonzero behavior:
  zero mask samples are zeroed and nonzero samples are preserved.

### Difference From `sfcut`

`sfcut` zeroes an explicit index window. `sfheadercut` zeroes samples indicated
by a mask/header RSF along one axis.

### Unsupported Parameters

- General header table filters.
- SEG-Y trace headers.
- Streaming/out-of-core.

## Deferred Commands

- `sfheaderattr`: needs a header table model and text formatting policy.
- `sfheadermath`: needs safe expression semantics over header table rows.
- `sfheadersort`: needs trace sorting semantics and header table metadata rules.
- `sfsegyheader`: needs a separate SEG-Y trace header table design.

## Optional Original Comparison Strategy

- Tests named `test_original_*` are optional and skip when upstream `sf*`
  commands are unavailable.
- Windows pure Python tests do not depend on original Madagascar.
- WSL `ubuntu2204` can be used as an optional comparison environment when
  available; see `docs/WSL_MADAGASCAR_TESTING.md`.
- Older upstream Madagascar behavior should be recorded as a version difference
  before changing local code or tests.

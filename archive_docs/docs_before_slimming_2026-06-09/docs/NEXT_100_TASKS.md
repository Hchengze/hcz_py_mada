# Next 100 Tasks

生成日期：2026-06-06。本文基于 `docs/MADAGASCAR_FULL_COVERAGE_AUDIT.md` 的本地源码覆盖率审计生成。所有任务都应小到可以在一个 Codex 对话中完成；任务本身不是实现顺序的硬承诺。

## Priority Rules

- `P0`: 入口、文档、测试基线和高影响低风险维护。
- `P1`: core RSF/header/generic/signal 基础兼容工具。
- `P2`: seismic baseline、格式增强和设计先行的性能路线。
- `P3`: prototype 收敛、hybrid kernel 或较大范围扩展。
- `P4`: 明确暂缓、非目标或治理类任务。

## Task List

| # | Priority | Task | Acceptance criteria | Add tests? |
| ---: | --- | --- | --- | --- |
| 1 | `P0` | Done: decide CLI entry policy and register stable console_scripts | pyproject/docs agree on one policy; subprocess smoke test covers stable command paths. | yes |
| 2 | `P0` | Done: add a CLI inventory doc generated from pymadagascar/cli | Doc lists every current CLI module, expected invocation and source module. | no |
| 3 | `P0` | Done: add subprocess smoke test for sfspike-equivalent CLI | Test runs spike command via selected entry path and verifies RSF output shape. | yes |
| 4 | `P0` | Done: add subprocess smoke test for sfwindow-equivalent CLI | Test creates a fixture, windows it, and verifies header dimensions. | yes |
| 5 | `P0` | Done: add subprocess smoke test for sfmath-equivalent CLI | Test runs a deterministic expression and checks numeric output. | yes |
| 6 | `P0` | Done: document original Madagascar comparison environment | Docs explain RSFROOT/PATH requirements and how to run pytest -rs on a machine with sf* commands. | no |
| 7 | `P0` | Add a source-scan reproduction note for this audit | Audit doc records exact scan rules and caveats for M* files, aliases and book token counts. | no |
| 8 | `P0` | Done: create optional test marker strategy for original Madagascar comparisons | pytest docs explain how optional comparison tests skip and how to select them. | yes |
| 9 | `P0` | Done: update known limitations for command coverage denominator | KNOWN_LIMITATIONS or compatibility docs state full-source coverage and core coverage separately. | no |
| 10 | `P0` | Done: add docs-only warning for prototype seismic/imaging/modeling commands | Docs label NMO/Semblance/FK/Radon/Kirchhoff/acoustic2d as prototype or partial consistently. | no |
| 11 | `P0` | Done: add minimal example for sfattr-equivalent CLI | Subprocess smoke reads a small RSF and checks deterministic attributes. | yes |
| 12 | `P0` | Done: add minimal example for sfput-equivalent CLI | Subprocess smoke updates harmless header keys and verifies roundtrip. | yes |
| 13 | `P0` | Done: add minimal example for sfdd-equivalent dtype conversion | Subprocess smoke converts float32 to float64 and checks dtype/header. | yes |
| 14 | `P0` | Done: add audit regression check for current CLI count | `tools/check_cli_inventory.py` and `tests/test_release_tools.py` catch accidental disappearance of CLI modules or console scripts. | yes |
| 15 | `P0` | Done: add docs command-name consistency for stable console_scripts | Docs avoid stale pymada-* names unless console_scripts exist. | no |
| 16 | `P1` | Done: implement sfget header query subset | API and CLI return requested header values; missing key behavior documented. | yes |
| 17 | `P1` | Done: add optional original comparison for sfget | Test compares simple keys with original sfget when installed, otherwise skips. | yes |
| 18 | `P1` | Done: implement sfdisfil small numeric dump subset | CLI dumps small arrays deterministically with documented formatting. | yes |
| 19 | `P1` | Done: add optional original comparison for sfdisfil | Test compares a tiny float fixture with tolerances or documented text differences. | yes |
| 20 | `P1` | Done: expand sfdd native endian conversion tests | Roundtrip tests cover little/big native forms currently supported. | yes |
| 21 | `P1` | Done: add RSF ascii_float read/write tests | Tiny ascii_float fixtures document expected sidecar text semantics. | yes |
| 22 | `P1` | Done: implement RSF ascii_float read/write subset | Tiny ascii_float RSF roundtrips through read_rsf/write_rsf. | yes |
| 23 | `P1` | Add RSF int16/uint8 dtype design note | Docs decide whether short/uchar are in scope and map to NumPy dtypes. | no |
| 24 | `P1` | Done: implement safe `sfcp` subset and document `sfmv` omission | `cp` API/CLI/tests/example are present; `sfmv` behavior remains explicitly out of scope for Stage B-1. | yes |
| 25 | `P1` | Add sfcat streaming limitation test case | Test documents current in-memory behavior and safe failure for incompatible shapes. | yes |
| 26 | `P1` | Done: extend sfadd subset for multiply mode | `multiply_rsf` and module-only `mul` cover RSF x RSF and RSF x scalar; original `sfmul` remains an `sfadd` alias subset. | yes |
| 27 | `P1` | Done: extend sfadd subset for divide mode | `divide_rsf` and module-only `div` cover RSF / RSF and RSF / scalar with explicit `zero_policy`. | yes |
| 28 | `P1` | Done: add sfreal/sfimag/sfcmplx/sfrtoc scope decision note | Docs explain stable file-backed complex subset, `sfimag` alias handling, and deferred `sfrtoc pair=`/`complex128`. | no |
| 29 | `P1` | Done: implement sfreal/sfimag for complex RSF | Complex input produces real or imaginary component with correct dtype/header, API, CLI, example and optional original comparisons. | yes |
| 30 | `P1` | Done: implement sfcmplx/sfrtoc for basic complex conversion | Two real RSFs combine into complex RSF; real input converts to complex with zero imaginary part; shape/type errors are tested. | yes |
| 31 | `P1` | Done: add sfcut/headercut scope note | Docs distinguish data zeroing from header-mask cutting. | no |
| 32 | `P1` | Done: improve par=file parser compatibility tests | Parser tests cover whitespace, comments, repeated keys and CLI override order. | yes |
| 33 | `P1` | Done: implement a minimal par=file parser enhancement | CLI can load a small parameter file and command-line args override it. | yes |
| 34 | `P1` | Done: add sfheaderattr/header table scope note | `docs/design/HEADER_METADATA_COMMANDS_DESIGN.md` defines ordinary RSF header vs header table vs trace/SEG-Y header boundaries. | no |
| 35 | `P1` | Implement sfheaderattr small subset if accepted | API/CLI extracts selected metadata/header-derived attributes. | yes |
| 36 | `P1` | Done: add sfheadermath scope note | Design doc defers header table expression semantics to B-3-2 instead of treating it as ordinary RSF header math. | no |
| 37 | `P1` | Implement sfheadermath small subset if accepted | CLI applies a safe metadata expression to a deterministic header fixture. | yes |
| 38 | `P1` | Done: add sfsegyheader scope note | Design doc separates SEG-Y trace header table generation from ordinary RSF header/mask commands and defers it to B-3-3. | no |
| 39 | `P1` | Add SEG-Y trace header table fixture test | Synthetic SEG-Y fixture yields deterministic header table columns. | yes |
| 40 | `P1` | Add test for preserving n1 fastest-axis convention through generic commands | Generic operations verify RSF axis ordering after write/read. | yes |
| 41 | `P1` | Done: implement sfsmooth triangle smoothing baseline | Impulse response matches documented triangle kernel on 1D/2D fixtures. | yes |
| 42 | `P1` | Done: add optional original comparison for sfsmooth | Small constant fixture compares against original sfsmooth when installed. | yes |
| 43 | `P1` | Done: implement sfboxsmooth subset or parameter in smooth | Box smoothing impulse response is deterministic and documented. | yes |
| 44 | `P1` | Done: implement sfnoise seeded Gaussian/uniform subset | Seeded output is reproducible and header-compatible; supports direct generation and adding noise to existing RSF data. | yes |
| 45 | `P1` | Done: add optional original comparison for sfnoise | Comparison uses deterministic `var=0 rep=y` because NumPy RNG sequence intentionally differs from original Madagascar. | yes |
| 46 | `P1` | Done: implement sfricker-related Ricker wavelet utility subset | Direct time-domain generator has peak time, frequency, header, CLI and acoustic2d reuse tests. | yes |
| 47 | `P1` | Done: add optional original Ricker-family comparison smoke | Related `sfricker1` impulse smoke runs when original Madagascar is installed; full `sfricker` spectrum-estimation equivalence remains out of scope. | yes |
| 48 | `P1` | Done: expand sffft1 axis/header tests | FFT/IFFT/RFFT verify axis metadata, dtype, frequency axes, subprocess CLI and inverse consistency. | yes |
| 49 | `P1` | Done: document optional original inverse FFT scope | Existing forward original comparison remains; inverse path convention differences are documented in `docs/SIGNAL_COMPATIBILITY.md`. | yes |
| 50 | `P1` | Done: expand sfbandpass response tests | Tests cover flo/fhi transition edges, low/high suppression, taper midpoint, zero-phase behavior and subprocess CLI. | yes |
| 51 | `P1` | Done: add sfbandpass parameter compatibility table | Docs map implemented and missing parameters to Madagascar names in `docs/SIGNAL_COMPATIBILITY.md`. | no |
| 52 | `P2` | Implement sfcosft baseline if accepted | DCT/cosine transform fixture roundtrips or matches NumPy definition. | yes |
| 53 | `P2` | Add sfspectra scope note | Docs decide whether spectra/spectra2 enter signal module. | no |
| 54 | `P2` | Implement sfspectra minimal power spectrum | 1D sine fixture peaks at expected frequency. | yes |
| 55 | `P2` | Extend convolution mode tests | conv/corr/xcorr cover full/same/valid, dtype and header behavior. | yes |
| 56 | `P2` | Add direct convolution C++ design note | Docs define Python baseline, benchmark size and tolerance before C++ work. | no |
| 57 | `P2` | Implement direct convolution C++ kernel after design | C++ vs Python test passes and fallback remains default-safe. | yes |
| 58 | `P2` | Add interpolation scope note for sfstretch/remap/spline | Docs split interpolation tasks into pure baseline and future hybrid kernels. | no |
| 59 | `P2` | Implement 1D linear stretch baseline | Tiny monotonic mapping fixture produces expected interpolated samples. | yes |
| 60 | `P2` | Add optional original comparison for stretch baseline | Original comparison runs only when matching command is installed. | yes |
| 61 | `P2` | Expand gain/sfpow parameter compatibility table | Docs list implemented gain parameters and missing Madagascar behavior. | no |
| 62 | `P2` | Add AGC edge-padding behavior tests | AGC tests cover short traces and window larger than trace. | yes |
| 63 | `P2` | Add mute geometry/header scope note | Docs define offset/header source for mute and gather operations. | no |
| 64 | `P2` | Add stack axis/weighting tests | Stack tests cover axis selection, weights and header updates if supported. | yes |
| 65 | `P2` | Extend NMO offset table input design | Docs define offset vector/header/table input precedence. | no |
| 66 | `P2` | Implement NMO offset vector input | Synthetic CMP fixture with explicit offsets corrects to expected event alignment. | yes |
| 67 | `P2` | Add optional original comparison for NMO offset vector | Comparison uses tiny CMP and skips without sfnmo. | yes |
| 68 | `P2` | Extend Semblance velocity axis metadata tests | Output velocity/time axes and labels are deterministic. | yes |
| 69 | `P2` | Add Semblance synthetic velocity peak test | Synthetic hyperbola peaks near expected velocity. | yes |
| 70 | `P2` | Add NMO C++ kernel design note | Docs define inner-loop API, fallback, benchmark and tolerance. | no |
| 71 | `P2` | Implement nmo_interpolate_cpp after design | C++ and Python outputs match on small CMP; no compiler path still passes. | yes |
| 72 | `P2` | Add Semblance C++ kernel design note | Docs define scan kernel inputs and benchmark dimensions. | no |
| 73 | `P2` | Implement semblance_scan_cpp after design | C++ and Python outputs match; benchmark report updated. | yes |
| 74 | `P2` | Add FK mask parameter compatibility table | Docs map current fan/velocity mask to Madagascar FK/dipfilter parameters. | no |
| 75 | `P2` | Add FK synthetic slope-event test | Filter preserves/rejects expected slope band on tiny data. | yes |
| 76 | `P2` | Add Radon adjoint dot-product test | Forward/adjoint pair satisfies dot-product identity on small fixture. | yes |
| 77 | `P2` | Add Radon LS design note | Docs define least-squares interface, regularization and solver scope. | no |
| 78 | `P3` | Implement Radon least-squares prototype | Tiny synthetic event reconstructs within documented tolerance. | yes |
| 79 | `P2` | Add DMO/FKDMO scope note | Docs decide whether DMO remains deferred or enters a prototype milestone. | no |
| 80 | `P3` | Add velocity transform sfveltran design note | Docs split pure baseline from hybrid scatter/gather kernel. | no |
| 81 | `P2` | Add small public SEG-Y fixture plan | Docs identify source, license, size and expected regression fields. | no |
| 82 | `P2` | Add synthetic SEG-Y 3D inline/crossline test design | Test plan defines inline/crossline headers and RSF axes. | no |
| 83 | `P3` | Implement SEG-Y 3D synthetic read prototype | Synthetic 3D fixture maps to deterministic n1/n2/n3 axes. | yes |
| 84 | `P2` | Add Kirchhoff compatibility table against sfkirchnew | Docs list missing antialiasing, half derivative, weights and amplitudes. | no |
| 85 | `P2` | Add Kirchhoff amplitude regression fixture | Tiny diffraction test checks peak location and amplitude trend. | yes |
| 86 | `P3` | Add Kirchhoff C++ kernel design note | Docs define summation kernel API and benchmark before implementation. | no |
| 87 | `P3` | Implement Kirchhoff C++ summation after design | C++ and Python results match; fallback and benchmark pass. | yes |
| 88 | `P2` | Add acoustic2d stability/CFL docs | Docs state finite-difference order, boundary condition and stability limits. | no |
| 89 | `P2` | Add acoustic2d travel-time regression test | Homogeneous medium fixture arrives near expected travel time. | yes |
| 90 | `P3` | Add acoustic2d C++ timestep design note | Docs define timestep kernel, memory layout and benchmark. | no |
| 91 | `P3` | Implement acoustic2d C++ timestep after design | C++ and Python wavefields match within tolerance; fallback remains safe. | yes |
| 92 | `P3` | Add plot grey3/graph3 scope note | Docs decide whether 3D Matplotlib quicklook is in scope. | no |
| 93 | `P3` | Implement grey3 quicklook if accepted | Small 3D fixture writes deterministic PNG without VPlot dependency. | yes |
| 94 | `P3` | Add book hotspot migration policy | Docs define how top book commands influence priority without migrating book wholesale. | no |
| 95 | `P3` | Add tests/data policy | Docs define fixture size, licensing and generated-vs-checked-in data rules. | no |
| 96 | `P4` | Document VPlot/pens non-goals | Docs explicitly defer byte-level VPlot/pens compatibility and list accepted substitutes. | no |
| 97 | `P4` | Document SCons/book workflow non-goals | Docs state that reproducible book build system is not part of current package target. | no |
| 98 | `P4` | Document user/* migration gate | Docs require source review, fixture and owner rationale before any user/* command migration. | no |
| 99 | `P4` | Document trip/IWAVE/RVL non-goals | Docs explain why IWAVE/RVL/MPI/PETSc/CUDA should be separate projects or special milestones. | no |
| 100 | `P4` | Add recurring coverage audit update process | Docs define when to rerun source scan and how to update coverage percentages. | no |

## Recommended First 10

1. `P0` Done: decide CLI entry policy and register stable console_scripts. Acceptance: pyproject/docs agree on one policy; subprocess smoke tests cover stable command paths. Add tests: yes.
2. `P0` Done: add a CLI inventory doc generated from pymadagascar/cli. Acceptance: doc lists every current CLI module, expected invocation and source module. Add tests: no.
3. `P0` Done: add subprocess smoke test for sfspike-equivalent CLI. Acceptance: test runs spike command via selected entry path and verifies RSF output shape. Add tests: yes.
4. `P0` Done: add subprocess smoke test for sfwindow-equivalent CLI. Acceptance: test creates a fixture, windows it, and verifies header dimensions. Add tests: yes.
5. `P0` Done: add subprocess smoke test for sfmath-equivalent CLI. Acceptance: test runs a deterministic expression and checks numeric output. Add tests: yes.
6. `P0` Done: document original Madagascar comparison environment. Acceptance: docs explain RSFROOT/PATH requirements and how to run pytest -rs on a machine with sf* commands. Add tests: no.
7. `P0` Add a source-scan reproduction note for this audit。验收：Audit doc records exact scan rules and caveats for M* files, aliases and book token counts. 新增测试：no。
8. `P0` Done: create optional test marker strategy for original Madagascar comparisons. Acceptance: pytest docs explain how optional comparison tests skip and how to select them. Add tests: yes.
9. `P0` Done: update known limitations for command coverage denominator. Acceptance: KNOWN_LIMITATIONS or compatibility docs state full-source coverage and core coverage separately. Add tests: no.
10. `P0` Done: add docs-only warning for prototype seismic/imaging/modeling commands. Acceptance: docs label NMO/Semblance/FK/Radon/Kirchhoff/acoustic2d as prototype or partial consistently. Add tests: no.

## Notes

- 2026-06-08 handoff audit after P1-07: P1-06 (`sfsmooth`/`sfboxsmooth`) and
  P1-07 (`sfmask`/`sfcut`/`sfreverse`) were analyzed but not implemented at
  that time.
- 2026-06-09 P1-11: tasks #41-43 are now complete with
  `pymadagascar.signal.smooth`, `pymadagascar.cli.smooth`,
  `pymadagascar.cli.boxsmooth`, tests, docs, and `examples/smooth_demo.py`.
- 2026-06-09 P1-12: P1-07 (`sfmask`/`sfcut`/`sfreverse`) is now complete
  with `pymadagascar.generic.mask/cut/reverse`, CLI modules, tests, docs, and
  `examples/mask_cut_reverse_demo.py`.
- 2026-06-09 P1-13: tasks #48-51 are now complete as a tests/docs hardening
  pass for `sffft1`-style FFT and `sfbandpass`-style filtering. No signal
  algorithms were rewritten; compatibility boundaries live in
  `docs/SIGNAL_COMPATIBILITY.md`.
- 2026-06-09 stage-0 handoff audit: tasks #20-22 and #32-33 are confirmed
  complete in current code/tests/docs (`ascii_float`, endian tests, and
  `par=file` compatibility).
- 2026-06-09 stage A release baseline: task #14 is complete with
  `tools/check_release.py`, `tools/check_cli_inventory.py`,
  `tools/check_docs_commands.py`, `tests/test_release_tools.py`,
  `docs/RELEASE_CHECKLIST.md`, and `docs/CHANGELOG.md`.
- 2026-06-09 Stage B-1: task #24 is complete for the safe `sfcp` subset with
  `copy_rsf_dataset`, `python -m pymadagascar.cli.cp`, tests, docs, and
  `examples/cp_rm_min_max_demo.py`. `sfmv` remains deferred/documented.
- The same Stage B-1 batch also added safe `sfrm` removal and script-friendly
  `sfmin/sfmax` statistic subsets; `sfmin/sfmax` are documented as `sfstack`
  alias-adjacent text-statistic utilities, not full upstream RSF-output clones.
- 2026-06-09 Stage B-2: completed `sfmul`, `sfdiv`, `sftpow`, and
  `sfinterleave` as stable Python subsets with APIs, module-only CLIs, pytest,
  optional original-comparison hooks, docs, and
  `examples/mul_div_tpow_interleave_demo.py`. B-3 header commands and B-4
  dottest/conjgrad remain deferred.
- 2026-06-09 Stage B-3-1: completed source audit and design for header/metadata
  command boundaries, then implemented `sfheaderwindow` and `sfheadercut` as
  Python mask/header RSF subsets with APIs, module-only CLIs, pytest, optional
  original-comparison hooks, docs, and `examples/header_window_cut_demo.py`.
  `sfheaderattr`, `sfheadermath`, `sfheadersort`, `sfsegyheader`, and B-4
  dottest/conjgrad remain deferred.
- 任何新增功能任务都必须先读对应原始源码路径，不可只按命令名猜行为。
- 每个新增或扩展命令至少需要 Python API、CLI、pytest、docs；能找到原始 `sf*` 时还应有 optional comparison test。
- Hybrid 任务必须保持 Python fallback，并在没有 C++ 编译器时继续通过 pure Python 测试。
- `P4` 任务不是“永远不能做”，而是要求先明确边界，避免把完整 Madagascar 生态一次性搬进当前包。

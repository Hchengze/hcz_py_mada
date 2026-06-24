# Code Comment Guide

G4-1 establishes this guide for future core code and algorithm work. It does
not require rewriting old code in bulk, but new source-backed commands and
core algorithm edits should follow it.

## Guiding Rule

Use comments to explain why the code is shaped a certain way. Do not translate
every statement mechanically. A useful comment records the RSF contract,
source mapping, axis/header meaning, bounded subset boundary, or a non-obvious
numerical choice.

Public docstrings may remain English or use bilingual wording. Internal
comments around key algorithms should use Chinese whenever practical, because
that is the clearest working language for this project.

## Places That Need Chinese Comments

Add Chinese comments for these situations:

- RSF axis/header mapping: explain how `n#`, `o#`, `d#`, labels, units, and
  dtype are read, preserved, or changed.
- NumPy shape contracts: explain how NumPy dimensions map to RSF axes. For
  example, a 2-D RSF file with `n1=time`, `n2=trace` is usually stored as a
  NumPy array shaped `(n2, n1)`.
- Source-backed commands: name the Original Madagascar source file and explain
  which upstream behavior the Python code follows.
- Bounded subsets: state what is supported and what upstream modes are out of
  scope.
- Coordinates and sampling: explain physical coordinates, units, sample
  intervals, origins, and index direction when they matter.
- In-place behavior: explain when code intentionally returns a new object and
  when `inplace=True` is supported.
- Mask, geometry, gather, seismic axis, and side-input behavior: explain these
  explicitly because they are easy to misread from shapes alone.
- Tests with geophysical meaning: add short Chinese comments describing the
  RSF or geophysical scenario, not just the expected number.

## Source Mapping Comments

For a source-backed command, include a compact comment near the implementation
or wrapper:

```python
# 对齐 Madagascar 的 ../src-master/system/generic/Mexample.c。
# 本 bounded subset 只实现规则 RSF 网格上的 in-memory 行为；
# upstream 的 streaming/native-byte/extra side-output 模式不在本函数范围内。
```

If the command depends on a helper under `../src-master/api/c`, mention that
too:

```python
# Sobel stencil 来自 ../src-master/api/c/edge.c；
# 这里按 RSF n1/n2 平面处理，NumPy shape 为 (..., n2, n1)。
```

## RSF Axis And Shape Comments

When code reshapes, stacks, pads, sprays, transposes, windows, or gathers data,
write the axis contract before the transformation:

```python
# RSF axis 是 1-based：axis=2 表示 header 里的 n2/o2/d2。
# NumPy 存储顺序反过来，2-D 数据 shape=(n2, n1)，所以修改 RSF axis 2
# 时通常对应 NumPy 的倒数第二个维度。
```

For seismic gathers, be more explicit:

```python
# 输入约定为 n1=time, n2=offset, n3=shot。
# Python 数组 shape=(n3, n2, n1)。这里只处理规则采样 geometry，
# 不解释 SEG-Y trace headers 或不规则 source/receiver 坐标。
```

## Bounded Subset Comments

When intentionally omitting upstream behavior, say so close to the decision:

```python
# upstream 支持 mask side output；本 subset 只返回重排后的数据。
# 这样可以保持 RSFData chain 的单输出语义，mask 行为留给未来专题设计。
```

This avoids accidental compatibility promises and helps future audits decide
whether a missing behavior is intentional or a bug.

## Numerical And Boundary Comments

Add comments for boundary and numerical choices that affect test expectations:

```python
# Franklin pnpoly 的边界规则不是“所有边界都算 inside”。
# 为了和 Madagascar helper 行为一致，测试点只按 crossing 规则翻转 mask。
```

For filters and interpolation:

```python
# 这里不是 FFT taper convenience；Butterworth 递推状态来自 upstream helper。
# 若未来改成 NumPy/SciPy 近似，必须在 docs 中标为非 byte-identical subset。
```

## Test Comments

Tests should document the RSF/geophysical fixture being asserted:

```python
# 小型 CMP-like gather：axis1 是 time，axis2 是 signed offset。
# 这个 fixture 只验证规则 offset 的 bounded subset，不代表 SEG-Y geometry。
```

Do not add comments that simply restate the assertion:

```python
# Bad: 检查结果等于 expected。
```

## What Not To Do

- Do not add noisy comments for obvious assignments or simple loops.
- Do not claim full Madagascar compatibility unless the docs and tests prove
  it.
- Do not hide a source mismatch behind a vague comment such as "similar to
  Madagascar"; say what matches and what does not.
- Do not add comments that contradict coverage docs.
- Do not use comments to justify skipping or xfail-ing tests. Failing tests
  must be fixed or explicitly investigated.

## Checklist For Future Codex Passes

Before finishing a future implementation pass, check:

- Source-backed mapping is named in code, tests, and docs.
- RSF axis/header changes are explained.
- NumPy shape order is explained where non-obvious.
- Bounded subset and unsupported upstream behavior are stated.
- No-in-place or `inplace=True` behavior is tested and documented.
- Tests include a short scenario comment for masks, gathers, geometry,
  seismic axes, interpolation, or filters.
- Pythonic convenience remains labeled as convenience and is not counted as
  source-backed command coverage.

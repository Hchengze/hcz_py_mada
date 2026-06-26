# Source-Backed Command Proposal Template

## Purpose

这是后续新增 source-backed command 之前要填写的开发前模板。它用于把
source mapping、RSF axis/header、NumPy shape、bounded subset、测试和
coverage 决策先写清楚，再决定是否进入实现。

不要在本模板文件里填写某个真实 command 的结果。本文件是可复用模板，不
承诺 backlog 中任何候选一定会实现，也不是 coverage authority。

可以保留英文术语，例如 RSFData、source mapping、bounded subset、CLI、
console script 和 coverage。解释性文字尽量使用中文。

## 1. Candidate Summary

- Candidate:
- Proposed command name:
- Proposed Python topic module:
- Proposed owner area:
- Proceed / stop:

填写说明：简短说明这个候选想解决什么 RSF command workflow 问题，以及为
什么它属于 pymadagascar 当前主线。不要写成“为了增加 numerator”。

## 2. Official Source Mapping

- Official source:
- Helper source:
- Related aliases:
- Related command family:

填写说明：写出精确的 Original Madagascar source path。如果命令依赖
`../src-master/api/c` 或其他 helper，也要写出 helper path。source path 不清楚
时必须停止。

## 3. Upstream Semantics

- Five-line upstream summary:
- Input model:
- Output model:
- Important parameters:

填写说明：用五行以内说明 upstream 核心语义。若无法简洁说明，说明这个候选
还不适合实现，应该停留在 audit 或 design-first 阶段。

## 4. Current Project Overlap

- Existing Python implementation:
- Existing CLI:
- Existing `RSFData` method:
- Existing docs:
- Pythonic convenience conflict:
- Already counted:

填写说明：检查当前项目是否已有同名函数、相近 Pythonic convenience、prototype
或已计数 command。若语义不同，不能把现有 convenience 改写成 source-backed
coverage。

## 5. Risk Classification

- Risk:
- Risk reason:
- Required design before coding:

填写说明：风险只能写 low、medium、high 或 uncertain。medium 风险通常需要
专题设计后再实现；high 风险默认 deferred。

## 6. Input RSF Contract

- Required dtype:
- Required dimensions:
- Required `n#`:
- Required `o#`:
- Required `d#`:
- Required labels/units:
- Required header keys:

填写说明：说明输入 RSF header 的要求。RSF axis 是 1-based；例如 axis 2 指
header 中的 `n2/o2/d2`，不是 NumPy 的第二个维度。

## 7. Output RSF Contract

- Output dtype:
- Output dimensions:
- Changed axes:
- Preserved axes:
- New header keys:
- Removed or ignored header keys:

填写说明：说明输出数据和 header 如何变化，包括 `n#`、`o#`、`d#`、label、unit、
dtype、source metadata 等。shape-changing command 必须写清 axis 变化。

## 8. NumPy Shape Contract

- Input NumPy shape:
- Output NumPy shape:
- RSF-to-NumPy axis mapping:
- Shape-changing behavior:

填写说明：明确 NumPy shape 与 RSF `n1/n2/n3` 的对应关系。普通 2D RSF 通常是
`shape=(n2, n1)`；普通 3D gather 常见为 `shape=(n3, n2, n1)`。

## 9. Side Inputs / Side Outputs

- Side inputs:
- Side input RSF contracts:
- Side outputs:
- Side output handling:

填写说明：记录是否需要 `poly=`、`a0=`、`mask=`、`velocity=` 等 side input，或
mask、weights、report 等 side output。若 upstream 有 side output 而 bounded
subset 不支持，要明确写出。

## 10. Bounded Subset

- Supported parameters:
- Supported modes:
- In-memory/file-backed behavior:
- Streaming downgrade:

填写说明：只写 Python 实现准备支持的范围。bounded subset 要小、清楚、可测试。
如果 upstream 有 streaming/native-byte/pipe 行为，而 Python 只做 in-memory
NumPy subset，要明确说明降级。

## 11. Unsupported Upstream Behavior

- Unsupported parameters:
- Unsupported modes:
- Unsupported side inputs/outputs:
- Unsupported geometry:
- Unsupported streaming/native-byte behavior:

填写说明：这里是防止误承诺 full Madagascar compatibility 的关键小节。凡是不做
的 upstream 行为都要写清楚。

## 12. API Surface Plan

- Topic API:
- `RSFData` method:
- Root export:
- Source metadata:

填写说明：算法实现应放在 topic module，不应直接塞进 `api.py`。root export 默认
为 no。只有普通单输出数据语义才适合加 `RSFData` chain method。

## 13. CLI / Console Plan

- CLI module:
- Console script:
- Help smoke:
- File-backed subprocess test:

填写说明：说明是否需要 `python -m pymadagascar.cli.<name>` 和注册 console
script。不是每个 module-only 工具都需要 console script。

## 14. Test Plan

- Numeric fixture:
- RSF header/axis fixture:
- No-in-place test:
- Invalid parameter tests:
- CLI help test:
- CLI subprocess test:
- `RSFData` consistency test:
- Side input/output tests:
- Pythonic convenience no-miscount test:

填写说明：测试说明要写出小型 RSF 或地球物理场景，例如 axis 1 是 time、axis 2
是 offset。不要只写“检查结果等于 expected”。

## 15. Documentation Plan

- Coverage docs:
- API docs:
- User-facing docs:
- Known limitations:
- Changelog:

填写说明：列出实现后需要同步的文档。若计入 coverage，必须同步 coverage
authority；若不计数，也要避免 docs 暗示它是 source-backed command。

## 16. Chinese Comment Plan

- Source mapping comment:
- RSF axis/header comment:
- NumPy shape comment:
- Bounded subset comment:
- Test scenario comment:

填写说明：遵循 `CODE_COMMENT_GUIDE.md`。注释要解释为什么这样做，特别是 source
mapping、axis/header、shape contract、bounded subset 和测试场景，不要逐行翻译
显而易见的代码。

## 17. Coverage Admission Decision

- Counted:
- Full numerator change:
- Core numerator change:
- Direct numerator change:
- Denominator change:
- Reason:

填写说明：denominator change 应为 none。如果是否计数不确定，就不要计数。只
有 source mapping、bounded subset、tests 和 docs 都清楚时才允许增加 numerator。

## 18. Stop / Proceed Decision

- Decision:
- Stop reason:
- Proceed reason:
- Required follow-up:

填写说明：只能选择 stop、defer、design-first、implement one command，或在极低
风险时 implement two commands。不要为了增加 numerator 而 proceed。

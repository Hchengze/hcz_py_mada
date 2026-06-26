# Source Audit Worksheet

## Purpose

这是给 Codex 或人工开发者做 read-only source audit 时使用的临时 worksheet。
它用于记录候选命令的源码研读结果，再决定是否填写
`SOURCE_COMMAND_TEMPLATE.md`。

本 worksheet 不是 coverage authority，也不替代 `COVERAGE_AND_ROADMAP.md`。
如果 audit 结果不清楚，应停止在审计结论，不进入实现。

## Candidate Audit Table

| Field | Value |
| --- | --- |
| candidate |  |
| official source path |  |
| helper source path |  |
| family |  |
| upstream semantics |  |
| existing implementation |  |
| already counted? |  |
| Pythonic convenience conflict? |  |
| risk |  |
| decision |  |
| reason |  |

字段说明：

- `candidate`: 候选 command 名或候选 family 名。
- `official source path`: `../src-master` 下的精确 source path。
- `helper source path`: 如果依赖 `api/c` 或其他 helper，写出精确 helper path。
- `family`: unary、mask、statistic、axis transform、gather geometry、filter、
  interpolation、plot、solver 等清楚分类。
- `upstream semantics`: 用几句话概括官方源码核心行为。
- `existing implementation`: 当前 pymadagascar 中已有的 function、CLI、
  prototype 或 convenience。
- `already counted?`: yes、no 或 uncertain。若 uncertain，应停止。
- `Pythonic convenience conflict?`: 是否有同名或相近 convenience 可能被误计数。
- `risk`: low、medium、high 或 uncertain。
- `decision`: stop、defer、design-first 或 proposal-ready。
- `reason`: 简短说明为什么做这个决定。

## Source Reading Notes

- Files read:
- Parameters read:
- Input RSF assumptions:
- Output RSF assumptions:
- Axis/header changes:
- Streaming/native-byte behavior:
- Boundary conditions:
- Error handling:

填写说明：记录源码真正做了什么，而不是只记文件名。重点写清 RSF axis/header、
shape 变化、参数默认值、边界行为和 upstream 依赖。

## Helper-Level Dependencies

- Helper files:
- Helper functions:
- Boundary behavior:
- Numerical behavior:
- Byte-identical risk:

填写说明：如果 command 的关键行为来自 helper，应记录 helper 文件和函数。Python
bounded subset 不一定 byte-identical，但不能忽略 helper-level source mapping。

## Existing Project Overlap

- Existing topic API:
- Existing `RSFData` method:
- Existing CLI module:
- Existing console script:
- Existing docs:
- Existing tests:
- Existing coverage entry:

填写说明：说明 overlap 是真正 source-aligned，还是 Pythonic convenience、prototype
或 already-counted command。不要把 convenience 当成 source-backed command。

## Risk Notes

- Low-risk evidence:
- Medium-risk evidence:
- High-risk evidence:
- Unknowns:

填写说明：把风险证据写出来。若 unknown 会影响 source mapping、bounded subset、
tests 或 coverage，就不要进入实现。

## Implementation Decision

- Decision:
- Candidate count for this pass:
- Why this count is safe:
- Coverage effect:
- Denominator effect:

允许的 decision：

- stop with audit only;
- defer;
- design-first;
- implement one low-risk command;
- implement two extremely low-risk commands.

不要默认实现三个 command。不要为了增加 numerator 而实现。

## Required Follow-Up

- Proposal template needed:
- Design doc needed:
- Tests needed:
- Docs needed:
- Release inventory needed:
- Chinese comments needed:
- Full pytest needed:

填写说明：让下一步动作清楚可执行。audit worksheet 本身不修改 code、不改变
coverage，也不替代后续 proposal 和 tests。

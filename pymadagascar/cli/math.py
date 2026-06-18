"""Madagascar-style CLI for safe RSF math expressions."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.math import MathExpressionError, math_rsf
from pymadagascar.io.rsf import RSFError, SF_MAX_DIM, read_rsf, write_rsf


HELP_TEXT = """Math parameters:
  output=             Mathematical expression to evaluate.
  input.rsf           Optional input RSF file; expression may use input or data.
  n1= n2= n3=...      Output size when no input file is provided.
  o#= d#=             Axis origin and spacing; defaults to o#=0, d#=1.
  label#= unit#=      Optional axis label and unit.
  out=                Output RSF header path. Required for this file-backed CLI.

Supported expression variables are x1, x2, x3, ..., input, data, pi, and e.
Supported functions are sin, cos, tan, exp, log, sqrt, and abs.
"""


def math_command(params: RSFParams) -> int:
    expression = params.get_string("output")
    output = _output_file(params)
    if output in {"-", "stdout"}:
        raise ParameterParseError("pymada-math currently requires file-backed out=")

    input_path = _input_file(params)
    try:
        if input_path is not None:
            input_rsf = read_rsf(input_path)
            axes = _axes_from_input(input_rsf.header, params)
            result = math_rsf(expression, data=input_rsf, axes=axes)
        else:
            shape = _parse_shape(params)
            axes = _axes_from_params(params, shape)
            result = math_rsf(expression, axes=axes)
        write_rsf(output, result.data, result.header)
    except (MathExpressionError, ValueError, RSFError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        math_command,
        argv,
        prog="pymada-math",
        description="Evaluate safe NumPy math expressions on RSF coordinates and input data.",
        help_text=HELP_TEXT,
    )


def _input_file(params: RSFParams) -> str | None:
    value = params.params.get("in")
    if value is None and params.positionals:
        value = params.positionals[0]
    if value in {None, "", "-", "stdin"}:
        return None
    return value


def _output_file(params: RSFParams) -> str:
    value = params.params.get("out") or params.params.get("--out")
    if value is None and len(params.positionals) >= 2:
        value = params.positionals[1]
    if value in {None, ""}:
        raise MissingParameterError("out")
    return value


def _parse_shape(params: RSFParams) -> tuple[int, ...]:
    shape: list[int] = []
    for axis in range(1, SF_MAX_DIM + 1):
        key = f"n{axis}"
        if not params.has(key):
            break
        value = params.get_int(key)
        if value < 1:
            raise ParameterParseError(f"{key}= must be positive")
        shape.append(value)
    if not shape:
        raise MissingParameterError("n1")
    return tuple(shape)


def _axes_from_params(params: RSFParams, shape: tuple[int, ...]) -> tuple[Axis, ...]:
    axes: list[Axis] = []
    for index, size in enumerate(shape, start=1):
        axes.append(
            Axis(
                n=size,
                o=params.get_float(f"o{index}", 0.0),
                d=params.get_float(f"d{index}", 1.0),
                label=params.get_string(f"label{index}", None),
                unit=params.get_string(f"unit{index}", None),
                index=index,
            )
        )
    return tuple(axes)


def _axes_from_input(header, params: RSFParams) -> tuple[Axis, ...]:
    cube = Hypercube.from_header(header)
    axes: list[Axis] = []
    for axis in cube.axes:
        index = axis.index
        axes.append(
            axis.copy(
                o=params.get_float(f"o{index}", axis.o),
                d=params.get_float(f"d{index}", axis.d),
                label=params.get_string(f"label{index}", axis.label),
                unit=params.get_string(f"unit{index}", axis.unit),
            )
        )
    return tuple(axes)


if __name__ == "__main__":
    sys.exit(main())

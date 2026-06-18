"""Madagascar-style CLI for adding or generating synthetic noise."""

from __future__ import annotations

from collections.abc import Sequence
import sys

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.core.axis import Axis
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.generic.noise import NoiseError, noise_rsf
from pymadagascar.io.rsf import RSFError, SF_MAX_DIM, dtype_from_format


HELP_TEXT = """sfnoise-compatible Python subset:
  input.rsf           Optional input RSF file. If provided, add noise to it.
  n1= n2=...          Shape for direct noise generation when no input is given.
  out=output.rsf      Output RSF header path.
  seed=1              Fixed seed for reproducible NumPy random samples.
  mean=0              Noise mean.
  std=1               Noise standard deviation for normal noise.
  var=                Noise variance; overrides std= when provided.
  range=              Madagascar-style range; normal uses 2*range/9,
                      uniform uses [mean-range, mean+range].
  distribution=normal normal or uniform. type=y/n is also accepted.
  rep=y               Replace input with noise instead of adding noise.
  dtype=float32       Direct-generation dtype; default float32.

The random sequence is NumPy-based and is not byte-identical to original
sfnoise. Shape/header/dtype behavior is tested on small RSF fixtures.
"""


def noise_command(params: RSFParams) -> int:
    input_path = _input_file(params)
    output_path = params.output_path(required=True)
    assert output_path is not None

    try:
        shape = None if input_path is not None else _parse_shape(params)
        noise_rsf(
            input_path=input_path,
            output_path=output_path,
            shape=shape,
            seed=params.get_int("seed", None),
            mean=params.get_float("mean", 0.0),
            std=_parse_std(params),
            distribution=_parse_distribution(params),
            var=params.get_float("var", None),
            noise_range=params.get_float("range", None),
            replace=_parse_replace(params),
            dtype=_parse_dtype(params),
            axes=None if shape is None else _parse_axes(params, shape),
        )
    except (NoiseError, RSFError, OSError, ValueError) as exc:
        raise ParameterParseError(str(exc)) from exc
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run_rsf_command(
        noise_command,
        argv,
        prog="pymada-noise",
        description="Add random noise to RSF data or generate a noise RSF.",
        help_text=HELP_TEXT,
    )


def _input_file(params: RSFParams) -> str | None:
    value = params.params.get("in") or params.params.get("input")
    if value is None and params.positionals:
        value = params.positionals[0]
    if value in {None, "", "-", "stdin"}:
        return None
    return value


def _parse_shape(params: RSFParams) -> tuple[int, ...]:
    if params.has("shape"):
        shape = tuple(params.get_list("shape", item_type=int))
    else:
        values: list[int] = []
        for axis in range(1, SF_MAX_DIM + 1):
            key = f"n{axis}"
            if not params.has(key):
                break
            value = params.get_int(key)
            if value < 1:
                raise ParameterParseError(f"{key}= must be positive")
            values.append(value)
        shape = tuple(values)
    if not shape:
        raise MissingParameterError("n1")
    if any(size < 1 for size in shape):
        raise ParameterParseError("shape dimensions must be positive")
    return shape


def _parse_axes(params: RSFParams, shape: tuple[int, ...]) -> tuple[Axis, ...]:
    axes: list[Axis] = []
    for index, size in enumerate(shape, start=1):
        axes.append(
            Axis(
                n=size,
                o=params.get_float(f"o{index}", 0.0),
                d=params.get_float(f"d{index}", 0.004 if index == 1 else 0.1),
                label=params.get_string(
                    f"label{index}",
                    "Time" if index == 1 else "Distance",
                ),
                unit=params.get_string(f"unit{index}", "s" if index == 1 else "km"),
                index=index,
            )
        )
    return tuple(axes)


def _parse_distribution(params: RSFParams) -> str | bool:
    if params.has("distribution"):
        return params.get_string("distribution")
    if params.has("dist"):
        return params.get_string("dist")
    if params.has("type"):
        return params.get_bool("type")
    return "normal"


def _parse_std(params: RSFParams) -> float:
    if params.has("std"):
        return params.get_float("std")
    return params.get_float("sigma", 1.0)


def _parse_replace(params: RSFParams) -> bool:
    if params.has("rep"):
        return params.get_bool("rep")
    if params.has("replace"):
        return params.get_bool("replace")
    return False


def _parse_dtype(params: RSFParams) -> str:
    if params.has("data_format"):
        return str(dtype_from_format(params.get_string("data_format")))
    return params.get_string("dtype", "float32")


if __name__ == "__main__":
    sys.exit(main())

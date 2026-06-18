"""Evaluate safe NumPy math expressions on RSF coordinates and data."""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader


class MathExpressionError(ValueError):
    """Raised when a math expression is unsafe or unsupported."""


_ALLOWED_FUNCTIONS = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "exp": np.exp,
    "log": np.log,
    "sqrt": np.sqrt,
    "abs": np.abs,
}

_ALLOWED_CONSTANTS = {
    "pi": np.pi,
    "e": np.e,
}


def safe_eval_math(expression: str, variables: Mapping[str, Any] | None = None) -> Any:
    """Evaluate a restricted mathematical expression without Python ``eval``.

    Supported syntax is limited to numeric constants, named variables,
    unary ``+``/``-``, binary ``+``/``-``/``*``/``/``/``**``, parentheses, and
    calls to whitelisted NumPy math functions. Madagascar-style ``^`` is
    accepted as exponentiation and translated to ``**`` before parsing.
    """

    if not isinstance(expression, str) or not expression.strip():
        raise MathExpressionError("expression must be a non-empty string")

    prepared = expression.replace("^", "**")
    try:
        tree = ast.parse(prepared, mode="eval")
    except SyntaxError as exc:
        raise MathExpressionError(f"invalid math expression: {expression!r}") from exc

    names: dict[str, Any] = dict(_ALLOWED_CONSTANTS)
    if variables:
        names.update(variables)
    return _eval_node(tree.body, names)


def math_rsf(
    expression: str,
    header: RSFHeader | Mapping[str, Any] | None = None,
    data: RSFArray | np.ndarray | None = None,
    shape: int | Sequence[int] | None = None,
    axes: Sequence[Axis | Mapping[str, Any]] | None = None,
) -> RSFArray:
    """Evaluate ``expression`` over RSF coordinates and optional input data.

    ``shape`` and ``axes`` are in RSF order ``(n1, n2, ...)``. Returned data is
    float32 and stored in NumPy order ``(..., n2, n1)``.
    """

    input_array, input_header = _normalize_input(data, header)
    cube = _resolve_hypercube(input_array, input_header, shape, axes)
    base_header = input_header.copy() if input_header is not None else RSFHeader()
    output_header = cube.to_header(base_header)
    output_header["data_format"] = "native_float"
    output_header["esize"] = 4

    variables = _coordinate_variables(cube)
    if input_array is not None:
        if input_array.shape != cube.numpy_shape:
            raise ValueError(
                f"input data shape {input_array.shape} does not match header shape {cube.numpy_shape}"
            )
        variables["input"] = input_array
        variables["data"] = input_array

    result = safe_eval_math(expression, variables)
    output = _broadcast_result(result, cube.numpy_shape).astype(np.float32, copy=False)
    return RSFArray(np.ascontiguousarray(output), output_header)


def _eval_node(node: ast.AST, names: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise MathExpressionError(f"unsupported literal: {node.value!r}")

    if isinstance(node, ast.Name):
        if node.id in names:
            return names[node.id]
        raise MathExpressionError(f"unknown variable or constant: {node.id}")

    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, names)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise MathExpressionError("unsupported unary operator")

    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, names)
        right = _eval_node(node.right, names)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            return left**right
        raise MathExpressionError("unsupported binary operator")

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise MathExpressionError("only direct math function calls are allowed")
        function = _ALLOWED_FUNCTIONS.get(node.func.id)
        if function is None:
            raise MathExpressionError(f"unsupported math function: {node.func.id}")
        if node.keywords:
            raise MathExpressionError("keyword arguments are not allowed")
        args = [_eval_node(arg, names) for arg in node.args]
        return function(*args)

    raise MathExpressionError(f"unsupported expression syntax: {type(node).__name__}")


def _normalize_input(
    data: RSFArray | np.ndarray | None,
    header: RSFHeader | Mapping[str, Any] | None,
) -> tuple[np.ndarray | None, RSFHeader | None]:
    if isinstance(data, RSFArray):
        if header is not None:
            raise ValueError("header must not be provided separately when data is an RSFArray")
        return np.asarray(data.data), data.header

    input_header = None
    if header is not None:
        input_header = header.copy() if isinstance(header, RSFHeader) else RSFHeader(header)
    input_array = np.asarray(data) if data is not None else None
    return input_array, input_header


def _resolve_hypercube(
    data: np.ndarray | None,
    header: RSFHeader | None,
    shape: int | Sequence[int] | None,
    axes: Sequence[Axis | Mapping[str, Any]] | None,
) -> Hypercube:
    if axes is not None:
        normalized_axes = _normalize_axes(axes)
        cube = Hypercube(normalized_axes)
        if shape is not None and cube.shape != _normalize_shape(shape):
            raise ValueError("shape does not match axes")
    elif header is not None:
        cube = Hypercube.from_header(header)
        if shape is not None and cube.shape != _normalize_shape(shape):
            raise ValueError("shape does not match header dimensions")
    elif shape is not None:
        cube = Hypercube(_default_axes(_normalize_shape(shape)))
    elif data is not None:
        cube = Hypercube(_default_axes(tuple(reversed(data.shape))))
    else:
        raise ValueError("math_rsf requires data, header, axes, or shape")

    if data is not None and data.shape != cube.numpy_shape:
        raise ValueError(f"input data shape {data.shape} does not match RSF shape {cube.shape}")
    return cube


def _coordinate_variables(cube: Hypercube) -> dict[str, np.ndarray]:
    variables: dict[str, np.ndarray] = {}
    ndim = cube.ndim
    for axis in cube.axes:
        reshape = [1] * ndim
        reshape[ndim - axis.index] = axis.n
        values = axis.coordinates().reshape(reshape)
        variables[f"x{axis.index}"] = values
    return variables


def _broadcast_result(result: Any, shape: tuple[int, ...]) -> np.ndarray:
    array = np.asarray(result)
    try:
        return np.broadcast_to(array, shape)
    except ValueError as exc:
        raise ValueError(f"expression result with shape {array.shape} cannot broadcast to {shape}") from exc


def _normalize_axes(axes: Sequence[Axis | Mapping[str, Any]]) -> tuple[Axis, ...]:
    normalized: list[Axis] = []
    for index, axis in enumerate(axes, start=1):
        if isinstance(axis, Axis):
            normalized.append(axis.copy(index=index))
        else:
            if "n" not in axis:
                raise ValueError(f"axis {index} is missing n")
            normalized.append(
                Axis(
                    n=int(axis["n"]),
                    o=float(axis.get("o", 0.0)),
                    d=float(axis.get("d", 1.0)),
                    label=axis.get("label"),
                    unit=axis.get("unit"),
                    index=index,
                )
            )
    return tuple(normalized)


def _default_axes(shape: tuple[int, ...]) -> tuple[Axis, ...]:
    return tuple(Axis(n=size, o=0.0, d=1.0, index=index) for index, size in enumerate(shape, start=1))


def _normalize_shape(shape: int | Sequence[int]) -> tuple[int, ...]:
    if isinstance(shape, int):
        normalized = (shape,)
    else:
        normalized = tuple(int(size) for size in shape)
    if not normalized:
        raise ValueError("shape must contain at least one axis")
    if any(size < 1 for size in normalized):
        raise ValueError("all shape dimensions must be positive")
    return normalized

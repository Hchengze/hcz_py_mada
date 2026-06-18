"""RSF file information helpers."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, Literal

import numpy as np

from pymadagascar.io.rsf import RSFHeader, read_header, read_rsf


_MISSING = object()
DEFAULT_DISFIL_MAX_VALUES = 1000
HeaderCast = Literal["raw", "string", "int", "float"] | Callable[[str], Any] | None
DisfilAxisFormat = Literal["flat", "multi", "rsf", "none"]


class HeaderKeyError(ValueError):
    """Raised when a requested RSF header key is missing."""


class HeaderCastError(ValueError):
    """Raised when a header value cannot be cast to the requested type."""


class DisfilError(ValueError):
    """Raised when an RSF array cannot be formatted as a safe text dump."""


def info_rsf(path: str | Path) -> dict[str, Any]:
    """Return basic information about a file-backed RSF dataset."""

    header_path = Path(path).expanduser()
    header = read_header(header_path)
    binary_path = header.binary_path(header_path)
    expected_bytes = header.sample_count * header.esize
    actual_bytes = binary_path.stat().st_size if binary_path.exists() else None

    axes: list[dict[str, Any]] = []
    for axis in range(1, len(header.dimensions) + 1):
        axis_info = header.axis(axis)
        axes.append(
            {
                "index": axis,
                "n": int(axis_info["n"]) if axis_info["n"] is not None else 1,
                "o": axis_info["o"],
                "d": axis_info["d"],
                "label": axis_info["label"],
                "unit": axis_info["unit"],
            }
        )

    return {
        "path": header_path,
        "header": header,
        "binary_path": binary_path,
        "binary_exists": binary_path.exists(),
        "expected_bytes": expected_bytes,
        "actual_bytes": actual_bytes,
        "data_format": header.data_format,
        "esize": header.esize,
        "dimensions": header.dimensions,
        "numpy_shape": header.shape,
        "sample_count": header.sample_count,
        "dtype": header.dtype,
        "axes": axes,
    }


def get_header_value(
    path: str | Path,
    key: str,
    default: Any = _MISSING,
    cast: HeaderCast = None,
) -> Any:
    """Return one RSF header value.

    Missing keys raise ``HeaderKeyError`` unless ``default`` is provided. The
    default value is cast using the same rule as header values.
    """

    values = get_header_values(path, [key], default=default, cast=cast)
    return next(iter(values.values()))


def get_header_values(
    path: str | Path,
    keys: Iterable[str],
    default: Any = _MISSING,
    cast: HeaderCast = None,
) -> "OrderedDict[str, Any]":
    """Return requested RSF header values in key order."""

    header = read_header(path)
    normalized = [_normalize_key(key) for key in keys]
    if not normalized:
        raise ValueError("at least one header key is required")

    values: OrderedDict[str, Any] = OrderedDict()
    for key in normalized:
        if key in header:
            values[key] = _cast_header_value(header[key], cast=cast, key=key)
        elif default is not _MISSING:
            values[key] = _cast_header_value(default, cast=cast, key=key)
        else:
            raise HeaderKeyError(f"header key not found: {key}")
    return values


def format_header_values(values: dict[str, Any], *, parform: bool = True) -> str:
    """Format header values for stable CLI output."""

    lines: list[str] = []
    for key, value in values.items():
        text = _format_header_scalar(value)
        lines.append(f"{key}={text}" if parform else text)
    return "\n".join(lines)


def disfil_array(
    data: Any,
    header: RSFHeader | dict[str, Any] | None = None,
    max_values: int | None = None,
    precision: int = 6,
    axis_format: DisfilAxisFormat = "flat",
) -> str:
    """Return a stable text dump for a small RSF array.

    The default limit prevents accidental dumps of large RSF files. Pass an
    explicit ``max_values`` to show a different number of samples.
    """

    array = np.asarray(data)
    if array.ndim == 0:
        array = array.reshape(1)
    _validate_disfil_header(array, header)
    limit = _normalize_disfil_max_values(max_values)
    precision = _normalize_disfil_precision(precision)
    axis_format = _normalize_disfil_axis_format(axis_format)

    total = int(array.size)
    shown = min(total, limit)
    flat = array.ravel(order="C")
    lines: list[str] = []
    for linear_index in range(shown):
        value = _format_disfil_scalar(flat[linear_index], precision=precision)
        prefix = _format_disfil_axis(linear_index, array.shape, axis_format)
        lines.append(value if prefix is None else f"{prefix}\t{value}")
    if shown < total:
        lines.append(f"# truncated: shown={shown} total={total} max={limit}")
    return "\n".join(lines)


def disfil_rsf(
    path: str | Path,
    max_values: int | None = None,
    precision: int = 6,
    axis_format: DisfilAxisFormat = "flat",
) -> str:
    """Read an RSF file and return a safe, stable text dump of its data."""

    rsf = read_rsf(path)
    return disfil_array(
        rsf.data,
        rsf.header,
        max_values=max_values,
        precision=precision,
        axis_format=axis_format,
    )


def format_info(info: dict[str, Any]) -> str:
    """Format ``info_rsf`` output as compact command-line text."""

    header: RSFHeader = info["header"]
    lines = [
        f"path: {info['path']}",
        f"data_format: {info['data_format']}",
        f"esize: {info['esize']}",
        f"in: {header.get_string('in', '')}",
        f"binary_path: {info['binary_path']}",
        f"binary_exists: {str(info['binary_exists']).lower()}",
        f"bytes: expected={info['expected_bytes']} actual={info['actual_bytes']}",
        "dimensions: " + " ".join(f"n{i + 1}={n}" for i, n in enumerate(info["dimensions"])),
        "numpy_shape: " + "x".join(str(size) for size in info["numpy_shape"]),
        f"samples: {info['sample_count']}",
        f"dtype: {info['dtype']}",
    ]

    for axis in info["axes"]:
        pieces = [f"axis{axis['index']}"]
        for key in ("o", "d", "label", "unit"):
            value = axis[key]
            if value is not None:
                pieces.append(f"{key}={value}")
        lines.append(" ".join(pieces))

    return "\n".join(lines)


def _normalize_key(key: str) -> str:
    normalized = str(key).strip()
    if not normalized:
        raise ValueError("header key must not be empty")
    return normalized


def _cast_header_value(value: Any, *, cast: HeaderCast, key: str) -> Any:
    if cast is None:
        return str(value)
    if isinstance(cast, str):
        normalized = cast.strip().lower()
        if normalized in {"raw", "string"}:
            return str(value)
        if normalized == "int":
            try:
                return int(str(value), 10)
            except (TypeError, ValueError) as exc:
                raise HeaderCastError(
                    f"cannot cast header key {key!r} value {value!r} to int"
                ) from exc
        if normalized == "float":
            try:
                return float(str(value))
            except (TypeError, ValueError) as exc:
                raise HeaderCastError(
                    f"cannot cast header key {key!r} value {value!r} to float"
                ) from exc
        raise HeaderCastError(f"unsupported header cast {cast!r}")
    try:
        if callable(cast):
            return cast(str(value))
    except (TypeError, ValueError) as exc:
        name = getattr(cast, "__name__", str(cast))
        raise HeaderCastError(f"cannot cast header key {key!r} value {value!r} to {name}") from exc
    raise HeaderCastError(f"unsupported header cast {cast!r}")


def _format_header_scalar(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _validate_disfil_header(
    array: np.ndarray,
    header: RSFHeader | dict[str, Any] | None,
) -> None:
    if header is None:
        return
    rsf_header = header if isinstance(header, RSFHeader) else RSFHeader(header)
    if rsf_header.shape != array.shape:
        raise DisfilError(
            f"header shape {rsf_header.shape} does not match data shape {array.shape}"
        )


def _normalize_disfil_max_values(max_values: int | None) -> int:
    if max_values is None:
        return DEFAULT_DISFIL_MAX_VALUES
    try:
        limit = int(max_values)
    except (TypeError, ValueError) as exc:
        raise DisfilError(f"max_values must be an integer, got {max_values!r}") from exc
    if limit < 1:
        raise DisfilError("max_values must be at least 1")
    return limit


def _normalize_disfil_precision(precision: int) -> int:
    try:
        value = int(precision)
    except (TypeError, ValueError) as exc:
        raise DisfilError(f"precision must be an integer, got {precision!r}") from exc
    if value < 1:
        raise DisfilError("precision must be at least 1")
    return value


def _normalize_disfil_axis_format(axis_format: str) -> DisfilAxisFormat:
    normalized = str(axis_format).strip().lower()
    if normalized not in {"flat", "multi", "rsf", "none"}:
        raise DisfilError("axis_format must be one of flat, multi, rsf, or none")
    return normalized  # type: ignore[return-value]


def _format_disfil_axis(
    linear_index: int,
    shape: tuple[int, ...],
    axis_format: DisfilAxisFormat,
) -> str | None:
    if axis_format == "none":
        return None
    if axis_format == "flat":
        return str(linear_index)
    multi = np.unravel_index(linear_index, shape, order="C")
    if axis_format == "multi":
        return "(" + ",".join(str(index) for index in multi) + ")"
    rsf_indices = tuple(reversed(multi))
    return ",".join(f"i{axis}={index}" for axis, index in enumerate(rsf_indices, start=1))


def _format_disfil_scalar(value: Any, *, precision: int) -> str:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, complex):
        real = _format_disfil_float(value.real, precision=precision)
        imag = _format_disfil_float(abs(value.imag), precision=precision)
        sign = "+" if value.imag >= 0 else "-"
        return f"{real}{sign}{imag}j"
    if isinstance(value, float):
        return _format_disfil_float(value, precision=precision)
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def _format_disfil_float(value: float, *, precision: int) -> str:
    return f"{float(value):.{precision}g}"

"""Minimal RSF-backed header table helpers.

The project-level header table subset stores one numeric table in an ordinary
RSF file. RSF ``n1`` is the number of header keys (columns), and RSF ``n2`` is
the number of rows/traces. Key names are recorded as ``key1=``, ``key2=``, ...
and mirrored in ``header_keys=`` for easy inspection.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re

import numpy as np

from pymadagascar.generic.math import MathExpressionError, safe_eval_math
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


_KEY_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class HeaderTableError(ValueError):
    """Raised when a minimal RSF header table is invalid or unsupported."""


@dataclass(frozen=True)
class HeaderTable:
    """Numeric header table data, key names, and RSF metadata."""

    data: np.ndarray
    keys: tuple[str, ...]
    header: RSFHeader
    header_path: Path | None = None

    @property
    def row_count(self) -> int:
        return int(self.data.shape[0])

    @property
    def key_count(self) -> int:
        return int(self.data.shape[1])

    def key_index(self, key: str) -> int:
        try:
            return self.keys.index(key)
        except ValueError as exc:
            raise HeaderTableError(
                f"header table has no key {key!r}; available keys: {', '.join(self.keys)}"
            ) from exc

    def column(self, key: str) -> np.ndarray:
        return np.asarray(self.data[:, self.key_index(key)])

    def as_columns(self) -> dict[str, np.ndarray]:
        return {key: self.column(key).copy() for key in self.keys}


def read_header_table(path: str | Path) -> HeaderTable:
    """Read a minimal RSF-backed header table."""

    rsf = read_rsf(path)
    data = _validate_table_data(rsf.data)
    keys = _keys_from_header(rsf.header, data.shape[1])
    return HeaderTable(data, keys, rsf.header.copy(), rsf.header_path)


def write_header_table(
    path: str | Path,
    table: HeaderTable | Mapping[str, Sequence[Any]] | np.ndarray,
    header: RSFHeader | Mapping[str, Any] | None = None,
    *,
    data_format: str | None = None,
) -> HeaderTable:
    """Write a minimal header table as an ordinary RSF file."""

    data, keys, base_header = _coerce_table(table, header)
    output_header = _header_with_keys(base_header, keys)
    written = write_rsf(path, data, output_header, data_format=data_format)
    return HeaderTable(np.asarray(written.data), keys, written.header.copy(), written.header_path)


def header_table_attr(
    path: str | Path,
    keys: str | Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Return count/min/max/mean statistics for selected header table keys."""

    table = read_header_table(path)
    selected = _selected_keys(table, keys)
    stats: list[dict[str, Any]] = []
    for key in selected:
        values = np.asarray(table.column(key), dtype=np.float64)
        finite = values[np.isfinite(values)]
        if finite.size:
            minimum = float(np.min(finite))
            maximum = float(np.max(finite))
            mean = float(np.mean(finite))
        else:
            minimum = maximum = mean = float("nan")
        stats.append(
            {
                "key": key,
                "count": int(finite.size),
                "min": minimum,
                "max": maximum,
                "mean": mean,
            }
        )
    return stats


def format_header_table_attr(stats: Sequence[Mapping[str, Any]]) -> str:
    """Format ``header_table_attr`` results as stable CLI text."""

    lines = ["key count min max mean"]
    for item in stats:
        lines.append(
            " ".join(
                [
                    str(item["key"]),
                    str(int(item["count"])),
                    _format_number(float(item["min"])),
                    _format_number(float(item["max"])),
                    _format_number(float(item["mean"])),
                ]
            )
        )
    return "\n".join(lines)


def header_table_math(
    input_path: str | Path,
    output_path: str | Path,
    expression: str,
    *,
    key: str | None = None,
    out_key: str | None = None,
    overwrite: bool = False,
) -> HeaderTable:
    """Compute a new or replacement key from a safe expression over columns."""

    target_key = out_key or key
    if not target_key:
        raise HeaderTableError("out_key= is required")
    _validate_key_name(target_key)

    table = read_header_table(input_path)
    existing = target_key in table.keys
    if existing and not overwrite:
        raise HeaderTableError(
            f"key {target_key!r} already exists; pass overwrite=True to replace it"
        )

    variables = {name: table.column(name).astype(np.float64, copy=False) for name in table.keys}
    try:
        result = safe_eval_math(expression, variables)
    except MathExpressionError as exc:
        raise HeaderTableError(str(exc)) from exc

    column = _broadcast_column(result, table.row_count, expression)
    output = table.data.astype(np.float32, copy=True)
    if existing:
        keys = table.keys
        output[:, table.key_index(target_key)] = column
    else:
        keys = table.keys + (target_key,)
        output = np.column_stack([output, column]).astype(np.float32, copy=False)

    return write_header_table(output_path, HeaderTable(output, keys, table.header.copy()))


def header_table_sort(
    input_path: str | Path,
    output_path: str | Path,
    key: str,
    *,
    reverse: bool = False,
    stable: bool = True,
) -> HeaderTable:
    """Sort a header table's rows by one key."""

    table = read_header_table(input_path)
    values = np.asarray(table.column(key), dtype=np.float64)
    kind = "stable" if stable else "quicksort"
    order = np.argsort(-values if reverse else values, kind=kind)
    sorted_data = np.ascontiguousarray(table.data[order])
    return write_header_table(output_path, HeaderTable(sorted_data, table.keys, table.header.copy()))


header_attr_table = header_table_attr
header_math_table = header_table_math
header_sort_table = header_table_sort
headermath_rsf = header_table_math
headersort_rsf = header_table_sort


def _coerce_table(
    table: HeaderTable | Mapping[str, Sequence[Any]] | np.ndarray,
    header: RSFHeader | Mapping[str, Any] | None,
) -> tuple[np.ndarray, tuple[str, ...], RSFHeader]:
    if isinstance(table, HeaderTable):
        data = np.asarray(table.data)
        keys = table.keys
        base_header = table.header.copy()
        if header is not None:
            base_header = header.copy() if isinstance(header, RSFHeader) else RSFHeader(header)
    elif isinstance(table, Mapping):
        keys = tuple(str(key) for key in table)
        _validate_keys(keys)
        columns = [np.asarray(values) for values in table.values()]
        if not columns:
            raise HeaderTableError("header table requires at least one key")
        lengths = {column.reshape(-1).size for column in columns}
        if len(lengths) != 1:
            raise HeaderTableError("all header table columns must have the same length")
        data = np.column_stack([column.reshape(-1) for column in columns])
        base_header = header.copy() if isinstance(header, RSFHeader) else RSFHeader(header)
    else:
        data = np.asarray(table)
        base_header = header.copy() if isinstance(header, RSFHeader) else RSFHeader(header)
        data = _normalize_array_data(data)
        keys = _keys_from_header(base_header, data.shape[1])

    data = _validate_table_data(data)
    _validate_keys(keys)
    if data.shape[1] != len(keys):
        raise HeaderTableError(
            f"header table has {data.shape[1]} columns but {len(keys)} key names"
        )
    return np.ascontiguousarray(_cast_supported_table_dtype(data)), keys, base_header


def _validate_table_data(data: np.ndarray) -> np.ndarray:
    normalized = _normalize_array_data(np.asarray(data))
    dtype = normalized.dtype
    if np.iscomplexobj(normalized):
        raise HeaderTableError("header table data must be real numeric values")
    if not (
        np.issubdtype(dtype, np.integer)
        or np.issubdtype(dtype, np.unsignedinteger)
        or np.issubdtype(dtype, np.floating)
        or np.issubdtype(dtype, np.bool_)
    ):
        raise HeaderTableError("header table data must be numeric")
    return normalized


def _cast_supported_table_dtype(data: np.ndarray) -> np.ndarray:
    dtype = np.asarray(data).dtype
    if np.issubdtype(dtype, np.bool_):
        return np.asarray(data, dtype=np.int32)
    if np.issubdtype(dtype, np.integer) or np.issubdtype(dtype, np.unsignedinteger):
        return np.asarray(data, dtype=np.int32)
    if dtype == np.dtype("float64"):
        return np.asarray(data, dtype=np.float64)
    return np.asarray(data, dtype=np.float32)


def _normalize_array_data(data: np.ndarray) -> np.ndarray:
    if data.ndim == 1:
        data = data.reshape((-1, 1))
    if data.ndim != 2:
        raise HeaderTableError("header table data must be a two-dimensional array")
    if data.shape[0] < 1:
        raise HeaderTableError("header table requires at least one row")
    if data.shape[1] < 1:
        raise HeaderTableError("header table requires at least one key")
    return data


def _keys_from_header(header: RSFHeader, nkeys: int) -> tuple[str, ...]:
    raw = header.get("header_keys") or header.get("keys")
    if raw:
        keys = tuple(part.strip() for part in str(raw).split(",") if part.strip())
    else:
        keys = tuple(str(header.get(f"key{index}", "")).strip() for index in range(1, nkeys + 1))
        if any(not key for key in keys):
            raise HeaderTableError(
                "header table is missing key names; provide key1/key2/... or header_keys="
            )

    _validate_keys(keys)
    if len(keys) != nkeys:
        raise HeaderTableError(f"header has {len(keys)} key names but table has {nkeys} columns")
    return keys


def _header_with_keys(header: RSFHeader, keys: tuple[str, ...]) -> RSFHeader:
    output = header.copy()
    _validate_keys(keys)
    output["header_table"] = "pymadagascar-minimal"
    output["header_keys"] = ",".join(keys)
    output["header_nkeys"] = len(keys)
    for index, key in enumerate(keys, start=1):
        output[f"key{index}"] = key
    for name in list(output):
        match = re.fullmatch(r"key(\d+)", name)
        if match and int(match.group(1)) > len(keys):
            del output[name]
    if "label1" not in output:
        output["label1"] = "Header key"
    if "label2" not in output:
        output["label2"] = "Trace"
    return output


def _selected_keys(table: HeaderTable, keys: str | Sequence[str] | None) -> tuple[str, ...]:
    if keys is None:
        return table.keys
    if isinstance(keys, str):
        selected = tuple(part.strip() for part in keys.split(",") if part.strip())
    else:
        selected = tuple(str(key).strip() for key in keys if str(key).strip())
    if not selected:
        raise HeaderTableError("key selection is empty")
    for key in selected:
        table.key_index(key)
    return selected


def _broadcast_column(result: Any, rows: int, expression: str) -> np.ndarray:
    array = np.asarray(result)
    if np.iscomplexobj(array):
        raise HeaderTableError("headermath expressions must produce real values")
    if array.shape == ():
        return np.full(rows, float(array), dtype=np.float32)
    try:
        column = np.broadcast_to(array, (rows,))
    except ValueError as exc:
        raise HeaderTableError(
            f"expression result for {expression!r} cannot broadcast to {rows} rows"
        ) from exc
    return np.asarray(column, dtype=np.float32)


def _validate_keys(keys: Sequence[str]) -> None:
    if not keys:
        raise HeaderTableError("header table requires at least one key")
    seen: set[str] = set()
    for key in keys:
        _validate_key_name(key)
        if key in seen:
            raise HeaderTableError(f"duplicate header table key {key!r}")
        seen.add(key)


def _validate_key_name(key: str) -> None:
    if not _KEY_NAME_RE.match(str(key)):
        raise HeaderTableError(
            f"header table key {key!r} must be a valid Python identifier"
        )


def _format_number(value: float) -> str:
    return f"{value:.7g}"

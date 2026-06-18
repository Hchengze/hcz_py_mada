"""Data copying, type conversion, and endian conversion for RSF files."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray, RSFHeader, format_from_dtype, read_rsf, write_rsf


class DDError(ValueError):
    """Raised when an sfdd-style conversion is unsupported or unsafe."""


_TYPE_ALIASES: dict[str, np.dtype[Any]] = {
    "float": np.dtype("float32"),
    "float32": np.dtype("float32"),
    "native_float": np.dtype("float32"),
    "double": np.dtype("float64"),
    "float64": np.dtype("float64"),
    "native_double": np.dtype("float64"),
    "int": np.dtype("int32"),
    "int32": np.dtype("int32"),
    "integer": np.dtype("int32"),
    "native_int": np.dtype("int32"),
    "complex": np.dtype("complex64"),
    "complex64": np.dtype("complex64"),
    "native_complex": np.dtype("complex64"),
}

_SUPPORTED_BASE_DTYPES = {
    np.dtype("float32"),
    np.dtype("float64"),
    np.dtype("int32"),
    np.dtype("complex64"),
}

_BIG_ENDIAN_ALIASES = {"big", "be", "xdr"}
_LITTLE_ENDIAN_ALIASES = {"little", "le"}
_NATIVE_ENDIAN_ALIASES = {"native", "="}


def copy_rsf(input_path: str | Path, output_path: str | Path) -> RSFArray:
    """Copy an RSF file while preserving supported dtype/form metadata."""

    rsf = read_rsf(input_path)
    output_dtype = rsf.header.dtype
    output = _cast_values(rsf.data, output_dtype)
    return write_rsf(output_path, output, rsf.header.copy())


def convert_dtype_rsf(
    input_path: str | Path,
    output_path: str | Path,
    dtype: str | np.dtype[Any],
    *,
    trunc: bool = False,
) -> RSFArray:
    """Convert an RSF file to a supported numeric dtype.

    The output keeps the input form when possible: XDR input stays XDR, native
    input stays native. Complex conversions preserve the array shape; converting
    real data to complex creates a zero imaginary part.
    """

    rsf = read_rsf(input_path)
    base_dtype = normalize_dtype(dtype)
    output_dtype = _with_input_form(base_dtype, rsf.header)
    output = _cast_values(rsf.data, output_dtype, trunc=trunc)
    return write_rsf(output_path, output, rsf.header.copy())


def convert_endian_rsf(
    input_path: str | Path,
    output_path: str | Path,
    endian: str,
) -> RSFArray:
    """Convert the binary payload to little/native or XDR big-endian form."""

    rsf = read_rsf(input_path)
    output_dtype = dtype_with_endian(normalize_dtype(rsf.data.dtype), endian)
    output = _cast_values(rsf.data, output_dtype)
    return write_rsf(output_path, output, rsf.header.copy(), data_format=format_from_dtype(output_dtype))


def convert_to_ascii_float_rsf(
    input_path: str | Path,
    output_path: str | Path,
    dtype: str | np.dtype[Any] | None = None,
    *,
    trunc: bool = False,
) -> RSFArray:
    """Convert an RSF file to the supported ascii_float sidecar subset."""

    rsf = read_rsf(input_path)
    target_dtype = normalize_dtype(dtype or rsf.data.dtype)
    if target_dtype not in {np.dtype("float32"), np.dtype("float64")}:
        raise DDError("form=ascii only supports float32/float64 values in this subset")
    output = _cast_values(rsf.data, target_dtype, trunc=trunc)
    return write_rsf(output_path, output, rsf.header.copy(), data_format="ascii_float")


def normalize_dtype(dtype: str | np.dtype[Any]) -> np.dtype[Any]:
    """Normalize an sfdd/NumPy dtype name to a supported native dtype."""

    if isinstance(dtype, str):
        key = dtype.strip().lower().replace("-", "_")
        if key.startswith("xdr_"):
            key = "native_" + key[4:]
        if key in _TYPE_ALIASES:
            return _TYPE_ALIASES[key]
        try:
            normalized = np.dtype(key)
        except TypeError as exc:
            raise DDError(f"unsupported type={dtype!r}") from exc
    else:
        normalized = np.dtype(dtype)

    native = normalized.newbyteorder("=")
    if native not in _SUPPORTED_BASE_DTYPES:
        raise DDError(
            "supported dtypes are float32, float64, int32, and complex64"
        )
    return native


def dtype_with_endian(dtype: str | np.dtype[Any], endian: str) -> np.dtype[Any]:
    """Return ``dtype`` with the requested byte order."""

    base = normalize_dtype(dtype)
    normalized = endian.strip().lower()
    if normalized in _BIG_ENDIAN_ALIASES:
        return base.newbyteorder(">")
    if normalized in _NATIVE_ENDIAN_ALIASES:
        return base
    if normalized in _LITTLE_ENDIAN_ALIASES:
        if sys.byteorder != "little":
            raise DDError("little-endian RSF output is only supported on little-endian hosts")
        return base.newbyteorder("<")
    raise DDError("endian= must be one of little, big, xdr, or native")


def _with_input_form(dtype: np.dtype[Any], header: RSFHeader) -> np.dtype[Any]:
    data_format = header.data_format
    if data_format.startswith("xdr_"):
        return dtype.newbyteorder(">")
    return dtype


def _cast_values(
    data: np.ndarray,
    dtype: np.dtype[Any],
    *,
    trunc: bool = False,
) -> np.ndarray:
    array = np.asarray(data)
    target = np.dtype(dtype)

    if target.kind in {"i", "u"}:
        values = np.real(array) if np.iscomplexobj(array) else array
        if np.asarray(values).dtype.kind == "f":
            values = np.trunc(values) if trunc else np.rint(values)
        return np.ascontiguousarray(values.astype(target))

    if target.kind == "f":
        values = np.real(array) if np.iscomplexobj(array) else array
        return np.ascontiguousarray(values.astype(target))

    if target.kind == "c":
        return np.ascontiguousarray(array.astype(target))

    raise DDError(f"unsupported target dtype {target}")

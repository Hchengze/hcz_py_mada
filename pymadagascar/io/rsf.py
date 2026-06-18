"""Read and write Madagascar RSF header/data files.

This module implements the ordinary file-backed RSF layout:
a text header file with key=value parameters and a separate binary data file
referenced by the header's in= parameter. A small ascii_float sidecar subset is
also supported for compatibility.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Iterator, Mapping

import numpy as np

SF_MAX_DIM = 9

_HEADER_TOKEN_RE = re.compile(
    r"""(?P<key>[A-Za-z_][A-Za-z0-9_.:-]*)=(?P<value>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|[^\s]+)"""
)

_FORMAT_TO_DTYPE: dict[str, np.dtype[Any]] = {
    "ascii_float": np.dtype("float32"),
    "native_float": np.dtype("=f4"),
    "native_double": np.dtype("=f8"),
    "native_int": np.dtype("=i4"),
    "native_complex": np.dtype("=c8"),
    "xdr_float": np.dtype(">f4"),
    "xdr_double": np.dtype(">f8"),
    "xdr_int": np.dtype(">i4"),
    "xdr_complex": np.dtype(">c8"),
}

_DTYPE_TO_FORMAT: dict[np.dtype[Any], str] = {
    np.dtype("float32"): "native_float",
    np.dtype("float64"): "native_double",
    np.dtype("int32"): "native_int",
    np.dtype("complex64"): "native_complex",
    np.dtype(">f4"): "xdr_float",
    np.dtype(">f8"): "xdr_double",
    np.dtype(">i4"): "xdr_int",
    np.dtype(">c8"): "xdr_complex",
}

_FORMAT_ESIZE: dict[str, int] = {
    "ascii_float": 0,
    "native_float": 4,
    "native_double": 8,
    "native_int": 4,
    "native_complex": 8,
    "xdr_float": 4,
    "xdr_double": 8,
    "xdr_int": 4,
    "xdr_complex": 8,
}


class RSFError(ValueError):
    """Raised when an RSF file cannot be parsed or read safely."""


class RSFHeader:
    """Ordered RSF header parameter table.

    Values are stored as strings because RSF headers are text key=value tables.
    Typed accessors convert values on demand.
    """

    def __init__(self, values: Mapping[str, Any] | Iterable[tuple[str, Any]] | None = None):
        self.params: OrderedDict[str, str] = OrderedDict()
        if values:
            items = values.items() if isinstance(values, Mapping) else values
            for key, value in items:
                self[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.params

    def __getitem__(self, key: str) -> str:
        return self.params[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.params[str(key)] = _stringify_value(value)

    def __delitem__(self, key: str) -> None:
        del self.params[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.params)

    def __len__(self) -> int:
        return len(self.params)

    def __repr__(self) -> str:
        return f"RSFHeader({dict(self.params)!r})"

    def copy(self) -> "RSFHeader":
        return RSFHeader(self.params.items())

    def get(self, key: str, default: Any = None) -> str | Any:
        return self.params.get(key, default)

    def items(self) -> Iterable[tuple[str, str]]:
        return self.params.items()

    def get_int(self, key: str, default: int | None = None) -> int | None:
        value = self.get(key)
        if value is None:
            return default
        return int(value)

    def get_float(self, key: str, default: float | None = None) -> float | None:
        value = self.get(key)
        if value is None:
            return default
        return float(value)

    def get_string(self, key: str, default: str | None = None) -> str | None:
        value = self.get(key)
        if value is None:
            return default
        return str(value)

    @property
    def data_format(self) -> str:
        value = self.get_string("data_format")
        if value:
            return value
        esize = self.get_int("esize")
        if esize == 0:
            return "ascii_float"
        raise RSFError("RSF header has no data_format= and is not ascii esize=0")

    @property
    def dtype(self) -> np.dtype[Any]:
        return dtype_from_format(self.data_format)

    @property
    def esize(self) -> int:
        if "esize" in self:
            return int(self["esize"])
        if self.data_format == "ascii_float":
            return 0
        return int(self.dtype.itemsize)

    @property
    def dimensions(self) -> tuple[int, ...]:
        highest = 0
        values: list[int] = []
        for axis in range(1, SF_MAX_DIM + 1):
            key = f"n{axis}"
            if key in self:
                highest = axis
                values.append(int(self[key]))
            else:
                values.append(1)
        if highest == 0:
            raise RSFError("RSF header is missing n1=")
        return tuple(values[:highest])

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(reversed(self.dimensions))

    @property
    def sample_count(self) -> int:
        count = 1
        for size in self.dimensions:
            count *= size
        return count

    def axis(self, axis: int) -> dict[str, str | None]:
        if axis < 1 or axis > SF_MAX_DIM:
            raise ValueError(f"axis must be between 1 and {SF_MAX_DIM}")
        return {
            "n": self.get(f"n{axis}"),
            "d": self.get(f"d{axis}"),
            "o": self.get(f"o{axis}"),
            "label": self.get(f"label{axis}"),
            "unit": self.get(f"unit{axis}"),
        }

    def set_dimensions_from_shape(self, shape: tuple[int, ...]) -> None:
        if not shape:
            raise RSFError("RSF data must have at least one dimension")
        if len(shape) > SF_MAX_DIM:
            raise RSFError(f"RSF supports at most {SF_MAX_DIM} dimensions")

        dimensions = tuple(reversed(tuple(int(size) for size in shape)))
        for axis in range(1, SF_MAX_DIM + 1):
            key = f"n{axis}"
            if axis <= len(dimensions):
                self[key] = dimensions[axis - 1]
            elif key in self:
                del self[key]

    def binary_path(self, header_path: str | Path) -> Path:
        dataname = self.get_string("in")
        if not dataname:
            raise RSFError("RSF header is missing in= binary path")
        if dataname in {"stdin", "stdout"}:
            raise RSFError(f"in={dataname!r} is a stream and is not supported by file reader")

        binary = Path(dataname)
        if binary.is_absolute():
            return binary
        return Path(header_path).expanduser().resolve().parent / binary


@dataclass(frozen=True)
class RSFArray:
    """NumPy data and its RSF header."""

    data: np.ndarray
    header: RSFHeader
    header_path: Path | None = None
    binary_path: Path | None = None

    @property
    def shape(self) -> tuple[int, ...]:
        return self.data.shape

    @property
    def dtype(self) -> np.dtype[Any]:
        return self.data.dtype

    def __array__(self, dtype: Any = None) -> np.ndarray:
        return np.asarray(self.data, dtype=dtype)

    def __iter__(self) -> Iterator[Any]:
        yield self.data
        yield self.header


def read_header(path: str | Path) -> RSFHeader:
    """Read an RSF text header."""

    header_path = Path(path).expanduser()
    with header_path.open("r", encoding="utf-8", errors="replace") as stream:
        return _parse_header_text(stream.read())


def write_header(path: str | Path, header: RSFHeader | Mapping[str, Any]) -> None:
    """Write an RSF text header without writing binary data."""

    header_path = Path(path).expanduser()
    header_path.parent.mkdir(parents=True, exist_ok=True)
    rsf_header = _coerce_header(header)
    with header_path.open("w", encoding="utf-8", newline="\n") as stream:
        for key, value in rsf_header.items():
            stream.write(f"\t{key}={_format_header_value(key, value)}\n")


def read_rsf(path: str | Path) -> RSFArray:
    """Read an RSF header and its sidecar array."""

    header_path = Path(path).expanduser()
    header = read_header(header_path)
    data_format = header.data_format
    dtype = header.dtype
    binary_path = header.binary_path(header_path)

    expected = header.sample_count
    if data_format == "ascii_float":
        data = _read_ascii_float(binary_path, expected)
    else:
        data = np.fromfile(binary_path, dtype=dtype, count=expected)
    if data.size != expected:
        raise RSFError(
            f"Data file {binary_path} has {data.size} elements, expected {expected}"
        )

    data = data.reshape(header.shape)
    native_data = np.asarray(data, dtype=_native_dtype(dtype))
    return RSFArray(native_data, header, header_path=header_path.resolve(), binary_path=binary_path)


def write_rsf(
    path: str | Path,
    data: np.ndarray,
    header: RSFHeader | Mapping[str, Any] | None = None,
    *,
    data_format: str | None = None,
) -> RSFArray:
    """Write an RSF header and sidecar data file.

    The generated sidecar path is ``<header name>@`` in the same directory and
    the header stores it as ``./<header name>@``. By default data are written in
    native binary form based on the NumPy dtype. Pass ``data_format="ascii_float"``
    or provide that header data_format to write the small ASCII float subset.
    """

    header_path = Path(path).expanduser()
    header_path.parent.mkdir(parents=True, exist_ok=True)

    array = np.asarray(data)
    rsf_header = _coerce_header(header).copy() if header is not None else RSFHeader()
    output_format = _select_output_format(array, rsf_header, data_format)
    binary_path = header_path.with_name(header_path.name + "@")

    rsf_header.set_dimensions_from_shape(array.shape)
    rsf_header["data_format"] = output_format
    rsf_header["esize"] = _FORMAT_ESIZE[output_format]
    rsf_header["in"] = f"./{binary_path.name}"

    write_header(header_path, rsf_header)
    if output_format == "ascii_float":
        written_array = _write_ascii_float(binary_path, array)
    else:
        written_array = np.ascontiguousarray(array)
        written_array.tofile(binary_path)
    return RSFArray(written_array, rsf_header, header_path=header_path.resolve(), binary_path=binary_path.resolve())


def dtype_from_format(data_format: str) -> np.dtype[Any]:
    """Return the NumPy dtype for a supported RSF data_format value."""

    fmt = _strip_quotes(data_format)
    if fmt in _FORMAT_TO_DTYPE:
        return _FORMAT_TO_DTYPE[fmt]
    if fmt.startswith("xdr_"):
        raise RSFError(f"Unsupported XDR data_format: {fmt}")
    if fmt.startswith("ascii_"):
        raise RSFError(f"ASCII data_format is not supported by read_rsf yet: {fmt}")
    raise RSFError(f"Unsupported RSF data_format: {fmt}")


def format_from_dtype(dtype: np.dtype[Any] | str) -> str:
    """Return the RSF native data_format for a supported NumPy dtype."""

    normalized = np.dtype(dtype)
    if normalized in _DTYPE_TO_FORMAT:
        return _DTYPE_TO_FORMAT[normalized]
    if normalized.byteorder == "<" and sys.byteorder == "little":
        native = normalized.newbyteorder("=")
        if native in _DTYPE_TO_FORMAT:
            return _DTYPE_TO_FORMAT[native]
    if normalized.byteorder == ">" and sys.byteorder == "big":
        native = normalized.newbyteorder("=")
        if native in _DTYPE_TO_FORMAT:
            return _DTYPE_TO_FORMAT[native]
    raise RSFError(
        "Unsupported dtype. Supported dtypes are float32, float64, int32, complex64, "
        "and their XDR big-endian equivalents. Use data_format='ascii_float' "
        "explicitly for ASCII float output."
    )


def _select_output_format(
    array: np.ndarray,
    header: RSFHeader,
    data_format: str | None,
) -> str:
    if data_format is not None:
        requested = _strip_quotes(data_format)
    else:
        requested = _requested_format_from_header(header)

    if requested is None:
        return format_from_dtype(array.dtype)
    if requested == "ascii_float":
        if np.asarray(array).dtype.kind != "f":
            raise RSFError("ascii_float output only supports float32 or float64 input data")
        return requested
    if requested.startswith("ascii_"):
        raise RSFError("Only ascii_float output is supported")
    if requested in _FORMAT_TO_DTYPE:
        return requested
    raise RSFError(f"Unsupported RSF data_format: {requested}")


def _requested_format_from_header(header: RSFHeader) -> str | None:
    header_format = header.get_string("data_format")
    if header_format == "ascii_float":
        return "ascii_float"
    if header_format and header_format.startswith("ascii_"):
        return header_format
    form = header.get_string("form")
    if form and form.strip().lower().startswith("a"):
        return "ascii_float"
    return None


def _read_ascii_float(path: Path, expected: int) -> np.ndarray:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RSFError(f"Cannot read ASCII RSF data file {path}: {exc}") from exc
    data = np.fromstring(text, sep=" ", dtype=np.float32)
    if data.size != expected:
        raise RSFError(f"ASCII file {path} has {data.size} elements, expected {expected}")
    return data


def _write_ascii_float(path: Path, array: np.ndarray) -> np.ndarray:
    if np.asarray(array).dtype.kind != "f":
        raise RSFError("ascii_float output only supports float32 or float64 input data")
    output = np.ascontiguousarray(np.asarray(array, dtype=np.float32))
    flat = output.ravel()
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for start in range(0, flat.size, 8):
            values = " ".join(f"{float(value):.9g}" for value in flat[start : start + 8])
            stream.write(values + "\n")
    return output


def _parse_header_text(text: str) -> RSFHeader:
    header = RSFHeader()
    for match in _HEADER_TOKEN_RE.finditer(text):
        header[match.group("key")] = _strip_quotes(match.group("value"))
    return header


def _coerce_header(header: RSFHeader | Mapping[str, Any]) -> RSFHeader:
    if isinstance(header, RSFHeader):
        return header
    return RSFHeader(header)


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _stringify_value(value: Any) -> str:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _format_header_value(key: str, value: str) -> str:
    if _looks_numeric(value):
        return value
    if "," in value and all(_looks_numeric(part) for part in value.split(",")):
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _looks_numeric(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return bool(value)


def _native_dtype(dtype: np.dtype[Any]) -> np.dtype[Any]:
    if dtype.byteorder in ("=", "|"):
        return dtype
    return dtype.newbyteorder("=")

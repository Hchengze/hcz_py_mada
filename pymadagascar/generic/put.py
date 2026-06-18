"""Copy RSF datasets while updating header parameters."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


class PutHeaderError(ValueError):
    """Raised when a requested header update would make the RSF inconsistent."""


_PROTECTED_KEYS = {"in", "esize", "data_format"}


def put_header(
    path: str | Path,
    updates: Mapping[str, Any],
    output_path: str | Path | None = None,
) -> RSFArray:
    """Copy ``path`` to a new RSF file while applying header updates.

    The original file is never modified. If ``output_path`` is omitted, the
    output path is ``<stem>_put<suffix>`` beside the input header.
    """

    input_path = Path(path).expanduser()
    output = _default_output_path(input_path) if output_path is None else Path(output_path).expanduser()
    if input_path.resolve() == output.resolve():
        raise PutHeaderError("output_path must be different from the input path")

    rsf = read_rsf(input_path)
    header = rsf.header.copy()
    for key, value in updates.items():
        normalized_key = str(key)
        if normalized_key in _PROTECTED_KEYS:
            raise PutHeaderError(f"{normalized_key}= is managed by RSF I/O and cannot be changed by put_header")
        if normalized_key in {"out", "output", "--out"}:
            continue
        header[normalized_key] = value

    _validate_dimensions(header, rsf.data.shape)
    return write_rsf(output, rsf.data, header)


def _default_output_path(path: Path) -> Path:
    suffix = path.suffix or ".rsf"
    stem = path.name[: -len(path.suffix)] if path.suffix else path.name
    return path.with_name(stem + "_put" + suffix)


def _validate_dimensions(header: RSFHeader, data_shape: tuple[int, ...]) -> None:
    expected = tuple(reversed(data_shape))
    try:
        dimensions = header.dimensions
    except Exception as exc:  # noqa: BLE001 - converted to user-facing consistency error
        raise PutHeaderError(f"updated header has invalid dimensions: {exc}") from exc
    if dimensions != expected:
        raise PutHeaderError(
            f"updated n# dimensions {dimensions} do not match binary data shape {expected}"
        )

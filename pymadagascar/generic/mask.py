"""Create integer masks from real-valued RSF datasets."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


class MaskError(ValueError):
    """Raised when a mask operation is invalid."""


def mask_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    min_value: float | None = None,
    max_value: float | None = None,
) -> RSFArray:
    """Write a ``native_int`` 0/1 mask for samples inside ``[min, max]``."""

    rsf = read_rsf(input_path)
    data = np.asarray(rsf.data)
    if np.iscomplexobj(data):
        raise MaskError("mask_rsf only supports real-valued data")

    lower = -np.inf if min_value is None else float(min_value)
    upper = np.inf if max_value is None else float(max_value)
    if lower > upper:
        raise MaskError("min= must be <= max=")

    mask = ((data >= lower) & (data <= upper)).astype(np.int32)
    return write_rsf(output_path, np.ascontiguousarray(mask), rsf.header.copy())

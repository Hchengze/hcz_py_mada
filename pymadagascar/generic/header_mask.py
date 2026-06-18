"""Mask-driven header-style window and cut helpers for RSF datasets."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf
from pymadagascar.seismic._utils import broadcast_axis_values, validate_rsf_axis


class HeaderMaskError(ValueError):
    """Raised when a header/mask RSF selection is invalid."""


def header_window_rsf(
    input_path: str | Path,
    mask_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 2,
    keep_nonzero: bool = True,
) -> RSFArray:
    """Window an RSF dataset along a 1-based axis using a one-dimensional mask."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = validate_rsf_axis(axis, cube.ndim)
    selector = _selection_from_mask(mask_path, axis_size=cube.axis(axis).n, keep_nonzero=keep_nonzero)
    start, count = _continuous_selection(selector)

    np_axis = rsf.data.ndim - axis
    slices: list[slice] = [slice(None)] * rsf.data.ndim
    slices[np_axis] = slice(start, start + count)
    result = np.ascontiguousarray(rsf.data[tuple(slices)])

    old_axis = cube.axis(axis)
    out_cube = cube.update_axis(axis, n=count, o=old_axis.o + start * old_axis.d)
    return write_rsf(output_path, result, out_cube.to_header(rsf.header.copy()))


def header_cut_rsf(
    input_path: str | Path,
    mask_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 2,
    cut_nonzero: bool = True,
) -> RSFArray:
    """Zero samples along a 1-based axis using a one-dimensional mask."""

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    axis = validate_rsf_axis(axis, cube.ndim)
    cut_selector = _selection_from_mask(mask_path, axis_size=cube.axis(axis).n, keep_nonzero=cut_nonzero)
    cut_mask = broadcast_axis_values(cut_selector.astype(bool), axis=axis, ndim=rsf.data.ndim)
    result = np.where(cut_mask, np.zeros((), dtype=rsf.data.dtype), rsf.data)
    return write_rsf(output_path, np.ascontiguousarray(result.astype(rsf.data.dtype)), rsf.header.copy())


def _selection_from_mask(
    mask_path: str | Path,
    *,
    axis_size: int,
    keep_nonzero: bool,
) -> np.ndarray:
    mask = read_rsf(mask_path)
    values = np.asarray(mask.data).reshape(-1)
    if values.size != axis_size:
        raise HeaderMaskError(
            f"mask sample count {values.size} does not match selected axis length {axis_size}"
        )
    nonzero = values != 0
    return nonzero if keep_nonzero else ~nonzero


def _continuous_selection(selector: np.ndarray) -> tuple[int, int]:
    indices = np.flatnonzero(selector)
    if indices.size == 0:
        raise HeaderMaskError("mask selection is empty")
    start = int(indices[0])
    stop = int(indices[-1]) + 1
    if not np.all(selector[start:stop]):
        raise HeaderMaskError("header_window_rsf requires a continuous mask selection")
    return start, stop - start

"""Rotate RSF data cyclically along one or more axes."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, SF_MAX_DIM, read_rsf, write_rsf


class RotateError(ValueError):
    """Raised when a rotate operation is invalid."""


def rotate_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    rotations: Mapping[int, int],
) -> RSFArray:
    """Cyclically rotate samples by Madagascar-style ``rot#`` counts.

    Axis numbers are 1-based RSF axes. A positive ``rot#`` moves the first
    ``rot#`` samples of that axis to the end, matching upstream ``sfrotate``.
    """

    rsf = read_rsf(input_path)
    cube = Hypercube.from_header(rsf.header)
    normalized = _normalize_rotations(rotations, cube)

    result = np.asarray(rsf.data)
    for rsf_axis, shift in normalized.items():
        if shift:
            result = np.roll(result, shift=-shift, axis=cube.ndim - rsf_axis)
    return write_rsf(output_path, np.ascontiguousarray(result), rsf.header.copy())


def _normalize_rotations(rotations: Mapping[int, int], cube: Hypercube) -> dict[int, int]:
    if not rotations:
        return {}

    normalized: dict[int, int] = {}
    for axis, value in rotations.items():
        rsf_axis = int(axis)
        if rsf_axis < 1 or rsf_axis > SF_MAX_DIM:
            raise RotateError(f"rot axis must be between 1 and {SF_MAX_DIM}, got {rsf_axis}")
        if rsf_axis > cube.ndim:
            raise RotateError(f"rot{rsf_axis}= is outside input ndim={cube.ndim}")
        length = cube.axis(rsf_axis).n
        shift = int(value)
        if shift < 0:
            shift += length
        if shift < 0 or shift >= length:
            raise RotateError(
                f"rot{rsf_axis}={value} must be smaller than n{rsf_axis}={length}"
            )
        normalized[rsf_axis] = shift
    return normalized

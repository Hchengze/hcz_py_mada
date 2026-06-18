"""Byte scaling helpers for quicklook RSF workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


class ByteScaleError(ValueError):
    """Raised when byte scaling parameters or input data are invalid."""


def byte_scale(
    data: Any,
    clip: float | None = None,
    pclip: float | None = None,
    bias: float | None = None,
    allpos: bool = False,
) -> np.ndarray:
    """Scale real data to integer byte levels in the inclusive range 0..255.

    The returned dtype is ``int32`` rather than ``uint8`` because the current
    stable RSF writer supports ``native_int`` but not Madagascar ``uchar``.
    Non-finite samples are ignored when estimating limits and are written as 0.
    """

    array = np.asarray(data)
    if np.iscomplexobj(array):
        raise ByteScaleError("byte_scale only supports real-valued data")

    try:
        values = np.asarray(array, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ByteScaleError("byte_scale only supports real numeric data") from exc

    finite_mask = np.isfinite(values)
    finite = values[finite_mask]
    if finite.size == 0:
        raise ByteScaleError("cannot byte-scale data with no finite samples")

    lower, upper = _byte_limits(finite, clip=clip, pclip=pclip, bias=bias, allpos=allpos)
    output = np.zeros(values.shape, dtype=np.int32)
    if upper <= lower:
        return output

    clipped = np.clip(values[finite_mask], lower, upper)
    scaled = (clipped - lower) * (255.0 / (upper - lower))
    output[finite_mask] = np.rint(scaled).astype(np.int32)
    return output


def byte_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    clip: float | None = None,
    pclip: float | None = None,
    bias: float | None = None,
    allpos: bool = False,
) -> RSFArray:
    """Read an RSF file, byte-scale its data, and write a ``native_int`` RSF."""

    rsf = read_rsf(input_path)
    scaled = byte_scale(rsf.data, clip=clip, pclip=pclip, bias=bias, allpos=allpos)
    return write_rsf(output_path, np.ascontiguousarray(scaled), rsf.header.copy())


def _byte_limits(
    finite: np.ndarray,
    *,
    clip: float | None,
    pclip: float | None,
    bias: float | None,
    allpos: bool,
) -> tuple[float, float]:
    center = _coerce_bias(bias)
    if allpos:
        origin = 0.0 if center is None else center
        if clip is not None:
            return origin, origin + _coerce_clip(clip)
        if pclip is not None:
            upper = _positive_percentile(finite - origin, pclip)
            return origin, origin + upper
        return origin, float(np.max(finite))

    if clip is not None:
        midpoint = 0.0 if center is None else center
        width = _coerce_clip(clip)
        return midpoint - width, midpoint + width

    if pclip is not None:
        midpoint = 0.0 if center is None else center
        width = _absolute_percentile(finite - midpoint, pclip)
        return midpoint - width, midpoint + width

    if center is not None:
        width = float(np.max(np.abs(finite - center)))
        return center - width, center + width

    return float(np.min(finite)), float(np.max(finite))


def _coerce_clip(value: float) -> float:
    clip = float(value)
    if not np.isfinite(clip) or clip <= 0.0:
        raise ByteScaleError("clip= must be a positive finite value")
    return clip


def _coerce_bias(value: float | None) -> float | None:
    if value is None:
        return None
    bias = float(value)
    if not np.isfinite(bias):
        raise ByteScaleError("bias= must be finite")
    return bias


def _coerce_pclip(value: float) -> float:
    pclip = float(value)
    if not np.isfinite(pclip) or pclip <= 0.0 or pclip > 100.0:
        raise ByteScaleError("pclip= must be > 0 and <= 100")
    return pclip


def _absolute_percentile(values: np.ndarray, pclip: float) -> float:
    return float(np.percentile(np.abs(values), _coerce_pclip(pclip)))


def _positive_percentile(values: np.ndarray, pclip: float) -> float:
    positive = values[values > 0.0]
    if positive.size == 0:
        return 0.0
    return float(np.percentile(positive, _coerce_pclip(pclip)))

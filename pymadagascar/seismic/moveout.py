"""Spike traces from arbitrary moveout-time tables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


class MoveoutError(ValueError):
    """Raised when moveout spike-generation parameters are invalid."""


def moveout_spikes(
    times: Any,
    *,
    n1: int,
    o1: float = 0.0,
    d1: float = 1.0,
    eps: float = 0.1,
    nw: int = 10,
    interpolation: str = "linear",
) -> np.ndarray:
    """Place unit spikes at moveout times, adding an RSF axis-1 time dimension."""

    move = np.asarray(times)
    if move.ndim < 1:
        raise MoveoutError("moveout requires at least one moveout time sample")
    if np.iscomplexobj(move) or not np.issubdtype(move.dtype, np.number):
        raise MoveoutError("moveout times must be real numeric values")
    if not np.all(np.isfinite(move)):
        raise MoveoutError("moveout times must be finite")
    nt = int(n1)
    if nt <= 0:
        raise MoveoutError("n1= must be positive")
    origin = float(o1)
    sampling = float(d1)
    if not np.isfinite(origin):
        raise MoveoutError("o1= must be finite")
    if not np.isfinite(sampling) or sampling <= 0.0:
        raise MoveoutError("d1= must be positive")
    eps_value = float(eps)
    if not np.isfinite(eps_value) or eps_value < 0.0:
        raise MoveoutError("eps= must be non-negative")
    width = int(nw)
    if width < 0:
        raise MoveoutError("nw= must be non-negative")
    method = str(interpolation).lower()
    if method not in {"linear", "nearest"}:
        raise MoveoutError("interpolation= must be 'linear' or 'nearest'")

    flat = move.astype(np.float64, copy=False).reshape(-1)
    out = np.zeros((flat.size, nt), dtype=np.float32)
    sample = (flat - origin) / sampling
    if method == "nearest":
        indices = np.rint(sample).astype(np.int64)
        live = (indices >= 0) & (indices < nt)
        out[np.nonzero(live)[0], indices[live]] = 1.0
    else:
        left = np.floor(sample).astype(np.int64)
        frac = sample - left
        live_left = (left >= 0) & (left < nt)
        out[np.nonzero(live_left)[0], left[live_left]] += (1.0 - frac[live_left]).astype(np.float32)
        right = left + 1
        live_right = (right >= 0) & (right < nt)
        out[np.nonzero(live_right)[0], right[live_right]] += frac[live_right].astype(np.float32)
    return np.ascontiguousarray(out.reshape(move.shape + (nt,)))


def moveout_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    n1: int,
    o1: float = 0.0,
    d1: float = 1.0,
    eps: float = 0.1,
    nw: int = 10,
    interpolation: str = "linear",
) -> RSFArray:
    """Apply the bounded ``sfmoveout`` subset to RSF files."""

    rsf = read_rsf(input_path)
    result = moveout_spikes(
        rsf.data,
        n1=n1,
        o1=o1,
        d1=d1,
        eps=eps,
        nw=nw,
        interpolation=interpolation,
    )
    header = _shifted_header(rsf.header, n1=int(n1), o1=float(o1), d1=float(d1))
    header["moveout_eps"] = float(eps)
    header["moveout_nw"] = int(nw)
    header["moveout_interpolation"] = interpolation
    header["moveout_source"] = "../src-master/system/seismic/Mmoveout.c"
    header["moveout_subset"] = "unit-spikes-from-moveout-times"
    return write_rsf(output_path, result, header)


def _shifted_header(input_header: RSFHeader, *, n1: int, o1: float, d1: float) -> RSFHeader:
    input_dims = input_header.dimensions
    header = RSFHeader(
        {
            "n1": n1,
            "o1": o1,
            "d1": d1,
            "label1": "Time",
            "unit1": "s",
        }
    )
    for axis, size in enumerate(input_dims, start=1):
        out_axis = axis + 1
        header[f"n{out_axis}"] = size
        for key in ("o", "d", "label", "unit"):
            value = input_header.get(f"{key}{axis}")
            if value is not None:
                header[f"{key}{out_axis}"] = value
    return header


__all__ = ["MoveoutError", "moveout_rsf", "moveout_spikes"]

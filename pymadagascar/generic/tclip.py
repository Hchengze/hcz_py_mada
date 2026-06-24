"""Threshold clipping aligned with ``system/generic/Mtclip.c``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


class TClipError(ValueError):
    """Raised when a threshold-clipping request is invalid."""


def tclip(
    data: Any,
    *,
    lowercut: float = 0.2,
    uppercut: float = 0.8,
) -> np.ndarray:
    """Apply the bounded ``sftclip`` lower/upper threshold transform."""

    # 对齐 ../src-master/system/generic/Mtclip.c：
    # 本 bounded subset 只处理实数数组，低于 lowercut 的样点置 0，
    # 高于 uppercut 的样点置 1，中间样点保持原值；不扩展额外滤波语义。
    lower = float(lowercut)
    upper = float(uppercut)
    if lower > upper:
        raise TClipError("lowercut must be <= uppercut")
    array = _real_array(data)
    result = array.copy()
    result[result < lower] = 0.0
    result[result > upper] = 1.0
    return np.ascontiguousarray(result)


def tclip_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    lowercut: float = 0.2,
    uppercut: float = 0.8,
) -> RSFArray:
    """Apply bounded ``sftclip`` threshold clipping to an RSF file."""

    rsf = read_rsf(input_path)
    result = tclip(rsf.data, lowercut=lowercut, uppercut=uppercut)
    header = rsf.header.copy()
    # 输出保持输入 RSF shape/header，只增加 source/subset 相关 provenance；
    # 这样 RSFData chain 的 no-inplace 行为可由外层包装统一保证。
    header["tclip_source"] = "../src-master/system/generic/Mtclip.c"
    header["tclip_lowercut"] = float(lowercut)
    header["tclip_uppercut"] = float(uppercut)
    return write_rsf(output_path, result, header)


def _real_array(data: Any) -> np.ndarray:
    array = np.asarray(data)
    if np.iscomplexobj(array):
        raise TClipError("tclip requires real-valued input")
    if not np.issubdtype(array.dtype, np.number):
        raise TClipError("tclip requires numeric input")
    dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    return np.asarray(array, dtype=dtype)


__all__ = ["TClipError", "tclip", "tclip_rsf"]

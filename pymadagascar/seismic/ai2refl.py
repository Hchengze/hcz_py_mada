"""Acoustic impedance to reflectivity conversion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf
from pymadagascar.seismic._utils import numpy_axis, validate_rsf_axis


class AI2ReflError(ValueError):
    """Raised when an acoustic-impedance conversion request is invalid."""


def ai2refl(data: Any, *, axis: int = 1, eps: float | None = None) -> np.ndarray:
    """Convert acoustic impedance to reflection coefficients along one RSF axis."""

    array = _real_array(data, name="data")
    if array.ndim < 1:
        raise AI2ReflError("ai2refl requires at least one dimension")
    axis = validate_rsf_axis(axis, array.ndim)
    np_axis = numpy_axis(axis, array.ndim)
    if array.shape[np_axis] < 1:
        raise AI2ReflError("ai2refl requires a non-empty axis")
    epsilon = np.finfo(np.float32).eps if eps is None else float(eps)
    if epsilon < 0.0:
        raise AI2ReflError("eps= must be non-negative")

    # RSF axis 是 1-based；NumPy shape 与 RSF 轴顺序相反。
    # 先把用户指定的 RSF axis 移到最后一维，后续公式就能逐 trace
    # 沿相邻样点计算 r=(a2-a1)/(a2+a1+eps)。
    moved = np.moveaxis(array.astype(np.float64, copy=False), np_axis, -1)
    out = np.zeros_like(moved, dtype=np.float64)
    if moved.shape[-1] > 1:
        imp1 = moved[..., :-1]
        imp2 = moved[..., 1:]
        out[..., :-1] = (imp2 - imp1) / (imp2 + imp1 + epsilon)
    result = np.moveaxis(out, -1, np_axis)
    dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    return np.ascontiguousarray(result.astype(dtype, copy=False))


def ai2refl_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
    eps: float | None = None,
) -> RSFArray:
    """Apply the bounded ``sfai2refl`` subset to RSF files."""

    rsf = read_rsf(input_path)
    result = ai2refl(rsf.data, axis=axis, eps=eps)
    header = rsf.header.copy()
    # 与 ../src-master/system/seismic/Mai2refl.c 对齐的 bounded subset：
    # 保持输入网格 shape，只记录沿哪个 RSF axis 做 AI -> reflectivity。
    header["ai2refl_axis"] = axis
    header["ai2refl_source"] = "../src-master/system/seismic/Mai2refl.c"
    return write_rsf(output_path, result, header)


def refl2ai(data: Any, a0: Any, *, axis: int = 1) -> np.ndarray:
    """Convert reflection coefficients to acoustic impedance along one RSF axis."""

    array = _real_array(data, name="data")
    if array.ndim < 1:
        raise AI2ReflError("refl2ai requires at least one dimension")
    axis = validate_rsf_axis(axis, array.ndim)
    np_axis = numpy_axis(axis, array.ndim)
    if array.shape[np_axis] < 1:
        raise AI2ReflError("refl2ai requires a non-empty axis")

    # 对齐 ../src-master/system/seismic/Mrefl2ai.c：
    # a0 是每条 trace 的初始 acoustic impedance；反射系数沿指定 RSF axis
    # 递推更新 current *= (1+r)/(1-r)。这里不解释 SEG-Y headers 或地层模型。
    moved = np.moveaxis(array.astype(np.float64, copy=False), np_axis, -1)
    trace_shape = moved.shape[:-1]
    initial = _broadcast_initial_impedance(a0, trace_shape)
    out = np.empty_like(moved, dtype=np.float64)
    current = initial.astype(np.float64, copy=True)
    for sample in range(moved.shape[-1]):
        out[..., sample] = current
        refl = moved[..., sample]
        if np.any(refl == 1.0):
            raise AI2ReflError("refl2ai cannot update impedance where reflectivity is 1")
        current *= (1.0 + refl) / (1.0 - refl)
    result = np.moveaxis(out, -1, np_axis)
    dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    return np.ascontiguousarray(result.astype(dtype, copy=False))


def refl2ai_rsf(
    input_path: str | Path,
    a0_path: str | Path,
    output_path: str | Path,
    *,
    axis: int = 1,
) -> RSFArray:
    """Apply the bounded ``sfrefl2ai`` subset to RSF files."""

    rsf = read_rsf(input_path)
    a0_rsf = read_rsf(a0_path)
    # a0 是 side input，可为标量或每条 trace 一个初值；输出仍使用输入
    # reflectivity 的 RSF header/shape，只增加 source provenance。
    result = refl2ai(rsf.data, a0_rsf.data, axis=axis)
    header = rsf.header.copy()
    header["refl2ai_axis"] = axis
    header["refl2ai_source"] = "../src-master/system/seismic/Mrefl2ai.c"
    return write_rsf(output_path, result, header)


def _broadcast_initial_impedance(a0: Any, trace_shape: tuple[int, ...]) -> np.ndarray:
    initial = _real_array(a0, name="a0")
    trace_count = int(np.prod(trace_shape, dtype=np.int64))
    # trace_shape 是把递推 axis 移到最后以后剩余的所有 trace 维度；
    # NumPy 广播只接受“一个全局 a0”或“每条 trace 一个 a0”。
    if initial.size == 1:
        return np.full(trace_shape, float(initial.reshape(-1)[0]), dtype=np.float64)
    if initial.shape == trace_shape:
        return initial.astype(np.float64, copy=False)
    if initial.size == trace_count:
        return initial.reshape(trace_shape).astype(np.float64, copy=False)
    raise AI2ReflError("a0 must be scalar or contain one initial impedance per trace")


def _real_array(data: Any, *, name: str) -> np.ndarray:
    array = np.asarray(data)
    if np.iscomplexobj(array):
        raise AI2ReflError(f"{name} must be real-valued")
    if not np.issubdtype(array.dtype, np.number):
        raise AI2ReflError(f"{name} must be numeric")
    dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    return np.asarray(array, dtype=dtype)


__all__ = ["AI2ReflError", "ai2refl", "ai2refl_rsf", "refl2ai", "refl2ai_rsf"]

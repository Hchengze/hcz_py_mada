"""Trace/plane interleaving subset aligned with ``system/generic/Mlpad.c``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


class LPadError(ValueError):
    """Raised when an ``sflpad`` request is invalid."""


@dataclass(frozen=True)
class LPadResult:
    """Result arrays for bounded ``sflpad`` trace/plane interleaving."""

    data: np.ndarray
    mask: np.ndarray


def lpad(data: Any, *, jump: int = 2) -> LPadResult:
    """Interleave traces and planes with zeros following ``Mlpad.c``."""

    jump_value = int(jump)
    if jump_value < 1:
        raise LPadError("jump must be >= 1")
    array = _real_array(data)
    ndim = array.ndim
    if ndim < 2:
        raise LPadError("lpad requires at least two RSF axes")

    # 对齐 ../src-master/system/generic/Mlpad.c：
    # upstream 在 RSF axis2 上插入 zero traces，并在存在 axis3 时插入 zero planes。
    # NumPy shape 与 RSF 轴顺序相反，因此先反转成 [n1,n2,n3,...] 再更新长度。
    rsf_dims = list(reversed(array.shape))
    if rsf_dims[1] > 1:
        rsf_dims[1] *= jump_value
    if ndim >= 3 and rsf_dims[2] > 1:
        rsf_dims[2] *= jump_value
    output_shape = tuple(reversed(rsf_dims))

    output = np.zeros(output_shape, dtype=array.dtype)
    mask = np.zeros(output_shape, dtype=np.int32)
    # target 表示原始样点在放大后网格中的位置；mask side output 用 1 标出
    # 被保留的原始 trace/plane，0 表示插入的空 trace/plane。
    target = tuple(
        slice(None, None, jump_value) if _should_interleave_numpy_axis(axis, array.shape) else slice(None)
        for axis in range(ndim)
    )
    output[target] = array
    mask[target] = 1
    return LPadResult(data=np.ascontiguousarray(output), mask=np.ascontiguousarray(mask))


def lpad_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    jump: int = 2,
    mask: str | Path | None = None,
) -> RSFArray:
    """Apply bounded ``sflpad`` to an RSF file and optionally write a mask."""

    rsf = read_rsf(input_path)
    result = lpad(rsf.data, jump=jump)
    output_header = _lpad_header(rsf.header, result.data.shape, jump=int(jump))
    # bounded subset 保持 in-memory 数组语义；不声明 upstream streaming/pipe 行为。
    output_header["lpad_source"] = "../src-master/system/generic/Mlpad.c"
    output_header["lpad_jump"] = int(jump)
    written = write_rsf(output_path, result.data.astype(rsf.data.dtype, copy=False), output_header)
    if mask is not None:
        mask_header = _lpad_header(rsf.header, result.mask.shape, jump=int(jump))
        mask_header["lpad_source"] = "../src-master/system/generic/Mlpad.c"
        mask_header["lpad_jump"] = int(jump)
        write_rsf(mask, result.mask, mask_header)
    return written


def _lpad_header(header: Any, shape: tuple[int, ...], *, jump: int) -> Any:
    output_header = header.copy()
    cube = Hypercube.from_header(output_header)
    output_header.set_dimensions_from_shape(shape)
    ndim = len(shape)
    # 插值式 lpad 不是改变物理范围，而是在 axis2/axis3 之间补零；
    # 因此 n2/n3 变大，d2/d3 按 jump 缩小，o2/o3 保持输入 origin。
    if cube.ndim >= 2 and cube.axis(2).n > 1:
        axis = cube.axis(2)
        output_header["d2"] = axis.d / jump
    if ndim >= 3 and cube.ndim >= 3 and cube.axis(3).n > 1:
        axis = cube.axis(3)
        output_header["d3"] = axis.d / jump
    return output_header


def _should_interleave_numpy_axis(axis: int, shape: tuple[int, ...]) -> bool:
    rsf_axis = len(shape) - axis
    if rsf_axis not in {2, 3}:
        return False
    return shape[axis] > 1


def _real_array(data: Any) -> np.ndarray:
    array = np.asarray(data)
    if np.iscomplexobj(array):
        raise LPadError("lpad requires real-valued input")
    if not np.issubdtype(array.dtype, np.number):
        raise LPadError("lpad requires numeric input")
    return np.ascontiguousarray(array)


__all__ = ["LPadError", "LPadResult", "lpad", "lpad_rsf"]

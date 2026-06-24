"""Smooth Sobel-gradient subsets aligned with ``system/generic/Mgrad*.c``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.io.rsf import RSFArray, read_rsf, write_rsf


class EdgeError(ValueError):
    """Raised when a smooth-gradient request is invalid."""


def grad2(data: Any) -> np.ndarray:
    """Return the ``sfgrad2`` 2-D Sobel gradient-squared subset."""

    array = _real_array(data)
    if array.ndim < 2:
        raise EdgeError("grad2 requires at least two axes")
    result = np.zeros_like(array)
    # 对齐 ../src-master/system/generic/Mgrad2.c；
    # Sobel stencil 来自 ../src-master/api/c/edge.c 的 sf_sobel2。
    # RSF n1/n2 平面在 NumPy 中对应最后两维 shape=(..., n2, n1)。
    slices = int(np.prod(array.shape[:-2], dtype=np.int64))
    reshaped = array.reshape((slices, *array.shape[-2:]))
    out = result.reshape((slices, *array.shape[-2:]))
    for index in range(slices):
        _sobel2_inplace(reshaped[index], out[index])
    return np.ascontiguousarray(result)


def grad3(data: Any, *, dim: int = 0) -> np.ndarray:
    """Return the ``sfgrad3`` 3-D Sobel component or gradient-squared subset."""

    dim_value = int(dim)
    if dim_value not in {0, 1, 2, 3}:
        raise EdgeError("grad3 dim must be 0, 1, 2, or 3")
    array = _real_array(data)
    if array.ndim < 3:
        raise EdgeError("grad3 requires at least three axes")
    result = np.zeros_like(array)
    # 对齐 ../src-master/system/generic/Mgrad3.c 和 api/c/edge.c：
    # 每个 RSF n1/n2/n3 block 在 NumPy 中是最后三维 shape=(..., n3, n2, n1)。
    # dim=0 输出梯度平方；dim=1/2/3 输出固定 Sobel component。
    slices = int(np.prod(array.shape[:-3], dtype=np.int64))
    reshaped = array.reshape((slices, *array.shape[-3:]))
    out = result.reshape((slices, *array.shape[-3:]))
    for index in range(slices):
        _sobel3_inplace(reshaped[index], out[index], dim=dim_value)
    return np.ascontiguousarray(result)


def grad2_rsf(input_path: str | Path, output_path: str | Path) -> RSFArray:
    """Apply bounded ``sfgrad2`` Sobel gradient squared to an RSF file."""

    rsf = read_rsf(input_path)
    result = grad2(rsf.data)
    header = rsf.header.copy()
    # helper-level source mapping 必须写入 header，避免只记录 Mgrad2.c
    # 而丢失真正定义 Sobel stencil 的 edge.c。
    header["grad2_source"] = "../src-master/system/generic/Mgrad2.c"
    header["grad2_edge_source"] = "../src-master/api/c/edge.c"
    return write_rsf(output_path, result.astype(rsf.data.dtype, copy=False), header)


def grad3_rsf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    dim: int = 0,
) -> RSFArray:
    """Apply bounded ``sfgrad3`` Sobel component or gradient squared to RSF."""

    rsf = read_rsf(input_path)
    result = grad3(rsf.data, dim=dim)
    header = rsf.header.copy()
    # 本 subset 不做 physical-spacing normalization，也不引入替代边界条件；
    # 边界样点保持 upstream Sobel helper 的 zero-edge 行为。
    header["grad3_source"] = "../src-master/system/generic/Mgrad3.c"
    header["grad3_edge_source"] = "../src-master/api/c/edge.c"
    header["grad3_dim"] = int(dim)
    return write_rsf(output_path, result.astype(rsf.data.dtype, copy=False), header)


def _real_array(data: Any) -> np.ndarray:
    array = np.asarray(data)
    if np.iscomplexobj(array):
        raise EdgeError("grad requires real-valued input")
    if not np.issubdtype(array.dtype, np.number):
        raise EdgeError("grad requires numeric input")
    dtype = np.float64 if array.dtype == np.dtype("float64") else np.float32
    return np.ascontiguousarray(array, dtype=dtype)


def _sobel2_inplace(array: np.ndarray, out: np.ndarray) -> None:
    if array.shape[-2] < 3 or array.shape[-1] < 3:
        return
    # 这里的下标顺序对应 C helper 中 x[i2][i1]：
    # NumPy 倒数第二维是 RSF axis2，倒数第一维是 RSF axis1。
    w1 = (
        array[2:, 2:]
        - array[2:, :-2]
        + 2.0 * (array[1:-1, 2:] - array[1:-1, :-2])
        + array[:-2, 2:]
        - array[:-2, :-2]
    )
    w2 = (
        array[2:, 2:]
        - array[:-2, 2:]
        + 2.0 * (array[2:, 1:-1] - array[:-2, 1:-1])
        + array[2:, :-2]
        - array[:-2, :-2]
    )
    out[1:-1, 1:-1] = w1 * w1 + w2 * w2


def _sobel3_components(array: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    c = array
    # 3-D stencil 逐项翻译自 api/c/edge.c 的 sf_sobel3/sf_sobel32。
    # 这些权重不是普通中心差分，不能用 np.gradient 之类 convenience 替代计数。
    w1 = (
        c[:-2, :-2, 2:]
        - c[:-2, :-2, :-2]
        + c[2:, :-2, 2:]
        - c[2:, :-2, :-2]
        + c[:-2, 2:, 2:]
        - c[:-2, 2:, :-2]
        + c[2:, 2:, 2:]
        - c[2:, 2:, :-2]
        + 4.0
        * (
            c[:-2, 1:-1, 2:]
            - c[:-2, 1:-1, :-2]
            + c[2:, 1:-1, 2:]
            - c[2:, 1:-1, :-2]
            + c[1:-1, :-2, 2:]
            - c[1:-1, :-2, :-2]
            + c[1:-1, 2:, 2:]
            - c[1:-1, 2:, :-2]
            + c[1:-1, 1:-1, 2:]
            - c[1:-1, 1:-1, :-2]
        )
    )
    w2 = (
        c[:-2, 2:, :-2]
        - c[:-2, :-2, :-2]
        + c[2:, 2:, :-2]
        - c[2:, :-2, :-2]
        + c[:-2, 2:, 2:]
        - c[:-2, :-2, 2:]
        + c[2:, 2:, 2:]
        - c[2:, :-2, 2:]
        + 4.0
        * (
            c[:-2, 2:, 1:-1]
            - c[:-2, :-2, 1:-1]
            + c[2:, 2:, 1:-1]
            - c[2:, :-2, 1:-1]
            + c[1:-1, 2:, :-2]
            - c[1:-1, :-2, :-2]
            + c[1:-1, 2:, 2:]
            - c[1:-1, :-2, 2:]
            + c[1:-1, 2:, 1:-1]
            - c[1:-1, :-2, 1:-1]
        )
    )
    w3 = (
        c[2:, :-2, :-2]
        - c[:-2, :-2, :-2]
        + c[2:, 2:, :-2]
        - c[:-2, 2:, :-2]
        + c[2:, :-2, 2:]
        - c[:-2, :-2, 2:]
        + c[2:, 2:, 2:]
        - c[:-2, 2:, 2:]
        + 4.0
        * (
            c[2:, :-2, 1:-1]
            - c[:-2, :-2, 1:-1]
            + c[2:, 2:, 1:-1]
            - c[:-2, 2:, 1:-1]
            + c[2:, 1:-1, :-2]
            - c[:-2, 1:-1, :-2]
            + c[2:, 1:-1, 2:]
            - c[:-2, 1:-1, 2:]
            + c[2:, 1:-1, 1:-1]
            - c[:-2, 1:-1, 1:-1]
        )
    )
    return w1, w2, w3


def _sobel3_inplace(array: np.ndarray, out: np.ndarray, *, dim: int) -> None:
    if min(array.shape[-3:]) < 3:
        return
    w1, w2, w3 = _sobel3_components(array)
    if dim == 0:
        out[1:-1, 1:-1, 1:-1] = (w1 * w1 + w2 * w2 + w3 * w3) / 36.0
    elif dim == 1:
        out[1:-1, 1:-1, 1:-1] = w1 / 6.0
    elif dim == 2:
        out[1:-1, 1:-1, 1:-1] = w2 / 6.0
    else:
        out[1:-1, 1:-1, 1:-1] = w3 / 6.0


__all__ = ["EdgeError", "grad2", "grad2_rsf", "grad3", "grad3_rsf"]

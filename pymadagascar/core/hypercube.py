"""RSF hypercube metadata model."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import reduce
from operator import mul
from typing import Any

from pymadagascar.core.axis import Axis
from pymadagascar.io.rsf import RSFHeader, SF_MAX_DIM


@dataclass(frozen=True)
class Hypercube:
    """Regularly sampled multidimensional RSF metadata.

    Axes are stored in RSF order: axis 1 is n1/o1/d1 and is the fastest
    varying RSF data axis. ``shape`` therefore returns ``(n1, n2, ...)``.
    Use ``numpy_shape`` for the NumPy storage shape ``(..., n2, n1)``.
    """

    axes: tuple[Axis, ...]

    def __init__(self, axes: Sequence[Axis]):
        if not axes:
            raise ValueError("Hypercube requires at least one axis")
        if len(axes) > SF_MAX_DIM:
            raise ValueError(f"RSF supports at most {SF_MAX_DIM} axes")
        normalized = tuple(axis.copy(index=i + 1) for i, axis in enumerate(axes))
        object.__setattr__(self, "axes", normalized)

    @property
    def ndim(self) -> int:
        return len(self.axes)

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(axis.n for axis in self.axes)

    @property
    def numpy_shape(self) -> tuple[int, ...]:
        return tuple(reversed(self.shape))

    @property
    def size(self) -> int:
        return reduce(mul, self.shape, 1)

    def leftsize(self, axis: int) -> int:
        """Return product of dimensions after ``axis``.

        This mirrors Madagascar's ``sf_leftsize(file, dim)`` convention:
        ``axis=0`` returns the whole cube size, ``axis=1`` returns
        ``n2*n3*...``, and ``axis=ndim`` returns 1.
        """

        if axis < 0 or axis > self.ndim:
            raise ValueError(f"axis must be between 0 and {self.ndim}")
        return reduce(mul, (a.n for a in self.axes[axis:]), 1)

    def axis(self, i: int) -> Axis:
        """Return a 1-based RSF axis."""

        return self.axes[_axis_to_offset(i, self.ndim)]

    def update_axis(self, i: int, **updates: object) -> "Hypercube":
        """Return a copy with one axis updated."""

        offset = _axis_to_offset(i, self.ndim)
        axes = list(self.axes)
        axes[offset] = axes[offset].copy(**updates)
        return Hypercube(axes)

    def transpose(self, order: Sequence[int]) -> "Hypercube":
        """Return a hypercube with axes reordered.

        ``order`` may be either a complete 1-based RSF permutation, such as
        ``[2, 1, 3]``, or a complete 0-based Python permutation, such as
        ``[1, 0, 2]``.
        """

        offsets = _normalize_order(order, self.ndim)
        return Hypercube([self.axes[offset] for offset in offsets])

    def window(self, axis: int, start: int, count: int, stride: int = 1) -> "Hypercube":
        """Return metadata for a sampled window along one axis.

        ``start`` is zero-based sample index, matching Madagascar's ``f#``.
        """

        if start < 0:
            raise ValueError("window start must be >= 0")
        if count < 1:
            raise ValueError("window count must be >= 1")
        if stride < 1:
            raise ValueError("window stride must be >= 1")

        current = self.axis(axis)
        stop = start + (count - 1) * stride
        if stop >= current.n:
            raise ValueError(
                f"window exceeds axis {axis}: start={start}, count={count}, stride={stride}, n={current.n}"
            )

        return self.update_axis(
            axis,
            n=count,
            o=current.o + start * current.d,
            d=current.d * stride,
        )

    def to_header(self, base: RSFHeader | Mapping[str, Any] | None = None) -> RSFHeader:
        """Convert hypercube axes to RSF header fields."""

        header = base.copy() if isinstance(base, RSFHeader) else RSFHeader(base)
        for i, axis in enumerate(self.axes, start=1):
            header[f"n{i}"] = axis.n
            header[f"o{i}"] = axis.o
            header[f"d{i}"] = axis.d
            if axis.label is not None:
                header[f"label{i}"] = axis.label
            elif f"label{i}" in header:
                del header[f"label{i}"]
            if axis.unit is not None:
                header[f"unit{i}"] = axis.unit
            elif f"unit{i}" in header:
                del header[f"unit{i}"]

        for i in range(self.ndim + 1, SF_MAX_DIM + 1):
            for prefix in ("n", "o", "d", "label", "unit"):
                key = f"{prefix}{i}"
                if key in header:
                    del header[key]
        return header

    @classmethod
    def from_header(cls, header: RSFHeader | Mapping[str, Any]) -> "Hypercube":
        """Create a hypercube from RSF n#/o#/d#/label#/unit# fields."""

        rsf_header = header if isinstance(header, RSFHeader) else RSFHeader(header)
        axes: list[Axis] = []
        for i, n in enumerate(rsf_header.dimensions, start=1):
            axes.append(
                Axis(
                    n=n,
                    o=float(rsf_header.get(f"o{i}", 0.0)),
                    d=float(rsf_header.get(f"d{i}", 1.0)),
                    label=rsf_header.get(f"label{i}"),
                    unit=rsf_header.get(f"unit{i}"),
                    index=i,
                )
            )
        return cls(axes)


def _axis_to_offset(axis: int, ndim: int) -> int:
    if axis < 1 or axis > ndim:
        raise ValueError(f"axis must be between 1 and {ndim}")
    return axis - 1


def _normalize_order(order: Sequence[int], ndim: int) -> list[int]:
    values = list(order)
    if len(values) != ndim:
        raise ValueError(f"transpose order must contain {ndim} axes")

    one_based = set(range(1, ndim + 1))
    zero_based = set(range(ndim))
    value_set = set(values)
    if value_set == one_based:
        return [value - 1 for value in values]
    if value_set == zero_based:
        return values
    raise ValueError(
        f"transpose order must be a 1-based or 0-based permutation for {ndim} axes"
    )


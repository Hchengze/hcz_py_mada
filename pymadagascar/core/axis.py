"""Axis metadata for regularly sampled RSF datasets."""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np


@dataclass(frozen=True)
class Axis:
    """One RSF axis, corresponding to n#, o#, d#, label#, and unit#."""

    n: int
    o: float = 0.0
    d: float = 1.0
    label: str | None = None
    unit: str | None = None
    index: int = 1

    def __post_init__(self) -> None:
        if self.n < 1:
            raise ValueError("Axis n must be >= 1")
        if self.index < 1:
            raise ValueError("Axis index must be >= 1")

    def coordinates(self) -> np.ndarray:
        """Return physical coordinates for all samples on this axis."""

        return self.o + self.d * np.arange(self.n, dtype=np.float64)

    def copy(self, **updates: object) -> "Axis":
        """Return a copy, optionally replacing selected fields."""

        return replace(self, **updates)


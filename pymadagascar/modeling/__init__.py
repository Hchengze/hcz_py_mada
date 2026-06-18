"""Prototype seismic forward-modeling algorithms."""

from .acoustic2d import (
    Acoustic2DError,
    absorbing_boundary_simple,
    acoustic2d_forward,
    ricker_wavelet,
)

__all__ = [
    "Acoustic2DError",
    "absorbing_boundary_simple",
    "acoustic2d_forward",
    "ricker_wavelet",
]


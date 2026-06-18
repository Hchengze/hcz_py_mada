"""Optional C++ accelerated kernels with NumPy fallback."""

from .array_ops import (
    add_arrays_cpp,
    backend_name,
    cpp_available,
    last_backend,
    scale_array_cpp,
)
from .xcorr import batch_xcorr_cpp, last_xcorr_backend, xcorr_backend_name

__all__ = [
    "add_arrays_cpp",
    "batch_xcorr_cpp",
    "backend_name",
    "cpp_available",
    "last_backend",
    "last_xcorr_backend",
    "scale_array_cpp",
    "xcorr_backend_name",
]

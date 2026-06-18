"""RSF input/output helpers."""

from .rsf import RSFArray, RSFHeader, read_header, read_rsf, write_header, write_rsf
from .segy import (
    SegyError,
    SegyHeaders,
    extract_trace_header_table,
    read_segy_headers,
    rsf_to_segy,
    segy_to_rsf,
)

__all__ = [
    "RSFArray",
    "RSFHeader",
    "SegyError",
    "SegyHeaders",
    "extract_trace_header_table",
    "read_header",
    "read_rsf",
    "read_segy_headers",
    "rsf_to_segy",
    "segy_to_rsf",
    "write_header",
    "write_rsf",
]

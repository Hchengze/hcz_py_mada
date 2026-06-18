"""Comparison helpers for RSF migration tests."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from pymadagascar.io.rsf import RSFHeader, read_header, read_rsf


@dataclass(frozen=True)
class ComparisonResult:
    """Boolean-compatible comparison result with diagnostic details."""

    passed: bool
    message: str
    max_abs_diff: float | None = None
    max_rel_diff: float | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.passed

    def assert_ok(self) -> None:
        if not self.passed:
            raise AssertionError(self.message)


def compare_arrays(
    a: Any,
    b: Any,
    rtol: float = 1e-5,
    atol: float = 1e-8,
) -> ComparisonResult:
    """Compare two array-like objects with NumPy allclose semantics."""

    left = np.asarray(a)
    right = np.asarray(b)
    details: dict[str, Any] = {
        "shape1": left.shape,
        "shape2": right.shape,
        "dtype1": str(left.dtype),
        "dtype2": str(right.dtype),
        "rtol": rtol,
        "atol": atol,
    }

    if left.shape != right.shape:
        return ComparisonResult(
            False,
            f"Array shape mismatch: {left.shape} != {right.shape}",
            details=details,
        )

    try:
        passed = bool(np.allclose(left, right, rtol=rtol, atol=atol, equal_nan=True))
        max_abs, max_rel = _array_error_stats(left, right)
    except (TypeError, ValueError) as exc:
        return ComparisonResult(
            False,
            f"Array values are not comparable with allclose: {exc}",
            details=details,
        )

    details["max_abs_diff"] = max_abs
    details["max_rel_diff"] = max_rel
    message = "Arrays match" if passed else (
        f"Array values differ: max_abs_diff={max_abs:g}, max_rel_diff={max_rel:g}, "
        f"rtol={rtol:g}, atol={atol:g}"
    )
    return ComparisonResult(passed, message, max_abs, max_rel, details)


def compare_headers(
    h1: RSFHeader | Mapping[str, Any] | str | os.PathLike[str],
    h2: RSFHeader | Mapping[str, Any] | str | os.PathLike[str],
    ignore_keys: Iterable[str] | None = None,
) -> ComparisonResult:
    """Compare two RSF headers after optionally ignoring volatile keys."""

    header1 = _coerce_header(h1)
    header2 = _coerce_header(h2)
    ignored = set(ignore_keys or ())
    keys1 = set(header1.params) - ignored
    keys2 = set(header2.params) - ignored

    missing = sorted(keys2 - keys1)
    extra = sorted(keys1 - keys2)
    value_mismatches: list[tuple[str, str, str]] = []
    for key in sorted(keys1 & keys2):
        value1 = header1[key]
        value2 = header2[key]
        if not _header_values_equal(value1, value2):
            value_mismatches.append((key, value1, value2))

    details: dict[str, Any] = {
        "missing": missing,
        "extra": extra,
        "mismatches": value_mismatches,
        "ignored": sorted(ignored),
    }

    if missing or extra or value_mismatches:
        parts: list[str] = []
        if missing:
            parts.append(f"missing keys in first header: {', '.join(missing)}")
        if extra:
            parts.append(f"extra keys in first header: {', '.join(extra)}")
        if value_mismatches:
            preview = ", ".join(
                f"{key}: {value1!r} != {value2!r}"
                for key, value1, value2 in value_mismatches[:5]
            )
            parts.append(f"value mismatches: {preview}")
        return ComparisonResult(False, "Header mismatch: " + "; ".join(parts), details=details)

    return ComparisonResult(True, "Headers match", details=details)


def compare_rsf(
    file1: str | os.PathLike[str],
    file2: str | os.PathLike[str],
    rtol: float = 1e-5,
    atol: float = 1e-8,
    ignore_keys: Iterable[str] | None = ("in",),
) -> ComparisonResult:
    """Compare two file-backed RSF datasets."""

    rsf1 = read_rsf(file1)
    rsf2 = read_rsf(file2)
    header_result = compare_headers(rsf1.header, rsf2.header, ignore_keys=ignore_keys)
    array_result = compare_arrays(rsf1.data, rsf2.data, rtol=rtol, atol=atol)
    passed = bool(header_result) and bool(array_result)
    details = {
        "header": header_result,
        "array": array_result,
        "file1": str(Path(file1)),
        "file2": str(Path(file2)),
    }
    if passed:
        return ComparisonResult(True, "RSF files match", details=details)
    return ComparisonResult(
        False,
        f"RSF mismatch: {header_result.message}; {array_result.message}",
        array_result.max_abs_diff,
        array_result.max_rel_diff,
        details,
    )


def assert_rsf_allclose(
    file1: str | os.PathLike[str],
    file2: str | os.PathLike[str],
    rtol: float = 1e-5,
    atol: float = 1e-8,
    ignore_keys: Iterable[str] | None = ("in",),
) -> None:
    """Assert that two RSF files have compatible headers and allclose payloads."""

    compare_rsf(file1, file2, rtol=rtol, atol=atol, ignore_keys=ignore_keys).assert_ok()


def _coerce_header(
    value: RSFHeader | Mapping[str, Any] | str | os.PathLike[str],
) -> RSFHeader:
    if isinstance(value, RSFHeader):
        return value
    if isinstance(value, (str, os.PathLike)):
        return read_header(value)
    return RSFHeader(value)


def _header_values_equal(value1: str, value2: str) -> bool:
    if value1 == value2:
        return True
    number1 = _parse_float(value1)
    number2 = _parse_float(value2)
    if number1 is None or number2 is None:
        return False
    if math.isnan(number1) and math.isnan(number2):
        return True
    return number1 == number2


def _parse_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _array_error_stats(left: np.ndarray, right: np.ndarray) -> tuple[float, float]:
    if left.size == 0:
        return 0.0, 0.0

    diff = np.abs(left - right)
    finite_diff = diff[np.isfinite(diff)]
    max_abs = float(np.max(finite_diff)) if finite_diff.size else 0.0

    scale = np.abs(right)
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = np.where(scale > 0, diff / scale, np.where(diff == 0, 0.0, np.inf))
    finite_rel = rel[np.isfinite(rel)]
    max_rel = float(np.max(finite_rel)) if finite_rel.size else float("inf")
    return max_abs, max_rel

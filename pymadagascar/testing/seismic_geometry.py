"""Internal seismic geometry fixtures and contract checks.

This module is testing infrastructure for the seismic topic work.  It defines
small deterministic geometry helpers for regular signed-offset gathers,
explicit offset vectors, and minimal numeric source/receiver tables.  It is not
part of the stable public API and is deliberately not exported from
``pymadagascar.testing``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf


SOURCE_RECEIVER_FIELDS = (
    "trace",
    "source_x",
    "receiver_x",
    "offset",
    "midpoint",
    "channel",
    "source_id",
    "receiver_id",
)


class SeismicGeometryError(ValueError):
    """Raised when a small-gather geometry fixture violates its contract."""


@dataclass(frozen=True)
class RegularOffsetGeometry:
    """Regular signed-offset geometry represented by ordinary RSF axis 2."""

    offsets: np.ndarray
    unit: str
    time_unit: str
    velocity_unit: str
    axis: int
    sign_convention: str
    coordinate_sampling: str
    source: str = "ordinary_rsf_axis"

    def as_report(self) -> dict[str, object]:
        return {
            "source": self.source,
            "axis": self.axis,
            "unit": self.unit,
            "time_unit": self.time_unit,
            "velocity_unit": self.velocity_unit,
            "sign_convention": self.sign_convention,
            "coordinate_sampling": self.coordinate_sampling,
            "ntrace": int(self.offsets.size),
            "offset_min": float(np.min(self.offsets)),
            "offset_max": float(np.max(self.offsets)),
            "offset_step": float(self.offsets[1] - self.offsets[0])
            if self.offsets.size > 1
            else 0.0,
        }


@dataclass(frozen=True)
class ExplicitOffsetVector:
    """Trace-compatible offset vector for irregular small-gather fixtures."""

    values: np.ndarray
    unit: str
    time_unit: str
    velocity_unit: str
    sign_convention: str
    source: str = "explicit_offset_vector"

    def as_report(self) -> dict[str, object]:
        return {
            "source": self.source,
            "unit": self.unit,
            "time_unit": self.time_unit,
            "velocity_unit": self.velocity_unit,
            "sign_convention": self.sign_convention,
            "ntrace": int(self.values.size),
            "offset_min": float(np.min(self.values)),
            "offset_max": float(np.max(self.values)),
            "regular_spacing": _regular_spacing(self.values),
        }


def make_regular_offset_geometry(
    item: RSFArray | str | Path,
    *,
    expected_ntrace: int | None = None,
    offset_axis: int = 2,
    velocity_unit: str = "m/s",
) -> RegularOffsetGeometry:
    """Validate and return the S1/S3 regular signed-offset gather geometry."""

    rsf = _as_rsf_array(item)
    cube = Hypercube.from_header(rsf.header)
    if cube.ndim < 2 or np.asarray(rsf.data).ndim < 2:
        raise SeismicGeometryError("regular offset gather requires at least 2D RSF data")
    if offset_axis != 2:
        raise SeismicGeometryError("S4-2 regular offset contract requires RSF axis 2")

    time_axis = cube.axis(1)
    offset = cube.axis(offset_axis)
    _validate_time_axis(time_axis)
    if expected_ntrace is not None and offset.n != int(expected_ntrace):
        raise SeismicGeometryError(
            f"regular offset axis has {offset.n} traces, expected {expected_ntrace}"
        )
    if rsf.data.shape[0] != offset.n:
        raise SeismicGeometryError(
            f"NumPy trace dimension has {rsf.data.shape[0]} traces, expected n2={offset.n}"
        )
    if offset.label != "Offset":
        raise SeismicGeometryError("regular offset axis must have label2=Offset")
    if not offset.unit:
        raise SeismicGeometryError("regular offset axis must define unit2=")
    if not np.isfinite(offset.o):
        raise SeismicGeometryError("regular offset o2= must be finite")
    if not np.isfinite(offset.d) or offset.d <= 0.0:
        raise SeismicGeometryError("regular offset d2= must be finite and positive")

    sampling = rsf.header.get("coordinate_sampling", "regular")
    if sampling != "regular":
        raise SeismicGeometryError("regular offset gather requires coordinate_sampling=regular")
    role = rsf.header.get("axis2_role", "signed_offset")
    if role != "signed_offset":
        raise SeismicGeometryError("regular offset gather requires axis2_role=signed_offset")
    sign = rsf.header.get("offset_sign_convention", "receiver_minus_source")
    if sign != "receiver_minus_source":
        raise SeismicGeometryError(
            "regular offset gather requires receiver_minus_source sign convention"
        )
    unit = str(offset.unit)
    time_unit = str(time_axis.unit or "")
    validate_offset_unit_consistency(unit, time_unit=time_unit, velocity_unit=velocity_unit)
    offsets = offset.coordinates()
    return RegularOffsetGeometry(
        offsets=offsets,
        unit=unit,
        time_unit=time_unit,
        velocity_unit=velocity_unit,
        axis=offset_axis,
        sign_convention=sign,
        coordinate_sampling=sampling,
    )


def make_explicit_offset_vector(
    offset: ExplicitOffsetVector | RSFArray | str | Path | np.ndarray,
    *,
    expected_ntrace: int,
    unit: str = "m",
    time_unit: str = "s",
    velocity_unit: str = "m/s",
    sign_convention: str = "receiver_minus_source",
) -> ExplicitOffsetVector:
    """Validate a trace-compatible explicit offset vector."""

    if isinstance(offset, ExplicitOffsetVector):
        values = np.asarray(offset.values, dtype=np.float64)
        unit = offset.unit
        time_unit = offset.time_unit
        velocity_unit = offset.velocity_unit
        sign_convention = offset.sign_convention
    elif isinstance(offset, RSFArray):
        values = _as_1d_offset_array(offset.data)
        unit = str(offset.header.get("offset_unit", unit))
        time_unit = str(offset.header.get("time_unit", time_unit))
        velocity_unit = str(offset.header.get("velocity_unit", velocity_unit))
        sign_convention = str(offset.header.get("offset_sign_convention", sign_convention))
    elif isinstance(offset, (str, Path)):
        return make_explicit_offset_vector(
            read_rsf(offset),
            expected_ntrace=expected_ntrace,
            unit=unit,
            time_unit=time_unit,
            velocity_unit=velocity_unit,
            sign_convention=sign_convention,
        )
    else:
        values = _as_1d_offset_array(offset)

    if values.size != int(expected_ntrace):
        raise SeismicGeometryError(
            f"explicit offset vector has {values.size} samples, expected {expected_ntrace}"
        )
    if not bool(np.all(np.isfinite(values))):
        raise SeismicGeometryError("explicit offset vector values must be finite")
    if sign_convention != "receiver_minus_source":
        raise SeismicGeometryError(
            "explicit offset vector requires receiver_minus_source sign convention"
        )
    validate_offset_unit_consistency(unit, time_unit=time_unit, velocity_unit=velocity_unit)
    return ExplicitOffsetVector(
        values=np.ascontiguousarray(values, dtype=np.float64),
        unit=unit,
        time_unit=time_unit,
        velocity_unit=velocity_unit,
        sign_convention=sign_convention,
    )


def validate_offset_unit_consistency(
    offset_unit: str,
    *,
    time_unit: str = "s",
    velocity_unit: str = "m/s",
) -> str:
    """Validate the offset/time/velocity unit contract for small gathers."""

    if not offset_unit:
        raise SeismicGeometryError("offset unit must be provided")
    if not time_unit:
        raise SeismicGeometryError("time unit must be provided")
    if not velocity_unit:
        raise SeismicGeometryError("velocity unit must be provided")
    expected = f"{offset_unit}/{time_unit}"
    if velocity_unit != expected:
        raise SeismicGeometryError(
            f"velocity unit {velocity_unit!r} is incompatible with "
            f"offset unit {offset_unit!r} and time unit {time_unit!r}; expected {expected!r}"
        )
    return offset_unit


def write_offset_vector_rsf(
    path: str | Path,
    offset: ExplicitOffsetVector | np.ndarray,
    *,
    unit: str = "m",
    time_unit: str = "s",
    velocity_unit: str = "m/s",
) -> RSFArray:
    """Write an explicit offset vector as a small internal RSF coordinate file."""

    vector = make_explicit_offset_vector(
        offset,
        expected_ntrace=np.asarray(offset.values if isinstance(offset, ExplicitOffsetVector) else offset).size,
        unit=unit,
        time_unit=time_unit,
        velocity_unit=velocity_unit,
    )
    header = RSFHeader(
        {
            "o1": 0,
            "d1": 1,
            "label1": "Trace",
            "unit1": "index",
            "coordinate_role": "explicit_offset",
            "geometry_model": "explicit_offset_vector",
            "offset_unit": vector.unit,
            "time_unit": vector.time_unit,
            "velocity_unit": vector.velocity_unit,
            "offset_sign_convention": vector.sign_convention,
            "fixture_scope": "internal_testing",
            "trace_header_model": "explicit_offset_vector_only",
            "segy_trace_header_model": "not_supported",
        }
    )
    return write_rsf(path, vector.values, header)


def make_source_receiver_table(
    *,
    ntrace: int | None = None,
    offsets: np.ndarray | ExplicitOffsetVector | None = None,
    offset_o: float = -500.0,
    offset_d: float = 50.0,
    midpoint: float = 0.0,
    unit: str = "m",
    path: str | Path | None = None,
) -> RSFArray:
    """Create a deterministic minimal numeric source/receiver geometry table."""

    if offsets is None:
        if ntrace is None:
            ntrace = 21
        values = float(offset_o) + float(offset_d) * np.arange(int(ntrace), dtype=np.float64)
    else:
        raw_values = offsets.values if isinstance(offsets, ExplicitOffsetVector) else offsets
        values = _as_1d_offset_array(raw_values)
        if ntrace is None:
            ntrace = int(values.size)
    vector = make_explicit_offset_vector(
        values,
        expected_ntrace=int(ntrace),
        unit=unit,
        time_unit="s",
        velocity_unit=f"{unit}/s",
    )
    if not np.isfinite(float(midpoint)):
        raise SeismicGeometryError("midpoint must be finite")

    trace = np.arange(vector.values.size, dtype=np.float64)
    midpoint_values = np.full(vector.values.size, float(midpoint), dtype=np.float64)
    source_x = midpoint_values - 0.5 * vector.values
    receiver_x = midpoint_values + 0.5 * vector.values
    table = np.column_stack(
        [
            trace,
            source_x,
            receiver_x,
            vector.values,
            midpoint_values,
            trace,
            trace,
            trace,
        ]
    ).astype(np.float64)
    header = _source_receiver_header(vector.values.size, unit=vector.unit)
    result = RSFArray(table, header)
    if path is not None:
        return write_rsf(path, result.data, result.header)
    return result


def validate_source_receiver_table(
    item: RSFArray | str | Path,
    *,
    atol: float = 1.0e-9,
) -> dict[str, object]:
    """Validate the minimal numeric source/receiver table contract."""

    table = _as_rsf_array(item)
    data = np.asarray(table.data, dtype=np.float64)
    if data.ndim != 2:
        raise SeismicGeometryError("source/receiver table must be a 2D numeric RSF table")
    fields = _field_names(table.header)
    missing = [field for field in SOURCE_RECEIVER_FIELDS if field not in fields]
    if missing:
        raise SeismicGeometryError(
            "source/receiver table is missing required fields: " + ", ".join(missing)
        )
    if data.shape[1] != len(fields):
        raise SeismicGeometryError(
            f"source/receiver table has {data.shape[1]} columns, header lists {len(fields)}"
        )
    if not bool(np.all(np.isfinite(data))):
        raise SeismicGeometryError("source/receiver table values must be finite")

    values = {field: data[:, fields.index(field)] for field in SOURCE_RECEIVER_FIELDS}
    expected_offset = values["receiver_x"] - values["source_x"]
    expected_midpoint = 0.5 * (values["source_x"] + values["receiver_x"])
    max_offset_error = float(np.max(np.abs(values["offset"] - expected_offset)))
    max_midpoint_error = float(np.max(np.abs(values["midpoint"] - expected_midpoint)))
    trace_sequence_ok = bool(np.array_equal(values["trace"], np.arange(data.shape[0])))
    channel_sequence_ok = bool(np.array_equal(values["channel"], np.arange(data.shape[0])))
    metrics = {
        "ntrace": int(data.shape[0]),
        "field_count": int(data.shape[1]),
        "finite": True,
        "offset_relation_ok": max_offset_error <= float(atol),
        "midpoint_relation_ok": max_midpoint_error <= float(atol),
        "trace_sequence_ok": trace_sequence_ok,
        "channel_sequence_ok": channel_sequence_ok,
        "max_abs_offset_error": max_offset_error,
        "max_abs_midpoint_error": max_midpoint_error,
        "trace_header_model": table.header.get("trace_header_model"),
        "segy_trace_header_model": table.header.get("segy_trace_header_model"),
    }
    metrics["overall_pass"] = bool(
        metrics["offset_relation_ok"]
        and metrics["midpoint_relation_ok"]
        and metrics["trace_sequence_ok"]
        and metrics["channel_sequence_ok"]
        and table.header.get("trace_header_model") == "minimal_numeric_header_table"
        and table.header.get("segy_trace_header_model") == "not_supported"
    )
    return metrics


def table_column(item: RSFArray | str | Path, field: str) -> np.ndarray:
    """Return one numeric column from a minimal source/receiver table."""

    table = _as_rsf_array(item)
    fields = _field_names(table.header)
    if field not in fields:
        raise SeismicGeometryError(f"source/receiver table has no field {field!r}")
    data = np.asarray(table.data, dtype=np.float64)
    return np.ascontiguousarray(data[:, fields.index(field)], dtype=np.float64)


def _source_receiver_header(ntrace: int, *, unit: str) -> RSFHeader:
    header = RSFHeader(
        {
            "n1": len(SOURCE_RECEIVER_FIELDS),
            "o1": 0,
            "d1": 1,
            "label1": "HeaderKey",
            "unit1": "index",
            "n2": ntrace,
            "o2": 0,
            "d2": 1,
            "label2": "Trace",
            "unit2": "index",
            "fixture_scope": "internal_testing",
            "geometry_model": "minimal_source_receiver_table",
            "source_receiver_geometry": "deterministic_1d",
            "trace_header_model": "minimal_numeric_header_table",
            "segy_trace_header_model": "not_supported",
            "offset_sign_convention": "receiver_minus_source",
            "coordinate_unit": unit,
            "field_count": len(SOURCE_RECEIVER_FIELDS),
            "field_names": ",".join(SOURCE_RECEIVER_FIELDS),
            "ordinary_rsf_header_boundary": "regular_axes_only",
            "explicit_offset_boundary": "1d_trace_compatible_coordinate",
            "segy_header_boundary": "not_supported",
        }
    )
    for index, field in enumerate(SOURCE_RECEIVER_FIELDS, start=1):
        header[f"key{index}"] = field
        header[f"key{index}_unit"] = _field_unit(field, unit=unit)
    return header


def _field_unit(field: str, *, unit: str) -> str:
    if field in {"source_x", "receiver_x", "offset", "midpoint"}:
        return unit
    return "index"


def _as_rsf_array(item: RSFArray | str | Path) -> RSFArray:
    if isinstance(item, RSFArray):
        return item
    return read_rsf(item)


def _as_1d_offset_array(values: Any) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        raise SeismicGeometryError("explicit offset vector must be 1D")
    return np.ascontiguousarray(array, dtype=np.float64)


def _validate_time_axis(axis: Any) -> None:
    if axis.label != "Time":
        raise SeismicGeometryError("regular offset gather requires label1=Time")
    if axis.unit != "s":
        raise SeismicGeometryError("regular offset gather requires unit1=s")
    if not np.isfinite(axis.o):
        raise SeismicGeometryError("time axis o1= must be finite")
    if not np.isfinite(axis.d) or axis.d <= 0.0:
        raise SeismicGeometryError("time axis d1= must be finite and positive")


def _field_names(header: RSFHeader) -> list[str]:
    names = header.get("field_names")
    if names:
        return [name.strip() for name in str(names).split(",") if name.strip()]
    count = int(header.get("field_count", 0))
    return [str(header.get(f"key{index}", "")) for index in range(1, count + 1)]


def _regular_spacing(values: np.ndarray, *, atol: float = 1.0e-9) -> bool:
    if values.size <= 2:
        return True
    spacing = np.diff(values)
    return bool(np.allclose(spacing, spacing[0], atol=atol, rtol=0.0))

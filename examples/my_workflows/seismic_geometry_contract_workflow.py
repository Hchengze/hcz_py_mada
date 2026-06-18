"""S4-2 small-gather geometry contract workflow.

This deterministic workflow documents internal geometry boundaries for future
seismic-topic work.  It is not a SEG-Y trace-header adapter, survey database,
or production geometry loader.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from pymadagascar.io.rsf import read_rsf
from pymadagascar.testing.seismic_fixtures import make_hyperbolic_gather_fixture
from pymadagascar.testing.seismic_geometry import (
    make_explicit_offset_vector,
    make_regular_offset_geometry,
    make_source_receiver_table,
    table_column,
    validate_source_receiver_table,
    write_offset_vector_rsf,
)
from pymadagascar.testing.seismic_metrics import write_metrics_json

from _common import parse_output_dir, print_outputs


def run_pipeline(output_dir: Path) -> dict[str, object]:
    """Run the S4-2 geometry contract design workflow."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "gather": output_dir / "s4_geometry_gather.rsf",
        "offset": output_dir / "s4_geometry_offset_vector.rsf",
        "table": output_dir / "s4_geometry_source_receiver_table.rsf",
        "report": output_dir / "s4_geometry_report.json",
    }

    gather = make_hyperbolic_gather_fixture(path=paths["gather"])
    regular = make_regular_offset_geometry(gather, expected_ntrace=gather.data.shape[0])
    explicit = make_explicit_offset_vector(
        regular.offsets,
        expected_ntrace=gather.data.shape[0],
        unit=regular.unit,
        time_unit=regular.time_unit,
        velocity_unit=regular.velocity_unit,
    )
    write_offset_vector_rsf(paths["offset"], explicit)
    make_source_receiver_table(offsets=explicit, path=paths["table"])

    offset_rsf = read_rsf(paths["offset"])
    table_rsf = read_rsf(paths["table"])
    table_metrics = validate_source_receiver_table(table_rsf)
    table_offsets = table_column(table_rsf, "offset")
    source_x = table_column(table_rsf, "source_x")
    receiver_x = table_column(table_rsf, "receiver_x")
    midpoint = table_column(table_rsf, "midpoint")
    offset_values = np.asarray(offset_rsf.data, dtype=np.float64)

    metrics = {
        "ntrace": int(gather.data.shape[0]),
        "regular_offset_min_m": float(np.min(regular.offsets)),
        "regular_offset_max_m": float(np.max(regular.offsets)),
        "regular_offset_step_m": float(regular.offsets[1] - regular.offsets[0]),
        "regular_explicit_max_abs_diff_m": float(
            np.max(np.abs(regular.offsets - offset_values))
        ),
        "table_offset_max_abs_diff_m": float(np.max(np.abs(table_offsets - offset_values))),
        "table_midpoint_max_abs_error_m": float(
            np.max(np.abs(midpoint - 0.5 * (source_x + receiver_x)))
        ),
        "table_receiver_minus_source_max_abs_error_m": float(
            np.max(np.abs(table_offsets - (receiver_x - source_x)))
        ),
        "finite_fraction": _finite_fraction(
            gather.data,
            offset_values,
            table_rsf.data,
        ),
        "source_receiver_table_overall_pass": bool(table_metrics["overall_pass"]),
    }
    checks = {
        "regular_explicit_agree": metrics["regular_explicit_max_abs_diff_m"] <= 1.0e-12,
        "table_offsets_agree": metrics["table_offset_max_abs_diff_m"] <= 1.0e-12,
        "table_offset_formula": bool(table_metrics["offset_relation_ok"]),
        "table_midpoint_formula": bool(table_metrics["midpoint_relation_ok"]),
        "finite": metrics["finite_fraction"] == 1.0,
        "ordinary_rsf_header_boundary": gather.header["trace_header_model"]
        == "ordinary_rsf_only",
        "minimal_header_table_boundary": table_rsf.header["trace_header_model"]
        == "minimal_numeric_header_table",
        "not_segy_trace_header": table_rsf.header["segy_trace_header_model"]
        == "not_supported",
    }
    checks["overall_pass"] = bool(all(checks.values()))

    report: dict[str, object] = {
        "workflow": "seismic_geometry_contract",
        "stage": "S4-2",
        "status": "internal_geometry_contract_design",
        "fixture": "hyperbolic_gather",
        "madagascar_references": [
            "../src-master/system/seismic/Mnmo.c",
            "../src-master/system/seismic/Mvscan.c",
            "../src-master/system/seismic/Mslant.c",
            "../src-master/system/seismic/Mradon.c",
            "../src-master/system/seismic/Mheaderattr.c",
            "../src-master/system/seismic/Mheadermath.c",
            "../src-master/system/main/headersort.c",
            "../src-master/system/seismic/Msegyheader.c",
        ],
        "contracts": {
            "regular_offset": regular.as_report(),
            "explicit_offset": explicit.as_report(),
            "source_receiver_table": {
                "field_names": [
                    "trace",
                    "source_x",
                    "receiver_x",
                    "offset",
                    "midpoint",
                    "channel",
                    "source_id",
                    "receiver_id",
                ],
                "trace_header_model": "minimal_numeric_header_table",
                "segy_trace_header_model": "not_supported",
            },
            "ordinary_rsf_header": "regular_axes_only",
            "explicit_offset_vector": "1d_trace_compatible_coordinate",
            "segy_trace_header": "out_of_scope",
        },
        "metrics": metrics,
        "checks": checks,
    }
    write_metrics_json(paths["report"], report)
    return report


def _finite_fraction(*arrays: np.ndarray) -> float:
    total = sum(array.size for array in arrays)
    finite = sum(int(np.count_nonzero(np.isfinite(array))) for array in arrays)
    return float(finite / total)


def main(argv: Sequence[str] | None = None) -> int:
    output_dir = parse_output_dir("seismic_geometry_contract", argv)
    report = run_pipeline(output_dir)
    metrics = report["metrics"]
    checks = report["checks"]
    assert isinstance(metrics, dict)
    assert isinstance(checks, dict)
    print(f"output_dir={output_dir}")
    print(
        "geometry_contract: "
        f"ntrace={metrics['ntrace']} "
        f"offset_diff={metrics['regular_explicit_max_abs_diff_m']:.6g} "
        f"table_diff={metrics['table_offset_max_abs_diff_m']:.6g} "
        f"overall_pass={checks['overall_pass']}"
    )
    print_outputs(
        [
            output_dir / "s4_geometry_gather.rsf",
            output_dir / "s4_geometry_offset_vector.rsf",
            output_dir / "s4_geometry_source_receiver_table.rsf",
            output_dir / "s4_geometry_report.json",
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

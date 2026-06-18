"""Demo for Stage C-6 robust statistics and non-finite QC.

Run from the project root:
    python examples/robust_statistics_nan_qc_demo.py [output_directory]
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar import RSFData
from pymadagascar.generic.statistics import (
    fillnan_rsf,
    isnan_rsf,
    mean_rsf,
    median_rsf,
    range_rsf,
    rms_rsf,
    std_rsf,
)
from pymadagascar.io.rsf import RSFHeader, write_rsf


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("robust_statistics_nan_qc_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    panel = np.array(
        [
            [0.0, 1.0, np.nan, 3.0, 25.0, 5.0],
            [1.0, 2.0, 3.0, np.inf, 5.0, 6.0],
            [-2.0, -1.0, 0.0, 1.0, 2.0, -np.inf],
        ],
        dtype=np.float32,
    )
    header = RSFHeader(
        {
            "n1": panel.shape[1],
            "o1": 0.0,
            "d1": 0.004,
            "label1": "Time",
            "unit1": "s",
            "n2": panel.shape[0],
            "o2": 100.0,
            "d2": 25.0,
            "label2": "Trace",
        }
    )

    paths = {
        "input": output_dir / "panel_with_nonfinite.rsf",
        "mask": output_dir / "nonfinite_mask.rsf",
        "filled": output_dir / "panel_filled.rsf",
        "mean": output_dir / "trace_mean.rsf",
        "rms": output_dir / "trace_rms.rsf",
        "std": output_dir / "trace_std.rsf",
        "median": output_dir / "trace_median.rsf",
        "range": output_dir / "trace_range.rsf",
        "chain": output_dir / "cleaned_trace_rms.rsf",
    }
    write_rsf(paths["input"], panel, header)

    isnan_rsf(paths["input"], paths["mask"], mode="nonfinite")
    fillnan_rsf(paths["input"], paths["filled"], mode="nonfinite", value=0.0)
    mean_rsf(paths["input"], paths["mean"], axis=1, nan_policy="omit")
    rms_rsf(paths["input"], paths["rms"], axis=1, nan_policy="omit")
    std_rsf(paths["input"], paths["std"], axis=1, nan_policy="omit")
    median_rsf(paths["input"], paths["median"], axis=1, nan_policy="omit")
    range_rsf(paths["input"], paths["range"], axis=1, nan_policy="omit")

    chained = RSFData(panel, header).fillnan(0.0, mode="nonfinite").rms(axis=1)
    chained.write(paths["chain"])

    print(f"output_dir={output_dir}")
    for name, path in paths.items():
        print(f"{name}={path}")
    print(f"RSFData chain shape={chained.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

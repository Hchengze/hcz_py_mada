"""Demo for Stage C-5 unary transforms and distribution QC.

Run from the project root:
    python examples/unary_distribution_qc_demo.py [output_directory]
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar import RSFData
from pymadagascar.generic.unary import (
    abs_rsf,
    exp_rsf,
    histogram_rsf,
    log_rsf,
    pow_rsf,
    quantile_rsf,
    sign_rsf,
    sqrt_rsf,
)
from pymadagascar.io.rsf import RSFHeader, write_rsf


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("unary_distribution_qc_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    n1 = 64
    n2 = 3
    x = np.linspace(-2.0, 2.0, n1, dtype=np.float32)
    panel = np.vstack(
        [
            x,
            np.sin(np.pi * x),
            0.5 * x + 0.25 * np.cos(3.0 * np.pi * x),
        ]
    ).astype(np.float32)
    header = RSFHeader(
        {
            "n1": n1,
            "o1": float(x[0]),
            "d1": float(x[1] - x[0]),
            "label1": "Sample coordinate",
            "n2": n2,
            "o2": 0.0,
            "d2": 1.0,
            "label2": "Trace",
        }
    )

    paths = {
        "input": output_dir / "synthetic_panel.rsf",
        "abs": output_dir / "panel_abs.rsf",
        "sign": output_dir / "panel_sign.rsf",
        "sqrt": output_dir / "panel_sqrt_abs.rsf",
        "log": output_dir / "panel_log_abs.rsf",
        "exp": output_dir / "panel_exp.rsf",
        "pow": output_dir / "panel_pow.rsf",
        "histogram": output_dir / "panel_histogram.rsf",
        "quantile": output_dir / "panel_quantile.rsf",
        "chain": output_dir / "panel_chain.rsf",
    }
    write_rsf(paths["input"], panel, header)

    abs_rsf(paths["input"], paths["abs"])
    sign_rsf(paths["input"], paths["sign"])
    sqrt_rsf(paths["abs"], paths["sqrt"])
    log_rsf(paths["abs"], paths["log"])
    exp_rsf(paths["input"], paths["exp"])
    pow_rsf(paths["input"], paths["pow"], exponent=2.0)
    histogram_rsf(paths["input"], paths["histogram"], bins=12)
    quantile_rsf(paths["input"], paths["quantile"], q=[0.05, 0.5, 0.95])

    chained = RSFData(panel, header).abs().sqrt().pow(2.0)
    chained.write(paths["chain"])

    print(f"output_dir={output_dir}")
    for name, path in paths.items():
        print(f"{name}={path}")
    print(f"RSFData chain shape={chained.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

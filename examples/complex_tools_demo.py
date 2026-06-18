"""Demonstrate basic complex RSF tools.

Run from the project root:

    python examples/complex_tools_demo.py

Optionally pass an output directory:

    python examples/complex_tools_demo.py complex_tools_output
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.generic.complex_tools import cmplx_rsf, imag_rsf, real_rsf, rtoc_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("examples") / "complex_tools_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    real_path = output_dir / "real_part.rsf"
    imag_path = output_dir / "imag_part.rsf"
    complex_path = output_dir / "complex.rsf"
    extracted_real_path = output_dir / "extracted_real.rsf"
    extracted_imag_path = output_dir / "extracted_imag.rsf"
    rtoc_path = output_dir / "real_to_complex.rsf"

    header = RSFHeader(
        {
            "o1": 0.0,
            "d1": 1.0,
            "label1": "Frequency bin",
            "o2": 0.0,
            "d2": 1.0,
            "label2": "Trace",
        }
    )
    real = np.array([[1.0, -3.0, 5.0], [7.0, 0.0, -1.5]], dtype=np.float32)
    imag = np.array([[2.0, -4.0, 0.5], [-8.0, 0.0, 3.5]], dtype=np.float32)
    write_rsf(real_path, real, header)
    write_rsf(imag_path, imag, header)

    cmplx_rsf(real_path, imag_path, complex_path)
    real_rsf(complex_path, extracted_real_path)
    imag_rsf(complex_path, extracted_imag_path)
    rtoc_rsf(real_path, rtoc_path)

    complex_data = read_rsf(complex_path).data
    rtoc_data = read_rsf(rtoc_path).data

    print(f"wrote {complex_path}")
    print(f"wrote {extracted_real_path}")
    print(f"wrote {extracted_imag_path}")
    print(f"wrote {rtoc_path}")
    print("")
    print(f"complex dtype: {complex_data.dtype}, shape: {complex_data.shape}")
    print(f"real-to-complex imaginary max: {np.max(np.abs(rtoc_data.imag)):g}")
    print("")
    print("CLI equivalents:")
    print(f"python -m pymadagascar.cli.cmplx {real_path} {imag_path} out={complex_path}")
    print(f"python -m pymadagascar.cli.real {complex_path} out={extracted_real_path}")
    print(f"python -m pymadagascar.cli.imag {complex_path} out={extracted_imag_path}")
    print(f"python -m pymadagascar.cli.rtoc {real_path} out={rtoc_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

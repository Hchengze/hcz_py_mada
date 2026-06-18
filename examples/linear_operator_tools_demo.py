"""Demo for minimal linear-operator dot tests and CG solvers.

Run from the project root:
    python examples/linear_operator_tools_demo.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.generic.linear_operator import (
    MatrixOperator,
    complex_dot_test,
    conjugate_gradient,
    conjugate_gradient_normal,
    dot_test,
    format_dot_test_result,
)
from pymadagascar.io.rsf import write_rsf


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("linear_operator_tools_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    real_matrix_path = output_dir / "real_matrix.rsf"
    real_rhs_path = output_dir / "real_rhs.rsf"
    real_spd_solution_path = output_dir / "real_spd_solution.rsf"
    real_normal_solution_path = output_dir / "real_normal_solution.rsf"
    complex_matrix_path = output_dir / "complex_matrix.rsf"
    complex_rhs_path = output_dir / "complex_rhs.rsf"
    complex_solution_path = output_dir / "complex_solution.rsf"

    real_matrix = np.array([[4.0, 1.0], [1.0, 3.0]], dtype=np.float32)
    real_rhs = np.array([1.0, 2.0], dtype=np.float32)
    write_rsf(real_matrix_path, real_matrix)
    write_rsf(real_rhs_path, real_rhs)

    real_operator = MatrixOperator(real_matrix)
    real_dot = dot_test(real_operator, seed=0)

    # Keep the API calls explicit: SPD solves A x=b, normal solves least squares.
    real_spd = conjugate_gradient(real_operator, real_rhs, niter=10, tol=1e-10)
    real_normal = conjugate_gradient_normal(real_operator, real_rhs, niter=10, tol=1e-10)
    write_rsf(real_spd_solution_path, real_spd.solution)
    write_rsf(real_normal_solution_path, real_normal.solution)

    complex_matrix = np.array(
        [[3.0 + 0.0j, 1.0 - 0.25j], [1.0 + 0.25j, 2.0 + 0.0j]],
        dtype=np.complex64,
    )
    complex_rhs = np.array([1.0 + 1.0j, 2.0 - 0.5j], dtype=np.complex64)
    write_rsf(complex_matrix_path, complex_matrix)
    write_rsf(complex_rhs_path, complex_rhs)

    complex_operator = MatrixOperator(complex_matrix)
    ctest = complex_dot_test(complex_operator, seed=0)
    csol = conjugate_gradient(complex_operator, complex_rhs, niter=10, tol=1e-10)
    write_rsf(complex_solution_path, np.asarray(csol.solution, dtype=np.complex64))

    print(f"output_dir={output_dir}")
    print("real dottest:")
    print(format_dot_test_result(real_dot))
    print(f"real SPD solution={real_spd.solution.tolist()} -> {real_spd_solution_path}")
    print(f"real normal solution={real_normal.solution.tolist()} -> {real_normal_solution_path}")
    print("complex cdottest:")
    print(format_dot_test_result(ctest))
    print(f"complex Hermitian solution={csol.solution.tolist()} -> {complex_solution_path}")
    print(f"wrote {real_matrix_path}")
    print(f"wrote {real_rhs_path}")
    print(f"wrote {complex_matrix_path}")
    print(f"wrote {complex_rhs_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

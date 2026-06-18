"""Demo for minimal RSF header table tools.

Run from the project root:
    python examples/header_table_tools_demo.py
"""

from __future__ import annotations

from pathlib import Path
import tempfile

import numpy as np

from pymadagascar.generic.header_table import (
    format_header_table_attr,
    header_table_attr,
    header_table_math,
    header_table_sort,
    read_header_table,
    write_header_table,
)


def main() -> None:
    workdir = Path(tempfile.mkdtemp(prefix="pymada_header_table_demo_"))
    headers = workdir / "headers.rsf"
    with_offset2 = workdir / "headers_with_offset2.rsf"
    sorted_headers = workdir / "headers_sorted.rsf"

    write_header_table(
        headers,
        {
            "offset": np.array([300.0, 100.0, 200.0], dtype=np.float32),
            "cdp": np.array([30.0, 10.0, 20.0], dtype=np.float32),
            "trace": np.array([1.0, 2.0, 3.0], dtype=np.float32),
        },
    )

    print(f"workdir={workdir}")
    print("headerattr:")
    print(format_header_table_attr(header_table_attr(headers, keys="offset,cdp")))

    header_table_math(headers, with_offset2, "offset*offset", out_key="offset2")
    header_table_sort(with_offset2, sorted_headers, "offset")

    for path in [headers, with_offset2, sorted_headers]:
        table = read_header_table(path)
        print(f"{path.name}: {path}")
        print(f"  keys={table.keys}")
        print(f"  data={table.data.tolist()}")


if __name__ == "__main__":
    main()

"""Demo for safe RSF copy/remove and min/max statistics."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

from pymadagascar.generic.file_ops import copy_rsf_dataset, remove_rsf_dataset
from pymadagascar.generic.stats import format_stat, max_rsf, min_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    out = Path(args[0]) if args else Path("_tmp_cp_rm_min_max_demo")
    out.mkdir(parents=True, exist_ok=True)

    source = out / "input.rsf"
    copied = out / "copy.rsf"

    data = np.array([[1.0, -2.0, 3.0], [4.0, 5.0, -6.0]], dtype=np.float32)
    header = RSFHeader({"o1": 0.0, "d1": 0.004, "label1": "Time", "unit1": "s"})
    write_rsf(source, data, header)

    copy_rsf_dataset(source, copied, overwrite=True)
    loaded = read_rsf(copied)
    print(f"copied shape={loaded.data.shape} dtype={loaded.data.dtype}")
    print(format_stat(min_rsf(copied)))
    print(format_stat(max_rsf(copied, axis=1)))

    dry_run = remove_rsf_dataset(copied)
    print("dry-run remove:")
    for path in dry_run.paths:
        print(f"  would_remove={path}")

    removed = remove_rsf_dataset(copied, dry_run=False, confirm=True)
    print(f"removed {len(removed.paths)} files")


if __name__ == "__main__":
    main()

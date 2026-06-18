"""Small helpers shared by local workflow examples."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import tempfile


def parse_output_dir(workflow_name: str, argv: Sequence[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description=f"Run the {workflow_name} pymadagascar workflow.")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=None,
        help="Directory for generated RSF/PNG outputs.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path(tempfile.mkdtemp(prefix=f"pymadagascar_{workflow_name}_"))
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def print_outputs(paths: Sequence[Path]) -> None:
    print("outputs:")
    for path in paths:
        print(f"  {path}")

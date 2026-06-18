"""Generate a small RSF spike dataset."""

from __future__ import annotations

from pathlib import Path
import sys

from pymadagascar.generic import spike
from pymadagascar.io.rsf import read_rsf, write_rsf


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args[0]) if args else Path("examples") / "spike_demo_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "spike_demo.rsf"
    rsf = spike(
        shape=(8, 4),
        locations=[(3, 2), (6, 4)],
        magnitudes=[1.0, -0.5],
    )
    write_rsf(output, rsf.data, rsf.header)

    loaded = read_rsf(output)
    print(f"Wrote {output}")
    print(f"NumPy shape: {loaded.data.shape}")
    print(f"RSF dimensions n1..nN: {loaded.header.dimensions}")
    print(f"Nonzero samples: {loaded.data.nonzero()}")


if __name__ == "__main__":
    main()

"""Benchmark hybrid batch_xcorr_cpp against the pure NumPy reference."""

from __future__ import annotations

import argparse
import gc
import shutil
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from pymadagascar.hybrid import cpp_available, last_xcorr_backend
from pymadagascar.hybrid.xcorr import _batch_xcorr_numpy, batch_xcorr_cpp


@dataclass
class Timing:
    name: str
    seconds: float
    peak_mib: float
    max_abs_error: float | None = None
    backend: str | None = None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ntraces", type=int, default=128)
    parser.add_argument("--nsamples", type=int, default=256)
    parser.add_argument("--dtype", choices=["float32", "float64"], default="float32")
    parser.add_argument("--mode", choices=["full", "same", "valid"], default="full")
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.ntraces < 1 or args.nsamples < 1:
        raise SystemExit("ntraces and nsamples must be positive")
    if args.repeat < 1:
        raise SystemExit("repeat must be positive")

    rng = np.random.default_rng(args.seed)
    data = rng.normal(size=(args.ntraces, args.nsamples)).astype(args.dtype)

    pure = _time_call(
        "python_numpy",
        lambda: _batch_xcorr_numpy(data, mode=args.mode),
        repeat=args.repeat,
        warmup=args.warmup,
    )
    reference = _batch_xcorr_numpy(data, mode=args.mode)

    timings = [pure]
    if cpp_available():
        hybrid = _time_call(
            "hybrid_cpp",
            lambda: batch_xcorr_cpp(data, mode=args.mode),
            repeat=args.repeat,
            warmup=args.warmup,
        )
        hybrid.backend = last_xcorr_backend()
        hybrid.max_abs_error = float(np.max(np.abs(batch_xcorr_cpp(data, mode=args.mode) - reference)))
        timings.append(hybrid)
    else:
        timings.append(Timing("hybrid_cpp", seconds=float("nan"), peak_mib=float("nan"), backend="unavailable"))

    report = _format_report(
        timings,
        ntraces=args.ntraces,
        nsamples=args.nsamples,
        dtype=args.dtype,
        mode=args.mode,
        repeat=args.repeat,
        madagascar_status=_madagascar_status(),
    )
    print(report)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report + "\n", encoding="utf-8")
    return 0


def _time_call(
    name: str,
    func: Callable[[], np.ndarray],
    *,
    repeat: int,
    warmup: int,
) -> Timing:
    for _ in range(warmup):
        func()
    gc.collect()

    elapsed: list[float] = []
    peaks: list[float] = []
    for _ in range(repeat):
        gc.collect()
        tracemalloc.start()
        start = time.perf_counter()
        result = func()
        seconds = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed.append(seconds)
        peaks.append(peak / (1024 * 1024))
        del result
    return Timing(name=name, seconds=statistics.median(elapsed), peak_mib=max(peaks))


def _format_report(
    timings: list[Timing],
    *,
    ntraces: int,
    nsamples: int,
    dtype: str,
    mode: str,
    repeat: int,
    madagascar_status: str,
) -> str:
    pure = timings[0]
    lines = [
        "# batch_xcorr_cpp Benchmark",
        "",
        f"- data shape: ({ntraces}, {nsamples})",
        f"- dtype: {dtype}",
        f"- mode: {mode}",
        f"- repeat: {repeat} median timing",
        f"- original Madagascar comparison: {madagascar_status}",
        "",
        "| implementation | backend | time_s | speedup_vs_python | peak_mem_mib | max_abs_error |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for item in timings:
        if np.isnan(item.seconds):
            lines.append(f"| {item.name} | {item.backend or ''} | n/a | n/a | n/a | n/a |")
            continue
        speedup = pure.seconds / item.seconds if item.seconds > 0 else float("inf")
        error = "reference" if item.max_abs_error is None else f"{item.max_abs_error:.6g}"
        lines.append(
            f"| {item.name} | {item.backend or item.name} | {item.seconds:.6f} | "
            f"{speedup:.3f} | {item.peak_mib:.3f} | {error} |"
        )
    return "\n".join(lines)


def _madagascar_status() -> str:
    candidates = ["sfxcorr", "sfcorr", "sfconv"]
    found = [name for name in candidates if shutil.which(name)]
    if not found:
        return "unavailable"
    return "available programs detected: " + ", ".join(found)


if __name__ == "__main__":
    raise SystemExit(main())

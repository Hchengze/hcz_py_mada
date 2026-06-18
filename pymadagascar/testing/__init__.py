"""Testing helpers for pymadagascar migration work."""

from .compare import (
    ComparisonResult,
    assert_rsf_allclose,
    compare_arrays,
    compare_headers,
    compare_rsf,
)
from .fixtures import (
    make_1d_rsf,
    make_2d_rsf,
    make_3d_rsf,
    make_ramp,
    make_random,
    make_sine,
    make_spike,
)
from .runner import (
    CommandComparisonResult,
    CommandRun,
    CommandRunError,
    MadagascarNotFoundError,
    compare_command_outputs,
    original_madagascar_available,
    run_madagascar_command,
    run_original_madagascar,
    run_pymadagascar,
)

__all__ = [
    "CommandComparisonResult",
    "CommandRun",
    "CommandRunError",
    "ComparisonResult",
    "MadagascarNotFoundError",
    "assert_rsf_allclose",
    "compare_arrays",
    "compare_command_outputs",
    "compare_headers",
    "compare_rsf",
    "make_1d_rsf",
    "make_2d_rsf",
    "make_3d_rsf",
    "make_ramp",
    "make_random",
    "make_sine",
    "make_spike",
    "original_madagascar_available",
    "run_madagascar_command",
    "run_original_madagascar",
    "run_pymadagascar",
]

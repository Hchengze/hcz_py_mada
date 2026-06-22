"""Lightweight release-baseline checks for pymadagascar."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.path.insert(0, str(ROOT))
    checks: list[tuple[str, Callable[[], None]]] = [
        ("import public package API", _check_public_api),
        ("package metadata is release-safe", _check_package_metadata),
        ("import lower-level modules", _check_lower_level_imports),
        ("hybrid fallback is available", _check_hybrid_fallback),
        ("required docs and examples exist", _check_required_paths),
        ("CLI inventory and runtime targets are consistent", _check_cli_inventory),
        ("example inventory is consistent", _check_examples_inventory),
        ("learning notebook is consistent", _check_learning_notebook),
        ("temporary output policy is documented", _check_output_policy),
    ]

    failures: list[str] = []
    for label, check in checks:
        try:
            check()
        except Exception as exc:  # pragma: no cover - exercised through subprocess tests.
            failures.append(f"{label}: {exc}")

    if failures:
        print("Release check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Release check passed.")
    print(
        "Summary: metadata, public imports, CLI targets, fallback hybrid backend, "
        "docs, learning notebook, examples, and temporary-output policy are consistent."
    )
    return 0


def _check_public_api() -> None:
    import pymadagascar
    from pymadagascar import RSFData, __version__, read, write

    for name, obj in {
        "pymadagascar": pymadagascar,
        "__version__": __version__,
        "read": read,
        "write": write,
        "RSFData": RSFData,
    }.items():
        if obj is None:
            raise RuntimeError(f"{name} imported as None")


def _check_package_metadata() -> None:
    import pymadagascar

    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data.get("project", {})
    if project.get("name") != "pymadagascar-hybrid":
        raise RuntimeError("unexpected project.name")
    version = str(project.get("version", ""))
    if not version or pymadagascar.__version__ != version:
        raise RuntimeError("pyproject version and pymadagascar.__version__ differ")
    readme = project.get("readme")
    if readme != "README.md" or not (ROOT / readme).is_file():
        raise RuntimeError("project.readme must reference the root README.md")
    if project.get("requires-python") != ">=3.10":
        raise RuntimeError("requires-python must remain >=3.10")
    dependencies = project.get("dependencies", [])
    if not any(str(item).startswith("numpy") for item in dependencies):
        raise RuntimeError("NumPy runtime dependency is missing")
    if any("pybind11" in str(item) or "ninja" in str(item) for item in dependencies):
        raise RuntimeError("C++ build tools must not be runtime dependencies")
    scripts = project.get("scripts", {})
    if not isinstance(scripts, dict) or len(scripts) != 36:
        raise RuntimeError("expected exactly 36 registered console scripts")

    build_system = data.get("build-system", {})
    build_requires = [str(item).lower() for item in build_system.get("requires", [])]
    if any("pybind11" in item or "ninja" in item for item in build_requires):
        raise RuntimeError("default build requirements must not require C++ tooling")
    scikit_build = data.get("tool", {}).get("scikit-build", {})
    if scikit_build.get("wheel", {}).get("cmake") is not False:
        raise RuntimeError("default wheel must disable CMake")
    cmake_define = scikit_build.get("cmake", {}).get("define", {})
    if cmake_define.get("PYMADAGASCAR_BUILD_CPP") != "OFF":
        raise RuntimeError("default C++ build define must be OFF")


def _check_lower_level_imports() -> None:
    from pymadagascar.core.params import RSFParams
    from pymadagascar.generic.array_math import divide_rsf, multiply_rsf, tpow_rsf
    from pymadagascar.generic.difference import diff_rsf, difference_metric
    from pymadagascar.generic.file_ops import copy_rsf_dataset
    from pymadagascar.generic.header_mask import header_cut_rsf, header_window_rsf
    from pymadagascar.generic.header_table import read_header_table, write_header_table
    from pymadagascar.generic.interleave import interleave_rsf
    from pymadagascar.generic.linear_operator import MatrixOperator, conjugate_gradient_normal, dot_test
    from pymadagascar.generic.rotate import rotate_rsf
    from pymadagascar.generic.sampling import bin_2d, linear_resample, max1, slice_array
    from pymadagascar.generic.spike import spike
    from pymadagascar.generic.stats import min_rsf
    from pymadagascar.generic.statistics import fillnan, isnan_mask, mean, range_stats
    from pymadagascar.generic.unary import absolute, histogram, quantile
    from pymadagascar.io.rsf import read_rsf, write_rsf
    from pymadagascar.seismic.mute import mutter
    from pymadagascar.seismic.stack import stack_along_axis, stack_rsf, stacks_rsf
    from pymadagascar.signal.calculus import causal_integrate, deriv, integral
    from pymadagascar.signal.conditioning import clip2, shift
    from pymadagascar.signal.convolution import autocorr, circular_convolve, envelope_correlation
    from pymadagascar.signal.fft import fft_rsf
    from pymadagascar.signal.preprocessing import cosine_taper, envelope, spectra, threshold
    from pymadagascar.signal.qc import bandstop, decimate, demean, detrend, local_rms, notch
    from pymadagascar.signal.spectral import (
        frequency_attributes,
        spectral_normalize,
        spectral_whiten,
        transfer_function,
        welch_csd,
        welch_psd,
    )
    from pymadagascar.signal.transforms import cosft, fft1_rsf, spectra2

    for name, obj in {
        "read_rsf": read_rsf,
        "write_rsf": write_rsf,
        "RSFParams": RSFParams,
        "generic.spike": spike,
        "generic.copy_rsf_dataset": copy_rsf_dataset,
        "generic.min_rsf": min_rsf,
        "generic.multiply_rsf": multiply_rsf,
        "generic.divide_rsf": divide_rsf,
        "generic.diff_rsf": diff_rsf,
        "generic.difference_metric": difference_metric,
        "generic.tpow_rsf": tpow_rsf,
        "generic.interleave_rsf": interleave_rsf,
        "generic.rotate_rsf": rotate_rsf,
        "generic.header_window_rsf": header_window_rsf,
        "generic.header_cut_rsf": header_cut_rsf,
        "generic.read_header_table": read_header_table,
        "generic.write_header_table": write_header_table,
        "generic.MatrixOperator": MatrixOperator,
        "generic.dot_test": dot_test,
        "generic.conjugate_gradient_normal": conjugate_gradient_normal,
        "generic.linear_resample": linear_resample,
        "generic.bin_2d": bin_2d,
        "generic.slice_array": slice_array,
        "generic.max1": max1,
        "generic.mean": mean,
        "generic.range_stats": range_stats,
        "generic.isnan_mask": isnan_mask,
        "generic.fillnan": fillnan,
        "generic.absolute": absolute,
        "generic.histogram": histogram,
        "generic.quantile": quantile,
        "signal.fft_rsf": fft_rsf,
        "signal.autocorr": autocorr,
        "signal.circular_convolve": circular_convolve,
        "signal.envelope_correlation": envelope_correlation,
        "signal.shift": shift,
        "signal.deriv": deriv,
        "signal.causal_integrate": causal_integrate,
        "signal.integral": integral,
        "signal.clip2": clip2,
        "signal.cosine_taper": cosine_taper,
        "signal.threshold": threshold,
        "signal.spectra": spectra,
        "signal.fft1_rsf": fft1_rsf,
        "signal.cosft": cosft,
        "signal.spectra2": spectra2,
        "signal.envelope": envelope,
        "signal.demean": demean,
        "signal.detrend": detrend,
        "signal.decimate": decimate,
        "signal.bandstop": bandstop,
        "signal.notch": notch,
        "signal.local_rms": local_rms,
        "signal.welch_psd": welch_psd,
        "signal.welch_csd": welch_csd,
        "signal.transfer_function": transfer_function,
        "signal.spectral_whiten": spectral_whiten,
        "signal.spectral_normalize": spectral_normalize,
        "signal.frequency_attributes": frequency_attributes,
        "seismic.stack_rsf": stack_rsf,
        "seismic.stacks_rsf": stacks_rsf,
        "seismic.stack_along_axis": stack_along_axis,
        "seismic.mutter": mutter,
    }.items():
        if obj is None:
            raise RuntimeError(f"{name} imported as None")


def _check_hybrid_fallback() -> None:
    import numpy as np

    from pymadagascar import hybrid

    available = hybrid.cpp_available()
    backend = hybrid.backend_name()
    result = hybrid.add_arrays_cpp(np.array([1.0], dtype=np.float32), np.array([2.0], dtype=np.float32))
    if result.shape != (1,) or float(result[0]) != 3.0:
        raise RuntimeError("hybrid add_arrays_cpp fallback returned an unexpected result")
    if backend not in {"cpp", "numpy"}:
        raise RuntimeError(f"unexpected hybrid backend name: {backend!r}")
    if not available and backend != "numpy":
        raise RuntimeError("missing C++ extension should report numpy backend")


def _check_required_paths() -> None:
    required = [
        "docs/README.md",
        "docs/PROJECT_STATUS.md",
        "docs/USER_GUIDE.md",
        "docs/API_AND_COMPATIBILITY.md",
        "docs/COVERAGE_AND_ROADMAP.md",
        "docs/TESTING_AND_ENVIRONMENT.md",
        "docs/KNOWN_LIMITATIONS.md",
        "docs/CHANGELOG.md",
        "docs/PYMADAGASCAR_LEARNING_GUIDE.ipynb",
        "README.md",
        ".gitignore",
        "pyproject.toml",
        "examples/local_quickstart.py",
        "examples/axis_calculus_conditioning_demo.py",
        "examples/seismic_gather_qc_demo.py",
        "examples/unary_distribution_qc_demo.py",
        "examples/robust_statistics_nan_qc_demo.py",
        "examples/spectral_averaging_attributes_demo.py",
        "examples/my_workflows",
        "examples/my_workflows/das_void_diffraction_workflow.py",
        "examples/my_workflows/seismic_signal_contract_workflow.py",
        "examples/my_workflows/seismic_signal_metrics_workflow.py",
        "examples/my_workflows/seismic_nmo_contract_workflow.py",
        "examples/my_workflows/seismic_semblance_contract_workflow.py",
        "examples/my_workflows/seismic_geometry_contract_workflow.py",
        "examples/my_workflows/seismic_fk_contract_workflow.py",
        "examples/my_workflows/seismic_small_gather_processing_workflow.py",
        "pymadagascar/testing/seismic_fixtures.py",
        "pymadagascar/testing/seismic_metrics.py",
        "pymadagascar/testing/seismic_geometry.py",
        "tests/test_seismic_signal_contracts.py",
        "tests/test_seismic_signal_metrics.py",
        "tests/test_seismic_nmo_contract.py",
        "tests/test_seismic_semblance_contract.py",
        "tests/test_seismic_geometry_contract.py",
        "tests/test_seismic_fk_contract.py",
        "tests/test_seismic_integrated_workflow.py",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    if missing:
        raise RuntimeError("missing required paths: " + ", ".join(missing))


def _check_cli_inventory() -> None:
    from tools.check_cli_inventory import validate_cli_inventory

    failures = validate_cli_inventory()
    if failures:
        raise RuntimeError("; ".join(failures))


def _check_examples_inventory() -> None:
    from tools.check_examples_inventory import validate_examples

    failures = validate_examples()
    if failures:
        raise RuntimeError("; ".join(failures))


def _check_learning_notebook() -> None:
    from tools.check_learning_notebook import validate_learning_notebook

    failures = validate_learning_notebook()
    if failures:
        raise RuntimeError("; ".join(failures))


def _check_output_policy() -> None:
    ignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    required_patterns = {
        "_tmp_*/",
        "examples/_output/",
        "examples/*_output/",
        "examples/my_workflows/_outputs/",
    }
    missing = sorted(pattern for pattern in required_patterns if pattern not in ignore_text)
    if missing:
        raise RuntimeError(".gitignore is missing output patterns: " + ", ".join(missing))


if __name__ == "__main__":
    raise SystemExit(main())

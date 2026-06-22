from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.generic import (
    add_noise as package_add_noise,
    noise as package_noise,
    noise_rsf as package_noise_rsf,
)
from pymadagascar.api import RSFData
from pymadagascar.generic.noise import NoiseError, add_noise, noise, noise_rsf
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _header() -> RSFHeader:
    return RSFHeader(
        {
            "o1": 0.5,
            "d1": 0.25,
            "label1": "Time",
            "unit1": "s",
            "o2": 2.0,
            "d2": 1.5,
            "label2": "Trace",
            "unit2": "km",
        }
    )


def _run_noise_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not env.get("PYTHONPATH")
        else str(PROJECT_ROOT) + os.pathsep + env["PYTHONPATH"]
    )
    return subprocess.run(
        [sys.executable, "-m", "pymadagascar.cli.noise", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_noise_seed_reproducibility() -> None:
    first = noise(shape=(8,), seed=123, std=0.5)
    second = noise(shape=(8,), seed=123, std=0.5)
    different = noise(shape=(8,), seed=124, std=0.5)

    assert package_noise is noise
    np.testing.assert_array_equal(first.data, second.data)
    assert not np.array_equal(first.data, different.data)


def test_noise_generates_1d_float32_rsf() -> None:
    result = noise(shape=(5,), seed=1, var=0.0, mean=2.0)

    assert result.data.shape == (5,)
    assert result.data.dtype == np.float32
    assert result.header.dimensions == (5,)
    assert result.header["data_format"] == "native_float"
    np.testing.assert_array_equal(result.data, np.full(5, 2.0, dtype=np.float32))


def test_noise_generates_2d_rsf_with_axis_metadata() -> None:
    result = noise(
        shape=(3, 2),
        seed=1,
        var=0.0,
        mean=1.5,
        axes=[
            {"n": 3, "o": 0.1, "d": 0.2, "label": "Sample", "unit": "s"},
            {"n": 2, "o": 4.0, "d": 2.0, "label": "Trace", "unit": "km"},
        ],
    )

    assert result.data.shape == (2, 3)
    assert result.header.dimensions == (3, 2)
    assert result.header["o1"] == "0.1"
    assert result.header["d2"] == "2"
    assert result.header["label2"] == "Trace"
    np.testing.assert_array_equal(result.data, np.full((2, 3), 1.5, dtype=np.float32))


def test_add_noise_adds_to_existing_data_with_seed() -> None:
    data = np.arange(4, dtype=np.float32)

    first = add_noise(data, seed=7, std=0.25)
    second = add_noise(data, seed=7, std=0.25)

    assert package_add_noise is add_noise
    assert first.dtype == np.float32
    np.testing.assert_array_equal(first, second)
    assert not np.array_equal(first, data)


def test_add_noise_var_zero_adds_mean_exactly() -> None:
    data = np.array([1.0, 2.0, 3.0], dtype=np.float32)

    result = add_noise(data, var=0.0, mean=3.0, distribution="uniform", seed=1)

    np.testing.assert_array_equal(result, np.array([4.0, 5.0, 6.0], dtype=np.float32))


def test_noise_rsf_adds_noise_and_inherits_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "noisy.rsf"
    data = np.arange(6, dtype=np.float32).reshape(2, 3)
    write_rsf(input_path, data, _header())

    result = noise_rsf(input_path, output_path, var=0.0, mean=2.0, seed=3)
    loaded = read_rsf(output_path)

    assert package_noise_rsf is noise_rsf
    assert result.header_path == output_path.resolve()
    assert loaded.header["label1"] == "Time"
    assert loaded.header["unit2"] == "km"
    np.testing.assert_array_equal(loaded.data, data + np.float32(2.0))


def test_noise_rsf_replace_uses_input_shape_and_header(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "replacement.rsf"
    write_rsf(input_path, np.arange(6, dtype=np.float32).reshape(2, 3), _header())

    noise_rsf(input_path, output_path, replace=True, var=0.0, mean=-1.0, seed=2)
    loaded = read_rsf(output_path)

    assert loaded.header.dimensions == (3, 2)
    assert loaded.header["o1"] == "0.5"
    np.testing.assert_array_equal(loaded.data, np.full((2, 3), -1.0, dtype=np.float32))


def test_rsfdata_noise_chain_method_does_not_mutate_source() -> None:
    data = np.arange(4, dtype=np.float32)
    rsf = RSFData(data, RSFHeader({"n1": 4, "o1": 0.0, "d1": 1.0, "label1": "Sample"}))

    noisy = rsf.noise(var=0.0, mean=2.0, seed=11)
    replaced = rsf.noise(var=0.0, mean=-1.0, seed=11, replace=True)

    np.testing.assert_array_equal(rsf.numpy(), data)
    np.testing.assert_array_equal(noisy.numpy(), data + np.float32(2.0))
    np.testing.assert_array_equal(replaced.numpy(), np.full(4, -1.0, dtype=np.float32))
    assert noisy.header["label1"] == "Sample"


def test_uniform_noise_range_bounds() -> None:
    result = noise(shape=(100,), seed=5, mean=10.0, distribution="uniform", noise_range=0.5)

    assert np.all(result.data >= 9.5)
    assert np.all(result.data <= 10.5)


def test_noise_rejects_invalid_distribution() -> None:
    with pytest.raises(NoiseError, match="normal or uniform"):
        noise(shape=(4,), distribution="laplace")


@pytest.mark.cli
def test_noise_cli_subprocess_generates_and_adds_noise(tmp_path: Path) -> None:
    direct_path = tmp_path / "direct.rsf"
    input_path = tmp_path / "input.rsf"
    noisy_path = tmp_path / "noisy.rsf"
    data = np.arange(4, dtype=np.float32)
    write_rsf(input_path, data, RSFHeader({"o1": 1.0, "d1": 0.5, "label1": "Sample"}))

    direct = _run_noise_cli(
        ["n1=4", "out=" + str(direct_path), "seed=1", "var=0", "mean=2"],
        tmp_path,
    )
    noisy = _run_noise_cli(
        [str(input_path), "out=" + str(noisy_path), "seed=1", "var=0", "mean=3"],
        tmp_path,
    )

    assert direct.returncode == 0, direct.stderr
    assert noisy.returncode == 0, noisy.stderr
    np.testing.assert_array_equal(read_rsf(direct_path).data, np.full(4, 2.0, dtype=np.float32))
    np.testing.assert_array_equal(read_rsf(noisy_path).data, data + np.float32(3.0))
    assert read_rsf(noisy_path).header["label1"] == "Sample"


@pytest.mark.original_madagascar
def test_original_sfnoise_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfnoise"):
        pytest.skip("Original Madagascar sfnoise is not installed")

    input_path = tmp_path / "input.rsf"
    original_path = tmp_path / "original.rsf"
    python_path = tmp_path / "python.rsf"
    write_rsf(input_path, np.arange(6, dtype=np.float32).reshape(2, 3), _header())

    run_original_madagascar(
        ["sfnoise", "in=input.rsf", "out=original.rsf", "rep=y", "seed=1", "var=0"],
        cwd=tmp_path,
        require_program="sfnoise",
    )
    noise_rsf(input_path, python_path, replace=True, seed=1, var=0.0)

    assert_rsf_allclose(original_path, python_path, ignore_keys={"in"})

from pathlib import Path

import numpy as np
import pytest

from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.testing.compare import (
    assert_rsf_allclose,
    compare_arrays,
    compare_headers,
    compare_rsf,
)
from pymadagascar.testing.fixtures import (
    make_1d_rsf,
    make_2d_rsf,
    make_3d_rsf,
    make_ramp,
    make_random,
    make_sine,
    make_spike,
)


def test_compare_arrays_passes_within_tolerance() -> None:
    left = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    right = left + np.array([0.0, 1.0e-6, -1.0e-6], dtype=np.float32)

    result = compare_arrays(left, right, rtol=1e-5, atol=1e-7)

    assert result
    assert result.max_abs_diff is not None


def test_compare_arrays_fails_outside_tolerance() -> None:
    result = compare_arrays([1.0, 2.0], [1.0, 2.2], rtol=1e-6, atol=1e-8)

    assert not result
    assert "Array values differ" in result.message


def test_compare_arrays_reports_shape_mismatch() -> None:
    result = compare_arrays(np.zeros((2, 3)), np.zeros((3, 2)))

    assert not result
    assert "shape mismatch" in result.message


def test_compare_headers_matches_numeric_equivalents() -> None:
    left = RSFHeader({"n1": 4, "o1": 0, "d1": "1.0", "label1": "Time"})
    right = RSFHeader({"n1": "4", "o1": "0.0", "d1": 1, "label1": "Time"})

    assert compare_headers(left, right)


def test_compare_headers_ignore_keys() -> None:
    left = RSFHeader({"n1": 4, "in": "./left.rsf@"})
    right = RSFHeader({"n1": 4, "in": "./right.rsf@"})

    assert not compare_headers(left, right)
    assert compare_headers(left, right, ignore_keys={"in"})


def test_compare_headers_reports_missing_and_mismatched_keys() -> None:
    left = RSFHeader({"n1": 4, "label1": "Time"})
    right = RSFHeader({"n1": 5, "unit1": "s"})

    result = compare_headers(left, right)

    assert not result
    assert "missing keys" in result.message
    assert "extra keys" in result.message
    assert "n1" in result.message


def test_compare_rsf_and_assert_allclose(tmp_path: Path) -> None:
    first = tmp_path / "first.rsf"
    second = tmp_path / "second.rsf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    header = RSFHeader({"label1": "Fast", "label2": "Slow"})
    write_rsf(first, data, header)
    write_rsf(second, data.copy(), header)

    assert compare_rsf(first, second)
    assert_rsf_allclose(first, second)


def test_compare_rsf_uses_rtol_and_atol(tmp_path: Path) -> None:
    first = tmp_path / "first.rsf"
    second = tmp_path / "second.rsf"
    data = np.ones((2, 3), dtype=np.float32)
    write_rsf(first, data, {"label1": "Fast"})
    write_rsf(second, data + 1e-4, {"label1": "Fast"})

    assert compare_rsf(first, second, rtol=1e-3, atol=1e-6)
    assert not compare_rsf(first, second, rtol=1e-6, atol=1e-8)


def test_assert_rsf_allclose_raises_with_diagnostics(tmp_path: Path) -> None:
    first = tmp_path / "first.rsf"
    second = tmp_path / "second.rsf"
    write_rsf(first, np.zeros(4, dtype=np.float32))
    write_rsf(second, np.ones(4, dtype=np.float32))

    with pytest.raises(AssertionError, match="RSF mismatch"):
        assert_rsf_allclose(first, second)


def test_fixture_rsf_shapes_and_metadata(tmp_path: Path) -> None:
    one = make_1d_rsf(n=5)
    two_path = tmp_path / "two.rsf"
    two = make_2d_rsf(two_path, shape=(3, 4))
    three = make_3d_rsf(shape=(2, 3, 4))

    assert one.data.shape == (5,)
    assert one.header.dimensions == (5,)
    assert two.data.shape == (3, 4)
    assert read_rsf(two_path).header.dimensions == (4, 3)
    assert three.data.shape == (2, 3, 4)
    assert three.header.dimensions == (4, 3, 2)


def test_fixture_signal_arrays_are_deterministic() -> None:
    spike = make_spike((5,), position=2)
    ramp = make_ramp((2, 3), start=1.0, step=0.5)
    sine = make_sine((4,), frequency=0.25)
    random1 = make_random((3, 3), seed=123)
    random2 = make_random((3, 3), seed=123)

    np.testing.assert_array_equal(spike, np.array([0, 0, 1, 0, 0], dtype=np.float32))
    np.testing.assert_array_equal(ramp, np.array([[1.0, 1.5, 2.0], [2.5, 3.0, 3.5]], dtype=np.float32))
    np.testing.assert_allclose(sine, np.array([0.0, 1.0, 0.0, -1.0], dtype=np.float32), atol=1e-6)
    np.testing.assert_array_equal(random1, random2)


def test_fixture_generators_can_write_rsf_files(tmp_path: Path) -> None:
    result = make_random(shape=(2, 2), seed=3, path=tmp_path / "random.rsf")

    assert hasattr(result, "header")
    loaded = read_rsf(tmp_path / "random.rsf")
    np.testing.assert_array_equal(loaded.data, result.data)

import numpy as np
import pytest

import pymadagascar.hybrid as hybrid
from pymadagascar.hybrid import xcorr as hybrid_xcorr


def _expected(data: np.ndarray, *, axis: int = -1, mode: str = "full") -> np.ndarray:
    array = np.asarray(data)
    moved = np.moveaxis(array, axis, -1)
    traces = moved.reshape((-1, moved.shape[-1]))
    output = np.stack([np.correlate(trace, trace, mode=mode) for trace in traces])
    reshaped = output.reshape(moved.shape[:-1] + (output.shape[-1],))
    return np.moveaxis(reshaped, -1, axis)


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
@pytest.mark.parametrize("mode", ["full", "same", "valid"])
def test_batch_xcorr_matches_numpy_small(dtype: type[np.floating], mode: str) -> None:
    data = np.array([[1.0, 0.0, 2.0], [0.0, 1.0, -1.0]], dtype=dtype)

    result = hybrid.batch_xcorr_cpp(data, axis=-1, mode=mode)

    np.testing.assert_allclose(result, _expected(data, mode=mode), rtol=1e-6, atol=1e-6)
    assert result.dtype == data.dtype


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_batch_xcorr_matches_numpy_medium(dtype: type[np.floating]) -> None:
    rng = np.random.default_rng(2026)
    data = rng.normal(size=(16, 96)).astype(dtype)

    result = hybrid.batch_xcorr_cpp(data, mode="full")

    tolerance = 2e-5 if dtype is np.float32 else 1e-10
    np.testing.assert_allclose(result, _expected(data, mode="full"), rtol=tolerance, atol=tolerance)


def test_batch_xcorr_axis_handling_3d() -> None:
    data = np.arange(2 * 3 * 5, dtype=np.float32).reshape(2, 3, 5)

    result = hybrid.batch_xcorr_cpp(data, axis=1, mode="same")

    np.testing.assert_allclose(result, _expected(data, axis=1, mode="same"), rtol=1e-6, atol=1e-6)
    assert result.shape == data.shape


def test_batch_xcorr_accepts_non_contiguous_arrays() -> None:
    base = np.arange(6 * 12, dtype=np.float64).reshape(6, 12)
    data = base[::2, 1::3]

    assert not data.flags.c_contiguous
    result = hybrid.batch_xcorr_cpp(data, mode="full")

    np.testing.assert_allclose(result, _expected(data, mode="full"), rtol=1e-10, atol=1e-10)


def test_batch_xcorr_numpy_fallback_when_cpp_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYMADAGASCAR_DISABLE_CPP", "1")
    hybrid_xcorr._reset_xcorr_for_tests()
    data = np.array([[1.0, 2.0, 1.0], [0.5, -1.0, 0.0]], dtype=np.float32)

    result = hybrid_xcorr.batch_xcorr_cpp(data, mode="full")

    np.testing.assert_allclose(result, _expected(data, mode="full"), rtol=1e-6, atol=1e-6)
    assert hybrid_xcorr.last_xcorr_backend() == "numpy"

    monkeypatch.delenv("PYMADAGASCAR_DISABLE_CPP", raising=False)
    hybrid_xcorr._reset_xcorr_for_tests()


def test_batch_xcorr_cpp_result_matches_numpy_when_extension_available() -> None:
    if not hybrid.cpp_available():
        pytest.skip("optional C++ extension is not built in this environment")
    data = np.linspace(-2.0, 2.0, 4 * 32, dtype=np.float64).reshape(4, 32)

    result = hybrid.batch_xcorr_cpp(data, mode="same")

    np.testing.assert_allclose(result, _expected(data, mode="same"), rtol=1e-10, atol=1e-10)
    assert hybrid.last_xcorr_backend() == "cpp"


def test_batch_xcorr_rejects_bad_mode() -> None:
    with pytest.raises(ValueError, match="mode must be full"):
        hybrid.batch_xcorr_cpp(np.ones((2, 4), dtype=np.float32), mode="bad")

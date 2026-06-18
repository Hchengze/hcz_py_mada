import numpy as np

import pymadagascar.hybrid as hybrid
from pymadagascar.hybrid import array_ops


def test_hybrid_package_imports():
    assert hybrid.backend_name() in {"cpp", "numpy"}
    assert isinstance(hybrid.cpp_available(), bool)


def test_cpp_extension_import_when_available():
    if hybrid.cpp_available():
        import pymadagascar._core as core

        assert hasattr(core, "add_arrays_cpp")
        assert hasattr(core, "scale_array_cpp")
    else:
        assert hybrid.backend_name() == "numpy"


def test_add_arrays_cpp_matches_numpy():
    a = np.arange(6, dtype=np.float32).reshape(2, 3)
    b = np.full_like(a, 2)

    out = hybrid.add_arrays_cpp(a, b)

    np.testing.assert_allclose(out, a + b)
    assert hybrid.last_backend() in {"cpp", "numpy"}


def test_scale_array_cpp_matches_numpy():
    a = np.linspace(-1.0, 1.0, 7, dtype=np.float64)

    out = hybrid.scale_array_cpp(a, 2.5)

    np.testing.assert_allclose(out, a * 2.5)
    assert hybrid.last_backend() in {"cpp", "numpy"}


def test_numpy_fallback_when_cpp_disabled(monkeypatch):
    monkeypatch.setenv("PYMADAGASCAR_DISABLE_CPP", "1")
    array_ops._reset_core_for_tests()

    a = np.array([1, 2, 3], dtype=np.float32)
    b = np.array([4, 5, 6], dtype=np.float32)

    added = array_ops.add_arrays_cpp(a, b)
    scaled = array_ops.scale_array_cpp(a, 3.0)

    np.testing.assert_allclose(added, a + b)
    np.testing.assert_allclose(scaled, a * 3.0)
    assert array_ops.backend_name() == "numpy"
    assert array_ops.last_backend() == "numpy"

    monkeypatch.delenv("PYMADAGASCAR_DISABLE_CPP", raising=False)
    array_ops._reset_core_for_tests()

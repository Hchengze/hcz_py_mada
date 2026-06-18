"""Shared pytest marker policy for the test suite."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


HYBRID_TEST_MODULES = {
    "test_hybrid_import.py",
    "test_hybrid_xcorr.py",
}

PROTOTYPE_TEST_MODULES = {
    "test_acoustic2d.py",
    "test_fk.py",
    "test_kirchhoff.py",
    "test_nmo_semblance.py",
    "test_radon.py",
    "test_segy.py",
}


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items: list[Any]) -> None:
    """Apply project markers by stable naming conventions."""

    for item in items:
        module_name = _module_name(item)
        test_name = item.name

        if test_name.startswith(("test_original_", "test_cli_original_")):
            item.add_marker(pytest.mark.original_madagascar)

        if module_name in HYBRID_TEST_MODULES:
            item.add_marker(pytest.mark.hybrid)

        if module_name in PROTOTYPE_TEST_MODULES:
            item.add_marker(pytest.mark.prototype)

        if module_name.startswith("test_cli_") or "_cli" in test_name:
            item.add_marker(pytest.mark.cli)


def _module_name(item: Any) -> str:
    path = getattr(item, "path", None)
    if path is None:
        path = getattr(item, "fspath")
    return Path(str(path)).name

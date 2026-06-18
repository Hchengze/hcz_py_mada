from __future__ import annotations

from pathlib import Path


def test_pytest_ini_registers_project_markers() -> None:
    pytest_ini = Path(__file__).resolve().parents[1] / "pytest.ini"
    text = pytest_ini.read_text(encoding="utf-8")

    for marker in ("original_madagascar", "slow", "hybrid", "cli", "prototype"):
        assert f"    {marker}:" in text

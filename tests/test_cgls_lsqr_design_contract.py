from __future__ import annotations

import pkgutil
from pathlib import Path

import pymadagascar.cli as cli_package
import pymadagascar.generic.linear_operator as linear_operator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT.parent / "src-master"


def test_solver_source_audit_paths_are_recorded_by_existing_tree() -> None:
    required = [
        SOURCE_ROOT / "system" / "main" / "conjgrad.c",
        SOURCE_ROOT / "system" / "main" / "cconjgrad.c",
        SOURCE_ROOT / "api" / "c" / "conjgrad.c",
        SOURCE_ROOT / "api" / "c" / "cconjgrad.c",
        SOURCE_ROOT / "user" / "pyang" / "Mmwni2d.c",
        SOURCE_ROOT / "book" / "slim" / "geo2008NewInsightsPareto" / "Matfcts" / "private" / "lsqr.m",
        SOURCE_ROOT / "trip" / "rvl" / "umin" / "include" / "lsqr.hh",
    ]

    assert all(path.is_file() for path in required)


def test_i0_4_cgls_lsqr_design_is_documented() -> None:
    roadmap = (PROJECT_ROOT / "docs" / "COVERAGE_AND_ROADMAP.md").read_text(encoding="utf-8")
    compatibility = (PROJECT_ROOT / "docs" / "API_AND_COMPATIBILITY.md").read_text(encoding="utf-8")

    for text in [roadmap, compatibility]:
        assert "I0-4" in text
        assert "CGLS" in text
        assert "LSQR" in text
        assert "run_cg_with_history" in text
        assert "run_cgnr_with_history" in text
    assert "not implemented" in compatibility


def test_cgls_and_lsqr_are_not_implemented_or_exported() -> None:
    for name in ["cgls", "lsqr", "CGLS", "LSQR"]:
        assert not hasattr(linear_operator, name)

    module_names = {module.name for module in pkgutil.iter_modules(cli_package.__path__)}
    assert "cgls" not in module_names
    assert "lsqr" not in module_names

from __future__ import annotations

import tomllib
from pathlib import Path

import pymadagascar


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
AUTHORITY_DOCS = {
    "README.md",
    "PROJECT_STATUS.md",
    "USER_GUIDE.md",
    "API_SURFACE.md",
    "API_AND_COMPATIBILITY.md",
    "COVERAGE_AND_ROADMAP.md",
    "TESTING_AND_ENVIRONMENT.md",
    "KNOWN_LIMITATIONS.md",
    "CHANGELOG.md",
}


def test_project_identity_and_public_version_match() -> None:
    project = PYPROJECT["project"]
    assert project["name"] == "pymadagascar-hybrid"
    assert project["version"] == pymadagascar.__version__
    assert project["requires-python"] == ">=3.10"
    assert project["readme"] == "README.md"
    assert (ROOT / project["readme"]).is_file()


def test_runtime_dependencies_keep_cpp_optional() -> None:
    dependencies = PYPROJECT["project"]["dependencies"]
    assert dependencies == ["numpy>=1.23"]
    assert "cpp" in PYPROJECT["project"]["optional-dependencies"]
    assert "test" in PYPROJECT["project"]["optional-dependencies"]


def test_default_build_is_pure_python() -> None:
    build_requires = PYPROJECT["build-system"]["requires"]
    assert build_requires == ["scikit-build-core>=0.8"]
    settings = PYPROJECT["tool"]["scikit-build"]
    assert settings["wheel"]["cmake"] is False
    assert settings["cmake"]["define"]["PYMADAGASCAR_BUILD_CPP"] == "OFF"


def test_console_script_metadata_has_expected_size_and_targets() -> None:
    scripts = PYPROJECT["project"]["scripts"]
    assert len(scripts) == 63
    assert all(name.startswith("pymada-") for name in scripts)
    assert all(target.startswith("pymadagascar.cli.") for target in scripts.values())
    assert all(target.endswith(":main") for target in scripts.values())


def test_authority_docs_are_exactly_the_live_docs_set() -> None:
    actual = {path.name for path in (ROOT / "docs").glob("*.md")}
    assert actual == AUTHORITY_DOCS


def test_release_output_paths_are_ignored() -> None:
    ignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in (
        "_tmp_*/",
        "examples/_output/",
        "examples/*_output/",
        "examples/my_workflows/_outputs/",
    ):
        assert pattern in ignore_text

"""Tests for the static learning-notebook artifact."""

from __future__ import annotations

from pathlib import Path

from tools.check_learning_notebook import (
    NOTEBOOK,
    REQUIRED_KEYWORDS,
    load_notebook,
    validate_learning_notebook,
)


ROOT = Path(__file__).resolve().parents[1]


def test_learning_notebook_exists_and_uses_nbformat_four() -> None:
    assert NOTEBOOK == ROOT / "docs" / "PYMADAGASCAR_LEARNING_GUIDE.ipynb"
    assert NOTEBOOK.is_file()
    notebook = load_notebook()
    assert notebook["nbformat"] == 4
    assert isinstance(notebook["cells"], list)


def test_learning_notebook_contains_required_topics() -> None:
    notebook = load_notebook()
    text = "\n".join(
        "".join(cell.get("source", []))
        if isinstance(cell.get("source", []), list)
        else str(cell.get("source", ""))
        for cell in notebook["cells"]
    ).lower()
    for keyword in REQUIRED_KEYWORDS:
        assert keyword.lower() in text


def test_learning_notebook_static_inventory_is_consistent() -> None:
    assert validate_learning_notebook() == []

"""Tests for the live XMind feature-map artifact."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from tools.check_mindmap import (
    REQUIRED_BRANCH_PREFIXES,
    REQUIRED_MEMBERS,
    load_root_topic,
    validate_mindmap,
)


ROOT = Path(__file__).resolve().parents[1]
MINDMAP = ROOT / "docs" / "PYMADAGASCAR_MINDMAP.xmind"


def test_mindmap_exists_and_is_xmind_workbook() -> None:
    assert MINDMAP.is_file()
    assert zipfile.is_zipfile(MINDMAP)
    with zipfile.ZipFile(MINDMAP) as archive:
        assert REQUIRED_MEMBERS <= set(archive.namelist())
        content = json.loads(archive.read("content.json").decode("utf-8"))
    assert content[0]["rootTopic"]["title"] == "pymadagascar"


def test_mindmap_has_required_top_level_branches() -> None:
    root_topic = load_root_topic()
    branches = {
        child["title"]
        for child in root_topic["children"]["attached"]
    }
    for prefix in REQUIRED_BRANCH_PREFIXES:
        assert any(title.startswith(prefix) for title in branches)


def test_mindmap_snapshot_and_live_inventory_are_consistent() -> None:
    assert validate_mindmap() == []

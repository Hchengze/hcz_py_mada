"""Validate the frozen XMind snapshot and current repository inventory."""

from __future__ import annotations

import json
import re
import tomllib
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[1]
MINDMAP = ROOT / "docs" / "PYMADAGASCAR_MINDMAP.xmind"
PROJECT_STATUS = ROOT / "docs" / "PROJECT_STATUS.md"
CLI_DIR = ROOT / "pymadagascar" / "cli"
PYPROJECT = ROOT / "pyproject.toml"

REQUIRED_MEMBERS = {
    "content.json",
    "metadata.json",
    "manifest.json",
    "content.xml",
    "META-INF/manifest.xml",
}

REQUIRED_BRANCH_PREFIXES = {
    "Project Identity",
    "Current Baseline",
    "Interfaces",
    "Core RSF Foundation",
    "Generic Data Operations",
    "Statistics and QC",
    "Signal Processing",
    "Seismic Processing",
    "Linear Operators and Inversion Foundation",
    "Modeling and Imaging Prototypes",
    "Data Formats and Headers",
    "Plotting and Visualization",
    "Examples and Workflows",
    "Testing and Release Tools",
    "Roadmap",
    "Stable vs Prototype Boundary",
}

REQUIRED_TEXT = {
    "Stage C-1 through Stage C-10 completed",
    "D-1 retained prototype",
    "D-2 paused",
    "Mindmap Documentation Pass M1",
    "C-11 must be bounded and use-case-driven",
    "Mindmap is a visual index, not an API stability source",
    "Pythonic convenience: direct local API or CLI, not upstream coverage",
    "workflow-only: example-local helpers, not public API",
    "XMind workbook feature map [visual index]",
    "check_mindmap.py",
}

ABSOLUTE_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]|/(?:home|mnt|Users)/)")
FROZEN_NOTICE = "XMind remains frozen at the"
SNAPSHOT_COUNTS = {
    "Pytest files": 62,
    "Top-level examples": 34,
    "Workflows": 6,
    "Workflow helpers": 1,
    "Authoritative Markdown docs": 8,
    "Mindmap artifacts": 1,
}
SNAPSHOT_TEST_STATUS = {
    "Windows pytest: 725 passed, 94 skipped",
    "WSL pytest: 791 passed, 28 skipped",
    "WSL original marker: 66 passed, 27 skipped",
}


def main() -> int:
    failures = validate_mindmap()
    if failures:
        print("Mindmap check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    cli_modules = _cli_modules()
    console_scripts = _console_scripts()
    print("Mindmap check passed.")
    print(
        "Summary: valid frozen Stage C-10/M1 XMind workbook with modern JSON "
        "and legacy XML, "
        f"{len(cli_modules)} CLI modules, {len(console_scripts)} console_scripts, "
        f"{len(cli_modules) - len(console_scripts)} module-only CLIs, "
        f"current repository {_pytest_file_count()} pytest files and "
        f"{_workflow_count()} workflows; required snapshot and roadmap boundaries agree."
    )
    return 0


def validate_mindmap(path: Path = MINDMAP) -> list[str]:
    failures: list[str] = []
    if not path.is_file():
        return [f"missing mindmap: {path.relative_to(ROOT)}"]
    if list((ROOT / "docs").glob("*.mm")):
        failures.append("legacy .mm mindmap artifacts remain in docs")

    try:
        with zipfile.ZipFile(path) as archive:
            members = set(archive.namelist())
            missing_members = sorted(REQUIRED_MEMBERS - members)
            if missing_members:
                return [
                    "XMind workbook is missing members: "
                    + ", ".join(missing_members)
                ]
            content = json.loads(archive.read("content.json").decode("utf-8"))
            metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            legacy_content = ET.fromstring(archive.read("content.xml"))
            legacy_manifest = ET.fromstring(
                archive.read("META-INF/manifest.xml")
            )
    except zipfile.BadZipFile as exc:
        return [f"mindmap is not a valid ZIP/XMind workbook: {exc}"]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"XMind JSON does not parse as UTF-8 JSON: {exc}"]
    except ET.ParseError as exc:
        return [f"XMind compatibility XML does not parse: {exc}"]

    if not isinstance(content, list) or len(content) != 1:
        return ["content.json must contain exactly one XMind sheet"]
    sheet = content[0]
    if not isinstance(sheet, dict) or sheet.get("class") != "sheet":
        return ["content.json sheet must have class=sheet"]
    root_topic = sheet.get("rootTopic")
    if not isinstance(root_topic, dict):
        return ["content.json sheet has no rootTopic object"]
    if root_topic.get("title") != "pymadagascar":
        failures.append("root topic title must be pymadagascar")

    active_sheet = metadata.get("activeSheetId")
    if active_sheet != sheet.get("id"):
        failures.append("metadata.json activeSheetId does not match the sheet id")

    manifest_entries = manifest.get("file-entries")
    if not isinstance(manifest_entries, dict):
        failures.append("manifest.json has no file-entries object")
    else:
        missing_manifest = sorted(REQUIRED_MEMBERS - set(manifest_entries))
        if missing_manifest:
            failures.append(
                "manifest.json is missing entries: "
                + ", ".join(missing_manifest)
            )

    legacy_title = _legacy_root_title(legacy_content)
    if legacy_title != "pymadagascar":
        failures.append("legacy content.xml root topic must be pymadagascar")
    if _local_name(legacy_manifest.tag) != "manifest":
        failures.append("META-INF/manifest.xml has an invalid root element")

    topics = list(_iter_topics(root_topic))
    texts = [str(topic.get("title", "")) for topic in topics]
    text_set = set(texts)
    branch_titles = {
        str(topic.get("title", ""))
        for topic in _attached_children(root_topic)
    }
    missing_branches = sorted(
        prefix
        for prefix in REQUIRED_BRANCH_PREFIXES
        if not any(title.startswith(prefix) for title in branch_titles)
    )
    if missing_branches:
        failures.append("missing top-level branches: " + ", ".join(missing_branches))

    missing_text = sorted(REQUIRED_TEXT - text_set)
    if missing_text:
        failures.append("missing required nodes: " + ", ".join(missing_text))

    absolute_paths = sorted(text for text in texts if ABSOLUTE_PATH_RE.search(text))
    if absolute_paths:
        failures.append("mindmap contains absolute paths: " + ", ".join(absolute_paths))

    cli_modules = _cli_modules()
    console_scripts = _console_scripts()
    registered_modules = {
        target.partition(":")[0].removeprefix("pymadagascar.cli.")
        for target in console_scripts.values()
    }
    module_only = set(cli_modules) - registered_modules

    failures.extend(
        _compare_child_inventory(
            topics,
            f"Registered console scripts ({len(console_scripts)})",
            set(console_scripts),
            "registered console scripts",
        )
    )
    failures.extend(
        _compare_child_inventory(
            topics,
            f"Module-only CLI modules ({len(module_only)})",
            module_only,
            "module-only CLI modules",
        )
    )

    snapshot_counts = {
        f"CLI modules: {len(cli_modules)}",
        f"Registered console_scripts: {len(console_scripts)}",
        f"Module-only CLI modules: {len(module_only)}",
        f"Pytest files: {SNAPSHOT_COUNTS['Pytest files']}",
        f"Top-level examples: {SNAPSHOT_COUNTS['Top-level examples']}",
        f"Workflows: {SNAPSHOT_COUNTS['Workflows']} plus "
        f"{SNAPSHOT_COUNTS['Workflow helpers']} helper",
        f"Authoritative Markdown docs: "
        f"{SNAPSHOT_COUNTS['Authoritative Markdown docs']}",
        f"Mindmap artifacts: {SNAPSHOT_COUNTS['Mindmap artifacts']}",
    }
    missing_counts = sorted(snapshot_counts - text_set)
    if missing_counts:
        failures.append(
            "stale or missing frozen-snapshot inventory nodes: "
            + ", ".join(missing_counts)
        )

    try:
        status_text = PROJECT_STATUS.read_text(encoding="utf-8")
        expected_status = _coverage_status_nodes(status_text)
        failures.extend(_validate_current_inventory(status_text))
    except RuntimeError as exc:
        failures.append(str(exc))
    else:
        missing_status = sorted(expected_status - text_set)
        if missing_status:
            failures.append(
                "mindmap coverage baseline disagrees with PROJECT_STATUS.md: "
                + ", ".join(missing_status)
            )
        missing_snapshot_status = sorted(SNAPSHOT_TEST_STATUS - text_set)
        if missing_snapshot_status:
            failures.append(
                "mindmap is missing frozen test baselines: "
                + ", ".join(missing_snapshot_status)
            )

    return failures


def load_root_topic(path: Path = MINDMAP) -> dict[str, Any]:
    """Load the root topic from the modern XMind JSON payload."""
    with zipfile.ZipFile(path) as archive:
        content = json.loads(archive.read("content.json").decode("utf-8"))
    root_topic = content[0]["rootTopic"]
    if not isinstance(root_topic, dict):
        raise TypeError("XMind rootTopic must be an object")
    return root_topic


def _iter_topics(topic: dict[str, Any]) -> Iterator[dict[str, Any]]:
    yield topic
    for child in _attached_children(topic):
        yield from _iter_topics(child)


def _attached_children(topic: dict[str, Any]) -> list[dict[str, Any]]:
    children = topic.get("children", {})
    if not isinstance(children, dict):
        return []
    attached = children.get("attached", [])
    if not isinstance(attached, list):
        return []
    return [child for child in attached if isinstance(child, dict)]


def _legacy_root_title(root: ET.Element) -> str | None:
    for topic in root.iter():
        if _local_name(topic.tag) != "topic":
            continue
        for child in topic:
            if _local_name(child.tag) == "title":
                return child.text
        return None
    return None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _compare_child_inventory(
    topics: list[dict[str, Any]],
    branch_title: str,
    expected: set[str],
    label: str,
) -> list[str]:
    branch = next(
        (topic for topic in topics if topic.get("title") == branch_title),
        None,
    )
    if branch is None:
        return [f"missing {label} branch: {branch_title}"]
    actual = {
        str(child.get("title", ""))
        for child in _attached_children(branch)
    }
    failures: list[str] = []
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        failures.append(f"mindmap is missing {label}: " + ", ".join(missing))
    if extra:
        failures.append(f"mindmap lists stale {label}: " + ", ".join(extra))
    return failures


def _coverage_status_nodes(text: str) -> set[str]:
    full_coverage = _require_match(
        text,
        r"Full Madagascar/alias command surface \| `([^`]+)`",
        "full coverage",
    )
    core_coverage = _require_match(
        text,
        r"Core `system/` \+ `plot/main` command surface \| `([^`]+)`",
        "core coverage",
    )
    direct_coverage = _require_match(
        text,
        r"Direct `system/main` source-backed commands \| `([^`]+)`",
        "direct system/main coverage",
    )
    return {
        f"Full coverage: {full_coverage}",
        f"Core coverage: {core_coverage}",
        f"Direct system/main: {direct_coverage}",
    }


def _validate_current_inventory(text: str) -> list[str]:
    live = {
        "User-facing CLI modules": len(_cli_modules()),
        "Registered `pymada-*` console scripts": len(_console_scripts()),
        "Pytest files": _pytest_file_count(),
        "Top-level example scripts": _top_level_example_count(),
        "Workflow scripts under `examples/my_workflows/`": _workflow_count(),
        "Current docs markdown files": _markdown_doc_count(),
        "Mindmap artifacts": _mindmap_count(),
    }
    patterns = {
        "User-facing CLI modules": r"User-facing CLI modules \| ([0-9]+) \|",
        "Registered `pymada-*` console scripts": (
            r"Registered `pymada-\*` console scripts \| ([0-9]+) \|"
        ),
        "Pytest files": r"Pytest files \| ([0-9]+) \|",
        "Top-level example scripts": r"Top-level example scripts \| ([0-9]+) \|",
        "Workflow scripts under `examples/my_workflows/`": (
            r"Workflow scripts under `examples/my_workflows/` \| "
            r"([0-9]+) plus [0-9]+ helper \|"
        ),
        "Current docs markdown files": (
            r"Current docs markdown files \| ([0-9]+) \|"
        ),
        "Mindmap artifacts": r"Mindmap artifacts \| ([0-9]+) \|",
    }
    failures: list[str] = []
    for label, value in live.items():
        documented = int(_require_match(text, patterns[label], label))
        if documented != value:
            failures.append(
                f"PROJECT_STATUS.md {label} is {documented}, live repository is {value}"
            )

    snapshot_live = {
        "Pytest files": live["Pytest files"],
        "Top-level examples": live["Top-level example scripts"],
        "Workflows": live["Workflow scripts under `examples/my_workflows/`"],
        "Workflow helpers": _workflow_helper_count(),
        "Authoritative Markdown docs": live["Current docs markdown files"],
        "Mindmap artifacts": live["Mindmap artifacts"],
    }
    for label, snapshot_value in SNAPSHOT_COUNTS.items():
        if snapshot_live[label] < snapshot_value:
            failures.append(
                f"live {label} count {snapshot_live[label]} is below frozen "
                f"snapshot {snapshot_value}"
            )
    if snapshot_live != SNAPSHOT_COUNTS and FROZEN_NOTICE not in text:
        failures.append(
            "PROJECT_STATUS.md must declare the intentionally frozen XMind snapshot"
        )
    return failures


def _require_match(text: str, pattern: str, label: str) -> str:
    match = re.search(pattern, text, flags=re.DOTALL)
    if match is None:
        raise RuntimeError(f"could not parse {label} from PROJECT_STATUS.md")
    return match.group(1).strip()


def _cli_modules() -> list[str]:
    return sorted(
        path.stem
        for path in CLI_DIR.glob("*.py")
        if path.name not in {"__init__.py", "base.py"}
    )


def _console_scripts() -> dict[str, str]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    scripts = data.get("project", {}).get("scripts", {})
    if not isinstance(scripts, dict):
        raise RuntimeError("pyproject.toml [project.scripts] must be a table")
    return {str(name): str(target) for name, target in scripts.items()}


def _pytest_file_count() -> int:
    return len(list((ROOT / "tests").glob("test_*.py")))


def _top_level_example_count() -> int:
    return len(list((ROOT / "examples").glob("*.py")))


def _workflow_count() -> int:
    return len(
        [
            path
            for path in (ROOT / "examples" / "my_workflows").glob("*.py")
            if not path.name.startswith("_")
        ]
    )


def _workflow_helper_count() -> int:
    return len(
        [
            path
            for path in (ROOT / "examples" / "my_workflows").glob("_*.py")
            if path.name != "__init__.py"
        ]
    )


def _markdown_doc_count() -> int:
    return len(list((ROOT / "docs").glob("*.md")))


def _mindmap_count() -> int:
    return len(list((ROOT / "docs").glob("*.xmind")))


if __name__ == "__main__":
    raise SystemExit(main())

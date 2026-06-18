"""Safe file-level RSF dataset operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

from pymadagascar.io.rsf import RSFHeader, read_header, write_header


class FileToolError(ValueError):
    """Raised when an RSF file operation is unsupported or unsafe."""


@dataclass(frozen=True)
class CopyResult:
    """Files written by ``copy_rsf_dataset``."""

    header_path: Path
    binary_path: Path


@dataclass(frozen=True)
class RemoveResult:
    """Files selected by ``remove_rsf_dataset``."""

    paths: tuple[Path, ...]
    dry_run: bool
    missing: tuple[Path, ...] = ()


def copy_rsf_dataset(
    input_path: str | Path,
    output_path: str | Path,
    *,
    overwrite: bool = False,
) -> CopyResult:
    """Copy an RSF header and sidecar without rewriting the numeric payload.

    This is a narrow ``sfcp``-style file utility. It preserves the input
    sidecar bytes, writes a copied header, and updates ``in=`` to the output
    sidecar path. Directory copies, recursive copies, streams, and same-file
    copies are intentionally unsupported.
    """

    source_header = _header_path(input_path)
    target_header = _header_path(output_path)
    _assert_regular_input(source_header)
    _assert_regular_output(target_header)

    if source_header.resolve() == target_header.resolve():
        raise FileToolError("input and output headers must be different files")

    header = read_header(source_header)
    source_binary = _binary_path(header, source_header)
    if not source_binary.exists():
        raise FileToolError(f"input sidecar does not exist: {source_binary}")
    if source_binary.is_dir():
        raise FileToolError(f"input sidecar is a directory: {source_binary}")

    target_binary = target_header.with_name(target_header.name + "@")
    _assert_regular_output(target_binary)
    _check_overwrite(target_header, target_binary, overwrite=overwrite)

    target_header.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_binary, target_binary)

    copied_header = header.copy()
    copied_header["in"] = f"./{target_binary.name}"
    write_header(target_header, copied_header)
    return CopyResult(target_header.resolve(), target_binary.resolve())


def remove_rsf_dataset(
    path: str | Path,
    *,
    dry_run: bool = True,
    confirm: bool = False,
    missing_ok: bool = False,
) -> RemoveResult:
    """Remove an RSF header and its sidecar with conservative safety checks.

    By default the function only reports what would be removed. Actual removal
    requires ``dry_run=False`` and ``confirm=True``. Directories, recursive
    removal, root paths, and the current working directory are rejected.
    """

    header_path = _header_path(path)
    _assert_safe_delete_target(header_path)

    if not header_path.exists():
        if missing_ok:
            return RemoveResult((), dry_run=dry_run, missing=(header_path.resolve(),))
        raise FileToolError(f"header does not exist: {header_path}")
    if header_path.is_dir():
        raise FileToolError(f"refusing to remove directory: {header_path}")

    header = read_header(header_path)
    binary_path = _binary_path(header, header_path)
    _assert_safe_delete_target(binary_path)

    existing: list[Path] = []
    missing: list[Path] = []
    for candidate in (binary_path, header_path):
        if candidate.exists():
            if candidate.is_dir():
                raise FileToolError(f"refusing to remove directory: {candidate}")
            existing.append(candidate.resolve())
        else:
            missing.append(candidate.resolve())

    paths = _dedupe_paths(existing)
    if dry_run:
        return RemoveResult(paths, dry_run=True, missing=tuple(missing))

    if not confirm:
        raise FileToolError("actual removal requires confirm=y")

    for target in paths:
        target.unlink()
    return RemoveResult(paths, dry_run=False, missing=tuple(missing))


def _header_path(path: str | Path) -> Path:
    text = str(path).strip()
    if not text:
        raise FileToolError("path must not be empty")
    return Path(text).expanduser()


def _binary_path(header: RSFHeader, header_path: Path) -> Path:
    try:
        return header.binary_path(header_path)
    except Exception as exc:
        raise FileToolError(str(exc)) from exc


def _assert_regular_input(path: Path) -> None:
    if not path.exists():
        raise FileToolError(f"input header does not exist: {path}")
    if path.is_dir():
        raise FileToolError(f"input header is a directory: {path}")


def _assert_regular_output(path: Path) -> None:
    if path.exists() and path.is_dir():
        raise FileToolError(f"output path is a directory: {path}")


def _check_overwrite(header: Path, binary: Path, *, overwrite: bool) -> None:
    existing = [path for path in (header, binary) if path.exists()]
    if existing and not overwrite:
        names = ", ".join(str(path) for path in existing)
        raise FileToolError(f"output already exists; pass overwrite=y to replace: {names}")


def _assert_safe_delete_target(path: Path) -> None:
    resolved = path.expanduser().resolve()
    if resolved == Path.cwd().resolve():
        raise FileToolError(f"refusing to remove the current directory: {path}")
    if resolved == Path(resolved.anchor):
        raise FileToolError(f"refusing to remove filesystem root: {path}")


def _dedupe_paths(paths: list[Path]) -> tuple[Path, ...]:
    seen: set[Path] = set()
    deduped: list[Path] = []
    for path in paths:
        if path not in seen:
            deduped.append(path)
            seen.add(path)
    return tuple(deduped)

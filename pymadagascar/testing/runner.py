"""Command runners for original-Madagascar regression checks."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Mapping, Sequence

from .compare import ComparisonResult, compare_rsf


Command = str | Sequence[str]


@dataclass(frozen=True)
class CommandRun:
    """Captured command execution result."""

    args: Command
    returncode: int
    stdout: str | bytes
    stderr: str
    cwd: str | None = None
    stdin_path: str | None = None
    stdout_path: str | None = None


class CommandRunError(RuntimeError):
    """Raised when a checked command exits with a nonzero status."""

    def __init__(self, result: CommandRun):
        message = (
            f"Command failed with exit code {result.returncode}: "
            f"{_command_display(result.args)}"
        )
        stderr = result.stderr.strip()
        if stderr:
            message += f"\nstderr: {_shorten(stderr)}"
        self.result = result
        super().__init__(message)


class MadagascarNotFoundError(RuntimeError):
    """Raised when original Madagascar command-line programs are unavailable."""


@dataclass(frozen=True)
class CommandComparisonResult:
    """Result of running two commands and comparing their RSF outputs."""

    original: CommandRun
    pymadagascar: CommandRun
    comparison: ComparisonResult

    def __bool__(self) -> bool:
        return bool(self.comparison)

    def assert_ok(self) -> None:
        self.comparison.assert_ok()


def original_madagascar_available(program: str = "sfspike") -> bool:
    """Return True if a Madagascar executable is discoverable."""

    return find_original_madagascar(program) is not None


def find_original_madagascar(
    program: str = "sfspike",
    env: Mapping[str, str] | None = None,
) -> str | None:
    """Find an original Madagascar executable in PATH or RSFROOT/bin."""

    merged_env = _merged_env(env)
    path_parts: list[str] = []
    rsfroot = merged_env.get("RSFROOT")
    if rsfroot:
        path_parts.append(str(Path(rsfroot) / "bin"))
    path_parts.append(merged_env.get("PATH", ""))
    return shutil.which(program, path=os.pathsep.join(path_parts))


def run_original_madagascar(
    cmd: Command,
    cwd: str | os.PathLike[str] | None = None,
    timeout: float | None = 60.0,
    check: bool = True,
    env: Mapping[str, str] | None = None,
    require_program: str = "sfspike",
    stdin_path: str | os.PathLike[str] | None = None,
    stdout_path: str | os.PathLike[str] | None = None,
    decode_stdout: bool = False,
) -> CommandRun:
    """Run an original Madagascar command if Madagascar is installed.

    Original RSF programs normally consume their primary dataset from stdin and
    write their primary dataset to stdout. Use ``stdin_path`` and
    ``stdout_path`` for that protocol. ``decode_stdout`` is intentionally false
    by default because an uncaptured RSF stream may contain arbitrary bytes.

    For compatibility with older tests, sequence commands containing
    ``in=path`` or ``out=path`` are translated to file redirection. New code
    should pass the explicit path arguments instead.
    """

    run_env = _merged_env(env)
    if find_original_madagascar(require_program, run_env) is None:
        raise MadagascarNotFoundError(
            f"Original Madagascar executable {require_program!r} was not found. "
            "Install Madagascar or set RSFROOT/PATH to enable this regression check."
        )
    normalized_cmd, stdin_path, stdout_path = _normalize_madagascar_io(
        cmd,
        stdin_path=stdin_path,
        stdout_path=stdout_path,
    )
    return _run_command(
        normalized_cmd,
        cwd=cwd,
        timeout=timeout,
        check=check,
        env=run_env,
        stdin_path=stdin_path,
        stdout_path=stdout_path,
        decode_stdout=decode_stdout,
    )


def run_madagascar_command(
    program: str,
    args: Sequence[str] = (),
    *,
    params: Mapping[str, Any] | None = None,
    stdin_path: str | os.PathLike[str] | None = None,
    stdout_path: str | os.PathLike[str] | None = None,
    cwd: str | os.PathLike[str] | None = None,
    timeout: float | None = 60.0,
    check: bool = True,
    env: Mapping[str, str] | None = None,
    decode_stdout: bool = False,
) -> CommandRun:
    """Run one upstream Madagascar program with explicit RSF I/O semantics."""

    command = [program, *[str(arg) for arg in args]]
    if params:
        command.extend(f"{key}={_format_parameter(value)}" for key, value in params.items())
    return run_original_madagascar(
        command,
        cwd=cwd,
        timeout=timeout,
        check=check,
        env=env,
        require_program=program,
        stdin_path=stdin_path,
        stdout_path=stdout_path,
        decode_stdout=decode_stdout,
    )


def run_pymadagascar(
    cmd: Command,
    cwd: str | os.PathLike[str] | None = None,
    timeout: float | None = 60.0,
    check: bool = True,
    env: Mapping[str, str] | None = None,
    stdin_path: str | os.PathLike[str] | None = None,
    stdout_path: str | os.PathLike[str] | None = None,
    decode_stdout: bool = True,
) -> CommandRun:
    """Run a pymadagascar command with this project on PYTHONPATH."""

    run_env = _merged_env(env)
    project_root = str(Path(__file__).resolve().parents[2])
    existing_pythonpath = run_env.get("PYTHONPATH")
    run_env["PYTHONPATH"] = (
        project_root
        if not existing_pythonpath
        else project_root + os.pathsep + existing_pythonpath
    )
    return _run_command(
        cmd,
        cwd=cwd,
        timeout=timeout,
        check=check,
        env=run_env,
        stdin_path=stdin_path,
        stdout_path=stdout_path,
        decode_stdout=decode_stdout,
    )


def compare_command_outputs(
    original_cmd: Command,
    pymadagascar_cmd: Command,
    original_output: str | os.PathLike[str],
    pymadagascar_output: str | os.PathLike[str],
    rtol: float = 1e-5,
    atol: float = 1e-8,
    ignore_keys: Sequence[str] | None = ("in",),
    cwd: str | os.PathLike[str] | None = None,
    timeout: float | None = 60.0,
    env: Mapping[str, str] | None = None,
) -> CommandComparisonResult:
    """Run original and Python commands, then compare their RSF output files."""

    original = run_original_madagascar(
        original_cmd,
        cwd=cwd,
        timeout=timeout,
        env=env,
    )
    pymadagascar = run_pymadagascar(
        pymadagascar_cmd,
        cwd=cwd,
        timeout=timeout,
        env=env,
    )
    comparison = compare_rsf(
        original_output,
        pymadagascar_output,
        rtol=rtol,
        atol=atol,
        ignore_keys=ignore_keys,
    )
    return CommandComparisonResult(original, pymadagascar, comparison)


def _run_command(
    cmd: Command,
    cwd: str | os.PathLike[str] | None,
    timeout: float | None,
    check: bool,
    env: Mapping[str, str],
    stdin_path: str | os.PathLike[str] | None = None,
    stdout_path: str | os.PathLike[str] | None = None,
    decode_stdout: bool = False,
) -> CommandRun:
    run_env = dict(env)
    resolved_stdin = _resolve_io_path(stdin_path, cwd)
    resolved_stdout = _resolve_io_path(stdout_path, cwd)
    if resolved_stdout is not None:
        resolved_stdout.parent.mkdir(parents=True, exist_ok=True)
        # Keep Madagascar sidecars beside the explicitly redirected header.
        # This avoids leaking test payloads into a user's global DATAPATH.
        run_env["DATAPATH"] = str(resolved_stdout.parent) + os.sep

    stdin_stream = resolved_stdin.open("rb") if resolved_stdin is not None else None
    stdout_stream = resolved_stdout.open("wb") if resolved_stdout is not None else None
    try:
        completed = subprocess.run(
            cmd,
            cwd=cwd,
            env=run_env,
            timeout=timeout,
            stdin=stdin_stream,
            stdout=stdout_stream if stdout_stream is not None else subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            shell=isinstance(cmd, str),
        )
    finally:
        if stdin_stream is not None:
            stdin_stream.close()
        if stdout_stream is not None:
            stdout_stream.close()

    stdout_bytes = completed.stdout or b""
    stdout: str | bytes = (
        _decode_stream(stdout_bytes) if decode_stdout else stdout_bytes
    )
    result = CommandRun(
        args=cmd,
        returncode=completed.returncode,
        stdout=stdout,
        stderr=_decode_stream(completed.stderr or b""),
        cwd=str(cwd) if cwd is not None else None,
        stdin_path=str(resolved_stdin) if resolved_stdin is not None else None,
        stdout_path=str(resolved_stdout) if resolved_stdout is not None else None,
    )
    if check and result.returncode != 0:
        raise CommandRunError(result)
    return result


def _merged_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    merged = os.environ.copy()
    if env:
        merged.update({str(key): str(value) for key, value in env.items()})
    return merged


def _command_display(cmd: Command) -> str:
    if isinstance(cmd, str):
        return cmd
    return " ".join(cmd)


def _normalize_madagascar_io(
    cmd: Command,
    *,
    stdin_path: str | os.PathLike[str] | None,
    stdout_path: str | os.PathLike[str] | None,
) -> tuple[Command, str | os.PathLike[str] | None, str | os.PathLike[str] | None]:
    if isinstance(cmd, str):
        return cmd, stdin_path, stdout_path

    normalized: list[str] = []
    for item in cmd:
        value = str(item)
        key, separator, path = value.partition("=")
        if separator and key == "in" and stdin_path is None:
            stdin_path = path
            continue
        if separator and key == "out" and stdout_path is None:
            stdout_path = path
            continue
        normalized.append(value)
    return normalized, stdin_path, stdout_path


def _resolve_io_path(
    path: str | os.PathLike[str] | None,
    cwd: str | os.PathLike[str] | None,
) -> Path | None:
    if path is None:
        return None
    resolved = Path(path).expanduser()
    if not resolved.is_absolute() and cwd is not None:
        resolved = Path(cwd) / resolved
    return resolved.resolve()


def _decode_stream(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def _format_parameter(value: Any) -> str:
    if isinstance(value, bool):
        return "y" if value else "n"
    return str(value)


def _shorten(text: str, limit: int = 500) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3] + "..."

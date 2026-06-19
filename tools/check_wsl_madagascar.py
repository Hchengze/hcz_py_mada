"""Probe the optional WSL/Original-Madagascar comparison environment."""

from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
import os
from pathlib import PurePosixPath
import shlex
import subprocess
import sys
from typing import Sequence


DEFAULT_DISTRO = "ubuntu2204"
DEFAULT_USER = os.environ.get("PYMADAGASCAR_WSL_USER", "hcz")
DEFAULT_CONDA_ENV = os.environ.get("PYMADAGASCAR_WSL_CONDA_ENV")
COMMANDS = ("sfspike", "sfmath", "sfwindow", "sfdisfil", "sfattr", "sfdd")


@dataclass(frozen=True)
class ProbeResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class ProbeSummary:
    shell: str
    rsfroot: str
    python: str
    python_version: str
    package_version: str
    found: dict[str, str]
    missing: tuple[str, ...]


def main(argv: list[str] | None = None) -> int:
    options = _parse_args(sys.argv[1:] if argv is None else argv)
    inside_wsl = _inside_wsl()
    location = "current WSL" if inside_wsl else f"WSL distribution {options.distro}"
    print(f"Checking {location} as user {options.user}.")

    if not inside_wsl:
        distro_check = _run(_wsl_prefix(options) + ["true"])
        if distro_check.returncode != 0:
            print("WSL check failed.")
            _print_streams(distro_check)
            list_result = _run(["wsl.exe", "-l", "-v"])
            if list_result.stdout.strip() or list_result.stderr.strip():
                print("Current `wsl -l -v` output:")
                _print_streams(list_result)
            return _finish(
                options.strict,
                "optional WSL probe unavailable; Windows release checks may continue.",
            )

    shell = _select_shell(options, inside_wsl)
    if shell is None:
        return _finish(options.strict, "could not detect an available bash or zsh shell.")

    command = _shell_command(
        shell,
        _probe_script(options.conda_env),
        interactive=shell == "zsh",
    )
    result = _run(command if inside_wsl else _wsl_prefix(options) + command)
    if result.stderr.strip():
        print("Probe stderr:")
        print(result.stderr.rstrip())
    if result.returncode != 0:
        _print_streams(result)
        return _finish(options.strict, f"{shell} environment probe failed.")

    summary = _parse_probe_output(result.stdout, shell)
    _print_summary(summary, options.conda_env)
    failures: list[str] = []
    if summary.missing:
        failures.append("missing Madagascar commands: " + ", ".join(summary.missing))
    if not summary.package_version:
        failures.append("pymadagascar import failed in the selected Python environment")
    if not summary.python:
        failures.append("no Python interpreter was found")

    if failures:
        for failure in failures:
            print(f"- {failure}")
        if shell == "bash":
            print(
                "Hint: if RSFROOT is configured only in ~/.zshrc, retry with "
                "`--shell zsh` or move shared environment exports to a shell-neutral profile."
            )
        return _finish(
            options.strict,
            "optional comparison environment is incomplete; pure Python checks may continue.",
        )

    print("Summary: WSL, the Conda environment, pymadagascar, and selected sf* commands are available.")
    return 0


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="return failure for an incomplete environment")
    parser.add_argument("--distro", default=DEFAULT_DISTRO, help="WSL distribution name")
    parser.add_argument("--user", default=DEFAULT_USER, help="WSL login user")
    parser.add_argument(
        "--shell",
        choices=("auto", "bash", "zsh"),
        default="auto",
        help="login shell used to load RSFROOT/PATH",
    )
    parser.add_argument(
        "--conda-env",
        default=DEFAULT_CONDA_ENV,
        help="Conda environment prefix containing the project Python",
    )
    options = parser.parse_args(list(argv))
    if options.conda_env is None:
        options.conda_env = f"/home/{options.user}/Software/Anaconda/envs/pymadagascar-dev"
    return options


def _inside_wsl() -> bool:
    return bool(os.environ.get("WSL_DISTRO_NAME")) or (
        sys.platform.startswith("linux") and "microsoft" in os.uname().release.lower()
    )


def _wsl_prefix(options: argparse.Namespace) -> list[str]:
    return ["wsl.exe", "-d", options.distro, "-u", options.user, "--"]


def _select_shell(options: argparse.Namespace, inside_wsl: bool) -> str | None:
    if options.shell != "auto":
        return options.shell if _shell_available(options.shell, options, inside_wsl) else None

    detected = _detect_login_shell(options, inside_wsl)
    candidates = [detected, "zsh", "bash"]
    for candidate in candidates:
        if candidate in {"bash", "zsh"} and _shell_available(candidate, options, inside_wsl):
            return candidate
    return None


def _detect_login_shell(options: argparse.Namespace, inside_wsl: bool) -> str | None:
    command = ["getent", "passwd", options.user]
    result = _run(command if inside_wsl else _wsl_prefix(options) + command)
    if result.returncode != 0 or not result.stdout.strip():
        return None
    shell_path = result.stdout.strip().splitlines()[-1].rsplit(":", 1)[-1]
    name = PurePosixPath(shell_path).name
    return name if name in {"bash", "zsh"} else None


def _shell_available(
    shell: str,
    options: argparse.Namespace,
    inside_wsl: bool,
) -> bool:
    command = ["sh", "-lc", f"command -v {shlex.quote(shell)}"]
    result = _run(command if inside_wsl else _wsl_prefix(options) + command)
    return result.returncode == 0 and bool(result.stdout.strip())


def _shell_command(shell: str, script: str, *, interactive: bool) -> list[str]:
    flags = "-lic" if interactive else "-lc"
    payload = base64.b64encode(script.encode("utf-8")).decode("ascii")
    # wsl.exe passes arguments through Windows command-line quoting. Sending
    # the probe body as base64 keeps quotes, newlines, and shell variables
    # intact; the outer login shell still loads the user's RSF environment.
    command = f"printf %s {payload} | base64 --decode | {shell}"
    return [shell, flags, command]


def _probe_script(conda_env: str) -> str:
    conda_bin = str(PurePosixPath(conda_env) / "bin")
    commands = " ".join(shlex.quote(command) for command in COMMANDS)
    return f"""
set +e
if [ -d {shlex.quote(conda_bin)} ]; then
    export PATH={shlex.quote(conda_bin)}:"$PATH"
fi
if [ -n "${{RSFROOT:-}}" ]; then
    export PATH="$RSFROOT/bin:$PATH"
fi
printf 'RSFROOT=%s\\n' "${{RSFROOT:-}}"
printf 'PATH_VALUE=%s\\n' "$PATH"
python_path="$(command -v python || command -v python3 || true)"
printf 'PYTHON=%s\\n' "$python_path"
if [ -n "$python_path" ]; then
    printf 'PYTHON_VERSION=%s\\n' "$("$python_path" --version 2>&1)"
    package_version="$("$python_path" -c 'import pymadagascar; print(pymadagascar.__version__)' 2>/dev/null)"
    printf 'PYMADAGASCAR=%s\\n' "$package_version"
else
    printf 'PYTHON_VERSION=\\n'
    printf 'PYMADAGASCAR=\\n'
fi
for program in {commands}; do
    found="$(command -v "$program" || true)"
    if [ -n "$found" ]; then
        printf 'FOUND %s=%s\\n' "$program" "$found"
    else
        printf 'MISSING %s\\n' "$program"
    fi
done
"""


def _parse_probe_output(text: str, shell: str) -> ProbeSummary:
    values: dict[str, str] = {}
    found: dict[str, str] = {}
    missing: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("FOUND "):
            name, separator, path = line.removeprefix("FOUND ").partition("=")
            if separator and name:
                found[name] = path
        elif line.startswith("MISSING "):
            name = line.removeprefix("MISSING ").strip()
            if name:
                missing.append(name)
        elif "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    for command in COMMANDS:
        if command not in found and command not in missing:
            missing.append(command)
    return ProbeSummary(
        shell=shell,
        rsfroot=values.get("RSFROOT", ""),
        python=values.get("PYTHON", ""),
        python_version=values.get("PYTHON_VERSION", ""),
        package_version=values.get("PYMADAGASCAR", ""),
        found=found,
        missing=tuple(missing),
    )


def _print_summary(summary: ProbeSummary, conda_env: str) -> None:
    print(f"Shell: {summary.shell}")
    print(f"Conda env: {conda_env}")
    print(f"RSFROOT: {summary.rsfroot or '<unset>'}")
    print(f"Python: {summary.python or '<missing>'}")
    print(f"Python version: {summary.python_version or '<unknown>'}")
    print(f"pymadagascar: {summary.package_version or '<import failed>'}")
    for command in COMMANDS:
        value = summary.found.get(command)
        print(f"{command}: {value if value else '<missing>'}")


def _finish(strict: bool, message: str) -> int:
    print(f"Summary: {message}")
    return 1 if strict else 0


def _run(args: Sequence[str]) -> ProbeResult:
    try:
        completed = subprocess.run(
            list(args),
            capture_output=True,
            check=False,
            timeout=30,
        )
    except FileNotFoundError as exc:
        return ProbeResult(1, "", str(exc))
    except subprocess.TimeoutExpired as exc:
        return ProbeResult(
            1,
            _decode_stream(exc.stdout),
            _decode_stream(exc.stderr) or "probe timed out",
        )
    return ProbeResult(
        completed.returncode,
        _decode_stream(completed.stdout),
        _decode_stream(completed.stderr),
    )


def _decode_stream(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return _clean_text(value)
    if value.count(b"\x00") > max(1, len(value) // 8):
        for encoding in ("utf-16le", "utf-16"):
            try:
                return _clean_text(value.decode(encoding, errors="replace"))
            except UnicodeError:
                pass
    return _clean_text(value.decode("utf-8", errors="replace"))


def _clean_text(text: str) -> str:
    cleaned = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    return "".join(
        char if char in {"\n", "\t"} or ord(char) >= 32 else " "
        for char in cleaned
    )


def _print_streams(result: ProbeResult) -> None:
    if result.stdout.strip():
        print("stdout:")
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print("stderr:")
        print(result.stderr.rstrip())


if __name__ == "__main__":
    raise SystemExit(main())

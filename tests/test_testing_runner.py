from pathlib import Path
import sys

import pytest

from pymadagascar.testing.runner import (
    CommandRunError,
    MadagascarNotFoundError,
    original_madagascar_available,
    run_madagascar_command,
    run_original_madagascar,
    run_pymadagascar,
)


def test_run_pymadagascar_adds_project_to_pythonpath() -> None:
    result = run_pymadagascar(
        [
            sys.executable,
            "-c",
            "import pymadagascar; print(pymadagascar.__name__)",
        ]
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "pymadagascar"


def test_binary_stdout_is_not_decoded() -> None:
    result = run_pymadagascar(
        [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'\\xff\\x00RSF')"],
        decode_stdout=False,
    )

    assert result.stdout == b"\xff\x00RSF"


def test_text_stdout_is_decoded_explicitly() -> None:
    result = run_pymadagascar(
        [sys.executable, "-c", "print('plain text')"],
        decode_stdout=True,
    )

    assert result.stdout == "plain text\n"


def test_file_redirection_is_binary_safe(tmp_path: Path) -> None:
    source = tmp_path / "input.bin"
    output = tmp_path / "output.bin"
    source.write_bytes(b"\x00\xffpayload")

    result = run_pymadagascar(
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())",
        ],
        stdin_path=source,
        stdout_path=output,
        decode_stdout=False,
    )

    assert result.stdout == b""
    assert result.stdin_path == str(source.resolve())
    assert result.stdout_path == str(output.resolve())
    assert output.read_bytes() == source.read_bytes()


def test_command_failure_reports_decoded_stderr() -> None:
    with pytest.raises(CommandRunError, match="diagnostic from child") as error:
        run_pymadagascar(
            [
                sys.executable,
                "-c",
                "import sys; sys.stderr.buffer.write(b'diagnostic from child\\xff'); raise SystemExit(7)",
            ]
        )

    assert error.value.result.returncode == 7
    assert "diagnostic from child" in error.value.result.stderr


def test_run_madagascar_command_builds_params_and_redirection(
    tmp_path: Path,
) -> None:
    source = tmp_path / "input.txt"
    output = tmp_path / "output.txt"
    source.write_text("input", encoding="utf-8")

    result = run_madagascar_command(
        sys.executable,
        [
            "-c",
            (
                "import sys; "
                "sys.stdout.write(sys.stdin.read() + '|' + ','.join(sys.argv[1:]))"
            ),
        ],
        params={"flag": True, "count": 2},
        stdin_path=source,
        stdout_path=output,
    )

    assert result.returncode == 0
    assert output.read_text(encoding="utf-8") == "input|flag=y,count=2"


def test_run_original_madagascar_raises_when_required_program_missing() -> None:
    with pytest.raises(MadagascarNotFoundError):
        run_original_madagascar(
            [sys.executable, "-c", "print('not reached')"],
            require_program="definitely_missing_sf_program_for_test",
        )


def test_original_madagascar_regression_can_skip_when_missing(tmp_path: Path) -> None:
    if not original_madagascar_available():
        pytest.skip("Original Madagascar command-line programs are not installed")

    output = tmp_path / "original.rsf"
    run_original_madagascar(
        ["sfspike", "n1=4"],
        cwd=tmp_path,
        stdout_path=output,
    )

    assert output.exists()

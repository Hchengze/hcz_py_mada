from io import BytesIO, StringIO
from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar.cli.base import run_rsf_command
from pymadagascar.cli.info import info_command
from pymadagascar.core.params import MissingParameterError, ParameterParseError, RSFParams
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_key_value_parsing() -> None:
    params = RSFParams(
        [
            "n1=10",
            "d1=0.004",
            'label1="Time sample"',
            "n1=12",
        ],
        prog="sfexample",
    )

    assert params.get_int("n1") == 12
    assert params.get_float("d1") == 0.004
    assert params.get_string("label1") == "Time sample"
    assert params.prog == "sfexample"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("y", True),
        ("yes", True),
        ("true", True),
        ("1", True),
        ("n", False),
        ("no", False),
        ("false", False),
        ("0", False),
    ],
)
def test_bool_parameter_parsing(raw: str, expected: bool) -> None:
    params = RSFParams([f"verb={raw}"])

    assert params.get_bool("verb") is expected


def test_default_values() -> None:
    params = RSFParams([])

    assert params.get_int("n1", 1) == 1
    assert params.get_float("d1", 0.004) == 0.004
    assert params.get_bool("verb", False) is False
    assert params.get_string("label1", "Time") == "Time"
    assert params.get_list("rect", item_type=int, default=[1, 1]) == [1, 1]


def test_missing_parameter_raises() -> None:
    params = RSFParams([])

    with pytest.raises(MissingParameterError, match="clip="):
        params.get_float("clip")


def test_invalid_parameter_error_message() -> None:
    params = RSFParams(["verb=maybe"])

    with pytest.raises(ParameterParseError, match="verb=.*boolean"):
        params.get_bool("verb")


def test_list_parsing_and_madagascar_repeat_style() -> None:
    params = RSFParams(["scale=1,-2,3", "rect=2*4,3x5"])

    assert params.get_list("scale", item_type=float) == [1.0, -2.0, 3.0]
    assert params.get_list("rect", item_type=int) == [4, 4, 5, 5, 5]
    assert params.get_list("scale", item_type=float, count=5) == [1.0, -2.0, 3.0, 3.0, 3.0]


def test_par_file_and_quoted_values(tmp_path: Path) -> None:
    par_file = tmp_path / "test.par"
    par_file.write_text(
        'n1=10 label1="Time sample" verb=y scale=2*1.5,3\n',
        encoding="utf-8",
    )

    params = RSFParams([f"par={par_file}", "n1=20"])

    assert params.get_int("n1") == 20
    assert params.get_string("label1") == "Time sample"
    assert params.get_bool("verb") is True
    assert params.get_list("scale", item_type=float) == [1.5, 1.5, 3.0]


def test_par_file_comments_empty_lines_and_types(tmp_path: Path) -> None:
    par_file = tmp_path / "typed.par"
    par_file.write_text(
        """
# full-line comment

n1=10
d1=0.004     # inline comment
verb=yes
label1="Time # sample"
rect=2*4,3x5
        """,
        encoding="utf-8",
    )

    params = RSFParams([f"par={par_file}"])

    assert params.get_int("n1") == 10
    assert params.get_float("d1") == 0.004
    assert params.get_bool("verb") is True
    assert params.get_string("label1") == "Time # sample"
    assert params.get_list("rect", item_type=int) == [4, 4, 5, 5, 5]


def test_par_file_repeated_keys_last_value_wins(tmp_path: Path) -> None:
    par_file = tmp_path / "repeat.par"
    par_file.write_text(
        """
n1=5
n1=6
label1=Initial
label1="Final label"
        """,
        encoding="utf-8",
    )

    params = RSFParams([f"par={par_file}"])

    assert params.get_int("n1") == 6
    assert params.get_string("label1") == "Final label"


def test_par_file_order_matches_madagascar_left_to_right(tmp_path: Path) -> None:
    par_file = tmp_path / "override.par"
    par_file.write_text("n1=30 label1=Par\n", encoding="utf-8")

    command_line_overrides_par = RSFParams([f"par={par_file}", "n1=40"])
    par_overrides_previous_command_line = RSFParams(["n1=40", f"par={par_file}"])

    assert command_line_overrides_par.get_int("n1") == 40
    assert par_overrides_previous_command_line.get_int("n1") == 30
    assert par_overrides_previous_command_line.get_string("label1") == "Par"


def test_missing_par_file_raises_parse_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.par"

    with pytest.raises(ParameterParseError, match="Cannot open par file"):
        RSFParams([f"par={missing}"])


def test_cli_subprocess_accepts_par_file(tmp_path: Path) -> None:
    par_file = tmp_path / "spike.par"
    output = tmp_path / "spike.rsf"
    par_file.write_text(
        'n1=4 k1=2 label1="From par" d1=0.25\n',
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not env.get("PYTHONPATH")
        else str(PROJECT_ROOT) + os.pathsep + env["PYTHONPATH"]
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pymadagascar.cli.spike",
            f"par={par_file}",
            "n1=5",
            f"out={output}",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    rsf = read_rsf(output)
    assert rsf.header.dimensions == (5,)
    assert rsf.header["label1"] == "From par"
    assert rsf.header["d1"] == "0.25"
    np.testing.assert_array_equal(rsf.data, np.array([0, 1, 0, 0, 0], dtype=np.float32))


def test_positional_input_output_paths() -> None:
    params = RSFParams(["input.rsf", "output.rsf"])

    assert params.input_path() == "input.rsf"
    assert params.output_path() == "output.rsf"


def test_in_out_parameters_override_positionals() -> None:
    params = RSFParams(["pos_in.rsf", "pos_out.rsf", "in=kw_in.rsf", "out=kw_out.rsf"])

    assert params.input_path() == "kw_in.rsf"
    assert params.output_path() == "kw_out.rsf"


def test_stdin_stdout_simulation() -> None:
    stdin = BytesIO(b"abc")
    stdout = BytesIO()
    params = RSFParams([], stdin=stdin, stdout=stdout)

    with params.open_input() as stream:
        assert stream.read() == b"abc"

    with params.open_output() as stream:
        stream.write(b"xyz")

    assert stdout.getvalue() == b"xyz"


def test_open_input_output_files(tmp_path: Path) -> None:
    in_file = tmp_path / "in.bin"
    out_file = tmp_path / "out.bin"
    in_file.write_bytes(b"data")
    params = RSFParams([str(in_file), str(out_file)])

    with params.open_input() as stream:
        assert stream.read() == b"data"

    with params.open_output() as stream:
        stream.write(b"copy")

    assert out_file.read_bytes() == b"copy"


def test_run_rsf_command_reports_parameter_errors() -> None:
    stderr = StringIO()

    def command(params: RSFParams) -> None:
        params.get_int("n1")

    code = run_rsf_command(command, [], prog="sfmissing", stderr=stderr)

    assert code == 2
    assert "sfmissing: Missing required parameter: n1=" in stderr.getvalue()


def test_run_rsf_command_help() -> None:
    stdout = StringIO()

    code = run_rsf_command(
        lambda params: None,
        ["--help"],
        prog="sfhelp",
        description="Help text example.",
        stdout=stdout,
    )

    assert code == 0
    assert "Usage: sfhelp" in stdout.getvalue()
    assert "Help text example." in stdout.getvalue()
    assert "key=value" in stdout.getvalue()


def test_info_command_example(tmp_path: Path) -> None:
    data = np.arange(6, dtype=np.float32).reshape(2, 3)
    path = tmp_path / "example.rsf"
    write_rsf(
        path,
        data,
        RSFHeader({"label1": "Time", "unit1": "s", "label2": "Trace"}),
    )
    params = RSFParams([str(path)])

    text = info_command(params)

    assert f"path: {path}" in text
    assert "data_format: native_float" in text
    assert "dimensions: n1=3 n2=2" in text
    assert "numpy_shape: 2x3" in text
    assert "axis1 label=Time unit=s" in text

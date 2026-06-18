from pathlib import Path

import numpy as np
import pytest

from pymadagascar.cli.math import main as math_main
from pymadagascar.core.axis import Axis
from pymadagascar.generic.math import MathExpressionError, math_rsf, safe_eval_math
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.testing.compare import assert_rsf_allclose
from pymadagascar.testing.runner import original_madagascar_available, run_original_madagascar


def test_api_1d_coordinate_expression() -> None:
    result = math_rsf(
        "x1",
        axes=[Axis(n=5, o=1.0, d=0.5, label="Time", unit="s")],
    )

    np.testing.assert_allclose(
        result.data,
        np.array([1.0, 1.5, 2.0, 2.5, 3.0], dtype=np.float32),
    )
    assert result.header.dimensions == (5,)
    assert result.header["o1"] == "1"
    assert result.header["d1"] == "0.5"
    assert result.header["label1"] == "Time"
    assert result.header["unit1"] == "s"
    assert result.header["data_format"] == "native_float"


def test_api_2d_coordinate_expression_broadcasts_in_rsf_order() -> None:
    result = math_rsf(
        "x1 + x2",
        axes=[
            Axis(n=4, o=0.0, d=1.0, label="Fast"),
            Axis(n=3, o=10.0, d=10.0, label="Slow"),
        ],
    )
    expected = np.array(
        [
            [10.0, 11.0, 12.0, 13.0],
            [20.0, 21.0, 22.0, 23.0],
            [30.0, 31.0, 32.0, 33.0],
        ],
        dtype=np.float32,
    )

    assert result.data.shape == (3, 4)
    np.testing.assert_allclose(result.data, expected)
    assert result.header.dimensions == (4, 3)


def test_api_input_data_expression_inherits_header() -> None:
    data = np.arange(6, dtype=np.float32).reshape(2, 3)
    header = RSFHeader(
        {
            "n1": 3,
            "n2": 2,
            "o1": 1.0,
            "d1": 0.25,
            "label1": "Time",
            "unit1": "s",
            "label": "Amplitude",
        }
    )

    result = math_rsf("input*2 + data", header=header, data=data)

    np.testing.assert_array_equal(result.data, data * 3)
    assert result.header["label1"] == "Time"
    assert result.header["unit1"] == "s"
    assert result.header["label"] == "Amplitude"


def test_api_math_functions_and_constants() -> None:
    result = math_rsf("sin(pi*x1/2) + cos(0) + sqrt(abs(x1-2)) + log(e)", shape=(5,))
    x1 = np.arange(5, dtype=np.float64)
    expected = np.sin(np.pi * x1 / 2.0) + 1.0 + np.sqrt(np.abs(x1 - 2.0)) + 1.0

    np.testing.assert_allclose(result.data, expected.astype(np.float32), rtol=1e-6)


def test_api_power_accepts_madagascar_caret() -> None:
    result = math_rsf("x1^2", shape=(4,))

    np.testing.assert_array_equal(result.data, np.array([0, 1, 4, 9], dtype=np.float32))


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('echo bad')",
        "open('x')",
        "np.sin(x1)",
        "[x1]",
        "x1.__class__",
        "lambda x: x",
    ],
)
def test_safe_eval_blocks_unsafe_or_unsupported_expressions(expression: str) -> None:
    with pytest.raises(MathExpressionError):
        safe_eval_math(expression, {"x1": np.arange(3, dtype=np.float32)})


def test_safe_eval_blocks_unknown_function() -> None:
    with pytest.raises(MathExpressionError, match="unsupported math function"):
        safe_eval_math("where(x1)", {"x1": np.arange(3, dtype=np.float32)})


def test_cli_coordinate_expression_writes_rsf(tmp_path: Path) -> None:
    output = tmp_path / "math.rsf"

    code = math_main(["n1=5", "o1=1", "d1=0.5", "output=x1", "out=" + str(output)])
    result = read_rsf(output)

    assert code == 0
    np.testing.assert_allclose(
        result.data,
        np.array([1.0, 1.5, 2.0, 2.5, 3.0], dtype=np.float32),
    )
    assert result.header["o1"] == "1"
    assert result.header["d1"] == "0.5"


def test_cli_input_data_expression(tmp_path: Path) -> None:
    input_file = tmp_path / "input.rsf"
    output_file = tmp_path / "output.rsf"
    data = np.arange(6, dtype=np.float32).reshape(2, 3)
    write_rsf(
        input_file,
        data,
        RSFHeader({"o1": 1.0, "d1": 0.5, "label1": "Sample", "unit1": "s"}),
    )

    code = math_main([str(input_file), "output=input*2", "out=" + str(output_file)])
    result = read_rsf(output_file)

    assert code == 0
    np.testing.assert_array_equal(result.data, data * 2)
    assert result.header["label1"] == "Sample"
    assert result.header["unit1"] == "s"


def test_cli_reports_invalid_expression(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    output = tmp_path / "bad.rsf"

    code = math_main(["n1=4", "output=__import__('os')", "out=" + str(output)])

    assert code == 2
    assert "unsupported math function" in capsys.readouterr().err
    assert not output.exists()


def test_cli_requires_out_not_output_path(capsys: pytest.CaptureFixture[str]) -> None:
    code = math_main(["n1=4", "output=x1"])

    assert code == 2
    assert "Missing required parameter: out=" in capsys.readouterr().err


def test_cli_original_sfmath_comparison_when_available(tmp_path: Path) -> None:
    if not original_madagascar_available("sfmath"):
        pytest.skip("Original Madagascar sfmath is not installed")

    original = tmp_path / "original.rsf"
    python = tmp_path / "python.rsf"
    run_original_madagascar(
        ["sfmath", "n1=5", "o1=1", "d1=0.5", "output=x1", "out=original.rsf"],
        cwd=tmp_path,
        require_program="sfmath",
    )
    assert math_main(["n1=5", "o1=1", "d1=0.5", "output=x1", "out=" + str(python)]) == 0

    assert_rsf_allclose(original, python, ignore_keys={"in", "x1"})

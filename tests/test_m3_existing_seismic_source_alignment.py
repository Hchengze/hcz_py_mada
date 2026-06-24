from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from pymadagascar import RSFData
from pymadagascar.cli.agc import main as agc_main
from pymadagascar.cli.slant import main as slant_main
from pymadagascar.cli.vscan import main as vscan_main
from pymadagascar.io.rsf import RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic.agc import AGCError, agc_rsf


def _gather_header(nt: int = 64, nx: int = 5, *, dt: float = 0.004) -> RSFHeader:
    return RSFHeader(
        {
            "n1": nt,
            "o1": 0.0,
            "d1": dt,
            "label1": "Time",
            "unit1": "s",
            "n2": nx,
            "o2": 0.0,
            "d2": 50.0,
            "label2": "Offset",
            "unit2": "m",
        }
    )


def _hyperbolic_gather(nt: int = 101, nh: int = 5, velocity: float = 2000.0) -> np.ndarray:
    dt = 0.004
    times = dt * np.arange(nt, dtype=np.float64)
    offsets = 150.0 * np.arange(nh, dtype=np.float64)
    data = np.zeros((nh, nt), dtype=np.float32)
    for ih, offset in enumerate(offsets):
        arrival = np.sqrt(0.24 * 0.24 + (offset / velocity) ** 2)
        data[ih] = np.exp(-0.5 * ((times - arrival) / 0.012) ** 2)
    return data


def test_agc_source_alignment_metadata_and_no_inplace(tmp_path: Path) -> None:
    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "agc.rsf"
    data = np.full((2, 8), 2.0, dtype=np.float32)
    write_rsf(input_path, data, _gather_header(nt=8, nx=2, dt=0.1))

    agc_rsf(input_path, output_path, rect=0.2, axis=1)
    loaded = read_rsf(output_path)
    original = read_rsf(input_path)

    np.testing.assert_allclose(loaded.data, np.ones_like(data), atol=1e-6)
    np.testing.assert_array_equal(original.data, data)
    assert loaded.header["agc_source"] == "../src-master/system/generic/Magc.c"
    assert loaded.header["agc_madagascar_subset"] == "local_rms_one_axis"
    assert loaded.header["agc_window_samples"] == "2"


def test_agc_console_script_help_and_invalid_params(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pymadagascar.cli.agc", "--help"],
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0
    assert "pymada-agc" in result.stdout

    input_path = tmp_path / "input.rsf"
    output_path = tmp_path / "bad.rsf"
    write_rsf(input_path, np.ones((2, 8), dtype=np.float32), _gather_header(nt=8, nx=2))
    with pytest.raises(AGCError, match="rect= must be positive"):
        agc_rsf(input_path, output_path, rect=0.0)
    assert agc_main([str(input_path), "out=" + str(output_path), "rect=0"]) == 2


def test_slant_cli_alias_and_rsfdata_chain(tmp_path: Path) -> None:
    input_path = tmp_path / "gather.rsf"
    output_path = tmp_path / "slant.rsf"
    data = np.ones((5, 64), dtype=np.float32)
    write_rsf(input_path, data, _gather_header())

    code = slant_main(
        [
            str(input_path),
            "out=" + str(output_path),
            "p0=-0.001",
            "dp=0.0005",
            "np=5",
        ]
    )
    panel = read_rsf(output_path)

    assert code == 0
    assert panel.header.dimensions == (64, 5)
    assert panel.header["radon_madagascar_reference"] == "Mslant.c/slant.c small subset"
    assert panel.header["radon_sfradon_equivalence"] == "not_sfradon"

    rsf = RSFData(data, _gather_header())
    chained = rsf.slant(pmin=-0.001, pmax=0.001, dp=0.0005)
    np.testing.assert_array_equal(rsf.numpy(), data)
    assert chained.header.dimensions == (64, 5)


def test_vscan_cli_alias_and_rsfdata_chain(tmp_path: Path) -> None:
    input_path = tmp_path / "cmp.rsf"
    output_path = tmp_path / "vscan.rsf"
    data = _hyperbolic_gather()
    write_rsf(input_path, data, _gather_header(nt=101, nx=5))

    code = vscan_main(
        [
            str(input_path),
            "out=" + str(output_path),
            "v0=1800",
            "dv=100",
            "nv=5",
            "half=n",
            "stretch=0",
        ]
    )
    panel = read_rsf(output_path)

    assert code == 0
    assert panel.header.dimensions == (101, 5)
    assert panel.header["semblance_reference_source"] == "../src-master/system/seismic/Mvscan.c"
    assert panel.header["semblance_madagascar_subset"] == "velocity_panel_semblance_only"

    rsf = RSFData(data, _gather_header(nt=101, nx=5))
    chained = rsf.vscan(vmin=1800.0, vmax=2200.0, dv=100.0, half=False, stretch=None)
    np.testing.assert_array_equal(rsf.numpy(), data)
    assert chained.header.dimensions == (101, 5)

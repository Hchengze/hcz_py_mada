from __future__ import annotations

from argparse import Namespace
import base64

from tools import check_wsl_madagascar as probe


def _options(**updates: object) -> Namespace:
    values = {
        "strict": False,
        "distro": "ubuntu2204",
        "user": "hcz",
        "shell": "auto",
        "conda_env": "/opt/conda/envs/pymadagascar-dev",
    }
    values.update(updates)
    return Namespace(**values)


def test_parse_probe_output_keeps_command_names() -> None:
    summary = probe._parse_probe_output(
        "\n".join(
            [
                "RSFROOT=/opt/rsf",
                "PYTHON=/opt/conda/bin/python",
                "PYTHON_VERSION=Python 3.11.9",
                "PYMADAGASCAR=0.1.0",
                "FOUND sfspike=/opt/rsf/bin/sfspike",
                "MISSING sfmath",
            ]
        ),
        "zsh",
    )

    assert summary.rsfroot == "/opt/rsf"
    assert summary.found["sfspike"] == "/opt/rsf/bin/sfspike"
    assert "sfmath" in summary.missing
    assert "" not in summary.missing


def test_probe_script_adds_conda_and_rsf_paths() -> None:
    script = probe._probe_script("/opt/conda/envs/dev")

    assert "/opt/conda/envs/dev/bin" in script
    assert 'export PATH="$RSFROOT/bin:$PATH"' in script
    assert "import pymadagascar" in script
    for command in probe.COMMANDS:
        assert command in script


def test_shell_command_transports_script_as_base64() -> None:
    script = 'printf "RSFROOT=%s\\n" "$RSFROOT"\n'
    command = probe._shell_command("zsh", script, interactive=True)

    assert command[:2] == ["zsh", "-lic"]
    payload = command[2].split()[2]
    assert base64.b64decode(payload).decode("utf-8") == script


def test_shell_detection_prefers_login_shell(monkeypatch) -> None:
    options = _options()
    monkeypatch.setattr(probe, "_detect_login_shell", lambda *_args: "zsh")
    monkeypatch.setattr(probe, "_shell_available", lambda shell, *_args: shell == "zsh")

    assert probe._select_shell(options, inside_wsl=False) == "zsh"


def test_windows_wsl_prefix_uses_executable_name() -> None:
    assert probe._wsl_prefix(_options()) == [
        "wsl.exe",
        "-d",
        "ubuntu2204",
        "-u",
        "hcz",
        "--",
    ]


def test_non_strict_missing_wsl_is_non_blocking(monkeypatch, capsys) -> None:
    monkeypatch.setattr(probe, "_inside_wsl", lambda: False)
    monkeypatch.setattr(
        probe,
        "_run",
        lambda _args: probe.ProbeResult(1, "", "WSL unavailable"),
    )

    assert probe.main([]) == 0
    assert "optional WSL probe unavailable" in capsys.readouterr().out


def test_strict_missing_wsl_fails(monkeypatch) -> None:
    monkeypatch.setattr(probe, "_inside_wsl", lambda: False)
    monkeypatch.setattr(
        probe,
        "_run",
        lambda _args: probe.ProbeResult(1, "", "WSL unavailable"),
    )

    assert probe.main(["--strict"]) == 1


def test_complete_direct_probe_passes(monkeypatch, capsys) -> None:
    output = [
        "RSFROOT=/opt/rsf",
        "PYTHON=/opt/conda/bin/python",
        "PYTHON_VERSION=Python 3.11.9",
        "PYMADAGASCAR=0.1.0",
    ]
    output.extend(f"FOUND {name}=/opt/rsf/bin/{name}" for name in probe.COMMANDS)
    monkeypatch.setattr(probe, "_inside_wsl", lambda: True)
    monkeypatch.setattr(probe, "_select_shell", lambda *_args: "zsh")
    monkeypatch.setattr(
        probe,
        "_run",
        lambda _args: probe.ProbeResult(0, "\n".join(output), ""),
    )

    assert probe.main(["--strict", "--shell", "zsh"]) == 0
    assert "selected sf* commands are available" in capsys.readouterr().out

# WSL Madagascar Testing

This document describes how to use the optional original Madagascar
installation inside WSL distribution `ubuntu2204` for upstream comparison tests.
The Windows host can still run all pure Python tests without Madagascar.

## Scope

- WSL distribution name: `ubuntu2204`.
- Original Madagascar comparison tests are optional.
- Pure Python tests must not depend on Madagascar, WSL, RSFROOT, or `sf*`
  commands.
- Older Madagascar versions are useful as reference checks, but version-specific
  behavior differences should be documented rather than hidden by changing pure
  Python tests.

## Check WSL From PowerShell

List available WSL distributions:

```powershell
wsl -l -v
```

Enter the expected distribution:

```powershell
wsl -d ubuntu2204
```

Run the lightweight repository check from Windows PowerShell:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe tools\check_wsl_madagascar.py
```

This check only probes WSL, selected `sf*` commands, `RSFROOT`, and WSL Python.
It does not run pytest and does not modify the repository.

## Check Madagascar Inside WSL

Inside `ubuntu2204`, check representative commands:

```bash
which sfspike
which sfmath
which sfwindow
which sfattr
which sfdd
```

Check `RSFROOT`:

```bash
echo $RSFROOT
```

If `RSFROOT` is set but `sf*` commands are not on `PATH`, prepend the
Madagascar binary directory:

```bash
export PATH="$RSFROOT/bin:$PATH"
```

Then re-check:

```bash
which sfspike
which sfmath
which sfwindow
which sfattr
which sfdd
```

If `RSFROOT` is empty but `which sfspike` succeeds, the comparison tests can
still run because command discovery uses `PATH`.

## Enter The Repository In WSL

Use the Linux path for the Windows workspace. A typical path is:

```bash
cd /mnt/e/HczDocument/BaiduDisk/BaiduSyncdisk/HCZ_work/CodexProject/HCZ_madagascar/hcz_mada
```

If the path differs, locate it from WSL with `ls /mnt/e` or clone/copy the repo
to a native Linux path. Avoid mixing Windows Python with Linux `sf*` binaries;
run Python and Madagascar commands inside the same WSL distribution.

## Install pymadagascar Editable In WSL

From the `hcz_mada` directory inside WSL:

```bash
python -m pip install -e ".[test]" --no-build-isolation
```

If the shell or pip version has trouble with extras, install in two steps:

```bash
python -m pip install -e . --no-build-isolation
python -m pip install pytest matplotlib
```

Do not build C++ for this optional comparison workflow unless a separate hybrid
task explicitly asks for it.

## Run Tests In WSL

Run pure Python pytest:

```bash
python -m pytest -q -m "not original_madagascar"
```

Run only original Madagascar comparison tests:

```bash
python -m pytest -q -rs -m original_madagascar
```

Run the full suite:

```bash
python -m pytest -q -rs
```

Use `-rs` so missing commands and version-specific skips or failures are
visible.

## Older Madagascar Versions

The `ubuntu2204` Madagascar installation may be older than the source snapshot
audited in this repository. Possible differences include:

- Different accepted parameters or aliases for an `sf*` command.
- Different text formatting for tools such as `sfin`, `sfattr`, `sfget`, or
  `sfdisfil`.
- Different FFT normalization, frequency-axis conventions, or filter edge
  behavior.
- Different behavior around zero denominators, non-positive coordinates, NaNs,
  endian/ascii formats, or trace/header metadata.
- Missing newer commands or commands installed under a different name.

Record these as version differences when the local Python behavior is
documented, deterministic, and pure Python tests still pass. Do not weaken pure
Python tests because a WSL comparison differs.

## What To Record

When running WSL comparison tests, record:

- Output of `wsl -l -v`.
- Output of `tools/check_wsl_madagascar.py`.
- `echo $RSFROOT`.
- `which sfspike sfmath sfwindow sfattr sfdd`.
- Python path and version used in WSL.
- The exact pytest command and result.
- Any command-specific version differences, including the upstream command
  version or build path if known.

## Hard Rules

- Do not make original Madagascar a hard dependency.
- Do not change pure Python tests to require WSL or `sf*`.
- Do not convert real pure Python failures into skips.
- Do not edit original Madagascar source.
- Do not use WSL comparison differences as a reason to register new commands,
  add algorithms, or start a migration batch.

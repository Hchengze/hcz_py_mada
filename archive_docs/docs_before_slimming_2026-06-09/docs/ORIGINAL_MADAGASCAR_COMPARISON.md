# Original Madagascar Comparison Tests

This project is usable without an original Madagascar installation. Original
Madagascar is only needed for optional compatibility checks that compare
`pymadagascar` output with upstream `sf*` command-line programs.

## When Original Madagascar Is Needed

Install or enable original Madagascar when you want to verify that a migrated
command agrees with upstream behavior on small deterministic fixtures. This is
especially useful before changing RSF I/O, CLI parameter handling, generic array
commands, FFT/filter behavior, or seismic prototypes.

Pure Python unit tests, RSF roundtrip tests, local CLI smoke tests, examples, and
Python fallback behavior must continue to pass when original Madagascar is not
installed.

## Check Commands On PATH

The current optional comparison suite uses commands such as:

- `sfspike`, `sfmath`, `sfwindow`
- `sfin`, `sfattr`, `sfput`
- `sfcat`, `sftransp`, `sfdd`
- `sfscale`, `sfconv`, `sffft1`, `sfbandpass`
- `sfnmo`, `sfvscan`, `sfslant`, `sfkirchnew`
- `sfpad`, `sfspray`, `sfpow`, `sfstack`, `sfsegyread`

PowerShell:

```powershell
Get-Command sfspike, sfmath, sfwindow, sfin, sfattr, sfput
```

Linux or WSL:

```bash
command -v sfspike sfmath sfwindow sfin sfattr sfput
```

If a command is missing, tests that need that command will skip with a reason
such as `Original Madagascar sfspike is not installed`.

## RSFROOT And PATH

`pymadagascar.testing.runner.find_original_madagascar()` searches both `PATH`
and `$RSFROOT/bin`. If `sf*` programs are already on `PATH`, `RSFROOT` is not
required for these tests. If they are not on `PATH`, set `RSFROOT` and prepend
its `bin` directory.

PowerShell:

```powershell
$env:RSFROOT = "C:\path\to\madagascar"
$env:PATH = "$env:RSFROOT\bin;$env:PATH"
Get-Command sfspike
```

Linux or WSL:

```bash
export RSFROOT=/path/to/madagascar
export PATH="$RSFROOT/bin:$PATH"
command -v sfspike
```

Use the path that contains the installed Madagascar `bin` directory, not the
local `src-master` source tree.

## Run Tests

Run the full suite:

```powershell
python -m pytest -q -rs
```

Run only original Madagascar comparison tests:

```powershell
python -m pytest -q -rs -m original_madagascar
```

Run everything except original Madagascar comparison tests:

```powershell
python -m pytest -q -m "not original_madagascar"
```

Show marker help:

```powershell
python -m pytest --markers
```

Show skip reasons:

```powershell
python -m pytest -q -rs
```

The `-rs` option is the easiest way to confirm whether skips are caused by
missing original `sf*` commands, missing C++ extension support, or another
documented optional dependency.

## Marker Policy

Markers are registered in `pytest.ini`:

- `original_madagascar`: optional comparisons against upstream `sf*` commands.
- `slow`: intentionally slower tests.
- `hybrid`: optional C++/hybrid backend tests.
- `cli`: command-line or subprocess CLI tests.
- `prototype`: prototype or partial module tests.

`tests/conftest.py` applies markers by stable naming conventions:

- Test names starting with `test_original_` or `test_cli_original_` are marked
  `original_madagascar`.
- Files named `test_hybrid_*.py` are marked `hybrid`.
- Files named `test_cli_*.py`, or test names containing `_cli`, are marked
  `cli`.
- Current prototype module test files are marked `prototype`.

New optional comparison tests should follow this naming pattern:

```python
def test_original_sfxxx_comparison_when_available(tmp_path):
    if not original_madagascar_available("sfxxx"):
        pytest.skip("Original Madagascar sfxxx is not installed")
    ...
```

Do not mark a pure Python failure as skipped. Optional skips are only for
environment-dependent comparisons, not for broken local behavior.

## Windows Notes

- Use PowerShell `Get-Command sfspike` to verify executable discovery.
- Madagascar may be easier to run through WSL than native Windows, depending on
  how it was built.
- Keep paths quoted when they contain spaces.
- If using WSL Madagascar, run pytest from WSL too; do not mix Windows Python
  with Linux `sf*` binaries.

## Linux Notes

- Source your Madagascar environment setup before running pytest.
- Confirm that `$RSFROOT/bin` is before unrelated tools on `PATH`.
- Use `python -m pytest -q -rs -m original_madagascar` after environment setup.

## WSL Notes

- Use Linux paths inside WSL, for example `/home/user/madagascar`.
- Run both Python and `sf*` commands inside the same WSL distribution.
- Avoid crossing Windows and WSL path conventions in RSF `in=` headers.
- The known optional comparison distribution for this workstation is
  `ubuntu2204`.
- From Windows PowerShell, run `wsl -l -v` to confirm the distribution and
  `D:\HczApp\Anaconda\envs\mywork\python.exe tools\check_wsl_madagascar.py`
  to probe WSL Madagascar command availability.
- Enter WSL with `wsl -d ubuntu2204`, then run pytest from inside the WSL
  repository path, not from Windows Python.

Detailed WSL instructions live in `docs/WSL_MADAGASCAR_TESTING.md`.

## WSL ubuntu2204 Optional Workflow

PowerShell discovery:

```powershell
wsl -l -v
wsl -d ubuntu2204
D:\HczApp\Anaconda\envs\mywork\python.exe tools\check_wsl_madagascar.py
```

Inside WSL:

```bash
which sfspike
which sfmath
which sfwindow
which sfattr
which sfdd
echo $RSFROOT
export PATH="$RSFROOT/bin:$PATH"
cd /mnt/e/HczDocument/BaiduDisk/BaiduSyncdisk/HCZ_work/CodexProject/HCZ_madagascar/hcz_mada
python -m pip install -e ".[test]" --no-build-isolation
python -m pytest -q -rs -m original_madagascar
python -m pytest -q -rs
```

If the WSL Madagascar version is older than the audited source snapshot, record
behavior differences as version differences. Examples include accepted
parameters, alias availability, text formatting, FFT/filter conventions, zero
division behavior, and trace/header metadata behavior. Do not make pure Python
tests depend on those differences and do not silently skip pure Python failures.

## Why Missing Madagascar Should Not Fail Pure Python Tests

The package target is a Python-friendly RSF and geophysics toolkit with optional
upstream comparison tests. A user should be able to install and use the pure
Python package locally without building or installing the full original
Madagascar ecosystem. Missing `sf*` programs therefore skip only the tests whose
purpose is upstream compatibility validation.

Older original Madagascar builds, including the optional WSL `ubuntu2204`
installation, are reference comparators rather than the source of truth for the
pure Python baseline. A mismatch may be a real pymadagascar bug, an upstream
version difference, or an intentionally documented Python subset. Record which
case it is before changing code or tests.

# pymadagascar

pymadagascar is a Python-friendly local toolkit for RSF data I/O, selected
Madagascar-style command-line workflows, NumPy-backed signal processing, and
small geophysical examples.

It is not a complete Madagascar clone. Pure Python is the supported default;
the existing C++ extension is optional acceleration with NumPy fallback.

## Local Install

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install -e ".[test]" --no-build-isolation
```

The default wheel skips CMake and does not require Ninja or a C++ compiler.

## Verify

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pytest -q
D:\HczApp\Anaconda\envs\mywork\python.exe tools/check_release.py
```

Start with [docs/README.md](docs/README.md) for the current authoritative
documentation, status, compatibility limits, and roadmap.

## Optional C++

Install the optional build tools first, then explicitly enable the CMake wheel:

```powershell
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install -e ".[cpp]" --no-build-isolation
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install -e . --no-build-isolation --config-settings=wheel.cmake=true --config-settings=cmake.define.PYMADAGASCAR_BUILD_CPP=ON
```

This path also requires a working C++17 compiler. It is not required for the
pure Python release baseline.

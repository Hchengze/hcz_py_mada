# Building pymadagascar-hybrid

This project skeleton uses:

- pybind11 for Python/C++ bindings;
- CMake for native build configuration;
- scikit-build-core as the PEP 517 build backend;
- NumPy arrays through `pybind11::array_t`.

The current C++ extension exposes these small kernels:

- `add_arrays_cpp(a, b)`
- `scale_array_cpp(a, scale)`
- `batch_xcorr_cpp(traces, mode="full")`

FFT, NMO, semblance, finite difference, and imaging kernels are not implemented
in C++ yet.

## Install In Editable Mode

From the `hcz_mada` directory:

```powershell
python -m pip install -U pip
python -m pip install -e .[test]
```

By default, the package installs with the C++ extension disabled. This keeps the
pure Python and NumPy fallback package installable on machines without a C++
compiler.

To explicitly build the optional C++ extension:

```powershell
python -m pip install -e .[test] --config-settings=cmake.define.PYMADAGASCAR_BUILD_CPP=ON
```

If the extension builds successfully, Python can import `pymadagascar._core`.
If it is not built, tests and scripts can still use the NumPy fallback wrappers.

## Disable The C++ Extension At Runtime

Set:

```powershell
$env:PYMADAGASCAR_DISABLE_CPP = "1"
```

On Linux/macOS:

```bash
export PYMADAGASCAR_DISABLE_CPP=1
```

The Python wrappers will then skip importing `pymadagascar._core` and use NumPy.

## Check The Active Backend

```python
from pymadagascar.hybrid import backend_name, cpp_available, last_backend
from pymadagascar.hybrid import add_arrays_cpp, batch_xcorr_cpp, last_xcorr_backend

print(cpp_available())
print(backend_name())
result = add_arrays_cpp([1, 2], [3, 4])
print(last_backend())  # "cpp" or "numpy"
xcorr = batch_xcorr_cpp([[1.0, 0.0, 1.0]])
print(last_xcorr_backend())  # "cpp" or "numpy"
```

## Windows Build Notes

Install:

- Python 3.10+;
- CMake 3.20+;
- a Visual Studio Build Tools C++ compiler;
- `pip install scikit-build-core pybind11 numpy`.

Typical command:

```powershell
cd hcz_mada
python -m pip install -e .[test] --config-settings=cmake.define.PYMADAGASCAR_BUILD_CPP=ON
```

If CMake cannot find a compiler, install "Desktop development with C++" from
Visual Studio Build Tools and restart the terminal.

If you call a Conda environment's `python.exe` directly without activating it,
ensure its `Scripts` directory is visible so `cmake.exe` and `ninja.exe` can be
found:

```powershell
$env:PATH = "D:\HczApp\Anaconda\envs\mywork\Scripts;" + $env:PATH
D:\HczApp\Anaconda\envs\mywork\python.exe -m pip install -e . --no-build-isolation
```

If CMake cannot find pybind11, make sure the same Python environment is active:

```powershell
python -m pip install pybind11 scikit-build-core
```

## Benchmark The XCorr Kernel

Run:

```powershell
python benchmarks/bench_xcorr.py --ntraces 128 --nsamples 256 --dtype float32 --mode full --repeat 5 --report benchmarks/bench_xcorr_report.md
```

The report compares the pure NumPy reference with the optional C++ backend when
`pymadagascar._core` is available. If the extension is not built, the C++
column is marked unavailable instead of failing.

## Linux Build Notes

Install a compiler and CMake, for example on Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake python3-dev
python -m pip install -U pip
python -m pip install -e .[test]
```

For Conda environments:

```bash
conda install -c conda-forge cmake compilers pybind11 scikit-build-core numpy
python -m pip install -e .[test]
```

## Common Errors

`No CMAKE_CXX_COMPILER could be found`

Install a C++ compiler and ensure it is visible in the current shell.

`Could not find pybind11Config.cmake`

Install pybind11 into the active Python environment or Conda environment.

`ImportError: cannot import name _core`

The extension was not built or is not on `PYTHONPATH`. The Python wrappers will
fallback to NumPy unless `pymadagascar._core` is imported directly.

`DLL load failed` on Windows

The extension may have been built against a different Python or compiler
runtime. Rebuild inside the active environment.

## Next Kernel Candidates

The first realistic C++ kernels should be small, well-tested loops with stable
Python APIs:

- convolution/correlation direct kernels;
- semblance inner scan loop;
- NMO interpolation loop;
- 2D acoustic FD time stepping;
- Kirchhoff hyperbola summation.

#include "kernels/xcorr.hpp"

#include <algorithm>
#include <string>
#include <vector>

#include <pybind11/pybind11.h>

namespace py = pybind11;

namespace pymadagascar::kernels {
namespace {

struct ModeInfo {
    py::ssize_t length;
    py::ssize_t crop_start;
};

ModeInfo mode_info(py::ssize_t n, const std::string& mode) {
    if (n < 1) {
        throw py::value_error("traces must have at least one sample");
    }
    if (mode == "full") {
        return {2 * n - 1, 0};
    }
    if (mode == "same") {
        return {n, (n - 1) / 2};
    }
    if (mode == "valid") {
        return {1, n - 1};
    }
    throw py::value_error("mode must be full, same, or valid");
}

template <typename T>
py::array_t<T> batch_xcorr_typed(py::array traces, const std::string& mode) {
    py::array_t<T, py::array::c_style | py::array::forcecast> input(traces);
    py::buffer_info info = input.request();
    if (info.ndim != 2) {
        throw py::value_error("batch_xcorr_cpp expects a 2D trace matrix");
    }
    const auto ntraces = static_cast<py::ssize_t>(info.shape[0]);
    const auto nsamples = static_cast<py::ssize_t>(info.shape[1]);
    ModeInfo window = mode_info(nsamples, mode);

    py::array_t<T> output({ntraces, window.length});
    auto in = input.template unchecked<2>();
    auto out = output.template mutable_unchecked<2>();

    {
        py::gil_scoped_release release;
        for (py::ssize_t itrace = 0; itrace < ntraces; ++itrace) {
            for (py::ssize_t out_index = 0; out_index < window.length; ++out_index) {
                const py::ssize_t full_index = out_index + window.crop_start;
                const py::ssize_t lag = full_index - (nsamples - 1);
                const py::ssize_t i0 = std::max<py::ssize_t>(0, -lag);
                const py::ssize_t i1 = std::min<py::ssize_t>(nsamples, nsamples - lag);
                double sum = 0.0;
                for (py::ssize_t i = i0; i < i1; ++i) {
                    sum += static_cast<double>(in(itrace, i)) *
                           static_cast<double>(in(itrace, i + lag));
                }
                out(itrace, out_index) = static_cast<T>(sum);
            }
        }
    }

    return output;
}

}  // namespace

py::array batch_xcorr_cpp(py::array traces, const std::string& mode) {
    py::buffer_info info = traces.request();
    if (info.ndim != 2) {
        throw py::value_error("batch_xcorr_cpp expects a 2D trace matrix");
    }
    if (info.format == py::format_descriptor<float>::format()) {
        return batch_xcorr_typed<float>(traces, mode);
    }
    if (info.format == py::format_descriptor<double>::format()) {
        return batch_xcorr_typed<double>(traces, mode);
    }
    throw py::type_error("batch_xcorr_cpp supports float32 and float64 arrays");
}

}  // namespace pymadagascar::kernels

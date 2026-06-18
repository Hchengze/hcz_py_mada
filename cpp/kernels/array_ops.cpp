#include "kernels/array_ops.hpp"

#include <stdexcept>
#include <vector>

namespace py = pybind11;

namespace pymadagascar::kernels {

py::array_t<double> add_arrays_cpp(
    py::array_t<double, py::array::c_style | py::array::forcecast> a,
    py::array_t<double, py::array::c_style | py::array::forcecast> b) {
    const py::buffer_info a_info = a.request();
    const py::buffer_info b_info = b.request();
    if (a_info.shape != b_info.shape) {
        throw std::invalid_argument("add_arrays_cpp requires arrays with identical shapes");
    }

    auto result = py::array_t<double>(a_info.shape);
    py::buffer_info result_info = result.request();
    const auto* a_ptr = static_cast<const double*>(a_info.ptr);
    const auto* b_ptr = static_cast<const double*>(b_info.ptr);
    auto* out_ptr = static_cast<double*>(result_info.ptr);

    const auto size = static_cast<std::size_t>(a_info.size);
    for (std::size_t i = 0; i < size; ++i) {
        out_ptr[i] = a_ptr[i] + b_ptr[i];
    }
    return result;
}

py::array_t<double> scale_array_cpp(
    py::array_t<double, py::array::c_style | py::array::forcecast> a,
    double scale) {
    const py::buffer_info a_info = a.request();
    auto result = py::array_t<double>(a_info.shape);
    py::buffer_info result_info = result.request();
    const auto* a_ptr = static_cast<const double*>(a_info.ptr);
    auto* out_ptr = static_cast<double*>(result_info.ptr);

    const auto size = static_cast<std::size_t>(a_info.size);
    for (std::size_t i = 0; i < size; ++i) {
        out_ptr[i] = a_ptr[i] * scale;
    }
    return result;
}

}  // namespace pymadagascar::kernels


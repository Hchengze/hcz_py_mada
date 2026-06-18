#pragma once

#include <pybind11/numpy.h>

namespace pymadagascar::kernels {

pybind11::array_t<double> add_arrays_cpp(
    pybind11::array_t<double, pybind11::array::c_style | pybind11::array::forcecast> a,
    pybind11::array_t<double, pybind11::array::c_style | pybind11::array::forcecast> b);

pybind11::array_t<double> scale_array_cpp(
    pybind11::array_t<double, pybind11::array::c_style | pybind11::array::forcecast> a,
    double scale);

}  // namespace pymadagascar::kernels


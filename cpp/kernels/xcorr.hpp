#pragma once

#include <pybind11/numpy.h>
#include <string>

namespace pymadagascar::kernels {

pybind11::array batch_xcorr_cpp(pybind11::array traces, const std::string& mode);

}  // namespace pymadagascar::kernels

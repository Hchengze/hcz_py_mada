#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include "kernels/array_ops.hpp"
#include "kernels/xcorr.hpp"

namespace py = pybind11;

PYBIND11_MODULE(_core, m) {
    m.doc() = "Optional C++ kernels for pymadagascar-hybrid";
    m.def("add_arrays_cpp", &pymadagascar::kernels::add_arrays_cpp,
          py::arg("a"), py::arg("b"),
          "Add two NumPy arrays using a C++ loop.");
    m.def("scale_array_cpp", &pymadagascar::kernels::scale_array_cpp,
          py::arg("a"), py::arg("scale"),
          "Scale a NumPy array using a C++ loop.");
    m.def("batch_xcorr_cpp", &pymadagascar::kernels::batch_xcorr_cpp,
          py::arg("traces"), py::arg("mode") = "full",
          "Autocorrelate a 2D trace matrix using a C++ loop.");
}

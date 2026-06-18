cmake_minimum_required(VERSION 3.20)

project(pymadagascar_hybrid LANGUAGES NONE)

option(PYMADAGASCAR_BUILD_CPP "Build pymadagascar C++ extension" ON)

if(PYMADAGASCAR_BUILD_CPP)
    enable_language(CXX)

    find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
    find_package(pybind11 CONFIG REQUIRED)

    pybind11_add_module(_core MODULE
        cpp/bindings.cpp
        cpp/kernels/array_ops.cpp
        cpp/kernels/xcorr.cpp
    )

    target_compile_features(_core PRIVATE cxx_std_17)
    target_include_directories(_core PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/cpp
    )

    install(TARGETS _core LIBRARY DESTINATION pymadagascar)
endif()

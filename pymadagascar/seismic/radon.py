"""Small-scale Radon and tau-p transforms for 2D RSF gathers.

The linear ``radon`` direction implemented here is an adjoint slant stack
(``m = A^T d``). The ``iradon`` direction is deterministic modeling
(``d = A m``), not a solved least-squares inverse and not a high-resolution
``sfradon`` equivalent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np

from pymadagascar.core.axis import Axis
from pymadagascar.core.hypercube import Hypercube
from pymadagascar.io.rsf import RSFArray, RSFHeader, read_rsf, write_rsf
from pymadagascar.seismic._utils import numpy_axis, real_output_dtype, validate_rsf_axis


RadonKind = Literal["linear", "parabolic"]


class RadonError(ValueError):
    """Raised when a Radon transform request is invalid."""


def linear_radon(
    input_path: str | Path,
    output_path: str | Path,
    *,
    pmin: float,
    pmax: float,
    dp: float,
    axis: int = 1,
    offset_axis: int = 2,
    offset: str | Path | np.ndarray | None = None,
    least_squares: bool = False,
    normalize: bool = False,
) -> RSFArray:
    """Apply the adjoint linear Radon/slant-stack transform ``m = A^T d``.

    The input is a 2D gather with time/tau on axis 1 and offset on axis 2 by
    default. The output has axes ``tau`` and ``p``. This is the small
    sfslant-style operator direction, not a solved inverse.
    """

    return _radon_adjoint(
        input_path,
        output_path,
        pmin=pmin,
        pmax=pmax,
        dp=dp,
        axis=axis,
        offset_axis=offset_axis,
        offset=offset,
        kind="linear",
        x0=1.0,
        least_squares=least_squares,
        normalize=normalize,
    )


def inverse_linear_radon(
    input_path: str | Path,
    output_path: str | Path,
    *,
    nx: int | None = None,
    ox: float | None = None,
    dx: float | None = None,
    offset: str | Path | np.ndarray | None = None,
    axis: int = 1,
    p_axis: int = 2,
    least_squares: bool = False,
    normalize: bool = False,
) -> RSFArray:
    """Apply linear Radon modeling ``d = A m``.

    This is the algebraic inverse side of the transform pair, not a solved
    least-squares inverse.
    """

    return _radon_modeling(
        input_path,
        output_path,
        nx=nx,
        ox=ox,
        dx=dx,
        offset=offset,
        axis=axis,
        p_axis=p_axis,
        kind="linear",
        x0=1.0,
        least_squares=least_squares,
        normalize=normalize,
    )


def parabolic_radon(
    input_path: str | Path,
    output_path: str | Path,
    *,
    qmin: float,
    qmax: float,
    dq: float,
    axis: int = 1,
    offset_axis: int = 2,
    offset: str | Path | np.ndarray | None = None,
    x0: float = 1.0,
    least_squares: bool = False,
    normalize: bool = False,
) -> RSFArray:
    """Apply the adjoint parabolic Radon transform.

    The moveout is ``t = tau + q * (x/x0)^2``.
    """

    return _radon_adjoint(
        input_path,
        output_path,
        pmin=qmin,
        pmax=qmax,
        dp=dq,
        axis=axis,
        offset_axis=offset_axis,
        offset=offset,
        kind="parabolic",
        x0=x0,
        least_squares=least_squares,
        normalize=normalize,
    )


def inverse_parabolic_radon(
    input_path: str | Path,
    output_path: str | Path,
    *,
    nx: int | None = None,
    ox: float | None = None,
    dx: float | None = None,
    offset: str | Path | np.ndarray | None = None,
    x0: float = 1.0,
    axis: int = 1,
    p_axis: int = 2,
    least_squares: bool = False,
    normalize: bool = False,
) -> RSFArray:
    """Apply parabolic Radon modeling ``d = A m``."""

    return _radon_modeling(
        input_path,
        output_path,
        nx=nx,
        ox=ox,
        dx=dx,
        offset=offset,
        axis=axis,
        p_axis=p_axis,
        kind="parabolic",
        x0=x0,
        least_squares=least_squares,
        normalize=normalize,
    )


def radon_adjoint_array(
    data: np.ndarray,
    tau: np.ndarray,
    offsets: np.ndarray,
    p_values: np.ndarray,
    *,
    kind: RadonKind = "linear",
    x0: float = 1.0,
    normalize: bool = False,
) -> np.ndarray:
    """Return ``A^T data`` for arrays shaped ``(nx, nt)``.

    ``data`` must be finite real samples. ``tau`` and ``p_values`` must be
    finite regularly sampled axes, and ``offsets`` must be finite with length
    matching the trace axis.
    """

    gather = _validate_real_array(data, ndim=2, name="data")
    offsets = _validate_vector(offsets, "offsets")
    p_values = _validate_regular_samples(p_values, "p_values")
    tau = _validate_regular_time(tau)
    if gather.shape != (offsets.size, tau.size):
        raise RadonError(f"data shape must be {(offsets.size, tau.size)}, got {gather.shape}")
    _validate_kind(kind)
    x0 = _validate_x0(x0, kind=kind)

    model = np.zeros((p_values.size, tau.size), dtype=np.float64)
    _radon_operator(model, gather, tau, offsets, p_values, adjoint=True, kind=kind, x0=x0)
    if normalize and offsets.size > 0:
        model /= float(offsets.size)
    return model.astype(np.float32)


def radon_model_array(
    model: np.ndarray,
    tau: np.ndarray,
    offsets: np.ndarray,
    p_values: np.ndarray,
    *,
    kind: RadonKind = "linear",
    x0: float = 1.0,
    normalize: bool = False,
) -> np.ndarray:
    """Return deterministic modeling ``A model`` for arrays shaped ``(np, nt)``.

    This is paired with :func:`radon_adjoint_array`; it is not a solved inverse
    and does not imply high-resolution Radon behavior.
    """

    radon = _validate_real_array(model, ndim=2, name="model")
    offsets = _validate_vector(offsets, "offsets")
    p_values = _validate_regular_samples(p_values, "p_values")
    tau = _validate_regular_time(tau)
    if radon.shape != (p_values.size, tau.size):
        raise RadonError(f"model shape must be {(p_values.size, tau.size)}, got {radon.shape}")
    _validate_kind(kind)
    x0 = _validate_x0(x0, kind=kind)

    data = np.zeros((offsets.size, tau.size), dtype=np.float64)
    _radon_operator(radon, data, tau, offsets, p_values, adjoint=False, kind=kind, x0=x0)
    if normalize and p_values.size > 0:
        data /= float(p_values.size)
    return data.astype(np.float32)


def _radon_adjoint(
    input_path: str | Path,
    output_path: str | Path,
    *,
    pmin: float,
    pmax: float,
    dp: float,
    axis: int,
    offset_axis: int,
    offset: str | Path | np.ndarray | None,
    kind: RadonKind,
    x0: float,
    least_squares: bool,
    normalize: bool,
) -> RSFArray:
    if least_squares:
        raise RadonError("least_squares=True is reserved for a future solver-backed implementation")

    p_values = _radon_samples(pmin, pmax, dp)
    rsf = read_rsf(input_path)
    cube = _validate_2d_axes(rsf.header, axis=axis, other_axis=offset_axis, name="offset_axis")
    dtype = real_output_dtype(rsf.data)
    input_data = _validate_real_array(rsf.data, ndim=2, name="input data").astype(
        dtype, copy=False
    )
    gather = _move_2d_to_other_time(input_data, axis, offset_axis)
    tau = cube.axis(axis).coordinates()
    offsets = _offset_values(offset, rsf.header, offset_axis, gather.shape[0])

    model = radon_adjoint_array(
        gather,
        tau,
        offsets,
        p_values,
        kind=kind,
        x0=x0,
        normalize=normalize,
    )
    header = _radon_header(
        rsf.header,
        p_values,
        offsets,
        axis=axis,
        offset_axis=offset_axis,
        kind=kind,
        x0=x0,
        normalize=normalize,
    )
    return write_rsf(output_path, np.ascontiguousarray(model), header)


def _radon_modeling(
    input_path: str | Path,
    output_path: str | Path,
    *,
    nx: int | None,
    ox: float | None,
    dx: float | None,
    offset: str | Path | np.ndarray | None,
    axis: int,
    p_axis: int,
    kind: RadonKind,
    x0: float,
    least_squares: bool,
    normalize: bool,
) -> RSFArray:
    if least_squares:
        raise RadonError("least_squares=True is reserved for a future solver-backed implementation")

    rsf = read_rsf(input_path)
    cube = _validate_2d_axes(rsf.header, axis=axis, other_axis=p_axis, name="p_axis")
    dtype = real_output_dtype(rsf.data)
    input_model = _validate_real_array(rsf.data, ndim=2, name="input model").astype(
        dtype, copy=False
    )
    model = _move_2d_to_other_time(input_model, axis, p_axis)
    tau = cube.axis(axis).coordinates()
    p_values = _validate_regular_samples(cube.axis(p_axis).coordinates(), "p axis")
    offsets = _modeling_offsets(
        offset,
        rsf.header,
        nx=nx,
        ox=ox,
        dx=dx,
    )

    data = radon_model_array(
        model,
        tau,
        offsets,
        p_values,
        kind=kind,
        x0=x0,
        normalize=normalize,
    )
    header = _inverse_header(rsf.header, offsets, axis=axis, p_axis=p_axis, kind=kind, normalize=normalize)
    return write_rsf(output_path, np.ascontiguousarray(data), header)


def _radon_operator(
    model: np.ndarray,
    data: np.ndarray,
    tau: np.ndarray,
    offsets: np.ndarray,
    p_values: np.ndarray,
    *,
    adjoint: bool,
    kind: RadonKind,
    x0: float,
) -> None:
    _validate_kind(kind)
    x0 = _validate_x0(x0, kind=kind)
    t0 = float(tau[0])
    dt = float(tau[1] - tau[0]) if tau.size > 1 else 1.0
    nt = tau.size

    for ip, p_value in enumerate(p_values):
        for ix, offset in enumerate(offsets):
            shift = _moveout(float(p_value), float(offset), kind=kind, x0=x0)
            sample = (tau + shift - t0) / dt
            lower = np.floor(sample).astype(np.int64)
            frac = sample - lower
            valid0 = (lower >= 0) & (lower < nt)
            valid1 = (lower + 1 >= 0) & (lower + 1 < nt)

            if adjoint:
                if np.any(valid0):
                    model[ip, valid0] += (1.0 - frac[valid0]) * data[ix, lower[valid0]]
                if np.any(valid1):
                    model[ip, valid1] += frac[valid1] * data[ix, lower[valid1] + 1]
            else:
                values = model[ip]
                if np.any(valid0):
                    np.add.at(data[ix], lower[valid0], (1.0 - frac[valid0]) * values[valid0])
                if np.any(valid1):
                    np.add.at(data[ix], lower[valid1] + 1, frac[valid1] * values[valid1])


def _moveout(p_value: float, offset: float, *, kind: RadonKind, x0: float) -> float:
    if kind == "linear":
        return p_value * offset
    if kind == "parabolic":
        scaled = offset / x0
        return p_value * scaled * scaled
    raise RadonError(f"unsupported Radon kind {kind!r}")


def _radon_samples(pmin: float, pmax: float, dp: float) -> np.ndarray:
    pmin = _finite_float(pmin, "pmin")
    pmax = _finite_float(pmax, "pmax")
    dp = _finite_float(dp, "dp")
    if dp <= 0.0:
        raise RadonError("dp= must be positive")
    if pmax < pmin:
        raise RadonError("pmax= must be greater than or equal to pmin=")
    count = int(np.floor((pmax - pmin) / dp + 0.5)) + 1
    values = pmin + dp * np.arange(count, dtype=np.float64)
    return values[values <= pmax + 0.5 * dp]


def _validate_2d_axes(header: RSFHeader, *, axis: int, other_axis: int, name: str) -> Hypercube:
    cube = Hypercube.from_header(header)
    if cube.ndim != 2:
        raise RadonError(f"Radon transforms currently require 2D input, got {cube.ndim}D")
    validate_rsf_axis(axis, cube.ndim)
    validate_rsf_axis(other_axis, cube.ndim)
    if axis == other_axis:
        raise RadonError(f"axis and {name} must be different")
    axis_obj = cube.axis(axis)
    _validate_axis_sampling(axis_obj, axis=axis)
    other_obj = cube.axis(other_axis)
    _validate_axis_sampling(other_obj, axis=other_axis)
    return cube


def _move_2d_to_other_time(data: np.ndarray, axis: int, other_axis: int) -> np.ndarray:
    time_np = numpy_axis(axis, data.ndim)
    other_np = numpy_axis(other_axis, data.ndim)
    return np.moveaxis(data, [other_np, time_np], [0, 1])


def _offset_values(
    offset: str | Path | np.ndarray | None,
    header: RSFHeader,
    offset_axis: int,
    nx: int,
) -> np.ndarray:
    if offset is None:
        values = Hypercube.from_header(header).axis(offset_axis).coordinates()
    elif isinstance(offset, np.ndarray):
        values = np.asarray(offset, dtype=np.float64)
    else:
        values = np.asarray(read_rsf(offset).data, dtype=np.float64).reshape(-1)
    values = _validate_vector(values, "offset")
    if values.size != nx:
        raise RadonError(f"offset data has {values.size} samples, expected {nx}")
    return values


def _modeling_offsets(
    offset: str | Path | np.ndarray | None,
    header: RSFHeader,
    *,
    nx: int | None,
    ox: float | None,
    dx: float | None,
) -> np.ndarray:
    if offset is not None:
        if isinstance(offset, np.ndarray):
            values = np.asarray(offset, dtype=np.float64)
        else:
            values = np.asarray(read_rsf(offset).data, dtype=np.float64).reshape(-1)
        offsets = _validate_vector(values, "offset")
        if nx is not None:
            expected_nx = _positive_int(nx, "nx")
            if offsets.size != expected_nx:
                raise RadonError(
                    f"offset data has {offsets.size} samples, expected nx={expected_nx}"
                )
        return offsets

    if nx is None:
        stored_nx = header.get("radon_nx")
        if stored_nx is None:
            raise RadonError("nx= is required when Radon header metadata is unavailable")
        nx = _positive_int(stored_nx, "nx")
    else:
        nx = _positive_int(nx, "nx")
    if ox is None:
        ox = _finite_float(header.get("radon_ox", 0.0), "ox")
    else:
        ox = _finite_float(ox, "ox")
    if dx is None:
        stored_dx = header.get("radon_dx")
        if stored_dx is None:
            raise RadonError("dx= is required when Radon header metadata is unavailable")
        dx = _finite_float(stored_dx, "dx")
    else:
        dx = _finite_float(dx, "dx")
    if dx <= 0.0:
        raise RadonError("dx= must be positive")
    return ox + dx * np.arange(nx, dtype=np.float64)


def _radon_header(
    header: RSFHeader,
    p_values: np.ndarray,
    offsets: np.ndarray,
    *,
    axis: int,
    offset_axis: int,
    kind: RadonKind,
    x0: float,
    normalize: bool,
) -> RSFHeader:
    cube = Hypercube.from_header(header)
    time_axis = cube.axis(axis)
    offset_axis_obj = cube.axis(offset_axis)
    axes = [
        Axis(
            n=time_axis.n,
            o=time_axis.o,
            d=time_axis.d,
            label="Tau",
            unit=time_axis.unit,
            index=1,
        ),
        Axis(
            n=p_values.size,
            o=float(p_values[0]),
            d=float(p_values[1] - p_values[0]) if p_values.size > 1 else 1.0,
            label="Slowness" if kind == "linear" else "Parabolic Moveout",
            unit=_p_unit(time_axis.unit, offset_axis_obj.unit, kind=kind),
            index=2,
        ),
    ]
    output = Hypercube(axes).to_header(header.copy())
    output["radon_kind"] = kind
    output["radon_adjoint"] = "y"
    output["radon_direction"] = "adjoint_slant_stack"
    output["radon_operator_form"] = "m=A^T d"
    output["radon_normalize"] = "y" if normalize else "n"
    output["radon_nx"] = offsets.size
    output["radon_ox"] = float(offsets[0])
    output["radon_dx"] = _regular_spacing(offsets, default=float(offset_axis_obj.d))
    output["radon_x0"] = x0
    output["radon_time_label"] = time_axis.label or ""
    output["radon_time_unit"] = time_axis.unit or ""
    output["radon_offset_label"] = offset_axis_obj.label or ""
    output["radon_offset_unit"] = offset_axis_obj.unit or ""
    output["axis2_role"] = "slowness" if kind == "linear" else "parabolic_moveout"
    output["radon_madagascar_reference"] = "Mslant.c/slant.c small subset"
    output["radon_sfradon_equivalence"] = "not_sfradon"
    return output


def _inverse_header(
    header: RSFHeader,
    offsets: np.ndarray,
    *,
    axis: int,
    p_axis: int,
    kind: RadonKind,
    normalize: bool,
) -> RSFHeader:
    cube = Hypercube.from_header(header)
    tau_axis = cube.axis(axis)
    axes = [
        Axis(
            n=tau_axis.n,
            o=tau_axis.o,
            d=tau_axis.d,
            label=_stored_or_default(header, "radon_time_label", "Time"),
            unit=_stored_or_default(header, "radon_time_unit", tau_axis.unit),
            index=1,
        ),
        Axis(
            n=offsets.size,
            o=float(offsets[0]),
            d=_regular_spacing(offsets, default=float(header.get("radon_dx", 1.0))),
            label=_stored_or_default(header, "radon_offset_label", "Offset"),
            unit=_stored_or_default(header, "radon_offset_unit", None),
            index=2,
        ),
    ]
    output = Hypercube(axes).to_header(header.copy())
    output["radon_kind"] = kind
    output["radon_adjoint"] = "n"
    output["radon_direction"] = "modeling"
    output["radon_operator_form"] = "d=A m"
    output["radon_normalize"] = "y" if normalize else "n"
    output["radon_np"] = cube.axis(p_axis).n
    output["axis2_role"] = "signed_offset"
    output["radon_madagascar_reference"] = "Mslant.c/slant.c small subset"
    output["radon_sfradon_equivalence"] = "not_sfradon"
    return output


def _p_unit(time_unit: str | None, offset_unit: str | None, *, kind: RadonKind) -> str | None:
    if kind == "parabolic":
        if time_unit and offset_unit:
            return f"{time_unit}/{offset_unit}^2"
        return time_unit
    if time_unit and offset_unit:
        return f"{time_unit}/{offset_unit}"
    return None


def _stored_or_default(header: RSFHeader, key: str, default: str | None) -> str | None:
    value = header.get(key)
    if value in {None, ""}:
        return default
    return str(value)


def _regular_spacing(values: np.ndarray, *, default: float) -> float:
    if values.size < 2:
        return default
    diffs = np.diff(values)
    if np.allclose(diffs, diffs[0], rtol=1e-6, atol=1e-12):
        return float(diffs[0])
    return default


def _validate_regular_time(values: np.ndarray) -> np.ndarray:
    time = _validate_vector(values, "tau")
    if time.size > 1:
        diffs = np.diff(time)
        if not np.allclose(diffs, diffs[0], rtol=1e-6, atol=1e-12):
            raise RadonError("tau/time axis must be regularly sampled")
        if diffs[0] <= 0.0:
            raise RadonError("tau/time axis sampling must be positive")
    return time


def _validate_regular_samples(values: np.ndarray, name: str) -> np.ndarray:
    samples = _validate_vector(values, name)
    if samples.size > 1:
        diffs = np.diff(samples)
        if not np.all(diffs > 0.0):
            raise RadonError(f"{name} must be strictly increasing")
        if not np.allclose(diffs, diffs[0], rtol=1e-6, atol=1e-12):
            raise RadonError(f"{name} must be regularly sampled")
    return samples


def _validate_vector(values: np.ndarray, name: str) -> np.ndarray:
    vector = np.asarray(values, dtype=np.float64).reshape(-1)
    if vector.size < 1:
        raise RadonError(f"{name} must contain at least one value")
    if not np.all(np.isfinite(vector)):
        raise RadonError(f"{name} contains non-finite values")
    return vector


def _validate_real_array(values: np.ndarray, *, ndim: int, name: str) -> np.ndarray:
    array = np.asarray(values)
    if array.ndim != ndim or array.size == 0:
        raise RadonError(f"{name} must be a non-empty {ndim}D array")
    if np.iscomplexobj(array) or array.dtype.kind not in {"b", "i", "u", "f"}:
        raise RadonError(f"{name} must contain real numeric samples")
    array = np.asarray(array, dtype=np.float64)
    if not np.all(np.isfinite(array)):
        raise RadonError(f"{name} contains non-finite samples")
    return array


def _validate_axis_sampling(axis_obj: Axis, *, axis: int) -> None:
    _finite_float(axis_obj.o, f"o{axis}")
    d_value = _finite_float(axis_obj.d, f"d{axis}")
    if d_value <= 0.0:
        raise RadonError(f"d{axis}= must be positive")


def _validate_x0(value: float, *, kind: RadonKind) -> float:
    x0 = _finite_float(value, "x0")
    if kind == "parabolic" and x0 == 0.0:
        raise RadonError("x0= must be nonzero for parabolic Radon")
    return x0


def _finite_float(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RadonError(f"{name}= must be finite") from exc
    if not np.isfinite(number):
        raise RadonError(f"{name}= must be finite")
    return number


def _positive_int(value: object, name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise RadonError(f"{name}= must be positive") from exc
    if number <= 0:
        raise RadonError(f"{name}= must be positive")
    return number


def _validate_kind(kind: RadonKind) -> None:
    if kind not in {"linear", "parabolic"}:
        raise RadonError(f"kind= must be linear or parabolic, got {kind!r}")

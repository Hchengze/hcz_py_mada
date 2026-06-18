"""Small SEG-Y reader/writer for RSF conversion.

This module focuses on ordinary 2D post-stack or gather-style SEG-Y files:
one 3200-byte textual header, one 400-byte binary header, and fixed-length
240-byte trace headers followed by one trace of samples.
"""

from __future__ import annotations

import base64
import csv
from dataclasses import dataclass
from pathlib import Path
import struct
import sys
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from .rsf import RSFArray, RSFHeader, read_rsf, write_rsf


TEXTUAL_HEADER_BYTES = 3200
BINARY_HEADER_BYTES = 400
TRACE_HEADER_BYTES = 240
SEGY_DATA_START = TEXTUAL_HEADER_BYTES + BINARY_HEADER_BYTES


class SegyError(ValueError):
    """Raised when a SEG-Y file cannot be interpreted by this module."""


@dataclass(frozen=True)
class TraceHeaderField:
    """A standard SEG-Y trace-header integer field."""

    name: str
    offset: int
    size: int


@dataclass(frozen=True)
class SegyHeaders:
    """Textual, binary, and trace-header metadata from a SEG-Y file."""

    textual_header: str
    textual_encoding: str
    binary_header: dict[str, int]
    trace_headers: list[dict[str, int]]
    endian: str
    sample_format: int
    sample_interval_us: int
    samples_per_trace: int
    trace_count: int


TRACE_HEADER_FIELDS: tuple[TraceHeaderField, ...] = (
    TraceHeaderField("tracl", 0, 4),
    TraceHeaderField("tracr", 4, 4),
    TraceHeaderField("fldr", 8, 4),
    TraceHeaderField("tracf", 12, 4),
    TraceHeaderField("ep", 16, 4),
    TraceHeaderField("cdp", 20, 4),
    TraceHeaderField("cdpt", 24, 4),
    TraceHeaderField("trid", 28, 2),
    TraceHeaderField("nvs", 30, 2),
    TraceHeaderField("nhs", 32, 2),
    TraceHeaderField("duse", 34, 2),
    TraceHeaderField("offset", 36, 4),
    TraceHeaderField("gelev", 40, 4),
    TraceHeaderField("selev", 44, 4),
    TraceHeaderField("sdepth", 48, 4),
    TraceHeaderField("gdel", 52, 4),
    TraceHeaderField("sdel", 56, 4),
    TraceHeaderField("swdep", 60, 4),
    TraceHeaderField("gwdep", 64, 4),
    TraceHeaderField("scalel", 68, 2),
    TraceHeaderField("scalco", 70, 2),
    TraceHeaderField("sx", 72, 4),
    TraceHeaderField("sy", 76, 4),
    TraceHeaderField("gx", 80, 4),
    TraceHeaderField("gy", 84, 4),
    TraceHeaderField("counit", 88, 2),
    TraceHeaderField("wevel", 90, 2),
    TraceHeaderField("swevel", 92, 2),
    TraceHeaderField("sut", 94, 2),
    TraceHeaderField("gut", 96, 2),
    TraceHeaderField("sstat", 98, 2),
    TraceHeaderField("gstat", 100, 2),
    TraceHeaderField("tstat", 102, 2),
    TraceHeaderField("laga", 104, 2),
    TraceHeaderField("lagb", 106, 2),
    TraceHeaderField("delrt", 108, 2),
    TraceHeaderField("muts", 110, 2),
    TraceHeaderField("mute", 112, 2),
    TraceHeaderField("ns", 114, 2),
    TraceHeaderField("dt", 116, 2),
    TraceHeaderField("gain", 118, 2),
    TraceHeaderField("igc", 120, 2),
    TraceHeaderField("igi", 122, 2),
    TraceHeaderField("corr", 124, 2),
    TraceHeaderField("sfs", 126, 2),
    TraceHeaderField("sfe", 128, 2),
    TraceHeaderField("slen", 130, 2),
    TraceHeaderField("styp", 132, 2),
    TraceHeaderField("stas", 134, 2),
    TraceHeaderField("stae", 136, 2),
    TraceHeaderField("tatyp", 138, 2),
    TraceHeaderField("afilf", 140, 2),
    TraceHeaderField("afils", 142, 2),
    TraceHeaderField("nofilf", 144, 2),
    TraceHeaderField("nofils", 146, 2),
    TraceHeaderField("lcf", 148, 2),
    TraceHeaderField("hcf", 150, 2),
    TraceHeaderField("lcs", 152, 2),
    TraceHeaderField("hcs", 154, 2),
    TraceHeaderField("year", 156, 2),
    TraceHeaderField("day", 158, 2),
    TraceHeaderField("hour", 160, 2),
    TraceHeaderField("minute", 162, 2),
    TraceHeaderField("sec", 164, 2),
    TraceHeaderField("timbas", 166, 2),
    TraceHeaderField("trwf", 168, 2),
    TraceHeaderField("grnors", 170, 2),
    TraceHeaderField("grnofr", 172, 2),
    TraceHeaderField("grnlof", 174, 2),
    TraceHeaderField("gaps", 176, 2),
    TraceHeaderField("otrav", 178, 2),
    TraceHeaderField("cdpx", 180, 4),
    TraceHeaderField("cdpy", 184, 4),
    TraceHeaderField("iline", 188, 4),
    TraceHeaderField("xline", 192, 4),
    TraceHeaderField("shnum", 196, 4),
    TraceHeaderField("shsca", 200, 2),
    TraceHeaderField("tval", 202, 2),
    TraceHeaderField("tconst4", 204, 4),
    TraceHeaderField("tconst2", 208, 2),
    TraceHeaderField("tunits", 210, 2),
    TraceHeaderField("device", 212, 2),
    TraceHeaderField("tscalar", 214, 2),
    TraceHeaderField("stype", 216, 2),
    TraceHeaderField("sendir", 218, 4),
    TraceHeaderField("unknown", 222, 2),
    TraceHeaderField("smeas4", 224, 4),
    TraceHeaderField("smeas2", 228, 2),
    TraceHeaderField("smeasu", 230, 2),
    TraceHeaderField("unass1", 232, 4),
    TraceHeaderField("unass2", 236, 4),
)

TRACE_HEADER_FIELD_MAP = {field.name: field for field in TRACE_HEADER_FIELDS}
DEFAULT_TRACE_TABLE_KEYS = (
    "tracl",
    "tracr",
    "fldr",
    "tracf",
    "cdp",
    "cdpt",
    "offset",
    "sx",
    "sy",
    "gx",
    "gy",
    "scalco",
    "ns",
    "dt",
    "delrt",
    "iline",
    "xline",
)
BINARY_HEADER_FIELDS: tuple[tuple[str, int, int], ...] = (
    ("jobid", 0, 4),
    ("lino", 4, 4),
    ("reno", 8, 4),
    ("ntrpr", 12, 2),
    ("nart", 14, 2),
    ("hdt", 16, 2),
    ("dto", 18, 2),
    ("hns", 20, 2),
    ("nso", 22, 2),
    ("format", 24, 2),
    ("fold", 26, 2),
    ("tsort", 28, 2),
)
SUPPORTED_SAMPLE_FORMATS = {1, 2, 3, 5, 7, 8}


def segy_to_rsf(
    segy_path: str | Path,
    output_path: str | Path,
    *,
    endian: str = "auto",
    sample_format: int | None = None,
    trace_header_csv: str | Path | None = None,
) -> RSFArray:
    """Convert a fixed-length 2D SEG-Y file to an RSF data/header pair."""

    input_path = Path(segy_path).expanduser()
    headers = read_segy_headers(input_path, endian=endian, sample_format=sample_format)
    if headers.trace_count < 1:
        raise SegyError("SEG-Y file contains no traces")

    sample_size = _sample_size(headers.sample_format)
    data = np.empty((headers.trace_count, headers.samples_per_trace), dtype=np.float32)
    with input_path.open("rb") as stream:
        stream.seek(SEGY_DATA_START)
        for itrace in range(headers.trace_count):
            trace_header = stream.read(TRACE_HEADER_BYTES)
            if len(trace_header) != TRACE_HEADER_BYTES:
                raise SegyError(f"trace {itrace + 1} is missing its 240-byte header")
            parsed = _parse_trace_header(trace_header, headers.endian)
            trace_ns = _unsigned_ushort(parsed.get("ns", headers.samples_per_trace))
            if trace_ns != headers.samples_per_trace:
                raise SegyError("variable-length SEG-Y traces are not supported")
            raw = stream.read(sample_size * trace_ns)
            if len(raw) != sample_size * trace_ns:
                raise SegyError(f"trace {itrace + 1} data is truncated")
            data[itrace] = _decode_samples(raw, headers.sample_format, headers.endian, trace_ns)

    csv_path: Path | None = None
    if trace_header_csv is not None:
        csv_path = Path(trace_header_csv).expanduser()
        _write_trace_header_csv(csv_path, headers.trace_headers)

    first_trace = headers.trace_headers[0]
    delrt_ms = first_trace.get("delrt", 0)
    header = RSFHeader(
        {
            "n1": headers.samples_per_trace,
            "n2": headers.trace_count,
            "o1": delrt_ms / 1000.0,
            "d1": headers.sample_interval_us / 1000000.0,
            "label1": "Time",
            "unit1": "s",
            "o2": 0.0,
            "d2": 1.0,
            "label2": "Trace",
            "segy_format": headers.sample_format,
            "segy_endian": headers.endian,
            "segy_sample_interval_us": headers.sample_interval_us,
            "segy_textual_encoding": headers.textual_encoding,
            "segy_textual_header_b64": _text_to_b64(headers.textual_header),
        }
    )
    if csv_path is not None:
        header["segy_trace_headers"] = str(csv_path)

    return write_rsf(output_path, data, header)


def rsf_to_segy(
    input_path: str | Path,
    output_path: str | Path,
    *,
    endian: str = "big",
    sample_format: int | None = None,
    trace_headers: str | Path | Sequence[Mapping[str, Any]] | None = None,
    textual_header: str | Path | None = None,
) -> Path:
    """Convert an RSF dataset to a fixed-length 2D SEG-Y file."""

    rsf = read_rsf(input_path)
    traces = _rsf_traces(rsf)
    ns = traces.shape[1]
    ntr = traces.shape[0]
    endian = _normalize_endian(endian, allow_auto=False)
    format_code = int(sample_format if sample_format is not None else rsf.header.get("segy_format", 5))
    if format_code not in SUPPORTED_SAMPLE_FORMATS:
        raise SegyError(f"sample format {format_code} is not supported")

    d1 = float(rsf.header.get("d1", 1.0))
    o1 = float(rsf.header.get("o1", 0.0))
    dt_us = _positive_ushort(int(round(d1 * 1000000.0)), "sample interval")
    delrt_ms = _signed_short(int(round(o1 * 1000.0)), "trace delay")
    rows = _coerce_trace_headers(trace_headers, rsf, ntr)
    text = _resolve_textual_header(textual_header, rsf)

    output = Path(output_path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as stream:
        stream.write(_encode_textual_header(text, encoding="ascii"))
        stream.write(_build_binary_header(ns, dt_us, format_code, endian))
        for index, trace in enumerate(traces):
            header_values = _default_trace_header(index, ns, dt_us, delrt_ms)
            if rows is not None:
                header_values.update({key: int(value) for key, value in rows[index].items() if key != "trace"})
            header_values["ns"] = ns
            header_values["dt"] = dt_us
            header_values["delrt"] = delrt_ms
            stream.write(_build_trace_header(header_values, endian))
            stream.write(_encode_samples(trace, format_code, endian))

    return output.resolve()


def read_segy_headers(
    path: str | Path,
    *,
    endian: str = "auto",
    sample_format: int | None = None,
) -> SegyHeaders:
    """Read SEG-Y textual, binary, and trace headers without loading data."""

    segy_path = Path(path).expanduser()
    size = segy_path.stat().st_size
    if size < SEGY_DATA_START:
        raise SegyError("SEG-Y file is shorter than 3600 bytes")

    with segy_path.open("rb") as stream:
        textual_block = stream.read(TEXTUAL_HEADER_BYTES)
        binary_block = stream.read(BINARY_HEADER_BYTES)
        detected = _detect_endian(binary_block) if _is_auto_endian(endian) else _normalize_endian(endian)
        binary = _parse_binary_header(binary_block, detected)
        format_code = int(sample_format if sample_format is not None else binary.get("format", 0))
        if format_code not in SUPPORTED_SAMPLE_FORMATS:
            raise SegyError(f"sample format {format_code} is not supported")

        ns = _unsigned_ushort(binary.get("hns", 0))
        dt_us = _unsigned_ushort(binary.get("hdt", 0))
        if ns <= 0:
            first_header = stream.read(TRACE_HEADER_BYTES)
            if len(first_header) != TRACE_HEADER_BYTES:
                raise SegyError("cannot determine ns from SEG-Y headers")
            parsed = _parse_trace_header(first_header, detected)
            ns = _unsigned_ushort(parsed.get("ns", 0))
            dt_us = dt_us or _unsigned_ushort(parsed.get("dt", 0))
            stream.seek(SEGY_DATA_START)
        if ns <= 0:
            raise SegyError("number of samples per trace is not set")
        if dt_us <= 0:
            raise SegyError("sample interval is not set")

        record_size = TRACE_HEADER_BYTES + ns * _sample_size(format_code)
        payload = size - SEGY_DATA_START
        if payload % record_size != 0:
            raise SegyError(
                f"SEG-Y payload size {payload} is not divisible by fixed trace record size {record_size}"
            )
        trace_count = payload // record_size
        trace_headers: list[dict[str, int]] = []
        for _ in range(trace_count):
            raw_header = stream.read(TRACE_HEADER_BYTES)
            if len(raw_header) != TRACE_HEADER_BYTES:
                raise SegyError("truncated SEG-Y trace header")
            trace_headers.append(_parse_trace_header(raw_header, detected))
            stream.seek(ns * _sample_size(format_code), 1)

    textual, textual_encoding = _decode_textual_header(textual_block)
    return SegyHeaders(
        textual_header=textual,
        textual_encoding=textual_encoding,
        binary_header=binary,
        trace_headers=trace_headers,
        endian=detected,
        sample_format=format_code,
        sample_interval_us=dt_us,
        samples_per_trace=ns,
        trace_count=int(trace_count),
    )


def extract_trace_header_table(
    path: str | Path,
    *,
    keys: Sequence[str] | None = None,
    endian: str = "auto",
    output_csv: str | Path | None = None,
) -> list[dict[str, int]]:
    """Extract selected SEG-Y trace-header words as a table."""

    selected = tuple(keys) if keys is not None else DEFAULT_TRACE_TABLE_KEYS
    for key in selected:
        if key not in TRACE_HEADER_FIELD_MAP:
            raise SegyError(f"unknown SEG-Y trace header key {key!r}")

    headers = read_segy_headers(path, endian=endian)
    rows: list[dict[str, int]] = []
    for index, header in enumerate(headers.trace_headers):
        row = {"trace": index + 1}
        row.update({key: int(header.get(key, 0)) for key in selected})
        rows.append(row)

    if output_csv is not None:
        _write_trace_header_csv(Path(output_csv).expanduser(), rows)
    return rows


def _rsf_traces(rsf: RSFArray) -> np.ndarray:
    if len(rsf.header.dimensions) < 1:
        raise SegyError("RSF input must have n1=")
    ns = rsf.header.dimensions[0]
    data = np.asarray(rsf.data)
    if data.size % ns != 0:
        raise SegyError("RSF data size is not divisible by n1")
    return np.ascontiguousarray(data.reshape((-1, ns)).astype(np.float32, copy=False))


def _coerce_trace_headers(
    trace_headers: str | Path | Sequence[Mapping[str, Any]] | None,
    rsf: RSFArray,
    ntr: int,
) -> list[dict[str, int]] | None:
    candidate = trace_headers
    if candidate is None and rsf.header.get("segy_trace_headers") and rsf.header_path is not None:
        header_path = Path(rsf.header.get("segy_trace_headers"))
        candidate = header_path if header_path.is_absolute() else rsf.header_path.parent / header_path
    if candidate is None:
        return None

    rows = _read_trace_header_csv(candidate) if isinstance(candidate, (str, Path)) else [
        {str(key): int(value) for key, value in row.items()} for row in candidate
    ]
    if len(rows) != ntr:
        raise SegyError(f"trace header table has {len(rows)} rows, expected {ntr}")
    return rows


def _resolve_textual_header(textual_header: str | Path | None, rsf: RSFArray) -> str:
    if textual_header is not None:
        path = Path(textual_header)
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace")
        return str(textual_header)
    encoded = rsf.header.get("segy_textual_header_b64")
    if encoded:
        try:
            return base64.b64decode(str(encoded).encode("ascii")).decode("utf-8", errors="replace")
        except (ValueError, OSError):
            pass
    return _default_textual_header()


def _default_textual_header() -> str:
    lines = [
        "C 1 PYMadagascar generated SEG-Y file",
        "C 2 Converted from an RSF dataset",
        "C 3 Sample format defaults to IEEE float unless format= overrides it",
    ]
    lines.extend(f"C {index:2d}" for index in range(4, 41))
    return "\n".join(lines)


def _decode_textual_header(block: bytes) -> tuple[str, str]:
    ascii_text = block.decode("ascii", errors="replace")
    printable = sum(1 for char in ascii_text if char.isprintable() or char in "\r\n\t ")
    if printable / max(len(ascii_text), 1) > 0.85:
        return _format_textual_lines(ascii_text), "ascii"
    return _format_textual_lines(block.decode("cp500", errors="replace")), "ebcdic-cp500"


def _encode_textual_header(text: str, *, encoding: str = "ascii") -> bytes:
    lines = text.splitlines() or _default_textual_header().splitlines()
    padded = "".join((line[:80]).ljust(80) for line in (lines + [""] * 40)[:40])
    codec = "cp500" if encoding.lower().startswith("ebcdic") else "ascii"
    return padded.encode(codec, errors="replace")


def _format_textual_lines(text: str) -> str:
    return "\n".join(text[index : index + 80].rstrip() for index in range(0, TEXTUAL_HEADER_BYTES, 80)).rstrip()


def _text_to_b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _parse_binary_header(block: bytes, endian: str) -> dict[str, int]:
    return {name: _read_int(block, offset, size, endian) for name, offset, size in BINARY_HEADER_FIELDS}


def _build_binary_header(ns: int, dt_us: int, sample_format: int, endian: str) -> bytes:
    block = bytearray(BINARY_HEADER_BYTES)
    values = {
        "jobid": 1,
        "lino": 1,
        "reno": 1,
        "hdt": dt_us,
        "dto": dt_us,
        "hns": ns,
        "nso": ns,
        "format": sample_format,
        "tsort": 1,
    }
    for name, offset, size in BINARY_HEADER_FIELDS:
        if name in values:
            _write_int(block, offset, size, int(values[name]), endian)
    return bytes(block)


def _parse_trace_header(block: bytes, endian: str) -> dict[str, int]:
    return {field.name: _read_int(block, field.offset, field.size, endian) for field in TRACE_HEADER_FIELDS}


def _build_trace_header(values: Mapping[str, int], endian: str) -> bytes:
    block = bytearray(TRACE_HEADER_BYTES)
    for field in TRACE_HEADER_FIELDS:
        _write_int(block, field.offset, field.size, int(values.get(field.name, 0)), endian)
    return bytes(block)


def _default_trace_header(index: int, ns: int, dt_us: int, delrt_ms: int) -> dict[str, int]:
    trace_number = index + 1
    return {
        "tracl": trace_number,
        "tracr": trace_number,
        "fldr": 1,
        "tracf": trace_number,
        "cdp": trace_number,
        "cdpt": 1,
        "trid": 1,
        "ns": ns,
        "dt": dt_us,
        "delrt": delrt_ms,
    }


def _detect_endian(binary_header: bytes) -> str:
    candidates = []
    for endian in ("big", "little"):
        parsed = _parse_binary_header(binary_header, endian)
        score = 0
        if parsed["format"] in SUPPORTED_SAMPLE_FORMATS:
            score += 4
        if 0 < _unsigned_ushort(parsed["hns"]) < 100000:
            score += 3
        if 0 < _unsigned_ushort(parsed["hdt"]) < 1000000:
            score += 2
        candidates.append((score, endian))
    candidates.sort(reverse=True)
    if candidates[0][0] == 0:
        raise SegyError("could not infer SEG-Y endian from binary header")
    return candidates[0][1]


def _normalize_endian(value: str, *, allow_auto: bool = True) -> str:
    normalized = str(value).strip().lower()
    if normalized in {"big", "be", "xdr", ">"}:
        return "big"
    if normalized in {"little", "le", "<"}:
        return "little"
    if normalized in {"native"}:
        return sys.byteorder
    if normalized in {"auto", "y", "yes", "true", "1"} and allow_auto:
        return "auto"
    if normalized in {"n", "no", "false", "0"}:
        return sys.byteorder
    raise SegyError("endian= must be auto, big, little, or native")


def _is_auto_endian(value: str) -> bool:
    return _normalize_endian(value, allow_auto=True) == "auto"


def _endian_prefix(endian: str) -> str:
    return ">" if endian == "big" else "<"


def _read_int(block: bytes, offset: int, size: int, endian: str) -> int:
    prefix = _endian_prefix(endian)
    if size == 4:
        return struct.unpack_from(prefix + "i", block, offset)[0]
    if size == 2:
        return struct.unpack_from(prefix + "h", block, offset)[0]
    if size == 1:
        return struct.unpack_from("b", block, offset)[0]
    raise SegyError(f"unsupported integer field size {size}")


def _write_int(block: bytearray, offset: int, size: int, value: int, endian: str) -> None:
    prefix = _endian_prefix(endian)
    try:
        if size == 4:
            struct.pack_into(prefix + "i", block, offset, value)
        elif size == 2:
            if value > 32767:
                value -= 65536
            struct.pack_into(prefix + "h", block, offset, value)
        elif size == 1:
            struct.pack_into("b", block, offset, value)
        else:
            raise SegyError(f"unsupported integer field size {size}")
    except struct.error as exc:
        raise SegyError(f"trace or binary header value {value} does not fit in {size} bytes") from exc


def _sample_size(format_code: int) -> int:
    if format_code in {1, 2, 5}:
        return 4
    if format_code == 3:
        return 2
    if format_code in {7, 8}:
        return 1
    raise SegyError(f"sample format {format_code} is not supported")


def _decode_samples(raw: bytes, format_code: int, endian: str, ns: int) -> np.ndarray:
    prefix = _endian_prefix(endian)
    if format_code == 1:
        return _ibm_to_float32(np.frombuffer(raw, dtype=np.dtype(prefix + "u4"), count=ns))
    if format_code == 2:
        return np.frombuffer(raw, dtype=np.dtype(prefix + "i4"), count=ns).astype(np.float32)
    if format_code == 3:
        return np.frombuffer(raw, dtype=np.dtype(prefix + "i2"), count=ns).astype(np.float32)
    if format_code == 5:
        return np.frombuffer(raw, dtype=np.dtype(prefix + "f4"), count=ns).astype(np.float32)
    if format_code in {7, 8}:
        return np.frombuffer(raw, dtype=np.dtype("i1"), count=ns).astype(np.float32)
    raise SegyError(f"sample format {format_code} is not supported")


def _encode_samples(trace: np.ndarray, format_code: int, endian: str) -> bytes:
    array = np.asarray(trace)
    prefix = _endian_prefix(endian)
    if format_code == 1:
        words = _float32_to_ibm(array.astype(np.float32, copy=False))
        return words.astype(np.dtype(prefix + "u4"), copy=False).tobytes()
    if format_code == 2:
        return np.rint(array).astype(np.dtype(prefix + "i4"), copy=False).tobytes()
    if format_code == 3:
        return np.rint(array).astype(np.dtype(prefix + "i2"), copy=False).tobytes()
    if format_code == 5:
        return array.astype(np.dtype(prefix + "f4"), copy=False).tobytes()
    if format_code in {7, 8}:
        return np.rint(array).astype(np.dtype("i1"), copy=False).tobytes()
    raise SegyError(f"sample format {format_code} is not supported")


def _ibm_to_float32(words: np.ndarray) -> np.ndarray:
    raw = words.astype(np.uint32, copy=False)
    sign = np.where((raw & 0x80000000) != 0, -1.0, 1.0)
    exponent = ((raw >> 24) & 0x7F).astype(np.int32) - 64
    fraction = (raw & 0x00FFFFFF).astype(np.float64) / float(0x01000000)
    values = sign * fraction * np.power(16.0, exponent)
    values[(raw & 0x7FFFFFFF) == 0] = 0.0
    return values.astype(np.float32)


def _float32_to_ibm(values: np.ndarray) -> np.ndarray:
    output = np.zeros(values.size, dtype=np.uint32)
    flat = np.asarray(values, dtype=np.float32).ravel()
    for index, value in enumerate(flat):
        number = float(value)
        if number == 0.0:
            continue
        sign = 0x80000000 if number < 0 else 0
        number = abs(number)
        exponent = 64
        while number < 1.0:
            number *= 16.0
            exponent -= 1
        while number >= 1.0:
            number /= 16.0
            exponent += 1
        fraction = int(number * 0x01000000 + 0.5)
        if fraction >= 0x01000000:
            fraction >>= 4
            exponent += 1
        output[index] = np.uint32(sign | ((exponent & 0x7F) << 24) | (fraction & 0x00FFFFFF))
    return output.reshape(values.shape)


def _write_trace_header_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = _csv_fieldnames(rows)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _read_trace_header_csv(path: str | Path) -> list[dict[str, int]]:
    with Path(path).expanduser().open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = []
        for raw in reader:
            row: dict[str, int] = {}
            for key, value in raw.items():
                if key is None or value in {None, ""}:
                    continue
                row[key] = int(float(value))
            rows.append(row)
        return rows


def _csv_fieldnames(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    fields: list[str] = []
    for preferred in ("trace",) + DEFAULT_TRACE_TABLE_KEYS:
        if any(preferred in row for row in rows):
            fields.append(preferred)
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(str(key))
    return fields


def _unsigned_ushort(value: int) -> int:
    return value + 65536 if value < 0 else value


def _positive_ushort(value: int, name: str) -> int:
    if value <= 0 or value > 65535:
        raise SegyError(f"{name} must fit in an unsigned 2-byte SEG-Y field")
    return value


def _signed_short(value: int, name: str) -> int:
    if value < -32768 or value > 32767:
        raise SegyError(f"{name} must fit in a signed 2-byte SEG-Y field")
    return value

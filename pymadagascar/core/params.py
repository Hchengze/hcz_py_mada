"""Madagascar-style command-line parameter parsing."""

from __future__ import annotations

from collections import OrderedDict
from contextlib import contextmanager
from pathlib import Path
import shlex
import sys
from typing import Any, BinaryIO, Callable, Iterator, Sequence, TextIO, TypeVar


_MISSING = object()
T = TypeVar("T")


class ParameterParseError(ValueError):
    """Raised when a command-line parameter cannot be parsed."""


class MissingParameterError(ParameterParseError):
    """Raised when a required parameter is missing."""

    def __init__(self, key: str):
        super().__init__(f"Missing required parameter: {key}=")
        self.key = key


class RSFParams:
    """Parameter table compatible with Madagascar's key=value style.

    Args are passed without the program name. Non key=value tokens are kept as
    positional arguments; by convention the first positional argument is input
    and the second is output.
    """

    TRUE_VALUES = {"y", "yes", "true", "t", "1", "on"}
    FALSE_VALUES = {"n", "no", "false", "f", "0", "off"}

    def __init__(
        self,
        args: Sequence[str] | None = None,
        *,
        prog: str | None = None,
        stdin: Any | None = None,
        stdout: Any | None = None,
        stderr: TextIO | None = None,
    ):
        self.prog = prog or Path(sys.argv[0]).name
        self.stdin = stdin if stdin is not None else sys.stdin
        self.stdout = stdout if stdout is not None else sys.stdout
        self.stderr = stderr if stderr is not None else sys.stderr
        self.params: OrderedDict[str, str] = OrderedDict()
        self.positionals: list[str] = []
        self.flags: list[str] = []
        self.help_requested = False

        self._parse(list(args) if args is not None else sys.argv[1:])

    @classmethod
    def from_argv(cls, argv: Sequence[str] | None = None, **kwargs: Any) -> "RSFParams":
        raw = list(argv) if argv is not None else sys.argv
        prog = kwargs.pop("prog", Path(raw[0]).name if raw else None)
        args = raw[1:] if raw else []
        return cls(args, prog=prog, **kwargs)

    def _parse(self, args: list[str]) -> None:
        for token in args:
            if token in {"-h", "--help"}:
                self.help_requested = True
                self.flags.append(token)
                continue

            if "=" not in token:
                self.positionals.append(token)
                continue

            key, value = token.split("=", 1)
            if key == "par":
                self._load_parameter_file(value)
                continue

            value = _strip_quotes(value)
            self.params[key] = value
            if key in {"help", "--help"} and self._parse_bool(value):
                self.help_requested = True

    def _load_parameter_file(self, filename: str) -> None:
        path = Path(_strip_quotes(filename)).expanduser()
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ParameterParseError(f"Cannot open par file {path}: {exc}") from exc
        tokens = _tokenize_parameter_text(text, source=str(path))
        self._parse(tokens)

    def has(self, key: str) -> bool:
        return key in self.params

    def get(self, key: str, default: Any = _MISSING) -> str:
        if key in self.params:
            return self.params[key]
        if default is _MISSING:
            raise MissingParameterError(key)
        return default

    def get_int(self, key: str, default: int | object = _MISSING) -> int:
        value = self.get(key, default)
        if value is default and default is not _MISSING:
            return value  # type: ignore[return-value]
        try:
            return int(str(value), 10)
        except ValueError as exc:
            raise ParameterParseError(f"{key}= must be an integer, got {value!r}") from exc

    def get_float(self, key: str, default: float | object = _MISSING) -> float:
        value = self.get(key, default)
        if value is default and default is not _MISSING:
            return value  # type: ignore[return-value]
        try:
            return float(str(value))
        except ValueError as exc:
            raise ParameterParseError(f"{key}= must be a float, got {value!r}") from exc

    def get_bool(self, key: str, default: bool | object = _MISSING) -> bool:
        value = self.get(key, default)
        if value is default and default is not _MISSING:
            return value  # type: ignore[return-value]
        return self._parse_bool(str(value), key=key)

    def get_string(self, key: str, default: str | object = _MISSING) -> str:
        value = self.get(key, default)
        if value is default and default is not _MISSING:
            return value  # type: ignore[return-value]
        return str(value)

    def get_list(
        self,
        key: str,
        *,
        item_type: Callable[[str], T] = str,
        default: list[T] | object = _MISSING,
        count: int | None = None,
    ) -> list[T]:
        if key not in self.params:
            if default is _MISSING:
                raise MissingParameterError(key)
            return default  # type: ignore[return-value]

        values = _expand_list_tokens(self.params[key])
        if not values:
            raise ParameterParseError(f"{key}= list is empty")

        if count is not None:
            if count < 0:
                raise ValueError("count must be non-negative")
            if len(values) < count:
                values.extend([values[-1]] * (count - len(values)))
            else:
                values = values[:count]

        try:
            return [item_type(value) for value in values]
        except ValueError as exc:
            raise ParameterParseError(f"{key}= list contains invalid values: {self.params[key]!r}") from exc

    def input_path(self, default: str | None = None, *, required: bool = False) -> str | None:
        value = self.params.get("in") or self.params.get("input")
        if value is None and self.positionals:
            value = self.positionals[0]
        if value is None:
            value = default
        if required and value in {None, "", "-", "stdin"}:
            raise MissingParameterError("in")
        return value

    def output_path(self, default: str | None = None, *, required: bool = False) -> str | None:
        value = self.params.get("out") or self.params.get("--out") or self.params.get("output")
        if value is None and len(self.positionals) >= 2:
            value = self.positionals[1]
        if value is None:
            value = default
        if required and value in {None, "", "-", "stdout"}:
            raise MissingParameterError("out")
        return value

    @contextmanager
    def open_input(self, path: str | Path | None = None, mode: str = "rb") -> Iterator[Any]:
        target = str(path) if path is not None else self.input_path()
        if target in {None, "", "-", "stdin"}:
            yield _binary_stream(self.stdin) if "b" in mode else self.stdin
            return

        with Path(target).expanduser().open(mode) as stream:
            yield stream

    @contextmanager
    def open_output(self, path: str | Path | None = None, mode: str = "wb") -> Iterator[Any]:
        target = str(path) if path is not None else self.output_path()
        if target in {None, "", "-", "stdout"}:
            yield _binary_stream(self.stdout) if "b" in mode else self.stdout
            return

        output = Path(target).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open(mode) as stream:
            yield stream

    def format_help(self, description: str | None = None, extra: str | None = None) -> str:
        lines = [f"Usage: {self.prog} [key=value ...] [input.rsf [output.rsf]]"]
        if description:
            lines.extend(["", description])
        lines.extend(
            [
                "",
                "Madagascar-style parameters:",
                "  key=value        Set a parameter.",
                "  par=file.par     Load whitespace/newline-separated parameters from a file.",
                "                   Later parameters override earlier values.",
                "  in=file.rsf      Input file path, equivalent to first positional input.",
                "  out=file.rsf     Output file path, equivalent to second positional output.",
                "  - or stdin       Use standard input.",
                "  - or stdout      Use standard output.",
            ]
        )
        if extra:
            lines.extend(["", extra])
        return "\n".join(lines)

    def _parse_bool(self, value: str, key: str = "bool") -> bool:
        lowered = value.strip().lower()
        if lowered in self.TRUE_VALUES:
            return True
        if lowered in self.FALSE_VALUES:
            return False
        raise ParameterParseError(
            f"{key}= must be a boolean value (yes/no, true/false, y/n, 1/0), got {value!r}"
        )


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _tokenize_parameter_text(text: str, *, source: str = "parameter text") -> list[str]:
    """Tokenize a Madagascar-style parameter file.

    Parameter files use shell-like whitespace tokenization with quote support.
    Unquoted ``#`` starts a comment; quoted ``#`` remains part of the value.
    """

    try:
        return shlex.split(text, comments=True, posix=True)
    except ValueError as exc:
        raise ParameterParseError(f"Cannot parse par file {source}: {exc}") from exc


def _expand_list_tokens(raw: str) -> list[str]:
    expanded: list[str] = []
    for token in raw.split(","):
        item = _strip_quotes(token.strip())
        if not item:
            continue
        repeat = _split_repeat(item)
        if repeat is None:
            expanded.append(item)
        else:
            count, value = repeat
            expanded.extend([value] * count)
    return expanded


def _split_repeat(item: str) -> tuple[int, str] | None:
    for sep in ("*", "x"):
        if sep in item:
            count_text, value = item.split(sep, 1)
            if count_text.strip().isdigit() and value:
                return int(count_text), value
    return None


def _binary_stream(stream: Any) -> BinaryIO:
    return getattr(stream, "buffer", stream)

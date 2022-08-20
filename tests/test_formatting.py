import sys

import pytest
from _pytest.fixtures import SubRequest
from _pytest.monkeypatch import MonkeyPatch

from exceptiongroup import ExceptionGroup


@pytest.fixture(
    params=[
        pytest.param(True, id="patched"),
        pytest.param(
            False,
            id="unpatched",
            marks=[
                pytest.mark.skipif(
                    sys.version_info >= (3, 11),
                    reason="No patching is done on Python >= 3.11",
                )
            ],
        ),
    ],
)
def patched(request: SubRequest) -> bool:
    return request.param


@pytest.fixture(
    params=[pytest.param(False, id="newstyle"), pytest.param(True, id="oldstyle")]
)
def old_argstyle(request: SubRequest) -> bool:
    return request.param


def test_formatting(capsys):
    exceptions = []
    try:
        raise ValueError("foo")
    except ValueError as exc:
        exceptions.append(exc)

    try:
        raise RuntimeError("bar")
    except RuntimeError as exc:
        exc.__notes__ = ["Note from bar handler"]
        exceptions.append(exc)

    try:
        raise ExceptionGroup("test message", exceptions)
    except ExceptionGroup as exc:
        exc.add_note("Displays notes attached to the group too")
        sys.excepthook(type(exc), exc, exc.__traceback__)

    lineno = test_formatting.__code__.co_firstlineno
    module_prefix = "" if sys.version_info >= (3, 11) else "exceptiongroup."
    output = capsys.readouterr().err
    assert output == (
        f"""\
  + Exception Group Traceback (most recent call last):
  |   File "{__file__}", line {lineno + 14}, in test_formatting
  |     raise ExceptionGroup("test message", exceptions)
  | {module_prefix}ExceptionGroup: test message (2 sub-exceptions)
  | Displays notes attached to the group too
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "{__file__}", line {lineno + 3}, in test_formatting
    |     raise ValueError("foo")
    | ValueError: foo
    +---------------- 2 ----------------
    | Traceback (most recent call last):
    |   File "{__file__}", line {lineno + 8}, in test_formatting
    |     raise RuntimeError("bar")
    | RuntimeError: bar
    | Note from bar handler
    +------------------------------------
"""
    )


def test_formatting_exception_only(capsys):
    exceptions = []
    try:
        raise ValueError("foo")
    except ValueError as exc:
        exceptions.append(exc)

    try:
        raise RuntimeError("bar")
    except RuntimeError as exc:
        exc.__notes__ = ["Note from bar handler"]
        exceptions.append(exc)

    try:
        raise ExceptionGroup("test message", exceptions)
    except ExceptionGroup as exc:
        exc.add_note("Displays notes attached to the group too")
        sys.excepthook(type(exc), exc, exc.__traceback__)

    lineno = test_formatting_exception_only.__code__.co_firstlineno
    module_prefix = "" if sys.version_info >= (3, 11) else "exceptiongroup."
    output = capsys.readouterr().err
    assert output == (
        f"""\
  + Exception Group Traceback (most recent call last):
  |   File "{__file__}", line {lineno + 14}, in test_formatting_exception_only
  |     raise ExceptionGroup("test message", exceptions)
  | {module_prefix}ExceptionGroup: test message (2 sub-exceptions)
  | Displays notes attached to the group too
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "{__file__}", line {lineno + 3}, in test_formatting_exception_only
    |     raise ValueError("foo")
    | ValueError: foo
    +---------------- 2 ----------------
    | Traceback (most recent call last):
    |   File "{__file__}", line {lineno + 8}, in test_formatting_exception_only
    |     raise RuntimeError("bar")
    | RuntimeError: bar
    | Note from bar handler
    +------------------------------------
"""
    )


def test_formatting_syntax_error(capsys):
    try:
        exec("//serser")
    except SyntaxError as exc:
        sys.excepthook(type(exc), exc, exc.__traceback__)

    if sys.version_info >= (3, 10):
        underline = "\n    ^^"
    elif sys.version_info >= (3, 8):
        underline = "\n    ^"
    else:
        underline = "\n     ^"

    lineno = test_formatting_syntax_error.__code__.co_firstlineno
    output = capsys.readouterr().err
    assert output == (
        f"""\
Traceback (most recent call last):
  File "{__file__}", line {lineno + 2}, \
in test_formatting_syntax_error
    exec("//serser")
  File "<string>", line 1
    //serser{underline}
SyntaxError: invalid syntax
"""
    )


def test_format_exception(
    patched: bool, old_argstyle: bool, monkeypatch: MonkeyPatch
) -> None:
    if not patched:
        # Block monkey patching, then force the module to be re-imported
        del sys.modules["traceback"]
        del sys.modules["exceptiongroup"]
        del sys.modules["exceptiongroup._formatting"]
        monkeypatch.setattr(sys, "excepthook", lambda *args: sys.__excepthook__(*args))

    from exceptiongroup import format_exception

    exceptions = []
    try:
        raise ValueError("foo")
    except ValueError as exc:
        exceptions.append(exc)

    try:
        raise RuntimeError("bar")
    except RuntimeError as exc:
        exc.__notes__ = ["Note from bar handler"]
        exceptions.append(exc)

    try:
        exc = ExceptionGroup("test message", exceptions)
        exc.add_note("Displays notes attached to the group too")
        raise exc
    except ExceptionGroup as exc:
        if old_argstyle:
            lines = format_exception(type(exc), exc, exc.__traceback__)
        else:
            lines = format_exception(exc)

        assert isinstance(lines, list)
        lineno = test_format_exception.__code__.co_firstlineno
        module_prefix = "" if sys.version_info >= (3, 11) else "exceptiongroup."
        assert "".join(lines) == (
            f"""\
  + Exception Group Traceback (most recent call last):
  |   File "{__file__}", line {lineno + 27}, in test_format_exception
  |     raise exc
  | {module_prefix}ExceptionGroup: test message (2 sub-exceptions)
  | Displays notes attached to the group too
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "{__file__}", line {lineno + 14}, in test_format_exception
    |     raise ValueError("foo")
    | ValueError: foo
    +---------------- 2 ----------------
    | Traceback (most recent call last):
    |   File "{__file__}", line {lineno + 19}, in test_format_exception
    |     raise RuntimeError("bar")
    | RuntimeError: bar
    | Note from bar handler
    +------------------------------------
"""
        )


def test_format_exception_only(
    patched: bool, old_argstyle: bool, monkeypatch: MonkeyPatch
) -> None:
    if not patched:
        # Block monkey patching, then force the module to be re-imported
        del sys.modules["traceback"]
        del sys.modules["exceptiongroup"]
        del sys.modules["exceptiongroup._formatting"]
        monkeypatch.setattr(sys, "excepthook", lambda *args: sys.__excepthook__(*args))

    from exceptiongroup import format_exception_only

    exceptions = []
    try:
        raise ValueError("foo")
    except ValueError as exc:
        exceptions.append(exc)

    try:
        raise RuntimeError("bar")
    except RuntimeError as exc:
        exc.__notes__ = ["Note from bar handler"]
        exceptions.append(exc)

    exc = ExceptionGroup("test message", exceptions)
    exc.add_note("Displays notes attached to the group too")
    if old_argstyle:
        output = format_exception_only(type(exc), exc)
    else:
        output = format_exception_only(exc)

    module_prefix = "" if sys.version_info >= (3, 11) else "exceptiongroup."
    assert output == [
        f"{module_prefix}ExceptionGroup: test message (2 sub-exceptions)\n",
        "Displays notes attached to the group too\n",
    ]

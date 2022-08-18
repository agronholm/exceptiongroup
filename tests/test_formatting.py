import gc
import sys

import pytest

from exceptiongroup import ExceptionGroup
from exceptiongroup._formatting import exceptiongroup_unraisablehook


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


@pytest.mark.skipif(
    sys.version_info < (3, 8), reason="sys.unraisablehook was added in Python 3.8"
)
def test_unraisablehook(capsys, monkeypatch):
    # Pytest overrides sys.unraisablehook so we temporarily override that here
    monkeypatch.setattr(sys, "unraisablehook", exceptiongroup_unraisablehook)

    class Foo:
        def __del__(self):
            raise ExceptionGroup("the bad", [Exception("critical debug information")])

    Foo()
    gc.collect()

    lineno = Foo.__del__.__code__.co_firstlineno
    module_prefix = "" if sys.version_info >= (3, 11) else "exceptiongroup."
    output = capsys.readouterr().err
    assert output == (
        f"""\
Exception ignored in: {Foo.__del__!r}
  File "{__file__}", line {lineno + 1}, in __del__
    raise ExceptionGroup("the bad", [Exception("critical debug information")])
  + Exception Group Traceback (most recent call last):
  |   File "{__file__}", line {lineno + 1}, in __del__
  |     raise ExceptionGroup("the bad", [Exception("critical debug information")])
  | {module_prefix}ExceptionGroup: the bad (1 sub-exception)
  +-+---------------- 1 ----------------
    | Exception: critical debug information
    +------------------------------------
"""
    )

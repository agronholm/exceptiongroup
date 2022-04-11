import sys

from exceptiongroup import ExceptionGroup


def test_formatting(capsys):
    exceptions = []
    try:
        raise ValueError("foo")
    except ValueError as exc:
        exceptions.append(exc)

    try:
        raise RuntimeError("bar")
    except RuntimeError as exc:
        exc.__note__ = "Note from bar handler"
        exceptions.append(exc)

    try:
        raise ExceptionGroup("test message", exceptions)
    except ExceptionGroup as exc:
        exc.__note__ = "Displays notes attached to the group too"
        sys.excepthook(type(exc), exc, exc.__traceback__)

    lineno = test_formatting.__code__.co_firstlineno
    if sys.version_info >= (3, 11):
        module_prefix = ""
        underline1 = "\n  |     " + "^" * 48
        underline2 = "\n    |     " + "^" * 23
        underline3 = "\n    |     " + "^" * 25
    else:
        module_prefix = "exceptiongroup."
        underline1 = underline2 = underline3 = ""

    output = capsys.readouterr().err
    assert output == (
        f"""\
  + Exception Group Traceback (most recent call last):
  |   File "{__file__}", line {lineno + 14}, in test_formatting
  |     raise ExceptionGroup("test message", exceptions){underline1}
  | {module_prefix}ExceptionGroup: test message (2 sub-exceptions)
  | Displays notes attached to the group too
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "{__file__}", line {lineno + 3}, in test_formatting
    |     raise ValueError("foo"){underline2}
    | ValueError: foo
    +---------------- 2 ----------------
    | Traceback (most recent call last):
    |   File "{__file__}", line {lineno + 8}, in test_formatting
    |     raise RuntimeError("bar"){underline3}
    | RuntimeError: bar
    | Note from bar handler
    +------------------------------------
"""
    )

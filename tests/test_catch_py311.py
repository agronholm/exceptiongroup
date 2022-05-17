import pytest

from exceptiongroup import BaseExceptionGroup, ExceptionGroup, catch


def test_catch_ungrouped():
    value_type_errors = []
    zero_division_errors = []
    for exc in [ValueError("foo"), TypeError("bar"), ZeroDivisionError()]:
        try:
            raise exc
        except* (ValueError, TypeError) as e:
            value_type_errors.append(e)
        except* ZeroDivisionError as e:
            zero_division_errors.append(e)

    assert len(value_type_errors) == 2

    assert isinstance(value_type_errors[0], ExceptionGroup)
    assert len(value_type_errors[0].exceptions) == 1
    assert isinstance(value_type_errors[0].exceptions[0], ValueError)

    assert isinstance(value_type_errors[1], ExceptionGroup)
    assert len(value_type_errors[1].exceptions) == 1
    assert isinstance(value_type_errors[1].exceptions[0], TypeError)

    assert len(zero_division_errors) == 1
    assert isinstance(zero_division_errors[0], ExceptionGroup)
    assert isinstance(zero_division_errors[0].exceptions[0], ZeroDivisionError)
    assert len(zero_division_errors[0].exceptions) == 1


def test_catch_group():
    value_runtime_errors = []
    zero_division_errors = []
    try:
        raise ExceptionGroup(
            "booboo",
            [
                ValueError("foo"),
                ValueError("bar"),
                RuntimeError("bar"),
                ZeroDivisionError(),
            ],
        )
    except* (ValueError, RuntimeError) as exc:
        value_runtime_errors.append(exc)
    except* ZeroDivisionError as exc:
        zero_division_errors.append(exc)

    assert len(value_runtime_errors) == 1
    assert isinstance(value_runtime_errors[0], ExceptionGroup)
    exceptions = value_runtime_errors[0].exceptions
    assert isinstance(exceptions[0], ValueError)
    assert isinstance(exceptions[1], ValueError)
    assert isinstance(exceptions[2], RuntimeError)

    assert len(zero_division_errors) == 1
    assert isinstance(zero_division_errors[0], ExceptionGroup)
    exceptions = zero_division_errors[0].exceptions
    assert isinstance(exceptions[0], ZeroDivisionError)


def test_catch_nested_group():
    value_runtime_errors = []
    zero_division_errors = []
    try:
        nested_group = ExceptionGroup(
            "nested", [RuntimeError("bar"), ZeroDivisionError()]
        )
        raise ExceptionGroup("booboo", [ValueError("foo"), nested_group])
    except* (ValueError, RuntimeError) as exc:
        value_runtime_errors.append(exc)
    except* ZeroDivisionError as exc:
        zero_division_errors.append(exc)

    assert len(value_runtime_errors) == 1
    exceptions = value_runtime_errors[0].exceptions
    assert isinstance(exceptions[0], ValueError)
    assert isinstance(exceptions[1], ExceptionGroup)
    assert isinstance(exceptions[1].exceptions[0], RuntimeError)

    assert len(zero_division_errors) == 1
    assert isinstance(zero_division_errors[0], ExceptionGroup)
    assert isinstance(zero_division_errors[0].exceptions[0], ExceptionGroup)
    assert isinstance(
        zero_division_errors[0].exceptions[0].exceptions[0], ZeroDivisionError
    )


def test_catch_no_match():
    try:
        try:
            group = ExceptionGroup("booboo", [ZeroDivisionError()])
            raise group
        except* (ValueError, RuntimeError):
            pass
    except ExceptionGroup as exc:
        assert exc is not group
    else:
        pytest.fail("Did not raise an ExceptionGroup")


def test_catch_full_match():
    try:
        raise ExceptionGroup("booboo", [ValueError()])
    except* (ValueError, RuntimeError):
        pass


def test_catch_handler_raises():
    try:
        try:
            raise ExceptionGroup("booboo", [ValueError("bar")])
        except* ValueError:
            raise RuntimeError("new")
    except ExceptionGroup as exc:
        assert exc.message == ""
        assert len(exc.exceptions) == 1
        assert isinstance(exc.exceptions[0], RuntimeError)
    else:
        pytest.fail("Did not raise an ExceptionGroup")


def test_catch_subclass():
    lookup_errors = []
    try:
        raise KeyError("foo")
    except* LookupError as e:
        lookup_errors.append(e)

    assert len(lookup_errors) == 1
    assert isinstance(lookup_errors[0], ExceptionGroup)
    exceptions = lookup_errors[0].exceptions
    assert isinstance(exceptions[0], KeyError)

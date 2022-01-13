import pytest

from exceptiongroup import BaseExceptionGroup, ExceptionGroup, catch


@pytest.mark.parametrize(
    "exc_type",
    [
        pytest.param(BaseExceptionGroup, id="naked_basegroup"),
        pytest.param(ExceptionGroup, id="naked_group"),
        pytest.param((ValueError, BaseExceptionGroup), id="iterable_basegroup"),
        pytest.param((ValueError, ExceptionGroup), id="iterable_group"),
    ],
)
def test_catch_bad_exc_type(exc_type):
    with pytest.raises(TypeError, match="catching ExceptionGroup with catch"):
        with catch(exc_type, lambda e: True):
            pass


def test_catch_ungrouped():
    def handler1(e):
        handler1_exceptions.append(e)

    def handler2(e):
        handler2_exceptions.append(e)

    handler1_exceptions = []
    handler2_exceptions = []
    for exc in [ValueError("foo"), TypeError("bar"), ZeroDivisionError()]:
        with catch((ValueError, TypeError), handler1), catch(
            ZeroDivisionError, handler2
        ):
            raise exc

    assert len(handler1_exceptions) == 2
    assert isinstance(handler1_exceptions[0], ValueError)
    assert isinstance(handler1_exceptions[1], TypeError)

    assert len(handler2_exceptions) == 1
    assert isinstance(handler2_exceptions[0], ZeroDivisionError)


def test_catch_group():
    def handler1(exc):
        handler1_exceptions.append(exc)

    def handler2(exc):
        handler2_exceptions.append(exc)

    handler1_exceptions = []
    handler2_exceptions = []
    with catch((ValueError, RuntimeError), handler1), catch(
        ZeroDivisionError, handler2
    ):
        raise ExceptionGroup(
            "booboo", [ValueError("foo"), RuntimeError("bar"), ZeroDivisionError()]
        )

    assert len(handler1_exceptions) == 2
    assert isinstance(handler1_exceptions[0], ValueError)
    assert isinstance(handler1_exceptions[1], RuntimeError)

    assert len(handler2_exceptions) == 1
    assert isinstance(handler2_exceptions[0], ZeroDivisionError)


def test_catch_nested_group():
    def handler1(exc):
        handler1_exceptions.append(exc)

    def handler2(exc):
        handler2_exceptions.append(exc)

    handler1_exceptions = []
    handler2_exceptions = []
    with catch((ValueError, RuntimeError), handler1), catch(
        ZeroDivisionError, handler2
    ):
        nested_group = ExceptionGroup(
            "nested", [RuntimeError("bar"), ZeroDivisionError()]
        )
        raise ExceptionGroup("booboo", [ValueError("foo"), nested_group])

    assert len(handler1_exceptions) == 2
    assert isinstance(handler1_exceptions[0], ValueError)
    assert isinstance(handler1_exceptions[1], RuntimeError)

    assert len(handler2_exceptions) == 1
    assert isinstance(handler2_exceptions[0], ZeroDivisionError)


def test_catch_no_match():
    try:
        with catch((ValueError, RuntimeError), lambda e: None):
            group = ExceptionGroup("booboo", [ZeroDivisionError()])
            raise group
    except ExceptionGroup as exc:
        assert exc is not group
    else:
        pytest.fail("Did not raise an ExceptionGroup")


def test_catch_full_match():
    with catch((ValueError, RuntimeError), lambda e: None):
        raise ExceptionGroup("booboo", [ValueError()])


def test_catch_handler_raises():
    def handler(exc):
        raise RuntimeError("new")

    try:
        with catch((ValueError, ValueError), handler):
            raise ExceptionGroup("booboo", [ValueError("bar")])
    except ExceptionGroup as exc:
        assert exc.message == ""
        assert len(exc.exceptions) == 1
        assert isinstance(exc.exceptions[0], RuntimeError)
    else:
        pytest.fail("Did not raise an ExceptionGroup")

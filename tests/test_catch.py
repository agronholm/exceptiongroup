import pytest

from exceptiongroup import BaseExceptionGroup, ExceptionGroup, catch


def test_bad_arg():
    with pytest.raises(TypeError, match="the argument must be a mapping"):
        with catch(1):
            pass


def test_bad_handler():
    with pytest.raises(TypeError, match="handlers must be callable"):
        with catch({RuntimeError: None}):
            pass


@pytest.mark.parametrize(
    "exc_type",
    [
        pytest.param(BaseExceptionGroup, id="naked_basegroup"),
        pytest.param(ExceptionGroup, id="naked_group"),
        pytest.param((ValueError, BaseExceptionGroup), id="iterable_basegroup"),
        pytest.param((ValueError, ExceptionGroup), id="iterable_group"),
    ],
)
def test_catch_exceptiongroup(exc_type):
    with pytest.raises(TypeError, match="catching ExceptionGroup with catch"):
        with catch({exc_type: (lambda e: True)}):
            pass


def test_catch_ungrouped():
    exceptions1 = []
    exceptions2 = []
    for exc in [ValueError("foo"), TypeError("bar"), ZeroDivisionError()]:
        with catch(
            {
                (ValueError, TypeError): exceptions1.append,
                ZeroDivisionError: exceptions2.append,
            }
        ):
            raise exc

    assert len(exceptions1) == 2
    assert isinstance(exceptions1[0], ValueError)
    assert isinstance(exceptions1[1], TypeError)

    assert len(exceptions2) == 1
    assert isinstance(exceptions2[0], ZeroDivisionError)


def test_catch_group():
    exceptions1 = []
    exceptions2 = []
    with catch(
        {
            (ValueError, RuntimeError): exceptions1.append,
            ZeroDivisionError: exceptions2.append,
        }
    ):
        raise ExceptionGroup(
            "booboo", [ValueError("foo"), RuntimeError("bar"), ZeroDivisionError()]
        )

    assert len(exceptions1) == 2
    assert isinstance(exceptions1[0], ValueError)
    assert isinstance(exceptions1[1], RuntimeError)

    assert len(exceptions2) == 1
    assert isinstance(exceptions2[0], ZeroDivisionError)


def test_catch_nested_group():
    exceptions1 = []
    exceptions2 = []
    with catch(
        {
            (ValueError, RuntimeError): exceptions1.append,
            ZeroDivisionError: exceptions2.append,
        }
    ):
        nested_group = ExceptionGroup(
            "nested", [RuntimeError("bar"), ZeroDivisionError()]
        )
        raise ExceptionGroup("booboo", [ValueError("foo"), nested_group])

    assert len(exceptions1) == 2
    assert isinstance(exceptions1[0], ValueError)
    assert isinstance(exceptions1[1], RuntimeError)

    assert len(exceptions2) == 1
    assert isinstance(exceptions2[0], ZeroDivisionError)


def test_catch_no_match():
    try:
        with catch({(ValueError, RuntimeError): (lambda e: None)}):
            group = ExceptionGroup("booboo", [ZeroDivisionError()])
            raise group
    except ExceptionGroup as exc:
        assert exc is not group
    else:
        pytest.fail("Did not raise an ExceptionGroup")


def test_catch_full_match():
    with catch({(ValueError, RuntimeError): (lambda e: None)}):
        raise ExceptionGroup("booboo", [ValueError()])


def test_catch_handler_raises():
    def handler(exc):
        raise RuntimeError("new")

    try:
        with catch({(ValueError, ValueError): handler}):
            raise ExceptionGroup("booboo", [ValueError("bar")])
    except ExceptionGroup as exc:
        assert exc.message == ""
        assert len(exc.exceptions) == 1
        assert isinstance(exc.exceptions[0], RuntimeError)
    else:
        pytest.fail("Did not raise an ExceptionGroup")

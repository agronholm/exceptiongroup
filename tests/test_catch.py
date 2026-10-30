import sys

import pytest

from exceptiongroup import BaseExceptionGroup, ExceptionGroup, catch

# PyPy doesn't implicitly chain an exception whose __context__ has been set explicitly,
# as split() does
PYPY = sys.implementation.name == "pypy"


def test_bad_arg():
    with pytest.raises(TypeError, match="the argument must be a mapping"), catch(1):
        pass


def test_bad_handler():
    with pytest.raises(TypeError, match="handlers must be callable"), catch(
        {RuntimeError: None}
    ):
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
    with pytest.raises(TypeError, match="catching ExceptionGroup with catch"), catch(
        {exc_type: (lambda e: True)}
    ):
        pass


def test_catch_ungrouped():
    value_type_errors = []
    zero_division_errors = []
    for exc in [ValueError("foo"), TypeError("bar"), ZeroDivisionError()]:
        with catch(
            {
                (ValueError, TypeError): value_type_errors.append,
                ZeroDivisionError: zero_division_errors.append,
            }
        ):
            raise exc

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
    with catch(
        {
            (ValueError, RuntimeError): value_runtime_errors.append,
            ZeroDivisionError: zero_division_errors.append,
        }
    ):
        raise ExceptionGroup(
            "booboo",
            [
                ValueError("foo"),
                ValueError("bar"),
                RuntimeError("bar"),
                ZeroDivisionError(),
            ],
        )

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
    with catch(
        {
            (ValueError, RuntimeError): value_runtime_errors.append,
            ZeroDivisionError: zero_division_errors.append,
        }
    ):
        nested_group = ExceptionGroup(
            "nested", [RuntimeError("bar"), ZeroDivisionError()]
        )
        raise ExceptionGroup("booboo", [ValueError("foo"), nested_group])

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
        with catch({(ValueError, RuntimeError): (lambda e: None)}):
            group = ExceptionGroup("booboo", [ZeroDivisionError()])
            raise group
    except ExceptionGroup as exc:
        assert exc is not group
    else:
        pytest.fail("Did not raise an ExceptionGroup")


def test_catch_single_no_match():
    try:
        with catch({(ValueError, RuntimeError): (lambda e: None)}):
            raise ZeroDivisionError
    except ZeroDivisionError:
        pass
    else:
        pytest.fail("Did not raise an ZeroDivisionError")


def test_catch_full_match():
    with catch({(ValueError, RuntimeError): (lambda e: None)}):
        raise ExceptionGroup("booboo", [ValueError()])


def test_catch_handler_raises():
    def handler(exc):
        raise RuntimeError("new")

    with pytest.raises(RuntimeError, match="new") as exc, catch(
        {(ValueError, ValueError): handler}
    ):
        excgrp = ExceptionGroup("booboo", [ValueError("bar")])
        raise excgrp

    context = exc.value.__context__
    assert isinstance(context, ExceptionGroup)
    assert str(context) == "booboo (1 sub-exception)"
    assert len(context.exceptions) == 1
    assert isinstance(context.exceptions[0], ValueError)
    assert exc.value.__cause__ is None


def test_bare_raise_in_handler():
    """Test that a bare "raise"  "middle" ecxeption group gets discarded."""

    def handler(exc):
        raise

    with pytest.raises(ExceptionGroup) as excgrp, catch(
        {(ValueError,): handler, (TypeError,): lambda eg: None}
    ):
        try:
            first_exc = RuntimeError("first")
            raise first_exc
        except RuntimeError as exc:
            middle_exc = ExceptionGroup(
                "bad", [ValueError(), ValueError(), TypeError()]
            )
            raise middle_exc from exc

    assert len(excgrp.value.exceptions) == 2
    assert all(isinstance(exc, ValueError) for exc in excgrp.value.exceptions)
    assert excgrp.value is not middle_exc
    assert excgrp.value.__cause__ is first_exc
    assert excgrp.value.__context__ is first_exc


def test_handler_raises_subgroup_preserves_group():
    matched = rest = None

    def handler(excgrp):
        nonlocal matched, rest
        matched = excgrp
        _, rest = excgrp.split(lambda exc: str(exc) == "handled")
        raise rest

    cause = ValueError("cause")
    with pytest.raises(ExceptionGroup) as excgrp, catch({RuntimeError: handler}):
        raise ExceptionGroup(
            "booboo", [RuntimeError("handled"), RuntimeError("unhandled")]
        ) from cause

    assert excgrp.value is rest
    assert len(excgrp.value.exceptions) == 1
    assert isinstance(excgrp.value.exceptions[0], RuntimeError)
    assert str(excgrp.value.exceptions[0]) == "unhandled"
    assert excgrp.value.__cause__ is cause
    if not PYPY:
        assert excgrp.value.__context__ is matched


def test_handler_raises_subgroup_from_none():
    matched = None

    def handler(excgrp):
        nonlocal matched
        matched = excgrp
        _, rest = excgrp.split(lambda exc: str(exc) == "handled")
        raise rest from None

    with pytest.raises(ExceptionGroup) as excgrp, catch({RuntimeError: handler}):
        raise ExceptionGroup(
            "booboo", [RuntimeError("handled"), RuntimeError("unhandled")]
        ) from ValueError("cause")

    assert excgrp.value.__cause__ is None
    assert excgrp.value.__suppress_context__
    if not PYPY:
        assert excgrp.value.__context__ is matched


def test_handler_raises_subgroup_from_matched():
    matched = None

    def handler(excgrp):
        nonlocal matched
        matched = excgrp
        _, rest = excgrp.split(lambda exc: str(exc) == "handled")
        raise rest from excgrp

    with pytest.raises(ExceptionGroup) as excgrp, catch({RuntimeError: handler}):
        raise ExceptionGroup(
            "booboo", [RuntimeError("handled"), RuntimeError("unhandled")]
        ) from ValueError("cause")

    assert excgrp.value.__cause__ is matched
    if not PYPY:
        assert excgrp.value.__context__ is matched


def test_bare_raise_in_handler_preserves_original_chaining():
    def handler(excgrp):
        raise

    context = KeyError("context")
    cause = ValueError("cause")
    handlers = {RuntimeError: handler, OSError: lambda eg: None}
    with pytest.raises(ExceptionGroup) as excgrp, catch(handlers):
        try:
            raise context
        except KeyError:
            raise ExceptionGroup("booboo", [RuntimeError(), OSError()]) from cause

    assert excgrp.value.__cause__ is cause
    assert excgrp.value.__context__ is context


def test_multiple_handlers_raise_not_chained_to_original():
    def handler(excgrp):
        raise ZeroDivisionError

    handlers = {RuntimeError: handler, OSError: handler}
    with pytest.raises(ExceptionGroup) as excgrp, catch(handlers):
        raise ExceptionGroup("booboo", [RuntimeError(), OSError()]) from ValueError(
            "cause"
        )

    assert excgrp.value.__cause__ is None
    assert excgrp.value.__context__ is None
    assert not excgrp.value.__suppress_context__


def test_catch_subclass():
    lookup_errors = []
    with catch({LookupError: lookup_errors.append}):
        raise KeyError("foo")

    assert len(lookup_errors) == 1
    assert isinstance(lookup_errors[0], ExceptionGroup)
    exceptions = lookup_errors[0].exceptions
    assert isinstance(exceptions[0], KeyError)


def test_async_handler(request):
    async def handler(eg):
        pass

    def delegate(eg):
        coro = handler(eg)
        request.addfinalizer(coro.close)
        return coro

    with pytest.raises(
        TypeError, match="Exception handler must be a sync function."
    ), catch({TypeError: delegate}):
        raise ExceptionGroup("message", [TypeError("uh-oh")])


def test_bare_reraise_from_naked_exception():
    def handler(eg):
        raise

    with pytest.raises(ExceptionGroup) as excgrp, catch({Exception: handler}):
        raise KeyError("foo")

    assert len(excgrp.value.exceptions) == 1
    assert isinstance(excgrp.value.exceptions[0], KeyError)
    assert str(excgrp.value.exceptions[0]) == "'foo'"
    assert excgrp.value.__cause__ is None
    assert excgrp.value.__context__ is None
    assert not excgrp.value.__suppress_context__


@pytest.mark.parametrize("handler_error_type", [RuntimeError, KeyboardInterrupt])
@pytest.mark.parametrize("multiple_handlers", [False, True])
def test_handler_raises_preserves_unmatched(handler_error_type, multiple_handlers):
    handled = ValueError("handled")
    unmatched = TypeError("unhandled")
    handler_error = handler_error_type("handler failed")
    original = BaseExceptionGroup("original", [handled, unmatched])
    seen = []

    def handler(group):
        seen.append(group)
        raise handler_error

    handlers = {ValueError: handler}
    if multiple_handlers:
        handlers[LookupError] = lambda group: None

    exceptions = ()
    try:
        with catch(handlers):
            raise original
    except BaseException as result:
        assert isinstance(result, BaseExceptionGroup)
        exceptions = result.exceptions

    assert len(exceptions) == 2
    assert exceptions[0] is handler_error
    remainder = exceptions[1]
    assert isinstance(remainder, ExceptionGroup)
    assert remainder.message == "original"
    assert remainder.exceptions == (unmatched,)
    assert seen[0].exceptions == (handled,)
    assert handler_error.__context__ is seen[0]


@pytest.mark.parametrize("reraise", [False, True], ids=["new_group", "bare_raise"])
def test_handler_raises_group_preserves_unmatched(reraise):
    unmatched = TypeError("unhandled")
    new_group = ExceptionGroup("new", [RuntimeError("handler failed")])
    seen = []

    def handler(group):
        seen.append(group)
        if reraise:
            raise
        raise new_group

    with pytest.raises(ExceptionGroup) as excgrp, catch({ValueError: handler}):
        raise ExceptionGroup("original", [ValueError("handled"), unmatched])

    assert len(excgrp.value.exceptions) == 2
    assert excgrp.value.exceptions[0] is (seen[0] if reraise else new_group)
    remainder = excgrp.value.exceptions[1]
    assert remainder.message == "original"
    assert remainder.exceptions == (unmatched,)


@pytest.mark.parametrize(
    "keys", [(ValueError, (ValueError,)), ((ValueError,), ValueError)]
)
def test_catch_equivalent_keys(keys):
    first, second = [], []
    leaf = ValueError("leaf")
    with catch({keys[0]: first.append, keys[1]: second.append}):
        raise ExceptionGroup("root", [leaf])

    assert len(first) == 1
    assert second == []
    assert first[0].message == "root"
    assert len(first[0].exceptions) == 1
    assert first[0].exceptions[0] is leaf


@pytest.mark.parametrize("original_error_type", [ValueError, KeyboardInterrupt])
@pytest.mark.parametrize("chaining", ["implicit", "explicit", "suppressed"])
def test_handler_raises_from_naked_exception_preserves_chaining(
    original_error_type, chaining
):
    original = original_error_type("original")
    handler_error = RuntimeError("handler failed")
    cause = KeyError("explicit cause")
    seen = []

    def handler(group):
        seen.append(group)
        if chaining == "explicit":
            raise handler_error from cause
        elif chaining == "suppressed":
            raise handler_error from None
        raise handler_error

    with pytest.raises(RuntimeError) as result, catch({original_error_type: handler}):
        raise original

    assert result.value is handler_error
    assert handler_error.__context__ is seen[0]
    assert seen[0].exceptions == (original,)
    assert handler_error.__cause__ is (cause if chaining == "explicit" else None)
    assert handler_error.__suppress_context__ is (chaining != "implicit")

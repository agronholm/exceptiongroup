import sys

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

    with pytest.raises(RuntimeError, match="new") as exc:
        with catch({(ValueError, ValueError): handler}):
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

    with pytest.raises(ExceptionGroup) as excgrp:
        with catch({(ValueError,): handler, (RuntimeError,): lambda eg: None}):
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

    with pytest.raises(TypeError, match="Exception handler must be a sync function."):
        with catch({TypeError: delegate}):
            raise ExceptionGroup("message", [TypeError("uh-oh")])


def test_bare_reraise_from_naked_exception():
    def handler(eg):
        raise

    with pytest.raises(ExceptionGroup) as excgrp, catch({Exception: handler}):
        raise KeyError("foo")

    assert len(excgrp.value.exceptions) == 1
    assert isinstance(excgrp.value.exceptions[0], KeyError)
    assert str(excgrp.value.exceptions[0]) == "'foo'"


class _HashableTypes:
    def __init__(self, types):
        self.types = types

    def __iter__(self):
        return iter(self.types)


class _FirstError(Exception):
    pass


class _LaterError(Exception):
    pass


@pytest.mark.parametrize(
    "keys", [(ValueError, (ValueError,)), ((ValueError,), ValueError)]
)
@pytest.mark.parametrize("grouped", [False, True])
def test_equivalent_keys_keep_first_handler(keys, grouped):
    leaf = ValueError("leaf")
    original = ExceptionGroup("root", [leaf]) if grouped else leaf
    first, second = [], []
    with catch({keys[0]: first.append, keys[1]: second.append}):
        raise original

    assert len(first) == 1
    assert second == []
    assert first[0].exceptions == (leaf,)
    assert first[0].message == ("root" if grouped else "")


@pytest.mark.parametrize(
    "keys", [(ValueError, (ValueError,)), ((ValueError,), ValueError)]
)
def test_equivalent_keys_preserve_nested_leaf_identity(keys):
    leaf = ValueError("leaf")
    original = ExceptionGroup("root", [ExceptionGroup("nested", [leaf])])
    first, second = [], []
    with catch({keys[0]: first.append, keys[1]: second.append}):
        raise original

    assert len(first) == 1
    assert second == []
    assert first[0].message == "root"
    assert first[0].exceptions[0].message == "nested"
    assert first[0].exceptions[0].exceptions[0] is leaf


@pytest.mark.parametrize("alias_first", [False, True])
def test_hashable_iterable_alias_keeps_mapping_order(alias_first):
    alias = _HashableTypes((ValueError,))
    keys = (alias, ValueError) if alias_first else (ValueError, alias)
    first, second = [], []
    leaf = ValueError("leaf")
    with catch({keys[0]: first.append, keys[1]: second.append}):
        raise leaf

    assert len(first) == 1
    assert first[0].exceptions[0] is leaf
    assert second == []


def test_mapping_iteration_order_controls_priority():
    class ReverseMapping(dict):
        def items(self):
            return iter(tuple(super().items())[::-1])

    first, second = [], []
    leaf = ValueError("leaf")
    handlers = ReverseMapping({ValueError: first.append, (ValueError,): second.append})
    with catch(handlers):
        raise leaf

    assert first == []
    assert len(second) == 1
    assert second[0].exceptions[0] is leaf


def test_overlapping_and_repeated_types_receive_remaining_leaves():
    value, type_error, lookup = ValueError(), TypeError(), KeyError()
    first, second, third = [], [], []
    with catch(
        {
            (ValueError, TypeError): first.append,
            (TypeError, LookupError, LookupError): second.append,
            (ValueError,): third.append,
        }
    ):
        raise ExceptionGroup("root", [value, type_error, lookup])

    assert first[0].exceptions == (value, type_error)
    assert second[0].exceptions == (lookup,)
    assert first[0].message == second[0].message == "root"
    assert third == []


@pytest.mark.parametrize(
    "keys", [(BaseException, (BaseException,)), ((BaseException,), BaseException)]
)
def test_equivalent_baseexception_keys_preserve_subclasses(keys):
    class ChildError(ValueError):
        pass

    child, interrupt = ChildError("child"), KeyboardInterrupt("interrupt")
    first, second = [], []
    with catch({keys[0]: first.append, keys[1]: second.append}):
        raise BaseExceptionGroup(
            "root", [child, BaseExceptionGroup("nested", [interrupt])]
        )

    assert len(first) == 1
    assert second == []
    assert first[0].exceptions[0] is child
    assert first[0].exceptions[1].message == "nested"
    assert first[0].exceptions[1].exceptions[0] is interrupt


@pytest.mark.parametrize(
    "keys",
    [
        (_FirstError, (_FirstError,)),
        ((_FirstError,), _FirstError),
        (_FirstError, (_FirstError, _FirstError)),
    ],
)
def test_later_entry_matches_leaf_mutated_by_first_handler(keys):
    first_leaf, later_leaf = _FirstError("first"), _LaterError("later")
    first, second, remaining = [], [], []

    def mutate(group):
        first.append(group)
        later_leaf.__class__ = _FirstError

    with catch(
        {keys[0]: mutate, keys[1]: second.append, _LaterError: remaining.append}
    ):
        raise ExceptionGroup("root", [first_leaf, later_leaf])

    assert len(first) == len(second) == 1
    assert first[0].exceptions == (first_leaf,)
    assert second[0].exceptions == (later_leaf,)
    assert remaining == []


def test_shared_callback_runs_for_each_distinct_matching_entry():
    value, type_error = ValueError(), TypeError()
    seen = []
    with catch({ValueError: seen.append, TypeError: seen.append}):
        raise ExceptionGroup("root", [value, type_error])

    assert len(seen) == 2
    assert seen[0].exceptions == (value,)
    assert seen[1].exceptions == (type_error,)


def test_shared_callback_keeps_equivalent_entries_after_mutation():
    first_leaf, later_leaf = _FirstError("first"), _LaterError("later")
    seen, remaining = [], []

    def handler(group):
        seen.append(group)
        later_leaf.__class__ = _FirstError

    with catch(
        {
            _FirstError: handler,
            (_FirstError,): handler,
            _LaterError: remaining.append,
            BaseException: remaining.append,
        }
    ):
        raise ExceptionGroup("root", [first_leaf, later_leaf])

    assert len(seen) == 2
    assert seen[0].exceptions == (first_leaf,)
    assert seen[1].exceptions == (later_leaf,)
    assert remaining == []


def test_catcher_snapshots_mapping_and_can_be_reused():
    seen, replacement = [], []
    handlers = {ValueError: seen.append, (ValueError,): replacement.append}
    catcher = catch(handlers)
    handlers.clear()
    handlers[ValueError] = replacement.append
    leaves = [ValueError("one"), ValueError("two")]
    for leaf in leaves:
        with catcher:
            raise leaf

    assert len(seen) == 2
    assert seen[0].exceptions == (leaves[0],)
    assert seen[1].exceptions == (leaves[1],)
    assert replacement == []


def test_handler_mapping_mutation_does_not_change_current_or_reused_catcher():
    seen, replaced = [], []

    def mutate(group):
        seen.append(group)
        handlers.clear()
        handlers[TypeError] = replaced.append

    handlers = {ValueError: mutate, TypeError: seen.append}
    catcher = catch(handlers)
    value, type_error = ValueError(), TypeError()
    for _ in range(2):
        with catcher:
            raise ExceptionGroup("root", [value, type_error])

    assert len(seen) == 4
    assert seen[1].exceptions == (type_error,)
    assert seen[3].exceptions == (type_error,)
    assert replaced == []


def test_iterable_key_is_consumed_at_construction():
    events, seen = [], []

    def types():
        events.append("iterated")
        yield ValueError

    key = types()
    catcher = catch({key: seen.append})
    assert events == ["iterated"]
    assert tuple(key) == ()
    with catcher:
        raise ValueError("leaf")

    assert len(seen) == 1
    assert events == ["iterated"]


def test_iterable_contents_are_snapshotted():
    types, seen = [ValueError], []
    catcher = catch({_HashableTypes(types): seen.append})
    types[:] = [TypeError]
    leaf = ValueError("leaf")
    with catcher:
        raise leaf

    assert seen[0].exceptions == (leaf,)


@pytest.mark.parametrize("argument", [None, 1, [], ()])
def test_invalid_mapping_is_rejected_at_construction(argument):
    with pytest.raises(TypeError) as caught:
        catch(argument)

    assert str(caught.value) == "the argument must be a mapping"


@pytest.mark.parametrize("key", [1, str, "bad", (ValueError, 1), (ValueError, str)])
def test_invalid_key_is_rejected_at_construction(key):
    with pytest.raises(TypeError) as caught:
        catch({key: list.append})

    assert (
        str(caught.value)
        == "each key must be either an exception classes or an iterable thereof"
    )


@pytest.mark.parametrize("group_type", [BaseExceptionGroup, ExceptionGroup])
def test_group_subclass_is_rejected_at_construction(group_type):
    class ChildGroup(group_type):
        pass

    with pytest.raises(TypeError) as caught:
        catch({(ValueError, ChildGroup): list.append})

    assert (
        str(caught.value)
        == "catching ExceptionGroup with catch() is not allowed. Use except instead."
    )


@pytest.mark.parametrize(
    "keys", [(ValueError, (ValueError,)), ((ValueError,), ValueError)]
)
def test_colliding_noncallable_handler_is_still_validated(keys):
    with pytest.raises(TypeError) as caught:
        catch({keys[0]: list.append, keys[1]: None})

    assert str(caught.value) == "handlers must be callable"


@pytest.mark.parametrize("key", [(str,), (ExceptionGroup,), (ValueError, 1)])
def test_callable_validation_precedes_element_validation(key):
    with pytest.raises(TypeError) as caught:
        catch({key: None})

    assert str(caught.value) == "handlers must be callable"


def test_key_conversion_precedes_callable_validation():
    error = RuntimeError("iteration failed")

    class BrokenTypes:
        def __iter__(self):
            raise error

    with pytest.raises(RuntimeError) as caught:
        catch({BrokenTypes(): None})

    assert caught.value is error


def test_validation_stops_before_converting_later_key():
    events = []

    class LaterTypes:
        def __iter__(self):
            events.append("iterated")
            return iter((TypeError,))

    with pytest.raises(TypeError, match="handlers must be callable"):
        catch({ValueError: None, LaterTypes(): list.append})

    assert events == []


def _expected_chained_context(original, previous_context, cause):
    """Use ordinary raise semantics to determine the final context identity."""
    active = ValueError("context control")
    control = RuntimeError("context control")
    control.__context__ = previous_context
    control.__cause__ = cause
    with pytest.raises(RuntimeError) as caught:
        try:
            raise active
        except ValueError:
            raise control from active
    assert caught.value is control
    assert control.__cause__ is active
    if control.__context__ is active:
        return original
    assert control.__context__ is previous_context
    return previous_context


@pytest.mark.parametrize("mode", ["bare", "explicit"])
def test_handler_reraise_preserves_active_exception_and_identity(mode):
    seen = []
    leaf = ValueError("leaf")

    def handler(group):
        assert sys.exc_info()[1] is group
        seen.append(group)
        if mode == "bare":
            raise
        raise group

    with pytest.raises(ExceptionGroup) as caught:
        with catch({ValueError: handler}):
            raise leaf

    assert caught.value is seen[0]
    assert caught.value.exceptions == (leaf,)
    assert caught.value.__cause__ is leaf
    assert caught.value.__context__ is _expected_chained_context(leaf, None, None)


def test_new_handler_error_is_not_dispatched_to_later_handlers():
    error, cause, leaf = (
        RuntimeError("handler"),
        LookupError("cause"),
        ValueError("leaf"),
    )
    seen, later = [], []

    def handler(group):
        assert sys.exc_info()[1] is group
        seen.append(group)
        raise error from cause

    with pytest.raises(RuntimeError) as caught:
        with catch({ValueError: handler, RuntimeError: later.append}):
            raise leaf

    assert caught.value is error
    assert later == []
    assert seen[0].exceptions == (leaf,)
    assert caught.value.__cause__ is leaf
    assert caught.value.__context__ is _expected_chained_context(leaf, seen[0], cause)


def test_group_reraise_preserves_cause_and_context():
    cause, leaf, seen = LookupError("cause"), ValueError("leaf"), []

    def handler(group):
        seen.append(group)
        raise

    with pytest.raises(ExceptionGroup) as caught:
        with catch({ValueError: handler}):
            raise ExceptionGroup("root", [leaf]) from cause

    assert caught.value is seen[0]
    assert caught.value.exceptions == (leaf,)
    assert caught.value.__cause__ is cause
    assert caught.value.__context__ is cause


def test_multiple_handler_errors_preserve_identity_and_order():
    errors = [RuntimeError("first"), KeyboardInterrupt("second")]

    def first(group):
        raise errors[0]

    def second(group):
        raise errors[1]

    with pytest.raises(BaseExceptionGroup) as caught:
        with catch({ValueError: first, TypeError: second}):
            raise ExceptionGroup("root", [ValueError(), TypeError()])

    assert caught.value.exceptions == tuple(errors)
    assert caught.value.exceptions[0] is errors[0]
    assert caught.value.exceptions[1] is errors[1]


def test_coroutine_rejection_preserves_original_cause(request):
    original, later = ValueError("leaf"), []

    async def async_handler(group):
        pass

    def handler(group):
        coro = async_handler(group)
        request.addfinalizer(coro.close)
        return coro

    with pytest.raises(
        TypeError, match="Exception handler must be a sync function."
    ) as caught:
        with catch({ValueError: handler, TypeError: later.append}):
            raise original

    assert caught.value.__cause__ is original
    assert caught.value.__context__ is original
    assert later == []


@pytest.mark.parametrize("empty_tuple", [False, True])
def test_empty_handlers_preserve_unmatched_naked_exception(empty_tuple):
    seen = []
    original = ValueError("leaf")
    handlers = {(): seen.append} if empty_tuple else {}
    with pytest.raises(ValueError) as caught:
        with catch(handlers):
            raise original

    assert caught.value is original
    assert seen == []


@pytest.mark.parametrize("handlers", [{}, {(): list.append}, {TypeError: list.append}])
def test_unmatched_group_preserves_leaf_identity(handlers):
    leaf = ValueError("leaf")
    with pytest.raises(ExceptionGroup) as caught:
        with catch(handlers):
            raise ExceptionGroup("root", [leaf])

    assert caught.value.message == "root"
    assert caught.value.exceptions == (leaf,)


def test_normal_completion_does_not_call_handlers():
    seen = []
    with catch({ValueError: seen.append, (ValueError,): seen.append}):
        pass

    assert seen == []

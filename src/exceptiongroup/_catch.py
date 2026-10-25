from __future__ import annotations

import inspect
import sys
from collections.abc import Callable, Iterable, Mapping
from contextlib import AbstractContextManager
from types import TracebackType
from typing import TYPE_CHECKING, Any

if sys.version_info < (3, 11):
    from ._exceptions import BaseExceptionGroup

if TYPE_CHECKING:
    _Handler = Callable[[BaseExceptionGroup[Any]], Any]


class _Catcher:
    def __init__(
        self, handler_entries: list[tuple[tuple[type[BaseException], ...], _Handler]]
    ):
        self._handler_entries = handler_entries

    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        etype: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        if exc is not None:
            unhandled = self.handle_exception(exc)
            if unhandled is exc:
                return False
            elif unhandled is None:
                return True
            else:
                if isinstance(exc, BaseExceptionGroup):
                    # Raising here would set __context__ to the original group, so
                    # restore the chaining set by split() or by the handler
                    context = unhandled.__context__
                    try:
                        raise unhandled
                    finally:
                        unhandled.__context__ = context

                raise unhandled from exc

        return False

    def handle_exception(self, exc: BaseException) -> BaseException | None:
        excgroup: BaseExceptionGroup | None
        if isinstance(exc, BaseExceptionGroup):
            excgroup = exc
        else:
            excgroup = BaseExceptionGroup("", [exc])

        new_exceptions: list[BaseException] = []
        for exc_types, handler in self._handler_entries:
            matched, excgroup = excgroup.split(exc_types)
            if matched:
                context = matched.__context__
                try:
                    try:
                        raise matched
                    except BaseExceptionGroup:
                        matched.__context__ = context
                        result = handler(matched)
                except BaseException as new_exc:
                    new_exceptions.append(new_exc)
                else:
                    if inspect.iscoroutine(result):
                        raise TypeError(
                            f"Error trying to handle {matched!r} with {handler!r}. "
                            "Exception handler must be a sync function."
                        ) from exc

            if not excgroup:
                break

        if new_exceptions:
            if len(new_exceptions) == 1:
                return new_exceptions[0]

            return BaseExceptionGroup("", new_exceptions)
        elif (
            excgroup and len(excgroup.exceptions) == 1 and excgroup.exceptions[0] is exc
        ):
            return exc
        else:
            return excgroup


def catch(
    __handlers: Mapping[type[BaseException] | Iterable[type[BaseException]], _Handler],
) -> AbstractContextManager[None]:
    if not isinstance(__handlers, Mapping):
        raise TypeError("the argument must be a mapping")

    handler_entries: list[tuple[tuple[type[BaseException], ...], _Handler]] = []
    for type_or_iterable, handler in __handlers.items():
        iterable: tuple[type[BaseException]]
        if isinstance(type_or_iterable, type) and issubclass(
            type_or_iterable, BaseException
        ):
            iterable = (type_or_iterable,)
        elif isinstance(type_or_iterable, Iterable):
            iterable = tuple(type_or_iterable)
        else:
            raise TypeError(
                "each key must be either an exception classes or an iterable thereof"
            )

        if not callable(handler):
            raise TypeError("handlers must be callable")

        for exc_type in iterable:
            if not isinstance(exc_type, type) or not issubclass(
                exc_type, BaseException
            ):
                raise TypeError(
                    "each key must be either an exception classes or an iterable "
                    "thereof"
                )

            if issubclass(exc_type, BaseExceptionGroup):
                raise TypeError(
                    "catching ExceptionGroup with catch() is not allowed. "
                    "Use except instead."
                )

        handler_entries.append((iterable, handler))

    return _Catcher(handler_entries)

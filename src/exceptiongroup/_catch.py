from __future__ import annotations

import sys
from collections.abc import Callable, Iterable, Mapping
from contextlib import AbstractContextManager
from types import TracebackType
from typing import TYPE_CHECKING, Any

if sys.version_info < (3, 11):
    from ._exceptions import BaseExceptionGroup

if TYPE_CHECKING:
    _Handler = Callable[[BaseException], Any]


class _Catcher:
    def __init__(self, handler_map: Mapping[type[BaseException], _Handler]):
        self._handler_map = handler_map
        self._exc_types = tuple(handler_map)

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
                raise unhandled from None

        return False

    def handle_exception(self, exc: BaseException) -> BaseException | None:
        if isinstance(exc, BaseExceptionGroup):
            matched, unmatched = exc.split(self._exc_types)
            matched_exceptions = matched.exceptions if matched else ()
            unhandled_exceptions: list[BaseException] = [unmatched] if unmatched else []

            # Match the exceptions against the given type(s) and call this method to
            # handle the individual exceptions
            for matched_exc in matched_exceptions:
                unhandled_exc = self.handle_exception(matched_exc)
                if unhandled_exc is not None:
                    unhandled_exceptions.append(unhandled_exc)

            if unhandled_exceptions:
                return BaseExceptionGroup("", unhandled_exceptions)
            else:
                return None

        handler = self._handler_map.get(type(exc))
        if handler is not None:
            try:
                handler(exc)
            except BaseException as new_exc:
                return new_exc
            else:
                return None
        else:
            return exc


def catch(
    __handlers: Mapping[type[BaseException] | Iterable[type[BaseException]], _Handler]
) -> AbstractContextManager[None]:
    if not isinstance(__handlers, Mapping):
        raise TypeError("the argument must be a mapping")

    handler_map = {}
    for type_or_iterable, handler in __handlers.items():
        iterable: Iterable[type[BaseException]]
        if isinstance(type_or_iterable, type):
            iterable = (type_or_iterable,)
        elif isinstance(type_or_iterable, Iterable):
            iterable = type_or_iterable
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

            handler_map[exc_type] = handler

    return _Catcher(handler_map)

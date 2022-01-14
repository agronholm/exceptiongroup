from __future__ import annotations

import sys
from collections.abc import Iterable
from inspect import isclass
from types import TracebackType
from typing import Any, Callable, ContextManager

if sys.version_info < (3, 11):
    from ._exceptions import BaseExceptionGroup


class _Catcher:
    def __init__(
        self,
        exc_type: type[BaseException] | tuple[type[BaseException], ...],
        handler: Callable[[BaseException], bool | None],
    ):
        self._exc_type = exc_type
        self._handler = handler

    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        etype: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None:
        if exc is not None:
            unhandled = self.handle_exception(exc)
            if unhandled is exc:
                return False
            elif unhandled is None:
                return True
            else:
                raise unhandled from None

    def handle_exception(self, exc: BaseException) -> BaseException | None:
        if not isinstance(exc, BaseExceptionGroup):
            if isinstance(exc, self._exc_type):
                try:
                    self._handler(exc)
                except BaseException as new_exc:
                    return new_exc
                else:
                    return None
            else:
                return exc

        matched, unmatched = exc.split(self._exc_type)
        matched_exceptions = matched.exceptions if matched else ()
        unhandled_exceptions: list[BaseException] = [unmatched] if unmatched else []

        # Match the exceptions against the given type(s) and call the handlers
        for matched_exc in matched_exceptions:
            unhandled_exc = self.handle_exception(matched_exc)
            if unhandled_exc is not None:
                unhandled_exceptions.append(unhandled_exc)

        if unhandled_exceptions:
            return BaseExceptionGroup("", unhandled_exceptions)
        else:
            return None


def catch(
    exc_type: type[BaseException] | tuple[type[BaseException], ...],
    handler: Callable[[BaseException], Any],
) -> ContextManager[None]:
    _exc_types = exc_type if isinstance(exc_type, Iterable) else [exc_type]
    for type_ in _exc_types:
        if not isclass(type_) or not issubclass(type_, BaseException):
            raise TypeError("exc_type must be an exception class")
        elif issubclass(type_, BaseExceptionGroup):
            raise TypeError(
                "catching ExceptionGroup with catch() is not allowed. "
                "Use except instead."
            )

    return _Catcher(exc_type, handler)

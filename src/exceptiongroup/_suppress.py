import sys
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Type

if sys.version_info < (3, 11):
    from ._exceptions import BaseExceptionGroup


class suppress(AbstractContextManager[None]):
    """Backport of :class:`contextlib.suppress` from Python 3.12.1."""

    def __init__(self, *exceptions: BaseException):
        self._exceptions = exceptions

    def __enter__(self) -> None:
        pass

    def __exit__(
        self, exctype: Type[BaseException], excinst: BaseException, exctb: TracebackType
    ) -> bool:
        # Unlike isinstance and issubclass, CPython exception handling
        # currently only looks at the concrete type hierarchy (ignoring
        # the instance and subclass checking hooks). While Guido considers
        # that a bug rather than a feature, it's a fairly hard one to fix
        # due to various internal implementation details. suppress provides
        # the simpler issubclass based semantics, rather than trying to
        # exactly reproduce the limitations of the CPython interpreter.
        #
        # See http://bugs.python.org/issue12029 for more details
        if exctype is None:
            return False

        if issubclass(exctype, self._exceptions):
            return True

        if issubclass(exctype, BaseExceptionGroup):
            match, rest = excinst.split(self._exceptions)
            if rest is None:
                return True

            raise rest

        return False

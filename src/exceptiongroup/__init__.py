__all__ = ["BaseExceptionGroup", "ExceptionGroup", "catch"]

import sys

from ._catch import catch
from ._version import version as __version__  # noqa: F401

if sys.version_info < (3, 11):
    from . import _formatting  # noqa: F401
    from ._exceptions import BaseExceptionGroup, ExceptionGroup

    BaseExceptionGroup.__module__ = __name__
    ExceptionGroup.__module__ = __name__
else:
    BaseExceptionGroup = BaseExceptionGroup
    ExceptionGroup = ExceptionGroup

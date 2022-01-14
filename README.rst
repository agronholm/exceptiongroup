.. image:: https://github.com/agronholm/exceptiongroup/actions/workflows/test.yml/badge.svg
  :target: https://github.com/agronholm/exceptiongroup/actions/workflows/test.yml
  :alt: Build Status
.. image:: https://coveralls.io/repos/github/agronholm/exceptiongroup/badge.svg?branch=main
  :target: https://coveralls.io/github/agronholm/exceptiongroup?branch=main
  :alt: Code Coverage

This is a backport of the ``BaseExceptionGroup`` and ``ExceptionGroup`` classes from
Python 3.11.

It contains the following:

* The  ``exceptiongroup.BaseExceptionGroup`` and ``exceptiongroup.ExceptionGroup``
  classes
* A utility function (``exceptiongroup.catch()``) for catching exceptions possibly
  nested in an exception group
* Patches to the ``TracebackException`` class that properly formats exception groups
  (installed on import)
* An exception hook that handles formatting of exception groups through
  ``TracebackException`` (installed on import)

The only difference with the Python 3.11 standard library implementation is that there
is no ``__note__`` attribute in ``BaseExceptionGroup`` or ``ExceptionGroup``.

If this package is imported on Python 3.11 or later, the built-in implementations of the
exception group classes are used instead, ``TracebackException`` is not monkey patched
and the exception hook won't be installed.

See the `standard library documentation`_ for more information on exception groups.

.. _standard library documentation: https://docs.python.org/3/library/exceptions.html

Catching exceptions
===================

Due to the lack of the ``except*`` syntax introduced by `PEP 654`_ in earlier Python
versions, you need to use ``exceptiongroup.catch()`` to catch exceptions that are
potentially nested inside an exception group. This function returns a context manager
that calls the given handler for any exceptions matching the first argument.

So, the following Python 3.11+ code:

.. code-block:: python3

    try:
        ...
    except* (ValueError, KeyError) as exc:
        print('Caught exception:', type(exc))

would be written as follows:

.. code-block:: python3

    from exceptiongroup import catch

    def handler(exc: Exception) -> None:
        print('Caught exception:', type(exc))

    with catch((ValueError, KeyError), handler):
        ...

.. note:: Just like with ``except*``, you cannot handle ``BaseExceptionGroup`` or
    ``ExceptionGroup`` with ``catch()``.

.. _PEP 654: https://www.python.org/dev/peps/pep-0654/

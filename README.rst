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
that calls the given handler for any exceptions matching the sole argument.

The argument to ``catch()`` must be a dict (or any ``Mapping``) where each key is either
an exception class or an iterable of exception classes. Each value must be a callable
that takes a single positional argument. The handler will be called at most once, with
an exception group as an argument which will contain all the exceptions that are any
of the given types, or their subclasses. The exception group may contain nested groups
containing more matching exceptions.

Thus, the following Python 3.11+ code:

.. code-block:: python3

    try:
        ...
    except* (ValueError, KeyError) as excgroup:
        for exc in excgroup.exceptions:
            print('Caught exception:', type(exc))
    except* RuntimeError:
        print('Caught runtime error')

would be written with this backport like this:

.. code-block:: python3

    from exceptiongroup import ExceptionGroup, catch

    def value_key_err_handler(excgroup: ExceptionGroup) -> None:
        for exc in excgroup.exceptions:
            print('Caught exception:', type(exc))

    def runtime_err_handler(exc: ExceptionGroup) -> None:
        print('Caught runtime error')

    with catch({
        (ValueError, KeyError): value_key_err_handler,
        RuntimeError: runtime_err_handler
    }):
        ...

**NOTE**: Just like with ``except*``, you cannot handle ``BaseExceptionGroup`` or
``ExceptionGroup`` with ``catch()``.

Notes on monkey patching
========================

To make exception groups render properly when an unhandled exception group is being
printed out, this package does two things when it is imported on any Python version
earlier than 3.11:

#. The  ``traceback.TracebackException`` class is monkey patched to store extra
   information about exception groups (in ``__init__()``) and properly format them (in
   ``format()``)
#. An exception hook is installed at ``sys.excepthook``, provided that no other hook is
   already present. This hook causes the exception to be formatted using
   ``traceback.TracebackException`` rather than the built-in rendered.

To prevent the exception hook and patches from being installed, set the environment
variable ``EXCEPTIONGROUP_NO_PATCH`` to ``1``.

.. _PEP 654: https://www.python.org/dev/peps/pep-0654/

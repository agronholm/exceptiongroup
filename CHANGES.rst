Version history
===============

This library adheres to `Semantic Versioning 2.0 <http://semver.org/>`_.

**UNRELEASED**

- Added custom versions of ``traceback.format_exception()``  and
  ``traceback.format_exception_only()`` that work with exception groups even if monkey
  patching was disabled or blocked

**1.0.0rc8**

- Don't monkey patch anything if ``sys.excepthook`` has been altered
- Fixed formatting of ``SyntaxError`` in the monkey patched
  ``TracebackException.format_exception_only()`` method

**1.0.0rc7**

- **BACKWARDS INCOMPATIBLE** Changed ``catch()`` to not wrap an exception in an
  exception group if only one exception arrived at ``catch()`` and it was not matched
  with any handlers. This was to match the behavior of ``except*``.

**1.0.0rc6**

- **BACKWARDS INCOMPATIBLE** Changed ``catch()`` to match the behavior of ``except*``:
  each handler will be called only once per key in the ``handlers`` dictionary, and with
  an exception group as the argument. Handlers now also catch subclasses of the given
  exception types, just like ``except*``.

**1.0.0rc5**

- Patch for ``traceback.TracebackException.format_exception_only()`` (PR by Zac Hatfield-Dodds)

**1.0.0rc4**

- Update `PEP 678`_ support to use ``.add_note()`` and ``__notes__`` (PR by Zac Hatfield-Dodds)

**1.0.0rc3**

- Added message about the number of sub-exceptions

**1.0.0rc2**

- Display and copy ``__note__`` (draft `PEP 678`_) if available (PR by Zac Hatfield-Dodds)

.. _PEP 678: https://www.python.org/dev/peps/pep-0678/

**1.0.0rc1**

- Initial release

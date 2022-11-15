Version history
===============

This library adheres to `Semantic Versioning 2.0 <http://semver.org/>`_.

**1.0.4**

- Fixed regression introduced in v1.0.3 where the code computing the suggestions would
  assume that both the ``obj`` attribute of ``AttributeError`` is always available, even
  though this is only true from Python 3.10 onwards
  (#43; PR by Carl Friedrich Bolz-Tereick)

**1.0.3**

- Fixed monkey patching breaking suggestions (on a ``NameError`` or ``AttributeError``)
  on Python 3.10 (#41; PR by Carl Friedrich Bolz-Tereick)

**1.0.2**

- Updated type annotations to match the ones in ``typeshed``

**1.0.1**

- Fixed formatted traceback missing exceptions beyond 2 nesting levels of
  ``__context__`` or ``__cause__``

**1.0.0**

- Fixed
  ``AttributeError: 'PatchedTracebackException' object has no attribute '__cause__'``
  on Python 3.10 (only) when a traceback is printed from an exception where an exception
  group is set as the cause (#33)
- Fixed a loop in exception groups being rendered incorrectly (#35)
- Fixed the patched formatting functions (``format_exception()``etc.) not passing the
  ``compact=True`` flag on Python 3.10 like the original functions do

**1.0.0rc9**

- Added custom versions of several ``traceback``  functions that work with exception
  groups even if monkey patching was disabled or blocked

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

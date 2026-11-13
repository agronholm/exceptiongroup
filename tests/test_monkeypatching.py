from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

import exceptiongroup


@pytest.mark.skipif(
    sys.version_info >= (3, 11), reason="No patching is done on Python >= 3.11"
)
@pytest.mark.parametrize("no_patch", [None, "", "0", "1"])
@pytest.mark.parametrize(
    "hook", ["default", "custom", "apport_excepthook", "partial_apport_excepthook"]
)
def test_import_monkeypatching(no_patch: str | None, hook: str) -> None:
    env = dict(os.environ)
    if no_patch is None:
        env.pop("EXCEPTIONGROUP_NO_PATCH", None)
    else:
        env["EXCEPTIONGROUP_NO_PATCH"] = no_patch

    code = """
import io
import os
import sys
import traceback
from pathlib import Path
from types import ModuleType

assert "exceptiongroup" not in sys.modules
sys.path.insert(0, sys.argv[1])
hook = sys.argv[2]
sys.excepthook = sys.__excepthook__
if hook != "default":
    def custom_hook(*args):
        sys.__excepthook__(*args)
    custom_hook.__name__ = hook
    sys.excepthook = custom_hook
if hook in ("apport_excepthook", "partial_apport_excepthook"):
    apport = ModuleType("apport_python_hook")
    apport.sys = sys
    sys.modules["apport_python_hook"] = apport

before = (
    sys.excepthook,
    traceback.TracebackException.__init__,
    traceback.TracebackException.format,
    traceback.TracebackException.format_exception_only,
)
import exceptiongroup

assert Path(exceptiongroup.__file__).parent.parent == Path(sys.argv[1])
after = (
    sys.excepthook,
    traceback.TracebackException.__init__,
    traceback.TracebackException.format,
    traceback.TracebackException.format_exception_only,
)
patch_expected = os.environ.get("EXCEPTIONGROUP_NO_PATCH") != "1" and hook != "custom"
assert (before[0] is not after[0]) == (patch_expected and hook == "default"), "hook identity"
assert all((old is not new) == patch_expected for old, new in zip(before[1:], after[1:])), "traceback methods"
if hook in ("apport_excepthook", "partial_apport_excepthook"):
    assert (apport.sys is not sys) == patch_expected, "Apport sys reference"

group = exceptiongroup.ExceptionGroup("manual group", [ValueError("manual leaf")])
assert "manual group" in "".join(exceptiongroup.format_exception_only(group))
formatted = "".join(exceptiongroup.format_exception(group))
assert "manual group" in formatted and "manual leaf" in formatted
stream = io.StringIO()
exceptiongroup.print_exception(group, file=stream)
assert not stream.closed and "manual leaf" in stream.getvalue()
try:
    raise group
except exceptiongroup.ExceptionGroup:
    stream = io.StringIO()
    exceptiongroup.print_exc(file=stream)
    assert not stream.closed and "manual leaf" in stream.getvalue()
assert after == (
    sys.excepthook,
    traceback.TracebackException.__init__,
    traceback.TracebackException.format,
    traceback.TracebackException.format_exception_only,
), "manual formatting changed patch state"
"""
    package_path = str(Path(exceptiongroup.__file__).parent.parent)
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code, package_path, hook],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

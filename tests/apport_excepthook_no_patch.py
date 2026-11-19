# This script exists solely for test_apport_excepthook_no_patch()
#
# It uses a fake apport_python_hook module so it can run outside of Ubuntu's
# system Python.
import os
import sys
import traceback
from types import ModuleType

apport_python_hook = ModuleType("apport_python_hook")
apport_python_hook.sys = sys
sys.modules["apport_python_hook"] = apport_python_hook


def apport_excepthook(*args):
    sys.__excepthook__(*args)


sys.excepthook = apport_excepthook
os.environ["EXCEPTIONGROUP_NO_PATCH"] = "1"
from exceptiongroup import ExceptionGroup  # unsorted import

assert apport_python_hook.sys is sys, "apport_python_hook.sys was replaced"

try:
    raise ExceptionGroup("msg1", [KeyError("msg2"), ValueError("msg3")])
except ExceptionGroup:
    traceback.print_exc()

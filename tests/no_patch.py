# This script exists solely for test_no_patch_env_var()
import os
import sys
import traceback

os.environ["EXCEPTIONGROUP_NO_PATCH"] = "1"
excepthook = sys.excepthook
from exceptiongroup import ExceptionGroup  # unsorted import

assert sys.excepthook is excepthook, "sys.excepthook was replaced"

try:
    raise ExceptionGroup("msg1", [KeyError("msg2"), ValueError("msg3")])
except ExceptionGroup:
    traceback.print_exc()

# This script exists solely for test_unpatched_tracebackexception_format()
import pickle
import sys
import traceback

assert "exceptiongroup" not in sys.modules, "exceptiongroup was already imported"

try:
    raise ValueError("hello")
except ValueError as exc:
    tbe = traceback.TracebackException(type(exc), exc, exc.__traceback__)
    sys.stdout.buffer.write(pickle.dumps(tbe, protocol=pickle.HIGHEST_PROTOCOL))

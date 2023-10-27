import os
import subprocess
import sys
from pathlib import Path

import pytest

import exceptiongroup


def run_script(name: str) -> "subprocess.CompletedProcess[bytes]":
    exceptiongroup_path = Path(exceptiongroup.__file__).parent.parent
    script_path = Path(__file__).parent / name

    env = dict(os.environ)
    print("parent PYTHONPATH:", env.get("PYTHONPATH"))
    if "PYTHONPATH" in env:  # pragma: no cover
        pp = env["PYTHONPATH"].split(os.pathsep)
    else:
        pp = []
    pp.insert(0, str(exceptiongroup_path))
    pp.insert(0, str(script_path.parent))
    env["PYTHONPATH"] = os.pathsep.join(pp)
    print("subprocess PYTHONPATH:", env.get("PYTHONPATH"))

    cmd = [sys.executable, "-u", str(script_path)]
    print("running:", cmd)
    completed = subprocess.run(
        cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    print("process output:")
    print(completed.stdout.decode("utf-8"))
    return completed


def assert_match_in_seq(pattern_list, string):
    import re

    offset = 0
    print("looking for pattern matches...")
    for pattern in pattern_list:
        print("checking pattern:", pattern)
        reobj = re.compile(pattern)
        match = reobj.search(string, offset)
        assert match is not None
        offset = match.end()


@pytest.mark.skipif(
    not Path("/usr/lib/python3/dist-packages/apport_python_hook.py").exists(),
    reason="need Ubuntu with python3-apport installed",
)
def test_apport_excepthook_monkeypatch_interaction():
    completed = run_script("apport_excepthook.py")
    stdout = completed.stdout.decode("utf-8")

    # No warning
    assert "custom sys.excepthook" not in stdout

    # Proper traceback
    assert_match_in_seq(
        [
            "ExceptionGroup",
            "group_error",
            "KeyError",
            "key_error",
            "ValueError",
            "value_error",
        ],
        stdout,
    )

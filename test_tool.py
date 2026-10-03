"""
test_tool.py  —  Rung 2 of the Docker test-runner: run tests (no Docker yet)

A "tool" like run_linter, but instead of checking code, it RUNS the code's
tests with pytest and reports what passed/failed.

Right now it runs directly on your machine (safe, because YOU wrote the test
code here). Next rung wraps this exact idea in a Docker container, so it's
safe to run code that came from a stranger's pull request.

SETUP (once, in your venv):
    pip install pytest

RUN:
    python test_tool.py
"""

import subprocess
import tempfile
import os


def run_tests(code: str, test_code: str) -> str:
    """Write the code + its test to a temp folder, run pytest, return the result."""
    # 1) A throwaway folder to hold both files.
    with tempfile.TemporaryDirectory() as tmpdir:
        # the code under test
        with open(os.path.join(tmpdir, "solution.py"), "w") as f:
            f.write(code)
        # the tests (they import from solution.py)
        with open(os.path.join(tmpdir, "test_solution.py"), "w") as f:
            f.write(test_code)

        # 2) Run pytest inside that folder and capture its output.
        result = subprocess.run(
            ["python", "-m", "pytest", "-q", tmpdir],
            capture_output=True,
            text=True,
            timeout=30,          # don't let a hanging test run forever
        )

    # 3) Hand back what pytest printed (both normal + error output).
    return (result.stdout + result.stderr).strip()


if __name__ == "__main__":
    # Example: a buggy add() and a test that should FAIL it.
    solution = '''
def add(a, b):
    return a - b          # BUG: subtracts instead of adds
'''
    tests = '''
from solution import add

def test_add():
    assert add(2, 3) == 5
'''

    print("Running the tests...\n")
    print(run_tests(solution, tests))
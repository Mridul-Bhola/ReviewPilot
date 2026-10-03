"""
docker_test_tool.py  —  run tests inside a Docker sandbox

Two entry points:
  run_tests_in_docker(code, test_code)  -> demo on a single code+test pair
  run_pr_tests(files)                   -> real use: runs a PR's test files

Untrusted code runs trapped in a network-isolated, resource-capped,
auto-deleted container, so it can't touch your real machine.

ONE-TIME SETUP (in the folder with the Dockerfile):
    docker build -t reviewpilot-sandbox .
"""

import subprocess
import tempfile
import shutil
import os

IMAGE = "reviewpilot-sandbox"


def _run_pytest_on_dir(workdir: str) -> str:
    cmd = [
        "docker", "run", "--rm",
        "--network", "none",      # no internet inside
        "--memory", "256m",       # cap RAM
        "--cpus", "1",            # cap CPU
        "-v", f"{workdir}:/code", # mount our folder into the container
        IMAGE,
        "pytest", "-q", "/code",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return "Tests timed out (over 60s) and were stopped."
    except FileNotFoundError:
        return "(Docker not available, skipped test run.)"


def run_tests_in_docker(code: str, test_code: str) -> str:
    """Demo: one code file + one test file."""
    workdir = tempfile.mkdtemp(dir=os.getcwd())
    try:
        with open(os.path.join(workdir, "solution.py"), "w") as f:
            f.write(code)
        with open(os.path.join(workdir, "test_solution.py"), "w") as f:
            f.write(test_code)
        return _run_pytest_on_dir(workdir)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _looks_like_test(name: str) -> bool:
    base = os.path.basename(name)
    return base.startswith("test_") or base.endswith("_test.py")


def run_pr_tests(files: dict) -> str:
    """
    files: {filename: code} for the PR's changed .py files.
    Writes them all into a sandbox folder; if any are test files, runs pytest.
    """
    if not any(_looks_like_test(n) for n in files):
        return "(No test files in this PR, so no tests were run.)"

    workdir = tempfile.mkdtemp(dir=os.getcwd())
    try:
        for name, code in files.items():
            # flatten to basename so tests and code sit together and can import
            with open(os.path.join(workdir, os.path.basename(name)), "w") as f:
                f.write(code)
        return _run_pytest_on_dir(workdir)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    solution = '''
def add(a, b):
    return a - b          # BUG: subtracts instead of adds
'''
    tests = '''
from solution import add

def test_add():
    assert add(2, 3) == 5
'''
    print("Running the tests inside a Docker sandbox...\n")
    print(run_tests_in_docker(solution, tests))
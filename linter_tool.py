"""
linter_tool.py  —  Step 4, part 1: your first "tool"

An agent is smarter than a plain chatbot because it can USE TOOLS to check
things, instead of just guessing. This is your first tool: a linter -- an
automatic error-checker for Python code.

Right now this just proves the tool works on its own. No AI involved yet.
Later, the AI will call this and write its review based on what it finds.

SETUP (once, in your venv):
    pip install ruff

RUN IT:
    python linter_tool.py
"""

import subprocess
import tempfile
import os


def run_linter(code: str) -> str:
    """Run the 'ruff' linter on some Python code and return what it finds."""
    # 1) Write the code to a temporary file (the linter checks files, not text).
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = f.name

    # 2) Run the linter on that file and capture whatever it prints out.
    result = subprocess.run(
        ["ruff", "check", temp_path],
        capture_output=True,
        text=True,
    )

    # 3) Delete the temporary file now that we're done with it.
    os.remove(temp_path)

    # 4) Hand back the linter's report (or a friendly note if it was clean).
    output = result.stdout.strip()
    return output if output else "No issues found by the linter."


if __name__ == "__main__":
    # A sample with two planted problems: unused imports, and a typo'd variable
    # name ("nmae" instead of "name") that doesn't exist.
    sample_code = '''import os
import sys

def greet(name):
    print("Hello " + nmae)
'''

    print("Running the linter on the sample code...\n")
    report = run_linter(sample_code)
    print(report)
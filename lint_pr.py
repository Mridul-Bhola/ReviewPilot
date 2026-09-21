"""
lint_pr.py  —  Step 4c: run the linter on a real PR's Python files

This chains together the two tools you already built:
    fetch_py_files.py  -> gets the full .py files from a PR
    linter_tool.py     -> checks a file for bugs

So it fetches PR #3's Python files and runs the linter on each one,
catching real bugs on a real pull request.

RUN (with GITHUB_TOKEN exported):
    python lint_pr.py
"""

from fetch_py_files import parse_pr_url, get_pr_python_files
from linter_tool import run_linter

PR_URL = "https://github.com/Mridul-Bhola/pr-agent-test/pull/3"


if __name__ == "__main__":
    owner, repo, pr_number = parse_pr_url(PR_URL)
    print(f"Fetching Python files from PR #{pr_number}...\n")

    files = get_pr_python_files(owner, repo, pr_number)

    if not files:
        print("No Python files in this PR to lint.")

    for filename, code in files.items():
        print("=" * 60)
        print("LINTING:", filename)
        print("=" * 60)
        report = run_linter(code)   # <-- the linter tool checks this file
        print(report)
        print()
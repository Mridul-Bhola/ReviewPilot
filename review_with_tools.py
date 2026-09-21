"""
review_with_tools.py  —  Step 4d: an AI review grounded in tool findings

This is the "agentic" review. Instead of the AI just reading the diff and
guessing, we FIRST run the linter on the PR's Python files, then hand the
AI BOTH the code changes AND the linter's findings. The AI reviews with
real facts in hand.

It reuses everything you already built:
    get_pr_changes        (from pr_reviewer_step2) -> the diff
    get_pr_python_files   (from fetch_py_files)     -> the full .py files
    run_linter            (from linter_tool)        -> the linter findings

RUN (with GEMINI_API_KEY and GITHUB_TOKEN exported):
    python review_with_tools.py
"""

import os
from google import genai

from pr_reviewer_step2 import get_pr_changes
from fetch_py_files import parse_pr_url, get_pr_python_files
from linter_tool import run_linter

PR_URL = "https://github.com/Mridul-Bhola/pr-agent-test/pull/3"
MODEL = "gemini-3.6-flash"


def review_with_tools(pr_url: str) -> str:
    owner, repo, pr_number = parse_pr_url(pr_url)

    # 1) Get the code changes (diff).
    diff = get_pr_changes(pr_url)

    # 2) Get the full Python files and run the linter on each.
    py_files = get_pr_python_files(owner, repo, pr_number)
    linter_report = ""
    for name, code in py_files.items():
        linter_report += f"\n--- {name} ---\n{run_linter(code)}\n"
    if not linter_report.strip():
        linter_report = "(No Python files were changed, so the linter did not run.)"

    # 3) Give the AI BOTH the diff and the linter's findings.
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = f"""You are a senior software engineer reviewing a pull request.
You are given the code changes (a git diff) AND the output of an automated
linter that was already run on the changed Python files.

Treat the linter findings as verified facts. Explain them in plain language,
then add your own judgment on bugs, edge cases, and clarity. Keep it short
and practical, and mention file names.

LINTER FINDINGS:
{linter_report}

CODE CHANGES (diff):
{diff}
"""

    result = client.models.generate_content(model=MODEL, contents=prompt)
    return result.text


if __name__ == "__main__":
    print("Reviewing with tools (linter + AI)...\n")
    print(review_with_tools(PR_URL))
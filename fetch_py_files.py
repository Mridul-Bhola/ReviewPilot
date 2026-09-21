"""
fetch_py_files.py  —  Step 4b: get the full Python files a PR changes

The linter needs whole .py files, not just the diff. This asks GitHub which
files a PR touched, keeps the Python ones, and downloads each file's full
contents so the linter can check them.

RUN (with GITHUB_TOKEN exported in this terminal):
    python fetch_py_files.py
"""

import os
import requests

# Your open PR that contains a .py file.
PR_URL = "https://github.com/Mridul-Bhola/pr-agent-test/pull/3"


def parse_pr_url(pr_url: str):
    """'.../owner/repo/pull/3' -> ('owner', 'repo', '3')"""
    parts = pr_url.rstrip("/").split("/")
    return parts[-4], parts[-3], parts[-1]


def get_pr_python_files(owner: str, repo: str, pr_number: str) -> dict:
    """Return {filename: full_contents} for every .py file the PR changes."""
    headers = {
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github+json",
    }

    # 1) Ask GitHub for the list of files this PR touched.
    files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    response = requests.get(files_url, headers=headers, timeout=30)
    response.raise_for_status()
    changed_files = response.json()

    # 2) Keep only the Python files that still exist (not deleted), and
    #    download each one's full contents from the PR's branch.
    python_files = {}
    for f in changed_files:
        filename = f["filename"]
        if filename.endswith(".py") and f["status"] != "removed":
            content = requests.get(f["raw_url"], headers=headers, timeout=30).text
            python_files[filename] = content

    return python_files


if __name__ == "__main__":
    owner, repo, pr_number = parse_pr_url(PR_URL)
    print(f"Looking for Python files in PR #{pr_number}...\n")

    files = get_pr_python_files(owner, repo, pr_number)

    if not files:
        print("No Python files found in this PR.")
    for name, content in files.items():
        print("=" * 60)
        print("FILE:", name)
        print("=" * 60)
        print(content)
"""
repo_context.py  —  pull in related files from the SAME repo for cross-file context

When a PR changes a file, the real bug is often in a file it imports (e.g. you
called a function with the wrong arguments, but the function lives elsewhere).
This fetches the local files a changed file imports, so the reviewer sees them.

Works on ANY repo: it uses the PR's own owner/repo and head commit, so no
per-repo setup. Best-effort: standard-library and third-party imports simply
aren't found in the repo and are skipped.
"""

import os
import ast
import base64
import requests


def _headers():
    return {
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github+json",
    }


def get_pr_head_ref(owner, repo, pr_number):
    """The exact commit the PR is at, so we fetch files as the PR sees them."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    r = requests.get(url, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()["head"]["sha"]


def extract_local_imports(code):
    """Module names this code imports (e.g. 'utils', 'app.db'). Best-effort."""
    mods = set()
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return mods
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                mods.add(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:   # ignore relative imports for simplicity
                mods.add(node.module)
    return mods


def module_to_paths(mod):
    """'app.db' -> ['app/db.py', 'app/db/__init__.py']"""
    p = mod.replace(".", "/")
    return [f"{p}.py", f"{p}/__init__.py"]


def fetch_repo_file(owner, repo, path, ref):
    """Download one file's text from the repo at a commit, or None if absent."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    r = requests.get(url, headers=_headers(), params={"ref": ref}, timeout=30)
    if r.status_code != 200:
        return None
    data = r.json()
    if isinstance(data, dict) and data.get("encoding") == "base64":
        try:
            return base64.b64decode(data["content"]).decode("utf-8", "replace")
        except Exception:
            return None
    return None


def get_related_context(owner, repo, pr_number, changed_files,
                        max_files=5, max_chars=6000):
    """
    changed_files: {filename: code} for the PR's changed .py files.
    Returns {path: content} for local files those changed files import.
    Capped so the prompt doesn't blow up on big repos.
    """
    ref = get_pr_head_ref(owner, repo, pr_number)
    changed_names = set(changed_files.keys())
    context = {}
    for code in changed_files.values():
        for mod in extract_local_imports(code):
            for cand in module_to_paths(mod):
                if cand in changed_names or cand in context:
                    continue
                content = fetch_repo_file(owner, repo, cand, ref)
                if content:
                    context[cand] = content[:max_chars]
                    break
            if len(context) >= max_files:
                return context
    return context
"""
pr_reviewer_step2.py  —  Step 2 of your PR Review Agent

What's new since Step 1:
  Instead of just PRINTING the review, this now POSTS it as a comment
  on the pull request itself, so it shows up on GitHub like a real
  reviewer left it.

What you need set in this same terminal (you already did both):
  - GEMINI_API_KEY   (from Step 1)
  - GITHUB_TOKEN     (the ghp_... token you just made)

Reminder: the keys live in the terminal, never in this file.
"""

import os
import requests
from google import genai


# 1) Paste the link to YOUR OWN test pull request here (the one you can comment on).
#    Example shape: https://github.com/your-username/pr-agent-test/pull/1
PR_URL = "https://github.com/Mridul-Bhola/pr-agent-test/pull/1"

# 2) The AI model. Swap this if Google retires it (check https://aistudio.google.com).
MODEL = "gemini-3.6-flash"


def parse_pr_url(pr_url: str):
    """Pull the owner, repo name, and PR number out of the link.

    'https://github.com/alice/my-repo/pull/1'  ->  ('alice', 'my-repo', '1')
    """
    parts = pr_url.rstrip("/").split("/")
    owner = parts[-4]
    repo = parts[-3]
    pr_number = parts[-1]
    return owner, repo, pr_number


def get_pr_changes(pr_url: str) -> str:
    """Download the code changes (diff) for a pull request from GitHub."""
    diff_url = pr_url.rstrip("/") + ".diff"
    response = requests.get(diff_url, timeout=30)
    response.raise_for_status()
    return response.text


def review_changes(diff_text: str) -> str:
    """Send the code changes to the AI and get a review back."""
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    prompt = f"""You are a senior software engineer reviewing a pull request.
Read the code changes below (in git diff format) and give a short, practical review.

Point out:
- Bugs or logic mistakes
- Missing edge cases or error handling
- Anything unclear or risky

Be specific and mention the file names. If the code looks fine, say so plainly.

CODE CHANGES:
{diff_text}
"""

    result = client.models.generate_content(model=MODEL, contents=prompt)
    return result.text


def post_comment(owner: str, repo: str, pr_number: str, review_text: str):
    """Post the review as a comment on the pull request, using the GitHub API."""
    # A PR is treated as an "issue" for general comments, hence /issues/ here.
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github+json",
    }
    body = {"body": review_text}

    response = requests.post(api_url, headers=headers, json=body, timeout=30)
    response.raise_for_status()
    # GitHub sends back a link to the comment it just created.
    return response.json()["html_url"]


if __name__ == "__main__":
    owner, repo, pr_number = parse_pr_url(PR_URL)

    print("Fetching the pull request changes...\n")
    changes = get_pr_changes(PR_URL)

    print("Asking the AI to review...\n")
    review = review_changes(changes)

    print("Posting the review to GitHub...\n")
    comment_link = post_comment(owner, repo, pr_number, review)

    print("=" * 60)
    print("Done! Your review was posted here:")
    print(comment_link)
    print("=" * 60)
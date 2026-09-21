"""
webhook_server.py  —  Step 4 integrated: automatic, tool-grounded reviews

When a pull request opens, the server now runs the LINTER-BACKED review
(review_with_tools) instead of the plain diff-only one. So an opened PR
automatically gets a review that cites real tool findings.

RUN (in the terminal where GEMINI_API_KEY and GITHUB_TOKEN are exported):
    uvicorn webhook_server:app --reload --port 8000
Keep ngrok running in a second terminal.
"""

from fastapi import FastAPI, Request, BackgroundTasks

# The tool-grounded review (fetches files, runs the linter, then reviews).
from review_with_tools import review_with_tools
# Still need these two to figure out where to post, and to post.
from pr_reviewer_step2 import parse_pr_url, post_comment

app = FastAPI()


@app.get("/")
def home():
    return {"status": "ReviewPilot server is running"}


def run_review(pr_url: str):
    """Background work: run the linter-backed review, then post it."""
    print(f"Reviewing PR (with tools): {pr_url}")
    owner, repo, pr_number = parse_pr_url(pr_url)
    review = review_with_tools(pr_url)          # <-- now uses the linter
    link = post_comment(owner, repo, pr_number, review)
    print("Posted review:", link)


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    # Ignore anything that isn't a pull-request event (e.g. the test ping).
    if "pull_request" not in data:
        return {"skipped": "not a pull_request event"}

    # Only review when a PR is newly opened or reopened.
    action = data.get("action")
    if action not in ("opened", "reopened"):
        return {"skipped": f"ignoring action: {action}"}

    pr_url = data["pull_request"]["html_url"]

    # Reply to GitHub instantly; do the slow review in the background.
    background_tasks.add_task(run_review, pr_url)
    return {"status": "review started", "pr": pr_url}
"""
webhook_server.py  —  auto PR reviews + saves each run + serves the dashboard API

On a pull request opening, it reviews (linter + sandboxed tests + context),
posts the comment, AND saves a record to Postgres. It also exposes read
endpoints the dashboard uses to show review history.

RUN (keys exported, Docker running, Postgres container up):
    uvicorn webhook_server:app --reload --port 8000
"""

import time
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from review_with_tools import review_with_tools
from pr_reviewer_step2 import parse_pr_url, post_comment
from db import init_db, save_review, get_reviews

app = FastAPI()

# Let the React dashboard (running on another port) call these endpoints.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()   # make sure the reviews table exists when the server starts


@app.get("/")
def home():
    return {"status": "ReviewPilot server is running"}


# ---- Dashboard API ----
@app.get("/reviews")
def list_reviews():
    """All recent reviews, newest first — the dashboard's main data source."""
    return get_reviews()


# ---- The review worker ----
def run_review(pr_url: str):
    print(f"Reviewing PR: {pr_url}")
    owner, repo, pr_number = parse_pr_url(pr_url)

    start = time.time()
    review = review_with_tools(pr_url)
    duration_ms = int((time.time() - start) * 1000)

    # Simple verdict: did it find anything?
    verdict = "clean" if review.strip() == "No issues found." else "issues found"

    # Save the run, then post the comment.
    save_review(f"{owner}/{repo}", pr_number, duration_ms, verdict, review)
    link = post_comment(owner, repo, pr_number, review)
    print(f"Saved + posted ({verdict}, {duration_ms}ms): {link}")


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    if "pull_request" not in data:
        return {"skipped": "not a pull_request event"}
    if data.get("action") not in ("opened", "reopened"):
        return {"skipped": f"ignoring action: {data.get('action')}"}

    pr_url = data["pull_request"]["html_url"]
    background_tasks.add_task(run_review, pr_url)
    return {"status": "review started", "pr": pr_url}
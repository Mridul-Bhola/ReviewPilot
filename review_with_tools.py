"""
review_with_tools.py  —  tool-grounded review with Langfuse tracing

Flow: fetch diff + files -> linter -> Docker-sandboxed tests -> cross-file
context -> AI review (retry + model fallback). Each AI call is traced to
Langfuse (latency + token usage), if Langfuse keys are set.

RUN (keys exported, Docker running, sandbox image built):
    python review_with_tools.py

Langfuse is OPTIONAL: if LANGFUSE_PUBLIC_KEY isn't set, tracing is skipped
and the review runs exactly as before.
"""

import os
import time
from google import genai
from google.genai import errors as genai_errors

from pr_reviewer_step2 import get_pr_changes
from fetch_py_files import parse_pr_url, get_pr_python_files
from linter_tool import run_linter
from repo_context import get_related_context
from docker_test_tool import run_pr_tests

# --- optional Langfuse tracing ---
LANGFUSE_ON = False
try:
    if os.environ.get("LANGFUSE_PUBLIC_KEY"):
        from langfuse import get_client
        langfuse = get_client()
        LANGFUSE_ON = True
except Exception:
    LANGFUSE_ON = False

PR_URL = "https://github.com/Mridul-Bhola/pr-agent-test/pull/5"
MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-flash-latest"]
MAX_RETRIES = 3
BASE_WAIT = 8


def _one_call(client, model, prompt):
    """A single generate_content call, traced to Langfuse if enabled."""
    if not LANGFUSE_ON:
        return client.models.generate_content(model=model, contents=prompt)

    # Wrap the call so Langfuse records latency + token usage.
    with langfuse.start_as_current_observation(
        as_type="generation", name="pr-review", model=model,
        input={"prompt": prompt},
    ) as gen:
        result = client.models.generate_content(model=model, contents=prompt)
        um = getattr(result, "usage_metadata", None)
        if um:
            gen.update(
                output=result.text,
                usage_details={
                    "input_tokens": um.prompt_token_count,
                    "output_tokens": um.candidates_token_count,
                },
            )
        else:
            gen.update(output=result.text)
        return result


def call_ai(client, prompt: str) -> str:
    last_error = None
    for model in MODELS:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = _one_call(client, model, prompt)
                if model != MODELS[0]:
                    print(f"(used fallback model: {model})")
                return result.text
            except genai_errors.ServerError as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    wait = BASE_WAIT * attempt
                    print(f"({model} busy, retry {attempt}/{MAX_RETRIES - 1} in {wait}s...)")
                    time.sleep(wait)
            except genai_errors.ClientError as e:
                last_error = e
                print(f"({model} unavailable, trying next model...)")
                break
    raise last_error


def review_with_tools(pr_url: str) -> str:
    owner, repo, pr_number = parse_pr_url(pr_url)

    diff = get_pr_changes(pr_url)
    py_files = get_pr_python_files(owner, repo, pr_number)

    linter_report = ""
    for name, code in py_files.items():
        linter_report += f"\n--- {name} ---\n{run_linter(code)}\n"
    if not linter_report.strip():
        linter_report = "(No Python files were changed, so the linter did not run.)"

    try:
        test_report = run_pr_tests(py_files)
    except Exception as e:
        test_report = f"(Could not run tests: {e})"

    context_block = ""
    try:
        related = get_related_context(owner, repo, pr_number, py_files)
        for path, content in related.items():
            context_block += f"\n--- {path} (context, NOT under review) ---\n{content}\n"
    except Exception as e:
        context_block = f"(Could not fetch related files: {e})"
    if not context_block.strip():
        context_block = "(No local imported files found for extra context.)"

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = f"""You are a senior engineer reviewing a pull request. You are given
the diff, a linter's output, the result of running the PR's tests in a sandbox,
and related files from the same repo (context only -- not under review).

Report ONLY real problems in the changed code AS WRITTEN:
- Bugs, logic errors, crashes, or security issues that actually occur.
- Failing tests: say which test failed and what it implies.
- Mismatches with the related files (e.g. wrong number of arguments).
- Treat the linter findings and test results as verified facts.

Do NOT report:
- Hypothetical "what if someone passes a wrong type" cases.
- Style preferences (type hints, docstrings, naming) unless they cause a bug.
- Problems in the related context files themselves.

Be concise and mention file names. If nothing in the diff has a real problem
and the tests pass, reply with EXACTLY:
No issues found.
and nothing else.

LINTER FINDINGS:
{linter_report}

TEST RESULTS (ran in a Docker sandbox):
{test_report}

RELATED FILES (context only):
{context_block}

CODE CHANGES (diff):
{diff}
"""
    review = call_ai(client, prompt)
    if LANGFUSE_ON:
        langfuse.flush()   # make sure the trace is sent
    return review


if __name__ == "__main__":
    print("Reviewing with tools (linter + sandboxed tests + context + AI)...\n")
    print(review_with_tools(PR_URL))
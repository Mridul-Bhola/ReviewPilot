"""
eval_runner.py  —  run the bot on each test case (resumable + model fallback)

Robust against API outages:
  - Tries several models in order; if one is overloaded (503) or unavailable
    (404), it falls through to the next.
  - Retries transient errors with growing backoff.
  - Saves results after EVERY successful case, and RESUMES on re-run
    (skips cases already done).

RUN (with GEMINI_API_KEY exported):
    python eval_runner.py
Re-run as needed; it picks up where it left off.
"""

import os
import json
import time
from google import genai
from google.genai import errors as genai_errors

from eval_dataset import CASES
from linter_tool import run_linter

# Tried in order. If the first is overloaded, it falls through to the next.
MODELS = ["gemini-3.6-flash", "gemini-3.6-pro", "gemini-flash-latest", "gemini-2.5-flash"]
RESULTS_FILE = "eval_results.json"
MAX_RETRIES = 3
BASE_WAIT = 8
PAUSE_BETWEEN = 2


def call_ai(client, prompt: str) -> str:
    """Try each model; retry transient errors; fall through on 503/404."""
    last_error = None
    for model in MODELS:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = client.models.generate_content(model=model, contents=prompt)
                if model != MODELS[0]:
                    print(f"    (used fallback model: {model})")
                return result.text
            except genai_errors.ServerError as e:      # 503 overloaded
                last_error = e
                if attempt < MAX_RETRIES:
                    wait = BASE_WAIT * attempt
                    print(f"    ({model} busy, retry {attempt}/{MAX_RETRIES - 1} in {wait}s...)")
                    time.sleep(wait)
            except genai_errors.ClientError as e:      # 404 model not available, etc.
                last_error = e
                print(f"    ({model} unavailable, trying next model...)")
                break  # move to next model immediately
    raise last_error


def review_code(client, code: str) -> str:
    linter_report = run_linter(code)
    prompt = f"""You are a senior software engineer reviewing a small piece of Python code.
You are also given the output of an automated linter that was run on it.

Treat the linter findings as verified facts. Then add your own judgment on
bugs, edge cases, and risky patterns. Be specific and concise.

LINTER FINDINGS:
{linter_report}

CODE:
{code}
"""
    return call_ai(client, prompt)


def load_done():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            return {r["name"]: r for r in json.load(f)}
    return {}


if __name__ == "__main__":
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    done = load_done()
    if done:
        print(f"Resuming — {len(done)} case(s) already done, skipping those.\n")

    for case in CASES:
        name = case["name"]
        if name in done:
            continue

        print(f"Reviewing case: {name} ...")
        try:
            review = review_code(client, case["code"])
        except Exception:
            print("  !! All models unavailable right now — stopping. "
                  "Run the script again later to continue.")
            break

        done[name] = {
            "name": name,
            "difficulty": case.get("difficulty", "?"),
            "expected_issues": case["expected_issues"],
            "review": review,
        }
        with open(RESULTS_FILE, "w") as f:
            json.dump(list(done.values()), f, indent=2)
        time.sleep(PAUSE_BETWEEN)

    total = len(CASES)
    print(f"\nProgress: {len(done)}/{total} cases done, saved to {RESULTS_FILE}")
    if len(done) < total:
        print("Not all cases finished. Run the script again to continue.")
    else:
        print("All cases complete! Now run:  python eval_score.py")
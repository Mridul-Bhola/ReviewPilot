"""
eval_runner.py  —  Step 5 (evals), piece 2: run the bot on each test case

For every sample in eval_dataset.py, this reviews the code the SAME way your
real bot does (run the linter, then ask the AI with those findings in hand),
and records the review text. Piece 3 will score these results.

It reuses run_linter from your linter_tool.py, so the eval measures the
same engine your bot actually uses.

RUN (with GEMINI_API_KEY exported):
    python eval_runner.py
It saves the results to eval_results.json.
"""

import os
import json
from google import genai

from eval_dataset import CASES
from linter_tool import run_linter

MODEL = "gemini-3.6-flash"


def review_code(code: str) -> str:
    """Same idea as review_with_tools, but on a raw code string:
    run the linter, then ask the AI to review with the findings."""
    linter_report = run_linter(code)

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = f"""You are a senior software engineer reviewing a small piece of Python code.
You are also given the output of an automated linter that was run on it.

Treat the linter findings as verified facts. Then add your own judgment on
bugs, edge cases, and risky patterns. Be specific and concise.

LINTER FINDINGS:
{linter_report}

CODE:
{code}
"""
    result = client.models.generate_content(model=MODEL, contents=prompt)
    return result.text


if __name__ == "__main__":
    results = []
    for case in CASES:
        print(f"Reviewing case: {case['name']} ...")
        review = review_code(case["code"])
        results.append({
            "name": case["name"],
            "expected_issues": case["expected_issues"],
            "review": review,
        })

    with open("eval_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone. Saved {len(results)} reviews to eval_results.json")
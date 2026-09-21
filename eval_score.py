"""
eval_score.py  —  Step 5 (evals), piece 3: grade the bot's reviews

Reads eval_results.json (what the bot said) and compares each review to the
answer key (what it SHOULD have said), then prints the scores.

How each case is graded:
  - Cases WITH expected issues (buggy code): did the review mention the
    expected keywords? If yes -> a "catch" (true positive).
    If no -> a "miss" (false negative).
  - The CLEAN case (no expected issues): did the review wrongly claim the
    code has a real bug? If yes -> a "false alarm" (false positive).

From those we compute:
  - Recall    = of all real bugs, how many did it catch?
  - Precision = of everything it flagged, how much was real?

RUN:
    python eval_score.py
"""

import json


def review_mentions(review: str, keywords: list) -> bool:
    """True if the review text mentions ANY of the expected keywords."""
    text = review.lower()
    return any(kw.lower() in text for kw in keywords)


if __name__ == "__main__":
    with open("eval_results.json") as f:
        results = json.load(f)

    catches = 0        # real bugs the bot correctly flagged (true positives)
    misses = 0         # real bugs the bot missed (false negatives)
    false_alarms = 0   # clean code the bot wrongly flagged (false positives)
    clean_ok = 0       # clean code the bot correctly left alone

    print("Per-case results:")
    print("-" * 50)
    for r in results:
        name = r["name"]
        expected = r["expected_issues"]
        review = r["review"]

        if expected:  # this is a buggy case
            if review_mentions(review, expected):
                catches += 1
                print(f"[CATCH ] {name}: found {expected}")
            else:
                misses += 1
                print(f"[MISS  ] {name}: did NOT mention {expected}")
        else:  # this is the clean case
            # For clean code, we look for the bot inventing a bug. We use a
            # few strong words; if it says the code is fine, no false alarm.
            invented = review_mentions(review, ["bug", "error", "undefined", "crash", "fix a"])
            if invented:
                false_alarms += 1
                print(f"[FALSE+] {name}: flagged a problem in clean code")
            else:
                clean_ok += 1
                print(f"[CLEAN ] {name}: correctly left clean code alone")

    print("-" * 50)

    # Recall: of all the real bugs, how many were caught?
    total_bugs = catches + misses
    recall = (catches / total_bugs * 100) if total_bugs else 0

    # Precision: of everything flagged (real catches + false alarms), how
    # much was a real bug?
    total_flagged = catches + false_alarms
    precision = (catches / total_flagged * 100) if total_flagged else 0

    print("\nSCORES")
    print(f"  Bugs caught (recall):     {catches}/{total_bugs}  = {recall:.0f}%")
    print(f"  Precision (flags correct): {catches}/{total_flagged}  = {precision:.0f}%")
    print(f"  False alarms on clean code: {false_alarms}")
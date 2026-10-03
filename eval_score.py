"""
eval_score.py  —  grade the bot's reviews, broken down by difficulty

Reads eval_results.json (what the bot said) and compares each review to the
answer key. Prints per-case results, a recall breakdown by difficulty tier,
and overall precision / false-alarm numbers.
"""

import json
from collections import defaultdict


def review_mentions(review: str, keywords: list) -> bool:
    text = review.lower()
    return any(kw.lower() in text for kw in keywords)


if __name__ == "__main__":
    with open("eval_results.json") as f:
        results = json.load(f)

    catches = 0
    misses = 0
    false_alarms = 0
    clean_ok = 0

    # recall tracked per difficulty tier
    tier_caught = defaultdict(int)
    tier_total = defaultdict(int)

    print("Per-case results:")
    print("-" * 60)
    for r in results:
        name = r["name"]
        expected = r["expected_issues"]
        difficulty = r.get("difficulty", "?")
        review = r["review"]

        if expected:  # a genuine bug
            tier_total[difficulty] += 1
            if review_mentions(review, expected):
                catches += 1
                tier_caught[difficulty] += 1
                print(f"[CATCH ] ({difficulty:6}) {name}")
            else:
                misses += 1
                print(f"[MISS  ] ({difficulty:6}) {name}: wanted {expected}")
        else:  # clean code
            invented = review_mentions(review, ["bug", "error", "undefined", "crash", "fix a"])
            if invented:
                false_alarms += 1
                print(f"[FALSE+] (clean ) {name}: flagged clean code")
            else:
                clean_ok += 1
                print(f"[CLEAN ] (clean ) {name}: correctly quiet")

    print("-" * 60)

    print("\nRecall by difficulty:")
    for tier in ("easy", "medium", "hard"):
        t = tier_total[tier]
        c = tier_caught[tier]
        pct = (c / t * 100) if t else 0
        print(f"  {tier:6}: {c}/{t}  = {pct:.0f}%")

    total_bugs = catches + misses
    recall = (catches / total_bugs * 100) if total_bugs else 0
    total_flagged = catches + false_alarms
    precision = (catches / total_flagged * 100) if total_flagged else 0

    print("\nOVERALL")
    print(f"  Recall (bugs caught):       {catches}/{total_bugs}  = {recall:.0f}%")
    print(f"  Precision (flags correct):  {catches}/{total_flagged}  = {precision:.0f}%")
    print(f"  False alarms on clean code: {false_alarms}/{false_alarms + clean_ok}")
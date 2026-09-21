"""
eval_dataset.py  —  Step 5 (evals), piece 1: the labeled test set

To measure how good your reviewer is, you first need an "answer key": code
samples where YOU already know what's wrong. Then you run the bot on each and
check whether its review caught the known problems.

Each case has:
  - name            : a short label for the case
  - code            : a small Python snippet
  - expected_issues : keywords a CORRECT review should mention
                      (an empty list means the code is clean -> the bot
                       should find nothing; that's our false-alarm check)

The mix on purpose:
  - some bugs the linter alone can catch (undefined name, unused import)
  - some deeper bugs only the AI should reason about (mutable default,
    divide-by-zero on empty input)
  - one clean file, to see if the bot invents problems that aren't there
"""

CASES = [
    {
        "name": "undefined_variable",
        "code": '''def greet(name):
    print("Hello " + nmae)
''',
        "expected_issues": ["nmae", "undefined"],
    },
    {
        "name": "unused_import",
        "code": '''import os

def add(a, b):
    return a + b
''',
        "expected_issues": ["os", "unused"],
    },
    {
        "name": "mutable_default_arg",
        "code": '''def append_item(item, items=[]):
    items.append(item)
    return items
''',
        "expected_issues": ["mutable", "default"],
    },
    {
        "name": "divide_by_zero_on_empty",
        "code": '''def average(numbers):
    return sum(numbers) / len(numbers)
''',
        "expected_issues": ["empty", "zero"],
    },
    {
        "name": "clean_code",
        "code": '''def multiply(a, b):
    return a * b
''',
        "expected_issues": [],  # nothing wrong -- the bot should stay quiet
    },
]
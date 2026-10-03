"""
eval_dataset.py  —  graded labeled test set

15 GENUINE bugs, graded by difficulty (3 easy / 7 medium / 5 hard), plus 5
clean/correct files so we can also measure false alarms (precision).

Each case:
  - name            : short label
  - difficulty      : "easy" | "medium" | "hard" | "clean"
  - code            : a small Python snippet
  - expected_issues : keywords a CORRECT review should mention.
                      Empty list = the code is fine; the bot should stay quiet.

Difficulty guide:
  easy   - obvious, usually linter-catchable (undefined name, missing return)
  medium - needs reasoning about behavior (mutable default, resource leak)
  hard   - subtle logic traps an experienced dev might miss
"""

CASES = [
    # ============ EASY (3) ============
    {
        "name": "undefined_variable",
        "difficulty": "easy",
        "code": '''def greet(name):
    print("Hello " + nmae)
''',
        "expected_issues": ["nmae", "undefined"],
    },
    {
        "name": "missing_return",
        "difficulty": "easy",
        "code": '''def double(x):
    result = x * 2
''',
        "expected_issues": ["return", "none"],
    },
    {
        "name": "bare_except_swallows_errors",
        "difficulty": "easy",
        "code": '''def parse(x):
    try:
        return int(x)
    except:
        return None
''',
        "expected_issues": ["bare", "except", "broad"],
    },

    # ============ MEDIUM (7) ============
    {
        "name": "mutable_default_arg",
        "difficulty": "medium",
        "code": '''def append_item(item, items=[]):
    items.append(item)
    return items
''',
        "expected_issues": ["mutable", "default"],
    },
    {
        "name": "divide_by_zero_on_empty",
        "difficulty": "medium",
        "code": '''def average(numbers):
    return sum(numbers) / len(numbers)
''',
        "expected_issues": ["empty", "zero"],
    },
    {
        "name": "off_by_one_index",
        "difficulty": "medium",
        "code": '''def last_n(items, n):
    result = []
    for i in range(len(items) - n, len(items) + 1):
        result.append(items[i])
    return result
''',
        "expected_issues": ["index", "range", "out of"],
    },
    {
        "name": "resource_not_closed",
        "difficulty": "medium",
        "code": '''def read_file(path):
    f = open(path)
    data = f.read()
    return data
''',
        "expected_issues": ["close", "with", "leak"],
    },
    {
        "name": "identity_vs_equality",
        "difficulty": "medium",
        "code": '''def is_active(status):
    if status is "active":
        return True
    return False
''',
        "expected_issues": ["is", "identity", "=="],
    },
    {
        "name": "modify_list_while_iterating",
        "difficulty": "medium",
        "code": '''def remove_negatives(nums):
    for n in nums:
        if n < 0:
            nums.remove(n)
    return nums
''',
        "expected_issues": ["iterat", "modify", "skip"],
    },
    {
        "name": "shadowed_builtin_breaks_call",
        "difficulty": "medium",
        "code": '''def total(sum):
    return sum([1, 2, 3]) + sum
''',
        "expected_issues": ["sum", "shadow", "builtin"],
    },

    # ============ HARD (5) ============
    {
        "name": "or_truthiness_always_true",
        "difficulty": "hard",
        "code": '''def is_privileged(role):
    if role == "admin" or "root":
        return True
    return False
''',
        "expected_issues": ["always", "truthy", "precedence"],
    },
    {
        "name": "late_binding_closure",
        "difficulty": "hard",
        "code": '''def make_multipliers():
    funcs = []
    for i in range(3):
        funcs.append(lambda x: x * i)
    return funcs
''',
        "expected_issues": ["closure", "late", "binding"],
    },
    {
        "name": "float_equality",
        "difficulty": "hard",
        "code": '''def is_third(value):
    return value == 0.1 + 0.2
''',
        "expected_issues": ["float", "precision", "isclose"],
    },
    {
        "name": "shallow_copy_shared_nested",
        "difficulty": "hard",
        "code": '''def duplicate(grid):
    copy = grid[:]
    copy[0].append(0)
    return copy
''',
        "expected_issues": ["shallow", "copy", "reference"],
    },
    {
        "name": "wrong_recursion_base_case",
        "difficulty": "hard",
        "code": '''def factorial(n):
    if n == 1:
        return 1
    return n * factorial(n - 1)
''',
        "expected_issues": ["base case", "zero", "recursion"],
    },

    # ============ CLEAN / CORRECT (5) -- bot should stay quiet ============
    {
        "name": "clean_multiply",
        "difficulty": "clean",
        "code": '''def multiply(a, b):
    return a * b
''',
        "expected_issues": [],
    },
    {
        "name": "clean_maximum",
        "difficulty": "clean",
        "code": '''def maximum(a, b):
    return a if a > b else b
''',
        "expected_issues": [],
    },
    {
        "name": "clean_with_open",
        "difficulty": "clean",
        "code": '''def read_text(path):
    with open(path) as f:
        return f.read()
''',
        "expected_issues": [],
    },
    {
        "name": "clean_safe_average",
        "difficulty": "clean",
        "code": '''def safe_average(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
''',
        "expected_issues": [],
    },
    {
        "name": "clean_safe_percent",
        "difficulty": "clean",
        "code": '''def to_percent(part, whole):
    if whole == 0:
        return 0
    return (part / whole) * 100
''',
        "expected_issues": [],
    },
]
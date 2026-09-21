"""
pr_reviewer.py  —  Step 1 of your PR Review Agent

What this script does:
  1. Takes a link to a GitHub pull request
  2. Downloads the code changes (the "diff") from GitHub
  3. Asks an AI model to review those changes
  4. Prints the review on your screen

That's the whole thing. No server, no automation yet — this just proves
the core idea works. Once you see it review real code, the rest is
adding pieces on top.

------------------------------------------------------------
ONE-TIME SETUP (do these two things first):

  1. Install the two libraries this script needs:
         pip install requests google-genai

  2. Get a free Gemini API key from:
         https://aistudio.google.com/apikey
     Then tell your computer about it:
         Mac / Linux:   export GEMINI_API_KEY="your_key_here"
         Windows (PowerShell):   setx GEMINI_API_KEY "your_key_here"
------------------------------------------------------------
"""

import os
import requests
from google import genai


# 1) Paste the pull request link you want to review between the quotes.
#    Tip: pick any small, PUBLIC pull request on GitHub to test with.
PR_URL = "https://github.com/pallets/flask/pull/5665"

# 2) The AI model to use. If this name ever stops working, check
#    https://aistudio.google.com for the current model name and swap it in.
MODEL = "gemini-3.6-flash"


def get_pr_changes(pr_url: str) -> str:
    """Download the code changes (diff) for a pull request from GitHub."""
    diff_url = pr_url.rstrip("/") + ".diff"   # GitHub serves the raw diff at this address
    response = requests.get(diff_url, timeout=30)
    response.raise_for_status()               # stops early with a clear error if the link is wrong
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


if __name__ == "__main__":
    print("Fetching the pull request changes...\n")
    changes = get_pr_changes(PR_URL)

    print("Asking the AI to review...\n")
    review = review_changes(changes)

    print("=" * 60)
    print("AI CODE REVIEW")
    print("=" * 60)
    print(review)
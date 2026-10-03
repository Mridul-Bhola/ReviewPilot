"""
db.py  —  store and fetch review runs in Postgres

Every time the bot reviews a PR, we save a record here. The dashboard later
reads these records to show review history.

Postgres runs in a Docker container (see setup below), so there's no native
Postgres install to manage.

ONE-TIME SETUP:
  1. Start a Postgres container:
       docker run --name reviewpilot-db \
         -e POSTGRES_PASSWORD=reviewpilot \
         -e POSTGRES_DB=reviewpilot \
         -p 5433:5432 -d postgres:16
  2. Install the Python driver:
       pip install psycopg2-binary
  3. Create the table:
       python db.py        (this runs init_db once)

The container keeps your data between restarts. To start it again later:
       docker start reviewpilot-db
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Where to find the database. Matches the docker command above.
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:reviewpilot@127.0.0.1:5433/reviewpilot",
)


def _connect():
    return psycopg2.connect(DB_URL)


def init_db():
    """Create the reviews table if it doesn't exist yet."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id          SERIAL PRIMARY KEY,
                repo        TEXT NOT NULL,
                pr_number   TEXT NOT NULL,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
                duration_ms INTEGER,
                verdict     TEXT,
                review      TEXT
            )
        """)
    print("Table 'reviews' is ready.")


def save_review(repo, pr_number, duration_ms, verdict, review):
    """Insert one review record. Returns its new id."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO reviews (repo, pr_number, duration_ms, verdict, review)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (repo, pr_number, duration_ms, verdict, review),
        )
        return cur.fetchone()[0]


def get_reviews(limit=50):
    """Return the most recent reviews, newest first (as a list of dicts)."""
    with _connect() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT * FROM reviews ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
        return cur.fetchall()


if __name__ == "__main__":
    # Running this file directly sets up the table, then does a quick self-test.
    init_db()
    new_id = save_review(
        repo="Mridul-Bhola/pr-agent-test",
        pr_number="4",
        duration_ms=1234,
        verdict="issues found",
        review="Example saved review — add() called with 3 args but takes 2.",
    )
    print(f"Saved a test review with id={new_id}")
    print("Recent reviews:")
    for r in get_reviews():
        print(f"  #{r['id']}  {r['repo']} PR {r['pr_number']}  [{r['verdict']}]")
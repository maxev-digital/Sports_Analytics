"""
Migration: Add opus_verdict and opus_reasoning columns to predictions table.

Safe to run multiple times — uses ALTER TABLE ... IF NOT EXISTS.

Run:
    python3 migrations/add_opus_verdict.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.db.connection import execute_write, execute_query


def column_exists(table: str, column: str) -> bool:
    rows = execute_query(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name   = %s
          AND column_name  = %s
        """,
        (table, column),
    )
    return len(rows) > 0


def run():
    added = []

    if not column_exists("predictions", "opus_verdict"):
        execute_write(
            "ALTER TABLE predictions ADD COLUMN opus_verdict VARCHAR(10) DEFAULT NULL"
        )
        added.append("opus_verdict")
        print("  + Added column: predictions.opus_verdict (VARCHAR 10)")
    else:
        print("  . Already exists: predictions.opus_verdict — skipped")

    if not column_exists("predictions", "opus_reasoning"):
        execute_write(
            "ALTER TABLE predictions ADD COLUMN opus_reasoning TEXT DEFAULT NULL"
        )
        added.append("opus_reasoning")
        print("  + Added column: predictions.opus_reasoning (TEXT)")
    else:
        print("  . Already exists: predictions.opus_reasoning — skipped")

    if added:
        print(f"\nMigration complete. Added {len(added)} column(s): {', '.join(added)}")
    else:
        print("\nNothing to do — columns already present.")


if __name__ == "__main__":
    print("Running migration: add_opus_verdict")
    run()

"""
Standalone Database Setup and Seeding Script
Run this script to initialize or reset the local SQLite database with demonstration data.

Usage:
    python scripts/setup_db.py
"""

import sys
from pathlib import Path

# Add project root to sys.path so app modules are resolvable
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.config import DB_PATH, SCHEMA_PATH
from app.database.db import init_db, get_db_connection
from app.database.seed_data import seed_database


def main():
    print("=" * 60)
    print("Internship Discovery Engine - Database Setup")
    print("=" * 60)
    print(f"Target Database: {DB_PATH}")
    print(f"Schema Source:   {SCHEMA_PATH}")

    # Reset existing database file if present for a clean setup
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("\n   [INFO] Cleaned existing database file for pristine setup.")

    # Initialize tables
    print("\n1. Initializing SQLite tables...")
    conn = init_db(DB_PATH, SCHEMA_PATH)
    print("   [OK] Tables created successfully (PRAGMA foreign_keys = ON).")

    # Seed demonstration data
    print("\n2. Seeding curated demonstration dataset...")
    seed_database(conn)
    print("   [OK] Seeding complete.")

    # Verify counts
    skills_count = conn.execute("SELECT COUNT(*) as c FROM skills;").fetchone()["c"]
    students_count = conn.execute("SELECT COUNT(*) as c FROM students;").fetchone()["c"]
    internships_count = conn.execute("SELECT COUNT(*) as c FROM internships;").fetchone()["c"]
    demo_count = conn.execute("SELECT COUNT(*) as c FROM internships WHERE is_demo = 1;").fetchone()["c"]

    print("\nDatabase Summary:")
    print(f"   * Skills Registered:       {skills_count}")
    print(f"   * Students Seeded:         {students_count}")
    print(f"   * Internships Seeded:      {internships_count} (Demonstration Flagged: {demo_count})")
    print("\nDatabase initialization completed successfully!")
    conn.close()


if __name__ == "__main__":
    main()

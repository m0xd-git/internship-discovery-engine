"""
Verification Script for Milestone 1 Database State
Checks database tables, record counts, demo flags, and foreign key enforcement.
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.database.db import get_db_connection


def main():
    print("=" * 60)
    print("Milestone 1 Database State Verification")
    print("=" * 60)

    conn = get_db_connection()

    # 1. Check Foreign Key enforcement
    fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
    print(f"1. Foreign Key Enforcement: {'ENABLED (1)' if fk_status == 1 else 'DISABLED (0)'}")

    # 2. Check 5 tables
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
    )
    tables = [row["name"] for row in cur.fetchall()]
    print(f"\n2. Tables Detected ({len(tables)} of 5 expected):")
    for t in tables:
        print(f"   * {t}")

    # 3. Check record counts
    students = conn.execute("SELECT COUNT(*) as c FROM students;").fetchone()["c"]
    skills = conn.execute("SELECT COUNT(*) as c FROM skills;").fetchone()["c"]
    internships = conn.execute("SELECT COUNT(*) as c FROM internships;").fetchone()["c"]
    demo_internships = conn.execute(
        "SELECT COUNT(*) as c FROM internships WHERE is_demo = 1;"
    ).fetchone()["c"]
    student_skills = conn.execute("SELECT COUNT(*) as c FROM student_skills;").fetchone()["c"]
    internship_skills = conn.execute(
        "SELECT COUNT(*) as c FROM internship_skills;"
    ).fetchone()["c"]

    print("\n3. Record Counts:")
    print(f"   * Students:          {students} (Expected: 3)")
    print(f"   * Skills:            {skills} (Expected: 21)")
    print(f"   * Internships:       {internships} (Expected: 6)")
    print(f"   * Demo Internships:  {demo_internships} (Expected: 6, all with is_demo = 1)")
    print(f"   * Student Skills:    {student_skills}")
    print(f"   * Internship Skills: {internship_skills}")

    # 4. Detail each internship
    print("\n4. Internship Listings Verification:")
    cur = conn.execute(
        "SELECT id, title, organization, min_cgpa, work_mode, is_demo FROM internships ORDER BY id;"
    )
    for row in cur.fetchall():
        status = "DEMO OK" if row["is_demo"] == 1 else "FAILED"
        print(
            f"   [{status}] ID {row['id']}: '{row['title']}' at '{row['organization']}' "
            f"(Min CGPA: {row['min_cgpa']}, Mode: {row['work_mode']}, is_demo: {row['is_demo']})"
        )

    # 5. Detail each student
    print("\n5. Student Profiles Verification:")
    cur = conn.execute("SELECT id, name, major, cgpa, preferred_work_mode FROM students ORDER BY id;")
    for row in cur.fetchall():
        print(
            f"   * ID {row['id']}: {row['name']} | Major: {row['major']} | "
            f"CGPA: {row['cgpa']} | Preferred Mode: {row['preferred_work_mode']}"
        )

    conn.close()

    # Assertions
    assert fk_status == 1, "Foreign key enforcement is not active!"
    assert len(tables) == 5, f"Expected 5 tables, found {len(tables)}"
    assert students == 3, f"Expected 3 students, found {students}"
    assert skills == 21, f"Expected 21 skills, found {skills}"
    assert internships == 6, f"Expected 6 internships, found {internships}"
    assert demo_internships == 6, f"Expected 6 demo internships, found {demo_internships}"

    print("\n[SUCCESS] All Milestone 1 database verification checks passed!")


if __name__ == "__main__":
    main()

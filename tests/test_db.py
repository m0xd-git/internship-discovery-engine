"""
Automated Database and Data Model Unit Tests
Tests schema integrity, check constraints, foreign keys, cascade deletes,
seed data verification, and data class conversions using in-memory SQLite.
"""

import sqlite3
import unittest
from pathlib import Path
import json

from app.config import SCHEMA_PATH, validate_weights, DEFAULT_SCORING_WEIGHTS
from app.database.db import get_db_connection, init_db, db_session
from app.database.seed_data import seed_database
from app.models.entities import Student, Internship, Skill, StudentSkill
from app.models.results import (
    EligibilityResult,
    SkillGapReport,
    ScoreBreakdown,
    RecommendationResult,
)


class DatabaseSchemaTestCase(unittest.TestCase):
    """
    Tests SQLite database schema creation and table structure.
    """

    def setUp(self):
        # Use isolated in-memory SQLite connection for every test
        self.conn = init_db(db_path=":memory:", schema_path=SCHEMA_PATH)

    def tearDown(self):
        self.conn.close()

    def test_schema_tables_exist(self):
        """Verify that all five expected core tables exist in SQLite."""
        cur = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = {row["name"] for row in cur.fetchall()}
        expected_tables = {
            "skills",
            "students",
            "student_skills",
            "internships",
            "internship_skills",
        }
        self.assertEqual(expected_tables, tables)

    def test_foreign_key_enforcement(self):
        """Verify that inserting a student_skill with non-existent student_id raises IntegrityError."""
        # Insert a valid skill first
        self.conn.execute("INSERT INTO skills (name, category) VALUES ('Python', 'Programming Language');")
        skill_id = self.conn.execute("SELECT id FROM skills WHERE name='Python';").fetchone()["id"]

        # Attempt to link skill to non-existent student id 9999
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO student_skills (student_id, skill_id, proficiency_level) VALUES (?, ?, ?);",
                (9999, skill_id, "Intermediate"),
            )

    def test_cascade_delete_student(self):
        """Verify that deleting a student cascades and deletes their associated student_skills."""
        # Create student
        self.conn.execute(
            """
            INSERT INTO students (name, email, major, cgpa, graduation_year, preferred_work_mode, preferred_location)
            VALUES ('Test Student', 'test@example.com', 'CS', 3.5, 2026, 'Remote', 'Anywhere');
            """
        )
        student_id = self.conn.execute("SELECT id FROM students WHERE email='test@example.com';").fetchone()["id"]

        # Create skill and link to student
        self.conn.execute("INSERT INTO skills (name, category) VALUES ('SQL', 'Database & Storage');")
        skill_id = self.conn.execute("SELECT id FROM skills WHERE name='SQL';").fetchone()["id"]

        self.conn.execute(
            "INSERT INTO student_skills (student_id, skill_id, proficiency_level) VALUES (?, ?, 'Advanced');",
            (student_id, skill_id),
        )

        # Confirm student_skills row exists
        count_before = self.conn.execute(
            "SELECT COUNT(*) as c FROM student_skills WHERE student_id = ?;", (student_id,)
        ).fetchone()["c"]
        self.assertEqual(count_before, 1)

        # Delete student
        self.conn.execute("DELETE FROM students WHERE id = ?;", (student_id,))

        # Verify cascade deletion in student_skills
        count_after = self.conn.execute(
            "SELECT COUNT(*) as c FROM student_skills WHERE student_id = ?;", (student_id,)
        ).fetchone()["c"]
        self.assertEqual(count_after, 0)

    def test_cgpa_check_constraint(self):
        """Verify that CGPA out of bounds (< 0.0 or > 4.0) triggers an IntegrityError."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO students (name, email, major, cgpa, graduation_year, preferred_work_mode, preferred_location)
                VALUES ('Invalid GPA', 'invalid@example.com', 'CS', 4.5, 2026, 'Remote', 'Anywhere');
                """
            )

        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO students (name, email, major, cgpa, graduation_year, preferred_work_mode, preferred_location)
                VALUES ('Negative GPA', 'negative@example.com', 'CS', -0.5, 2026, 'Remote', 'Anywhere');
                """
            )

    def test_work_mode_check_constraint(self):
        """Verify that invalid work mode triggers IntegrityError."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO internships (
                    title, organization, location, work_mode, min_cgpa,
                    eligible_majors_json, min_grad_year, max_grad_year, description
                ) VALUES ('Role', 'Org', 'City', 'Underwater', 3.0, '[]', 2025, 2027, 'Desc');
                """
            )


class SeedDataTestCase(unittest.TestCase):
    """
    Tests demonstration dataset seeding and data integrity.
    """

    def setUp(self):
        self.conn = init_db(db_path=":memory:", schema_path=SCHEMA_PATH)
        seed_database(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_seed_record_counts(self):
        """Verify expected minimum counts for skills, internships, and students."""
        skills_count = self.conn.execute("SELECT COUNT(*) as c FROM skills;").fetchone()["c"]
        internships_count = self.conn.execute("SELECT COUNT(*) as c FROM internships;").fetchone()["c"]
        students_count = self.conn.execute("SELECT COUNT(*) as c FROM students;").fetchone()["c"]

        self.assertGreaterEqual(skills_count, 20)
        self.assertGreaterEqual(internships_count, 6)
        self.assertGreaterEqual(students_count, 3)

    def test_all_demo_internships_have_flag(self):
        """Verify that 100% of seeded demonstration internships have is_demo = 1."""
        non_demo_count = self.conn.execute(
            "SELECT COUNT(*) as c FROM internships WHERE is_demo != 1;"
        ).fetchone()["c"]
        self.assertEqual(non_demo_count, 0)

    def test_internship_skills_mapping_exists(self):
        """Verify that seeded internships have associated required and preferred skills."""
        req_count = self.conn.execute(
            "SELECT COUNT(*) as c FROM internship_skills WHERE is_mandatory = 1;"
        ).fetchone()["c"]
        pref_count = self.conn.execute(
            "SELECT COUNT(*) as c FROM internship_skills WHERE is_mandatory = 0;"
        ).fetchone()["c"]

        self.assertGreater(req_count, 0)
        self.assertGreater(pref_count, 0)


class DataClassesTestCase(unittest.TestCase):
    """
    Tests Python entity models and engine result dataclasses.
    """

    def test_database_entity_serialization(self):
        """Verify Student and Internship dataclasses serialize to dict cleanly."""
        student = Student(
            id=1,
            name="Test Candidate",
            email="candidate@example.edu",
            major="Computer Science",
            cgpa=3.8,
            graduation_year=2026,
            preferred_work_mode="Remote",
            preferred_location="Bengaluru",
            bio_summary="Passionate about Python.",
        )
        data = student.to_dict()
        self.assertEqual(data["name"], "Test Candidate")
        self.assertEqual(data["cgpa"], 3.8)

        internship = Internship(
            id=10,
            title="Software Intern",
            organization="Tech Labs",
            location="Remote",
            work_mode="Remote",
            min_cgpa=3.0,
            eligible_majors=["Computer Science"],
            min_grad_year=2025,
            max_grad_year=2027,
            description="Role details...",
            is_demo=True,
            required_skills=["Python", "SQL"],
        )
        idata = internship.to_dict()
        self.assertTrue(idata["is_demo"])
        self.assertIn("Python", idata["required_skills"])

    def test_engine_result_objects_distinction(self):
        """Verify that computed result objects work dynamically and are decoupled from DB."""
        eligibility = EligibilityResult(
            is_eligible=True,
            rejection_reasons=[],
            checks={"cgpa_met": True, "major_eligible": True},
        )
        self.assertTrue(eligibility.is_eligible)
        self.assertEqual(len(eligibility.rejection_reasons), 0)

        gaps = SkillGapReport(
            matched_skills=["Python", "SQL"],
            missing_required_skills=["Docker"],
            missing_preferred_skills=["Git"],
            total_required_skills=3,
            total_preferred_skills=1,
        )
        self.assertTrue(gaps.has_critical_gap)
        self.assertEqual(gaps.missing_required_skills, ["Docker"])

        breakdown = ScoreBreakdown(
            required_skills={"points": 30.0, "max_points": 45.0, "details": "2 of 3 matched"},
            preferred_skills={"points": 0.0, "max_points": 15.0, "details": "0 of 1 matched"},
            academic_alignment={"points": 20.0, "max_points": 20.0, "details": "CS major, CGPA 3.8"},
            location_alignment={"points": 20.0, "max_points": 20.0, "details": "Remote matches Remote"},
            semantic_similarity={"points": 0.0, "max_points": 0.0, "details": "Deferred"},
        )

        rec = RecommendationResult(
            student_id=1,
            internship_id=10,
            internship_title="Software Intern",
            organization="Tech Labs",
            eligibility=eligibility,
            total_score=70.0,
            score_breakdown=breakdown,
            skill_gaps=gaps,
            is_demo=True,
        )
        payload = rec.to_dict()
        self.assertEqual(payload["total_score"], 70.0)
        self.assertTrue(payload["eligibility"]["is_eligible"])
        self.assertEqual(payload["skill_gaps"]["missing_required_skills"], ["Docker"])

    def test_weight_validation_helper(self):
        """Verify that weight validation catches improperly summed weights."""
        valid_weights = {"a": 0.5, "b": 0.3, "c": 0.2}
        self.assertTrue(validate_weights(valid_weights))

        invalid_weights = {"a": 0.5, "b": 0.3}  # sums to 0.8
        self.assertFalse(validate_weights(invalid_weights))

        self.assertTrue(validate_weights(DEFAULT_SCORING_WEIGHTS))


if __name__ == "__main__":
    unittest.main()

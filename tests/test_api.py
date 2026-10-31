"""
Automated REST API Integration Tests
=============================================================================
Tests all Flask endpoints:
- GET /api/internships (verifying data integrity and is_demo flag)
- GET /api/internships/<id>
- GET /api/students
- GET /api/students/<id>
- POST /api/students (input validation and persistence)
- POST /api/recommend (by student_id and dynamic payload, verifying segregation)

ISOLATION GUARANTEE:
Uses an isolated temporary SQLite database file for testing.
The persistent database `data/internship_engine.db` is NEVER touched.
=============================================================================
"""

import os
import json
import unittest
from pathlib import Path

from app import create_app
from app.config import SCHEMA_PATH
from app.database.db import init_db, get_db_connection
from app.database.seed_data import seed_database


class TestAPIEndpoints(unittest.TestCase):
    """
    Integration tests for Flask REST API routes.
    """

    @classmethod
    def setUpClass(cls):
        # Create an isolated temporary test database file in tests/
        cls.test_db_path = Path(__file__).resolve().parent / "test_api_isolated.db"
        if cls.test_db_path.exists():
            cls.test_db_path.unlink()

        # Initialize schema and seed with demonstration dataset
        conn = init_db(cls.test_db_path, SCHEMA_PATH)
        seed_database(conn)
        conn.close()

        # Instantiate Flask application configured to use the test database
        cls.app = create_app({
            "TESTING": True,
            "DB_PATH": cls.test_db_path,
        })
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        # Clean up temporary database file after all tests complete
        if cls.test_db_path.exists():
            try:
                cls.test_db_path.unlink()
            except PermissionError:
                pass

    # -------------------------------------------------------------------------
    # 1. Internships Endpoints
    # -------------------------------------------------------------------------
    def test_get_internships_list(self):
        """GET /api/internships must return all listings with is_demo=True and skills."""
        response = self.client.get("/api/internships")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["count"], 6)

        # Confirm all listings have demonstration flag
        for item in data["internships"]:
            self.assertTrue(item["is_demo"], f"Listing {item['title']} missing is_demo flag")
            self.assertIn("required_skills", item)
            self.assertIn("preferred_skills", item)

    def test_get_internship_by_id_success(self):
        """GET /api/internships/<id> must return the exact opportunity."""
        response = self.client.get("/api/internships/1")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["internship"]["id"], 1)

    def test_get_internship_by_id_not_found(self):
        """GET /api/internships/<id> with unknown ID must return 404."""
        response = self.client.get("/api/internships/9999")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data["status"], "error")
        self.assertIn("not found", data["message"].lower())

    # -------------------------------------------------------------------------
    # 2. Students Endpoints
    # -------------------------------------------------------------------------
    def test_get_students_list(self):
        """GET /api/students must return all seeded students."""
        response = self.client.get("/api/students")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["count"], 3)

    def test_get_student_by_id_success(self):
        """GET /api/students/<id> must return student with their skills."""
        response = self.client.get("/api/students/1")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["student"]["id"], 1)
        self.assertIsInstance(data["student"]["skills"], list)

    def test_get_student_by_id_not_found(self):
        """GET /api/students/<id> with unknown ID must return 404."""
        response = self.client.get("/api/students/9999")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data["status"], "error")

    def test_create_student_success(self):
        """POST /api/students with valid data must create and return the student profile."""
        payload = {
            "name": "Neha Gupta",
            "email": "neha.gupta@example.edu",
            "major": "Data Science",
            "cgpa": 3.75,
            "graduation_year": 2026,
            "preferred_work_mode": "Remote",
            "preferred_location": "Bengaluru, India",
            "bio_summary": "Interested in ML research and predictive modeling.",
            "skills": [
                {"name": "Python", "proficiency": "Advanced"},
                {"name": "SQL", "proficiency": "Intermediate"},
            ],
        }
        response = self.client.post(
            "/api/students",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["student"]["name"], "Neha Gupta")
        self.assertEqual(data["student"]["cgpa"], 3.75)
        self.assertEqual(len(data["student"]["skills"]), 2)

    def test_create_student_validation_errors(self):
        """POST /api/students must reject invalid inputs with descriptive 400 errors."""
        base_valid = {
            "name": "Validation User",
            "email": "valid@example.edu",
            "major": "Computer Science",
            "cgpa": 3.5,
            "graduation_year": 2026,
            "preferred_work_mode": "Remote",
            "preferred_location": "Delhi",
        }

        # 1. Missing name
        p1 = dict(base_valid, name="")
        r1 = self.client.post("/api/students", json=p1)
        self.assertEqual(r1.status_code, 400)
        self.assertIn("name", r1.get_json()["message"])

        # 2. Invalid CGPA (> 4.0)
        p2 = dict(base_valid, cgpa=4.5)
        r2 = self.client.post("/api/students", json=p2)
        self.assertEqual(r2.status_code, 400)
        self.assertIn("CGPA", r2.get_json()["message"])

        # 3. Invalid Graduation Year (< 2020)
        p3 = dict(base_valid, graduation_year=2015)
        r3 = self.client.post("/api/students", json=p3)
        self.assertEqual(r3.status_code, 400)
        self.assertIn("Graduation year", r3.get_json()["message"])

        # 4. Invalid Work Mode
        p4 = dict(base_valid, preferred_work_mode="Mars")
        r4 = self.client.post("/api/students", json=p4)
        self.assertEqual(r4.status_code, 400)
        self.assertIn("work mode", r4.get_json()["message"].lower())

        # 5. Invalid Email
        p5 = dict(base_valid, email="not-an-email")
        r5 = self.client.post("/api/students", json=p5)
        self.assertEqual(r5.status_code, 400)
        self.assertIn("email", r5.get_json()["message"].lower())

        # 6. Invalid Student ID
        p6 = dict(base_valid, id="invalid-id")
        r6 = self.client.post("/api/students", json=p6)
        self.assertEqual(r6.status_code, 400)
        self.assertIn("student ID", r6.get_json()["message"])

    def test_update_existing_student_by_id(self):
        """POST /api/students with id should update existing profile and commit to SQLite."""
        # 1. Read initial state directly from SQLite
        import sqlite3
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        initial_student = conn.execute("SELECT * FROM students WHERE id = 1;").fetchone()
        self.assertEqual(initial_student["name"], "Aarav Sharma")
        self.assertEqual(initial_student["cgpa"], 3.6)
        conn.close()

        initial_res = self.client.get("/api/students")
        initial_count = initial_res.get_json()["count"]

        # 2. Update Student 1 (Aarav Sharma)
        update_payload = {
            "id": 1,
            "name": "Aarav Sharma Updated",
            "email": "aarav.sharma@example.edu",
            "major": "Computer Science & Engineering",
            "cgpa": 3.85,
            "graduation_year": 2026,
            "preferred_work_mode": "Hybrid",
            "preferred_location": "Bengaluru, India",
            "bio_summary": "Updated bio summary for testing.",
            "skills": [
                {"name": "Python", "proficiency": "Advanced"},
                {"name": "Flask", "proficiency": "Intermediate"},
                {"name": "Docker", "proficiency": "Beginner"},
            ],
        }

        response = self.client.post("/api/students", json=update_payload)
        self.assertIn(response.status_code, (200, 201))
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["student"]["id"], 1)
        self.assertEqual(data["student"]["name"], "Aarav Sharma Updated")
        self.assertEqual(data["student"]["cgpa"], 3.85)
        self.assertEqual(data["student"]["preferred_work_mode"], "Hybrid")

        # 3. Verify SQLite on disk directly from a fresh connection
        fresh_conn = sqlite3.connect(self.test_db_path)
        fresh_conn.row_factory = sqlite3.Row
        updated_db_row = fresh_conn.execute("SELECT * FROM students WHERE id = 1;").fetchone()
        self.assertEqual(updated_db_row["name"], "Aarav Sharma Updated")
        self.assertEqual(updated_db_row["cgpa"], 3.85)
        self.assertEqual(updated_db_row["preferred_work_mode"], "Hybrid")
        self.assertEqual(updated_db_row["bio_summary"], "Updated bio summary for testing.")

        # Verify updated skills in SQLite
        skills_rows = fresh_conn.execute(
            """
            SELECT s.name, ss.proficiency_level
            FROM student_skills ss
            JOIN skills s ON ss.skill_id = s.id
            WHERE ss.student_id = 1
            ORDER BY s.name;
            """
        ).fetchall()
        skill_dict = {r["name"]: r["proficiency_level"] for r in skills_rows}
        self.assertIn("Python", skill_dict)
        self.assertEqual(skill_dict["Python"], "Advanced")
        self.assertIn("Flask", skill_dict)
        self.assertEqual(skill_dict["Flask"], "Intermediate")
        self.assertIn("Docker", skill_dict)
        self.assertEqual(skill_dict["Docker"], "Beginner")
        fresh_conn.close()

        # 4. Fetch via GET /api/students/1 and verify updated values
        get_res = self.client.get("/api/students/1")
        self.assertEqual(get_res.status_code, 200)
        get_data = get_res.get_json()["student"]
        self.assertEqual(get_data["name"], "Aarav Sharma Updated")
        self.assertEqual(get_data["cgpa"], 3.85)
        self.assertEqual(get_data["preferred_work_mode"], "Hybrid")

        # 5. Verify no duplicate student was created
        after_res = self.client.get("/api/students")
        after_count = after_res.get_json()["count"]
        self.assertEqual(after_count, initial_count, "Student count must not increase when updating an existing student.")

    def test_update_existing_student_email(self):
        """Updating an existing student's email should succeed, but conflicts must be rejected."""
        import sqlite3

        # Update Student 3's email to a new unique email
        payload = {
            "id": 3,
            "name": "Rohan Verma",
            "email": "rohan.newemail@example.edu",
            "major": "Information Technology",
            "cgpa": 2.8,
            "graduation_year": 2025,
            "preferred_work_mode": "Onsite",
            "preferred_location": "Hyderabad, India",
            "skills": ["Linux", "Git"],
        }
        res = self.client.post("/api/students", json=payload)
        self.assertIn(res.status_code, (200, 201))

        # Check DB directly
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        student3 = conn.execute("SELECT email FROM students WHERE id = 3;").fetchone()
        self.assertEqual(student3["email"], "rohan.newemail@example.edu")

        # Attempt to change Student 3's email to Student 2's email (conflict)
        conflict_payload = dict(payload, email="priya.patel@example.edu")
        conflict_res = self.client.post("/api/students", json=conflict_payload)
        self.assertEqual(conflict_res.status_code, 400)
        self.assertIn("already registered", conflict_res.get_json()["message"])

        # Verify Student 3's email was not corrupted
        student3_after = conn.execute("SELECT email FROM students WHERE id = 3;").fetchone()
        self.assertEqual(student3_after["email"], "rohan.newemail@example.edu")
        conn.close()

    def test_update_nonexistent_student_id_fails(self):
        """POST /api/students with a nonexistent ID must return 404 and not insert a new row."""
        import sqlite3
        conn = sqlite3.connect(self.test_db_path)
        count_before = conn.execute("SELECT COUNT(*) FROM students;").fetchone()[0]
        conn.close()

        payload = {
            "id": 9999,
            "name": "Ghost Student",
            "email": "ghost@example.edu",
            "major": "Computer Science",
            "cgpa": 3.5,
            "graduation_year": 2026,
            "preferred_work_mode": "Remote",
            "preferred_location": "Delhi",
        }
        response = self.client.post("/api/students", json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn("9999", response.get_json()["message"])

        conn = sqlite3.connect(self.test_db_path)
        count_after = conn.execute("SELECT COUNT(*) FROM students;").fetchone()[0]
        conn.close()
        self.assertEqual(count_after, count_before, "No new student should be inserted when ID does not exist.")

    def test_invalid_input_does_not_corrupt_existing_student(self):
        """Invalid inputs must be rejected with 400 and preserve existing database values."""
        import sqlite3
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        original = conn.execute("SELECT * FROM students WHERE id = 2;").fetchone()
        orig_cgpa = original["cgpa"]
        orig_major = original["major"]
        conn.close()

        # Send invalid CGPA (4.5)
        bad_payload = {
            "id": 2,
            "name": "Priya Patel",
            "email": "priya.patel@example.edu",
            "major": "Data Science",
            "cgpa": 4.5,
            "graduation_year": 2026,
            "preferred_work_mode": "Hybrid",
            "preferred_location": "Mumbai, India",
        }
        res = self.client.post("/api/students", json=bad_payload)
        self.assertEqual(res.status_code, 400)

        # Verify DB still has original values
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        current = conn.execute("SELECT * FROM students WHERE id = 2;").fetchone()
        self.assertEqual(current["cgpa"], orig_cgpa)
        self.assertEqual(current["major"], orig_major)
        conn.close()

    def test_create_new_student_duplicate_email_rejected(self):
        """Creating a new student with an existing email must return 400."""
        payload = {
            "name": "Another Person",
            "email": "aarav.sharma@example.edu", # Already registered to student 1
            "major": "Mechanical Engineering",
            "cgpa": 3.2,
            "graduation_year": 2026,
            "preferred_work_mode": "Onsite",
            "preferred_location": "Chennai",
        }
        res = self.client.post("/api/students", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("already registered", res.get_json()["message"])

    # -------------------------------------------------------------------------
    # 3. Recommendation Endpoints
    # -------------------------------------------------------------------------
    def test_recommend_by_registered_student_id(self):
        """POST /api/recommend with student_id must return segregated recommendations."""
        # Student 1 is Aarav Sharma (CS, CGPA 3.6, Remote)
        response = self.client.post(
            "/api/recommend",
            json={"student_id": 1},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(data["status"], "success")
        self.assertEqual(data["student_id"], 1)
        self.assertIn("eligible_recommendations", data)
        self.assertIn("ineligible_listings", data)

        eligible = data["eligible_recommendations"]
        ineligible = data["ineligible_listings"]

        self.assertGreater(len(eligible), 0)
        self.assertGreater(len(ineligible), 0)

        # Check descending sort order for eligible items
        scores = [item["total_score"] for item in eligible]
        self.assertEqual(scores, sorted(scores, reverse=True))

        # Check that ineligible items have total_score == 0.0 and reasons
        for inel in ineligible:
            self.assertEqual(inel["total_score"], 0.0)
            self.assertFalse(inel["eligibility"]["is_eligible"])
            self.assertGreater(len(inel["eligibility"]["rejection_reasons"]), 0)

    def test_recommend_by_unknown_student_id(self):
        """POST /api/recommend with nonexistent ID must return 404."""
        response = self.client.post("/api/recommend", json={"student_id": 9999})
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data["status"], "error")
        self.assertIn("9999", data["message"])

    def test_recommend_dynamic_profile_payload(self):
        """POST /api/recommend with full profile object must run dynamic discovery."""
        dynamic_payload = {
            "name": "Dynamic Candidate",
            "major": "Computer Science",
            "cgpa": 3.9,
            "graduation_year": 2026,
            "preferred_work_mode": "Remote",
            "preferred_location": "Bengaluru, India",
            "skills": ["Python", "SQL", "Git", "Docker"],
        }
        response = self.client.post("/api/recommend", json=dynamic_payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(data["status"], "success")
        self.assertEqual(data["student_name"], "Dynamic Candidate")
        self.assertGreater(len(data["eligible_recommendations"]), 0)

    def test_recommend_invalid_payload(self):
        """POST /api/recommend with empty or invalid payload must return 400."""
        response = self.client.post("/api/recommend", data="not json", content_type="text/plain")
        self.assertEqual(response.status_code, 400)

    # -------------------------------------------------------------------------
    # 4. Health Check Endpoint
    # -------------------------------------------------------------------------
    def test_health_check_endpoint(self):
        """GET /health must return 200 and operational status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")


if __name__ == "__main__":
    unittest.main()

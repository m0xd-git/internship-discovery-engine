"""
Frontend View & Static Asset Integration Tests
=============================================================================
Tests the web interface routes:
- GET / (Dashboard view)
- GET /profile (Student profile management view)
- GET /static/css/styles.css (Responsive stylesheet)
- GET /static/js/api.js, dashboard.js, profile.js (Frontend client logic)
- GET /nonexistent (404 error handling)
=============================================================================
"""

import unittest
from pathlib import Path

from app import create_app
from app.config import SCHEMA_PATH
from app.database.db import init_db
from app.database.seed_data import seed_database


class TestFrontendViews(unittest.TestCase):
    """
    Integration tests for frontend HTML views and static asset serving.
    """

    @classmethod
    def setUpClass(cls):
        # Create an isolated temporary test database file
        cls.test_db_path = Path(__file__).resolve().parent / "test_views_isolated.db"
        if cls.test_db_path.exists():
            cls.test_db_path.unlink()

        conn = init_db(cls.test_db_path, SCHEMA_PATH)
        seed_database(conn)
        conn.close()

        cls.app = create_app({
            "TESTING": True,
            "DB_PATH": cls.test_db_path,
        })
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        if cls.test_db_path.exists():
            try:
                cls.test_db_path.unlink()
            except PermissionError:
                pass

    def test_dashboard_view_renders_successfully(self):
        """GET / should render dashboard HTML with title and demonstration notices."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.content_type)

        html = response.get_data(as_text=True)
        # Check required architectural and ethical UI elements
        self.assertIn("Internship Discovery Engine", html)
        self.assertIn("ACADEMIC DEMONSTRATION", html)
        self.assertIn("is_demo = 1", html)
        self.assertIn("studentSelect", html)
        self.assertIn("discoverBtn", html)
        self.assertIn("tabEligible", html)
        self.assertIn("tabIneligible", html)
        self.assertIn("Ethical Recommender System Notice", html)
        self.assertIn("Scores do not represent hiring probabilities", html)

    def test_profile_view_renders_successfully(self):
        """GET /profile should render student profile management form."""
        response = self.client.get("/profile")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.content_type)

        html = response.get_data(as_text=True)
        self.assertIn("Student Competency & Academic Profile", html)
        self.assertIn("profileStudentSelect", html)
        self.assertIn("createNewProfileBtn", html)
        self.assertIn("profileModeBanner", html)
        self.assertIn("Select Profile to View / Edit", html)
        self.assertIn("+ Create New Student", html)
        self.assertIn("studentProfileForm", html)
        self.assertIn("studentName", html)
        self.assertIn("studentEmail", html)
        self.assertIn("studentMajor", html)
        self.assertIn("studentCgpa", html)
        self.assertIn("studentGradYear", html)
        self.assertIn("studentWorkMode", html)
        self.assertIn("studentLocation", html)
        self.assertIn("skillNameInput", html)
        self.assertIn("addSkillBtn", html)
        self.assertIn("saveProfileBtn", html)

    def test_static_stylesheet_served(self):
        """GET /static/css/styles.css should return CSS with 200 status."""
        response = self.client.get("/static/css/styles.css")
        self.assertEqual(response.status_code, 200)
        css = response.get_data(as_text=True)
        response.close()
        self.assertIn("--primary:", css)
        self.assertIn(".demo-banner", css)

    def test_static_scripts_served(self):
        """GET /static/js/*.js should return JavaScript assets with 200 status."""
        for script_name in ["api.js", "dashboard.js", "profile.js"]:
            response = self.client.get(f"/static/js/{script_name}")
            self.assertEqual(response.status_code, 200, f"Failed to serve /static/js/{script_name}")
            self.assertGreater(len(response.data), 0)
            response.close()

    def test_nonexistent_route_returns_404(self):
        """GET /nonexistent should return 404 Not Found."""
        response = self.client.get("/nonexistent-page-url")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()

"""
Automated Unit Tests for Rule-Based Eligibility Gatekeeper
Tests all boundary conditions, individual failures, multiple simultaneous failures,
major normalization, work-mode compatibility, and defensive handling.

All tests use in-memory dataclass instances; no persistent database rows are modified.
"""

import unittest
from app.models.entities import Student, Internship
from app.engine.eligibility import (
    check_eligibility,
    filter_eligible_internships,
    normalize_major,
    evaluate_cgpa_eligibility,
    evaluate_major_eligibility,
    evaluate_grad_year_eligibility,
    evaluate_work_mode_compatibility,
)


class TestEligibilityEngine(unittest.TestCase):
    """
    Test suite verifying deterministic behavior of the Rule-Based Eligibility Gatekeeper.
    """

    def setUp(self):
        # Baseline reference internship
        self.base_internship = Internship(
            id=1,
            title="Software Engineering Intern",
            organization="Tech Corp",
            location="Bengaluru",
            work_mode="Remote",
            min_cgpa=3.0,
            eligible_majors=["Computer Science", "Information Technology"],
            min_grad_year=2025,
            max_grad_year=2027,
            description="Backend role in Python.",
            is_demo=True,
            required_skills=["Python", "SQL"],
        )

        # Baseline fully eligible student
        self.eligible_student = Student(
            id=1,
            name="Alice Wonder",
            email="alice@example.edu",
            major="Computer Science",
            cgpa=3.5,
            graduation_year=2026,
            preferred_work_mode="Remote",
            preferred_location="Bengaluru",
            bio_summary="Passionate backend builder.",
        )

    # -------------------------------------------------------------------------
    # 1. Fully Passing Candidates
    # -------------------------------------------------------------------------
    def test_fully_eligible_student_passes(self):
        """A student meeting all academic and logistical requirements must pass."""
        result = check_eligibility(self.eligible_student, self.base_internship)
        self.assertTrue(result.is_eligible)
        self.assertEqual(len(result.rejection_reasons), 0)
        self.assertTrue(result.checks["cgpa_met"])
        self.assertTrue(result.checks["major_eligible"])
        self.assertTrue(result.checks["grad_year_valid"])
        self.assertTrue(result.checks["work_mode_compatible"])

    # -------------------------------------------------------------------------
    # 2. Individual Failure Cases
    # -------------------------------------------------------------------------
    def test_cgpa_failure_only(self):
        """A student with lower CGPA than cutoff must fail with explicit reason."""
        student = Student(
            id=2,
            name="Bob Lower GPA",
            email="bob@example.edu",
            major="Computer Science",
            cgpa=2.85,  # below 3.0
            graduation_year=2026,
            preferred_work_mode="Remote",
            preferred_location="Bengaluru",
        )
        result = check_eligibility(student, self.base_internship)
        self.assertFalse(result.is_eligible)
        self.assertFalse(result.checks["cgpa_met"])
        self.assertTrue(result.checks["major_eligible"])
        self.assertTrue(result.checks["grad_year_valid"])
        self.assertTrue(result.checks["work_mode_compatible"])
        self.assertEqual(len(result.rejection_reasons), 1)
        self.assertIn("CGPA requirement not met", result.rejection_reasons[0])
        self.assertIn("2.85", result.rejection_reasons[0])
        self.assertIn("3.00", result.rejection_reasons[0])

    def test_major_failure_only(self):
        """A student with non-matching major must fail with explicit reason."""
        student = Student(
            id=3,
            name="Charlie Mechanical",
            email="charlie@example.edu",
            major="Mechanical Engineering",
            cgpa=3.8,
            graduation_year=2026,
            preferred_work_mode="Remote",
            preferred_location="Bengaluru",
        )
        result = check_eligibility(student, self.base_internship)
        self.assertFalse(result.is_eligible)
        self.assertTrue(result.checks["cgpa_met"])
        self.assertFalse(result.checks["major_eligible"])
        self.assertEqual(len(result.rejection_reasons), 1)
        self.assertIn("Major requirement not met", result.rejection_reasons[0])
        self.assertIn("Mechanical Engineering", result.rejection_reasons[0])

    def test_grad_year_too_early_failure(self):
        """A student who graduated earlier than minimum allowed year must fail."""
        student = Student(
            id=4,
            name="Dana Alum",
            email="dana@example.edu",
            major="Computer Science",
            cgpa=3.7,
            graduation_year=2024,  # min_grad_year is 2025
            preferred_work_mode="Remote",
            preferred_location="Bengaluru",
        )
        result = check_eligibility(student, self.base_internship)
        self.assertFalse(result.is_eligible)
        self.assertFalse(result.checks["grad_year_valid"])
        self.assertEqual(len(result.rejection_reasons), 1)
        self.assertIn("earlier than minimum allowed (2025)", result.rejection_reasons[0])

    def test_grad_year_too_late_failure(self):
        """A student who graduates later than maximum allowed year must fail."""
        student = Student(
            id=5,
            name="Eve Freshman",
            email="eve@example.edu",
            major="Computer Science",
            cgpa=3.7,
            graduation_year=2028,  # max_grad_year is 2027
            preferred_work_mode="Remote",
            preferred_location="Bengaluru",
        )
        result = check_eligibility(student, self.base_internship)
        self.assertFalse(result.is_eligible)
        self.assertFalse(result.checks["grad_year_valid"])
        self.assertEqual(len(result.rejection_reasons), 1)
        self.assertIn("later than maximum allowed (2027)", result.rejection_reasons[0])

    def test_work_mode_incompatibility_failure(self):
        """A student with incompatible work mode preference must fail."""
        student = Student(
            id=6,
            name="Frank Onsite Only",
            email="frank@example.edu",
            major="Computer Science",
            cgpa=3.7,
            graduation_year=2026,
            preferred_work_mode="Onsite",  # internship is Remote
            preferred_location="Bengaluru",
        )
        result = check_eligibility(student, self.base_internship)
        self.assertFalse(result.is_eligible)
        self.assertFalse(result.checks["work_mode_compatible"])
        self.assertEqual(len(result.rejection_reasons), 1)
        self.assertIn("Work mode incompatibility", result.rejection_reasons[0])
        self.assertIn("student prefers 'Onsite' but internship requires 'Remote'", result.rejection_reasons[0])

    # -------------------------------------------------------------------------
    # 3. Multiple Simultaneous Failures (Non-Short-Circuiting)
    # -------------------------------------------------------------------------
    def test_multiple_simultaneous_failures_reported(self):
        """When multiple requirements fail, ALL failures must be reported."""
        student = Student(
            id=7,
            name="George Multi-Fail",
            email="george@example.edu",
            major="Civil Engineering",     # Fail: not CS/IT
            cgpa=2.2,                      # Fail: below 3.0
            graduation_year=2023,          # Fail: earlier than 2025
            preferred_work_mode="Onsite",  # Fail: internship is Remote
            preferred_location="Mumbai",
        )
        result = check_eligibility(student, self.base_internship)
        self.assertFalse(result.is_eligible)
        self.assertEqual(len(result.rejection_reasons), 4)
        self.assertFalse(result.checks["cgpa_met"])
        self.assertFalse(result.checks["major_eligible"])
        self.assertFalse(result.checks["grad_year_valid"])
        self.assertFalse(result.checks["work_mode_compatible"])

    # -------------------------------------------------------------------------
    # 4. Exact Boundary Conditions
    # -------------------------------------------------------------------------
    def test_exact_cgpa_boundary_passes(self):
        """Student with CGPA exactly equal to cutoff must pass."""
        ok, reason = evaluate_cgpa_eligibility(3.00, 3.00)
        self.assertTrue(ok)
        self.assertIsNone(reason)

    def test_cgpa_just_below_boundary_fails(self):
        """Student with CGPA slightly below cutoff must fail."""
        ok, reason = evaluate_cgpa_eligibility(2.99, 3.00)
        self.assertFalse(ok)
        self.assertIn("below minimum required", reason)

    def test_exact_grad_year_boundaries_pass(self):
        """Student graduating on exact min or max boundary year must pass."""
        ok_min, _ = evaluate_grad_year_eligibility(2025, 2025, 2027)
        self.assertTrue(ok_min)

        ok_max, _ = evaluate_grad_year_eligibility(2027, 2025, 2027)
        self.assertTrue(ok_max)

    # -------------------------------------------------------------------------
    # 5. Major Normalization & Wildcards
    # -------------------------------------------------------------------------
    def test_major_normalization_aliases(self):
        """Abbreviations and synonyms must normalize to canonical disciplines."""
        self.assertEqual(normalize_major("CS"), "computer science")
        self.assertEqual(normalize_major("cse"), "computer science")
        self.assertEqual(normalize_major("B.Tech in CS"), "computer science")
        self.assertEqual(normalize_major("IT"), "information technology")
        self.assertEqual(normalize_major("DS"), "data science")
        self.assertEqual(normalize_major("AI"), "artificial intelligence")

    def test_major_case_and_alias_matching(self):
        """Student with 'cs' must match an internship requiring 'Computer Science'."""
        ok, reason = evaluate_major_eligibility("cs", ["Computer Science", "Information Technology"])
        self.assertTrue(ok)
        self.assertIsNone(reason)

    def test_major_any_wildcard_passes_all(self):
        """An internship accepting 'Any' discipline must pass any valid student major."""
        ok, _ = evaluate_major_eligibility("History", ["Any"])
        self.assertTrue(ok)

        ok_star, _ = evaluate_major_eligibility("Mechanical", ["*"])
        self.assertTrue(ok_star)

        ok_empty, _ = evaluate_major_eligibility("Philosophy", [])
        self.assertTrue(ok_empty)

    # -------------------------------------------------------------------------
    # 6. Work Mode Compatibility Rules
    # -------------------------------------------------------------------------
    def test_work_mode_student_any_matches_all(self):
        """A student open to 'Any' mode must be compatible with Remote, Hybrid, and Onsite."""
        for mode in ["Remote", "Hybrid", "Onsite"]:
            ok, _ = evaluate_work_mode_compatibility("Any", mode)
            self.assertTrue(ok, f"Failed for mode {mode}")

    def test_work_mode_exact_matches(self):
        """Exact mode preferences must be compatible."""
        self.assertTrue(evaluate_work_mode_compatibility("Remote", "Remote")[0])
        self.assertTrue(evaluate_work_mode_compatibility("Hybrid", "Hybrid")[0])
        self.assertTrue(evaluate_work_mode_compatibility("Onsite", "Onsite")[0])

    def test_work_mode_incompatibilities(self):
        """Conflicting work modes must be rejected."""
        self.assertFalse(evaluate_work_mode_compatibility("Remote", "Hybrid")[0])
        self.assertFalse(evaluate_work_mode_compatibility("Remote", "Onsite")[0])
        self.assertFalse(evaluate_work_mode_compatibility("Onsite", "Remote")[0])
        self.assertFalse(evaluate_work_mode_compatibility("Hybrid", "Remote")[0])

    # -------------------------------------------------------------------------
    # 7. Defensive Handling of Missing / Invalid Values
    # -------------------------------------------------------------------------
    def test_missing_and_invalid_cgpa(self):
        """Missing or out-of-bounds CGPA must be rejected defensively."""
        self.assertFalse(evaluate_cgpa_eligibility(None, 3.0)[0])
        self.assertFalse(evaluate_cgpa_eligibility(-0.5, 3.0)[0])
        self.assertFalse(evaluate_cgpa_eligibility(4.5, 3.0)[0])

    def test_missing_major(self):
        """Missing or blank student major must be rejected."""
        self.assertFalse(evaluate_major_eligibility(None, ["Computer Science"])[0])
        self.assertFalse(evaluate_major_eligibility("   ", ["Computer Science"])[0])

    def test_missing_grad_year(self):
        """Missing or non-integer graduation year must be rejected."""
        self.assertFalse(evaluate_grad_year_eligibility(None, 2025, 2027)[0])

    def test_invalid_work_mode(self):
        """Unrecognized work mode string must be rejected."""
        self.assertFalse(evaluate_work_mode_compatibility("Mars", "Remote")[0])
        self.assertFalse(evaluate_work_mode_compatibility(None, "Remote")[0])

    # -------------------------------------------------------------------------
    # 8. Partitioning Utility (filter_eligible_internships)
    # -------------------------------------------------------------------------
    def test_filter_eligible_internships_partitioning(self):
        """Verify that filter_eligible_internships cleanly splits opportunities."""
        ineligible_internship = Internship(
            id=2,
            title="Senior AI Fellow",
            organization="Apex AI",
            location="Remote",
            work_mode="Remote",
            min_cgpa=3.9,  # student has 3.5
            eligible_majors=["Computer Science"],
            min_grad_year=2025,
            max_grad_year=2027,
            description="High threshold role.",
            is_demo=True,
        )

        all_internships = [self.base_internship, ineligible_internship]
        eligible, ineligible = filter_eligible_internships(self.eligible_student, all_internships)

        self.assertEqual(len(eligible), 1)
        self.assertEqual(len(ineligible), 1)
        self.assertEqual(eligible[0][0].id, 1)
        self.assertEqual(ineligible[0][0].id, 2)
        self.assertFalse(ineligible[0][1].is_eligible)
        self.assertIn("CGPA requirement not met", ineligible[0][1].rejection_reasons[0])


if __name__ == "__main__":
    unittest.main()

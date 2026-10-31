"""
Automated Unit Tests for Recommendation Scoring Engine
Tests multi-factor scoring, transparent breakdown arithmetic,
strict eligibility gatekeeping (ineligible items always score 0.0),
boundary clamping, missing profile data, empty requirements, and weight validation.

All tests use in-memory dataclass instances; no persistent database rows are modified.
"""

import unittest
from app.config import DEFAULT_SCORING_WEIGHTS
from app.models.entities import Student, Internship
from app.engine.scorer import (
    score_internship,
    generate_recommendations,
    calculate_required_skill_score,
    calculate_preferred_skill_score,
    calculate_academic_alignment_score,
    calculate_location_alignment_score,
)
from app.engine.gap_analyzer import analyze_skill_gaps


class TestScoringEngine(unittest.TestCase):
    """
    Unit tests verifying mathematical transparency, deterministic scoring,
    and strict gatekeeping invariants.
    """

    def setUp(self):
        # Baseline eligible internship
        self.internship = Internship(
            id=10,
            title="Full Stack Software Intern",
            organization="Innovate Corp",
            location="Bengaluru, India",
            work_mode="Remote",
            min_cgpa=3.0,
            eligible_majors=["Computer Science", "Information Technology"],
            min_grad_year=2025,
            max_grad_year=2027,
            description="Build scalable web backends and interfaces.",
            is_demo=True,
            required_skills=["Python", "SQL"],
            preferred_skills=["Docker", "Git"],
        )

        # Baseline fully qualified student
        self.student = Student(
            id=100,
            name="Divya Rao",
            email="divya@example.edu",
            major="Computer Science",
            cgpa=3.8,
            graduation_year=2026,
            preferred_work_mode="Remote",
            preferred_location="Bengaluru, India",
            skills=[],
        )

    # -------------------------------------------------------------------------
    # 1. Fully Matched Eligible Candidate
    # -------------------------------------------------------------------------
    def test_fully_matched_eligible_internship(self):
        """A candidate matching 100% of skills and criteria must earn top score."""
        self.student.skills = ["Python", "SQL", "Docker", "Git"]
        self.student.cgpa = 4.0  # Perfect GPA headroom

        rec = score_internship(self.student, self.internship)

        self.assertTrue(rec.eligibility.is_eligible)
        self.assertEqual(rec.total_score, 100.0)

        bd = rec.score_breakdown
        self.assertEqual(bd.required_skills["points"], 45.0)
        self.assertEqual(bd.preferred_skills["points"], 15.0)
        self.assertEqual(bd.academic_alignment["points"], 20.0)
        self.assertEqual(bd.location_alignment["points"], 20.0)

    # -------------------------------------------------------------------------
    # 2. Partial and Zero Skill Matches
    # -------------------------------------------------------------------------
    def test_partial_skill_match_scoring(self):
        """Partial skill matches must award exactly proportional points."""
        # Student has 1 of 2 required (Python), and 1 of 2 preferred (Docker)
        self.student.skills = ["Python", "Docker"]
        self.student.cgpa = 3.5

        rec = score_internship(self.student, self.internship)

        self.assertTrue(rec.eligibility.is_eligible)
        bd = rec.score_breakdown

        # Required: 1/2 * 45 = 22.5
        self.assertEqual(bd.required_skills["points"], 22.5)
        # Preferred: 1/2 * 15 = 7.5
        self.assertEqual(bd.preferred_skills["points"], 7.5)

        # Verify arithmetic sum
        expected_total = round(
            bd.required_skills["points"]
            + bd.preferred_skills["points"]
            + bd.academic_alignment["points"]
            + bd.location_alignment["points"]
            + bd.semantic_similarity["points"],
            2,
        )
        self.assertAlmostEqual(rec.total_score, expected_total, places=2)

    def test_no_skill_matches_still_eligible(self):
        """A candidate with no matching skills earns 0 skill points but keeps academic/location points."""
        self.student.skills = ["Rust", "Haskell"]  # Unrelated skills

        rec = score_internship(self.student, self.internship)

        self.assertTrue(rec.eligibility.is_eligible)
        bd = rec.score_breakdown
        self.assertEqual(bd.required_skills["points"], 0.0)
        self.assertEqual(bd.preferred_skills["points"], 0.0)
        self.assertGreater(bd.academic_alignment["points"], 0.0)
        self.assertGreater(bd.location_alignment["points"], 0.0)
        self.assertEqual(
            rec.total_score,
            round(bd.academic_alignment["points"] + bd.location_alignment["points"], 2),
        )

    # -------------------------------------------------------------------------
    # 3. Empty Requirements Handling (No Division-by-Zero)
    # -------------------------------------------------------------------------
    def test_empty_required_and_preferred_skills_handling(self):
        """Internship with no skills listed must award 0 skill points without crashing."""
        open_internship = Internship(
            id=11,
            title="General Explorer Intern",
            organization="Open Labs",
            location="Remote",
            work_mode="Remote",
            min_cgpa=2.5,
            eligible_majors=["Any"],
            min_grad_year=2025,
            max_grad_year=2027,
            description="Role with no required technical prerequisites.",
            is_demo=True,
            required_skills=[],
            preferred_skills=[],
        )

        rec = score_internship(self.student, open_internship)

        self.assertTrue(rec.eligibility.is_eligible)
        bd = rec.score_breakdown
        self.assertEqual(bd.required_skills["points"], 0.0)
        self.assertEqual(bd.preferred_skills["points"], 0.0)
        self.assertIn("No mandatory skills listed", bd.required_skills["details"])
        self.assertIn("No preferred bonus skills listed", bd.preferred_skills["details"])

    # -------------------------------------------------------------------------
    # 4. Strict Eligibility Gatekeeping (Ineligible Must Score EXACTLY 0.0)
    # -------------------------------------------------------------------------
    def test_ineligible_with_100_percent_skills_scores_zero(self):
        """CRITICAL INVARIANT: 100% skill match must NEVER override failed eligibility."""
        self.student.skills = ["Python", "SQL", "Docker", "Git"]
        self.student.cgpa = 2.7  # FAILS cutoff 3.0

        rec = score_internship(self.student, self.internship)

        self.assertFalse(rec.eligibility.is_eligible)
        self.assertEqual(rec.total_score, 0.0)

        # Confirm all components are 0.0 and reasons are explicitly documented
        bd = rec.score_breakdown
        self.assertEqual(bd.required_skills["points"], 0.0)
        self.assertEqual(bd.preferred_skills["points"], 0.0)
        self.assertEqual(bd.academic_alignment["points"], 0.0)
        self.assertEqual(bd.location_alignment["points"], 0.0)
        self.assertIn("Disqualified by Eligibility Gatekeeper", bd.required_skills["details"])
        self.assertIn("CGPA requirement not met", bd.required_skills["details"])

    def test_each_individual_eligibility_failure_scores_zero(self):
        """Any single eligibility failure must drop total_score to 0.0."""
        self.student.skills = ["Python", "SQL"]

        # Failure 1: Major mismatch
        bad_major_student = Student(
            id=101, name="Bad Major", email="m@edu.com", major="Civil Engineering",
            cgpa=3.5, graduation_year=2026, preferred_work_mode="Remote", preferred_location="Bengaluru",
        )
        rec1 = score_internship(bad_major_student, self.internship)
        self.assertEqual(rec1.total_score, 0.0)

        # Failure 2: Grad year too early
        early_student = Student(
            id=102, name="Early", email="e@edu.com", major="Computer Science",
            cgpa=3.5, graduation_year=2024, preferred_work_mode="Remote", preferred_location="Bengaluru",
        )
        rec2 = score_internship(early_student, self.internship)
        self.assertEqual(rec2.total_score, 0.0)

        # Failure 3: Work mode conflict
        onsite_student = Student(
            id=103, name="Onsite", email="o@edu.com", major="Computer Science",
            cgpa=3.5, graduation_year=2026, preferred_work_mode="Onsite", preferred_location="Bengaluru",
        )
        rec3 = score_internship(onsite_student, self.internship)
        self.assertEqual(rec3.total_score, 0.0)

    def test_multiple_eligibility_failures_score_zero(self):
        """Candidate failing multiple criteria must score 0.0 and report all failures."""
        disqualified_student = Student(
            id=104, name="Multi Fail", email="multi@edu.com", major="Fine Arts",
            cgpa=2.1, graduation_year=2023, preferred_work_mode="Onsite", preferred_location="Mumbai",
        )
        rec = score_internship(disqualified_student, self.internship)
        self.assertEqual(rec.total_score, 0.0)
        self.assertEqual(len(rec.eligibility.rejection_reasons), 4)

    # -------------------------------------------------------------------------
    # 5. Score Boundaries and Breakdown Arithmetic
    # -------------------------------------------------------------------------
    def test_score_boundaries_clamping(self):
        """Scores must strictly remain within [0.0, 100.0]."""
        self.student.skills = ["Python", "SQL", "Docker", "Git"]
        rec = score_internship(self.student, self.internship)
        self.assertGreaterEqual(rec.total_score, 0.0)
        self.assertLessEqual(rec.total_score, 100.0)

    def test_score_breakdown_arithmetic_matches_total(self):
        """The sum of individual breakdown points must equal the total_score."""
        self.student.skills = ["Python"]
        self.student.cgpa = 3.4
        rec = score_internship(self.student, self.internship)

        bd = rec.score_breakdown
        summed = round(
            bd.required_skills["points"]
            + bd.preferred_skills["points"]
            + bd.academic_alignment["points"]
            + bd.location_alignment["points"]
            + bd.semantic_similarity["points"],
            2,
        )
        self.assertEqual(rec.total_score, summed)

    # -------------------------------------------------------------------------
    # 6. Missing Profile Data Handling
    # -------------------------------------------------------------------------
    def test_missing_profile_data_handling(self):
        """Missing student profile fields must award 0 points defensively without crashing."""
        student_missing_data = Student(
            id=105,
            name="Incomplete Profile",
            email="inc@example.edu",
            major="",               # Missing major
            cgpa=3.5,
            graduation_year=2026,
            preferred_work_mode="Remote",
            preferred_location="",  # Missing location
        )
        # Because major is empty, eligibility will reject
        rec = score_internship(student_missing_data, self.internship)
        self.assertFalse(rec.eligibility.is_eligible)
        self.assertEqual(rec.total_score, 0.0)

    # -------------------------------------------------------------------------
    # 7. Weight Validation
    # -------------------------------------------------------------------------
    def test_weight_validation_catches_invalid_configs(self):
        """Invalid weights (negative or not summing to 1.0) must raise ValueError."""
        # Negative weight
        bad_weights_neg = {"required_skills": -0.1, "preferred_skills": 0.5, "academic_alignment": 0.3, "location_alignment": 0.3, "semantic_similarity": 0.0}
        with self.assertRaises(ValueError):
            score_internship(self.student, self.internship, bad_weights_neg)

        # Sum doesn't equal 1.0 (sums to 0.8)
        bad_weights_sum = {"required_skills": 0.3, "preferred_skills": 0.1, "academic_alignment": 0.2, "location_alignment": 0.2, "semantic_similarity": 0.0}
        with self.assertRaises(ValueError):
            score_internship(self.student, self.internship, bad_weights_sum)

    # -------------------------------------------------------------------------
    # 8. Segregation and Ranking in generate_recommendations()
    # -------------------------------------------------------------------------
    def test_generate_recommendations_segregation_and_ranking(self):
        """Eligible listings must be ranked descending; ineligible listings must be segregated."""
        # Role 1: Top match (Remote, CS, CGPA 3.0 cutoff)
        role1 = self.internship

        # Role 2: Eligible but lower skill match (Hybrid, min CGPA 3.2, Python + Data Analysis)
        role2 = Internship(
            id=12,
            title="Data Analyst Intern",
            organization="Health Authority",
            location="Bengaluru, India",
            work_mode="Remote",
            min_cgpa=3.2,
            eligible_majors=["Computer Science"],
            min_grad_year=2025,
            max_grad_year=2027,
            description="Analytics role.",
            is_demo=True,
            required_skills=["Pandas", "Tableau"],  # Student has none
            preferred_skills=[],
        )

        # Role 3: Ineligible (CGPA cutoff 3.9)
        role3 = Internship(
            id=13,
            title="Executive AI Scholar",
            organization="Apex Research",
            location="Bengaluru, India",
            work_mode="Remote",
            min_cgpa=3.9,  # student has 3.8
            eligible_majors=["Computer Science"],
            min_grad_year=2025,
            max_grad_year=2027,
            description="Ultra high cutoff.",
            is_demo=True,
            required_skills=["Python"],
        )

        self.student.skills = ["Python", "SQL", "Docker", "Git"]

        eligible, ineligible = generate_recommendations(self.student, [role1, role2, role3])

        # Verify segregation
        self.assertEqual(len(eligible), 2)
        self.assertEqual(len(ineligible), 1)

        # Verify ranking order: role1 (100 pts) > role2 (lower pts)
        self.assertEqual(eligible[0].internship_id, 10)
        self.assertEqual(eligible[1].internship_id, 12)
        self.assertGreater(eligible[0].total_score, eligible[1].total_score)

        # Verify ineligible listing
        self.assertEqual(ineligible[0].internship_id, 13)
        self.assertEqual(ineligible[0].total_score, 0.0)
        self.assertFalse(ineligible[0].eligibility.is_eligible)
        self.assertIn("CGPA requirement not met", ineligible[0].eligibility.rejection_reasons[0])


if __name__ == "__main__":
    unittest.main()

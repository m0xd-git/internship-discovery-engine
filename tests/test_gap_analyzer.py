"""
Automated Unit Tests for Skill-Gap Analyzer
Tests exact gap extraction, required vs preferred classification,
deduplication, empty lists, StudentSkill objects, and summary formatting.
"""

import unittest
from app.models.entities import StudentSkill
from app.engine.gap_analyzer import (
    analyze_skill_gaps,
    extract_skill_names,
    format_gap_summary,
)


class TestGapAnalyzer(unittest.TestCase):
    """
    Unit tests for deterministic skill gap analysis and reporting.
    """

    def test_all_skills_matched(self):
        """When a student possesses all required and preferred skills, gaps must be empty."""
        student_skills = ["Python", "SQL", "Git", "Docker"]
        required = ["python", "sql"]
        preferred = ["git", "docker"]

        report = analyze_skill_gaps(student_skills, required, preferred)

        self.assertEqual(len(report.matched_required_skills), 2)
        self.assertEqual(len(report.missing_required_skills), 0)
        self.assertEqual(len(report.matched_preferred_skills), 2)
        self.assertEqual(len(report.missing_preferred_skills), 0)
        self.assertFalse(report.has_critical_gap)
        self.assertEqual(report.total_required_skills, 2)
        self.assertEqual(report.total_preferred_skills, 2)

    def test_partial_match_with_critical_gap(self):
        """Missing required skills must be flagged as critical gaps."""
        student_skills = ["Python", "Git"]
        required = ["Python", "SQL", "Docker"]
        preferred = ["Git", "Linux"]

        report = analyze_skill_gaps(student_skills, required, preferred)

        self.assertEqual(report.matched_required_skills, ["Python"])
        self.assertEqual(sorted(report.missing_required_skills), ["Docker", "SQL"])
        self.assertEqual(report.matched_preferred_skills, ["Git"])
        self.assertEqual(report.missing_preferred_skills, ["Linux"])
        self.assertTrue(report.has_critical_gap)

    def test_alias_resolution_in_gap_analysis(self):
        """Aliases like 'postgres' or 'sklearn' must match 'PostgreSQL' or 'Scikit-Learn'."""
        student_skills = ["postgres", "sklearn"]
        required = ["PostgreSQL"]
        preferred = ["Scikit-Learn"]

        report = analyze_skill_gaps(student_skills, required, preferred)

        self.assertIn("PostgreSQL", report.matched_required_skills)
        self.assertIn("Scikit-Learn", report.matched_preferred_skills)
        self.assertEqual(len(report.missing_required_skills), 0)
        self.assertEqual(len(report.missing_preferred_skills), 0)

    def test_empty_student_skills_safe(self):
        """A student with no listed skills must have 0 matched and all missing."""
        report = analyze_skill_gaps([], ["Python", "SQL"], ["Docker"])

        self.assertEqual(len(report.matched_required_skills), 0)
        self.assertEqual(len(report.missing_required_skills), 2)
        self.assertEqual(len(report.matched_preferred_skills), 0)
        self.assertEqual(len(report.missing_preferred_skills), 1)
        self.assertTrue(report.has_critical_gap)

    def test_empty_internship_skills_safe(self):
        """An internship with no required or preferred skills must return clean zeros."""
        report = analyze_skill_gaps(["Python", "SQL"], [], [])

        self.assertEqual(len(report.matched_required_skills), 0)
        self.assertEqual(len(report.missing_required_skills), 0)
        self.assertEqual(len(report.matched_preferred_skills), 0)
        self.assertEqual(len(report.missing_preferred_skills), 0)
        self.assertFalse(report.has_critical_gap)

    def test_duplicate_skills_deduplication(self):
        """Redundant duplicate skills in student or internship lists must be deduplicated."""
        # Student lists Python 3 times with different casing and whitespace
        student_skills = ["Python", "python", "  PYTHON  ", "SQL"]
        required = ["python", "Python", "SQL"]
        preferred = ["sql", "Git"]  # SQL is already in required

        report = analyze_skill_gaps(student_skills, required, preferred)

        self.assertEqual(report.total_required_skills, 2)  # Python and SQL
        self.assertEqual(len(report.matched_required_skills), 2)
        # SQL should not appear again in preferred
        self.assertEqual(report.total_preferred_skills, 1)  # Only Git
        self.assertEqual(report.matched_preferred_skills, [])
        self.assertEqual(report.missing_preferred_skills, ["Git"])

    def test_student_skill_dataclass_objects(self):
        """Gap analyzer must support StudentSkill dataclass objects directly."""
        student_skills = [
            StudentSkill(student_id=1, skill_id=10, skill_name="Python", category="Language", proficiency_level="Advanced"),
            StudentSkill(student_id=1, skill_id=11, skill_name="PostgreSQL", category="Database", proficiency_level="Intermediate"),
        ]
        required = ["python", "postgres"]
        preferred = ["Docker"]

        report = analyze_skill_gaps(student_skills, required, preferred)

        self.assertEqual(len(report.matched_required_skills), 2)
        self.assertIn("Python", report.matched_required_skills)
        self.assertIn("PostgreSQL", report.matched_required_skills)
        self.assertEqual(report.missing_preferred_skills, ["Docker"])

    def test_format_gap_summary(self):
        """Summary text must clearly present matched counts and gaps."""
        student_skills = ["Python"]
        required = ["Python", "Docker"]
        preferred = ["Kubernetes"]

        report = analyze_skill_gaps(student_skills, required, preferred)
        summary = format_gap_summary(report)

        self.assertIn("Matched 1 of 2 required skills", summary)
        self.assertIn("Critical Gaps: [Docker]", summary)
        self.assertIn("Matched 0 of 1 preferred skills", summary)
        self.assertIn("Growth Opportunities: [Kubernetes]", summary)


if __name__ == "__main__":
    unittest.main()

"""
Automated Unit Tests for Skill Matcher & Canonical Normalization
Tests case-insensitivity, whitespace collapsing, symbol preservation,
alias dictionary resolution, display names, and unknown skills.
"""

import unittest
from app.engine.matcher import (
    normalize_skill_name,
    get_canonical_display_name,
    skills_match,
    find_matched_skill,
    SKILL_ALIASES,
)


class TestSkillMatcher(unittest.TestCase):
    """
    Unit tests for deterministic skill normalization and alias matching.
    """

    def test_case_insensitivity(self):
        """Skill matching must be strictly case-insensitive."""
        self.assertEqual(normalize_skill_name("python"), "python")
        self.assertEqual(normalize_skill_name("PYTHON"), "python")
        self.assertEqual(normalize_skill_name("PyThOn"), "python")
        self.assertTrue(skills_match("PYTHON", "python"))

    def test_whitespace_collapsing(self):
        """Leading, trailing, and redundant internal whitespace must be trimmed."""
        self.assertEqual(normalize_skill_name("  react  "), "react")
        self.assertEqual(normalize_skill_name("data   analysis"), "data analysis")
        self.assertTrue(skills_match("  flask  ", "flask"))

    def test_symbol_preservation(self):
        """Critical technology symbols (+, #, ., /) must not be stripped."""
        self.assertEqual(normalize_skill_name("C++"), "c++")
        self.assertEqual(normalize_skill_name("c++"), "c++")
        self.assertEqual(normalize_skill_name("C#"), "c#")
        self.assertEqual(normalize_skill_name("Node.js"), "node.js")
        self.assertEqual(normalize_skill_name("HTML/CSS"), "html/css")
        self.assertEqual(normalize_skill_name("CI/CD"), "ci/cd")

    def test_documented_aliases(self):
        """Curated aliases must map to canonical keys."""
        # Database aliases
        self.assertEqual(normalize_skill_name("postgres"), "postgresql")
        self.assertEqual(normalize_skill_name("pgsql"), "postgresql")
        self.assertEqual(normalize_skill_name("mongo"), "mongodb")

        # Machine Learning aliases
        self.assertEqual(normalize_skill_name("sklearn"), "scikit-learn")
        self.assertEqual(normalize_skill_name("scikit learn"), "scikit-learn")
        self.assertEqual(normalize_skill_name("torch"), "pytorch")
        self.assertEqual(normalize_skill_name("tf"), "tensorflow")

        # Framework aliases
        self.assertEqual(normalize_skill_name("reactjs"), "react")
        self.assertEqual(normalize_skill_name("react.js"), "react")
        self.assertEqual(normalize_skill_name("nodejs"), "node.js")
        self.assertEqual(normalize_skill_name("node js"), "node.js")
        self.assertEqual(normalize_skill_name("fast api"), "fastapi")

        # Cloud & DevOps aliases
        self.assertEqual(normalize_skill_name("k8s"), "kubernetes")
        self.assertEqual(normalize_skill_name("cicd"), "ci/cd")
        self.assertEqual(normalize_skill_name("github"), "git")

    def test_canonical_display_names(self):
        """Canonical display names must format skills for clean UI rendering."""
        self.assertEqual(get_canonical_display_name("postgres"), "PostgreSQL")
        self.assertEqual(get_canonical_display_name("sklearn"), "Scikit-Learn")
        self.assertEqual(get_canonical_display_name("c++"), "C++")
        self.assertEqual(get_canonical_display_name("c#"), "C#")
        self.assertEqual(get_canonical_display_name("node.js"), "Node.js")
        self.assertEqual(get_canonical_display_name("rest apis"), "REST APIs")
        self.assertEqual(get_canonical_display_name("ci/cd"), "CI/CD")

    def test_unknown_skill_handling(self):
        """Unrecognized skills must be gracefully preserved without crashing."""
        unknown = "Quantum Computing"
        self.assertEqual(normalize_skill_name(unknown), "quantum computing")
        self.assertEqual(get_canonical_display_name(unknown), "Quantum Computing")
        self.assertTrue(skills_match("Quantum Computing", "quantum computing"))
        self.assertFalse(skills_match("Quantum Computing", "Classical Computing"))

    def test_skills_match_function(self):
        """skills_match must accurately compare heterogeneous skill representations."""
        self.assertTrue(skills_match("PostgreSQL", "postgres"))
        self.assertTrue(skills_match("Scikit-Learn", "sklearn"))
        self.assertTrue(skills_match("Node.JS", "nodejs"))
        self.assertFalse(skills_match("Python", "Java"))
        self.assertFalse(skills_match("Python", None))
        self.assertFalse(skills_match(None, None))
        self.assertFalse(skills_match("", "   "))

    def test_find_matched_skill(self):
        """find_matched_skill must locate the matching candidate in an iterable."""
        candidates = ["Java", "PostgreSQL", "Docker", "Git"]
        match = find_matched_skill("postgres", candidates)
        self.assertEqual(match, "PostgreSQL")

        no_match = find_matched_skill("Rust", candidates)
        self.assertIsNone(no_match)


if __name__ == "__main__":
    unittest.main()

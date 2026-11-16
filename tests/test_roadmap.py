"""
Automated Unit Tests for Personalized Learning Roadmap Engine
Validates:
1. Knowledge base completeness for all 21 canonical skills.
2. Transitive prerequisite expansion (e.g. SQL for PostgreSQL, JS/HTML for React).
3. Priority inheritance (prerequisites inherit mandatory priority if supporting a required skill).
4. Prerequisite shared by multiple target skills (scheduled once with multiple dependent references).
5. Possessed prerequisites are strictly excluded (e.g. possessed SQL or Python).
6. Multi-level transitive prerequisite chains (A -> B -> C).
7. Dependency cycle safety (X <-> Y).
8. Strict separation from Skill-Gap Analyzer (gap report has only employer targets).
9. Interview readiness guidance for 100% matched students.
10. Graceful fallback for unknown/custom skills.
11. Deduplication of skill variations and aliases.
12. Zero-hallucination compliance (no external URLs, courses, or certificates).
13. Approximate self-paced duration disclosure.
14. Complete serialization with metadata attributes (origin, rationale, is_prerequisite, prerequisite_for).
"""

import unittest
from app.models.entities import Student, Internship, StudentSkill
from app.models.results import RoadmapStep, LearningRoadmap, SkillGapReport
from app.engine.gap_analyzer import analyze_skill_gaps
from app.engine.roadmap import (
    generate_learning_roadmap,
    generate_roadmap_for_internship,
    generate_roadmap_from_gap_report,
    get_skill_pedagogy,
    order_skills_with_prerequisites,
    expand_skill_prerequisites,
    SKILL_KNOWLEDGE_BASE,
)


class TestLearningRoadmapEngine(unittest.TestCase):
    """
    Comprehensive tests for deterministic roadmap generation, transitive prerequisite expansion,
    priority inheritance, and pedagogical sequencing.
    """

    def test_all_21_canonical_skills_in_knowledge_base(self):
        """Confirm that all 21 canonical skills exist in SKILL_KNOWLEDGE_BASE."""
        expected_canonical_keys = [
            "python", "javascript", "java", "c++", "sql", "postgresql",
            "mongodb", "react", "flask", "node.js", "html/css", "docker",
            "git", "linux", "data analysis", "machine learning", "pandas",
            "pytorch", "rest apis", "agile methodology", "technical writing",
        ]
        self.assertEqual(len(SKILL_KNOWLEDGE_BASE), 21)
        for key in expected_canonical_keys:
            self.assertIn(key, SKILL_KNOWLEDGE_BASE, f"Missing canonical key: {key}")
            data = SKILL_KNOWLEDGE_BASE[key]
            self.assertIn("canonical_name", data)
            self.assertIn("category", data)
            self.assertIn("min_weeks", data)
            self.assertIn("max_weeks", data)
            self.assertIn("prerequisites", data)
            self.assertIn("learning_focus", data)
            self.assertIn("practical_milestone", data)
            self.assertIsInstance(data["learning_focus"], list)
            self.assertTrue(len(data["learning_focus"]) >= 3)
            self.assertTrue(len(data["practical_milestone"]) > 10)

    # -------------------------------------------------------------------------
    # Core Regression Tests: Transitive Prerequisite Expansion & Priority
    # -------------------------------------------------------------------------

    def test_scenario_a_prerequisite_audit(self):
        """
        Regression Test 1: Scenario A from the prerequisite audit.
        Student possesses: Python, Git
        Required: Flask, PostgreSQL, Docker
        Preferred: React, Data Analysis

        Expected:
        - Injected prerequisites: SQL (for PostgreSQL), JavaScript and HTML/CSS (for React).
        - Python is possessed, so not scheduled for Flask.
        - Total steps: 8 (4 mandatory + 4 preferred).
        - Injected count: 3.
        - SQL precedes PostgreSQL.
        - JavaScript and HTML/CSS precede React.
        - Mandatory steps precede preferred steps.
        - Injected steps have is_prerequisite=True and descriptive rationale.
        """
        student_skills = ["Python", "Git"]
        required = ["Flask", "PostgreSQL", "Docker"]
        preferred = ["React", "Data Analysis"]

        roadmap = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
            internship_id=101,
            internship_title="Full-Stack Backend Intern",
            organization="CloudScale Innovations",
        )

        self.assertFalse(roadmap.is_fully_qualified)
        self.assertEqual(roadmap.total_steps, 8)
        self.assertEqual(roadmap.mandatory_steps_count, 4)
        self.assertEqual(roadmap.preferred_steps_count, 4)
        self.assertEqual(roadmap.injected_prerequisites_count, 3)

        step_names = [s.skill_name for s in roadmap.steps]
        self.assertEqual(
            step_names,
            ["SQL", "Flask", "PostgreSQL", "Docker", "JavaScript", "HTML/CSS", "React", "Data Analysis"]
        )

        # 1. SQL check (injected for PostgreSQL)
        sql_step = roadmap.steps[0]
        self.assertEqual(sql_step.skill_name, "SQL")
        self.assertEqual(sql_step.priority, "High (Mandatory Requirement)")
        self.assertEqual(sql_step.phase, "Phase 1: Critical Foundation")
        self.assertTrue(sql_step.is_prerequisite)
        self.assertEqual(sql_step.prerequisite_for, ["PostgreSQL"])
        self.assertEqual(sql_step.origin, "Injected Prerequisite")
        self.assertIn("Supporting prerequisite for PostgreSQL", sql_step.rationale)

        # SQL must appear before PostgreSQL
        self.assertLess(step_names.index("SQL"), step_names.index("PostgreSQL"))

        # 2. Flask check (employer target, prereq Python already possessed)
        flask_step = roadmap.steps[1]
        self.assertEqual(flask_step.skill_name, "Flask")
        self.assertEqual(flask_step.priority, "High (Mandatory Requirement)")
        self.assertFalse(flask_step.is_prerequisite)
        self.assertEqual(flask_step.origin, "Employer Requirement")

        # 3. PostgreSQL check
        pg_step = roadmap.steps[2]
        self.assertEqual(pg_step.skill_name, "PostgreSQL")
        self.assertEqual(pg_step.priority, "High (Mandatory Requirement)")
        self.assertFalse(pg_step.is_prerequisite)

        # 4. React prerequisites check (HTML/CSS & JavaScript injected as preferred)
        html_idx = step_names.index("HTML/CSS")
        js_idx = step_names.index("JavaScript")
        react_idx = step_names.index("React")

        self.assertLess(html_idx, react_idx)
        self.assertLess(js_idx, react_idx)

        js_step = roadmap.steps[js_idx]
        self.assertTrue(js_step.is_prerequisite)
        self.assertEqual(js_step.priority, "Medium (Growth Opportunity)")
        self.assertEqual(js_step.prerequisite_for, ["React"])
        self.assertEqual(js_step.origin, "Injected Prerequisite")
        self.assertIn("Supporting prerequisite for React", js_step.rationale)

    def test_student_possesses_sql_not_scheduled(self):
        """
        Regression Test 2: When student already possesses SQL, SQL must NOT be scheduled
        even though PostgreSQL requires it.
        """
        student_skills = ["Python", "Git", "SQL"]
        required = ["Flask", "PostgreSQL", "Docker"]
        preferred = ["React", "Data Analysis"]

        roadmap = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
        )

        step_names = [s.skill_name for s in roadmap.steps]
        self.assertNotIn("SQL", step_names)
        self.assertEqual(roadmap.mandatory_steps_count, 3)
        self.assertEqual(roadmap.total_steps, 7)
        self.assertEqual(roadmap.injected_prerequisites_count, 2)  # HTML/CSS and JavaScript for React

    def test_student_possesses_python_needs_flask(self):
        """
        Regression Test 3: Student possesses Python but needs Flask.
        Python must not be scheduled. Only Flask should be in the roadmap.
        """
        student_skills = ["Python"]
        required = ["Flask"]
        preferred = []

        roadmap = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
        )

        self.assertEqual(roadmap.total_steps, 1)
        self.assertEqual(roadmap.steps[0].skill_name, "Flask")
        self.assertFalse(roadmap.steps[0].is_prerequisite)
        self.assertEqual(roadmap.injected_prerequisites_count, 0)
        self.assertNotIn("Python", [s.skill_name for s in roadmap.steps])

    def test_postgresql_and_sql_both_explicitly_listed(self):
        """
        Regression Test 4: When PostgreSQL and SQL are both explicitly listed by the employer,
        SQL must appear only once, before PostgreSQL, and marked as an employer target (not injected).
        """
        student_skills = []
        required = ["PostgreSQL", "SQL"]
        preferred = []

        roadmap = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
        )

        self.assertEqual(roadmap.total_steps, 2)
        step_names = [s.skill_name for s in roadmap.steps]
        self.assertEqual(step_names, ["SQL", "PostgreSQL"])
        self.assertEqual(roadmap.injected_prerequisites_count, 0)

        sql_step = roadmap.steps[0]
        self.assertEqual(sql_step.skill_name, "SQL")
        self.assertFalse(sql_step.is_prerequisite)
        self.assertEqual(sql_step.origin, "Employer Requirement")

        pg_step = roadmap.steps[1]
        self.assertEqual(pg_step.skill_name, "PostgreSQL")
        self.assertFalse(pg_step.is_prerequisite)

    def test_shared_prerequisite_scheduled_once(self):
        """
        Regression Test 5: A prerequisite shared by multiple target skills (e.g. PyTorch and Flask
        both requiring Python) must be scheduled only once, with prerequisite_for referencing both.
        """
        student_skills = []
        required = ["PyTorch", "Flask"]
        preferred = []

        roadmap = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
        )

        step_names = [s.skill_name for s in roadmap.steps]
        self.assertEqual(step_names.count("Python"), 1)
        self.assertEqual(roadmap.total_steps, 3)

        python_step = roadmap.steps[0]
        self.assertEqual(python_step.skill_name, "Python")
        self.assertTrue(python_step.is_prerequisite)
        self.assertEqual(python_step.prerequisite_for, ["Flask", "PyTorch"])
        self.assertIn("Supporting prerequisite for Flask, PyTorch", python_step.rationale)

        # Python must appear before both Flask and PyTorch
        self.assertLess(step_names.index("Python"), step_names.index("Flask"))
        self.assertLess(step_names.index("Python"), step_names.index("PyTorch"))

    def test_transitive_prerequisite_chain(self):
        """
        Regression Test 6: Multi-level transitive prerequisite chain (A -> B -> C).
        Must order all steps topologically: C -> B -> A.
        """
        fake_kb = {
            "c language": {"canonical_name": "C Language", "category": "Core", "min_weeks": 1, "max_weeks": 2, "prerequisites": [], "learning_focus": ["C basics"], "practical_milestone": "Build C app"},
            "b framework": {"canonical_name": "B Framework", "category": "Lib", "min_weeks": 1, "max_weeks": 2, "prerequisites": ["C Language"], "learning_focus": ["B basics"], "practical_milestone": "Build B app"},
            "a application": {"canonical_name": "A Application", "category": "App", "min_weeks": 1, "max_weeks": 2, "prerequisites": ["B Framework"], "learning_focus": ["A basics"], "practical_milestone": "Build A app"},
        }

        roadmap = generate_learning_roadmap(
            student_skills=[],
            required_skills=["A Application"],
            preferred_skills=[],
            knowledge_base=fake_kb,
        )

        step_names = [s.skill_name for s in roadmap.steps]
        self.assertEqual(step_names, ["C Language", "B Framework", "A Application"])
        self.assertEqual(roadmap.total_steps, 3)
        self.assertEqual(roadmap.injected_prerequisites_count, 2)
        self.assertTrue(roadmap.steps[0].is_prerequisite)
        self.assertTrue(roadmap.steps[1].is_prerequisite)
        self.assertFalse(roadmap.steps[2].is_prerequisite)

    def test_dependency_cycle_safety(self):
        """
        Regression Test 7: A cycle in the dependency graph (X -> Y -> X) must terminate
        safely with no infinite recursion during expansion or sorting.
        """
        cycle_kb = {
            "skill x": {"canonical_name": "Skill X", "category": "Core", "min_weeks": 1, "max_weeks": 2, "prerequisites": ["Skill Y"], "learning_focus": ["X basics"], "practical_milestone": "Build X"},
            "skill y": {"canonical_name": "Skill Y", "category": "Core", "min_weeks": 1, "max_weeks": 2, "prerequisites": ["Skill X"], "learning_focus": ["Y basics"], "practical_milestone": "Build Y"},
        }

        roadmap = generate_learning_roadmap(
            student_skills=[],
            required_skills=["Skill X"],
            preferred_skills=[],
            knowledge_base=cycle_kb,
        )

        self.assertEqual(roadmap.total_steps, 2)
        step_names = [s.skill_name for s in roadmap.steps]
        self.assertIn("Skill X", step_names)
        self.assertIn("Skill Y", step_names)

    def test_prerequisite_shared_by_required_and_preferred_mandatory_wins(self):
        """
        Regression Test 8: Prerequisite shared by a required skill and a preferred skill
        (e.g. PyTorch required, Pandas preferred -> both need Python).
        Python must inherit Mandatory priority (High Priority).
        """
        student_skills = []
        required = ["PyTorch"]
        preferred = ["Pandas"]

        roadmap = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
        )

        step_names = [s.skill_name for s in roadmap.steps]
        self.assertEqual(roadmap.total_steps, 3)
        self.assertEqual(roadmap.mandatory_steps_count, 2)  # Python + PyTorch
        self.assertEqual(roadmap.preferred_steps_count, 1)  # Pandas

        python_step = roadmap.steps[0]
        self.assertEqual(python_step.skill_name, "Python")
        self.assertEqual(python_step.priority, "High (Mandatory Requirement)")
        self.assertTrue(python_step.is_prerequisite)
        self.assertEqual(python_step.prerequisite_for, ["Pandas", "PyTorch"])

    def test_preferred_skill_prerequisites_retain_preferred_priority(self):
        """
        Regression Test 9: Preferred skill prerequisites retain preferred priority
        when no mandatory dependency exists.
        """
        student_skills = []
        required = ["Docker"]
        preferred = ["React"]

        roadmap = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
        )

        self.assertEqual(roadmap.total_steps, 4)
        self.assertEqual(roadmap.mandatory_steps_count, 1)  # Docker
        self.assertEqual(roadmap.preferred_steps_count, 3)  # HTML/CSS, JavaScript, React

        # Docker is mandatory
        self.assertEqual(roadmap.steps[0].skill_name, "Docker")
        self.assertEqual(roadmap.steps[0].priority, "High (Mandatory Requirement)")

        # Injected prerequisites for React are preferred
        for step in roadmap.steps[1:]:
            self.assertEqual(step.priority, "Medium (Growth Opportunity)")
            self.assertEqual(step.phase, "Phase 3: Growth Opportunities")

    def test_skill_gap_analyzer_remains_unaffected(self):
        """
        Regression Test 10: The skill-gap analyzer must remain completely unaffected
        by roadmap prerequisite injection. It must continue reporting only the employer's
        declared required and preferred skills.
        """
        student_skills = ["Python", "Git"]
        required = ["Flask", "PostgreSQL", "Docker"]
        preferred = ["React", "Data Analysis"]

        # Run skill-gap analysis
        gap_report = analyze_skill_gaps(student_skills, required, preferred)

        # Gap report must ONLY contain the employer's declared skills
        self.assertEqual(gap_report.total_required_skills, 3)
        self.assertEqual(gap_report.total_preferred_skills, 2)
        self.assertEqual(sorted(gap_report.missing_required_skills), ["Docker", "Flask", "PostgreSQL"])
        self.assertEqual(sorted(gap_report.missing_preferred_skills), ["Data Analysis", "React"])

        # Injected roadmap skills (SQL, JavaScript, HTML/CSS) must NOT appear in gap report
        self.assertNotIn("SQL", gap_report.missing_required_skills)
        self.assertNotIn("JavaScript", gap_report.missing_preferred_skills)
        self.assertNotIn("HTML/CSS", gap_report.missing_preferred_skills)

    def test_fully_qualified_student_receives_interview_readiness_guidance(self):
        """
        Regression Test 11: Students who possess 100% of required and preferred skills
        receive interview readiness guidance rather than being assumed to have nothing to learn.
        """
        student_skills = ["Python", "Flask", "SQL", "Git"]
        required = ["Python", "Flask"]
        preferred = ["SQL", "Git"]

        roadmap = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
            internship_id=1,
            internship_title="Backend Developer Intern",
            organization="Tech Corp",
        )

        self.assertTrue(roadmap.is_fully_qualified)
        self.assertEqual(roadmap.mandatory_steps_count, 0)
        self.assertEqual(roadmap.preferred_steps_count, 0)
        self.assertEqual(roadmap.injected_prerequisites_count, 0)
        self.assertEqual(roadmap.total_steps, 1)

        step = roadmap.steps[0]
        self.assertEqual(step.step_number, 1)
        self.assertEqual(step.skill_name, "Technical Interview & Portfolio Readiness")
        self.assertEqual(step.priority, "Optional (Interview Readiness)")
        self.assertEqual(step.phase, "Preparation: Technical Interview Readiness")
        self.assertEqual(step.origin, "Interview Preparation")

    def test_unknown_custom_skill_handled_gracefully(self):
        """
        Regression Test 12: If an internship requires an unknown or custom skill (e.g. 'Quantum Computing'),
        the engine must not fail; it must use a graceful deterministic fallback with prerequisites=[].
        """
        student_skills = ["Python"]
        required = ["Quantum Computing"]
        preferred = ["Solidity"]

        roadmap = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
        )

        self.assertEqual(roadmap.total_steps, 2)
        step_names = [s.skill_name for s in roadmap.steps]
        self.assertEqual(step_names, ["Quantum Computing", "Solidity"])
        self.assertEqual(roadmap.steps[0].priority, "High (Mandatory Requirement)")
        self.assertEqual(roadmap.steps[1].priority, "Medium (Growth Opportunity)")
        self.assertEqual(roadmap.injected_prerequisites_count, 0)

        # Fallback learning focus and milestone
        self.assertTrue(len(roadmap.steps[0].learning_focus) >= 3)
        self.assertIn("proof-of-concept", roadmap.steps[0].practical_milestone.lower())

    # -------------------------------------------------------------------------
    # Structural, Serialization & Invariance Tests
    # -------------------------------------------------------------------------

    def test_duplicate_and_casing_variations_deduplicated(self):
        """Duplicate skills in requirements or mixed casing must be cleanly deduplicated."""
        student_skills = []
        required = ["python", "Python", "PYTHON 3", "py"]
        preferred = ["Python", "git", "Git", "GIT"]

        roadmap = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
        )

        self.assertEqual(roadmap.total_steps, 2)
        self.assertEqual(roadmap.mandatory_steps_count, 1)
        self.assertEqual(roadmap.preferred_steps_count, 1)
        step_names = [s.skill_name for s in roadmap.steps]
        self.assertEqual(step_names, ["Python", "Git"])

    def test_empty_skills_internship(self):
        """An internship with no listed skills should produce an interview readiness roadmap."""
        student_skills = ["Python"]
        roadmap = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=[],
            preferred_skills=[],
            internship_id=99,
            internship_title="General Intern",
            organization="Open Co",
        )

        self.assertTrue(roadmap.is_fully_qualified)
        self.assertEqual(roadmap.total_steps, 1)
        self.assertEqual(roadmap.steps[0].skill_name, "Technical Interview & Portfolio Readiness")

    def test_no_external_links_or_invented_courses(self):
        """Roadmap steps must be independent of external platforms; no invented URLs or platform names."""
        student_skills = []
        required = ["Python", "React", "Docker", "Machine Learning"]
        preferred = ["Agile Methodology", "Technical Writing"]

        roadmap = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
        )

        for step in roadmap.steps:
            self.assertNotIn("http://", step.practical_milestone.lower())
            self.assertNotIn("https://", step.practical_milestone.lower())
            self.assertNotIn("udemy.com", step.practical_milestone.lower())
            self.assertNotIn("coursera.org", step.practical_milestone.lower())
            for focus in step.learning_focus:
                self.assertNotIn("http://", focus.lower())
                self.assertNotIn("https://", focus.lower())

    def test_learning_durations_are_self_paced_estimates(self):
        """All duration representations must clearly disclose that they are approximate self-study estimates."""
        student_skills = []
        required = ["Python", "SQL"]
        preferred = ["Git"]

        roadmap = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
        )

        self.assertIn("self-paced estimate", roadmap.estimated_total_duration.lower())
        for step in roadmap.steps:
            self.assertIn("self-paced estimate", step.estimated_duration.lower())
            self.assertIn("approx.", step.estimated_duration.lower())

    def test_roadmap_serialization_to_dict(self):
        """to_dict() must produce a valid JSON-serializable dictionary with all metadata keys."""
        student_skills = ["Python"]
        required = ["PostgreSQL"]
        preferred = ["Git"]

        roadmap = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
            internship_id=5,
            internship_title="Data Analyst Intern",
            organization="DataWorks",
        )

        data = roadmap.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["internship_id"], 5)
        self.assertEqual(data["internship_title"], "Data Analyst Intern")
        self.assertEqual(data["organization"], "DataWorks")
        self.assertEqual(data["total_steps"], 3)  # SQL (injected), PostgreSQL, Git
        self.assertEqual(data["mandatory_steps_count"], 2)
        self.assertEqual(data["preferred_steps_count"], 1)
        self.assertEqual(data["injected_prerequisites_count"], 1)
        self.assertFalse(data["is_fully_qualified"])
        self.assertIn("ethical_notice", data)
        self.assertIn("Ethical Notice", data["ethical_notice"])
        self.assertEqual(len(data["steps"]), 3)

        # Inspect injected SQL step
        sql_dict = data["steps"][0]
        self.assertEqual(sql_dict["skill_name"], "SQL")
        self.assertTrue(sql_dict["is_prerequisite"])
        self.assertEqual(sql_dict["prerequisite_for"], ["PostgreSQL"])
        self.assertEqual(sql_dict["origin"], "Injected Prerequisite")
        self.assertIn("Supporting prerequisite for PostgreSQL", sql_dict["rationale"])

        # Inspect employer PostgreSQL step
        pg_dict = data["steps"][1]
        self.assertEqual(pg_dict["skill_name"], "PostgreSQL")
        self.assertFalse(pg_dict["is_prerequisite"])
        self.assertEqual(pg_dict["origin"], "Employer Requirement")

    def test_deterministic_output(self):
        """Generating a roadmap multiple times with identical inputs must produce exactly identical results."""
        student_skills = ["Python", "Git"]
        required = ["Flask", "PostgreSQL", "Docker"]
        preferred = ["React", "Data Analysis"]

        roadmap_1 = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
            internship_id=10,
        )
        roadmap_2 = generate_learning_roadmap(
            student_skills=student_skills,
            required_skills=required,
            preferred_skills=preferred,
            internship_id=10,
        )

        self.assertEqual(roadmap_1.to_dict(), roadmap_2.to_dict())

    def test_generate_roadmap_for_internship_wrapper(self):
        """Test high-level wrapper using Student and Internship entity models."""
        student = Student(
            id=1,
            name="Alice Smith",
            email="alice@example.com",
            major="Computer Science",
            cgpa=3.85,
            graduation_year=2026,
            preferred_work_mode="Remote",
            preferred_location="New York",
            skills=[
                StudentSkill(
                    student_id=1,
                    skill_id=1,
                    skill_name="Python",
                    category="Programming Language",
                    proficiency_level="Advanced",
                ),
                StudentSkill(
                    student_id=1,
                    skill_id=2,
                    skill_name="JavaScript",
                    category="Programming Language",
                    proficiency_level="Intermediate",
                ),
                StudentSkill(
                    student_id=1,
                    skill_id=3,
                    skill_name="HTML/CSS",
                    category="Framework & Library",
                    proficiency_level="Intermediate",
                ),
            ],
        )
        internship = Internship(
            id=101,
            title="Full-Stack Intern",
            organization="Innovate Labs",
            location="New York",
            work_mode="Remote",
            min_cgpa=3.0,
            eligible_majors=["Computer Science"],
            min_grad_year=2025,
            max_grad_year=2027,
            description="Software engineering internship.",
            required_skills=["Python", "React"],
            preferred_skills=["Docker"],
        )

        roadmap = generate_roadmap_for_internship(student, internship)

        self.assertEqual(roadmap.internship_id, 101)
        self.assertEqual(roadmap.internship_title, "Full-Stack Intern")
        self.assertEqual(roadmap.organization, "Innovate Labs")
        # Alice has Python, JavaScript, and HTML/CSS. React and Docker are missing.
        # Since React prerequisites (JS, HTML/CSS) are already possessed, no injected prerequisites!
        self.assertEqual(roadmap.total_steps, 2)
        self.assertEqual(roadmap.injected_prerequisites_count, 0)
        self.assertEqual(roadmap.steps[0].skill_name, "React")
        self.assertEqual(roadmap.steps[0].priority, "High (Mandatory Requirement)")
        self.assertEqual(roadmap.steps[1].skill_name, "Docker")
        self.assertEqual(roadmap.steps[1].priority, "Medium (Growth Opportunity)")

    def test_generate_roadmap_from_gap_report_wrapper(self):
        """Test wrapper that generates a roadmap directly from a pre-computed SkillGapReport."""
        gap_report = SkillGapReport(
            matched_required_skills=["Python"],
            missing_required_skills=["SQL"],
            matched_preferred_skills=[],
            missing_preferred_skills=["Git"],
            total_required_skills=2,
            total_preferred_skills=1,
        )

        roadmap = generate_roadmap_from_gap_report(
            gap_report=gap_report,
            student_skills=["Python"],
            internship_id=202,
            internship_title="Junior Analyst",
            organization="FinTech Ltd",
        )

        self.assertEqual(roadmap.internship_id, 202)
        self.assertEqual(roadmap.total_steps, 2)
        self.assertEqual(roadmap.mandatory_steps_count, 1)
        self.assertEqual(roadmap.preferred_steps_count, 1)
        self.assertEqual(roadmap.steps[0].skill_name, "SQL")
        self.assertEqual(roadmap.steps[1].skill_name, "Git")


if __name__ == "__main__":
    unittest.main()

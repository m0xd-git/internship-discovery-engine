"""
Automated Unit Tests for Recommendation Explanation and Rationale Engine
=============================================================================
Verifies:
1. Strongest scoring factor identification with single clear leader.
2. Tied strongest factors handled objectively without bias.
3. Zero-contribution factors (0.0 points) excluded from strongest factors.
4. Strict separation of eligibility disqualification reasons from recommendation scoring.
5. Semantic AI contextual alignment explanation with raw similarity, qualitative label, and disclaimer.
6. Semantic fallback explanation with reason and dynamic weight rebalancing details.
7. Ethical missing skill framing (profile omission vs personal competence).
8. Academic and location alignment explanation fidelity.
9. Defensive handling of empty or minimal profiles.
10. Arithmetic agreement between ScoreBreakdown and FactorExplanation.
11. Serialization to dict.
12. Batch explanation via explain_all_recommendations.
=============================================================================
"""

import unittest
from app.models.entities import Student, StudentSkill, Internship, InternshipSkill
from app.models.results import (
    EligibilityResult,
    SkillGapReport,
    ScoreBreakdown,
    RecommendationResult,
    FactorExplanation,
    RecommendationExplanation,
)
from app.engine.explainer import (
    explain_recommendation,
    explain_all_recommendations,
    identify_strongest_factors,
    explain_required_skills,
    explain_preferred_skills,
    explain_academic_alignment,
    explain_location_alignment,
    explain_semantic_similarity,
    _determine_impact_level,
    ETHICAL_PROFILE_NOTICE,
    SEMANTIC_DISCLAIMER_NOTICE,
)
from app.engine.scorer import score_internship


class TestRecommendationExplainer(unittest.TestCase):
    def setUp(self):
        self.student = Student(
            id=1,
            name="Alice Walker",
            email="alice@univ.edu",
            major="Computer Science",
            cgpa=3.85,
            graduation_year=2026,
            preferred_work_mode="Remote",
            preferred_location="Bangalore",
            bio_summary="Backend software engineer proficient in Python and SQL.",
            skills=[
                StudentSkill(1, 1, "Python", "Programming", "Advanced"),
                StudentSkill(1, 2, "SQL", "Database", "Intermediate"),
                StudentSkill(1, 3, "Git", "DevOps", "Intermediate"),
            ],
        )

        self.internship = Internship(
            id=101,
            title="Backend Python Developer",
            organization="Nexlify",
            location="Bangalore",
            work_mode="Remote",
            min_cgpa=3.0,
            eligible_majors=["Computer Science", "Information Technology"],
            min_grad_year=2025,
            max_grad_year=2027,
            description="Build scalable REST APIs using Python, Flask, and PostgreSQL.",
        )

    def test_strongest_factor_single_leader(self):
        """When one factor earns the most points, it must be the sole strongest factor."""
        factors = [
            FactorExplanation(
                factor_key="required_skills",
                display_name="Mandatory Required Skills",
                points_earned=30.0,
                max_points=30.0,
                weight_percentage=30.0,
                impact_level="High Positive Impact",
                summary="Matched all required skills.",
            ),
            FactorExplanation(
                factor_key="preferred_skills",
                display_name="Preferred Bonus Skills",
                points_earned=10.0,
                max_points=10.0,
                weight_percentage=10.0,
                impact_level="High Positive Impact",
                summary="Matched all preferred skills.",
            ),
            FactorExplanation(
                factor_key="academic_alignment",
                display_name="Academic Alignment",
                points_earned=15.0,
                max_points=15.0,
                weight_percentage=15.0,
                impact_level="High Positive Impact",
                summary="Direct major match.",
            ),
        ]

        strongest = identify_strongest_factors(factors)
        self.assertEqual(len(strongest), 1)
        self.assertEqual(strongest[0], "Mandatory Required Skills")
        self.assertTrue(factors[0].is_strongest_factor)
        self.assertFalse(factors[1].is_strongest_factor)
        self.assertFalse(factors[2].is_strongest_factor)

    def test_strongest_factors_tied_leaders(self):
        """When two factors tie for highest earned points, both must be marked as strongest."""
        factors = [
            FactorExplanation(
                factor_key="required_skills",
                display_name="Mandatory Required Skills",
                points_earned=20.0,
                max_points=30.0,
                weight_percentage=30.0,
                impact_level="Moderate Positive Impact",
                summary="Partial required skills match.",
            ),
            FactorExplanation(
                factor_key="location_alignment",
                display_name="Location & Work Mode Alignment",
                points_earned=20.0,
                max_points=20.0,
                weight_percentage=20.0,
                impact_level="High Positive Impact",
                summary="Remote match.",
            ),
            FactorExplanation(
                factor_key="preferred_skills",
                display_name="Preferred Bonus Skills",
                points_earned=10.0,
                max_points=10.0,
                weight_percentage=10.0,
                impact_level="High Positive Impact",
                summary="Matched preferred skills.",
            ),
        ]

        strongest = identify_strongest_factors(factors)
        self.assertEqual(len(strongest), 2)
        self.assertIn("Mandatory Required Skills", strongest)
        self.assertIn("Location & Work Mode Alignment", strongest)
        self.assertTrue(factors[0].is_strongest_factor)
        self.assertTrue(factors[1].is_strongest_factor)
        self.assertFalse(factors[2].is_strongest_factor)

    def test_zero_contribution_factors_never_strongest(self):
        """Factors earning 0.0 points must never be designated as the strongest factor."""
        factors = [
            FactorExplanation(
                factor_key="required_skills",
                display_name="Mandatory Required Skills",
                points_earned=0.0,
                max_points=30.0,
                weight_percentage=30.0,
                impact_level="Zero Contribution",
                summary="No skills matched.",
            ),
            FactorExplanation(
                factor_key="preferred_skills",
                display_name="Preferred Bonus Skills",
                points_earned=0.0,
                max_points=10.0,
                weight_percentage=10.0,
                impact_level="Zero Contribution",
                summary="No bonus skills matched.",
            ),
        ]

        strongest = identify_strongest_factors(factors)
        self.assertEqual(strongest, [])
        self.assertFalse(factors[0].is_strongest_factor)
        self.assertFalse(factors[1].is_strongest_factor)

    def test_impact_level_classification(self):
        """Verifies impact level classifications across score thresholds."""
        self.assertEqual(_determine_impact_level(0.0, 30.0, is_eligible=True), "Zero Contribution")
        self.assertEqual(_determine_impact_level(10.0, 30.0, is_eligible=False), "Disqualified")
        self.assertEqual(_determine_impact_level(25.0, 30.0, is_eligible=True), "High Positive Impact")  # 83.3% >= 75%
        self.assertEqual(_determine_impact_level(15.0, 30.0, is_eligible=True), "Moderate Positive Impact")  # 50.0% >= 40%
        self.assertEqual(_determine_impact_level(5.0, 30.0, is_eligible=True), "Low Positive Impact")  # 16.7% < 40%

    def test_ineligible_candidate_disqualification_explanation(self):
        """Disqualified candidate must have clear gatekeeper summary and strictly separated scoring."""
        ineligible_student = Student(
            id=2,
            name="Bob Disqualified",
            email="bob@univ.edu",
            major="Fine Arts",  # Ineligible major
            cgpa=2.2,           # Below 3.0 cutoff
            graduation_year=2026,
            preferred_work_mode="Remote",
            preferred_location="Bangalore",
        )

        rec = score_internship(ineligible_student, self.internship, use_semantic=False)
        self.assertFalse(rec.eligibility.is_eligible)
        self.assertEqual(rec.total_score, 0.0)

        explanation = rec.explanation
        self.assertIsNotNone(explanation)
        self.assertFalse(explanation.is_eligible)
        self.assertIn("Eligibility Gatekeeper Disqualification", explanation.headline)
        self.assertIsNotNone(explanation.eligibility_summary)
        self.assertIn("CGPA", explanation.eligibility_summary)
        self.assertIn("Major", explanation.eligibility_summary)
        self.assertEqual(explanation.strongest_factors, [])

        # All factors must be marked as Disqualified
        for key, factor in explanation.factors.items():
            self.assertEqual(factor.impact_level, "Disqualified")
            self.assertEqual(factor.points_earned, 0.0)

    def test_semantic_ai_explanation_transparency(self):
        """Active semantic scoring must disclose raw similarity, qualitative label, points, and disclaimer."""
        rec = score_internship(self.student, self.internship, use_semantic=True)
        self.assertTrue(rec.eligibility.is_eligible)

        explanation = rec.explanation
        self.assertIsNotNone(explanation)
        sem_factor = explanation.factors["semantic_similarity"]

        self.assertEqual(sem_factor.factor_key, "semantic_similarity")
        self.assertEqual(sem_factor.display_name, "Semantic AI Contextual Alignment")
        self.assertGreater(sem_factor.points_earned, 0.0)
        self.assertIn("raw_similarity", sem_factor.details)
        self.assertIn("qualitative_label", sem_factor.details)
        self.assertIn("notice", sem_factor.details)
        self.assertEqual(sem_factor.details["notice"], SEMANTIC_DISCLAIMER_NOTICE)
        self.assertIn("cosine similarity", sem_factor.summary)
        self.assertIn("Notice:", sem_factor.summary)

    def test_semantic_fallback_explanation(self):
        """When semantic fallback occurs, explanation must state fallback reason and rebalancing details."""
        # Create a mock result where semantic fallback was applied
        breakdown = ScoreBreakdown(
            required_skills={"points": 45.0, "max_points": 45.0, "weight": 0.45, "details": "Matched all"},
            preferred_skills={"points": 15.0, "max_points": 15.0, "weight": 0.15, "details": "Matched all"},
            academic_alignment={"points": 20.0, "max_points": 20.0, "weight": 0.20, "details": "Full match"},
            location_alignment={"points": 20.0, "max_points": 20.0, "weight": 0.20, "details": "Remote match"},
            semantic_similarity={
                "points": 0.0,
                "max_points": 0.0,
                "weight": 0.0,
                "raw_similarity": 0.0,
                "qualitative_label": "Not evaluated",
                "fallback_applied": True,
                "fallback_reason": "Zero embedding vector detected",
                "details": "Fallback applied",
                "notice": SEMANTIC_DISCLAIMER_NOTICE,
            },
        )
        rec = RecommendationResult(
            student_id=1,
            internship_id=101,
            internship_title="Backend Developer",
            organization="Nexlify",
            eligibility=EligibilityResult(is_eligible=True),
            total_score=100.0,
            score_breakdown=breakdown,
            skill_gaps=SkillGapReport(),
        )

        explanation = explain_recommendation(rec, self.student, self.internship)
        self.assertIsNotNone(explanation.fallback_summary)
        self.assertIn("Zero embedding vector detected", explanation.fallback_summary)
        self.assertIn("baseline heuristic", explanation.fallback_summary)

        sem_factor = explanation.factors["semantic_similarity"]
        self.assertEqual(sem_factor.impact_level, "Zero Contribution")
        self.assertTrue(sem_factor.details["fallback_applied"])
        self.assertIn("Dynamic fallback rebalanced", sem_factor.summary)

    def test_ethical_missing_skills_framing(self):
        """Missing skills must be framed as profile omissions, not deficits in personal ability."""
        # Student missing PostgreSQL and Flask
        internship_with_more_skills = Internship(
            id=102,
            title="Senior Backend Engineer",
            organization="TechCorp",
            location="Bangalore",
            work_mode="Remote",
            min_cgpa=3.0,
            eligible_majors=["Computer Science"],
            min_grad_year=2025,
            max_grad_year=2027,
            description="Requires Python, PostgreSQL, and Flask. Preferred: Docker.",
            required_skills=["Python", "PostgreSQL", "Flask"],
            preferred_skills=["Docker"],
        )
        rec = score_internship(self.student, internship_with_more_skills, use_semantic=False)
        explanation = rec.explanation
        self.assertIsNotNone(explanation)

        req_factor = explanation.factors["required_skills"]
        # Phrasing check: must say "Omitted from profile", not "unqualified" or "lacks capability"
        self.assertIn("Omitted from profile", req_factor.summary)
        self.assertNotIn("lacks capability", req_factor.summary.lower())
        self.assertNotIn("incompetent", req_factor.summary.lower())

        # Global ethical notice present
        self.assertEqual(explanation.ethical_notice, ETHICAL_PROFILE_NOTICE)

    def test_academic_and_location_explanation_accuracy(self):
        """Verifies that academic and location alignment factors report correct evidence."""
        rec = score_internship(self.student, self.internship, use_semantic=False)
        explanation = rec.explanation
        self.assertIsNotNone(explanation)

        acad_factor = explanation.factors["academic_alignment"]
        self.assertEqual(acad_factor.details["student_major"], "Computer Science")
        self.assertEqual(acad_factor.details["student_cgpa"], 3.85)
        self.assertEqual(acad_factor.details["internship_min_cgpa"], 3.0)
        self.assertIn("Computer Science", acad_factor.summary)

        loc_factor = explanation.factors["location_alignment"]
        self.assertEqual(loc_factor.details["student_preferred_location"], "Bangalore")
        self.assertEqual(loc_factor.details["student_preferred_work_mode"], "Remote")
        self.assertIn("Remote", loc_factor.summary)

    def test_empty_skills_listing_handling(self):
        """Listing with 0 required and 0 preferred skills must be handled gracefully."""
        empty_skills_internship = Internship(
            id=103,
            title="General Trainee",
            organization="OpenOrg",
            location="Bangalore",
            work_mode="Remote",
            min_cgpa=3.0,
            eligible_majors=["Computer Science"],
            min_grad_year=2025,
            max_grad_year=2027,
            description="General technical orientation.",
        )
        rec = score_internship(self.student, empty_skills_internship, use_semantic=False)
        explanation = rec.explanation
        self.assertIsNotNone(explanation)

        req_factor = explanation.factors["required_skills"]
        self.assertEqual(req_factor.impact_level, "Zero Contribution")
        self.assertIn("No mandatory required skills", req_factor.summary)

        pref_factor = explanation.factors["preferred_skills"]
        self.assertEqual(pref_factor.impact_level, "Zero Contribution")
        self.assertIn("No preferred bonus skills", pref_factor.summary)

    def test_points_arithmetic_matches_score_breakdown(self):
        """Points and max points in factor explanations must match ScoreBreakdown exactly."""
        rec = score_internship(self.student, self.internship, use_semantic=True)
        explanation = rec.explanation
        sb = rec.score_breakdown

        for key, factor in explanation.factors.items():
            sb_data = getattr(sb, key)
            self.assertAlmostEqual(factor.points_earned, float(sb_data.get("points", 0.0)), places=2)
            self.assertAlmostEqual(factor.max_points, float(sb_data.get("max_points", 0.0)), places=2)

    def test_serialization_to_dict(self):
        """Verifies serialization of RecommendationExplanation and FactorExplanation."""
        rec = score_internship(self.student, self.internship, use_semantic=False)
        rec_dict = rec.to_dict()

        self.assertIn("explanation", rec_dict)
        exp_dict = rec_dict["explanation"]
        self.assertIsNotNone(exp_dict)
        self.assertEqual(exp_dict["internship_id"], 101)
        self.assertEqual(exp_dict["is_eligible"], True)
        self.assertIn("headline", exp_dict)
        self.assertIn("factors", exp_dict)
        self.assertIn("ethical_notice", exp_dict)

        req_dict = exp_dict["factors"]["required_skills"]
        self.assertEqual(req_dict["factor_key"], "required_skills")
        self.assertIn("points_earned", req_dict)
        self.assertIn("impact_level", req_dict)
        self.assertIn("summary", req_dict)
        self.assertIn("details", req_dict)

    def test_explain_all_recommendations_batch(self):
        """explain_all_recommendations must attach explanations to every result in the batch."""
        rec1 = score_internship(self.student, self.internship, use_semantic=False)
        rec2 = score_internship(self.student, self.internship, use_semantic=False)

        # Clear existing explanations to simulate unpopulated batch
        rec1.explanation = None
        rec2.explanation = None

        batch = [rec1, rec2]
        processed = explain_all_recommendations(batch, student=self.student)

        self.assertEqual(len(processed), 2)
        for r in processed:
            self.assertIsNotNone(r.explanation)
            self.assertIsInstance(r.explanation, RecommendationExplanation)
            self.assertEqual(r.explanation.internship_id, 101)


if __name__ == "__main__":
    unittest.main()

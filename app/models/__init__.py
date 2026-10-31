"""
Data Models Package
Exposes database entity models and computed engine result dataclasses.
"""

from app.models.entities import (
    Skill,
    Student,
    StudentSkill,
    Internship,
    InternshipSkill,
)
from app.models.results import (
    EligibilityResult,
    SkillGapReport,
    ScoreBreakdown,
    RecommendationResult,
)

__all__ = [
    "Skill",
    "Student",
    "StudentSkill",
    "Internship",
    "InternshipSkill",
    "EligibilityResult",
    "SkillGapReport",
    "ScoreBreakdown",
    "RecommendationResult",
]

"""
Engine Result Models (Computed In-Memory Objects)
=============================================================================
CRITICAL ARCHITECTURAL DISTINCTION:
These dataclasses represent TRANSIENT COMPUTED RESULTS generated dynamically
by the recommendation engine at runtime.

THEY DO NOT REPRESENT DATABASE TABLES.
They are never persisted as static database rows because recommendations,
eligibility checks, and skill-gap breakdowns must always be computed freshly
from current student profiles, internship requirements, and scoring weights.
=============================================================================
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any


@dataclass
class EligibilityResult:
    """
    Computed outcome of the Rule-Based Eligibility Gatekeeper.
    Captures boolean pass/fail status and explicit, auditable reasons for any rejection.
    """
    is_eligible: bool
    rejection_reasons: List[str] = field(default_factory=list)
    checks: Dict[str, bool] = field(default_factory=dict)
    # Example checks: {"cgpa_met": True, "major_eligible": True, "work_mode_compatible": True, "grad_year_valid": True}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SkillGapReport:
    """
    Computed outcome of the Skill-Gap Analyzer.
    Categorizes competencies into matched required skills, missing required skills (critical gaps),
    matched preferred skills, and missing preferred skills (growth opportunities).
    """
    matched_required_skills: List[str] = field(default_factory=list)
    missing_required_skills: List[str] = field(default_factory=list)
    matched_preferred_skills: List[str] = field(default_factory=list)
    missing_preferred_skills: List[str] = field(default_factory=list)
    total_required_skills: int = 0
    total_preferred_skills: int = 0
    matched_skills: List[str] = field(default_factory=list)

    def __post_init__(self):
        # Synchronize matched_skills if subcategories were populated
        if (self.matched_required_skills or self.matched_preferred_skills) and not self.matched_skills:
            self.matched_skills = self.matched_required_skills + self.matched_preferred_skills
        elif self.matched_skills and not self.matched_required_skills:
            # Backward compatibility when matched_skills was provided directly
            self.matched_required_skills = list(self.matched_skills)

    @property
    def has_critical_gap(self) -> bool:
        """True if the student is missing one or more mandatory skills."""
        return len(self.missing_required_skills) > 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["has_critical_gap"] = self.has_critical_gap
        return data


@dataclass
class ScoreBreakdown:
    """
    Detailed point-by-point attribution explaining how the total recommendation score
    was mathematically derived. Ensures total transparency for students and viva defense.
    """
    required_skills: Dict[str, Any]      # {"points": 30.0, "max_points": 45.0, "details": "..."}
    preferred_skills: Dict[str, Any]     # {"points": 10.0, "max_points": 15.0, "details": "..."}
    academic_alignment: Dict[str, Any]   # {"points": 16.0, "max_points": 20.0, "details": "..."}
    location_alignment: Dict[str, Any]   # {"points": 20.0, "max_points": 20.0, "details": "..."}
    semantic_similarity: Dict[str, Any]  # {"points": 0.0, "max_points": 0.0, "details": "Deferred to M6"}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RecommendationResult:
    """
    Complete recommendation response payload for an internship.
    Bundles the internship metadata, computed eligibility status, normalized score (0-100),
    transparent score breakdown, and skill gap report.
    """
    student_id: int
    internship_id: int
    internship_title: str
    organization: str
    eligibility: EligibilityResult
    total_score: float                     # Range 0.0 to 100.0 (strictly 0.0 if ineligible)
    score_breakdown: ScoreBreakdown
    skill_gaps: SkillGapReport
    is_demo: bool = True                   # Transparently badges demonstration data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "internship_id": self.internship_id,
            "internship_title": self.internship_title,
            "organization": self.organization,
            "eligibility": self.eligibility.to_dict(),
            "total_score": round(self.total_score, 2),
            "score_breakdown": self.score_breakdown.to_dict(),
            "skill_gaps": self.skill_gaps.to_dict(),
            "is_demo": self.is_demo,
        }

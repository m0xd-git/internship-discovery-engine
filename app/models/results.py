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
from typing import List, Dict, Any, Optional


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
class FactorExplanation:
    """
    Transparent explanation for a single recommendation scoring factor.
    Captures points earned, maximum possible points, qualitative impact level,
    and factual human-readable summary.
    """
    factor_key: str                     # e.g. "required_skills", "preferred_skills", "academic_alignment", etc.
    display_name: str                   # e.g. "Mandatory Required Skills"
    points_earned: float                # Points awarded (0.0 to max_points)
    max_points: float                   # Maximum available points
    weight_percentage: float            # Configured weight as a percentage (e.g. 30.0 for 30%)
    impact_level: str                   # "High Positive Impact", "Moderate Positive Impact", "Low Positive Impact", "Zero Contribution", or "Disqualified"
    summary: str                        # Plain-language explanation grounded in evidence
    details: Dict[str, Any] = field(default_factory=dict) # Structured metadata
    is_strongest_factor: bool = False   # True if this factor contributed the most points among positive factors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RecommendationExplanation:
    """
    Comprehensive, transparent explanation payload for a recommendation result.
    Synthesizes the rationale behind the match score, identifies driving factors,
    explains semantic context, highlights skill gaps ethically, and isolates
    eligibility disqualification reasons.
    """
    internship_id: int
    internship_title: str
    organization: str
    total_score: float
    is_eligible: bool
    headline: str                       # High-level summary of the recommendation outcome
    eligibility_summary: Optional[str] = None  # Explicit reasons if disqualified; None if eligible
    fallback_summary: Optional[str] = None     # Explanation if semantic fallback occurred; None otherwise
    strongest_factors: List[str] = field(default_factory=list) # Display names of strongest driving factors
    factors: Dict[str, FactorExplanation] = field(default_factory=dict) # Factor explanations by key
    ethical_notice: str = (
        "Ethical Notice: Recommendations are evaluated strictly on declared profile information. "
        "Missing skills reflect profile omissions, not a confirmed lack of personal ability or potential."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "internship_id": self.internship_id,
            "internship_title": self.internship_title,
            "organization": self.organization,
            "total_score": round(self.total_score, 2),
            "is_eligible": self.is_eligible,
            "headline": self.headline,
            "eligibility_summary": self.eligibility_summary,
            "fallback_summary": self.fallback_summary,
            "strongest_factors": list(self.strongest_factors),
            "factors": {k: f.to_dict() for k, f in self.factors.items()},
            "ethical_notice": self.ethical_notice,
        }


@dataclass
class RecommendationResult:
    """
    Complete recommendation response payload for an internship.
    Bundles the internship metadata, computed eligibility status, normalized score (0-100),
    transparent score breakdown, skill gap report, rationale explanation, and learning roadmap.
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
    explanation: Optional[RecommendationExplanation] = None
    roadmap: Optional['LearningRoadmap'] = None

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
            "explanation": self.explanation.to_dict() if self.explanation else None,
            "roadmap": self.roadmap.to_dict() if self.roadmap else None,
        }


@dataclass
class RoadmapStep:
    """
    A single pedagogical milestone step in a personalized learning roadmap.
    Represents an actionable self-study target for a missing competency.
    """
    step_number: int
    skill_name: str
    priority: str                       # "High (Mandatory Requirement)" vs "Medium (Growth Opportunity)" vs "Optional (Interview Readiness)"
    phase: str                          # e.g. "Phase 1: Critical Foundation", "Phase 2: Core Requirements", "Phase 3: Growth Opportunities", "Preparation: Technical Interview Readiness"
    estimated_duration: str             # e.g. "Approx. 1–2 weeks (self-paced estimate)"
    learning_focus: List[str]           # Key technical concepts/topics to master
    practical_milestone: str            # A concrete, hands-on project milestone demonstrating mastery
    prerequisites: List[str] = field(default_factory=list) # Explicit prerequisites, if any
    is_prerequisite: bool = False       # True if injected as a supporting prerequisite, False if employer-listed
    prerequisite_for: List[str] = field(default_factory=list) # Canonical names of skills this prerequisite supports
    origin: str = "Employer Target"     # "Employer Target" vs "Injected Prerequisite" vs "Interview Preparation"
    rationale: str = ""                 # Human-readable explanation of why this step was included

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LearningRoadmap:
    """
    Personalized, deterministic learning roadmap generated for a student
    targeting a specific internship opportunity.
    """
    internship_id: int
    internship_title: str
    organization: str
    total_steps: int
    mandatory_steps_count: int
    preferred_steps_count: int
    estimated_total_duration: str       # e.g. "Approx. 3–5 weeks (self-paced estimate)" or "Self-paced interview preparation"
    is_fully_qualified: bool            # True if student has 0 missing skills
    steps: List[RoadmapStep] = field(default_factory=list)
    injected_prerequisites_count: int = 0  # Count of supporting prerequisites not explicitly listed by employer
    ethical_notice: str = (
        "Ethical Notice: Missing profile skills indicate absence from the student profile, "
        "not a verified lack of ability. Learning durations are approximate self-study estimates, "
        "not guaranteed completion times."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "internship_id": self.internship_id,
            "internship_title": self.internship_title,
            "organization": self.organization,
            "total_steps": self.total_steps,
            "mandatory_steps_count": self.mandatory_steps_count,
            "preferred_steps_count": self.preferred_steps_count,
            "injected_prerequisites_count": self.injected_prerequisites_count,
            "estimated_total_duration": self.estimated_total_duration,
            "is_fully_qualified": self.is_fully_qualified,
            "steps": [step.to_dict() for step in self.steps],
            "ethical_notice": self.ethical_notice,
        }

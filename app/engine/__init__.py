"""
Recommendation & Evaluation Engine Package
Exposes core business logic engines: eligibility, skill matching, semantic similarity, and scoring.
"""

from app.engine.eligibility import (
    check_eligibility,
    filter_eligible_internships,
    normalize_major,
)
from app.engine.matcher import (
    normalize_skill_name,
    get_canonical_display_name,
    skills_match,
    find_matched_skill,
    SKILL_ALIASES,
)
from app.engine.gap_analyzer import (
    analyze_skill_gaps,
    format_gap_summary,
)
from app.engine.scorer import (
    score_internship,
    generate_recommendations,
    calculate_required_skill_score,
    calculate_preferred_skill_score,
    calculate_academic_alignment_score,
    calculate_location_alignment_score,
)

__all__ = [
    "check_eligibility",
    "filter_eligible_internships",
    "normalize_major",
    "normalize_skill_name",
    "get_canonical_display_name",
    "skills_match",
    "find_matched_skill",
    "SKILL_ALIASES",
    "analyze_skill_gaps",
    "format_gap_summary",
    "score_internship",
    "generate_recommendations",
    "calculate_required_skill_score",
    "calculate_preferred_skill_score",
    "calculate_academic_alignment_score",
    "calculate_location_alignment_score",
]

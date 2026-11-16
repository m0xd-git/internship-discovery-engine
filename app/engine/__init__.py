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
from app.engine.roadmap import (
    generate_learning_roadmap,
    generate_roadmap_for_internship,
    generate_roadmap_from_gap_report,
    get_skill_pedagogy,
    order_skills_with_prerequisites,
    expand_skill_prerequisites,
    SkillPlanNode,
    SKILL_KNOWLEDGE_BASE,
)
from app.models.results import (
    RoadmapStep,
    LearningRoadmap,
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
)
from app.engine.scorer import (
    score_internship,
    generate_recommendations,
    calculate_required_skill_score,
    calculate_preferred_skill_score,
    calculate_academic_alignment_score,
    calculate_location_alignment_score,
    calculate_semantic_similarity_score,
)
from app.engine.semantic import (
    SemanticEngine,
    get_semantic_engine,
    is_semantic_available,
    get_text_embedding,
    cosine_similarity,
    text_similarity,
    build_student_semantic_text,
    build_internship_semantic_text,
    get_semantic_qualitative_label,
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
    "calculate_semantic_similarity_score",
    "SemanticEngine",
    "get_semantic_engine",
    "is_semantic_available",
    "get_text_embedding",
    "cosine_similarity",
    "text_similarity",
    "build_student_semantic_text",
    "build_internship_semantic_text",
    "get_semantic_qualitative_label",
    "generate_learning_roadmap",
    "generate_roadmap_for_internship",
    "generate_roadmap_from_gap_report",
    "get_skill_pedagogy",
    "order_skills_with_prerequisites",
    "expand_skill_prerequisites",
    "SkillPlanNode",
    "SKILL_KNOWLEDGE_BASE",
    "RoadmapStep",
    "LearningRoadmap",
    "FactorExplanation",
    "RecommendationExplanation",
    "explain_recommendation",
    "explain_all_recommendations",
    "identify_strongest_factors",
    "explain_required_skills",
    "explain_preferred_skills",
    "explain_academic_alignment",
    "explain_location_alignment",
    "explain_semantic_similarity",
]

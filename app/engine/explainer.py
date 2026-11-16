"""
Transparent Recommendation Explanation and Rationale Engine
=============================================================================
CRITICAL PEDAGOGICAL & AUDIT ROLE:
Produces deterministic, auditable, and human-understandable rationales for
recommendation scores. Every explanation is strictly derived from actual
RecommendationResult, ScoreBreakdown, EligibilityResult, and SkillGapReport data.

CORE ETHICAL & INVARIANT PRINCIPLES:
1. Strict Factual Grounding: Explanations are derived exclusively from computed
   evidence. No reasons, weights, or justifications are fabricated.
2. Ethical Profile Framing: Missing competencies are explicitly framed as profile
   omissions, not verified deficits in personal capability or potential.
3. Gatekeeper Isolation: Disqualified opportunities isolate eligibility rejection
   reasons cleanly; recommendation factors are marked as Disqualified.
4. Semantic AI Transparency: Raw cosine similarity, qualitative alignment bands,
   and point contributions are exposed alongside explicit non-probability notices.
5. Deterministic Strongest Factor Identification: Driving factors are identified
   objectively by points earned; ties are handled impartially; zero-contribution
   factors are excluded.
=============================================================================
"""

from typing import Dict, List, Optional, Any
from app.models.entities import Student, Internship
from app.models.results import (
    EligibilityResult,
    SkillGapReport,
    ScoreBreakdown,
    RecommendationResult,
    FactorExplanation,
    RecommendationExplanation,
)

ETHICAL_PROFILE_NOTICE = (
    "Ethical Notice: Recommendations are evaluated strictly on declared profile information. "
    "Missing skills reflect profile omissions, not a confirmed lack of personal ability or potential."
)

SEMANTIC_DISCLAIMER_NOTICE = (
    "Semantic AI measures contextual and vocabulary alignment between profiles using "
    "all-MiniLM-L6-v2 embeddings. It does not certify individual skill competence."
)


def _determine_impact_level(points_earned: float, max_points: float, is_eligible: bool) -> str:
    """
    Classifies a factor's qualitative impact on the recommendation score.
    Returns:
        'Disqualified' if opportunity failed eligibility gatekeeping.
        'Zero Contribution' if 0.0 points earned or available.
        'High Positive Impact' if >= 75% of max points earned.
        'Moderate Positive Impact' if >= 40% of max points earned.
        'Low Positive Impact' if > 0% but < 40% of max points earned.
    """
    if not is_eligible:
        return "Disqualified"
    if points_earned <= 0.0 or max_points <= 0.0:
        return "Zero Contribution"

    ratio = points_earned / max_points
    if ratio >= 0.75:
        return "High Positive Impact"
    elif ratio >= 0.40:
        return "Moderate Positive Impact"
    else:
        return "Low Positive Impact"


def identify_strongest_factors(factors: List[FactorExplanation]) -> List[str]:
    """
    Identifies the factor(s) contributing the highest positive points.
    
    Handles ties objectively by marking all top-scoring factors as strongest.
    Factors earning 0.0 points are strictly excluded from strongest factors.
    """
    positive_factors = [f for f in factors if f.points_earned > 0.0]
    if not positive_factors:
        return []

    max_points = max(f.points_earned for f in positive_factors)
    strongest_names: List[str] = []

    for f in factors:
        if f.points_earned > 0.0 and abs(f.points_earned - max_points) < 1e-6:
            f.is_strongest_factor = True
            strongest_names.append(f.display_name)
        else:
            f.is_strongest_factor = False

    return strongest_names


def explain_required_skills(
    breakdown_data: Dict[str, Any],
    skill_gaps: SkillGapReport,
    is_eligible: bool,
) -> FactorExplanation:
    """Generates an auditable explanation for mandatory required skills."""
    points = float(breakdown_data.get("points", 0.0))
    max_points = float(breakdown_data.get("max_points", 0.0))
    weight = float(breakdown_data.get("weight", 0.0)) * 100.0
    impact = _determine_impact_level(points, max_points, is_eligible)

    matched = list(skill_gaps.matched_required_skills)
    missing = list(skill_gaps.missing_required_skills)
    total = skill_gaps.total_required_skills

    if not is_eligible:
        summary = "Disqualified: Mandatory skill scoring bypassed due to failed eligibility gatekeeping."
    elif total == 0:
        summary = "No mandatory required skills were specified for this position (0 evaluated; 0.0 pts awarded)."
    elif len(matched) == total:
        summary = (
            f"Matched all {total} mandatory required skills ({', '.join(matched)}), "
            f"earning full points ({points:.2f}/{max_points:.2f} pts)."
        )
    elif len(matched) > 0:
        summary = (
            f"Matched {len(matched)} of {total} required skills ({', '.join(matched)}), "
            f"earning {points:.2f}/{max_points:.2f} pts. "
            f"Omitted from profile: [{', '.join(missing)}]."
        )
    else:
        summary = (
            f"Matched 0 of {total} mandatory skills (0.00/{max_points:.2f} pts). "
            f"All required skills are omitted from profile: [{', '.join(missing)}]."
        )

    details = {
        "matched_skills": matched,
        "missing_skills": missing,
        "total_skills": total,
        "match_percentage": round((len(matched) / total * 100.0), 1) if total > 0 else 0.0,
    }

    return FactorExplanation(
        factor_key="required_skills",
        display_name="Mandatory Required Skills",
        points_earned=points,
        max_points=max_points,
        weight_percentage=round(weight, 1),
        impact_level=impact,
        summary=summary,
        details=details,
    )


def explain_preferred_skills(
    breakdown_data: Dict[str, Any],
    skill_gaps: SkillGapReport,
    is_eligible: bool,
) -> FactorExplanation:
    """Generates an auditable explanation for preferred bonus skills."""
    points = float(breakdown_data.get("points", 0.0))
    max_points = float(breakdown_data.get("max_points", 0.0))
    weight = float(breakdown_data.get("weight", 0.0)) * 100.0
    impact = _determine_impact_level(points, max_points, is_eligible)

    matched = list(skill_gaps.matched_preferred_skills)
    missing = list(skill_gaps.missing_preferred_skills)
    total = skill_gaps.total_preferred_skills

    if not is_eligible:
        summary = "Disqualified: Preferred skill scoring bypassed due to failed eligibility gatekeeping."
    elif total == 0:
        summary = "No preferred bonus skills were specified for this position (0 evaluated; 0.0 pts awarded)."
    elif len(matched) == total:
        summary = (
            f"Matched all {total} preferred bonus skills ({', '.join(matched)}), "
            f"earning maximum bonus points ({points:.2f}/{max_points:.2f} pts)."
        )
    elif len(matched) > 0:
        summary = (
            f"Matched {len(matched)} of {total} preferred skills ({', '.join(matched)}), "
            f"earning {points:.2f}/{max_points:.2f} pts. "
            f"Omitted from profile: [{', '.join(missing)}]."
        )
    else:
        summary = (
            f"Matched 0 of {total} preferred skills (0.00/{max_points:.2f} pts). "
            f"Omitted from profile: [{', '.join(missing)}]."
        )

    details = {
        "matched_skills": matched,
        "missing_skills": missing,
        "total_skills": total,
        "match_percentage": round((len(matched) / total * 100.0), 1) if total > 0 else 0.0,
    }

    return FactorExplanation(
        factor_key="preferred_skills",
        display_name="Preferred Bonus Skills",
        points_earned=points,
        max_points=max_points,
        weight_percentage=round(weight, 1),
        impact_level=impact,
        summary=summary,
        details=details,
    )


def explain_academic_alignment(
    breakdown_data: Dict[str, Any],
    student: Optional[Student],
    internship: Optional[Internship],
    is_eligible: bool,
) -> FactorExplanation:
    """Generates an auditable explanation for academic alignment (major + CGPA margin)."""
    points = float(breakdown_data.get("points", 0.0))
    max_points = float(breakdown_data.get("max_points", 0.0))
    weight = float(breakdown_data.get("weight", 0.0)) * 100.0
    impact = _determine_impact_level(points, max_points, is_eligible)
    raw_details = breakdown_data.get("details", "")

    if not is_eligible:
        summary = "Disqualified: Academic scoring bypassed due to failed eligibility gatekeeping."
    elif raw_details:
        summary = f"Earned {points:.2f}/{max_points:.2f} pts for academic background. {raw_details}"
    else:
        summary = f"Academic background alignment contributed {points:.2f}/{max_points:.2f} pts."

    details = {
        "raw_details": raw_details,
        "student_major": getattr(student, "major", None),
        "student_cgpa": getattr(student, "cgpa", None),
        "internship_min_cgpa": getattr(internship, "min_cgpa", None),
        "internship_eligible_majors": getattr(internship, "eligible_majors", None),
    }

    return FactorExplanation(
        factor_key="academic_alignment",
        display_name="Academic Alignment",
        points_earned=points,
        max_points=max_points,
        weight_percentage=round(weight, 1),
        impact_level=impact,
        summary=summary,
        details=details,
    )


def explain_location_alignment(
    breakdown_data: Dict[str, Any],
    student: Optional[Student],
    internship: Optional[Internship],
    is_eligible: bool,
) -> FactorExplanation:
    """Generates an auditable explanation for location and work mode alignment."""
    points = float(breakdown_data.get("points", 0.0))
    max_points = float(breakdown_data.get("max_points", 0.0))
    weight = float(breakdown_data.get("weight", 0.0)) * 100.0
    impact = _determine_impact_level(points, max_points, is_eligible)
    raw_details = breakdown_data.get("details", "")

    if not is_eligible:
        summary = "Disqualified: Location scoring bypassed due to failed eligibility gatekeeping."
    elif raw_details:
        summary = f"Earned {points:.2f}/{max_points:.2f} pts for location and work mode. {raw_details}"
    else:
        summary = f"Location and work mode compatibility contributed {points:.2f}/{max_points:.2f} pts."

    details = {
        "raw_details": raw_details,
        "student_preferred_location": getattr(student, "preferred_location", None),
        "student_preferred_work_mode": getattr(student, "preferred_work_mode", None),
        "internship_location": getattr(internship, "location", None),
        "internship_work_mode": getattr(internship, "work_mode", None),
    }

    return FactorExplanation(
        factor_key="location_alignment",
        display_name="Location & Work Mode Alignment",
        points_earned=points,
        max_points=max_points,
        weight_percentage=round(weight, 1),
        impact_level=impact,
        summary=summary,
        details=details,
    )


def explain_semantic_similarity(
    breakdown_data: Dict[str, Any],
    is_eligible: bool,
) -> FactorExplanation:
    """
    Generates an auditable explanation for semantic AI contextual similarity.
    Discloses raw cosine similarity, qualitative label, earned points, and non-probability disclaimer.
    Explicitly explains fallback rebalancing when semantic AI was bypassed.
    """
    points = float(breakdown_data.get("points", 0.0))
    max_points = float(breakdown_data.get("max_points", 0.0))
    weight = float(breakdown_data.get("weight", 0.0)) * 100.0
    raw_sim = float(breakdown_data.get("raw_similarity", 0.0))
    qual_label = breakdown_data.get("qualitative_label", "Not evaluated")
    fallback_applied = bool(breakdown_data.get("fallback_applied", False))
    fallback_reason = breakdown_data.get("fallback_reason")
    notice = breakdown_data.get("notice", SEMANTIC_DISCLAIMER_NOTICE)

    if not is_eligible:
        impact = "Disqualified"
        summary = "Disqualified: Semantic AI encoding bypassed due to failed eligibility gatekeeping."
    elif fallback_applied:
        impact = "Zero Contribution"
        summary = (
            f"Semantic AI was bypassed due to: {fallback_reason or 'Engine unavailable'}. "
            f"Dynamic fallback rebalanced the score to baseline heuristic weights "
            f"(45% required, 15% preferred, 20% academic, 20% location)."
        )
    elif max_points <= 0.0 or qual_label == "Not evaluated":
        impact = "Zero Contribution"
        summary = "Semantic AI contextual alignment was not evaluated for this recommendation."
    else:
        impact = _determine_impact_level(points, max_points, is_eligible)
        summary = (
            f"Contextual similarity measured at {raw_sim:.4f} cosine similarity ({qual_label}), "
            f"contributing {points:.2f}/{max_points:.2f} pts to the match score. "
            f"Notice: Semantic AI measures vocabulary overlap and context, not verified skill ability."
        )

    details = {
        "raw_similarity": round(raw_sim, 4),
        "qualitative_label": qual_label,
        "fallback_applied": fallback_applied,
        "fallback_reason": fallback_reason,
        "notice": notice,
    }

    return FactorExplanation(
        factor_key="semantic_similarity",
        display_name="Semantic AI Contextual Alignment",
        points_earned=points,
        max_points=max_points,
        weight_percentage=round(weight, 1),
        impact_level=impact,
        summary=summary,
        details=details,
    )


def _generate_headline(rec: RecommendationResult, strongest_factors: List[str]) -> str:
    """Synthesizes a transparent, informative headline for the recommendation."""
    if not rec.eligibility.is_eligible:
        reasons = rec.eligibility.rejection_reasons
        reasons_text = "; ".join(reasons) if reasons else "Minimum eligibility requirements not met"
        return f"Eligibility Gatekeeper Disqualification: {reasons_text}"

    score = rec.total_score
    if score >= 80.0:
        tier = "Strong Match"
    elif score >= 60.0:
        tier = "Moderate Match"
    elif score >= 35.0:
        tier = "Partial Match"
    else:
        tier = "Low Match"

    if strongest_factors:
        return f"{tier} ({score:.1f}/100): Driven primarily by {', '.join(strongest_factors)}"
    else:
        return f"{tier} ({score:.1f}/100): General profile alignment"


def explain_recommendation(
    rec: RecommendationResult,
    student: Optional[Student] = None,
    internship: Optional[Internship] = None,
) -> RecommendationExplanation:
    """
    Constructs a comprehensive, deterministic RecommendationExplanation for a recommendation result.
    
    Grounds all statements in the actual computed scores and profiles.
    """
    is_eligible = rec.eligibility.is_eligible
    sb = rec.score_breakdown
    gaps = rec.skill_gaps

    req_data = sb.required_skills if isinstance(sb.required_skills, dict) else {}
    pref_data = sb.preferred_skills if isinstance(sb.preferred_skills, dict) else {}
    acad_data = sb.academic_alignment if isinstance(sb.academic_alignment, dict) else {}
    loc_data = sb.location_alignment if isinstance(sb.location_alignment, dict) else {}
    sem_data = sb.semantic_similarity if isinstance(sb.semantic_similarity, dict) else {}

    f_req = explain_required_skills(req_data, gaps, is_eligible)
    f_pref = explain_preferred_skills(pref_data, gaps, is_eligible)
    f_acad = explain_academic_alignment(acad_data, student, internship, is_eligible)
    f_loc = explain_location_alignment(loc_data, student, internship, is_eligible)
    f_sem = explain_semantic_similarity(sem_data, is_eligible)

    factors_dict = {
        "required_skills": f_req,
        "preferred_skills": f_pref,
        "academic_alignment": f_acad,
        "location_alignment": f_loc,
        "semantic_similarity": f_sem,
    }

    if is_eligible:
        strongest = identify_strongest_factors(list(factors_dict.values()))
        eligibility_summary = None
    else:
        strongest = []
        reasons_str = "; ".join(rec.eligibility.rejection_reasons) if rec.eligibility.rejection_reasons else "Minimum criteria not met"
        eligibility_summary = (
            f"This opportunity was excluded by the Rule-Based Eligibility Gatekeeper: {reasons_str}. "
            f"Total recommendation score is strictly 0.0."
        )

    fallback_summary: Optional[str] = None
    if sem_data.get("fallback_applied"):
        fb_reason = sem_data.get("fallback_reason", "Semantic AI engine unavailable")
        fallback_summary = (
            f"Semantic AI fallback was triggered ({fb_reason}). Scoring weights were automatically "
            f"rebalanced to baseline heuristic standards (45% required, 15% preferred, 20% academic, 20% location)."
        )

    headline = _generate_headline(rec, strongest)

    return RecommendationExplanation(
        internship_id=rec.internship_id,
        internship_title=rec.internship_title,
        organization=rec.organization,
        total_score=rec.total_score,
        is_eligible=is_eligible,
        headline=headline,
        eligibility_summary=eligibility_summary,
        fallback_summary=fallback_summary,
        strongest_factors=strongest,
        factors=factors_dict,
        ethical_notice=ETHICAL_PROFILE_NOTICE,
    )


def explain_all_recommendations(
    recommendations: List[RecommendationResult],
    student: Optional[Student] = None,
) -> List[RecommendationResult]:
    """
    Appends explanations to a batch of RecommendationResult instances.
    Returns the updated recommendation results.
    """
    for rec in recommendations:
        rec.explanation = explain_recommendation(rec, student=student)
    return recommendations

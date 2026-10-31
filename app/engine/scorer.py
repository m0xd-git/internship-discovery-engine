"""
Transparent Multi-Criteria Recommendation Scoring Engine
=============================================================================
CRITICAL ARCHITECTURAL ROLE:
Computes transparent, bounded, and deterministic recommendation match scores
(0.0 to 100.0) for eligible opportunities based on configurable heuristic weights.

NON-NEGOTIABLE CORE INVARIANTS:
1. Strict Eligibility Gatekeeping: An internship that fails eligibility
   receives a total_score of EXACTLY 0.0. High skill matches NEVER override
   failed eligibility.
2. Complete Mathematical Transparency: Every single point is accounted for
   in an auditable ScoreBreakdown object.
3. Non-Probability Notice: Match scores represent algorithmic alignment
   with listed criteria, NOT hiring probabilities.
4. No Double-Counting: Academic and logistical factors use distinct evidence.
=============================================================================
"""

from typing import Dict, List, Tuple, Optional, Any
from app.config import DEFAULT_SCORING_WEIGHTS, validate_weights
from app.models.entities import Student, Internship
from app.models.results import (
    EligibilityResult,
    SkillGapReport,
    ScoreBreakdown,
    RecommendationResult,
)
from app.engine.eligibility import check_eligibility, normalize_major
from app.engine.gap_analyzer import analyze_skill_gaps


def calculate_required_skill_score(
    gap_report: SkillGapReport,
    weight: float,
) -> Tuple[float, float, str]:
    """
    Computes points for mandatory required skills.

    Points = (Matched Required / Total Required) * (weight * 100)
    If no required skills are listed, 0.0 points awarded without division by zero.
    """
    max_points = round(weight * 100.0, 2)
    total = gap_report.total_required_skills
    matched = len(gap_report.matched_required_skills)

    if total == 0:
        return 0.0, max_points, "No mandatory skills listed by employer (0 of 0 evaluated; no points awarded)."

    ratio = matched / total
    points = round(ratio * max_points, 2)
    details = (
        f"Matched {matched} of {total} required skills ({ratio * 100:.1f}%). "
        f"Possessed: [{', '.join(gap_report.matched_required_skills) or 'None'}]."
    )
    if gap_report.missing_required_skills:
        details += f" Missing: [{', '.join(gap_report.missing_required_skills)}]."

    return points, max_points, details


def calculate_preferred_skill_score(
    gap_report: SkillGapReport,
    weight: float,
) -> Tuple[float, float, str]:
    """
    Computes points for preferred (nice-to-have) bonus skills.

    Points = (Matched Preferred / Total Preferred) * (weight * 100)
    If no preferred skills are listed, 0.0 points awarded without division by zero.
    """
    max_points = round(weight * 100.0, 2)
    total = gap_report.total_preferred_skills
    matched = len(gap_report.matched_preferred_skills)

    if total == 0:
        return 0.0, max_points, "No preferred bonus skills listed by employer (0 of 0 evaluated; no points awarded)."

    ratio = matched / total
    points = round(ratio * max_points, 2)
    details = (
        f"Matched {matched} of {total} preferred skills ({ratio * 100:.1f}%). "
        f"Possessed: [{', '.join(gap_report.matched_preferred_skills) or 'None'}]."
    )
    if gap_report.missing_preferred_skills:
        details += f" Missing: [{', '.join(gap_report.missing_preferred_skills)}]."

    return points, max_points, details


def calculate_academic_alignment_score(
    student: Student,
    internship: Internship,
    weight: float,
) -> Tuple[float, float, str]:
    """
    Computes academic alignment score based on two distinct sub-factors:
    1. Major Relevance (60% of academic weight)
    2. CGPA Margin Above Cutoff (40% of academic weight)

    Avoids double counting: Major measures discipline fit; CGPA margin measures performance.
    """
    max_points = round(weight * 100.0, 2)
    major_max = round(max_points * 0.60, 2)  # 12.0 pts at weight 0.20
    cgpa_max = round(max_points * 0.40, 2)   # 8.0 pts at weight 0.20

    # 1. Major Relevance Evaluation
    norm_student_major = normalize_major(student.major) if student.major else ""
    norm_eligible = [normalize_major(m) for m in internship.eligible_majors]

    major_points = 0.0
    major_detail = ""

    if not norm_student_major:
        major_points = 0.0
        major_detail = "Student academic major is missing (0 pts)."
    elif any(m in ("any", "all", "*") for m in norm_eligible) or not norm_eligible:
        major_points = major_max
        major_detail = f"Internship is open to all disciplines; full major credit awarded ({major_max:.1f} pts)."
    elif norm_student_major in norm_eligible or any(norm_student_major == m or m in norm_student_major or norm_student_major in m for m in norm_eligible if m):
        major_points = major_max
        major_detail = f"Major '{student.major}' matches target discipline ({major_max:.1f} pts)."
    else:
        major_points = 0.0
        major_detail = f"Major '{student.major}' is not among target disciplines (0 pts)."

    # 2. CGPA Performance Margin Evaluation
    cgpa_points = 0.0
    cgpa_detail = ""

    if student.cgpa is None or student.cgpa < 0.0:
        cgpa_points = 0.0
        cgpa_detail = "Student CGPA is missing or invalid (0 pts)."
    else:
        # Student meets baseline cutoff (verified by eligibility).
        # We award 50% baseline for meeting cutoff + up to 50% for margin exceeding cutoff.
        base_cgpa_pts = cgpa_max * 0.50
        margin_cgpa_pts = cgpa_max * 0.50

        min_c = internship.min_cgpa
        margin_headroom = 4.0 - min_c

        if margin_headroom > 0.0:
            excess = max(0.0, min(student.cgpa - min_c, margin_headroom))
            margin_ratio = excess / margin_headroom
        else:
            margin_ratio = 1.0 if student.cgpa >= min_c else 0.0

        earned_margin = margin_ratio * margin_cgpa_pts
        cgpa_points = round(base_cgpa_pts + earned_margin, 2)
        cgpa_detail = (
            f"CGPA {student.cgpa:.2f} (cutoff: {min_c:.2f}) earned {base_cgpa_pts:.1f} baseline + "
            f"{earned_margin:.1f} margin bonus ({cgpa_points:.1f} pts)."
        )

    total_pts = round(min(max_points, major_points + cgpa_points), 2)
    details = f"{major_detail} {cgpa_detail}"
    return total_pts, max_points, details


def calculate_location_alignment_score(
    student: Student,
    internship: Internship,
    weight: float,
) -> Tuple[float, float, str]:
    """
    Computes logistical and geographic alignment based on two distinct sub-factors:
    1. Work Mode Fit (50% of weight): Exact mode preference match
    2. Geographic Location Fit (50% of weight): Proximity or Remote universal accessibility

    Avoids double counting: Work mode measures scheduling/presence arrangement;
    geographic location measures physical city location.
    """
    max_points = round(weight * 100.0, 2)
    mode_max = round(max_points * 0.50, 2)  # 10.0 pts at weight 0.20
    geo_max = round(max_points * 0.50, 2)   # 10.0 pts at weight 0.20

    # 1. Work Mode Alignment
    student_mode = student.preferred_work_mode.strip().capitalize() if student.preferred_work_mode else ""
    internship_mode = internship.work_mode.strip().capitalize() if internship.work_mode else ""

    mode_points = 0.0
    mode_detail = ""

    if not student_mode:
        mode_points = 0.0
        mode_detail = "Student preferred work mode is unspecified (0 pts)."
    elif student_mode == internship_mode:
        mode_points = mode_max
        mode_detail = f"Exact work mode match: both are '{internship_mode}' ({mode_max:.1f} pts)."
    elif student_mode == "Any":
        # Candidate is flexible for all modes
        mode_points = round(mode_max * 0.80, 2)
        mode_detail = f"Flexible work mode: student accepts any arrangement ({mode_points:.1f} pts)."
    else:
        mode_points = 0.0
        mode_detail = f"Work mode mismatch: student prefers '{student_mode}', role requires '{internship_mode}' (0 pts)."

    # 2. Geographic Location Fit
    geo_points = 0.0
    geo_detail = ""

    student_loc = student.preferred_location.strip().lower() if student.preferred_location else ""
    job_loc = internship.location.strip().lower() if internship.location else ""

    if internship_mode == "Remote":
        # Universal geographic accessibility for remote opportunities
        geo_points = geo_max
        geo_detail = f"Remote opportunity: universally accessible from any location ({geo_max:.1f} pts)."
    elif not student_loc:
        geo_points = 0.0
        geo_detail = "Student location preference is unspecified (0 pts)."
    elif student_loc in ("any", "flexible", "anywhere"):
        geo_points = round(geo_max * 0.70, 2)
        geo_detail = f"Candidate is flexible to relocate ({geo_points:.1f} pts)."
    elif student_loc in job_loc or job_loc in student_loc:
        geo_points = geo_max
        geo_detail = f"Exact geographic match with '{internship.location}' ({geo_max:.1f} pts)."
    else:
        # Partial relocation distance penalty
        geo_points = round(geo_max * 0.20, 2)
        geo_detail = f"Different location: student in '{student.preferred_location}', role in '{internship.location}' ({geo_points:.1f} pts)."

    total_pts = round(min(max_points, mode_points + geo_points), 2)
    details = f"{mode_detail} {geo_detail}"
    return total_pts, max_points, details


def score_internship(
    student: Student,
    internship: Internship,
    weights: Optional[Dict[str, float]] = None,
) -> RecommendationResult:
    """
    Evaluates eligibility, analyzes skill gaps, and computes a transparent recommendation score.

    HARD GATE GUARANTEE:
    If `check_eligibility()` fails, total_score is strictly 0.0, and the breakdown
    documents the explicit rejection reasons.
    """
    active_weights = dict(weights or DEFAULT_SCORING_WEIGHTS)

    # 1. Validate weights configuration
    if any(w < 0.0 for w in active_weights.values()):
        raise ValueError("Scoring weights must be non-negative numbers.")
    if not validate_weights(active_weights):
        total_w = sum(active_weights.values())
        raise ValueError(f"Scoring weights must sum to 1.0 (currently sums to {total_w:.4f}).")

    # 2. Hard Gate: Rule-Based Eligibility Check
    eligibility = check_eligibility(student, internship)

    # 3. Exact Skill-Gap Analysis
    skill_gaps = analyze_skill_gaps(
        student_skills=student.skills,
        required_skills=internship.required_skills,
        preferred_skills=internship.preferred_skills,
    )

    w_req = active_weights.get("required_skills", 0.45)
    w_pref = active_weights.get("preferred_skills", 0.15)
    w_acad = active_weights.get("academic_alignment", 0.20)
    w_loc = active_weights.get("location_alignment", 0.20)
    w_sem = active_weights.get("semantic_similarity", 0.00)

    # If ineligible: total score is strictly 0.0
    if not eligibility.is_eligible:
        disqualify_msg = f"Disqualified by Eligibility Gatekeeper: {'; '.join(eligibility.rejection_reasons)}"
        breakdown = ScoreBreakdown(
            required_skills={"points": 0.0, "max_points": round(w_req * 100, 2), "weight": w_req, "details": disqualify_msg},
            preferred_skills={"points": 0.0, "max_points": round(w_pref * 100, 2), "weight": w_pref, "details": disqualify_msg},
            academic_alignment={"points": 0.0, "max_points": round(w_acad * 100, 2), "weight": w_acad, "details": disqualify_msg},
            location_alignment={"points": 0.0, "max_points": round(w_loc * 100, 2), "weight": w_loc, "details": disqualify_msg},
            semantic_similarity={"points": 0.0, "max_points": round(w_sem * 100, 2), "weight": w_sem, "details": "Deferred to Milestone 6."},
        )
        return RecommendationResult(
            student_id=student.id or 0,
            internship_id=internship.id or 0,
            internship_title=internship.title,
            organization=internship.organization,
            eligibility=eligibility,
            total_score=0.0,
            score_breakdown=breakdown,
            skill_gaps=skill_gaps,
            is_demo=internship.is_demo,
        )

    # 4. Compute transparent component scores for eligible candidates
    req_pts, req_max, req_desc = calculate_required_skill_score(skill_gaps, w_req)
    pref_pts, pref_max, pref_desc = calculate_preferred_skill_score(skill_gaps, w_pref)
    acad_pts, acad_max, acad_desc = calculate_academic_alignment_score(student, internship, w_acad)
    loc_pts, loc_max, loc_desc = calculate_location_alignment_score(student, internship, w_loc)
    sem_pts, sem_max, sem_desc = 0.0, round(w_sem * 100, 2), "Deferred to Milestone 6."

    total_score = round(min(100.0, max(0.0, req_pts + pref_pts + acad_pts + loc_pts + sem_pts)), 2)

    breakdown = ScoreBreakdown(
        required_skills={"points": req_pts, "max_points": req_max, "weight": w_req, "details": req_desc},
        preferred_skills={"points": pref_pts, "max_points": pref_max, "weight": w_pref, "details": pref_desc},
        academic_alignment={"points": acad_pts, "max_points": acad_max, "weight": w_acad, "details": acad_desc},
        location_alignment={"points": loc_pts, "max_points": loc_max, "weight": w_loc, "details": loc_desc},
        semantic_similarity={"points": sem_pts, "max_points": sem_max, "weight": w_sem, "details": sem_desc},
    )

    return RecommendationResult(
        student_id=student.id or 0,
        internship_id=internship.id or 0,
        internship_title=internship.title,
        organization=internship.organization,
        eligibility=eligibility,
        total_score=total_score,
        score_breakdown=breakdown,
        skill_gaps=skill_gaps,
        is_demo=internship.is_demo,
    )


def generate_recommendations(
    student: Student,
    internships: List[Internship],
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[List[RecommendationResult], List[RecommendationResult]]:
    """
    Ranks eligible internships by recommendation score while strictly segregating
    disqualified opportunities into a separate collection.

    Returns:
        Tuple:
            - eligible_recommendations: Ranked in descending order of match score.
            - ineligible_listings: Unranked opportunities with explicit exclusion reasons.
    """
    eligible_list: List[RecommendationResult] = []
    ineligible_list: List[RecommendationResult] = []

    for item in internships:
        rec = score_internship(student, item, weights)
        if rec.eligibility.is_eligible:
            eligible_list.append(rec)
        else:
            ineligible_list.append(rec)

    # Sort eligible opportunities descending by total score
    eligible_list.sort(key=lambda r: r.total_score, reverse=True)

    return eligible_list, ineligible_list

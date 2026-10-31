"""
Rule-Based Eligibility & Exclusion Gatekeeper Engine
=============================================================================
CRITICAL ARCHITECTURAL ROLE:
The Eligibility Gatekeeper acts as the deterministic first-stage filter
in the recommendation pipeline. It enforces mandatory academic and logistical
constraints before any skill matching or scoring takes place.

NON-NEGOTIABLE CORE INVARIANT:
A failed mandatory requirement CANNOT be overridden by a high skill match score.
If an internship is deemed ineligible, it is placed into an isolated exclusion
collection with explicit, human-readable reasons, and receives a score of 0.0.
=============================================================================
"""

import re
from typing import List, Tuple, Dict, Optional
from app.models.entities import Student, Internship
from app.models.results import EligibilityResult


# Curated mapping of common major abbreviations and synonyms to canonical names
MAJOR_ALIASES: Dict[str, str] = {
    "cs": "computer science",
    "cse": "computer science",
    "comp sci": "computer science",
    "computer science and engineering": "computer science",
    "it": "information technology",
    "info tech": "information technology",
    "se": "software engineering",
    "swe": "software engineering",
    "ds": "data science",
    "ai": "artificial intelligence",
    "aiml": "artificial intelligence",
    "ai/ml": "artificial intelligence",
    "ece": "electronics and communication engineering",
    "ee": "electrical engineering",
    "eee": "electrical engineering",
    "me": "mechanical engineering",
    "mech": "mechanical engineering",
    "math": "mathematics",
    "stats": "statistics",
    "stat": "statistics",
}


def normalize_major(major: Optional[str]) -> str:
    """
    Normalizes academic major names for resilient matching.
    Strips leading/trailing whitespace, converts to lowercase,
    removes extra internal spaces/punctuation, and resolves common abbreviations.

    Examples:
        'CS' -> 'computer science'
        '  Computer Science & Engineering  ' -> 'computer science'
        'Information Technology' -> 'information technology'
    """
    if not major or not isinstance(major, str):
        return ""

    cleaned = major.strip().lower()
    # Normalize common punctuation variations: replace '&' or '/' with ' and '
    cleaned = cleaned.replace("&", " and ").replace("/", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Check exact alias lookup
    if cleaned in MAJOR_ALIASES:
        return MAJOR_ALIASES[cleaned]

    # Check if a prefixed phrase matches an alias (e.g. "b.tech in cs" -> "computer science")
    cleaned_no_degrees = re.sub(
        r"^(b\.?tech|b\.?s\.?|b\.?e\.?|m\.?tech|m\.?s\.?|bachelor(?:'s)?(?:\s+of\s+science)?|master(?:'s)?(?:\s+of\s+science)?|major)\s+(?:in\s+)?",
        "",
        cleaned,
    ).strip()
    cleaned_no_degrees = re.sub(r"^(in|of)\s+", "", cleaned_no_degrees).strip()
    if cleaned_no_degrees in MAJOR_ALIASES:
        return MAJOR_ALIASES[cleaned_no_degrees]

    return cleaned_no_degrees or cleaned


def evaluate_cgpa_eligibility(
    student_cgpa: Optional[float],
    min_cgpa: float,
) -> Tuple[bool, Optional[str]]:
    """
    Evaluates student CGPA against the minimum cutoff threshold.

    Rules:
    - CGPA must be between 0.0 and 4.0.
    - If student_cgpa >= min_cgpa (evaluated to 2 decimal places): PASS.
    - An exact match (e.g. 3.00 >= 3.00) is a PASS.
    - Missing or None CGPA: FAIL.
    """
    if student_cgpa is None:
        return False, "Student CGPA is missing or unspecified."

    if not isinstance(student_cgpa, (int, float)) or student_cgpa < 0.0 or student_cgpa > 4.0:
        return False, f"Student CGPA ({student_cgpa}) is outside the valid range (0.0 - 4.0)."

    # Evaluate with standard 2 decimal place rounding to prevent IEEE 754 float precision artifacts
    if round(student_cgpa, 2) < round(min_cgpa, 2):
        return (
            False,
            f"CGPA requirement not met: student CGPA ({student_cgpa:.2f}) is below minimum required ({min_cgpa:.2f}).",
        )

    return True, None


def evaluate_major_eligibility(
    student_major: Optional[str],
    eligible_majors: List[str],
) -> Tuple[bool, Optional[str]]:
    """
    Evaluates whether student's major matches the accepted academic disciplines.

    Rules:
    - If eligible_majors contains 'Any', 'All', '*', or is empty: PASS.
    - Major names are normalized and matched against canonical forms.
    - Missing or empty student_major: FAIL.
    """
    if not student_major or not student_major.strip():
        return False, "Student academic major is missing or unspecified."

    # If the internship accepts any discipline
    if not eligible_majors:
        return True, None

    normalized_eligible = [normalize_major(m) for m in eligible_majors]
    if any(m in ("any", "all", "*") for m in normalized_eligible):
        return True, None

    normalized_student = normalize_major(student_major)

    # 1. Exact match against normalized list
    if normalized_student in normalized_eligible:
        return True, None

    # 2. Check bidirectional containment for compound names (e.g. "computer science" in "computer science and engineering")
    for accepted in normalized_eligible:
        if accepted and (normalized_student == accepted or accepted in normalized_student or normalized_student in accepted):
            return True, None

    accepted_list_str = ", ".join(f"'{m}'" for m in eligible_majors)
    return (
        False,
        f"Major requirement not met: student major '{student_major}' is not among accepted disciplines: [{accepted_list_str}].",
    )


def evaluate_grad_year_eligibility(
    student_grad_year: Optional[int],
    min_grad_year: int,
    max_grad_year: int,
) -> Tuple[bool, Optional[str]]:
    """
    Evaluates whether student's graduation year falls within the allowed range.

    Rules:
    - min_grad_year <= student_grad_year <= max_grad_year: PASS.
    - student_grad_year < min_grad_year: FAIL (graduated too early / alumni).
    - student_grad_year > max_grad_year: FAIL (graduating too late / early-year student).
    - Missing or None graduation year: FAIL.
    """
    if student_grad_year is None or not isinstance(student_grad_year, int):
        return False, "Student graduation year is missing or invalid."

    if student_grad_year < min_grad_year:
        return (
            False,
            f"Graduation year requirement not met: student graduation year ({student_grad_year}) "
            f"is earlier than minimum allowed ({min_grad_year}).",
        )

    if student_grad_year > max_grad_year:
        return (
            False,
            f"Graduation year requirement not met: student graduation year ({student_grad_year}) "
            f"is later than maximum allowed ({max_grad_year}).",
        )

    return True, None


def evaluate_work_mode_compatibility(
    student_preferred_mode: Optional[str],
    internship_mode: str,
) -> Tuple[bool, Optional[str]]:
    """
    Evaluates logistical work mode compatibility.

    Rules:
    - If student prefers 'Any': PASS (compatible with Remote, Hybrid, or Onsite).
    - If student preference matches internship mode exactly: PASS.
    - If student prefers 'Remote' and internship is 'Hybrid' or 'Onsite': FAIL.
    - If student prefers 'Onsite' and internship is 'Remote' or 'Hybrid': FAIL.
    - If student prefers 'Hybrid' and internship is 'Hybrid': PASS. (If internship is Remote or Onsite: FAIL).
    - Missing or unrecognized preference: FAIL.
    """
    valid_modes = {"Remote", "Hybrid", "Onsite"}

    if not student_preferred_mode or not isinstance(student_preferred_mode, str):
        return False, "Student preferred work mode is missing or unspecified."

    student_mode_clean = student_preferred_mode.strip().capitalize()
    if student_mode_clean not in valid_modes and student_mode_clean != "Any":
        return False, f"Student preferred work mode '{student_preferred_mode}' is not recognized (allowed: Remote, Hybrid, Onsite, Any)."

    internship_mode_clean = internship_mode.strip().capitalize()
    if internship_mode_clean not in valid_modes:
        return False, f"Internship work mode '{internship_mode}' is invalid."

    # If student is flexible for any work mode
    if student_mode_clean == "Any":
        return True, None

    # Exact match
    if student_mode_clean == internship_mode_clean:
        return True, None

    return (
        False,
        f"Work mode incompatibility: student prefers '{student_preferred_mode}' but internship requires '{internship_mode}'.",
    )


def check_eligibility(student: Student, internship: Internship) -> EligibilityResult:
    """
    Comprehensive Eligibility Gatekeeper.
    Evaluates all mandatory requirements for a student against an internship.

    CRITICAL NON-SHORT-CIRCUITING BEHAVIOR:
    Every check is evaluated independently. If a student fails on multiple
    criteria (e.g. both CGPA and Major), ALL failures are documented in
    `rejection_reasons` to provide complete, actionable feedback.

    Returns:
        EligibilityResult:
            - is_eligible: True only if ALL checks pass.
            - rejection_reasons: List of human-readable failure explanations.
            - checks: Detailed dictionary of boolean flags per criteria.
    """
    rejection_reasons: List[str] = []
    checks: Dict[str, bool] = {}

    # 1. CGPA Cutoff
    cgpa_ok, cgpa_reason = evaluate_cgpa_eligibility(student.cgpa, internship.min_cgpa)
    checks["cgpa_met"] = cgpa_ok
    if not cgpa_ok and cgpa_reason:
        rejection_reasons.append(cgpa_reason)

    # 2. Major Alignment
    major_ok, major_reason = evaluate_major_eligibility(student.major, internship.eligible_majors)
    checks["major_eligible"] = major_ok
    if not major_ok and major_reason:
        rejection_reasons.append(major_reason)

    # 3. Graduation Year Window
    grad_ok, grad_reason = evaluate_grad_year_eligibility(
        student.graduation_year,
        internship.min_grad_year,
        internship.max_grad_year,
    )
    checks["grad_year_valid"] = grad_ok
    if not grad_ok and grad_reason:
        rejection_reasons.append(grad_reason)

    # 4. Work Mode Compatibility
    mode_ok, mode_reason = evaluate_work_mode_compatibility(
        student.preferred_work_mode,
        internship.work_mode,
    )
    checks["work_mode_compatible"] = mode_ok
    if not mode_ok and mode_reason:
        rejection_reasons.append(mode_reason)

    is_eligible = len(rejection_reasons) == 0

    return EligibilityResult(
        is_eligible=is_eligible,
        rejection_reasons=rejection_reasons,
        checks=checks,
    )


def filter_eligible_internships(
    student: Student,
    internships: List[Internship],
) -> Tuple[List[Tuple[Internship, EligibilityResult]], List[Tuple[Internship, EligibilityResult]]]:
    """
    Partitions a collection of internships into eligible opportunities and
    disqualified listings, preserving explicit audit reasons for each item.

    Returns:
        Tuple:
            - eligible_items: [(Internship, EligibilityResult), ...]
            - ineligible_items: [(Internship, EligibilityResult), ...]
    """
    eligible: List[Tuple[Internship, EligibilityResult]] = []
    ineligible: List[Tuple[Internship, EligibilityResult]] = []

    for item in internships:
        result = check_eligibility(student, item)
        if result.is_eligible:
            eligible.append((item, result))
        else:
            ineligible.append((item, result))

    return eligible, ineligible

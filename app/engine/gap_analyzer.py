"""
Skill-Gap Analyzer Engine
=============================================================================
CRITICAL ARCHITECTURAL ROLE:
Compares a student's self-reported competencies against an internship's stated
requirements using exact canonical matching.

CATEGORIES OF COMPETENCY:
1. Matched Required Skills: Mandatory requirements the student possesses.
2. Missing Required Skills (Critical Gaps): Mandatory requirements the student lacks.
   (These represent high-priority learning obstacles).
3. Matched Preferred Skills: Nice-to-have bonus skills the student possesses.
4. Missing Preferred Skills (Growth Opportunities): Optional skills the student can learn.

ETHICAL AI NOTICE:
A missing skill simply means the student has not listed it on their profile;
it is not proof of inability. Recommendations must never treat missing entries
as permanent disqualifications of talent.
=============================================================================
"""

from typing import List, Union, Set, Dict, Optional
from app.models.entities import StudentSkill
from app.models.results import SkillGapReport
from app.engine.matcher import (
    normalize_skill_name,
    get_canonical_display_name,
)


def extract_skill_names(skills: List[Union[str, StudentSkill]]) -> List[str]:
    """
    Extracts raw skill string names from a heterogeneous list of strings or StudentSkill objects.
    """
    names: List[str] = []
    for item in skills:
        if isinstance(item, StudentSkill):
            names.append(item.skill_name)
        elif isinstance(item, str):
            names.append(item)
    return names


def analyze_skill_gaps(
    student_skills: List[Union[str, StudentSkill]],
    required_skills: List[str],
    preferred_skills: Optional[List[str]] = None,
) -> SkillGapReport:
    """
    Compares student competencies against internship required and preferred skills.

    Guarantees:
    - Case-insensitive, canonical alias resolution via matcher.
    - Strict deduplication (no skill appears twice in any list).
    - If a skill is erroneously listed in both required and preferred, required takes precedence.
    - Fully resilient to empty lists or None values.

    Returns:
        SkillGapReport with granular breakdown of matched and missing skills.
    """
    preferred_skills = preferred_skills or []

    # 1. Build normalized lookup dictionary of student skills:
    # {normalized_skill_name: canonical_display_name}
    raw_student_names = extract_skill_names(student_skills)
    student_skill_map: Dict[str, str] = {}
    for raw in raw_student_names:
        norm = normalize_skill_name(raw)
        if norm and norm not in student_skill_map:
            student_skill_map[norm] = get_canonical_display_name(raw)

    matched_required: List[str] = []
    missing_required: List[str] = []
    matched_preferred: List[str] = []
    missing_preferred: List[str] = []

    seen_normalized_skills: Set[str] = set()

    # 2. Evaluate Required Skills (Mandatory)
    for req in required_skills:
        norm_req = normalize_skill_name(req)
        if not norm_req:
            continue
        # Avoid duplicate evaluations within required skills
        if norm_req in seen_normalized_skills:
            continue
        seen_normalized_skills.add(norm_req)

        display_name = get_canonical_display_name(req)
        if norm_req in student_skill_map:
            matched_required.append(display_name)
        else:
            missing_required.append(display_name)

    # 3. Evaluate Preferred Skills (Nice-to-Have)
    for pref in preferred_skills:
        norm_pref = normalize_skill_name(pref)
        if not norm_pref:
            continue
        # If already covered under required skills, do not double-count in preferred
        if norm_pref in seen_normalized_skills:
            continue
        seen_normalized_skills.add(norm_pref)

        display_name = get_canonical_display_name(pref)
        if norm_pref in student_skill_map:
            matched_preferred.append(display_name)
        else:
            missing_preferred.append(display_name)

    # 4. Total counts
    total_required = len(matched_required) + len(missing_required)
    total_preferred = len(matched_preferred) + len(missing_preferred)

    return SkillGapReport(
        matched_required_skills=matched_required,
        missing_required_skills=missing_required,
        matched_preferred_skills=matched_preferred,
        missing_preferred_skills=missing_preferred,
        total_required_skills=total_required,
        total_preferred_skills=total_preferred,
    )


def format_gap_summary(report: SkillGapReport) -> str:
    """
    Generates a concise, student-friendly explanation of the skill-gap report.
    """
    parts: List[str] = []

    # Required skills summary
    if report.total_required_skills == 0:
        parts.append("No specific required skills listed.")
    else:
        req_matched = len(report.matched_required_skills)
        parts.append(f"Matched {req_matched} of {report.total_required_skills} required skills.")
        if report.missing_required_skills:
            missing_str = ", ".join(report.missing_required_skills)
            parts.append(f"Critical Gaps: [{missing_str}].")

    # Preferred skills summary
    if report.total_preferred_skills > 0:
        pref_matched = len(report.matched_preferred_skills)
        parts.append(f"Matched {pref_matched} of {report.total_preferred_skills} preferred skills.")
        if report.missing_preferred_skills:
            pref_missing_str = ", ".join(report.missing_preferred_skills)
            parts.append(f"Growth Opportunities: [{pref_missing_str}].")

    return " ".join(parts)

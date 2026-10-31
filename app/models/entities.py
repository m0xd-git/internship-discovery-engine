"""
Database Entity Models
Defines typed dataclasses corresponding directly to persistent SQLite tables.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Any, Dict
import json
import sqlite3


@dataclass
class Skill:
    """
    Represents a skill from the canonical 'skills' database table.
    """
    id: Optional[int]
    name: str
    category: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Skill":
        return cls(
            id=row["id"],
            name=row["name"],
            category=row["category"],
        )


@dataclass
class StudentSkill:
    """
    Represents an item from the 'student_skills' junction table.
    """
    student_id: int
    skill_id: int
    skill_name: str
    category: str
    proficiency_level: str  # 'Beginner', 'Intermediate', 'Advanced'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Student:
    """
    Represents a student profile from the 'students' table.
    """
    id: Optional[int]
    name: str
    email: str
    major: str
    cgpa: float
    graduation_year: int
    preferred_work_mode: str  # 'Remote', 'Hybrid', 'Onsite', 'Any'
    preferred_location: str
    bio_summary: str = ""
    skills: List[StudentSkill] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data

    @classmethod
    def from_row(cls, row: sqlite3.Row, skills: Optional[List[StudentSkill]] = None) -> "Student":
        return cls(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            major=row["major"],
            cgpa=float(row["cgpa"]),
            graduation_year=int(row["graduation_year"]),
            preferred_work_mode=row["preferred_work_mode"],
            preferred_location=row["preferred_location"],
            bio_summary=row["bio_summary"] or "",
            skills=skills or [],
        )


@dataclass
class InternshipSkill:
    """
    Represents an item from the 'internship_skills' junction table.
    """
    internship_id: int
    skill_id: int
    skill_name: str
    category: str
    is_mandatory: bool  # True = Required, False = Preferred

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Internship:
    """
    Represents an internship listing from the 'internships' table.
    """
    id: Optional[int]
    title: str
    organization: str
    location: str
    work_mode: str  # 'Remote', 'Hybrid', 'Onsite'
    min_cgpa: float
    eligible_majors: List[str]
    min_grad_year: int
    max_grad_year: int
    description: str
    department: str = ""
    stipend: str = "Unpaid"
    application_deadline: Optional[str] = None
    is_demo: bool = True  # Explicit demonstration flag
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(
        cls,
        row: sqlite3.Row,
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
    ) -> "Internship":
        # Parse eligible majors from stored JSON string
        raw_majors = row["eligible_majors_json"]
        if isinstance(raw_majors, str):
            try:
                eligible_majors = json.loads(raw_majors)
            except json.JSONDecodeError:
                eligible_majors = [m.strip() for m in raw_majors.split(",") if m.strip()]
        else:
            eligible_majors = raw_majors or []

        return cls(
            id=row["id"],
            title=row["title"],
            organization=row["organization"],
            department=row["department"] or "",
            location=row["location"],
            work_mode=row["work_mode"],
            min_cgpa=float(row["min_cgpa"]),
            eligible_majors=eligible_majors,
            min_grad_year=int(row["min_grad_year"]),
            max_grad_year=int(row["max_grad_year"]),
            description=row["description"],
            stipend=row["stipend"] or "Unpaid",
            application_deadline=row["application_deadline"],
            is_demo=bool(row["is_demo"]),
            required_skills=required_skills or [],
            preferred_skills=preferred_skills or [],
        )

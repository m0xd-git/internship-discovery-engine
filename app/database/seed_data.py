"""
Demonstration Dataset Seeder
Populates the database with realistic, clearly labelled demonstration data.

ACADEMIC INTEGRITY NOTE:
All internship records are explicitly marked with `is_demo = 1`.
These listings are realistic pedagogical demonstration examples and must never
be misrepresented as active commercial job opportunities.
"""

import json
import sqlite3
from typing import Dict, List, Tuple


# Canonical skill vocabulary across categories
DEMO_SKILLS: List[Tuple[str, str]] = [
    # (name, category)
    ("Python", "Programming Language"),
    ("JavaScript", "Programming Language"),
    ("Java", "Programming Language"),
    ("C++", "Programming Language"),
    ("SQL", "Database & Storage"),
    ("PostgreSQL", "Database & Storage"),
    ("MongoDB", "Database & Storage"),
    ("React", "Framework & Library"),
    ("Flask", "Framework & Library"),
    ("Node.js", "Framework & Library"),
    ("HTML/CSS", "Framework & Library"),
    ("Docker", "Cloud & DevOps"),
    ("Git", "Methodology & Tools"),
    ("Linux", "Cloud & DevOps"),
    ("Data Analysis", "Data Science & AI"),
    ("Machine Learning", "Data Science & AI"),
    ("Pandas", "Data Science & AI"),
    ("PyTorch", "Data Science & AI"),
    ("REST APIs", "Framework & Library"),
    ("Agile Methodology", "Methodology & Tools"),
    ("Technical Writing", "Soft Skills"),
]


# Curated demonstration internships with varied eligibility thresholds and skills
DEMO_INTERNSHIPS: List[Dict] = [
    {
        "title": "Backend Software Engineering Intern",
        "organization": "OpenTech Innovations",
        "department": "Platform Core",
        "location": "Bengaluru, India",
        "work_mode": "Remote",
        "min_cgpa": 3.0,
        "eligible_majors": ["Computer Science", "Information Technology", "Software Engineering"],
        "min_grad_year": 2025,
        "max_grad_year": 2027,
        "description": "Design and build scalable RESTful backend services using Python and Flask. Collaborate with senior architects on relational database schema design, automated testing, and CI/CD pipelines.",
        "stipend": "₹25,000 / month",
        "application_deadline": "2026-12-15",
        "is_demo": 1,
        "required_skills": ["Python", "SQL", "Git"],
        "preferred_skills": ["Flask", "Docker", "REST APIs"],
    },
    {
        "title": "Junior Data Science & Analytics Intern",
        "organization": "Civic Health Analytics Lab",
        "department": "Public Health Informatics",
        "location": "New Delhi, India",
        "work_mode": "Hybrid",
        "min_cgpa": 3.2,
        "eligible_majors": ["Computer Science", "Data Science", "Mathematics", "Statistics"],
        "min_grad_year": 2025,
        "max_grad_year": 2027,
        "description": "Perform exploratory data analysis on municipal public health datasets. Clean messy data with Pandas, extract insights, and present statistical findings to medical researchers.",
        "stipend": "₹22,000 / month",
        "application_deadline": "2026-11-30",
        "is_demo": 1,
        "required_skills": ["Python", "SQL", "Data Analysis"],
        "preferred_skills": ["Pandas", "Machine Learning"],
    },
    {
        "title": "Machine Learning Research Intern",
        "organization": "National Autonomous Intelligence Institute",
        "department": "Applied Deep Learning Group",
        "location": "Hyderabad, India",
        "work_mode": "Remote",
        "min_cgpa": 3.5,
        "eligible_majors": ["Computer Science", "Data Science", "Artificial Intelligence"],
        "min_grad_year": 2025,
        "max_grad_year": 2026,
        "description": "Assist in researching and fine-tuning transformer architectures for natural language understanding. Evaluate embeddings, run benchmarks on GPU clusters, and reproduce recent research papers.",
        "stipend": "₹35,000 / month",
        "application_deadline": "2026-12-01",
        "is_demo": 1,
        "required_skills": ["Python", "Machine Learning", "PyTorch"],
        "preferred_skills": ["Git", "Linux", "Docker"],
    },
    {
        "title": "Frontend Web Development Intern",
        "organization": "Digital Public Infrastructure Foundation",
        "department": "Citizen Portals",
        "location": "Bengaluru, India",
        "work_mode": "Onsite",
        "min_cgpa": 2.5,
        "eligible_majors": ["Computer Science", "Information Technology", "Any"],
        "min_grad_year": 2024,
        "max_grad_year": 2028,
        "description": "Create responsive, accessible citizen-facing web interfaces. Build clean modular components using modern JavaScript, HTML5, and CSS. Work with UX designers on accessibility standards.",
        "stipend": "₹18,000 / month",
        "application_deadline": "2026-12-31",
        "is_demo": 1,
        "required_skills": ["JavaScript", "HTML/CSS"],
        "preferred_skills": ["React", "Git", "REST APIs"],
    },
    {
        "title": "Cloud Infrastructure & DevOps Intern",
        "organization": "Nimbus Cloud Infrastructure",
        "department": "Systems Reliability",
        "location": "Pune, India",
        "work_mode": "Hybrid",
        "min_cgpa": 3.0,
        "eligible_majors": ["Computer Science", "Information Technology", "Electronics"],
        "min_grad_year": 2025,
        "max_grad_year": 2027,
        "description": "Containerize microservices using Docker and assist in managing Linux server environments. Automate system checks, monitor server logs, and configure basic continuous deployment scripts.",
        "stipend": "₹20,000 / month",
        "application_deadline": "2026-11-15",
        "is_demo": 1,
        "required_skills": ["Linux", "Docker", "Git"],
        "preferred_skills": ["Python", "Agile Methodology"],
    },
    {
        "title": "Open Source Tech & Public Policy Intern",
        "organization": "Global Urban Informatics Initiative",
        "department": "Policy Research",
        "location": "Mumbai, India",
        "work_mode": "Remote",
        "min_cgpa": 2.8,
        "eligible_majors": ["Computer Science", "Public Policy", "Economics", "Any"],
        "min_grad_year": 2024,
        "max_grad_year": 2028,
        "description": "Investigate public digital infrastructure policies. Analyze municipal open data releases, synthesize technical reports, and write summaries comparing international digital governance frameworks.",
        "stipend": "₹15,000 / month",
        "application_deadline": "2027-01-10",
        "is_demo": 1,
        "required_skills": ["Data Analysis", "Technical Writing"],
        "preferred_skills": ["Python", "SQL"],
    },
]


# Representative student profiles for demonstration and testing
DEMO_STUDENTS: List[Dict] = [
    {
        "name": "Aarav Sharma",
        "email": "aarav.sharma@example.edu",
        "major": "Computer Science",
        "cgpa": 3.6,
        "graduation_year": 2026,
        "preferred_work_mode": "Remote",
        "preferred_location": "Bengaluru, India",
        "bio_summary": "Computer science undergraduate passionate about backend systems, database performance, and open-source software engineering.",
        "skills": [
            ("Python", "Advanced"),
            ("SQL", "Intermediate"),
            ("Git", "Intermediate"),
            ("Flask", "Beginner"),
        ],
    },
    {
        "name": "Priya Patel",
        "email": "priya.patel@example.edu",
        "major": "Information Technology",
        "cgpa": 3.1,
        "graduation_year": 2025,
        "preferred_work_mode": "Hybrid",
        "preferred_location": "Pune, India",
        "bio_summary": "Front-end enthusiast building clean, accessible web applications with modern JavaScript frameworks and responsive design.",
        "skills": [
            ("JavaScript", "Intermediate"),
            ("HTML/CSS", "Advanced"),
            ("React", "Intermediate"),
            ("Git", "Beginner"),
        ],
    },
    {
        "name": "Rohan Verma",
        "email": "rohan.verma@example.edu",
        "major": "Mechanical Engineering",
        "cgpa": 2.9,
        "graduation_year": 2027,
        "preferred_work_mode": "Onsite",
        "preferred_location": "New Delhi, India",
        "bio_summary": "Engineering student exploring computational modeling, basic scripting, and data-driven analysis for physical systems.",
        "skills": [
            ("Python", "Beginner"),
            ("Data Analysis", "Beginner"),
        ],
    },
]


def seed_skills(conn: sqlite3.Connection) -> Dict[str, int]:
    """
    Inserts canonical skills into the database and returns a mapping of skill name to skill id.
    """
    skill_map: Dict[str, int] = {}
    for name, category in DEMO_SKILLS:
        conn.execute(
            """
            INSERT INTO skills (name, category)
            VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET category=excluded.category;
            """,
            (name, category),
        )
    
    cur = conn.execute("SELECT id, name FROM skills;")
    for row in cur.fetchall():
        skill_map[row["name"].lower()] = row["id"]
    return skill_map


def seed_internships(conn: sqlite3.Connection, skill_map: Dict[str, int]) -> None:
    """
    Inserts or updates demonstration internships and maps their required and preferred skills.
    Ensures idempotency when running setup or seed repeatedly.
    """
    for item in DEMO_INTERNSHIPS:
        majors_json = json.dumps(item["eligible_majors"])
        existing = conn.execute(
            "SELECT id FROM internships WHERE title = ? AND organization = ?;",
            (item["title"], item["organization"]),
        ).fetchone()

        if existing:
            internship_id = existing["id"]
            conn.execute(
                """
                UPDATE internships SET
                    department = ?, location = ?, work_mode = ?, min_cgpa = ?,
                    eligible_majors_json = ?, min_grad_year = ?, max_grad_year = ?,
                    description = ?, stipend = ?, application_deadline = ?, is_demo = ?
                WHERE id = ?;
                """,
                (
                    item["department"],
                    item["location"],
                    item["work_mode"],
                    item["min_cgpa"],
                    majors_json,
                    item["min_grad_year"],
                    item["max_grad_year"],
                    item["description"],
                    item["stipend"],
                    item["application_deadline"],
                    item["is_demo"],
                    internship_id,
                ),
            )
            # Clear old skill associations for this internship before re-inserting
            conn.execute("DELETE FROM internship_skills WHERE internship_id = ?;", (internship_id,))
        else:
            cur = conn.execute(
                """
                INSERT INTO internships (
                    title, organization, department, location, work_mode,
                    min_cgpa, eligible_majors_json, min_grad_year, max_grad_year,
                    description, stipend, application_deadline, is_demo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    item["title"],
                    item["organization"],
                    item["department"],
                    item["location"],
                    item["work_mode"],
                    item["min_cgpa"],
                    majors_json,
                    item["min_grad_year"],
                    item["max_grad_year"],
                    item["description"],
                    item["stipend"],
                    item["application_deadline"],
                    item["is_demo"],
                ),
            )
            internship_id = cur.lastrowid

        # Insert required skills (is_mandatory = 1)
        for req_skill in item["required_skills"]:
            skill_id = skill_map.get(req_skill.lower())
            if skill_id:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO internship_skills (internship_id, skill_id, is_mandatory)
                    VALUES (?, ?, 1);
                    """,
                    (internship_id, skill_id),
                )

        # Insert preferred skills (is_mandatory = 0)
        for pref_skill in item["preferred_skills"]:
            skill_id = skill_map.get(pref_skill.lower())
            if skill_id:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO internship_skills (internship_id, skill_id, is_mandatory)
                    VALUES (?, ?, 0);
                    """,
                    (internship_id, skill_id),
                )


def seed_students(conn: sqlite3.Connection, skill_map: Dict[str, int]) -> None:
    """
    Inserts representative student profiles and maps their self-reported skills.
    """
    for student in DEMO_STUDENTS:
        cur = conn.execute(
            """
            INSERT INTO students (
                name, email, major, cgpa, graduation_year,
                preferred_work_mode, preferred_location, bio_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                name=excluded.name,
                major=excluded.major,
                cgpa=excluded.cgpa,
                graduation_year=excluded.graduation_year,
                preferred_work_mode=excluded.preferred_work_mode,
                preferred_location=excluded.preferred_location,
                bio_summary=excluded.bio_summary;
            """,
            (
                student["name"],
                student["email"],
                student["major"],
                student["cgpa"],
                student["graduation_year"],
                student["preferred_work_mode"],
                student["preferred_location"],
                student["bio_summary"],
            ),
        )
        
        # Look up student id by email
        lookup = conn.execute("SELECT id FROM students WHERE email = ?;", (student["email"],)).fetchone()
        student_id = lookup["id"]

        for skill_name, proficiency in student["skills"]:
            skill_id = skill_map.get(skill_name.lower())
            if skill_id:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO student_skills (student_id, skill_id, proficiency_level)
                    VALUES (?, ?, ?);
                    """,
                    (student_id, skill_id, proficiency),
                )


def seed_database(conn: sqlite3.Connection) -> None:
    """
    Orchestrates full seeding process in a single transaction.
    """
    with conn:
        skill_map = seed_skills(conn)
        seed_internships(conn, skill_map)
        seed_students(conn, skill_map)

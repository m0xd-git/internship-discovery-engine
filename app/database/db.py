"""
Database Connection and Initialization Management
Provides clean SQLite connection handling, foreign key enforcement, and transaction context managers.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Generator, List, Dict, Any
from contextlib import contextmanager

from app.config import DB_PATH, SCHEMA_PATH
from app.models.entities import Student, StudentSkill, Internship


def get_db_connection(db_path: Optional[Path | str] = None) -> sqlite3.Connection:
    """
    Creates and configures a SQLite connection.
    Enforces foreign key constraints and enables dictionary-like row access.
    """
    target_path = db_path if db_path is not None else DB_PATH

    # If it is a file path, ensure the target directory exists
    if isinstance(target_path, Path) and str(target_path) != ":memory:":
        target_path.parent.mkdir(parents=True, exist_ok=True)
    elif isinstance(target_path, str) and target_path != ":memory:":
        Path(target_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(target_path))
    # CRITICAL: SQLite disables foreign key enforcement by default. We must enable it per connection.
    conn.execute("PRAGMA foreign_keys = ON;")
    # row_factory enables accessing columns by name: row['title']
    conn.row_factory = sqlite3.Row
    return conn


def init_db(
    db_path: Optional[Path | str] = None,
    schema_path: Optional[Path | str] = None,
) -> sqlite3.Connection:
    """
    Initializes database tables by executing schema.sql DDL script.
    """
    conn = get_db_connection(db_path)
    target_schema = schema_path if schema_path is not None else SCHEMA_PATH

    with open(target_schema, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with conn:
        conn.executescript(schema_sql)

    return conn


@contextmanager
def db_session(
    db_path: Optional[Path | str] = None,
) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database transactions.
    Automatically commits on normal completion or rolls back on exception, then closes.
    """
    conn = get_db_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_all_internships(conn: sqlite3.Connection) -> List[Internship]:
    """
    Retrieves all internships with their required and preferred skills using parameterized queries.
    """
    cur = conn.execute("SELECT * FROM internships ORDER BY id;")
    rows = cur.fetchall()
    internships: List[Internship] = []

    for row in rows:
        internship_id = row["id"]
        # Query associated skills
        skill_cur = conn.execute(
            """
            SELECT s.name, ik.is_mandatory
            FROM internship_skills ik
            JOIN skills s ON ik.skill_id = s.id
            WHERE ik.internship_id = ?
            ORDER BY s.name;
            """,
            (internship_id,),
        )
        required_skills: List[str] = []
        preferred_skills: List[str] = []
        for s_row in skill_cur.fetchall():
            if s_row["is_mandatory"] == 1:
                required_skills.append(s_row["name"])
            else:
                preferred_skills.append(s_row["name"])

        internships.append(Internship.from_row(row, required_skills, preferred_skills))

    return internships


def get_internship_by_id(conn: sqlite3.Connection, internship_id: int) -> Optional[Internship]:
    """
    Retrieves a single internship by its primary key ID.
    """
    cur = conn.execute("SELECT * FROM internships WHERE id = ?;", (internship_id,))
    row = cur.fetchone()
    if not row:
        return None

    skill_cur = conn.execute(
        """
        SELECT s.name, ik.is_mandatory
        FROM internship_skills ik
        JOIN skills s ON ik.skill_id = s.id
        WHERE ik.internship_id = ?
        ORDER BY s.name;
        """,
        (internship_id,),
    )
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    for s_row in skill_cur.fetchall():
        if s_row["is_mandatory"] == 1:
            required_skills.append(s_row["name"])
        else:
            preferred_skills.append(s_row["name"])

    return Internship.from_row(row, required_skills, preferred_skills)


def get_all_students(conn: sqlite3.Connection) -> List[Student]:
    """
    Retrieves all student profiles with their associated skills.
    """
    cur = conn.execute("SELECT * FROM students ORDER BY id;")
    rows = cur.fetchall()
    students: List[Student] = []

    for row in rows:
        student_id = row["id"]
        skill_cur = conn.execute(
            """
            SELECT ss.student_id, ss.skill_id, s.name as skill_name, s.category, ss.proficiency_level
            FROM student_skills ss
            JOIN skills s ON ss.skill_id = s.id
            WHERE ss.student_id = ?
            ORDER BY s.name;
            """,
            (student_id,),
        )
        student_skills = [
            StudentSkill(
                student_id=s_row["student_id"],
                skill_id=s_row["skill_id"],
                skill_name=s_row["skill_name"],
                category=s_row["category"],
                proficiency_level=s_row["proficiency_level"],
            )
            for s_row in skill_cur.fetchall()
        ]
        students.append(Student.from_row(row, student_skills))

    return students


def get_student_by_id(conn: sqlite3.Connection, student_id: int) -> Optional[Student]:
    """
    Retrieves a single student profile by ID.
    """
    cur = conn.execute("SELECT * FROM students WHERE id = ?;", (student_id,))
    row = cur.fetchone()
    if not row:
        return None

    skill_cur = conn.execute(
        """
        SELECT ss.student_id, ss.skill_id, s.name as skill_name, s.category, ss.proficiency_level
        FROM student_skills ss
        JOIN skills s ON ss.skill_id = s.id
        WHERE ss.student_id = ?
        ORDER BY s.name;
        """,
        (student_id,),
    )
    student_skills = [
        StudentSkill(
            student_id=s_row["student_id"],
            skill_id=s_row["skill_id"],
            skill_name=s_row["skill_name"],
            category=s_row["category"],
            proficiency_level=s_row["proficiency_level"],
        )
        for s_row in skill_cur.fetchall()
    ]
    return Student.from_row(row, student_skills)


def save_student(conn: sqlite3.Connection, student_data: Dict[str, Any]) -> Student:
    """
    Inserts or updates a student profile and their associated skills within a transaction.
    Uses strictly parameterized queries and commits changes to persistent SQLite storage.
    """
    email = student_data["email"].strip().lower()
    name = student_data["name"].strip()
    major = student_data["major"].strip()
    cgpa = float(student_data["cgpa"])
    grad_year = int(student_data["graduation_year"])
    work_mode = student_data["preferred_work_mode"].strip().capitalize()
    location = student_data["preferred_location"].strip()
    bio = (student_data.get("bio_summary") or "").strip()

    raw_id = student_data.get("id")
    student_id = None

    if raw_id is not None and str(raw_id).strip() != "":
        try:
            student_id = int(raw_id)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid student ID: '{raw_id}'. Must be an integer.")

    with conn:
        if student_id is not None:
            # Check if this student exists by primary key
            existing = conn.execute("SELECT id, email FROM students WHERE id = ?;", (student_id,)).fetchone()
            if not existing:
                raise KeyError(f"Student with ID {student_id} was not found.")

            # Check if another student is already using this email
            duplicate_email = conn.execute(
                "SELECT id FROM students WHERE email = ? AND id != ?;",
                (email, student_id),
            ).fetchone()
            if duplicate_email:
                raise ValueError(
                    f"Email '{email}' is already registered to another student profile (ID: {duplicate_email['id']})."
                )

            conn.execute(
                """
                UPDATE students SET
                    name = ?, email = ?, major = ?, cgpa = ?, graduation_year = ?,
                    preferred_work_mode = ?, preferred_location = ?, bio_summary = ?
                WHERE id = ?;
                """,
                (name, email, major, cgpa, grad_year, work_mode, location, bio, student_id),
            )
        else:
            # Creating a new student profile: check email uniqueness
            existing_email = conn.execute("SELECT id FROM students WHERE email = ?;", (email,)).fetchone()
            if existing_email:
                raise ValueError(
                    f"Email '{email}' is already registered to an existing student profile. Please use a unique email address."
                )

            cur = conn.execute(
                """
                INSERT INTO students (name, email, major, cgpa, graduation_year, preferred_work_mode, preferred_location, bio_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (name, email, major, cgpa, grad_year, work_mode, location, bio),
            )
            student_id = cur.lastrowid

        # Handle skills synchronization if provided
        raw_skills = student_data.get("skills", [])
        if raw_skills is not None:
            # Clear existing skill mappings for clean synchronization
            conn.execute("DELETE FROM student_skills WHERE student_id = ?;", (student_id,))

            for item in raw_skills:
                if isinstance(item, dict):
                    skill_name = item.get("name", "").strip()
                    proficiency = item.get("proficiency", "Intermediate").strip().capitalize()
                elif isinstance(item, str):
                    skill_name = item.strip()
                    proficiency = "Intermediate"
                else:
                    continue

                if not skill_name:
                    continue

                if proficiency not in ("Beginner", "Intermediate", "Advanced"):
                    proficiency = "Intermediate"

                # Check if skill exists in canonical skills table, otherwise insert it
                s_lookup = conn.execute("SELECT id FROM skills WHERE name = ? COLLATE NOCASE;", (skill_name,)).fetchone()
                if s_lookup:
                    skill_id = s_lookup["id"]
                else:
                    cur_s = conn.execute(
                        "INSERT INTO skills (name, category) VALUES (?, 'Methodology & Tools');",
                        (skill_name,),
                    )
                    skill_id = cur_s.lastrowid

                conn.execute(
                    """
                    INSERT OR REPLACE INTO student_skills (student_id, skill_id, proficiency_level)
                    VALUES (?, ?, ?);
                    """,
                    (student_id, skill_id, proficiency),
                )

        conn.commit()

    return get_student_by_id(conn, student_id)

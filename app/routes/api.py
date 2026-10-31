"""
REST API Blueprint
=============================================================================
Provides clean, defensively validated REST endpoints for:
1. Listing internships with demonstration badges (/api/internships)
2. Managing student profiles (/api/students)
3. Running recommendations with transparent score breakdowns (/api/recommend)

DEFENSIVE PRINCIPLES:
- Strictly parameterized SQL via db module.
- Explicit field-level validation with actionable error messages.
- No sensitive stack traces or internal paths exposed.
=============================================================================
"""

import re
from typing import Dict, Any, List
from flask import Blueprint, request, jsonify, current_app
from app.database.db import (
    get_db_connection,
    get_all_internships,
    get_internship_by_id,
    get_all_students,
    get_student_by_id,
    save_student,
)
from app.models.entities import Student, StudentSkill
from app.engine.scorer import generate_recommendations

api_bp = Blueprint("api", __name__)


def _get_db():
    """Helper to acquire database connection using configured DB_PATH."""
    db_path = current_app.config.get("DB_PATH")
    return get_db_connection(db_path)


# -----------------------------------------------------------------------------
# 1. Internships Endpoints
# -----------------------------------------------------------------------------
@api_bp.route("/internships", methods=["GET"])
def list_internships():
    """
    Returns all internship opportunities.
    All demonstration listings are clearly flagged with `is_demo: true`.
    """
    try:
        conn = _get_db()
        internships = get_all_internships(conn)
        conn.close()

        return jsonify({
            "status": "success",
            "count": len(internships),
            "internships": [item.to_dict() for item in internships],
        }), 200
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Unable to retrieve internship listings. Please try again later.",
        }), 500


@api_bp.route("/internships/<int:internship_id>", methods=["GET"])
def get_internship(internship_id: int):
    """
    Returns a single internship listing by ID.
    """
    try:
        conn = _get_db()
        internship = get_internship_by_id(conn, internship_id)
        conn.close()

        if not internship:
            return jsonify({
                "status": "error",
                "message": f"Internship with ID {internship_id} was not found.",
            }), 404

        return jsonify({
            "status": "success",
            "internship": internship.to_dict(),
        }), 200
    except Exception:
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred while retrieving the internship listing.",
        }), 500


# -----------------------------------------------------------------------------
# 2. Students Endpoints
# -----------------------------------------------------------------------------
@api_bp.route("/students", methods=["GET"])
def list_students():
    """
    Returns all registered student profiles.
    """
    try:
        conn = _get_db()
        students = get_all_students(conn)
        conn.close()

        return jsonify({
            "status": "success",
            "count": len(students),
            "students": [s.to_dict() for s in students],
        }), 200
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Unable to retrieve student profiles. Please try again later.",
        }), 500


@api_bp.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id: int):
    """
    Returns a single student profile by ID.
    """
    try:
        conn = _get_db()
        student = get_student_by_id(conn, student_id)
        conn.close()

        if not student:
            return jsonify({
                "status": "error",
                "message": f"Student with ID {student_id} was not found.",
            }), 404

        return jsonify({
            "status": "success",
            "student": student.to_dict(),
        }), 200
    except Exception:
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred while retrieving the student profile.",
        }), 500


@api_bp.route("/students", methods=["POST"])
def create_or_update_student():
    """
    Creates or updates a student profile.
    Strictly validates all academic, personal, and preference fields.
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid JSON payload. Request body must be a JSON object.",
        }), 400

    # 1. Validate Required Fields
    required_fields = ["name", "email", "major", "cgpa", "graduation_year", "preferred_work_mode", "preferred_location"]
    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            return jsonify({
                "status": "error",
                "message": f"Missing or empty required field: '{field}'.",
            }), 400

    # 2. Validate Email
    email = str(data["email"]).strip()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({
            "status": "error",
            "message": f"Invalid email format: '{email}'.",
        }), 400

    # 3. Validate CGPA
    try:
        cgpa = float(data["cgpa"])
        if cgpa < 0.0 or cgpa > 4.0:
            return jsonify({
                "status": "error",
                "message": f"CGPA ({cgpa}) must be between 0.0 and 4.0.",
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "CGPA must be a valid numeric value.",
        }), 400

    # 4. Validate Graduation Year
    try:
        grad_year = int(data["graduation_year"])
        if grad_year < 2020 or grad_year > 2035:
            return jsonify({
                "status": "error",
                "message": f"Graduation year ({grad_year}) must be between 2020 and 2035.",
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "Graduation year must be a valid integer year.",
        }), 400

    # 5. Validate Preferred Work Mode
    work_mode = str(data["preferred_work_mode"]).strip().capitalize()
    if work_mode not in ("Remote", "Hybrid", "Onsite", "Any"):
        return jsonify({
            "status": "error",
            "message": f"Invalid preferred work mode '{data['preferred_work_mode']}'. Allowed: Remote, Hybrid, Onsite, Any.",
        }), 400

    # 6. Validate Optional Student ID
    if "id" in data and data["id"] is not None and data["id"] != "":
        try:
            data["id"] = int(data["id"])
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": f"Invalid student ID '{data['id']}'. Must be an integer.",
            }), 400

    # 7. Save in database
    conn = None
    try:
        conn = _get_db()
        is_update = bool(data.get("id"))
        saved_student = save_student(conn, data)
        conn.commit()

        status_code = 200 if is_update else 201
        action_word = "updated" if is_update else "created"
        return jsonify({
            "status": "success",
            "message": f"Student profile {action_word} successfully.",
            "student": saved_student.to_dict(),
        }), status_code
    except KeyError as e:
        return jsonify({
            "status": "error",
            "message": str(e).strip("'\""),
        }), 404
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 400
    except sqlite3.IntegrityError as e:
        return jsonify({
            "status": "error",
            "message": f"Database constraint violation: {str(e)}",
        }), 400
    except Exception:
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred while saving the student profile. Please verify your data.",
        }), 500
    finally:
        if conn:
            conn.close()


# -----------------------------------------------------------------------------
# 3. Recommendation Endpoint
# -----------------------------------------------------------------------------
@api_bp.route("/recommend", methods=["POST"])
def get_recommendations():
    """
    Generates transparent, multi-criteria internship recommendations.
    Accepts either `{"student_id": 1}` or a full dynamic student profile object.

    Strict Invariants:
    - Hard gatekeeper runs first.
    - Returns segregated `eligible_recommendations` and `ineligible_listings`.
    - Every ineligible listing has score 0.0 with explicit reasons.
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid JSON payload. Please provide 'student_id' or a student profile object.",
        }), 400

    student: Student

    # Case A: Request by registered student_id
    if "student_id" in data:
        try:
            student_id = int(data["student_id"])
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": "Invalid 'student_id'. Must be an integer.",
            }), 400

        conn = _get_db()
        lookup_student = get_student_by_id(conn, student_id)
        conn.close()

        if not lookup_student:
            return jsonify({
                "status": "error",
                "message": f"Student with ID {student_id} does not exist.",
            }), 404
        student = lookup_student

    # Case B: Dynamic student profile provided directly in payload
    else:
        required_fields = ["name", "major", "cgpa", "graduation_year", "preferred_work_mode"]
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field for dynamic recommendation: '{field}'.",
                }), 400

        try:
            cgpa = float(data["cgpa"])
            grad_year = int(data["graduation_year"])
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": "Invalid numeric format for CGPA or graduation year.",
            }), 400

        # Parse skills if provided
        raw_skills = data.get("skills", [])
        student_skills: List[StudentSkill] = []
        for idx, item in enumerate(raw_skills):
            if isinstance(item, dict):
                s_name = item.get("name", "").strip()
                s_prof = item.get("proficiency", "Intermediate").strip()
            elif isinstance(item, str):
                s_name = item.strip()
                s_prof = "Intermediate"
            else:
                continue
            if s_name:
                student_skills.append(StudentSkill(
                    student_id=0,
                    skill_id=idx + 1,
                    skill_name=s_name,
                    category="Technical",
                    proficiency_level=s_prof,
                ))

        student = Student(
            id=None,
            name=str(data["name"]).strip(),
            email=str(data.get("email", "dynamic@example.edu")).strip(),
            major=str(data["major"]).strip(),
            cgpa=cgpa,
            graduation_year=grad_year,
            preferred_work_mode=str(data["preferred_work_mode"]).strip(),
            preferred_location=str(data.get("preferred_location", "Any")).strip(),
            bio_summary=str(data.get("bio_summary", "")).strip(),
            skills=student_skills,
        )

    # Load all internships
    try:
        conn = _get_db()
        internships = get_all_internships(conn)
        conn.close()

        # Generate recommendations using core engine
        eligible, ineligible = generate_recommendations(student, internships)

        return jsonify({
            "status": "success",
            "student_id": student.id,
            "student_name": student.name,
            "total_evaluated": len(internships),
            "eligible_count": len(eligible),
            "ineligible_count": len(ineligible),
            "eligible_recommendations": [rec.to_dict() for rec in eligible],
            "ineligible_listings": [rec.to_dict() for rec in ineligible],
        }), 200

    except Exception:
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred while calculating recommendations.",
        }), 500

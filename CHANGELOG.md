# Changelog

All notable changes, architectural decisions, and bug investigations for the **Public Internship Discovery and Skill-Gap Recommendation Engine** are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.5.2] - 2026-10-31
### Completed & Verified - Milestone 5: Full Web Application MVP & Student Portal

> **Milestone 5 Sign-off:** All manual and automated test gates for Milestone 5 have passed. Candidate profile loading, switching between students, creating new profiles, and updating existing profiles with committed SQLite persistence are fully verified. All 83 automated tests are passing cleanly.

#### Critical Bug Fix: Uncommitted SQLite Transactions on Profile Updates

#### Root Cause Analysis
- **Implicit Rollback on Connection Close:** In Python's `sqlite3`, DML statements (`UPDATE`, `INSERT`, `DELETE`) start a transaction implicitly. Neither `app/database/db.py` `save_student()` nor `app/routes/api.py` `create_or_update_student()` called `conn.commit()`. When `conn.close()` was executed at the end of the request, SQLite executed an **implicit rollback**, completely discarding all profile modifications from disk.
- **Why Previous Tests Appeared to Pass:** In `test_api.py`, `save_student()` read uncommitted changes from the active connection's in-memory transaction buffer before closing, returning the updated values in the JSON response payload. Previous tests verified the JSON response without querying SQLite from a fresh, independent disk connection.
- **Nonexistent ID Fallback Issue:** When an invalid or nonexistent `id` was submitted, the previous code fell back to email lookup or inserted a new student rather than returning a 404 error.

#### Fix Implementation
- **Persistent Transaction Commit (`app/database/db.py`):**
  - Wrapped `save_student()` in `with conn:` context manager and explicitly invoked `conn.commit()`.
  - Added strict existence check: If `student_id` is supplied, `SELECT id FROM students WHERE id = ?` is queried; if not found, a `KeyError` is raised.
  - Added duplicate email validation on update: Verified that the new email does not collide with a different student (`SELECT id FROM students WHERE email = ? AND id != ?`).
  - Added email conflict validation on create: Checked that new candidate emails are globally unique.
- **API Error Handling & Status Codes (`app/routes/api.py`):**
  - Added explicit `conn.commit()` and `finally: conn.close()` in `create_or_update_student()`.
  - Returned HTTP 200 for updates and HTTP 201 for new candidate creations.
  - Mapped `KeyError` to HTTP 404 (`Student with ID ... was not found.`).
  - Mapped `ValueError` and `sqlite3.IntegrityError` to HTTP 400 with human-readable error messages.
- **Frontend Error & Redirect Safety (`app/static/js/profile.js`):**
  - Ensured `API.saveStudent()` must resolve successfully before any dashboard redirect is triggered. On API errors, the user remains on `/profile` with the error alert displayed.

#### Automated Regression Tests
- Added 4 comprehensive regression tests in `tests/test_api.py`:
  1. `test_update_existing_student_by_id`: Verifies changes to CGPA, work mode, and skills are persisted directly to SQLite disk across fresh connections and reflected in subsequent `GET /api/students/<id>` calls without duplicating rows.
  2. `test_update_existing_student_email`: Verifies legitimate email updates succeed while email conflicts with other profiles are rejected with 400.
  3. `test_update_nonexistent_student_id_fails`: Verifies nonexistent IDs return 404 without inserting ghost records.
  4. `test_invalid_input_does_not_corrupt_existing_student`: Verifies rejected updates preserve existing database values without corruption.
  5. `test_create_new_student_duplicate_email_rejected`: Verifies creating a student with an existing email returns 400.
- Full test suite now stands at **83 passing tests** (11 DB + 21 Eligibility + 16 Matcher/Gap + 12 Scorer + 18 API + 5 Views).

---

## [0.5.1] - 2026-10-30
### Fixed & Enhanced - Student Profile Selector & Duplicate Prevention

#### Existing Profile Selection & Loading
- **Root Cause:** When accessing `/profile` directly without a query parameter (e.g. from the top navigation bar), the page previously had no selector dropdown and defaulted to an empty new-student form without querying existing profiles from `GET /api/students`.
- **Student Profile Selector:** Added a prominent selection bar (`#profileStudentSelect` and `#createNewProfileBtn`) to `app/templates/profile.html`.
- **Automatic Loading:** Updated `app/static/js/profile.js` to automatically fetch registered student profiles from `GET /api/students`. If existing students are present, it loads the first student (or one specified by URL parameter `?student_id=...`) via `GET /api/students/<id>` and populates their credentials and technical skills.
- **Obvious Mode Distinction:** Added a dynamic `#profileModeBanner` indicating whether the user is in **Editing Profile** mode (with student name and ID) or **New Profile** mode, adjusting button copy and descriptions accordingly.
- **Duplicate Prevention:** Updated `app/database/db.py` `save_student()` and `app/routes/api.py` `create_or_update_student()` to check existing records by `id` first (updating existing record and email in-place) before falling back to email lookup. This ensures editing an existing profile never produces accidental duplicate database rows.
- **Graceful Error Handling:** Handled missing students, invalid student IDs, and empty profile lists with user-friendly alerts and seamless fallback to New Student mode.

#### Automated Testing Suite
- Added `test_update_existing_student_by_id` in `tests/test_api.py` verifying that updating by ID updates the record without increasing total student count.
- Added invalid student ID validation test in `tests/test_api.py`.
- Added assertions in `tests/test_views.py` ensuring selector and mode banner elements are rendered in `/profile`.
- Total test suite now stands at **79 passing tests** (11 DB + 21 Eligibility + 16 Matcher/Gap + 12 Scorer + 14 API + 5 Views).

---

## [0.5.0] - 2026-10-29
### Added - Milestone 5: Working Flask Web Application & Student Discovery Portal MVP

#### Virtual Environment & Dependencies
- Verified absence of global virtual environments; initialized project-local virtual environment (`.venv`) using Python 3.13.
- Installed `Flask 3.1.3` (and standard dependencies: `Werkzeug`, `Jinja2`, `Click`, `Blinker`, `itsdangerous`, `MarkupSafe`) strictly within `.venv` without polluting the global environment.

#### Backend REST API Architecture (Part 1)
- Implemented `app/__init__.py`:
  - `create_app()`: Application factory supporting testing configuration overrides (`config_override`).
  - Registered blueprints `api_bp` (prefix `/api`) and `views_bp`.
  - Added defensive global error handlers (400, 404, 500) that return structured JSON for API calls without leaking stack traces or internal server paths.
- Implemented `app/routes/api.py`:
  - `GET /api/internships`: Queries all opportunities via parameterized SQL, marking all demonstration listings with `"is_demo": true`.
  - `GET /api/internships/<id>`: Retrieves single listing or returns 404 with descriptive JSON error.
  - `GET /api/students`: Lists registered student profiles with their skills.
  - `GET /api/students/<id>`: Retrieves single student with skills.
  - `POST /api/students`: Defensively validates student input (name, email format, CGPA range $0.0-4.0$, graduation year range $2020-2035$, work mode enum, location) and persists profile and skills using parameterized queries. Returns `201 Created`.
  - `POST /api/recommend`: Supports discovery by registered `student_id` or dynamic profile JSON. Computes multi-factor recommendations and returns segregated `eligible_recommendations` (sorted descending) and `ineligible_listings` (all scoring 0.0 with rejection reasons).
- Implemented `app/routes/views.py`: View routes for `/` (dashboard), `/profile` (profile editor), and `/health` (operational status).
- Updated `app/database/db.py`: Added parameterized database helpers (`get_all_internships`, `get_internship_by_id`, `get_all_students`, `get_student_by_id`, `save_student`).

#### Responsive Frontend & User Experience (Part 2)
- Implemented Jinja2 Templates (`app/templates/`):
  - `base.html`: Common layout with persistent demonstration banner (`is_demo = 1`), accessible navigation header, main content region, and ethical recommender footer disclaimer.
  - `dashboard.html`: Student profile selector dropdown, active candidate summary panel, recommendation discovery button with loading spinner, segregated tabs for eligible vs disqualified opportunities, interactive score breakdown accordions with progress bars, and critical vs growth skill pills.
  - `profile.html`: Full student profile editor with academic input fields, validation error indicators, interactive skill tag manager with proficiency level dropdowns (`Beginner`, `Intermediate`, `Advanced`), quick suggestion chips, and viva defense guidance aside.
- Implemented Client Assets (`app/static/`):
  - `css/styles.css`: Fully responsive, accessible stylesheet featuring CSS variables, high contrast typography, keyboard focus rings, mobile breakpoint rules, and semantic status color-coding.
  - `js/api.js`: Reusable API client wrapper with defensive error handling and network status diagnostics.
  - `js/dashboard.js`: Safe DOM rendering (zero direct `innerHTML` injection of user data), dynamic card construction, score progress bar rendering, and segregated tab switching.
  - `js/profile.js`: Client-side validation, interactive skill tag addition/removal, duplicate detection, quick suggestion chips, profile pre-population from URL parameters (`?student_id=...`), and automated redirect upon saving.
- Implemented Application Runner:
  - `run.py`: Application runner script at project root verifying database presence and launching Flask local server with informative startup console summary.

#### Automated Testing Suite
- Implemented `tests/test_api.py` (13 API integration tests) and `tests/test_views.py` (5 frontend view and asset tests).
- Maintained strict test database isolation: Test suites run against isolated temporary databases (`tests/test_api_isolated.db` and `tests/test_views_isolated.db`), leaving the persistent database `data/internship_engine.db` untouched.
- Full test suite now stands at **78 automated tests** (11 DB + 21 Eligibility + 16 Matcher/Gap + 12 Scorer + 13 API + 5 Views), all passing cleanly in ~0.24s.

---

## [0.4.0] - 2026-10-28
### Added - Milestone 4: Transparent Recommendation Scoring Engine

#### Transparent Multi-Criteria Scorer
- Implemented `app/engine/scorer.py`:
  - `score_internship()`: Evaluates hard eligibility, analyzes skill gaps, and computes bounded match scores ($0.0 \text{ to } 100.0$) using configured heuristic weights ($W_{req}=0.45, W_{pref}=0.15, W_{acad}=0.20, W_{loc}=0.20$).
  - `calculate_required_skill_score()`: Computes proportional points for mandatory skills, safely awarding 0 points if no mandatory skills are specified without division by zero.
  - `calculate_preferred_skill_score()`: Computes proportional points for nice-to-have bonus skills.
  - `calculate_academic_alignment_score()`: Evaluates discipline match (60% of academic) and CGPA margin above cutoff (40% of academic) without double-counting.
  - `calculate_location_alignment_score()`: Evaluates work mode compatibility (50% of location) and geographic proximity/remote accessibility (50% of location).
  - `generate_recommendations()`: Segregates opportunities into ranked `eligible_recommendations` (sorted descending by score) and `ineligible_listings` (all strictly scoring 0.0 with full audit rejection reasons).
- Enforced hard gatekeeping: Disqualified opportunities receive a total score of exactly 0.0 regardless of skill match.
- Clamped scores to $[0.0, 100.0]$ and ensured breakdown points sum to total score within rounding tolerance.
- Exported scorer functions in `app/engine/__init__.py`.

#### Automated Testing Suite
- Implemented `tests/test_scorer.py`:
  - 12 comprehensive unit tests covering fully matched candidates (100.0 score), partial skill matches, zero skill matches, empty requirements, single and multiple eligibility failures, score boundaries, missing profile data, weight validation, breakdown arithmetic, and collection segregation.
  - Total test suite now stands at 60 tests (11 DB + 21 Eligibility + 16 Skill Match/Gap + 12 Scorer), all passing in 0.017s.

---

## [0.3.0] - 2026-10-28
### Added - Milestone 3: Exact Skill Matching & Skill-Gap Analysis

#### Skill Normalization & Canonical Matching
- Implemented `app/engine/matcher.py`:
  - `normalize_skill_name()`: Strips whitespace, lowercases, collapses internal spaces, preserves critical symbols (`c++`, `c#`, `.net`, `node.js`, `html/css`), and maps synonyms to canonical keys.
  - `SKILL_ALIASES`: Curated canonical dictionary mapping over 50 real-world aliases and abbreviations across databases (`postgres` -> `postgresql`), frameworks (`reactjs` -> `react`, `nodejs` -> `node.js`), ML libraries (`sklearn` -> `scikit-learn`, `torch` -> `pytorch`), and DevOps tools (`k8s` -> `kubernetes`, `cicd` -> `ci/cd`).
  - `get_canonical_display_name()`: Converts canonical keys into standardized, professional brand names (`PostgreSQL`, `Scikit-Learn`, `C++`, `REST APIs`) for user interface rendering.
  - `skills_match()` and `find_matched_skill()`: Resilient comparison functions for individual skills and collections.

#### Skill-Gap Analyzer
- Implemented `app/engine/gap_analyzer.py`:
  - `analyze_skill_gaps()`: Computes set-theoretic skill differences between student competencies and opportunity requirements.
  - Explicitly categorizes skills into 4 distinct groups:
    1. `matched_required_skills`: Mandatory skills possessed by the student.
    2. `missing_required_skills`: Critical gaps preventing optimal performance.
    3. `matched_preferred_skills`: Nice-to-have bonus competencies possessed by the student.
    4. `missing_preferred_skills`: Growth opportunities the student can pursue.
  - Strict deduplication: Eliminates repeated skill inputs from students or employers and guarantees mandatory requirements take priority over preferred duplicates.
  - `format_gap_summary()`: Generates human-readable progress feedback for student dashboards.
  - Support for heterogeneous inputs: Seamlessly accepts plain string lists or `StudentSkill` dataclass objects.
- Updated `app/models/results.py`: Enhanced `SkillGapReport` with `matched_required_skills` and `matched_preferred_skills` while maintaining 100% backward compatibility with `matched_skills`.

#### Automated Testing Suite
- Implemented `tests/test_matcher.py` with 8 comprehensive unit tests covering case insensitivity, whitespace trimming, symbol preservation, alias mapping, display formatting, and unknown skills.
- Implemented `tests/test_gap_analyzer.py` with 8 comprehensive unit tests covering complete matches, partial matches with critical gaps, alias resolution, empty list edge cases, deduplication, `StudentSkill` objects, and summary string generation.
- Total test suite now stands at 48 tests (11 DB + 21 Eligibility + 16 Skill Match/Gap), passing in 0.015s.

---

## [0.2.0] - 2026-10-28
### Added - Milestone 2: Rule-Based Eligibility & Exclusion Gatekeeper

#### Eligibility Gatekeeper Engine
- Implemented `app/engine/eligibility.py`:
  - `evaluate_cgpa_eligibility()`: Asserts student CGPA meets or exceeds cutoff (with 2-decimal floating point precision), catching missing or out-of-range values defensively.
  - `evaluate_major_eligibility()`: Normalizes major names, handles common aliases (e.g. `CS` -> `Computer Science`), strips degree prefixes (`B.Tech in CS`), and supports wildcards (`Any`, `*`).
  - `evaluate_grad_year_eligibility()`: Asserts student graduation year falls strictly within `[min_grad_year, max_grad_year]`.
  - `evaluate_work_mode_compatibility()`: Evaluates compatibility between student preference (`Remote`, `Hybrid`, `Onsite`, `Any`) and internship requirements.
  - `check_eligibility()`: Orchestrates all 4 criteria in a non-short-circuiting manner, collecting every applicable failure into `rejection_reasons`.
  - `filter_eligible_internships()`: Partitions opportunity listings into eligible and ineligible sets with explicit audit payloads.
- Created `app/engine/__init__.py` exporting core gatekeeper functions.

#### Automated Testing Suite
- Implemented `tests/test_eligibility.py`:
  - 21 comprehensive unit tests covering fully passing candidates, individual failures for all 4 dimensions, multiple simultaneous failures, exact boundary cases, major normalization, work-mode matrices, defensive handling of `None`/invalid values, and collection partitioning.
  - Test suite runs entirely with in-memory dataclass fixtures, ensuring zero risk of modifying persistent database records.
  - Total test suite now stands at 32 tests (11 DB + 21 Eligibility), passing in 0.011s.

### Fixed / Investigated During Milestone 2
- **Major Normalization Degree Prefix Regex:** Initial regex in `normalize_major()` stripped `"b.tech"` from `"B.Tech in CS"` but left `"in cs"`, causing an alias lookup failure. Updated pattern to `r"^(b\.?tech|b\.?s\.?...)\s+(?:in\s+)?"` and added secondary `^(in|of)\s+` cleanup. Normalization now accurately resolves `"B.Tech in CS"`, `"B.S. in Computer Science"`, and other natural variations to canonical disciplines.

---

## [0.1.0] - 2026-10-28
### Added - Milestone 1: Structured Data Foundation & Persistent Storage

#### Database Architecture & Persistence
- Created `app/models/schema.sql` defining 5 normalized relational tables:
  - `skills`: Master catalog of skills across 7 domains with case-insensitive unique names.
  - `students`: Core academic and preference records with strict CGPA and year range constraints.
  - `student_skills`: Junction table pairing students with skills and self-reported proficiencies (`Beginner`, `Intermediate`, `Advanced`).
  - `internships`: Opportunity listings with eligibility cutoffs and explicit `is_demo` flag.
  - `internship_skills`: Junction table distinguishing mandatory skills (`is_mandatory = 1`) from preferred skills (`is_mandatory = 0`).
- Implemented `app/database/db.py`:
  - `get_db_connection()`: Enforces `PRAGMA foreign_keys = ON;` and enables `sqlite3.Row` dictionary-like column access.
  - `init_db()`: Executes schema creation scripts idempotently.
  - `db_session()`: Transaction context manager providing automatic commit on success and rollback on exceptions.

#### Data Models & Architectural Decoupling
- Implemented `app/models/entities.py` with typed `@dataclass` classes (`Student`, `Internship`, `Skill`, `StudentSkill`, `InternshipSkill`) mapping 1-to-1 with SQLite tables.
- Implemented `app/models/results.py` with transient, in-memory result dataclasses (`EligibilityResult`, `SkillGapReport`, `ScoreBreakdown`, `RecommendationResult`) to ensure computed outputs are clearly distinguished from persisted database entities.

#### Demonstration Dataset
- Created `app/database/seed_data.py`:
  - 21 canonical skills across languages, frameworks, databases, cloud, AI, and soft skills.
  - 6 realistic demonstration internships with diverse eligibility cutoffs and requirements, all flagged with `is_demo = 1`.
  - 3 representative student profiles representing distinct academic backgrounds and preferences.
- Created standalone CLI tool `scripts/setup_db.py` to initialize and seed the persistent database (`data/internship_engine.db`).

#### Configuration & Weight Management
- Implemented `app/config.py`:
  - Base paths for database, schema, and application directories.
  - `DEFAULT_SCORING_WEIGHTS` (45% required skills, 15% preferred skills, 20% academic, 20% location) with explicit academic disclaimer that weights are design heuristics, not empirical hiring probabilities.
  - `validate_weights()` helper function ensuring weights sum strictly to 1.0.

#### Automated Testing Suite
- Implemented `tests/test_db.py`:
  - 11 unit tests using Python standard library `unittest.TestCase` (fully compatible with future `pytest` runner).
  - Tests verify schema creation, foreign key constraints, cascade deletions, check constraints (CGPA and work mode), seed data counts, `is_demo` presence, dataclass serialization, and weight validation.
  - 100% test pass rate in 0.025 seconds.

#### Living Documentation
- Initialized `README.md` with system overview, architecture diagram, scoring formulas, and setup instructions.
- Initialized `LEARNING_GUIDE.md` with beginner-friendly conceptual deep dives, input/output demonstrations, viva questions/answers, and self-test exercises.

### Fixed / Investigated During Milestone 1
- **Windows Terminal Codepage Issue:** In `scripts/setup_db.py`, printing the Unicode character `\u2713` caused `UnicodeEncodeError: 'charmap' codec can't encode character` on standard Windows cp1252 consoles. Replaced unicode checkmarks with ASCII-safe markers `[OK]`, ensuring cross-platform stability without requiring environment variable tweaks.
- **Database Seeding Idempotency:** Running `scripts/setup_db.py` multiple times previously duplicated internship records because `internships` lacked unique conflict resolution. Added `UNIQUE(title, organization)` constraint to `schema.sql`, updated `seed_data.py` to use upsert semantics, and added automatic file cleanup in `setup_db.py`. Repeated runs now maintain exact expected counts (21 skills, 3 students, 6 demo internships).
- **Python Standard Library vs. External Packages:** Checked that `pytest` is not yet installed in the Python 3.13 environment. Wrote the test suite using standard library `unittest.TestCase` to verify the system without premature package installations.

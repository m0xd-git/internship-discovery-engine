# Public Internship Discovery and Skill-Gap Recommendation Engine

A student-facing decision-support application that matches students to feasible internship opportunities, identifies actionable skill gaps, and explains recommendation scores using transparent, multi-criteria evaluation and semantic understanding.

---

## Academic Notice & Ethics Disclaimer

> **IMPORTANT NOTICE FOR EVALUATORS AND EXAMINERS:**
> 1. **Demonstration Data:** All internship listings in this project are realistic demonstration samples, explicitly marked in the database with `is_demo = 1` and clearly badged in the user interface. They do not represent live or endorsed job postings.
> 2. **Alignment Metric vs. Hiring Outcome:** Recommendation scores reflect algorithmic alignment between structured student profiles and listed opportunity requirements. **A recommendation score is NOT a hiring probability or guarantee of selection.**
> 3. **Non-Negotiable Eligibility Gatekeeper:** Hard academic constraints (minimum CGPA, accepted majors, graduation timeframe) are strictly enforced before ranking. A high skill match will **never** override a failed mandatory requirement.

---

## Architecture Overview

The system uses a **Decoupled Layered Architecture (Domain-Driven Service Pattern)** separating persistence, core recommendation algorithms, and presentation:

```
+---------------------------------------------------------------+
|         Presentation Layer (Responsive Student Portal)        |
|            - Profile Editor | Discovery Dashboard             |
|            - Score Breakdown Cards | Skill-Gap Action Plans   |
+-------------------------------+-------------------------------+
                                | (HTTP / JSON REST)
+-------------------------------v-------------------------------+
|              Flask Web Controller & REST API Layer            |
|       /api/students | /api/internships | /api/recommendations |
+-------------------------------+-------------------------------+
                                |
+-------------------------------v-------------------------------+
|                      Core Engine Pipeline                     |
|  1. Eligibility Gatekeeper (Hard Pass/Fail Rules)             |
|  2. Canonical Skill Matcher (Exact & Alias Normalization)     |
|  3. Semantic Similarity (Sentence Transformers all-MiniLM-L6) |
|  4. Skill-Gap Analyzer (Missing Required vs Preferred)        |
|  5. Transparent Scorer (Bounded 0-100 Multi-Factor Math)     |
+-------------------------------+-------------------------------+
                                |
+-------------------------------v-------------------------------+
|              Persistence Layer (SQLite Database)              |
|        students | skills | student_skills                     |
|        internships | internship_skills                        |
+---------------------------------------------------------------+
```

---

## Database Design (Minimal 5-Table Relational Schema)

The persistent storage is powered by SQLite with foreign key enforcement enabled (`PRAGMA foreign_keys = ON;`):

1. **`students`**: Stores student academic profiles, CGPA, graduation year, work mode preference, and location.
2. **`skills`**: Master vocabulary of technical and professional competencies categorized by domain.
3. **`student_skills`**: Junction table mapping students to possessed skills with self-reported proficiency levels (`Beginner`, `Intermediate`, `Advanced`).
4. **`internships`**: Internship listings with hard eligibility cutoffs (min CGPA, eligible majors JSON, graduation year bounds) and the demonstration flag (`is_demo = 1`).
5. **`internship_skills`**: Junction table mapping opportunities to required skills, explicitly identifying mandatory requirements (`is_mandatory = 1`) versus preferred bonuses (`is_mandatory = 0`).

---

## Scoring Formula & Normalization

The engine computes a deterministic score bounded between $0.0$ and $100.0$:

$$\text{Total Score} = W_{req} \cdot S_{req} + W_{pref} \cdot S_{pref} + W_{acad} \cdot S_{acad} + W_{loc} \cdot S_{loc} + W_{sem} \cdot S_{sem}$$

### Component Weights (Configurable in `app/config.py`)

| Component | Baseline Weight (M1–M5) | Milestone 6 Weight (Semantic NLP) | Calculation Description |
| :--- | :---: | :---: | :--- |
| **Required Skills ($S_{req}$)** | $0.45$ ($45$ pts) | $0.40$ ($40$ pts) | $\frac{\|\text{Matched Required}\|}{\|\text{Total Required}\|} \times 100$ |
| **Preferred Skills ($S_{pref}$)** | $0.15$ ($15$ pts) | $0.15$ ($15$ pts) | $\frac{\|\text{Matched Preferred}\|}{\max(1, \|\text{Total Preferred}\|)} \times 100$ |
| **Academic Alignment ($S_{acad}$)** | $0.20$ ($20$ pts) | $0.10$ ($10$ pts) | Major match ($60\%$) $+$ GPA bonus above cutoff ($40\%$) |
| **Location / Mode Match ($S_{loc}$)** | $0.20$ ($20$ pts) | $0.10$ ($10$ pts) | Exact match ($100$), compatible hybrid ($50$), mismatch ($0$) |
| **Semantic Similarity ($S_{sem}$)** | *0.00 (Deferred)* | $0.25$ ($25$ pts) | $\max(0.0, \cos(\mathbf{e}_{student}, \mathbf{e}_{job})) \times 100$ |

*Note: Component weights sum strictly to $1.00$. They represent initial heuristic design hypotheses, not empirically fitted coefficients.*

---

## Directory Structure

```
ai proj/
├── app/
│   ├── __init__.py                # Flask Application Factory (create_app)
│   ├── config.py                  # Database paths, default weights, validation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schema.sql             # Relational DDL with integrity constraints
│   │   ├── entities.py            # Persistent database entity dataclasses
│   │   └── results.py             # Transient computed result dataclasses
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                  # SQLite connection, transaction manager & queries
│   │   └── seed_data.py           # Curated demonstration dataset (is_demo = 1)
│   ├── engine/
│   │   ├── __init__.py            # Exported recommendation engine interface
│   │   ├── eligibility.py         # Rule-based eligibility & exclusion gatekeeper
│   │   ├── matcher.py             # Canonical skill normalizer & alias resolver
│   │   ├── gap_analyzer.py        # Set-theoretic skill-gap analyzer
│   │   └── scorer.py              # Transparent multi-criteria scoring engine
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py                 # REST API endpoints (/api/internships, /api/students, /api/recommend)
│   │   └── views.py               # HTML template views (/, /profile, /health)
│   ├── templates/
│   │   ├── base.html              # Layout shell with demo banner, nav & ethical disclaimer
│   │   ├── dashboard.html         # Candidate discovery dashboard & results explorer
│   │   └── profile.html           # Student profile editor & skill tag manager
│   └── static/
│       ├── css/
│       │   └── styles.css         # Responsive, accessible stylesheet & mobile rules
│       └── js/
│           ├── api.js             # Defensive fetch API client wrapper
│           ├── dashboard.js       # Safe DOM controller for discovery & breakdowns
│           └── profile.js         # Profile form validator & interactive skill manager
├── data/
│   └── internship_engine.db       # Persistent SQLite database file
├── scripts/
│   ├── setup_db.py                # Standalone DB initialization and seeding CLI
│   └── verify_milestone1.py       # Milestone 1 integrity verification script
├── tests/
│   ├── __init__.py
│   ├── test_db.py                 # Unit tests for DB schema, constraints & dataclasses (11 tests)
│   ├── test_eligibility.py        # Unit tests for Rule-Based Eligibility Engine (21 tests)
│   ├── test_matcher.py            # Unit tests for Skill Normalizer & Aliases (8 tests)
│   ├── test_gap_analyzer.py       # Unit tests for Skill-Gap Analyzer (8 tests)
│   ├── test_scorer.py             # Unit tests for Transparent Recommendation Scorer (12 tests)
│   ├── test_api.py                # Integration tests for Flask REST API (18 tests)
│   └── test_views.py              # Integration tests for HTML views & static assets (5 tests)
├── run.py                         # Application runner (starts local dev server)
├── requirements.txt               # Minimal external dependencies (Flask)
├── .gitignore                     # Git exclusion rules (.venv, *.db, cache, secrets)
├── README.md                      # Project documentation (this file)
├── LEARNING_GUIDE.md              # Viva preparation and concept tutorial
└── CHANGELOG.md                   # Version log and architectural decisions
```

---

## REST API Specification

| Endpoint | Method | Description | Sample Status |
| :--- | :---: | :--- | :---: |
| `/api/internships` | `GET` | Retrieve all internship opportunities with `is_demo=True` flag | `200 OK` |
| `/api/internships/<id>` | `GET` | Retrieve detailed listing for a single opportunity | `200 OK` / `404` |
| `/api/students` | `GET` | List all registered student profiles with their skills | `200 OK` |
| `/api/students/<id>` | `GET` | Retrieve profile and skills for a specific student | `200 OK` / `404` |
| `/api/students` | `POST` | Create (201) or update (200) student profile with SQLite commit | `200 OK` / `201` / `400` / `404` |
| `/api/recommend` | `POST` | Generate recommendations (by `student_id` or dynamic profile) | `200 OK` / `400` / `404` |
| `/health` | `GET` | Operational health check probe returning system status | `200 OK` |

---

## Setup and Verification (Collaborator Quickstart)

### Prerequisites
- Python 3.10+ (Recommended: Python 3.11–3.13)
- Git

---

### Step-by-Step Installation

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd "ai proj"
```

#### 2. Create and Activate a Virtual Environment
Isolates dependencies from system-level Python packages:

- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
  *(Note: If PowerShell script execution is restricted, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`)*

- **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

#### 3. Install Dependencies
Install Flask and its production WSGI dependencies from `requirements.txt`:
```bash
pip install -r requirements.txt
```

#### 4. Initialize and Seed the Demonstration Database
Generates the local SQLite database (`data/internship_engine.db`) using the 5-table schema and populates it with 21 skills, 6 demonstration internships (`is_demo = 1`), and 3 initial student profiles:
```bash
python scripts/setup_db.py
```

#### 5. Launch the Web Application
Starts the local development server:
```bash
python run.py
```
Open your web browser and navigate to:
- **Candidate Discovery Dashboard:** [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Student Profile Management:** [http://127.0.0.1:5000/profile](http://127.0.0.1:5000/profile)
- **Operational Health Probe:** [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health)

#### 6. Run the Full Automated Test Suite (83 Tests)
Verifies database integrity, eligibility gatekeeper rules, canonical skill matching, transparent scoring, and Flask REST API endpoints:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## Project Status

- [x] **Milestone 1**: Structured Data Foundation & Persistent Storage (Completed & Verified)
- [x] **Milestone 2**: Rule-Based Eligibility & Exclusion Gatekeeper (Completed & Verified)
- [x] **Milestone 3**: Exact Skill Matching & Skill-Gap Analysis (Completed & Verified)
- [x] **Milestone 4**: Transparent Recommendation Scorer (Heuristic Baseline) (Completed & Verified)
- [x] **Milestone 5**: Flask REST API & Interactive Student Portal MVP (Completed & Verified)
- [ ] **Milestone 6**: Python 3.13 Verification & Sentence Transformers Semantic AI (Next)
- [ ] **Milestone 7**: Enhanced Visual Explanations & Actionable Learning Roadmaps
- [ ] **Milestone 8**: Final System Verification, Viva Defense Guide & Presentation Prep

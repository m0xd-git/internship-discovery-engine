# Learning Guide: College Presentation & Viva Preparation

This guide documents the theoretical and engineering concepts underpinning the **Public Internship Discovery and Skill-Gap Recommendation Engine** in the exact order they are implemented.

Use this document to prepare for your viva voce, project defense, and code walkthroughs.

---

## Milestone 1: Structured Data Foundation & Persistent Storage

### 1. Plain English Problem Explanation
Before an AI or recommendation engine can evaluate whether a student fits an internship, the application must represent students, internships, and competencies as **clean, structured data**.

If we simply kept student skills and internship requirements as unorganized free text or arbitrary spreadsheets, computers would struggle to reliably determine whether a student has "Python" or meets a "3.0 CGPA" cutoff. We need a relational database that enforces rules (e.g. CGPAs cannot be negative, skills cannot be duplicated) and maintains permanent relationships between students and their qualifications.

---

### 2. Core Concepts You Need to Understand

#### Concept A: Why a Relational Database (SQLite)?
- **What is it?** A Relational Database Management System (RDBMS) organizes information into tables with rows and columns, linked together by keys.
- **Why SQLite for this project?** SQLite is serverless, zero-configuration, and self-contained in a single disk file (`data/internship_engine.db`). It is built directly into Python's standard library (`import sqlite3`), meaning there are no external database servers (like MySQL or PostgreSQL) to install or configure, while still providing full SQL standard compliance.

#### Concept B: Primary Keys and Foreign Keys
- **Primary Key (PK):** A column (like `id` in `students`) that uniquely identifies each individual record in a table.
- **Foreign Key (FK):** A column in one table that points to the Primary Key of another table. For example, `student_skills.student_id` points to `students.id`.
- **The SQLite Gotcha:** In SQLite, foreign key enforcement is **disabled by default** for backwards compatibility with legacy versions. You must explicitly execute `PRAGMA foreign_keys = ON;` whenever opening a connection. If you forget this command, SQLite will allow you to insert invalid references!

#### Concept C: Junction Tables (Many-to-Many Relationships)
- One student can possess many skills.
- One skill (e.g., Python) can belong to many students.
- In relational database theory, this is called a **Many-to-Many ($M:N$) relationship**.
- Relational tables cannot store a list directly in a column without violating the First Normal Form (1NF). Instead, we use a **Junction Table** (`student_skills` and `internship_skills`) where each row represents a single pairing: `(student_id, skill_id, proficiency)`. The composite primary key `PRIMARY KEY (student_id, skill_id)` guarantees that a student cannot be linked to the exact same skill twice.

#### Concept D: Cascade Deletion (`ON DELETE CASCADE`)
- What happens if a student deletes their account? If their associated records in `student_skills` remain, those rows become **orphaned data**.
- By specifying `FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE`, SQLite automatically and atomically deletes all corresponding rows in `student_skills` whenever the parent student is deleted.

#### Concept E: Database Entities vs. Engine Result Objects
This is a critical architectural decision often tested in viva examinations:
- **Database Entities (`app/models/entities.py`):** These dataclasses (`Student`, `Internship`, `Skill`) map 1-to-1 to persistent rows in SQLite. They store state.
- **Engine Result Objects (`app/models/results.py`):** These dataclasses (`EligibilityResult`, `SkillGapReport`, `RecommendationResult`) represent **in-memory computations** generated on the fly.
- **Why NOT save recommendations in the database?** Because student profiles, internship requirements, and scoring algorithms are dynamic. Storing computed scores in database rows risks serving stale, out-of-date recommendations when a student updates their skills or an employer changes requirements.

#### Concept F: Python Context Managers (`with` statement)
- Opening and closing database connections manually can lead to resource leaks if an unhandled error crashes the program before `conn.close()` is reached.
- In `app/database/db.py`, the `@contextmanager` generator function `db_session()` ensures that:
  1. A transaction automatically commits if the block finishes without error (`conn.commit()`).
  2. The transaction automatically rolls back if an exception occurs (`conn.rollback()`), preventing half-written corrupted data.
  3. The connection is cleanly closed in the `finally` block regardless of outcome.

#### Concept G: Console Codepages on Windows
- Windows terminals historically use legacy single-byte codepages (like `cp1252`) by default rather than UTF-8.
- Attempting to `print()` non-ASCII unicode characters (such as unicode checkmarks `\u2713`) can throw a `UnicodeEncodeError`. Using ASCII markers like `[OK]` or configuring UTF-8 streams avoids environment-dependent crashes on Windows machines.

---

### 3. File Responsibilities in Milestone 1

| File | What It Does in Plain English |
| :--- | :--- |
| `app/models/schema.sql` | The SQL blueprint. Tells SQLite how to create our 5 tables and enforces rules (e.g. CGPA between $0.0$ and $4.0$). |
| `app/models/entities.py` | Python classes that match our SQLite tables, letting us work with clean objects (`student.cgpa`) instead of messy index tuples (`row[4]`). |
| `app/models/results.py` | Python classes for the calculations the engine will produce later (eligibility outcomes, skill gaps, point breakdowns). |
| `app/database/db.py` | The database manager. Opens connections, turns on foreign keys, and provides safe database sessions. |
| `app/database/seed_data.py` | Inserts realistic demo internships and students so we can test the system with real-world scenarios. |
| `scripts/setup_db.py` | A terminal script allowing you to build and seed your database with one command (`python scripts/setup_db.py`). |
| `tests/test_db.py` | Automated tests that prove every database rule, cascade delete, and dataclass works as expected. |

---

### 4. Concrete Input and Output Example

#### Input: Inserting an Invalid Student (CGPA = 4.8)
```python
conn.execute("""
    INSERT INTO students (name, email, major, cgpa, graduation_year, preferred_work_mode, preferred_location)
    VALUES ('Invalid Student', 'bad@edu.com', 'CS', 4.8, 2026, 'Remote', 'City');
""")
```

#### Output: SQLite Rejection
```
sqlite3.IntegrityError: CHECK constraint failed: cgpa >= 0.0 AND cgpa <= 4.0
```
*Why this is important:* The database itself acts as a defensive guardrail, preventing bad data from ever entering your recommendation pipeline.

---

### 5. Automated Test Results

Test command executed:
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Actual execution output:
```
test_database_entity_serialization (test_db.DataClassesTestCase) ... ok
test_engine_result_objects_distinction (test_db.DataClassesTestCase) ... ok
test_weight_validation_helper (test_db.DataClassesTestCase) ... ok
test_cascade_delete_student (test_db.DatabaseSchemaTestCase) ... ok
test_cgpa_check_constraint (test_db.DatabaseSchemaTestCase) ... ok
test_foreign_key_enforcement (test_db.DatabaseSchemaTestCase) ... ok
test_schema_tables_exist (test_db.DatabaseSchemaTestCase) ... ok
test_work_mode_check_constraint (test_db.DatabaseSchemaTestCase) ... ok
test_all_demo_internships_have_flag (test_db.SeedDataTestCase) ... ok
test_internship_skills_mapping_exists (test_db.SeedDataTestCase) ... ok
test_seed_record_counts (test_db.SeedDataTestCase) ... ok

----------------------------------------------------------------------
Ran 11 tests in 0.025s

OK
```

---

### 6. Sample Viva Questions & Model Answers

**Q1: Why did you use junction tables (`student_skills` and `internship_skills`) instead of storing skills as comma-separated strings inside the `students` or `internships` table?**
> *Model Answer:* Storing comma-separated strings violates First Normal Form (1NF), which requires all attribute values to be atomic. If skills were stored in a single text column, querying students with a specific skill would require slow substring searches (`LIKE '%Python%'`), which also causes false positives (e.g. matching 'Python' inside 'Pythonic'). A junction table allows indexed, exact joins, enforces foreign key integrity, and enables storing additional attributes per relationship, such as proficiency level or whether a skill is mandatory versus preferred.

**Q2: What is the purpose of `conn.row_factory = sqlite3.Row`?**
> *Model Answer:* By default, the Python `sqlite3` cursor returns rows as plain tuples (e.g., `row[0]`, `row[1]`). This makes code brittle because changing the column order in a `SELECT` query breaks the logic. Setting `conn.row_factory = sqlite3.Row` wraps returned rows in an object that allows case-insensitive column access by name (e.g., `row['title']`) as well as tuple unpacking, improving readability and maintainability.

**Q3: Why are recommendation scores and skill gaps NOT saved as columns in the `internships` table?**
> *Model Answer:* In database design, computed results that depend on multiple dynamic inputs (the student's current competencies, the employer's current criteria, and configurable algorithm weights) should not be statically stored in entity tables. Storing computed scores would lead to data anomalies and stale recommendations whenever a student acquires a new skill. Therefore, database tables store persistent facts, while engine result objects (`RecommendationResult`, `SkillGapReport`) are computed transiently in memory.

---

### 7. Check Your Understanding Exercise

**Question:**
Look at the following SQL statement from `app/models/schema.sql`:
```sql
CREATE TABLE IF NOT EXISTS student_skills (
    student_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    proficiency_level TEXT NOT NULL CHECK(proficiency_level IN ('Beginner', 'Intermediate', 'Advanced')),
    PRIMARY KEY (student_id, skill_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);
```

1. What happens if you try to insert `(student_id=1, skill_id=2, proficiency='Master')`?
2. What happens if you try to insert the exact same pair `(student_id=1, skill_id=2, proficiency='Beginner')` twice?
3. If student #1 is deleted from the `students` table, what happens to their rows in `student_skills`?

*(Self-check your answer before checking the answer key below!)*

<details>
<summary><b>Click to reveal Answer Key</b></summary>

1. **Rejection:** It fails with an `IntegrityError` because `'Master'` violates the `CHECK` constraint: `proficiency_level IN ('Beginner', 'Intermediate', 'Advanced')`.
2. **Rejection:** It fails with an `IntegrityError` because `PRIMARY KEY (student_id, skill_id)` enforces uniqueness on the composite pair.
3. **Automatic Cascade Deletion:** SQLite automatically deletes all rows where `student_id = 1` because of the `ON DELETE CASCADE` clause.
</details>

---

## Milestone 2: Rule-Based Eligibility & Exclusion Gatekeeper

### 1. Plain English Problem Explanation
Before an AI calculates a match score, the application must answer a fundamental question: **Is the student legally and academically allowed to take this internship?**

If an internship strictly requires a minimum CGPA of $3.20$, an applicant with a $2.90$ CGPA cannot be hired, even if they have perfect scores in Python and SQL. If we merely averaged their skills and GPA together into a single score, a high skill match might falsely recommend an internship that would automatically reject the student.

The **Eligibility Gatekeeper** acts as an auditable rule-based expert system that checks all mandatory requirements first. If any requirement fails, the internship is marked as disqualified with plain-English explanations.

---

### 2. Core Concepts You Need to Understand

#### Concept A: The Gatekeeper Pattern (Two-Stage Recommendation Pipeline)
- Modern recommender systems in regulated or high-stakes domains (admissions, hiring, finance) use a **Two-Stage Architecture**:
  1. **Stage 1 (Eligibility Gatekeeper):** Strict boolean logic ($Pass / Fail$) enforcing legal, academic, and operational constraints.
  2. **Stage 2 (Scoring & Ranking):** Soft multi-criteria optimization ranking the surviving opportunities.
- **Why this separation is vital:** It prevents "algorithmic compensation" where a high score on an optional feature masks a fatal deficiency in a mandatory requirement.

#### Concept B: Non-Short-Circuiting Evaluation
- In programming, boolean expressions usually short-circuit (e.g. `if not cond1: return False`).
- In user-facing decision support systems, **short-circuiting is poor UX**. If a student fails both CGPA and graduation year, but the system only tells them about CGPA, they will fix their CGPA, apply again, and be shocked by a new rejection for graduation year.
- Our gatekeeper evaluates **all criteria independently**, aggregating every applicable reason into the `rejection_reasons` list.

#### Concept C: String Canonicalization & Alias Resolution
- Real-world data is messy. One student writes `"CS"`, another `"Computer Science"`, and another `"B.Tech in CS"`.
- If we used naive string equality (`student.major == req_major`), all three would fail to match each other.
- **Canonicalization Pipeline:**
  1. Strip whitespace and lowercase: `"  CS  "` $\rightarrow$ `"cs"`.
  2. Remove degree prefixes: `"b.tech in cs"` $\rightarrow$ `"cs"`.
  3. Lookup alias dictionary: `"cs"` $\rightarrow$ `"computer science"`.
  4. Compare canonical tokens against the target list.

#### Concept D: Boundary Value Testing
- Software bugs frequently occur at the exact edges of ranges.
- If a cutoff is $\ge 3.00$:
  - $3.00$ must **PASS**.
  - $2.99$ must **FAIL**.
  - $3.01$ must **PASS**.
- In Python, comparing floats directly (e.g. `2.9999999999999995`) can cause subtle precision errors. We round to 2 decimal places (`round(val, 2)`) to ensure deterministic behavior.

---

### 3. File Responsibilities in Milestone 2

| File | What It Does in Plain English |
| :--- | :--- |
| `app/engine/eligibility.py` | Contains the pure Python rule engine. Evaluates CGPA cutoffs, accepted majors, graduation years, and work modes. Reports all rejection reasons. |
| `app/engine/__init__.py` | Package entry point exposing `check_eligibility`, `filter_eligible_internships`, and `normalize_major`. |
| `tests/test_eligibility.py` | 21 automated unit tests verifying boundary values, failure messages, alias matching, and partitioning without touching persistent database files. |

---

### 4. Concrete Input and Output Examples

#### Example 1: Fully Eligible Candidate
```python
student = Student(major="CS", cgpa=3.6, graduation_year=2026, preferred_work_mode="Remote")
internship = Internship(min_cgpa=3.0, eligible_majors=["Computer Science"], min_grad_year=2025, max_grad_year=2027, work_mode="Remote")

result = check_eligibility(student, internship)
```
**Output:**
```python
EligibilityResult(
    is_eligible=True,
    rejection_reasons=[],
    checks={'cgpa_met': True, 'major_eligible': True, 'grad_year_valid': True, 'work_mode_compatible': True}
)
```

#### Example 2: Ineligible Candidate (Multiple Failures)
```python
student = Student(major="Civil Engineering", cgpa=2.8, graduation_year=2024, preferred_work_mode="Onsite")
internship = Internship(min_cgpa=3.0, eligible_majors=["Computer Science"], min_grad_year=2025, max_grad_year=2027, work_mode="Remote")

result = check_eligibility(student, internship)
```
**Output:**
```python
EligibilityResult(
    is_eligible=False,
    rejection_reasons=[
        "CGPA requirement not met: student CGPA (2.80) is below minimum required (3.00).",
        "Major requirement not met: student major 'Civil Engineering' is not among accepted disciplines: ['Computer Science'].",
        "Graduation year requirement not met: student graduation year (2024) is earlier than minimum allowed (2025).",
        "Work mode incompatibility: student prefers 'Onsite' but internship requires 'Remote'."
    ],
    checks={'cgpa_met': False, 'major_eligible': False, 'grad_year_valid': False, 'work_mode_compatible': False}
)
```

---

### 5. Automated Test Results

Command executed:
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Actual execution output:
```
test_database_entity_serialization (test_db.DataClassesTestCase) ... ok
test_engine_result_objects_distinction (test_db.DataClassesTestCase) ... ok
test_weight_validation_helper (test_db.DataClassesTestCase) ... ok
test_cascade_delete_student (test_db.DatabaseSchemaTestCase) ... ok
test_cgpa_check_constraint (test_db.DatabaseSchemaTestCase) ... ok
test_foreign_key_enforcement (test_db.DatabaseSchemaTestCase) ... ok
test_schema_tables_exist (test_db.DatabaseSchemaTestCase) ... ok
test_work_mode_check_constraint (test_db.DatabaseSchemaTestCase) ... ok
test_all_demo_internships_have_flag (test_db.SeedDataTestCase) ... ok
test_internship_skills_mapping_exists (test_db.SeedDataTestCase) ... ok
test_seed_record_counts (test_db.SeedDataTestCase) ... ok
test_cgpa_failure_only (test_eligibility.TestEligibilityEngine) ... ok
test_cgpa_just_below_boundary_fails (test_eligibility.TestEligibilityEngine) ... ok
test_exact_cgpa_boundary_passes (test_eligibility.TestEligibilityEngine) ... ok
test_exact_grad_year_boundaries_pass (test_eligibility.TestEligibilityEngine) ... ok
test_filter_eligible_internships_partitioning (test_eligibility.TestEligibilityEngine) ... ok
test_fully_eligible_student_passes (test_eligibility.TestEligibilityEngine) ... ok
test_grad_year_too_early_failure (test_eligibility.TestEligibilityEngine) ... ok
test_grad_year_too_late_failure (test_eligibility.TestEligibilityEngine) ... ok
test_invalid_work_mode (test_eligibility.TestEligibilityEngine) ... ok
test_major_any_wildcard_passes_all (test_eligibility.TestEligibilityEngine) ... ok
test_major_case_and_alias_matching (test_eligibility.TestEligibilityEngine) ... ok
test_major_failure_only (test_eligibility.TestEligibilityEngine) ... ok
test_major_normalization_aliases (test_eligibility.TestEligibilityEngine) ... ok
test_missing_and_invalid_cgpa (test_eligibility.TestEligibilityEngine) ... ok
test_missing_grad_year (test_eligibility.TestEligibilityEngine) ... ok
test_missing_major (test_eligibility.TestEligibilityEngine) ... ok
test_multiple_simultaneous_failures_reported (test_eligibility.TestEligibilityEngine) ... ok
test_work_mode_exact_matches (test_eligibility.TestEligibilityEngine) ... ok
test_work_mode_incompatibilities (test_eligibility.TestEligibilityEngine) ... ok
test_work_mode_incompatibility_failure (test_eligibility.TestEligibilityEngine) ... ok
test_work_mode_student_any_matches_all (test_eligibility.TestEligibilityEngine) ... ok

----------------------------------------------------------------------
Ran 32 tests in 0.011s

OK
```

---

### 6. Sample Viva Questions & Model Answers

**Q1: Why did you implement eligibility as an explicit rule-based gatekeeper rather than letting a machine learning model decide who is eligible?**
> *Model Answer:* Machine learning models (especially neural networks or regressors) are probabilistic and prone to unexplainable boundary errors or spurious correlations. In contrast, academic prerequisites (such as minimum CGPA cutoffs, degree requirements, and graduation year windows) are hard, non-negotiable legal and organizational constraints. A rule-based gatekeeper guarantees 100% determinism, avoids algorithmic bias, and produces clear, human-readable rejection reasons that can be audited.

**Q2: What is the benefit of non-short-circuiting evaluation in `check_eligibility`?**
> *Model Answer:* In a traditional boolean `if-else` chain, evaluation stops on the first failed condition. However, for a student seeking internship opportunities, knowing only one failure reason leads to frustration if they resolve that issue only to be rejected by another hidden constraint. By evaluating all criteria independently, the gatekeeper provides a comprehensive diagnostic report of every constraint the student failed to meet.

---

### 7. Check Your Understanding Exercise

**Question:**
An internship specifies:
- `min_cgpa`: 3.20
- `eligible_majors`: `["Data Science", "Computer Science"]`
- `min_grad_year`: 2025
- `max_grad_year`: 2027
- `work_mode`: `"Remote"`

Student profile:
- `cgpa`: 3.20
- `major`: `"B.S. in Comp Sci"`
- `graduation_year`: 2027
- `preferred_work_mode`: `"Onsite"`

1. What will `result.is_eligible` be?
2. Which individual checks in `result.checks` will be `True` and which will be `False`?
3. What will be inside `result.rejection_reasons`?

*(Self-check your answer before checking the answer key below!)*

<details>
<summary><b>Click to reveal Answer Key</b></summary>

1. **`False`:** The student is not eligible due to work mode incompatibility.
2. **Checks Breakdown:**
   - `cgpa_met`: `True` ($3.20 \ge 3.20$ exact boundary pass)
   - `major_eligible`: `True` (`"B.S. in Comp Sci"` normalizes to `"computer science"`)
   - `grad_year_valid`: `True` ($2027 \le 2027$ exact boundary pass)
   - `work_mode_compatible`: `False` (student strictly prefers `"Onsite"` but internship requires `"Remote"`)
3. **Rejection Reasons:**
   - `["Work mode incompatibility: student prefers 'Onsite' but internship requires 'Remote'."]`
</details>

---

## Milestone 3: Exact Skill Matching & Skill-Gap Analysis

### 1. Plain English Problem Explanation
Once an internship passes the eligibility gatekeeper, the engine must compare the student's technical abilities with the employer's expectations.

This is harder than doing `if student_skill == required_skill` because:
1. **Terminology Variations:** A student might write `"Postgres"` or `"postgres"`, while the listing says `"PostgreSQL"`. A student writes `"sklearn"` while the job asks for `"Scikit-Learn"`.
2. **Punctuation Sensitivity:** Naive cleaning that removes all symbols will corrupt `"C++"` into `"C"`, or `"C#"` into `"C"`, turning three completely different programming languages into the same string!
3. **Skill Priority Differences:** Missing a **mandatory requirement** (e.g. knowing Python for a Python Backend role) is a critical blocker. Missing an **optional preference** (e.g. knowing Docker) is simply an opportunity to learn. The system must never treat these two kinds of gaps identically.

---

### 2. Core Concepts You Need to Understand

#### Concept A: The Token Normalization & Alias Pattern
In Information Retrieval (IR), matching queries against documents requires canonicalization:
- **Case Folding:** Lowercasing every token (`"Python"` $\rightarrow$ `"python"`).
- **Whitespace Collapsing:** Replacing multiple spaces with a single space (`"data   analysis"` $\rightarrow$ `"data analysis"`).
- **Curated Synonym / Alias Dictionary:** Mapping colloquial abbreviations to canonical identifiers:
  ```
  "postgres", "pgsql" ---------> "postgresql"
  "sklearn", "scikit learn" ---> "scikit-learn"
  "k8s", "kube" ---------------> "kubernetes"
  "reactjs", "react.js" -------> "react"
  ```
- **Display Canonicalization:** Transforming internal keys back into official industry brand names for the UI (`"postgresql"` $\rightarrow$ `"PostgreSQL"`, `"rest apis"` $\rightarrow$ `"REST APIs"`).

#### Concept B: Protecting Syntax-Critical Characters
Most text-cleaning tutorials advise stripping all non-alphanumeric characters (`re.sub(r'[^a-zA-Z0-9]', '', text)`).
**Why this breaks tech skills:**
- `"C++"` becomes `"C"`
- `"C#"` becomes `"C"`
- `".NET"` becomes `"NET"`
- `"Node.js"` becomes `"Nodejs"`
- `"HTML/CSS"` becomes `"HTMLCSS"`
Our custom normalizer explicitly handles and protects these meaningful industry symbols.

#### Concept C: Set Difference for Skill-Gap Analysis
Skill matching is fundamentally rooted in **Set Theory**:
- Let $S$ be the set of skills possessed by the student.
- Let $R$ be the set of mandatory required skills for the internship.
- Let $P$ be the set of preferred/optional skills for the internship.

Mathematically, the engine computes:
1. **Matched Required Skills:** $M_{req} = R \cap S$
2. **Critical Skill Gaps (Missing Required):** $G_{req} = R \setminus S$
3. **Matched Preferred Skills:** $M_{pref} = P \cap S$
4. **Growth Opportunities (Missing Preferred):** $G_{pref} = P \setminus S$

#### Concept D: Deduplication and Precedence Rules
- If a student lists `"Python"`, `"python"`, and `"  PYTHON  "`, the engine deduplicates them into a single entry to prevent score inflation.
- If an employer accidentally lists a skill as both required and preferred, the required classification takes precedence so the skill is not counted twice.

#### Concept E: Ethical Disclaimer Regarding "Missing" Skills
In candidate recommendation systems, you must never claim: *"The student lacks the ability to do X."*
The accurate, defensible statement is: *"The student has not listed competency X on their profile."*
This ethical distinction prevents algorithmic prejudice and reminds evaluators that recommendations guide exploration rather than rendering absolute hiring judgments.

---

### 3. File Responsibilities in Milestone 3

| File | What It Does in Plain English |
| :--- | :--- |
| `app/engine/matcher.py` | Contains the canonical alias dictionary and normalizer. Resolves abbreviations like `postgres` $\rightarrow$ `postgresql` and protects symbols like `C++`. |
| `app/engine/gap_analyzer.py` | Implements the set-theoretic comparison. Categorizes skills into matched required, critical gaps, matched preferred, and growth opportunities. |
| `tests/test_matcher.py` | 8 unit tests verifying case insensitivity, aliases, whitespace, symbol preservation, and unknown skill handling. |
| `tests/test_gap_analyzer.py` | 8 unit tests verifying complete matches, critical gaps, empty lists, deduplication, and summary formatting. |

---

### 4. Concrete Input and Output Example

#### Input:
```python
student_skills = ["postgres", "Python", "Git", "React"]

internship_required = ["PostgreSQL", "Python", "Docker"]
internship_preferred = ["Git", "Kubernetes"]

report = analyze_skill_gaps(student_skills, internship_required, internship_preferred)
```

#### Output (`SkillGapReport`):
```json
{
  "matched_required_skills": ["PostgreSQL", "Python"],
  "missing_required_skills": ["Docker"],
  "matched_preferred_skills": ["Git"],
  "missing_preferred_skills": ["Kubernetes"],
  "total_required_skills": 3,
  "total_preferred_skills": 2,
  "matched_skills": ["PostgreSQL", "Python", "Git"],
  "has_critical_gap": true
}
```

#### Human-Readable Summary:
```
"Matched 2 of 3 required skills. Critical Gaps: [Docker]. Matched 1 of 2 preferred skills. Growth Opportunities: [Kubernetes]."
```

---

### 5. Automated Test Results

Command executed:
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Actual execution output:
```
Ran 48 tests in 0.015s

OK
```
*(11 Database tests + 21 Eligibility Gatekeeper tests + 8 Matcher tests + 8 Gap Analyzer tests)*

---

### 6. Sample Viva Questions & Model Answers

**Q1: Why did you build a custom skill normalizer and alias dictionary instead of using generic regex punctuation removal?**
> *Model Answer:* Standard text preprocessing strips non-alphanumeric characters, which catastrophically mutates programming languages and tools like `C++`, `C#`, `.NET`, and `Node.js`. A custom normalizer preserves domain-critical characters while collapsing whitespace and resolving industry synonyms (e.g. `postgres` $\rightarrow$ `PostgreSQL`, `sklearn` $\rightarrow$ `Scikit-Learn`). This gives us 100% deterministic matching without requiring external dependencies or risking false mismatches.

**Q2: What is the difference between a "Critical Gap" and a "Growth Opportunity"?**
> *Model Answer:* A Critical Gap represents a missing mandatory requirement ($R \setminus S$). If a student lacks a mandatory skill, they may struggle in the daily responsibilities of the role. A Growth Opportunity represents a missing preferred or bonus skill ($P \setminus S$). Lacking a preferred skill will not prevent them from performing the core role, but acquiring it makes them a stronger candidate. Separating them allows the dashboard to give actionable, prioritized learning roadmaps to students.

---

### 7. Check Your Understanding Exercise

**Question:**
A student lists: `["py", "sklearn", "SQL"]`
An internship requires: `["Python", "Scikit-Learn", "Docker"]`
An internship prefers: `["SQL", "AWS"]`

1. What are the `matched_required_skills`?
2. What are the `missing_required_skills`?
3. What are the `matched_preferred_skills`?
4. What are the `missing_preferred_skills`?
5. Is `has_critical_gap` True or False?

*(Self-check your answer before checking the answer key below!)*

<details>
<summary><b>Click to reveal Answer Key</b></summary>

1. **`matched_required_skills`:** `["Python", "Scikit-Learn"]` (`"py"` resolved to Python, `"sklearn"` resolved to Scikit-Learn)
2. **`missing_required_skills`:** `["Docker"]`
3. **`matched_preferred_skills`:** `["SQL"]`
4. **`missing_preferred_skills`:** `["AWS"]`
5. **`has_critical_gap`:** `True` (because Docker is a missing mandatory requirement)
</details>

---

## Milestone 4: Transparent Recommendation Scoring Engine

### 1. Plain English Problem Explanation
How do we rank internship opportunities for a student who is eligible for multiple listings?

In many recommendation applications, scores are generated by opaque neural networks or arbitrary black-box functions. If a student receives an $82\%$ match score, neither the student nor the college evaluator knows how that number was created. Did they get points for having high grades? For knowing Python? Or did a location match inflate the score?

The **Transparent Recommendation Scorer** replaces the black box with **auditable, deterministic multi-criteria mathematics**. Every decimal point in the final score links directly to a verifiable line item in a transparent score breakdown.

---

### 2. Core Concepts You Need to Understand

#### Concept A: Multi-Criteria Decision Analysis (MCDA)
- When evaluating alternatives with multiple competing objectives (skills, academic background, location), computer science uses **Multi-Criteria Decision Analysis**.
- We use a **Weighted Additive Utility Model**:
  $$\text{Total Score} = \sum_{i=1}^{n} W_i \times S_i$$
- Constraints:
  1. All weights must be non-negative: $W_i \ge 0$.
  2. All weights must sum to $1.00$ ($100\%$): $\sum W_i = 1.00$.
  3. Every sub-score $S_i$ is normalized between $0.0$ and $100.0$.
  4. The resulting score is strictly bounded: $0.0 \le \text{Total Score} \le 100.0$.

#### Concept B: Hard Gatekeeping vs. Soft Ranking
- **The Core Rule:** A failed mandatory requirement can **never** be compensated for by a high skill match.
- If a candidate has $100\%$ of the required skills, but fails the minimum CGPA cutoff, the gatekeeper disqualifies the listing.
- The scorer assigns an in-memory score of **strictly $0.0$** and moves the listing into the `ineligible_listings` collection. The student is told exactly why they were disqualified.

#### Concept C: Avoiding Double-Counting
A common flaw in naive scoring systems is rewarding the same evidence twice across different factors:
- **Academic Alignment ($20$ pts):**
  - Sub-factor 1: **Major Relevance ($12.0$ pts):** Evaluates academic discipline fit.
  - Sub-factor 2: **CGPA Margin ($8.0$ pts):** Evaluates academic performance headroom above the required cutoff ($4.0$ baseline for meeting cutoff $+$ up to $4.0$ for excess performance).
  - *No double-counting:* Discipline and performance are evaluated on separate axes.
- **Location & Work Mode ($20$ pts):**
  - Sub-factor 1: **Work Mode Fit ($10.0$ pts):** Evaluates working arrangement compatibility (Remote, Hybrid, Onsite).
  - Sub-factor 2: **Geographic Proximity ($10.0$ pts):** Evaluates physical city location. Remote opportunities are accessible universally ($10.0$ pts); onsite/hybrid roles evaluate city proximity.
  - *No double-counting:* Working arrangement and physical city proximity are evaluated on separate axes.

#### Concept D: Fair Handling of Empty Requirements
- What happens if an internship lists **no mandatory skills**?
- If we gave $100\%$ ($45$ points) for an empty list, the student would receive an accidental windfall reward for skills they never demonstrated.
- If we divided by zero, the application would crash.
- **Fair Rule:** If $N_{req} == 0$, raw ratio is $0.0$ and points awarded are $0.0$, with a transparent explanatory note: `"No mandatory skills listed by employer (0 of 0 evaluated; no points awarded)"`.

#### Concept E: Non-Probability Disclosure
- The score is strictly an **algorithmic alignment metric**, measuring how closely candidate data matches posted criteria.
- It must **never** be represented as a "hiring probability," as hiring involves subjective human interviews, applicant pool competition, soft skills, and portfolio reviews not captured in listed requirements.

---

### 3. Step-by-Step Hand-Calculated Scoring Example

Let us trace an exact calculation by hand to demonstrate mathematical transparency:

#### Inputs:
- **Student:**
  - Major: Computer Science
  - CGPA: $3.50$
  - Preferred Work Mode: Remote
  - Preferred Location: Bengaluru, India
  - Skills: `["Python", "Git", "Docker"]`
- **Internship:**
  - Min CGPA: $3.00$
  - Eligible Majors: `["Computer Science", "Information Technology"]`
  - Work Mode: Remote
  - Location: Bengaluru, India
  - Required Skills: `["Python", "SQL"]` (2 required skills)
  - Preferred Skills: `["Docker", "Git", "Kubernetes"]` (3 preferred skills)

#### Step 1: Eligibility Gatekeeper Check
- CGPA: $3.50 \ge 3.00 \rightarrow$ **PASS**
- Major: `"Computer Science"` in `["Computer Science", "Information Technology"]` $\rightarrow$ **PASS**
- Work Mode: `"Remote"` == `"Remote"` $\rightarrow$ **PASS**
- Graduation Year: Within range $\rightarrow$ **PASS**
- **Outcome:** `is_eligible = True`. Proceed to multi-factor scoring.

#### Step 2: Factor 1 — Required Skills ($W_{req} = 0.45$, Max $45.0$ pts)
- Matched Required: `["Python"]` (1 skill)
- Total Required: 2 skills
- Points = $\frac{1}{2} \times 45.0 = \mathbf{22.50\text{ pts}}$

#### Step 3: Factor 2 — Preferred Skills ($W_{pref} = 0.15$, Max $15.0$ pts)
- Matched Preferred: `["Docker", "Git"]` (2 skills)
- Total Preferred: 3 skills
- Points = $\frac{2}{3} \times 15.0 = \mathbf{10.00\text{ pts}}$

#### Step 4: Factor 3 — Academic Alignment ($W_{acad} = 0.20$, Max $20.0$ pts)
- **Major Match ($60\%$ of $20.0 = 12.0$ pts):**
  - Direct match with Computer Science $\rightarrow \mathbf{12.00\text{ pts}}$
- **CGPA Margin ($40\%$ of $20.0 = 8.0$ pts):**
  - Baseline for meeting cutoff ($50\%$ of $8.0$): $4.00$ pts
  - Margin headroom: $4.00 - 3.00 = 1.00$
  - Excess CGPA: $3.50 - 3.00 = 0.50$
  - Margin ratio: $\frac{0.50}{1.00} = 0.50$
  - Margin bonus: $0.50 \times 4.00 = 2.00$ pts
  - CGPA points: $4.00 + 2.00 = \mathbf{6.00\text{ pts}}$
- Academic Total = $12.00 + 6.00 = \mathbf{18.00\text{ pts}}$

#### Step 5: Factor 4 — Location & Mode Alignment ($W_{loc} = 0.20$, Max $20.0$ pts)
- **Work Mode Fit ($50\%$ of $20.0 = 10.0$ pts):**
  - Exact match (`"Remote"` == `"Remote"`) $\rightarrow \mathbf{10.00\text{ pts}}$
- **Geographic Proximity ($50\%$ of $20.0 = 10.0$ pts):**
  - Remote opportunity (accessible from any location) $\rightarrow \mathbf{10.00\text{ pts}}$
- Location Total = $10.00 + 10.00 = \mathbf{20.00\text{ pts}}$

#### Step 6: Total Recommendation Score
$$\text{Total Score} = 22.50 + 10.00 + 18.00 + 20.00 + 0.00 = \mathbf{70.50\text{ / }100.0}$$
*Every single point is accounted for with zero black-box magic.*

---

### 4. Automated Test Results

Command executed:
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Actual execution output:
```
Ran 60 tests in 0.017s

OK
```
*(11 Database tests + 21 Eligibility tests + 8 Matcher tests + 8 Gap Analyzer tests + 12 Scorer tests)*

---

### 5. Sample Viva Questions & Model Answers

**Q1: How does your recommendation engine prevent algorithmic discrimination where an ineligible student is recommended an opportunity due to high keyword match?**
> *Model Answer:* We enforce a strict **Two-Stage Decision Pipeline**. Stage 1 is the deterministic Eligibility Gatekeeper that audits non-negotiable legal and academic constraints (CGPA cutoffs, degree eligibility, work authorization, graduation timeframe). If any mandatory condition fails, the internship is marked as disqualified and its score is forced to **strictly 0.0**. The scoring engine only ranks opportunities that have fully cleared Stage 1.

**Q2: How do you handle internships that list no required skills without causing division-by-zero or accidental score inflation?**
> *Model Answer:* In `calculate_required_skill_score`, we check if the total count of required skills is zero. If zero, instead of dividing by zero or awarding unearned points, the function safely returns $0.0$ points and documents in the breakdown details that no mandatory skills were listed. This ensures that scores reflect demonstrable qualifications rather than unstated criteria.

---

### 6. Check Your Understanding Exercise

**Question:**
An internship has:
- Required Skills: `["Python", "SQL", "Git"]` (3 skills, weight $W_{req} = 0.45$, max $45.0$ pts)
- Preferred Skills: `["Docker"]` (1 skill, weight $W_{pref} = 0.15$, max $15.0$ pts)

Student profile:
- Possesses: `["Python", "Git"]`
- Missing: `["SQL"]` (required) and `["Docker"]` (preferred)

1. How many points does the student earn for Required Skills?
2. How many points does the student earn for Preferred Skills?
3. If this student had a $2.60$ CGPA on a $3.00$ cutoff, what would their total recommendation score be?

*(Self-check your answer before checking the answer key below!)*

<details>
<summary><b>Click to reveal Answer Key</b></summary>

1. **`30.00 pts`:** $\frac{2}{3} \times 45.0 = 30.00$ points.
2. **`0.00 pts`:** $\frac{0}{1} \times 15.0 = 0.00$ points.
3. **`0.00 pts`:** The student failed the minimum CGPA cutoff ($2.60 < 3.00$). By invariant rule, failed eligibility immediately drops the total score to **strictly 0.0**, regardless of the 30 skill points earned!
</details>

---

## Milestone 5: Web Application MVP (Part 1 — Flask REST API)

### 1. Plain English Problem Explanation
So far, our recommendation engine existed purely as Python modules and unit tests. While engineers can run Python scripts from the command line, real students and university administrators need an accessible interface.

Before building the visual web page, we must construct the **API (Application Programming Interface)**. The API acts as the server-side controller: it receives incoming HTTP requests (e.g. "Find recommendations for Student #1"), validates input data, asks our engine to calculate matches, and returns clean, structured JSON.

---

### 2. Core Concepts You Need to Understand

#### Concept A: The Application Factory Pattern (`create_app`)
- In simple tutorials, Flask is created as a global variable: `app = Flask(__name__)`.
- **Why this causes problems in production and testing:** A global `app` cannot easily be reconfigured for automated tests without mutating production settings or database paths.
- **The Factory Pattern:** By wrapping app creation in a function (`create_app(config_override=None)`), we can instantiate separate, isolated copies of the app:
  1. A **Development App** pointing to `data/internship_engine.db`.
  2. A **Testing App** pointing to a temporary, isolated database (`tests/test_api_isolated.db`).

#### Concept B: Flask Blueprints for Modular Architecture
- Rather than cramming all route decorators into a single massive file, Flask uses **Blueprints**:
  - `app/routes/api.py` (`api_bp`, mounted at `/api`): Handles pure data operations, JSON inputs, and REST endpoints.
  - `app/routes/views.py` (`views_bp`): Handles rendering HTML templates and page navigation.
- This enforces the **Separation of Concerns** principle: API controllers do not care about HTML styling, and views do not duplicate business logic.

#### Concept C: SQLite In-Memory Concurrency in Web Servers
- In SQLite, `:memory:` databases are connection-private. If Route A opens connection 1 to `:memory:`, and Route B opens connection 2 to `:memory:`, they cannot see each other's data!
- For API integration testing where multiple HTTP requests occur, we use a **dedicated temporary test database file** (`tests/test_api_isolated.db`). It is initialized and seeded before the test suite starts, shared across test client requests, and unlinked when tests finish. This completely shields your real demo database from modification.

#### Concept D: Defensive Error Handling (No Leaked Stack Traces)
- A critical security and software engineering rule: **Never expose internal Python stack traces, database errors, or local filesystem paths to clients.**
- Leaking tracebacks gives potential attackers insights into database table structures and directory paths.
- We implement central error handlers returning predictable JSON structures:
  ```json
  {
    "status": "error",
    "message": "CGPA (4.5) must be between 0.0 and 4.0."
  }
  ```

---

### 3. Concrete API Request & Response Example

#### Request: `POST /api/recommend`
```json
{
  "student_id": 1
}
```

#### Response: `200 OK`
```json
{
  "status": "success",
  "student_id": 1,
  "student_name": "Aarav Sharma",
  "total_evaluated": 6,
  "eligible_count": 4,
  "ineligible_count": 2,
  "eligible_recommendations": [
    {
      "internship_id": 1,
      "internship_title": "Backend Software Engineering Intern",
      "organization": "OpenTech Innovations",
      "is_demo": true,
      "total_score": 78.5,
      "score_breakdown": {
        "required_skills": { "points": 45.0, "max_points": 45.0, "details": "Matched 3 of 3 required skills (100.0%). Possessed: [Python, SQL, Git]." },
        "preferred_skills": { "points": 5.0, "max_points": 15.0, "details": "Matched 1 of 3 preferred skills (33.3%). Possessed: [Flask]. Missing: [Docker, REST APIs]." },
        "academic_alignment": { "points": 18.5, "max_points": 20.0, "details": "Major 'Computer Science' matches target discipline. CGPA 3.60 earned baseline + margin bonus." },
        "location_alignment": { "points": 20.0, "max_points": 20.0, "details": "Exact work mode match: both are 'Remote'. Remote opportunity universally accessible." }
      },
      "skill_gaps": {
        "matched_required_skills": ["Python", "SQL", "Git"],
        "missing_required_skills": [],
        "matched_preferred_skills": ["Flask"],
        "missing_preferred_skills": ["Docker", "REST APIs"],
        "has_critical_gap": false
      }
    }
  ],
  "ineligible_listings": [
    {
      "internship_id": 4,
      "internship_title": "Frontend Web Development Intern",
      "organization": "Digital Public Infrastructure Foundation",
      "is_demo": true,
      "total_score": 0.0,
      "eligibility": {
        "is_eligible": false,
        "rejection_reasons": [
          "Work mode incompatibility: student prefers 'Remote' but internship requires 'Onsite'."
        ]
      }
    }
  ]
}
```

---

### 4. Automated Test Results

Command executed:
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Actual execution output:
```
Ran 73 tests in 0.223s

OK
```
*(11 Database + 21 Eligibility + 16 Skill Match/Gap + 12 Scorer + 13 API Integration tests)*

---

### 5. Sample Viva Questions & Model Answers

**Q1: What is the purpose of the Application Factory pattern in Flask, and how did it help in this project?**
> *Model Answer:* The Application Factory pattern (`create_app`) instantiates the Flask application dynamically inside a callable function rather than as a global instance. This allows us to pass different configuration dictionaries (`config_override`) at runtime. Specifically, during testing, we configure the app to use an isolated temporary database file (`tests/test_api_isolated.db`), completely preventing automated tests from modifying or resetting the user's persistent production/demonstration database.

**Q2: Why do you separate `/api` JSON routes from view rendering routes using Flask Blueprints?**
> *Model Answer:* Using Blueprints (`api_bp` and `views_bp`) decouples the presentation layer from the data API. The REST API conforms to client-agnostic standards, returning structured JSON with HTTP status codes (200, 201, 400, 404, 500). This separation of concerns means that if the frontend changes (e.g. transitioning from server-rendered templates to a single-page app or mobile client), the underlying API and core business logic remain completely unchanged and testable.

---

---

## Milestone 5 (Part 2): Responsive Student Portal & User Experience

### 1. Conceptual Foundation: Browser-to-Backend Architecture

In Milestone 5 Part 2, we built the presentation layer for our recommendation engine. A critical viva concept is understanding **how data travels between the browser and the backend engine**:

```
+-----------------------------------------------------------------------------------+
|                                  USER BROWSER                                     |
|                                                                                   |
|  [Student Profile Form]                                 [Discovery Dashboard]     |
|   - Academic inputs & validation                         - Candidate selector     |
|   - Interactive skill tags (Beginner/Inter/Adv)          - Dynamic summary card   |
|   - Quick suggestion chips                               - Discover button        |
+--------------------------+----------------------------------------+---------------+
                           |                                        |
                 POST /api/students                        POST /api/recommend
                 { profile JSON }                          { student_id: 1 }
                           |                                        |
+--------------------------v----------------------------------------v---------------+
|                                FLASK WEB APPLICATION                              |
|                                                                                   |
|  [views.py]                                    [api.py]                           |
|   - Renders Jinja2 HTML templates               - Validates JSON payload          |
|   - Serves static CSS & JavaScript              - Queries SQLite database         |
|                                                 - Invokes recommendation engine   |
+-----------------------------------------------------------+-----------------------+
                                                            |
+-----------------------------------------------------------v-----------------------+
|                                CORE ENGINE & PERSISTENCE                          |
|                                                                                   |
|  1. SQLite: Fetches student skills & internship requirements                     |
|  2. Rule Gatekeeper: Evaluates CGPA, majors, grad year, work mode                |
|  3. Skill Normalizer & Gap Analyzer: Categorizes mandatory vs preferred          |
|  4. Transparent Scorer: Computes bounded 0-100 scores and factor breakdown        |
+-----------------------------------------------------------------------------------+
```

---

### 2. Core Frontend Principles & Security Best Practices

#### A. Safe DOM Manipulation vs. XSS Vulnerabilities
A common vulnerability in web development is **Cross-Site Scripting (XSS)**, where untrusted user input is injected directly into the DOM using `element.innerHTML = userInput`. If a student enters their name as `<img src=x onerror=alert('hacked')>`, naive `innerHTML` would execute that script.

In our frontend (`dashboard.js` and `profile.js`), we strictly adhere to safe DOM manipulation:
```javascript
// SAFE: Uses native browser text node creation (never interprets HTML tags)
const title = document.createElement("h3");
title.className = "opp-title";
title.textContent = rec.internship_title; // Plain text only!
titleBox.appendChild(title);
```

#### B. Segregated Presentation: Eligible vs. Disqualified
To prevent student confusion and maintain algorithmic integrity:
1. **Eligible Tab:** Displays ranked opportunities sorted in descending order of match score ($0.0 \text{ to } 100.0$). Each card features an expandable accordion displaying the 4-factor breakdown (Required Skills 45%, Preferred Skills 15%, Academic 20%, Location 20%) with visual progress bars.
2. **Disqualified Tab:** Clearly isolates opportunities that failed mandatory criteria. Every listing in this tab displays a prominent red **0.0 Disqualified** badge and lists every specific reason why the candidate was excluded (e.g. *"Student CGPA (2.80) is below minimum required (3.00)"*).

#### C. Ethical UI Messaging
Recommendation scores are never presented as hiring guarantees. The persistent footer explicitly reminds users:
> *"Recommendation scores indicate algorithmic alignment between candidate profiles and listed opportunity requirements. Scores do not represent hiring probabilities or guarantees of employment. Missing skills represent absence from the student profile, not proof of inability."*

---

### 3. File Responsibilities in Milestone 5 Part 2

| File | What It Does in Plain English |
| :--- | :--- |
| `app/templates/base.html` | Base layout template with demonstration warning banner (`is_demo = 1`), brand navigation, and ethical footer. |
| `app/templates/dashboard.html` | Discovery dashboard template containing student selector, summary grid, tabs, and result containers. |
| `app/templates/profile.html` | Interactive profile editor template with academic inputs, skill tags panel, quick chips, and viva guidance card. |
| `app/static/css/styles.css` | Accessible, responsive CSS system with semantic color coding (green for matched, red for missing required, blue for preferred). |
| `app/static/js/api.js` | Reusable API wrapper for standard browser `fetch` with error parsing. |
| `app/static/js/dashboard.js` | Safe DOM controller for profile switching, recommendation execution, accordion toggles, and tab switching. |
| `app/static/js/profile.js` | Profile validator, skill tag addition/deletion, suggestion chips, URL pre-population, and API persistence. |
| `run.py` | Standalone application runner script to launch the local web server (`http://127.0.0.1:5000/`). |
| `tests/test_views.py` | 5 integration tests verifying dashboard HTML rendering, profile form rendering, and static asset delivery. |

---

### 4. Running the Complete Application Locally

To test the application in your browser:
```powershell
.\.venv\Scripts\python.exe run.py
```
Then navigate to:
- **Discovery Dashboard:** `http://127.0.0.1:5000/`
- **Student Profile Management:** `http://127.0.0.1:5000/profile`
- **Health Check:** `http://127.0.0.1:5000/health`

---

### 5. Automated Test Results Across Full Suite (83 Tests)

Command executed:
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Execution Summary:
```
test_api.py:          18 passing tests (REST API endpoints, ID updates, SQLite commit & error handling)
test_db.py:           11 passing tests (Database schema, constraints & dataclasses)
test_eligibility.py:  21 passing tests (Rule-based gatekeeper & boundary checks)
test_gap_analyzer.py:  8 passing tests (Skill-gap categorization & deduplication)
test_matcher.py:       8 passing tests (Skill normalizer, aliases & symbol preservation)
test_scorer.py:       12 passing tests (Transparent multi-factor scoring & segregation)
test_views.py:         5 passing tests (HTML template rendering & static asset serving)
----------------------------------------------------------------------
Ran 83 tests in 0.237s

OK
```

---

### 6. Sample Viva Questions & Model Answers

**Q1: Why did you build the frontend using vanilla JavaScript and server-rendered templates rather than a heavy framework like React or Angular?**
> *Model Answer:* For an academic capstone focused on recommendation algorithms and decision-support transparency, vanilla JavaScript and Jinja2 templates offer significant advantages:
> 1. **Zero build tooling complexity:** There are no Node.js dependencies, Webpack configurations, or compilation steps.
> 2. **Examiner transparency:** Any examiner can open the source files and immediately see how data is bound to the DOM using standard web standards (`document.createElement`, `fetch`).
> 3. **Fast and lightweight:** The entire frontend executes natively in any browser with zero startup delay or package vulnerabilities.

**Q2: In Python's `sqlite3`, what happens if you execute an UPDATE statement without calling `conn.commit()` before `conn.close()`?**
> *Model Answer:* In Python's `sqlite3` module, any DML statement (`UPDATE`, `INSERT`, `DELETE`) implicitly opens a database transaction. If you close the connection (`conn.close()`) without an explicit `conn.commit()`, SQLite executes an **implicit rollback**, silently discarding the changes from disk. Even if an in-memory query on the same connection reads the modified row before closing, future connections from the dashboard or profile page will only see the old uncommitted state. Using the `with conn:` context manager or calling `conn.commit()` guarantees changes are written and persisted to disk.

**Q3: How does the profile editor prevent accidental duplicate records when editing an existing student?**
> *Model Answer:* The profile editor maintains the active candidate's primary key (`currentEditingStudentId`). When saving changes, the frontend includes `"id": currentEditingStudentId` in the JSON payload sent to `POST /api/students`. In `app/database/db.py`, `save_student()` checks for this ID first. If found, it executes an `UPDATE students SET ... WHERE id = ?`, modifying the existing student's record and synchronizing their skill junction table without inserting a new row. If no ID is provided, it proceeds with new candidate creation.

**Q4: How does the frontend prevent Cross-Site Scripting (XSS) when rendering user-submitted profile data and skills?**
> *Model Answer:* The frontend strictly avoids `innerHTML` when interpolating dynamic data. Instead, it creates DOM nodes using `document.createElement()` and assigns user data exclusively through `element.textContent = data`. This ensures the browser treats the input strictly as literal text, neutralizing any `<script>` or malicious HTML tags.

**Q5: How does the dashboard communicate that a candidate was rejected by the engine?**
> *Model Answer:* Rather than simply omitting disqualified internships or burying them at the bottom with a low score, the UI provides a dedicated **Disqualified / Ineligible** tab. Each card displays an explicit `0.0 Disqualified` score and a highlighted callout box enumerating all exact failure reasons generated by the eligibility gatekeeper (such as CGPA below cutoff or work-mode mismatch). This makes the algorithmic decision completely auditable and transparent.

---

### 7. Check Your Understanding Exercise

**Question:**
When a student visits `/profile` directly from the navigation bar (without query parameters), how does the page handle profile selection?

1. What API call does `profile.js` make on page load?
2. Which profile is initially loaded into the form?
3. How can the user switch to creating a brand new student?

*(Self-check your answer before checking the answer key below!)*

<details>
<summary><b>Click to reveal Answer Key</b></summary>

1. **`API.getStudents()`** is called to retrieve all registered student profiles.
2. The dropdown (`profileStudentSelect`) is populated with all registered students, and the first student (e.g. Aarav Sharma, ID 1) is automatically loaded via **`API.getStudent(studentId)`**, populating all form inputs and skill tags.
3. The user can either select **`+ Create New Student Profile...`** from the dropdown or click the dedicated **`+ Create New Student`** button, which clears the form, sets `currentEditingStudentId = null`, and switches the mode banner to **New Profile**.
</details>






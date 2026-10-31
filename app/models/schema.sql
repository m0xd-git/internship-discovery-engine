-- ============================================================================
-- Public Internship Discovery and Skill-Gap Recommendation Engine
-- Database Schema: 5 Core Relational Tables
-- ============================================================================

-- Enforce foreign key constraints in SQLite
PRAGMA foreign_keys = ON;

-- 1. Skills: Canonical vocabulary of skills and competencies
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    category TEXT NOT NULL CHECK(category IN (
        'Programming Language',
        'Framework & Library',
        'Database & Storage',
        'Cloud & DevOps',
        'Data Science & AI',
        'Methodology & Tools',
        'Soft Skills'
    )),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Students: Persistent student profile, academic background, and preferences
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    major TEXT NOT NULL,
    cgpa REAL NOT NULL CHECK(cgpa >= 0.0 AND cgpa <= 4.0),
    graduation_year INTEGER NOT NULL CHECK(graduation_year >= 2020 AND graduation_year <= 2035),
    preferred_work_mode TEXT NOT NULL CHECK(preferred_work_mode IN ('Remote', 'Hybrid', 'Onsite', 'Any')),
    preferred_location TEXT NOT NULL,
    bio_summary TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Student Skills: Junction table linking students to possessed skills with proficiency
CREATE TABLE IF NOT EXISTS student_skills (
    student_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    proficiency_level TEXT NOT NULL CHECK(proficiency_level IN ('Beginner', 'Intermediate', 'Advanced')),
    PRIMARY KEY (student_id, skill_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- 4. Internships: Opportunity details, eligibility cutoffs, and demonstration marker
CREATE TABLE IF NOT EXISTS internships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL COLLATE NOCASE,
    organization TEXT NOT NULL COLLATE NOCASE,
    department TEXT DEFAULT '',
    location TEXT NOT NULL,
    work_mode TEXT NOT NULL CHECK(work_mode IN ('Remote', 'Hybrid', 'Onsite')),
    min_cgpa REAL NOT NULL DEFAULT 0.0 CHECK(min_cgpa >= 0.0 AND min_cgpa <= 4.0),
    eligible_majors_json TEXT NOT NULL, -- Stored as JSON array e.g. ["Computer Science", "Information Technology"]
    min_grad_year INTEGER NOT NULL,
    max_grad_year INTEGER NOT NULL,
    description TEXT NOT NULL,
    stipend TEXT DEFAULT 'Unpaid',
    application_deadline DATE,
    is_demo INTEGER NOT NULL DEFAULT 1 CHECK(is_demo IN (0, 1)), -- Transparent demonstration flag
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(title, organization)
);

-- 5. Internship Skills: Junction table mapping mandatory and preferred skills for listings
CREATE TABLE IF NOT EXISTS internship_skills (
    internship_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    is_mandatory INTEGER NOT NULL DEFAULT 1 CHECK(is_mandatory IN (0, 1)), -- 1 = Required, 0 = Preferred
    PRIMARY KEY (internship_id, skill_id),
    FOREIGN KEY (internship_id) REFERENCES internships(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

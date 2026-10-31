"""
Deterministic Skill Normalization & Canonical Matching Engine
=============================================================================
CRITICAL ARCHITECTURAL ROLE:
Provides deterministic, rule-based canonicalization and exact/alias skill
matching without reliance on heavy machine-learning packages or black-box logic.

HANDLES:
1. Case-insensitivity ('python' == 'Python')
2. Whitespace and punctuation variations ('Node.js' == 'node js' == 'nodejs')
3. Canonical industry aliases ('postgres' -> 'PostgreSQL', 'sklearn' -> 'Scikit-Learn')
4. C++ / C# symbol preservation ('c++' is preserved, not stripped to 'c')
=============================================================================
"""

import re
from typing import Optional, Dict, Iterable


# Canonical alias dictionary mapping alternative names, abbreviations, and common typos
# to their canonical lowercase representation.
SKILL_ALIASES: Dict[str, str] = {
    # Databases & Storage
    "postgres": "postgresql",
    "pgsql": "postgresql",
    "postgre": "postgresql",
    "postgressql": "postgresql",
    "mongo": "mongodb",
    "mssql": "sql server",
    "ms sql": "sql server",
    "microsoft sql server": "sql server",
    "sqlite3": "sqlite",

    # Programming Languages
    "py": "python",
    "python3": "python",
    "python 3": "python",
    "python 2": "python",
    "js": "javascript",
    "javascript es6": "javascript",
    "ecmascript": "javascript",
    "ts": "typescript",
    "golang": "go",
    "go lang": "go",
    "cpp": "c++",
    "c plus plus": "c++",
    "c#": "c#",
    "csharp": "c#",
    "c sharp": "c#",

    # Frameworks & Web Technologies
    "react": "react",
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",
    "vue": "vue.js",
    "vuejs": "vue.js",
    "vue.js": "vue.js",
    "vue js": "vue.js",
    "angular": "angular",
    "angularjs": "angular",
    "angular.js": "angular",
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "node js": "node.js",
    "express": "express.js",
    "expressjs": "express.js",
    "express.js": "express.js",
    "flask py": "flask",
    "flask framework": "flask",
    "django framework": "django",
    "fastapi": "fastapi",
    "fast api": "fastapi",
    "html": "html/css",
    "css": "html/css",
    "html5": "html/css",
    "css3": "html/css",
    "html / css": "html/css",
    "html/css": "html/css",
    "html and css": "html/css",

    # Data Science & Machine Learning
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "scikitlearn": "scikit-learn",
    "scikit_learn": "scikit-learn",
    "pandas library": "pandas",
    "numpy library": "numpy",
    "tf": "tensorflow",
    "torch": "pytorch",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "data analytics": "data analysis",

    # Cloud & DevOps
    "docker container": "docker",
    "docker containers": "docker",
    "k8s": "kubernetes",
    "kube": "kubernetes",
    "aws": "aws",
    "amazon web services": "aws",
    "gcp": "gcp",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "azure": "azure",
    "microsoft azure": "azure",
    "git": "git",
    "github": "git",
    "git/github": "git",
    "git / github": "git",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "ci cd": "ci/cd",
    "continuous integration": "ci/cd",

    # Methodologies & Tools
    "rest api": "rest apis",
    "rest apis": "rest apis",
    "restful api": "rest apis",
    "restful apis": "rest apis",
    "rest": "rest apis",
    "agile": "agile methodology",
    "agile methodology": "agile methodology",
    "scrum": "agile methodology",
    "tech writing": "technical writing",
}


# Canonical display names for user-facing presentations and UI badges
CANONICAL_DISPLAY_NAMES: Dict[str, str] = {
    "postgresql": "PostgreSQL",
    "mongodb": "MongoDB",
    "sql": "SQL",
    "sqlite": "SQLite",
    "sql server": "SQL Server",
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "c++": "C++",
    "c#": "C#",
    "go": "Go",
    "java": "Java",
    "react": "React",
    "vue.js": "Vue.js",
    "angular": "Angular",
    "node.js": "Node.js",
    "express.js": "Express.js",
    "flask": "Flask",
    "django": "Django",
    "fastapi": "FastAPI",
    "html/css": "HTML/CSS",
    "scikit-learn": "Scikit-Learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "data analysis": "Data Analysis",
    "natural language processing": "Natural Language Processing",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",
    "linux": "Linux",
    "git": "Git",
    "ci/cd": "CI/CD",
    "rest apis": "REST APIs",
    "agile methodology": "Agile Methodology",
    "technical writing": "Technical Writing",
}


def normalize_skill_name(name: Optional[str]) -> str:
    """
    Normalizes a skill name for deterministic comparison.
    
    Steps:
    1. Returns empty string if name is None or empty.
    2. Strips leading and trailing whitespace.
    3. Converts to lowercase.
    4. Handles special cases (e.g. preserves 'c++', 'c#', 'ci/cd', 'html/css').
    5. Checks against curated alias dictionary.
    
    Examples:
        '  Postgres ' -> 'postgresql'
        'SKLearn' -> 'scikit-learn'
        'Node.JS' -> 'node.js'
        'C++' -> 'c++'
    """
    if not name or not isinstance(name, str):
        return ""

    cleaned = name.strip().lower()

    # Normalize internal multiple whitespace: 'data   analysis' -> 'data analysis'
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Check direct match in alias table
    if cleaned in SKILL_ALIASES:
        return SKILL_ALIASES[cleaned]

    # Special punctuation normalizations:
    # 'node-js' or 'node_js' -> 'node.js'
    if cleaned in ("node-js", "node_js"):
        return "node.js"

    # 'react-js' or 'react_js' -> 'react'
    if cleaned in ("react-js", "react_js"):
        return "react"

    # 'vue-js' or 'vue_js' -> 'vue.js'
    if cleaned in ("vue-js", "vue_js"):
        return "vue.js"

    return cleaned


def get_canonical_display_name(name: str) -> str:
    """
    Returns the standard, branded display name for a skill.
    
    Examples:
        'postgres' -> 'PostgreSQL'
        'sklearn' -> 'Scikit-Learn'
        'c++' -> 'C++'
        'UNKNOWN' -> 'Unknown' (Title case fallback)
    """
    norm = normalize_skill_name(name)
    if norm in CANONICAL_DISPLAY_NAMES:
        return CANONICAL_DISPLAY_NAMES[norm]
    # Fallback to Title Cased original string
    return name.strip().title() if name else ""


def skills_match(skill1: Optional[str], skill2: Optional[str]) -> bool:
    """
    Determines whether two skill strings refer to the same canonical skill.
    
    Examples:
        skills_match('postgres', 'PostgreSQL') -> True
        skills_match('C++', 'c++') -> True
        skills_match('Python', 'Java') -> False
    """
    norm1 = normalize_skill_name(skill1)
    norm2 = normalize_skill_name(skill2)
    if not norm1 or not norm2:
        return False
    return norm1 == norm2


def find_matched_skill(target_skill: str, candidate_skills: Iterable[str]) -> Optional[str]:
    """
    Searches an iterable of candidate skill names for a match with target_skill.
    Returns the original candidate string if matched, otherwise None.
    """
    norm_target = normalize_skill_name(target_skill)
    if not norm_target:
        return None

    for cand in candidate_skills:
        if normalize_skill_name(cand) == norm_target:
            return cand
    return None

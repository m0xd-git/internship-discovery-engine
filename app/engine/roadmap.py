"""
Personalized Learning Roadmap Engine
=============================================================================
CRITICAL ARCHITECTURAL ROLE:
Transforms identified competency gaps into structured, actionable, and
pedagogically sequenced self-study milestones for students targeting
specific internship opportunities.

NON-NEGOTIABLE CORE INVARIANTS:
1. Strict Determinism: The roadmap is deterministic and explainable. No external
   APIs, random variations, or hallucinated third-party courses/certificates.
2. Mandatory Prioritization: Mandatory missing requirements are always sequenced
   ahead of preferred bonus opportunities.
3. Explicit Prerequisites: Prerequisite dependencies are only applied when
   explicitly defined in the verified skill knowledge base.
4. Approximate Durations: All learning durations are presented as approximate
   self-study estimates, not guaranteed completion times.
5. Interview Readiness: Students who match 100% of listed skills receive
   interview-readiness and portfolio presentation guidance, not an assumption
   that they have nothing left to learn.
6. Canonical Normalization: Integrates with the existing matcher's canonical
   skill normalizer and alias resolver.
7. Ethical AI Guardrail: Missing skills reflect absence from the student's profile,
   not verified proof of inability.
=============================================================================
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple, Any, Union
from app.models.entities import Student, Internship, StudentSkill
from app.models.results import SkillGapReport, RoadmapStep, LearningRoadmap
from app.engine.matcher import (
    normalize_skill_name,
    get_canonical_display_name,
)


# =============================================================================
# Pedagogical Knowledge Base for Canonical Skill Taxonomy (21 Skills)
# =============================================================================
SKILL_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "python": {
        "canonical_name": "Python",
        "category": "Programming Language",
        "min_weeks": 1,
        "max_weeks": 2,
        "prerequisites": [],
        "learning_focus": [
            "Core syntax, data structures (lists, dicts, sets, tuples), and control flow",
            "Functional paradigms, list comprehensions, and generator expressions",
            "Object-oriented programming (OOP): classes, inheritance, and dunder methods",
            "Exception handling, file I/O, virtual environments, and package management",
        ],
        "practical_milestone": "Build a modular command-line tool with robust error handling, unit tests, and structured file parsing.",
    },
    "javascript": {
        "canonical_name": "JavaScript",
        "category": "Programming Language",
        "min_weeks": 1,
        "max_weeks": 2,
        "prerequisites": [],
        "learning_focus": [
            "Variables (let/const), scopes, closures, and arrow functions",
            "Asynchronous programming: Callbacks, Promises, async/await, and the Event Loop",
            "DOM manipulation, event delegation, and browser Web APIs",
            "Modern ES6+ syntax: destructuring, spread/rest operators, and ES modules",
        ],
        "practical_milestone": "Develop an interactive browser dashboard that asynchronously fetches, filters, and displays JSON data.",
    },
    "java": {
        "canonical_name": "Java",
        "category": "Programming Language",
        "min_weeks": 2,
        "max_weeks": 3,
        "prerequisites": [],
        "learning_focus": [
            "Strong static typing, class design, interfaces, and polymorphism",
            "Java Collections Framework: List, Set, Map, and Queue implementations",
            "Exception handling hierarchies and Java Stream API functional pipelines",
            "JVM fundamentals, memory management basics, and build automation (Maven/Gradle)",
        ],
        "practical_milestone": "Implement a multi-threaded data processing pipeline utilizing Java Collections and Stream filters.",
    },
    "c++": {
        "canonical_name": "C++",
        "category": "Programming Language",
        "min_weeks": 2,
        "max_weeks": 3,
        "prerequisites": [],
        "learning_focus": [
            "Pointers, references, and manual/dynamic memory management",
            "Object-oriented modeling, operator overloading, and copy/move semantics",
            "Standard Template Library (STL): vector, map, algorithms, and iterators",
            "Resource Acquisition Is Initialization (RAII) and modern smart pointers",
        ],
        "practical_milestone": "Construct a custom templated data structure container (e.g., dynamic circular buffer) adhering strictly to RAII.",
    },
    "sql": {
        "canonical_name": "SQL",
        "category": "Database & Storage",
        "min_weeks": 1,
        "max_weeks": 2,
        "prerequisites": [],
        "learning_focus": [
            "Relational data modeling, table creation, and primary/foreign key constraints",
            "Data retrieval: SELECT filtering, WHERE clauses, and sorting",
            "Multi-table relational queries using INNER, LEFT, and FULL JOINs",
            "Aggregations (GROUP BY, HAVING), subqueries, and database indexing fundamentals",
        ],
        "practical_milestone": "Design a normalized 3-table relational database and write analytical queries with multi-table JOINs and aggregations.",
    },
    "postgresql": {
        "canonical_name": "PostgreSQL",
        "category": "Database & Storage",
        "min_weeks": 1,
        "max_weeks": 2,
        "prerequisites": ["SQL"],
        "learning_focus": [
            "Advanced PostgreSQL data types: JSONB, arrays, and UUIDs",
            "Common Table Expressions (CTEs), recursive queries, and window functions",
            "Transaction isolation levels, row-level locking, and ACID guarantees",
            "Query plan inspection using EXPLAIN ANALYZE and partial indexing",
        ],
        "practical_milestone": "Implement an audit-logging schema utilizing JSONB columns, window functions, and EXPLAIN-optimized indexes.",
    },
    "mongodb": {
        "canonical_name": "MongoDB",
        "category": "Database & Storage",
        "min_weeks": 1,
        "max_weeks": 2,
        "prerequisites": [],
        "learning_focus": [
            "Document-oriented database concepts, collections, and BSON structure",
            "CRUD operations using MongoDB query syntax and projection filters",
            "Aggregation pipeline stages: $match, $group, $project, and $lookup",
            "Compound indexes, text search indexes, and schema validation rules",
        ],
        "practical_milestone": "Build and query an e-commerce catalog collection using multi-stage aggregation pipelines and indexing.",
    },
    "react": {
        "canonical_name": "React",
        "category": "Framework & Library",
        "min_weeks": 2,
        "max_weeks": 3,
        "prerequisites": ["JavaScript", "HTML/CSS"],
        "learning_focus": [
            "Declarative UI component architecture, JSX syntax, and props passing",
            "State management with useState, useEffect, and custom hooks",
            "Controlled forms, lifting state up, and conditional rendering",
            "Component lifecycle, memoization (useMemo/useCallback), and REST API integration",
        ],
        "practical_milestone": "Build a responsive single-page application (SPA) with search filtering, modal dialogs, and live API data fetching.",
    },
    "flask": {
        "canonical_name": "Flask",
        "category": "Framework & Library",
        "min_weeks": 1,
        "max_weeks": 2,
        "prerequisites": ["Python"],
        "learning_focus": [
            "WSGI fundamentals, URL routing, request contexts, and response objects",
            "Application Factory pattern, Blueprints, and configuration separation",
            "Jinja2 template inheritance and static asset management",
            "Building RESTful JSON APIs, defensive error handlers, and SQLite integration",
        ],
        "practical_milestone": "Develop a modular 3-tier Flask REST API using Blueprints, custom HTTP error handlers, and SQLite persistence.",
    },
    "node.js": {
        "canonical_name": "Node.js",
        "category": "Framework & Library",
        "min_weeks": 1,
        "max_weeks": 2,
        "prerequisites": ["JavaScript"],
        "learning_focus": [
            "Node.js runtime architecture, asynchronous event loop, and buffers",
            "Core modules: fs, path, http, events, and stream processing",
            "Building HTTP servers with Express.js routing and custom middleware pipelines",
            "Environment configuration, security middleware (cors, helmet), and npm dependency management",
        ],
        "practical_milestone": "Construct a modular Express.js REST service with logging middleware, request validation, and JSON endpoints.",
    },
    "html/css": {
        "canonical_name": "HTML/CSS",
        "category": "Framework & Library",
        "min_weeks": 1,
        "max_weeks": 2,
        "prerequisites": [],
        "learning_focus": [
            "Semantic HTML5 document hierarchy and web accessibility guidelines (WCAG, ARIA)",
            "CSS Box Model, specificity, cascading rules, and CSS variables",
            "Modern responsive layouts using Flexbox and multi-column CSS Grid",
            "Media queries, mobile-first design patterns, and accessible typography",
        ],
        "practical_milestone": "Code a fully responsive, mobile-first landing page with CSS Grid and accessible navigation without external frameworks.",
    },
    "docker": {
        "canonical_name": "Docker",
        "category": "Cloud & DevOps",
        "min_weeks": 1,
        "max_weeks": 2,
        "prerequisites": [],
        "learning_focus": [
            "Containerization vs virtualization principles and Docker architecture",
            "Writing efficient Dockerfiles: base images, layer caching, and multi-stage builds",
            "Container lifecycle management: run, stop, inspect, volumes, and port mapping",
            "Multi-service orchestration using Docker Compose files and networking",
        ],
        "practical_milestone": "Containerize a full-stack web application (API service + database) using a multi-stage Dockerfile and Docker Compose.",
    },
    "git": {
        "canonical_name": "Git",
        "category": "Methodology & Tools",
        "min_weeks": 1,
        "max_weeks": 1,
        "prerequisites": [],
        "learning_focus": [
            "Distributed version control architecture: working tree, index, and commit graph",
            "Branching strategies: feature branches, fast-forward vs merge commits, and rebasing",
            "Remote collaboration workflows: cloning, tracking branches, fetching, and pulling",
            "Inspecting changes (diff, log), stashing, tags, and resolving merge conflicts",
        ],
        "practical_milestone": "Manage a collaborative multi-branch feature repository, resolve a simulated merge conflict, and tag a release.",
    },
    "linux": {
        "canonical_name": "Linux",
        "category": "Cloud & DevOps",
        "min_weeks": 1,
        "max_weeks": 2,
        "prerequisites": [],
        "learning_focus": [
            "Linux file hierarchy, navigation, and text utilities (grep, awk, sed, find)",
            "File permissions, ownership (chmod, chown), and user/group administration",
            "Process management: signals, background tasks (ps, top, kill), and systemd services",
            "Bash scripting: variables, control flow, exit codes, and cron automation",
        ],
        "practical_milestone": "Write an automated Bash backup and log-monitoring script scheduled via cron with alerting on disk usage.",
    },
    "data analysis": {
        "canonical_name": "Data Analysis",
        "category": "Data Science & AI",
        "min_weeks": 1,
        "max_weeks": 2,
        "prerequisites": [],
        "learning_focus": [
            "Exploratory Data Analysis (EDA) methodologies and workflow framing",
            "Descriptive statistics: central tendency, dispersion, and bivariate correlation",
            "Data hygiene: handling missing values, identifying outliers, and type normalization",
            "Data storytelling: selecting appropriate visual charts and summarizing findings",
        ],
        "practical_milestone": "Produce an exploratory data analysis report on an open civic dataset identifying key trends and data anomalies.",
    },
    "machine learning": {
        "canonical_name": "Machine Learning",
        "category": "Data Science & AI",
        "min_weeks": 2,
        "max_weeks": 3,
        "prerequisites": ["Python"],
        "learning_focus": [
            "Supervised vs unsupervised learning paradigms and objective formulation",
            "Feature preprocessing: scaling, one-hot encoding, and train/test splits",
            "Core predictive algorithms: Linear/Logistic Regression, Decision Trees, and Random Forests",
            "Evaluation metrics: Precision, Recall, F1-Score, ROC-AUC, and cross-validation",
        ],
        "practical_milestone": "Train, evaluate, and tune a supervised classification model on tabular data, reporting cross-validated metrics.",
    },
    "pandas": {
        "canonical_name": "Pandas",
        "category": "Data Science & AI",
        "min_weeks": 1,
        "max_weeks": 2,
        "prerequisites": ["Python"],
        "learning_focus": [
            "Series and DataFrame data structures, vectorization, and index alignment",
            "Data filtering, conditional selection, and handling missing data (isna, fillna)",
            "Reshaping data: groupby aggregations, pivot tables, and sorting",
            "Combining datasets: concat, merge, and relational join operations",
        ],
        "practical_milestone": "Clean and aggregate a messy multi-file CSV dataset into structured summary tables with custom grouped metrics.",
    },
    "pytorch": {
        "canonical_name": "PyTorch",
        "category": "Data Science & AI",
        "min_weeks": 2,
        "max_weeks": 3,
        "prerequisites": ["Python"],
        "learning_focus": [
            "Tensor manipulation, dimensions, slicing, and automatic differentiation (autograd)",
            "Building neural network architectures using torch.nn.Module",
            "Training loops: forward pass, loss calculation, backward propagation, and optimizers",
            "Data loading pipelines using Dataset and DataLoader abstractions",
        ],
        "practical_milestone": "Implement and train a deep neural network on image or text embeddings with a modular DataLoader and loss logging.",
    },
    "rest apis": {
        "canonical_name": "REST APIs",
        "category": "Framework & Library",
        "min_weeks": 1,
        "max_weeks": 2,
        "prerequisites": [],
        "learning_focus": [
            "REST architectural constraints: statelessness, client-server, and uniform interfaces",
            "HTTP methods semantics (GET, POST, PUT, PATCH, DELETE) and resource naming",
            "HTTP status codes (2xx, 4xx, 5xx) and structured error response design",
            "Request headers, query parameters, pagination strategies, and JSON payloads",
        ],
        "practical_milestone": "Design and document a complete OpenAPI/REST resource specification with mock endpoints and pagination.",
    },
    "agile methodology": {
        "canonical_name": "Agile Methodology",
        "category": "Methodology & Tools",
        "min_weeks": 1,
        "max_weeks": 1,
        "prerequisites": [],
        "learning_focus": [
            "Agile Manifesto core principles and iterative development cycles",
            "Scrum framework: roles (Product Owner, Scrum Master), sprints, and daily standups",
            "Authoring user stories with clear acceptance criteria and story point estimation",
            "Sprint planning, backlog refinement, sprint retrospectives, and Kanban boards",
        ],
        "practical_milestone": "Create a sprint backlog with prioritized user stories, acceptance criteria, and estimation for a software feature.",
    },
    "technical writing": {
        "canonical_name": "Technical Writing",
        "category": "Soft Skills",
        "min_weeks": 1,
        "max_weeks": 1,
        "prerequisites": [],
        "learning_focus": [
            "Audience analysis: writing for software engineers vs project stakeholders",
            "Structuring developer documentation: setup guides, API references, and architecture docs",
            "Clarity, conciseness, formatting standards, and Markdown documentation best practices",
            "Documenting system trade-offs, changelogs, and viva presentation materials",
        ],
        "practical_milestone": "Author a comprehensive technical README and architecture walkthrough for an engineering project.",
    },
}


# =============================================================================
# Helper & Retrieval Functions
# =============================================================================
def get_skill_pedagogy(skill_name: str) -> Dict[str, Any]:
    """
    Retrieves verified pedagogical learning focus and milestones for a given skill.
    Uses canonical alias resolution via matcher.
    Falls back gracefully to a deterministic learning template for unknown custom skills.
    """
    clean_name = skill_name.strip() if skill_name else "Unspecified Skill"
    norm_name = normalize_skill_name(clean_name)
    display_name = get_canonical_display_name(clean_name)

    # 1. Look up in verified canonical knowledge base
    if norm_name in SKILL_KNOWLEDGE_BASE:
        kb_entry = SKILL_KNOWLEDGE_BASE[norm_name]
        return {
            "canonical_name": kb_entry["canonical_name"],
            "category": kb_entry["category"],
            "min_weeks": kb_entry["min_weeks"],
            "max_weeks": kb_entry["max_weeks"],
            "prerequisites": list(kb_entry.get("prerequisites", [])),
            "learning_focus": list(kb_entry["learning_focus"]),
            "practical_milestone": kb_entry["practical_milestone"],
        }

    # 2. Defensive fallback for uncatalogued custom skills (Deterministic template)
    return {
        "canonical_name": display_name,
        "category": "Technical Competency",
        "min_weeks": 1,
        "max_weeks": 2,
        "prerequisites": [],
        "learning_focus": [
            f"Core syntax, foundational architecture, and core paradigms of {display_name}",
            f"Development environment setup, modern tooling, and standard workflows for {display_name}",
            f"Key design patterns, error handling, and performance considerations in {display_name}",
            f"Automated testing, debugging workflows, and community best practices for {display_name}",
        ],
        "practical_milestone": f"Construct a standalone proof-of-concept project or module demonstrating practical application of {display_name}.",
    }


def format_duration_string(min_weeks: int, max_weeks: int) -> str:
    """
    Formats a duration range into an approximate self-study estimate string.
    Guarantees non-authoritative self-paced framing.
    """
    if min_weeks == max_weeks:
        week_str = "1 week" if min_weeks == 1 else f"{min_weeks} weeks"
    else:
        week_str = f"{min_weeks}–{max_weeks} weeks"
    return f"Approx. {week_str} (self-paced estimate)"


def order_skills_with_prerequisites(
    target_skills: List[str],
    possessed_skills_norm: Optional[Set[str]] = None,
    knowledge_base: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    Orders a collection of target skills such that explicit prerequisites
    precede dependent skills.

    Guarantees:
    - Only explicit prerequisites in SKILL_KNOWLEDGE_BASE (or provided knowledge_base) are evaluated.
    - If a prerequisite is ALREADY possessed by the student, it is not re-scheduled.
    - If both a prerequisite and dependent skill are missing, prerequisite comes first.
    - Cycle detection prevents infinite recursion or deadlocks.
    - Preserves stable deterministic ordering.
    """
    if possessed_skills_norm is None:
        possessed_skills_norm = set()

    # 1. Deduplicate target skills preserving initial order
    unique_skills: List[str] = []
    seen_target_norms: Set[str] = set()

    for s in target_skills:
        if not s or not s.strip():
            continue
        norm = normalize_skill_name(s)
        if norm and norm not in seen_target_norms:
            seen_target_norms.add(norm)
            unique_skills.append(get_canonical_display_name(s))

    if not unique_skills:
        return []

    # 2. Build dependency graph for target skills
    # graph[u] = list of skills that must be learned BEFORE u
    dependencies: Dict[str, List[str]] = {}
    skill_norm_to_display: Dict[str, str] = {}

    for display_name in unique_skills:
        norm = normalize_skill_name(display_name)
        skill_norm_to_display[norm] = display_name
        if knowledge_base and norm in knowledge_base:
            pedagogy = knowledge_base[norm]
        else:
            pedagogy = get_skill_pedagogy(display_name)

        # Only consider prerequisites that are in target_skills AND not already possessed
        valid_prereqs = []
        for p in pedagogy.get("prerequisites", []):
            norm_p = normalize_skill_name(p)
            if norm_p not in possessed_skills_norm and norm_p in seen_target_norms:
                valid_prereqs.append(norm_p)

        dependencies[norm] = valid_prereqs

    # 3. Topological sort with cycle detection (DFS with 3 colors)
    # Colors: 0 = unvisited, 1 = visiting (in recursion stack), 2 = visited
    state: Dict[str, int] = {norm: 0 for norm in dependencies}
    ordered_norms: List[str] = []

    def dfs(node: str):
        state[node] = 1  # visiting
        for prereq in dependencies.get(node, []):
            if state.get(prereq, 0) == 1:
                # Cycle detected! Safely break cycle without looping
                continue
            elif state.get(prereq, 0) == 0:
                dfs(prereq)
        state[node] = 2  # visited
        ordered_norms.append(node)

    for norm in dependencies:
        if state[norm] == 0:
            dfs(norm)

    # ordered_norms now has prerequisites before dependents
    # Map back to canonical display names
    return [skill_norm_to_display[n] for n in ordered_norms if n in skill_norm_to_display]


# =============================================================================
# Transitive Prerequisite Expansion & Priority Inheritance
# =============================================================================
@dataclass
class SkillPlanNode:
    """
    Internal tracking node for prerequisite expansion and priority inheritance.
    """
    canonical_name: str
    is_employer_target: bool            # True if listed by employer, False if injected
    is_mandatory: bool                  # True = High Priority, False = Medium Priority
    prerequisite_for: Set[str] = field(default_factory=set) # Skills that depend on this prerequisite


def expand_skill_prerequisites(
    student_skills: List[Union[str, StudentSkill, Dict[str, Any]]],
    required_skills: List[str],
    preferred_skills: Optional[List[str]] = None,
    knowledge_base: Optional[Dict[str, Any]] = None,
) -> Tuple[List[str], List[str], Dict[str, SkillPlanNode]]:
    """
    Recursively expands employer-declared missing required and preferred skills
    with their explicit prerequisites from SKILL_KNOWLEDGE_BASE.

    Guarantees:
    - Recursively resolves transitive prerequisites (e.g. A -> B -> C).
    - If a student already possesses a prerequisite, it is excluded.
    - If a prerequisite is already an employer target, it is not duplicated.
    - If a prerequisite supports a required skill, it inherits Mandatory priority.
    - If a prerequisite supports both required and preferred skills, Mandatory priority wins.
    - If a prerequisite supports only preferred skills, it retains Preferred priority.
    - Cycle detection prevents infinite recursion.
    - Deduplicates identical skills and preserves canonical names.

    Returns:
        (ordered_mandatory_skills, ordered_preferred_skills, plan_nodes_dict)
    """
    preferred_skills = preferred_skills or []

    # 1. Normalize student possessed skills
    possessed_norms: Set[str] = set()
    for item in student_skills:
        name = ""
        if isinstance(item, StudentSkill):
            name = item.skill_name
        elif isinstance(item, str):
            name = item
        elif isinstance(item, dict):
            name = item.get("name", "") or item.get("skill_name", "")
        norm = normalize_skill_name(name)
        if norm:
            possessed_norms.add(norm)

    # 2. Extract employer-declared missing required and preferred skills
    seen_req_norms: Set[str] = set()
    employer_missing_required: List[str] = []
    for r in required_skills:
        norm_r = normalize_skill_name(r)
        if not norm_r or norm_r in seen_req_norms:
            continue
        seen_req_norms.add(norm_r)
        if norm_r not in possessed_norms:
            employer_missing_required.append(get_canonical_display_name(r))

    seen_pref_norms: Set[str] = set()
    employer_missing_preferred: List[str] = []
    for p in preferred_skills:
        norm_p = normalize_skill_name(p)
        if not norm_p or norm_p in seen_req_norms or norm_p in seen_pref_norms:
            continue
        seen_pref_norms.add(norm_p)
        if norm_p not in possessed_norms:
            employer_missing_preferred.append(get_canonical_display_name(p))

    # 3. Initialize plan nodes
    plan_nodes: Dict[str, SkillPlanNode] = {}

    for req_name in employer_missing_required:
        norm = normalize_skill_name(req_name)
        plan_nodes[norm] = SkillPlanNode(
            canonical_name=req_name,
            is_employer_target=True,
            is_mandatory=True,
        )

    for pref_name in employer_missing_preferred:
        norm = normalize_skill_name(pref_name)
        plan_nodes[norm] = SkillPlanNode(
            canonical_name=pref_name,
            is_employer_target=True,
            is_mandatory=False,
        )

    # 4. Recursive expansion helper
    def expand_prereqs(dependent_norm: str, is_mandatory: bool, dependent_display: str, visited_path: Set[str]):
        if knowledge_base and dependent_norm in knowledge_base:
            prereqs = knowledge_base[dependent_norm].get("prerequisites", [])
        else:
            pedagogy = get_skill_pedagogy(dependent_norm)
            prereqs = pedagogy.get("prerequisites", [])

        for prereq_str in prereqs:
            norm_p = normalize_skill_name(prereq_str)
            if not norm_p:
                continue
            # Exclude already possessed prerequisites
            if norm_p in possessed_norms:
                continue
            # Cycle detection on expansion path
            if norm_p in visited_path:
                continue

            canonical_p = get_canonical_display_name(prereq_str)

            if norm_p in plan_nodes:
                plan = plan_nodes[norm_p]
                plan.prerequisite_for.add(dependent_display)
                # If current branch is mandatory, but node was preferred, upgrade it!
                if is_mandatory and not plan.is_mandatory:
                    plan.is_mandatory = True
                    # Propagate mandatory upgrade to its prerequisites
                    expand_prereqs(norm_p, True, plan.canonical_name, visited_path | {norm_p})
            else:
                # Injected prerequisite
                new_plan = SkillPlanNode(
                    canonical_name=canonical_p,
                    is_employer_target=False,
                    is_mandatory=is_mandatory,
                )
                new_plan.prerequisite_for.add(dependent_display)
                plan_nodes[norm_p] = new_plan
                # Recursively expand this newly injected prerequisite
                expand_prereqs(norm_p, is_mandatory, canonical_p, visited_path | {norm_p})

    for req_name in employer_missing_required:
        norm = normalize_skill_name(req_name)
        expand_prereqs(norm, True, req_name, {norm})

    for pref_name in employer_missing_preferred:
        norm = normalize_skill_name(pref_name)
        expand_prereqs(norm, False, pref_name, {norm})

    # 5. Partition candidate skills into foundations (prereqs) and targets
    mandatory_foundations = [p.canonical_name for p in plan_nodes.values() if p.is_mandatory and p.prerequisite_for]
    mandatory_targets = [p.canonical_name for p in plan_nodes.values() if p.is_mandatory and not p.prerequisite_for]
    mandatory_candidates = mandatory_foundations + mandatory_targets

    preferred_foundations = [p.canonical_name for p in plan_nodes.values() if not p.is_mandatory and p.prerequisite_for]
    preferred_targets = [p.canonical_name for p in plan_nodes.values() if not p.is_mandatory and not p.prerequisite_for]
    preferred_candidates = preferred_foundations + preferred_targets

    # 6. Topologically sort within each priority tier
    ordered_mandatory = order_skills_with_prerequisites(
        mandatory_candidates, possessed_norms, knowledge_base=knowledge_base
    )
    ordered_preferred = order_skills_with_prerequisites(
        preferred_candidates, possessed_norms, knowledge_base=knowledge_base
    )

    return ordered_mandatory, ordered_preferred, plan_nodes


# =============================================================================
# Core Roadmap Generation Engine
# =============================================================================
def generate_learning_roadmap(
    student_skills: List[Union[str, StudentSkill, Dict[str, Any]]],
    required_skills: List[str],
    preferred_skills: Optional[List[str]] = None,
    internship_id: int = 0,
    internship_title: str = "Target Internship",
    organization: str = "Target Organization",
    knowledge_base: Optional[Dict[str, Any]] = None,
) -> LearningRoadmap:
    """
    Generates a deterministic, prioritized, and prerequisite-aware learning roadmap.

    Prioritization:
    - Phase 1 & 2: Mandatory Missing Requirements & Injected Prerequisites (High Priority).
    - Phase 3: Preferred Bonus Opportunities & Injected Prerequisites (Medium Priority).
    - If 100% matched: Phase 1: Technical Interview & Portfolio Readiness (Optional).

    Returns:
        LearningRoadmap dataclass instance.
    """
    preferred_skills = preferred_skills or []

    # 1. Expand missing target skills with transitive prerequisites
    ordered_mandatory, ordered_preferred, plan_nodes = expand_skill_prerequisites(
        student_skills=student_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        knowledge_base=knowledge_base,
    )

    # 2. Handle Fully Qualified Candidate (0 Missing Skills)
    if not ordered_mandatory and not ordered_preferred:
        interview_step = RoadmapStep(
            step_number=1,
            skill_name="Technical Interview & Portfolio Readiness",
            priority="Optional (Interview Readiness)",
            phase="Preparation: Technical Interview Readiness",
            estimated_duration="Approx. 1–2 weeks (self-paced estimate)",
            learning_focus=[
                "Review system design principles, modular architecture, and clean code conventions",
                "Prepare in-depth technical walkthroughs for your best academic or personal projects",
                "Practice explaining architectural trade-offs, testing methodologies, and debugging steps",
                "Formulate insightful technical questions about team engineering practices and stacks",
            ],
            practical_milestone="Conduct a mock technical interview and assemble an architectural project showcase highlighting your core competencies.",
            prerequisites=[],
            is_prerequisite=False,
            prerequisite_for=[],
            origin="Interview Preparation",
            rationale="Preparation milestone for interview-ready candidates who match all listed skills.",
        )
        return LearningRoadmap(
            internship_id=internship_id,
            internship_title=internship_title,
            organization=organization,
            total_steps=1,
            mandatory_steps_count=0,
            preferred_steps_count=0,
            injected_prerequisites_count=0,
            estimated_total_duration="Self-paced interview preparation",
            is_fully_qualified=True,
            steps=[interview_step],
        )

    steps: List[RoadmapStep] = []
    current_step_num = 1
    total_min_weeks = 0
    total_max_weeks = 0
    injected_count = 0

    # 3. Build Roadmap Steps for Mandatory Requirements & Injected Prerequisites
    for req_skill in ordered_mandatory:
        norm = normalize_skill_name(req_skill)
        node = plan_nodes[norm]
        pedagogy = knowledge_base[norm] if (knowledge_base and norm in knowledge_base) else get_skill_pedagogy(req_skill)
        duration_str = format_duration_string(pedagogy["min_weeks"], pedagogy["max_weeks"])
        total_min_weeks += pedagogy["min_weeks"]
        total_max_weeks += pedagogy["max_weeks"]

        is_prereq = not node.is_employer_target
        if is_prereq:
            injected_count += 1
            supporting_list = ", ".join(sorted(node.prerequisite_for))
            rationale = f"Supporting prerequisite for {supporting_list} — not explicitly listed by the employer."
            origin = "Injected Prerequisite"
            phase = "Phase 1: Critical Foundation"
        else:
            rationale = "Directly required by the employer."
            origin = "Employer Requirement"
            if node.prerequisite_for:
                phase = "Phase 1: Critical Foundation"
            else:
                phase = "Phase 2: Core Requirements" if len(ordered_mandatory) > 1 else "Phase 1: Mandatory Requirement"

        steps.append(RoadmapStep(
            step_number=current_step_num,
            skill_name=pedagogy["canonical_name"],
            priority="High (Mandatory Requirement)",
            phase=phase,
            estimated_duration=duration_str,
            learning_focus=pedagogy["learning_focus"],
            practical_milestone=pedagogy["practical_milestone"],
            prerequisites=pedagogy["prerequisites"],
            is_prerequisite=is_prereq,
            prerequisite_for=sorted(list(node.prerequisite_for)),
            origin=origin,
            rationale=rationale,
        ))
        current_step_num += 1

    # 4. Build Roadmap Steps for Preferred Bonus Opportunities & Injected Prerequisites
    for pref_skill in ordered_preferred:
        norm = normalize_skill_name(pref_skill)
        node = plan_nodes[norm]
        pedagogy = knowledge_base[norm] if (knowledge_base and norm in knowledge_base) else get_skill_pedagogy(pref_skill)
        duration_str = format_duration_string(pedagogy["min_weeks"], pedagogy["max_weeks"])
        total_min_weeks += pedagogy["min_weeks"]
        total_max_weeks += pedagogy["max_weeks"]

        is_prereq = not node.is_employer_target
        if is_prereq:
            injected_count += 1
            supporting_list = ", ".join(sorted(node.prerequisite_for))
            rationale = f"Supporting prerequisite for {supporting_list} — not explicitly listed by the employer."
            origin = "Injected Prerequisite"
        else:
            rationale = "Preferred bonus competency listed by the employer."
            origin = "Employer Preferred"

        steps.append(RoadmapStep(
            step_number=current_step_num,
            skill_name=pedagogy["canonical_name"],
            priority="Medium (Growth Opportunity)",
            phase="Phase 3: Growth Opportunities",
            estimated_duration=duration_str,
            learning_focus=pedagogy["learning_focus"],
            practical_milestone=pedagogy["practical_milestone"],
            prerequisites=pedagogy["prerequisites"],
            is_prerequisite=is_prereq,
            prerequisite_for=sorted(list(node.prerequisite_for)),
            origin=origin,
            rationale=rationale,
        ))
        current_step_num += 1

    total_duration_str = format_duration_string(total_min_weeks, total_max_weeks)

    return LearningRoadmap(
        internship_id=internship_id,
        internship_title=internship_title,
        organization=organization,
        total_steps=len(steps),
        mandatory_steps_count=len(ordered_mandatory),
        preferred_steps_count=len(ordered_preferred),
        injected_prerequisites_count=injected_count,
        estimated_total_duration=total_duration_str,
        is_fully_qualified=False,
        steps=steps,
    )


# =============================================================================
# High-Level Convenience Wrappers
# =============================================================================
def generate_roadmap_for_internship(
    student: Student,
    internship: Internship,
) -> LearningRoadmap:
    """
    Convenience wrapper to generate a learning roadmap from Student and Internship dataclasses.
    """
    return generate_learning_roadmap(
        student_skills=student.skills,
        required_skills=internship.required_skills,
        preferred_skills=internship.preferred_skills,
        internship_id=internship.id or 0,
        internship_title=internship.title,
        organization=internship.organization,
    )


def generate_roadmap_from_gap_report(
    gap_report: SkillGapReport,
    student_skills: List[Union[str, StudentSkill, Dict[str, Any]]],
    internship_id: int = 0,
    internship_title: str = "Target Internship",
    organization: str = "Target Organization",
) -> LearningRoadmap:
    """
    Convenience wrapper to generate a learning roadmap directly from a pre-computed SkillGapReport.
    """
    return generate_learning_roadmap(
        student_skills=student_skills,
        required_skills=gap_report.matched_required_skills + gap_report.missing_required_skills,
        preferred_skills=gap_report.matched_preferred_skills + gap_report.missing_preferred_skills,
        internship_id=internship_id,
        internship_title=internship_title,
        organization=organization,
    )

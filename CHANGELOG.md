# Changelog

All notable changes, architectural decisions, and bug investigations for the **Public Internship Discovery and Skill-Gap Recommendation Engine** are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.8.1] - 2026-11-16
### Added & Verified - Milestone 8.1: Environment-Based Semantic AI Toggle & Memory Optimization

#### Environment Configuration (`app/config.py`)
- **Robust Environment Variable Parser:** Added `parse_bool_env(var_name: str, default: bool = True) -> bool` handling truthy values (`"true"`, `"1"`, `"yes"`, `"on"`, `"t"`) and falsy values (`"false"`, `"0"`, `"no"`, `"off"`, `"f"`), case-insensitively, raising a clear `ValueError` on malformed inputs to prevent silent misconfiguration.
- **Dynamic Helper Function:** Implemented `is_semantic_ai_enabled() -> bool` reading `ENABLE_SEMANTIC_AI` dynamically at runtime, ensuring test mocks and container environments can toggle behavior cleanly without requiring process restarts.
- **Backwards-Compatible Constant:** Exported `ENABLE_SEMANTIC_AI: bool` reflecting the initial environment state.

#### Zero-Import Memory Isolation (`app/engine/semantic.py`)
- **Lazy-Load Import Guard:** Short-circuited `SemanticEngine.get_model()` before line 64 (`from sentence_transformers import SentenceTransformer`). When `is_semantic_ai_enabled()` returns `False`, `sentence_transformers` and `torch` are never imported into `sys.modules`.
- **Method-Level Defense:** Updated `encode_text()` and `encode_valid_text()` to short-circuit immediately when semantic AI is disabled, preventing accidental vector lookups or computations.
- **Availability Helper:** Added `SemanticEngine.is_available() -> bool` and exported `is_semantic_available() -> bool` in `app/engine/__init__.py`.
- **Memory Footprint Reduction:** Measured local heap memory via `tracemalloc`: reduced heap memory from $\sim 320\text{ MB}$ down to $\sim 20\text{ MB}$, completely eliminating the 512 MB RAM ceiling risk on Render Free.

#### Transparent Fallback Scoring (`app/engine/scorer.py`)
- **Configuration-Aware Fallback:** Added early check in `calculate_semantic_similarity_score()`. When disabled, sets:
  - `fallback_applied = True`
  - `fallback_reason = "Semantic AI disabled via configuration (ENABLE_SEMANTIC_AI=False)."`
  - `qualitative_label = "Disabled via configuration"`
  - `points = 0.0`, `max_points = 0.0`, `weight = 0.0`
- **Dynamic Weight Rebalancing:** Automatically activates the 4-factor heuristic baseline ($45\%$ required, $15\%$ preferred, $20\%$ academic, $20\%$ location, $0\%$ semantic), ensuring total scores remain bounded strictly between $0.0$ and $100.0$.
- **Hard Gatekeeper Preservation:** Preserved strict eligibility gatekeeper enforcement, canonical skill normalization, and prerequisite DAG learning roadmap generation.

#### Full Transparency & Frontend Integration (`app/engine/explainer.py`, `app/static/js/dashboard.js`)
- **Auditable Explanations:** Recommendation Explainer details explicit reason for fallback rebalancing in `fallback_summary` and marks semantic AI impact as `Zero Contribution`.
- **Ethical UI Rendering:** Discovery Dashboard renders `Fallback Active: Scored with 4 Baseline Heuristic Weights` without fabricating cosine similarities or misleading percentage matches.

#### Automated Test Suite Expansion (164 Tests)
- **Semantic Engine Tests (`tests/test_semantic.py`):** Added 5 unit tests verifying `parse_bool_env` defaults, truthy/falsy parsing, invalid value rejection, model bypass under `ENABLE_SEMANTIC_AI=false`, and zero `SentenceTransformer` imports.
- **Scorer Tests (`tests/test_scorer.py`):** Added 2 unit tests verifying baseline weight rebalancing and end-to-end multi-internship recommendation sorting under disabled configuration.
- **API Tests (`tests/test_api.py`):** Added 1 integration test verifying `POST /api/recommend` returns accurate fallback breakdown and explanation under disabled configuration.
- **Total Test Count:** Suite expanded to **164 tests** across 10 modules, all passing in $17.26\text{s}$.

---

## [0.7.5] - 2026-11-16
### Added & Verified - UI/UX Redesign: Milestones A, B, and C

#### Milestone A: Dedicated Opportunity Catalog (`/internships`)
- **Web View Route (`app/routes/views.py`):** Added `GET /internships` endpoint serving `templates/internships.html`.
- **Global Navigation Bar (`app/templates/base.html`):** Added "Internships" navigation link with active state highlighting.
- **Dedicated Browsing Interface (`app/templates/internships.html`):**
  - Instant client-side search input filtering by title, organization, and department.
  - Interactive work-mode filter pills (`All`, `Remote`, `Hybrid`, `Onsite`) with real-time count badges.
  - "Clear Filters" action button and empty-state reset.
  - Specifications grid highlighting stipend, min CGPA, graduation years, work mode, and location.
  - Expandable opportunity detail drawer disclosing description, key responsibilities, and hard gatekeeper eligibility criteria.
  - Student context bar enabling selection of a registered student to unlock a *"View Recommendations"* deep-link (`/?student_id=X`), preserving backend recommendation scoring without duplicating code.
- **Client Controller (`app/static/js/internships.js`):** Modular client-side architecture with safe DOM construction, accessible drawer toggles (`aria-expanded`, `aria-controls`), and filter state management.

#### Milestone B: Dashboard Redesign & Progressive Disclosure (`/`)
- **Compact Profile Context Bar (`app/templates/dashboard.html`):** Replaced 350px static details grid with a clean horizontal `.student-compact-bar` displaying candidate name, major, CGPA, graduation year, work mode, location, and a concise pill counter, with an easily accessible *"Edit Profile"* link to `/profile`. All original student metadata DOM IDs preserved.
- **Qualitative Match Tiers:**
  - Added visual match tier badges on recommendation cards:
    - `Strong Match` (Score $\ge 75$) - Emerald Green
    - `Moderate Match` (Score $\ge 50$) - Sky Blue
    - `Partial Match` (Score $> 0$) - Slate Gray
    - `Disqualified` (Score $= 0$) - Crimson Red
- **Always-Visible Driver Insights:** Prominently featured the explanation headline and top-scoring driver badges directly on the card face.
- **Progressive Disclosure Accordion Drawers:**
  - Factor Attribution Drawer: Collapsible panel containing the 5 scoring factor progress bars, point attributions, impact badges, and semantic AI metrics.
  - 4-Tier Skill Gaps Drawer: Collapsible panel organizing skills into matched required, missing required (profile omissions), matched preferred, and missing preferred.
- **Concise Roadmap Summary Card:** Replaced long inline timeline nodes with an actionable summary card showing self-study duration, step counts, and a direct button to launch the full learning roadmap modal.
- **Ineligible Listing Card Improvements:** Maintained hard gatekeeper exclusion reasons and educational-only roadmap modal access.

#### Milestone C: Accessibility Compliance, Visual Polish & Documentation
- **WAI-ARIA Modal Dialog Accessibility (`app/static/js/dashboard.js`):**
  - Shifted initial keyboard focus to `#closeRoadmapModalBtn` upon dialog open.
  - Implemented WAI-ARIA focus trap on `Tab` and `Shift+Tab` cycling focus strictly within focusable dialog elements.
  - Clean `Escape` key and backdrop click dismissal.
  - Implemented focus restoration, programmatically returning focus to the exact button (`lastActiveTrigger`) that opened the modal dialog.
- **Accessible State Toggles (`app/static/js/internships.js`, `app/static/js/dashboard.js`):**
  - Exposed `aria-expanded="true/false"` and `aria-controls="<drawer-id>"` across all factor drawers, skill-gap drawers, step drawers, and catalog detail drawers.
  - Exposed `role="group"` and `aria-pressed="true/false"` on work-mode filter pills.
- **High-Contrast Visible Focus Rings (`app/static/css/styles.css`):**
  - Applied `:focus-visible` styling (`outline: 2px solid var(--primary); outline-offset: 2px;`) across all buttons, links, inputs, selects, and textareas.
- **Responsive Multi-Device Layout:**
  - Added media query rules for tablet ($768\text{px}$) and mobile ($480\text{px}$) viewports.
  - Stacked filter toolbars and search inputs vertically on small screens.
  - Ensured card action buttons, modal dialogs, and navigation links wrap cleanly with zero horizontal overflow.
- **Automated Test Suite Expansion (`tests/test_views.py`):**
  - Added view integration tests covering catalog rendering, compact profile bar elements, and CSS responsive/accessibility classes.
  - Project test suite expanded to **156 tests** across 10 test modules, all passing.
- **Documentation Updates:**
  - Synchronized `README.md`, `LEARNING_GUIDE.md`, and `CHANGELOG.md` with complete 3-page architecture, progressive disclosure concepts, WAI-ARIA accessibility compliance, and viva examination preparation.

---

## [0.7.4] - 2026-11-15
### Added & Verified - Milestone 7.4: Frontend Integration for Explanations and Learning Roadmaps

#### Recommendation Explanation UI (`app/static/js/dashboard.js`, `app/static/css/styles.css`)
- **Headline & Top Drivers Rendering:**
  - Rendered backend-generated `rec.explanation.headline` prominently on each eligible recommendation card.
  - Highlighted primary scoring drivers (`strongest_factors`) with distinctive badges (`★ Factor Name`).
- **Expandable Factor Attribution Breakdown:**
  - Added collapsible accordion toggle (`View Factor Attribution & Score Breakdown ▼`).
  - Rendered each scoring factor with display name, weight percentage, points earned vs maximum points, and qualitative impact badge:
    - `"High Positive Impact"` (green badge)
    - `"Moderate Positive Impact"` (blue/cyan badge)
    - `"Low Positive Impact"` (slate badge)
    - `"Zero Contribution"` (light gray badge)
  - Color-coded progress bars matching factor impact tiers.
  - Displayed factual plain-language factor summaries from backend.
  - Transparently disclosed semantic AI metadata (qualitative alignment tier, raw cosine similarity to 4 decimals, and non-probability notices) and dynamic fallback notices.
- **Ethical Profile Framing:**
  - Integrated ethical notice on each card: *"Recommendations are evaluated strictly on declared profile information. Missing skills reflect profile omissions, not a confirmed lack of personal ability or potential."*

#### 4-Category Skill-Gap Visualization
- Explicitly separated skills into 4 distinct visual categories:
  1. **Matched Mandatory Skills** (`pill-matched-req`)
  2. **Critical Gaps (Missing Mandatory — Profile Omissions)** (`pill-missing-req`)
  3. **Matched Preferred Bonus Skills** (`pill-matched-pref`)
  4. **Growth Areas (Missing Preferred)** (`pill-missing-pref`)
- Labeled missing competencies as profile omissions, avoiding judgmental assumptions.

#### Learning Roadmap UI & Vertical Timeline
- **Embedded Roadmap Accordion:**
  - Added expandable timeline container inside eligible recommendation cards (`View Learning Roadmap (X Steps) ▼`).
  - Rendered summary bar: total estimated self-study duration, step counts (mandatory vs. preferred), and injected prerequisite count.
- **Vertical Timeline Nodes:**
  - Numbered step markers with distinct styling for injected prerequisites (`timeline-step-marker-injected`).
  - Rendered skill name, pedagogical phase badge (`badge-phase`), priority tier (`badge-priority-high`, `badge-priority-med`, `badge-priority-opt`), and origin badge.
  - Transitively injected supporting prerequisites prominently badged with purple pill (`badge-injected: Supporting Prerequisite`).
  - Displayed approximate self-study durations and human-readable pedagogical rationales.
  - Nested expand/collapse controls for step details: bulleted technical focus topics and concrete hands-on project milestones (`🎯 Practical Milestone`).

#### Dedicated Roadmap Modal Dialog (`app/templates/dashboard.html`, `app/static/js/api.js`, `app/static/js/dashboard.js`)
- Added accessible dialog markup (`role="dialog"`, `aria-modal="true"`) to `dashboard.html`.
- Implemented `API.getRoadmap(studentId, internshipId)` in `api.js`.
- Added modal trigger buttons to both eligible cards and ineligible listings.
- Handled loading spinner, error states, and responsive scrolling for mobile and desktop screens.
- **Educational Context for Ineligible Pairings:**
  - When opened for an ineligible student-internship pair, displays an educational warning callout:
    *"Educational Learning Plan: The candidate does not currently meet one or more mandatory eligibility requirements for this position. This curriculum is provided for self-study and skill growth only; learning these competencies does not confer eligibility."*
  - Lists explicit gatekeeper rejection reasons alongside the learning roadmap.
- Accessible modal behavior: close button, click-outside-to-dismiss, and `Escape` key shortcut.

#### Automated Testing Suite (`tests/test_views.py`)
- Added tests verifying modal dialog markup rendering and CSS stylesheet Milestone 7 classes.
- Full project test suite expanded to **150 tests** across 10 test modules, all passing.

---

## [0.7.3] - 2026-11-15
### Added & Verified - Milestone 7.3: API Integration for Explanations and Learning Roadmaps

#### In-Memory Result Models (`app/models/results.py`)
- **`RecommendationResult` Model Enhancement:**
  - Extended dataclass with `roadmap: Optional['LearningRoadmap'] = None`.
  - Updated `RecommendationResult.to_dict()` to include `"roadmap": self.roadmap.to_dict() if self.roadmap else None`.
  - Preserved full backwards compatibility with all previous positional instantiations.

#### Scoring Engine Integration (`app/engine/scorer.py`)
- Integrated `generate_roadmap_for_internship` from `app.engine.roadmap` into `score_internship`:
  - Eligible recommendations automatically attach a fully sequenced, prerequisite-aware `LearningRoadmap`.
  - Ineligible listings explicitly set `rec.roadmap = None` to avoid conflating hard academic disqualifications with actionable skill roadmaps in the recommendation feed.

#### REST API Endpoints Integration (`app/routes/api.py`)
- **Enhanced `/api/recommend` (POST):**
  - Updated response payload to deliver both `explanation` and `roadmap` objects alongside existing legacy fields (`student_id`, `internship_id`, `internship_title`, `organization`, `eligibility`, `total_score`, `score_breakdown`, `skill_gaps`, `is_demo`).
  - Strict preservation of all existing response structures ensures zero breakage for existing API clients.
- **Dedicated Personalized Roadmap Endpoints (GET):**
  - Implemented RESTful path routes:
    - `GET /api/students/<student_id>/roadmap/<internship_id>`
    - `GET /api/students/<student_id>/roadmaps/<internship_id>`
  - Implemented query parameter routes:
    - `GET /api/roadmap?student_id=X&internship_id=Y`
    - `GET /api/roadmaps?student_id=X&internship_id=Y`
  - Defensive Validation & Error Handling:
    - `400 Bad Request` if `student_id` or `internship_id` are non-numeric or non-positive integers.
    - `404 Not Found` if either student or internship record is not found in SQLite.
    - Parameterized SQL execution (`SELECT ... WHERE id = ?;`).
    - Robust handling of ineligible student-internship pairings: returns `200 OK` with `"is_eligible": false`, explicit gatekeeper rejection reasons, and the complete pedagogical learning roadmap so candidates can study required competencies.

#### Automated Testing Suite (`tests/test_api.py`)
- Added 11 new integration tests (bringing `test_api.py` to 30 tests and total suite to **148 tests**):
  1. `test_recommend_endpoint_includes_explanation`: Verifies `explanation` payload and factor breakdown.
  2. `test_recommend_endpoint_retains_all_existing_fields`: Verifies all 9 legacy response fields are preserved.
  3. `test_recommend_endpoint_returns_roadmap_for_eligible`: Verifies roadmap for eligible and `None` for ineligible.
  4. `test_dedicated_roadmap_endpoint_success`: Verifies path, plural alias, and query param routes.
  5. `test_dedicated_roadmap_injected_prerequisites_serialization`: Verifies serialized injected prerequisites (e.g. SQL before PostgreSQL).
  6. `test_dedicated_roadmap_invalid_student_id_returns_400`: Verifies string and negative ID validation.
  7. `test_dedicated_roadmap_invalid_internship_id_returns_400`: Verifies string and zero ID validation.
  8. `test_dedicated_roadmap_missing_student_or_internship_returns_404`: Verifies missing student or internship handling.
  9. `test_dedicated_roadmap_empty_skills_student`: Verifies defensive execution when profile skills are empty.
  10. `test_dedicated_roadmap_ineligible_internship_handling`: Verifies 200 response with `is_eligible: false` and roadmap.
  11. `test_recommend_semantic_fallback_handling`: Verifies fallback summary and weight rebalancing description in API.

---

## [0.7.2] - 2026-11-15
### Added & Verified - Milestone 7.2: Recommendation Explanation and Rationale Engine

#### In-Memory Explanation Result Models (`app/models/results.py`)
- **`FactorExplanation` Dataclass:**
  - Encapsulates transparent, auditable attribution for each recommendation scoring dimension.
  - Fields: `factor_key` (e.g. `required_skills`, `semantic_similarity`), `display_name` (e.g. `"Mandatory Required Skills"`), `points_earned` (0.0 to `max_points`), `max_points`, `weight_percentage`, `impact_level` (`"High Positive Impact"`, `"Moderate Positive Impact"`, `"Low Positive Impact"`, `"Zero Contribution"`, `"Disqualified"`), `summary` (plain-language explanation), `details` (structured metadata), and `is_strongest_factor` (boolean flag).
  - Includes `to_dict()` serialization.
- **`RecommendationExplanation` Dataclass:**
  - Encapsulates the complete rationale payload synthesized for an internship recommendation.
  - Fields: `internship_id`, `internship_title`, `organization`, `total_score`, `is_eligible`, `headline` (high-level takeaway), `eligibility_summary` (isolated gatekeeper exclusion reasons if disqualified), `fallback_summary` (isolated fallback notification if semantic AI was bypassed), `strongest_factors` (list of display names for driving factors), `factors` (mapping of factor keys to `FactorExplanation` objects), and `ethical_notice`.
  - Non-judgmental ethical notice: *"Ethical Notice: Recommendations are evaluated strictly on declared profile information. Missing skills reflect profile omissions, not a confirmed lack of personal ability or potential."*
  - Includes `to_dict()` serialization.
- **`RecommendationResult` Model Integration:**
  - Extended `RecommendationResult` with `explanation: Optional[RecommendationExplanation] = None`.
  - Updated `RecommendationResult.to_dict()` to include `"explanation": self.explanation.to_dict() if self.explanation else None`.

#### Rationale Engine Architecture (`app/engine/explainer.py`)
- **Factor Attribution & Plain-Language Explanations:**
  - `explain_required_skills`: Factual summary showing matched skills, match percentage, earned points, and profile omissions.
  - `explain_preferred_skills`: Factual summary of bonus points earned and omitted preferred skills.
  - `explain_academic_alignment`: Grounded in major relevance and CGPA margin above cutoff.
  - `explain_location_alignment`: Explains work mode (remote universality, hybrid compatibility, onsite) and location matching.
  - `explain_semantic_similarity`: Transparent disclosure of raw cosine similarity, qualitative alignment tier, point contribution, and non-probability disclaimer notice.
- **Deterministic Strongest Factor Identification (`identify_strongest_factors`):**
  - Filters strictly positive factor scores (`points_earned > 0.0`).
  - Handles ties objectively: if two or more factors earn equal top marks, all tied factors are marked with `is_strongest_factor = True` and listed in `strongest_factors`.
  - Factors earning 0.0 points are classified as `"Zero Contribution"` and are never designated as strongest.
- **Ethical Profile Absence Framing:**
  - Missing skills are described as *"Omitted from profile"* or *"Missing from profile"*, strictly prohibiting derogatory or negative framing such as "lacks ability" or "incompetent".
- **Hard Eligibility Gatekeeper Isolation:**
  - Ineligible candidates receive a score of strictly 0.0.
  - Explanations cleanly isolate gatekeeper rejection reasons in `eligibility_summary` without conflating them with recommendation points.
  - Recommendation factors are explicitly marked with `impact_level = "Disqualified"`.
- **Dynamic Semantic Fallback Transparency:**
  - If semantic AI is bypassed (`fallback_applied = True`), `fallback_summary` details the reason (e.g. zero vector, model offline) and documents the dynamic rebalancing to baseline heuristic weights (45% required, 15% preferred, 20% academic, 20% location).
- **Batch Processing (`explain_all_recommendations`):**
  - Attaches explanations across ranked recommendation batches cleanly.
- **Package Exports (`app/engine/__init__.py`):**
  - Exported `FactorExplanation`, `RecommendationExplanation`, `explain_recommendation`, `explain_all_recommendations`, `identify_strongest_factors`, and factor explainers.

#### Scoring Engine Integration (`app/engine/scorer.py`)
- Integrated `explain_recommendation` into `score_internship` so that every `RecommendationResult` (eligible or ineligible) automatically carries a complete, auditable explanation.

#### Automated Testing Suite (`tests/test_explainer.py`)
- Created 13 automated unit tests covering:
  1. Single strongest factor identification.
  2. Tied strongest factors without bias.
  3. Zero contribution factor exclusion.
  4. Impact level thresholds.
  5. Ineligible candidate gatekeeper isolation.
  6. Semantic AI transparency (raw cosine, qualitative label, notice).
  7. Semantic fallback explanation and rebalancing details.
  8. Ethical phrasing for missing competencies.
  9. Academic and location alignment explanation fidelity.
  10. Defensive handling of listings with zero required or preferred skills.
  11. Mathematical consistency between `ScoreBreakdown` and `FactorExplanation`.
  12. Serialization to JSON-ready dicts.
  13. Batch explanation via `explain_all_recommendations`.
- Total project test suite expanded to **137 tests** across 10 test modules, all passing.

---

## [0.7.1] - 2026-11-15
### Added & Verified - Milestone 7.1: Roadmap Engine & Result Models

#### In-Memory Result Models (`app/models/results.py`)
- **`RoadmapStep` Dataclass:**
  - Encapsulates an individual pedagogical learning milestone step.
  - Fields: `step_number`, `skill_name`, `priority` ("High (Mandatory Requirement)" vs "Medium (Growth Opportunity)" vs "Optional (Interview Readiness)"), `phase` ("Phase 1: Critical Foundation", "Phase 2: Core Requirements", "Phase 3: Growth Opportunities", "Preparation: Technical Interview Readiness"), `estimated_duration` ("Approx. X–Y weeks (self-paced estimate)"), `learning_focus` (list of key technical topics), `practical_milestone` (concrete project objective demonstrating applied competency), `prerequisites` (explicit prerequisites), `is_prerequisite` (boolean flag identifying injected supporting steps), `prerequisite_for` (list of dependent skill canonical names), `origin` ("Employer Requirement" vs "Injected Prerequisite" vs "Interview Preparation"), and `rationale` (human-readable explanation of step origin and purpose).
  - Includes `to_dict()` serialization.
- **`LearningRoadmap` Dataclass:**
  - Encapsulates the complete personalized learning roadmap for a student-internship pair.
  - Fields: `internship_id`, `internship_title`, `organization`, `total_steps`, `mandatory_steps_count`, `preferred_steps_count`, `injected_prerequisites_count`, `estimated_total_duration`, `is_fully_qualified`, `steps` (List[RoadmapStep]), and `ethical_notice`.
  - Non-prescriptive ethical notice: *"Ethical Notice: Missing profile skills indicate absence from the student profile, not a verified lack of ability. Learning durations are approximate self-study estimates, not guaranteed completion times."*
  - Includes `to_dict()` serialization.

#### Roadmap Engine Architecture (`app/engine/roadmap.py`)
- **Canonical Skill Pedagogical Knowledge Base (`SKILL_KNOWLEDGE_BASE`):**
  - Curated, deterministic learning definitions for all 21 canonical skills in the project taxonomy:
    `python`, `javascript`, `java`, `c++`, `sql`, `postgresql`, `mongodb`, `react`, `flask`, `node.js`, `html/css`, `docker`, `git`, `linux`, `data analysis`, `machine learning`, `pandas`, `pytorch`, `rest apis`, `agile methodology`, `technical writing`.
  - Each entry contains canonical display name, technical category, approximate self-paced duration range (weeks), explicit prerequisites, bulleted core learning concepts (3–5 topics), and a concrete hands-on project milestone.
- **Recursive Transitive Prerequisite Expansion (`expand_skill_prerequisites`):**
  - Automatically identifies missing foundational prerequisites for employer targets even when omitted from job postings (e.g. `SQL` for `PostgreSQL`, `JavaScript` & `HTML/CSS` for `React`).
  - Recursively resolves multi-level dependency chains ($A \to B \to C$).
  - Avoids re-scheduling prerequisites already possessed by the student.
  - Avoids duplicating prerequisites already declared as employer targets.
- **Priority Inheritance & Strongest Priority Rule:**
  - Injected prerequisites for mandatory requirements inherit `High (Mandatory Requirement)` priority.
  - Injected prerequisites for preferred skills inherit `Medium (Growth Opportunity)` priority.
  - Shared prerequisites supporting both tiers adopt `High (Mandatory Requirement)` priority.
- **Topological Sorting with Cycle Detection (`order_skills_with_prerequisites`):**
  - Directed Acyclic Graph (DAG) ordering with 3-color Depth-First Search (DFS: unvisited, visiting, visited).
  - Guarantees prerequisites precede dependent skills when both are missing.
  - Gracefully breaks cycles without infinite recursion or crashes if invalid or circular relationships are introduced.
- **Skill-Gap Separation Principle:**
  - Hard architectural decoupling: the employer-facing `SkillGapReport` (`app/engine/gap_analyzer.py`) continues auditing only declared employer requirements.
  - Recommendation scores and match percentages are never artificially inflated by injected supporting prerequisites.
- **Interview Readiness Guidance (`is_fully_qualified=True`):**
  - Students with 0 missing skills receive specialized technical interview and portfolio readiness preparation rather than an assumption that they have nothing left to learn.
- **Self-Paced Duration Formatting (`format_duration_string`):**
  - Explicit approximate framing (e.g., `"Approx. 1–2 weeks (self-paced estimate)"`). No promises or completion guarantees.
- **High-Level Wrappers:**
  - `generate_roadmap_for_internship(student, internship)`: Generates roadmap from dataclass entities.
  - `generate_roadmap_from_gap_report(gap_report, student_skills, ...)`: Generates roadmap directly from pre-computed `SkillGapReport`.
- **Package Exports (`app/engine/__init__.py`):**
  - Cleanly exported all new roadmap dataclasses and functions.

#### Automated Testing Suite (`tests/test_roadmap.py`)
- Expanded testing suite to 21 comprehensive unit tests covering:
  1. All 21 canonical skills present in `SKILL_KNOWLEDGE_BASE`.
  2. Scenario A prerequisite audit verification (SQL injected for PostgreSQL, JS/HTML injected for React).
  3. Possessed SQL correctly excluded from scheduling.
  4. Possessed Python correctly excluded for Flask.
  5. Both PostgreSQL and SQL explicitly listed (SQL once, before PostgreSQL, origin employer).
  6. Shared prerequisite (PyTorch and Flask both requiring Python scheduled once).
  7. Multi-level transitive prerequisite chain (A -> B -> C ordered C -> B -> A).
  8. Cycle safety in dependency graphs (X <-> Y no infinite recursion).
  9. Shared prerequisite priority inheritance (mandatory priority wins for PyTorch + Pandas).
  10. Preferred prerequisite priority preservation (JS/HTML for React remain preferred).
  11. Skill-gap analyzer independence (reports only employer targets).
  12. Interview readiness guidance for 100% matched students.
  13. Graceful fallback for unknown/custom skills.
  14. Deduplication of skill variations and aliases.
  15. Empty skills handling without errors.
  16. Zero-hallucination compliance (no external URLs, courses, or certificates).
  17. Approximate self-paced duration disclosure.
  18. Complete dictionary serialization with metadata (origin, rationale, is_prerequisite).
  19. Deterministic execution invariance.
  20. `generate_roadmap_for_internship` entity wrapper.
  21. `generate_roadmap_from_gap_report` report wrapper.
- Full automated test suite expanded from 103 to **124 passing tests** (0 failures, 0 errors).

---

## [0.6.5] - 2026-11-11
### Added & Verified - Milestone 6.5: Integrate Semantic AI into Internship Recommendations

#### Architectural Integration (`app/engine/scorer.py`, `app/engine/semantic.py`)
- **Deterministic Profile Text Synthesis (`build_student_semantic_text`, `build_internship_semantic_text`):**
  - Implemented structured text generators prioritizing primary technical competencies (claimed skills, required skills, preferred skills, core responsibilities).
  - Included secondary domain context (academic major, bio background, role title, employer organization) while avoiding corporate boilerplate and generic filler language.
  - Implemented substantive content guards: profiles without skills/bio and listings without skills/description return empty strings, triggering transparent fallback rebalancing.
- **Accurate Semantic Attribution & Non-Probability Terminology:**
  - Designed `calculate_semantic_similarity_score()` to compute raw cosine similarity, earned points, and qualitative alignment bands (`Strong`, `Moderate`, `Low`, `Minimal contextual alignment`).
  - Strict terminology guardrail: cosine similarity is never framed as a percentage match or skill possession metric.
  - Added non-probability notice to score breakdown: *"Semantic AI measures contextual and vocabulary alignment between profiles using all-MiniLM-L6-v2 embeddings. It does not certify individual skill competence."*
- **Mathematical Multi-Factor Weight Configurations (`app/config.py`):**
  - Semantic-Active Mode: 40% required skills, 15% preferred skills, 10% academic alignment, 10% location & mode match, 25% semantic AI alignment = 100%.
  - Baseline Heuristic Mode: 45% required skills, 15% preferred skills, 20% academic alignment, 20% location & mode match, 0% semantic AI alignment = 100%.
- **Robust Fallback Rebalancing:**
  - If model loading fails, vectors are invalid, or substantive text is missing, the engine falls back to baseline heuristic weights (45/15/20/20), flags `fallback_applied=True` with explicit `fallback_reason`, awards 0.0 semantic points, and normalizes total score to 100 points without crashing.
- **Strict Eligibility Gatekeeping Invariant:**
  - Hard gate check always runs first; ineligible opportunities score strictly 0.0 and NEVER invoke model inference or vector operations.
- **Frontend Dashboard Enhancements (`app/static/js/dashboard.js`):**
  - Updated score breakdown accordion to dynamically display 5 factors when semantic AI is active.
  - Renders earned points, progress track, raw cosine similarity, qualitative alignment badge, fallback warning (if active), and explanatory non-probability notice.
- **REST API Route Integration (`app/routes/api.py`):**
  - Updated `POST /api/recommend` to pass `use_semantic=True`, generating recommendations powered by the pretrained semantic model while returning fully transparent breakdown objects.

#### Automated Testing Suite
- Added 6 unit tests in `tests/test_scorer.py`:
  1. Active semantic scoring and point attribution.
  2. Conceptually related domain context outscoring unrelated context.
  3. Safe fallback rebalancing when student text lacks substantive content.
  4. Safe fallback rebalancing when model encoding returns `None`.
  5. Ineligible candidates strictly bypassing semantic encoding (0 mock calls).
  6. Mathematical score breakdown arithmetic exact sum (100.0 max points).
- Added 1 integration test in `tests/test_api.py`:
  - `test_recommend_endpoint_includes_semantic_breakdown`: verifies `POST /api/recommend` exposes all semantic metadata attributes.
- Full automated test suite expanded from 96 to **103 passing tests** (0 failures, 0 errors).

---

## [0.6.4] - 2026-11-11
### Added & Verified - Milestone 6.4: Semantic Engine Module & Embedding Cache

#### Architectural Implementation (`app/engine/semantic.py`)
- **Dedicated Semantic Engine Class (`SemanticEngine`):**
  - Encapsulates pretrained Transformer lifecycle using `sentence-transformers/all-MiniLM-L6-v2` strictly on CPU.
  - Implements offline-first model loading with `local_files_only=True` to eliminate redundant remote network calls.
  - Generates verified 384-dimensional dense vectors with numerical finiteness validation (no NaN or Inf coordinates).
- **In-Memory Embedding Cache (`_cache`):**
  - Implemented string-keyed vector cache in `SemanticEngine`. Repeated identical text bypasses Transformer forward passes entirely (0.0 ms cache hits).
  - Provided cache bypass (`use_cache=False`), cache inspection (`get_cache_size()`), and cache eviction (`clear_cache()`).
- **Mathematical Cosine Similarity (`compute_cosine_similarity`):**
  - Implemented mathematically bounded cosine similarity:
    $$\text{sim}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$$
  - Clamps output strictly within $[-1.0, 1.0]$. Zero vectors (from empty text or failed encodings) safely return `0.0` without division-by-zero errors.
- **Defensive Error Handling:**
  - Empty, `None`, or invalid non-string inputs safely return zero vectors of shape `(384,)`.
  - Model loading or encoding runtime exceptions are caught gracefully, logging warnings and returning zero vectors rather than crashing the web application.
- **Convenience API & Exports (`app/engine/__init__.py`):**
  - Exported `SemanticEngine`, `get_semantic_engine()`, `get_text_embedding()`, `cosine_similarity()`, and `text_similarity()`.

#### Testing & Verification (`tests/test_semantic.py`)
- Added 13 dedicated unit tests covering:
  1. Default initialization and CPU binding.
  2. Offline cached model loading.
  3. 384-dimensional shape and finite float values.
  4. Empty, None, and invalid input safety.
  5. Mathematical cosine similarity invariants (identical=1.0, orthogonal=0.0, opposite=-1.0, zero=0.0).
  6. Semantic ranking on benchmark sentences (ML vs Predictive Data $\gg$ Frontend HTML/CSS).
  7. Embedding cache hit detection and mock inference avoidance.
  8. Cache clearing and cache-bypass flags.
  9. Graceful degradation when model loading fails.
  10. Graceful degradation when model encoding raises runtime errors.
  11. Module-level convenience wrapper validation.
  12. Empty input handling in `text_similarity()`.
- Full automated test suite increased from 83 to **96 passing tests** (13 new tests).
- Scoring weights and recommendation logic untouched (`DEFAULT_SCORING_WEIGHTS` remains active).

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

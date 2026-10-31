"""
Application Configuration
Defines database paths, initial heuristic scoring weights, and system constants.
"""

from pathlib import Path
from typing import Dict

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "internship_engine.db"
SCHEMA_PATH = BASE_DIR / "app" / "models" / "schema.sql"

# Initial heuristic scoring weights
# ACADEMIC NOTE FOR EXAMINERS / VIVA:
# These weights represent initial design choices based on pedagogical prioritization.
# They are heuristic assumptions, NOT empirically trained on historical hiring outcomes,
# and should never be represented as actual hiring probabilities.
DEFAULT_SCORING_WEIGHTS: Dict[str, float] = {
    "required_skills": 0.45,       # 45% of score: Core mandatory skills listed by employer
    "preferred_skills": 0.15,      # 15% of score: Nice-to-have supplementary skills
    "academic_alignment": 0.20,    # 20% of score: Major match and academic performance
    "location_alignment": 0.20,    # 20% of score: Preferred work mode (Remote/Hybrid/Onsite)
    "semantic_similarity": 0.00,   # Deferred to Milestone 6 (will be 0.25 when activated)
}

# Future scoring weights configuration when Milestone 6 (Sentence Transformers) is integrated
SEMANTIC_ACTIVE_SCORING_WEIGHTS: Dict[str, float] = {
    "required_skills": 0.40,       # 40%
    "preferred_skills": 0.15,      # 15%
    "academic_alignment": 0.10,    # 10%
    "location_alignment": 0.10,    # 10%
    "semantic_similarity": 0.25,   # 25%: Genuine dense vector cosine similarity
}


def validate_weights(weights: Dict[str, float], tolerance: float = 1e-4) -> bool:
    """
    Validates that scoring weights sum to 1.0 within a floating point tolerance.
    """
    total = sum(weights.values())
    return abs(total - 1.0) <= tolerance

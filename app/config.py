"""
Application Configuration
Defines database paths, initial heuristic scoring weights, and system constants.
"""

import os
from pathlib import Path
from typing import Dict, Set

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "internship_engine.db"
SCHEMA_PATH = BASE_DIR / "app" / "models" / "schema.sql"

# Supported boolean representations for environment variables
TRUTHY_VALUES: Set[str] = {"true", "1", "yes", "on", "t"}
FALSY_VALUES: Set[str] = {"false", "0", "no", "off", "f"}


def parse_bool_env(var_name: str, default: bool = True) -> bool:
    """
    Parses a boolean environment variable with explicit validation.

    Supported truthy values (case-insensitive): 'true', '1', 'yes', 'on', 't'
    Supported falsy values (case-insensitive): 'false', '0', 'no', 'off', 'f'

    Args:
        var_name: The name of the environment variable.
        default: Default boolean value if the variable is unset or empty.

    Returns:
        bool: The parsed boolean value.

    Raises:
        ValueError: If the environment variable contains an invalid or unrecognized value.
    """
    raw_val = os.environ.get(var_name)
    if raw_val is None:
        return default
    cleaned = raw_val.strip().lower()
    if cleaned == "":
        return default
    if cleaned in TRUTHY_VALUES:
        return True
    if cleaned in FALSY_VALUES:
        return False

    valid_options = ", ".join(sorted(TRUTHY_VALUES | FALSY_VALUES))
    raise ValueError(
        f"Invalid boolean value '{raw_val}' for environment variable '{var_name}'. "
        f"Expected one of: {valid_options}."
    )


def is_semantic_ai_enabled() -> bool:
    """
    Dynamically checks whether semantic AI is enabled via the ENABLE_SEMANTIC_AI environment variable.
    Defaults to True if the variable is absent.
    """
    return parse_bool_env("ENABLE_SEMANTIC_AI", default=True)


# Default module-level constant for static inspection
ENABLE_SEMANTIC_AI: bool = is_semantic_ai_enabled()

# Semantic AI Configuration
SEMANTIC_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION: int = 384

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

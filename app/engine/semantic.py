"""
Pretrained Semantic AI & Vector Similarity Engine
=============================================================================
CRITICAL ARCHITECTURAL ROLE:
Provides dense vector embeddings and cosine-similarity evaluations using the
pretrained Transformer model `sentence-transformers/all-MiniLM-L6-v2`.

NON-NEGOTIABLE CORE INVARIANTS:
1. Strict Separation: Operates independently from the rule-based exact skill matcher
   (`app/engine/matcher.py`).
2. CPU Execution: Runs on standard CPU with no GPU or CUDA runtime dependencies.
3. Local Cache Priority: Loads model from local cache (`local_files_only=True`)
   to prevent redundant network requests and ensure offline reliability.
4. Embedding In-Memory Cache: Stores precomputed embeddings for identical text strings
   to avoid redundant neural network inference.
5. Defensive Graceful Degradation: If model loading or encoding fails, the engine
   fails safely by returning zero vectors and 0.0 similarity rather than crashing.
=============================================================================
"""

import logging
from typing import Optional, Dict, Any, Union
import numpy as np

from app.config import SEMANTIC_MODEL_NAME, EMBEDDING_DIMENSION, is_semantic_ai_enabled

logger = logging.getLogger(__name__)


class SemanticEngine:
    """
    Encapsulates pretrained Sentence Transformer model lifecycle, embedding generation,
    in-memory vector caching, and cosine-similarity computations.
    """

    def __init__(
        self,
        model_name: str = SEMANTIC_MODEL_NAME,
        device: str = "cpu",
        embedding_dim: int = EMBEDDING_DIMENSION,
    ):
        self.model_name = model_name
        self.device = device
        self.embedding_dim = embedding_dim
        self._model: Optional[Any] = None
        self._model_load_failed: bool = False
        self._cache: Dict[str, np.ndarray] = {}

    def get_model(self) -> Optional[Any]:
        """
        Lazily loads the SentenceTransformer model on CPU.
        Attempts to load from local cache first (offline mode). If that fails,
        falls back to standard download/load.
        
        Returns None if disabled via ENABLE_SEMANTIC_AI or if loading fails,
        setting a flag to avoid repeated crashes.
        """
        if not is_semantic_ai_enabled():
            logger.info("SemanticEngine: Semantic AI is disabled via ENABLE_SEMANTIC_AI environment variable.")
            return None

        if self._model is not None:
            return self._model

        if self._model_load_failed:
            return None

        try:
            from sentence_transformers import SentenceTransformer

            # Try loading from local offline cache first
            try:
                self._model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    local_files_only=True,
                )
                logger.info("SemanticEngine: Loaded %s from local cache.", self.model_name)
            except Exception as cache_err:
                logger.debug("SemanticEngine: Local cache load failed (%s); trying standard load.", cache_err)
                self._model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                )
                logger.info("SemanticEngine: Loaded %s via standard load.", self.model_name)

            return self._model

        except Exception as e:
            logger.warning("SemanticEngine: Failed to load model '%s': %s", self.model_name, e)
            self._model_load_failed = True
            return None

    def encode_text(self, text: Optional[str], use_cache: bool = True) -> np.ndarray:
        """
        Generates a 384-dimensional dense vector embedding for the input text.

        Guarantees:
        - If text is None, empty, whitespace-only, or not a string, returns a zero vector.
        - If use_cache is True, retrieves previously computed embeddings from in-memory cache.
        - If model loading fails, returns a zero vector defensively without raising exceptions.
        - Embeddings are guaranteed to be 1D numpy float32 arrays of length `embedding_dim`.
        """
        zero_vec = np.zeros(self.embedding_dim, dtype=np.float32)

        if not is_semantic_ai_enabled():
            logger.warning("SemanticEngine: Semantic AI disabled via configuration; returning zero vector.")
            return zero_vec

        if not text or not isinstance(text, str):
            return zero_vec

        cleaned = text.strip()
        if not cleaned:
            return zero_vec

        # Check in-memory cache
        if use_cache and cleaned in self._cache:
            return self._cache[cleaned].copy()

        model = self.get_model()
        if model is None:
            logger.warning("SemanticEngine: Model unavailable; returning zero vector.")
            return zero_vec

        try:
            # Generate embedding via SentenceTransformer
            raw_emb = model.encode(cleaned, convert_to_numpy=True, show_progress_bar=False)
            emb = np.asarray(raw_emb, dtype=np.float32).flatten()

            # Validate shape and finite numbers
            if emb.shape != (self.embedding_dim,) or not np.all(np.isfinite(emb)):
                logger.warning("SemanticEngine: Malformed embedding generated; returning zero vector.")
                return zero_vec

            if use_cache:
                self._cache[cleaned] = emb.copy()

            return emb

        except Exception as e:
            logger.warning("SemanticEngine: Encoding failed for text '%s...': %s", cleaned[:30], e)
            return zero_vec

    def encode_valid_text(self, text: Optional[str], use_cache: bool = True) -> Optional[np.ndarray]:
        """
        Validates input text and model availability, generating a verified non-zero embedding.

        Returns:
            1D float32 numpy array of shape (embedding_dim,) if text is valid AND
            model encoding succeeds with non-zero norm.
            Returns None if text is empty/invalid, model is unavailable, or encoding fails.
        """
        if not is_semantic_ai_enabled():
            return None

        if not text or not isinstance(text, str):
            return None

        cleaned = text.strip()
        if not cleaned:
            return None

        if use_cache and cleaned in self._cache:
            cached_emb = self._cache[cleaned]
            if cached_emb.shape == (self.embedding_dim,) and np.all(np.isfinite(cached_emb)) and float(np.linalg.norm(cached_emb)) > 1e-6:
                return cached_emb.copy()

        model = self.get_model()
        if model is None:
            return None

        try:
            raw_emb = model.encode(cleaned, convert_to_numpy=True, show_progress_bar=False)
            emb = np.asarray(raw_emb, dtype=np.float32).flatten()

            if emb.shape != (self.embedding_dim,) or not np.all(np.isfinite(emb)):
                return None

            norm = float(np.linalg.norm(emb))
            if norm <= 1e-6:
                return None

            if use_cache:
                self._cache[cleaned] = emb.copy()

            return emb

        except Exception as e:
            logger.warning("SemanticEngine: encode_valid_text failed for '%s...': %s", cleaned[:30], e)
            return None

    def compute_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Computes the cosine similarity between two 1D vector embeddings.

        Formula:
            sim(u, v) = (u . v) / (||u||_2 * ||v||_2)

        Guarantees:
        - Returns 0.0 if either vector is all zeros (e.g. from empty text).
        - Validates vector dimensions match.
        - Clamps the returned float strictly between -1.0 and 1.0.
        """
        if not isinstance(vec1, np.ndarray) or not isinstance(vec2, np.ndarray):
            return 0.0

        v1 = vec1.flatten()
        v2 = vec2.flatten()

        if v1.shape != (self.embedding_dim,) or v2.shape != (self.embedding_dim,):
            return 0.0

        if not (np.all(np.isfinite(v1)) and np.all(np.isfinite(v2))):
            return 0.0

        norm1 = float(np.linalg.norm(v1))
        norm2 = float(np.linalg.norm(v2))

        # Handle zero vectors (e.g. empty strings or failed embeddings)
        if norm1 <= 1e-9 or norm2 <= 1e-9:
            return 0.0

        dot_product = float(np.dot(v1, v2))
        similarity = dot_product / (norm1 * norm2)

        # Numerical clamping to [-1.0, 1.0]
        return float(np.clip(similarity, -1.0, 1.0))

    def similarity_between_texts(
        self,
        text1: Optional[str],
        text2: Optional[str],
        use_cache: bool = True,
    ) -> float:
        """
        Convenience method to directly calculate the semantic cosine similarity
        between two raw text strings.
        
        Returns a float between 0.0 and 1.0 for positive alignment, or 0.0 if empty.
        """
        if not text1 or not text2:
            return 0.0

        vec1 = self.encode_text(text1, use_cache=use_cache)
        vec2 = self.encode_text(text2, use_cache=use_cache)

        return self.compute_cosine_similarity(vec1, vec2)

    def clear_cache(self) -> None:
        """Clears the in-memory embedding cache."""
        self._cache.clear()

    def get_cache_size(self) -> int:
        """Returns the number of cached text embeddings."""
        return len(self._cache)

    def is_available(self) -> bool:
        """Returns True if semantic AI is enabled and operational."""
        if not is_semantic_ai_enabled():
            return False
        return not self._model_load_failed


# Global singleton instance for efficient application-wide reuse
_global_semantic_engine: Optional[SemanticEngine] = None


def get_semantic_engine() -> SemanticEngine:
    """
    Returns the process-wide singleton instance of SemanticEngine.
    """
    global _global_semantic_engine
    if _global_semantic_engine is None:
        _global_semantic_engine = SemanticEngine()
    return _global_semantic_engine


def is_semantic_available() -> bool:
    """
    Returns True if semantic AI is enabled and operational in the current environment.
    """
    if not is_semantic_ai_enabled():
        return False
    return get_semantic_engine().is_available()


def get_text_embedding(text: Optional[str], use_cache: bool = True) -> np.ndarray:
    """
    Convenience wrapper to get a 384-dimensional embedding for a text string.
    """
    return get_semantic_engine().encode_text(text, use_cache=use_cache)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Convenience wrapper to calculate cosine similarity between two vectors.
    """
    return get_semantic_engine().compute_cosine_similarity(vec1, vec2)


def text_similarity(text1: Optional[str], text2: Optional[str], use_cache: bool = True) -> float:
    """
    Convenience wrapper to calculate cosine similarity between two text strings.
    """
    return get_semantic_engine().similarity_between_texts(text1, text2, use_cache=use_cache)


def build_student_semantic_text(student: Any) -> str:
    """
    Constructs a deterministic, competency-focused textual representation of a student.
    Prioritizes claimed technical skills, followed by major and bio summary.
    Avoids generic filler language.

    Guard: If the student has neither technical skills nor a bio summary, returns an empty string
    so that safe fallback rebalancing triggers instead of encoding a non-technical major name.
    """
    raw_skills = getattr(student, "skills", []) or []
    skill_names = []
    for s in raw_skills:
        if hasattr(s, "skill_name") and s.skill_name:
            skill_names.append(s.skill_name.strip())
        elif isinstance(s, str) and s.strip():
            skill_names.append(s.strip())

    bio = str(getattr(student, "bio_summary", "") or "").strip()

    # Substantive content guard
    if not skill_names and not bio:
        return ""

    parts = []
    if skill_names:
        parts.append(f"Technical skills: {', '.join(skill_names)}")

    major = str(getattr(student, "major", "") or "").strip()
    if major:
        parts.append(f"Major: {major}")

    if bio:
        parts.append(f"Background: {bio}")

    return ". ".join(parts).strip()


def build_internship_semantic_text(internship: Any) -> str:
    """
    Constructs a deterministic, requirement-focused textual representation of an internship.
    Prioritizes required skills, preferred skills, and core responsibilities.
    Uses title and employer domain as secondary context.
    Avoids generic corporate boilerplate.

    Guard: If the internship has neither skills nor description, returns an empty string
    so that safe fallback rebalancing triggers.
    """
    req_skills = getattr(internship, "required_skills", []) or []
    clean_req = [s.strip() for s in req_skills if isinstance(s, str) and s.strip()]

    pref_skills = getattr(internship, "preferred_skills", []) or []
    clean_pref = [s.strip() for s in pref_skills if isinstance(s, str) and s.strip()]

    desc = str(getattr(internship, "description", "") or "").strip()

    # Substantive content guard
    if not clean_req and not clean_pref and not desc:
        return ""

    parts = []
    if clean_req:
        parts.append(f"Required skills: {', '.join(clean_req)}")

    if clean_pref:
        parts.append(f"Preferred skills: {', '.join(clean_pref)}")

    if desc:
        parts.append(f"Responsibilities: {desc}")

    title = str(getattr(internship, "title", "") or "").strip()
    org = str(getattr(internship, "organization", "") or "").strip()
    if title and org:
        parts.append(f"Role: {title} at {org}")
    elif title:
        parts.append(f"Role: {title}")

    return ". ".join(parts).strip()


def get_semantic_qualitative_label(similarity: float) -> str:
    """
    Translates raw cosine similarity into an accurate qualitative band.
    Avoids equating cosine similarity with a skill-match percentage.
    """
    if similarity >= 0.75:
        return "Strong contextual alignment"
    elif similarity >= 0.50:
        return "Moderate contextual alignment"
    elif similarity >= 0.25:
        return "Low contextual alignment"
    else:
        return "Minimal contextual alignment"


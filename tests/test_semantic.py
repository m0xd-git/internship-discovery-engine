"""
Automated Unit Tests for Semantic Engine & Embedding Cache
=============================================================================
Tests dense embedding generation, shape (384-dim), finite values,
cosine-similarity calculation, cache reuse, empty/invalid text handling,
and graceful degradation during model loading or encoding failures.
=============================================================================
"""

import unittest
from unittest.mock import MagicMock, patch
import numpy as np

from app.engine.semantic import (
    SemanticEngine,
    get_semantic_engine,
    get_text_embedding,
    cosine_similarity,
    text_similarity,
)
from app.config import SEMANTIC_MODEL_NAME, EMBEDDING_DIMENSION


class TestSemanticEngine(unittest.TestCase):
    """
    Unit tests for SemanticEngine vector operations and caching.
    """

    @classmethod
    def setUpClass(cls):
        # Pre-load shared model once at class level for fast test execution
        cls.shared_model = None
        try:
            temp_engine = SemanticEngine()
            cls.shared_model = temp_engine.get_model()
        except Exception:
            pass

    def setUp(self):
        # Fresh isolated engine instance for each test with shared underlying model
        self.engine = SemanticEngine()
        if self.shared_model is not None:
            self.engine._model = self.shared_model

    def test_initialization_defaults(self):
        """SemanticEngine must default to configured model, CPU device, and 384 dimensions."""
        fresh = SemanticEngine()
        self.assertEqual(fresh.model_name, SEMANTIC_MODEL_NAME)
        self.assertEqual(fresh.device, "cpu")
        self.assertEqual(fresh.embedding_dim, EMBEDDING_DIMENSION)
        self.assertEqual(fresh.get_cache_size(), 0)

    def test_model_loading_cached(self):
        """Model must load cleanly on CPU from local cache."""
        fresh = SemanticEngine()
        model = fresh.get_model()
        self.assertIsNotNone(model, "Model failed to load from cache.")
        # Repeated call must return the same instance (cached in self._model)
        self.assertIs(fresh.get_model(), model)

    def test_embedding_dimensions_and_finiteness(self):
        """Generated embeddings must have 384 dimensions and finite float values."""
        emb = self.engine.encode_text("Python backend development with Flask")
        self.assertIsInstance(emb, np.ndarray)
        self.assertEqual(emb.shape, (384,))
        self.assertTrue(np.all(np.isfinite(emb)), "Embedding contains NaN or Inf.")
        self.assertGreater(float(np.linalg.norm(emb)), 0.0)

    def test_empty_and_invalid_inputs(self):
        """Empty, None, or invalid text must return zero vectors of shape (384,) without crashing."""
        zero_vec = np.zeros(384, dtype=np.float32)

        for invalid_input in [None, "", "   ", "\t\n", 12345, [], {}]:
            emb = self.engine.encode_text(invalid_input)
            self.assertEqual(emb.shape, (384,))
            np.testing.assert_array_equal(emb, zero_vec)

    def test_cosine_similarity_mathematics(self):
        """Cosine similarity function must adhere strictly to mathematical vector definitions."""
        # 1. Identical vectors -> 1.0
        v1 = np.array([1.0, 2.0, 3.0] + [0.0] * 381, dtype=np.float32)
        self.assertAlmostEqual(self.engine.compute_cosine_similarity(v1, v1), 1.0, places=5)

        # 2. Orthogonal vectors -> 0.0
        v_ortho1 = np.array([1.0, 0.0] + [0.0] * 382, dtype=np.float32)
        v_ortho2 = np.array([0.0, 1.0] + [0.0] * 382, dtype=np.float32)
        self.assertAlmostEqual(self.engine.compute_cosine_similarity(v_ortho1, v_ortho2), 0.0, places=5)

        # 3. Opposite vectors -> -1.0
        self.assertAlmostEqual(self.engine.compute_cosine_similarity(v1, -v1), -1.0, places=5)

        # 4. Zero vectors -> 0.0
        v_zero = np.zeros(384, dtype=np.float32)
        self.assertEqual(self.engine.compute_cosine_similarity(v1, v_zero), 0.0)
        self.assertEqual(self.engine.compute_cosine_similarity(v_zero, v1), 0.0)
        self.assertEqual(self.engine.compute_cosine_similarity(v_zero, v_zero), 0.0)

        # 5. Invalid shape or types -> 0.0
        self.assertEqual(self.engine.compute_cosine_similarity(np.array([1.0, 2.0]), v1), 0.0)
        self.assertEqual(self.engine.compute_cosine_similarity("not_an_array", v1), 0.0)

    def test_semantic_ranking_benchmark_sentences(self):
        """Related domain concepts must produce significantly higher similarity than unrelated concepts."""
        text_a = "Machine learning and predictive analytics using Python"
        text_b = "Building predictive models and data analysis with Python"
        text_c = "Frontend web development using HTML and CSS"

        sim_ab = self.engine.similarity_between_texts(text_a, text_b)
        sim_ac = self.engine.similarity_between_texts(text_a, text_c)
        sim_bc = self.engine.similarity_between_texts(text_b, text_c)

        # Conceptual invariant: sim(A, B) >> sim(A, C)
        self.assertGreater(sim_ab, sim_ac, f"Expected {sim_ab} > {sim_ac}")
        self.assertGreater(sim_ab, 0.65, "Expected high semantic overlap for ML/Analytics.")
        self.assertLess(sim_ac, 0.25, "Expected low semantic overlap for ML vs HTML/CSS.")

    def test_embedding_cache_reuse(self):
        """Repeated encodings of identical text must hit the in-memory cache and avoid redundant computation."""
        sample_text = "Database indexing and SQL performance optimization"

        # Initially empty cache
        self.assertEqual(self.engine.get_cache_size(), 0)

        # First encoding: populates cache
        emb1 = self.engine.encode_text(sample_text, use_cache=True)
        self.assertEqual(self.engine.get_cache_size(), 1)

        # Mock the underlying model to verify it is NOT called on cache hit
        mock_model = MagicMock()
        self.engine._model = mock_model

        # Second encoding: must return cached vector without invoking mock_model.encode
        emb2 = self.engine.encode_text(sample_text, use_cache=True)
        mock_model.encode.assert_not_called()
        self.assertEqual(self.engine.get_cache_size(), 1)
        np.testing.assert_array_equal(emb1, emb2)

    def test_cache_clearing(self):
        """clear_cache() must empty all stored embeddings."""
        self.engine.encode_text("Docker containers and microservices")
        self.assertEqual(self.engine.get_cache_size(), 1)

        self.engine.clear_cache()
        self.assertEqual(self.engine.get_cache_size(), 0)

    def test_use_cache_false_bypasses_cache(self):
        """When use_cache=False, embeddings must not be saved to cache."""
        self.engine.encode_text("Cloud DevOps pipeline", use_cache=False)
        self.assertEqual(self.engine.get_cache_size(), 0)

    def test_graceful_model_loading_failure(self):
        """If model loading fails, engine must fail safely by returning zero vectors without throwing."""
        failing_engine = SemanticEngine(model_name="nonexistent/fake-model-path")

        # Mock SentenceTransformer import or constructor raising an OSError
        with patch("sentence_transformers.SentenceTransformer", side_effect=OSError("Model file not found")):
            model = failing_engine.get_model()
            self.assertIsNone(model)
            self.assertTrue(failing_engine._model_load_failed)

            # encode_text must return zero vector safely
            emb = failing_engine.encode_text("Some text")
            self.assertEqual(emb.shape, (384,))
            np.testing.assert_array_equal(emb, np.zeros(384, dtype=np.float32))

            # similarity_between_texts must return 0.0 safely
            sim = failing_engine.similarity_between_texts("A", "B")
            self.assertEqual(sim, 0.0)

    def test_graceful_encoding_runtime_failure(self):
        """If model.encode throws a runtime error, engine must return a zero vector safely."""
        mock_model = MagicMock()
        mock_model.encode.side_effect = RuntimeError("CUDA out of memory or inference crash")
        self.engine._model = mock_model

        emb = self.engine.encode_text("A valid prompt", use_cache=False)
        self.assertEqual(emb.shape, (384,))
        np.testing.assert_array_equal(emb, np.zeros(384, dtype=np.float32))

    def test_convenience_functions(self):
        """Global convenience functions must invoke the default SemanticEngine correctly."""
        v = get_text_embedding("Machine Learning")
        self.assertEqual(v.shape, (384,))

        sim = text_similarity("Python coding", "Python programming")
        self.assertGreater(sim, 0.70)

        cos = cosine_similarity(v, v)
        self.assertAlmostEqual(cos, 1.0, places=5)

    def test_text_similarity_with_empty_inputs(self):
        """text_similarity with empty or None inputs must return 0.0."""
        self.assertEqual(text_similarity(None, "Python"), 0.0)
        self.assertEqual(text_similarity("Python", ""), 0.0)
        self.assertEqual(text_similarity("", None), 0.0)


if __name__ == "__main__":
    unittest.main()

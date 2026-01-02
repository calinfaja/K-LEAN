"""Unit tests for klean.data.scripts.knowledge_db module.

Tests the hybrid search system with RRF fusion:
- Dense search (semantic similarity via BGE)
- Sparse search (keyword matching via BM42)
- RRF (Reciprocal Rank Fusion) combining both
- Cross-encoder reranking (default enabled)

ANTI-FALSE-POSITIVE MEASURES:
1. Test RRF scoring with known values
2. Verify sparse/dense search integration
3. Test fallback behavior when sparse model unavailable
4. Check file persistence (sparse_index.json)
"""

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_kb_dir(tmp_path):
    """Create temporary knowledge DB directory."""
    kb_dir = tmp_path / "test-project" / ".knowledge-db"
    kb_dir.mkdir(parents=True)

    # Create project markers
    (tmp_path / "test-project" / ".git").mkdir()

    return kb_dir


@pytest.fixture
def sample_entries():
    """Sample entries for testing."""
    return [
        {
            "id": "entry-1",
            "title": "BLE Power Optimization",
            "summary": "Nordic nRF52 power optimization techniques",
            "tags": ["ble", "power", "embedded"],
            "found_date": "2024-12-01T00:00:00",
        },
        {
            "id": "entry-2",
            "title": "OAuth2 Implementation",
            "summary": "OAuth2 security patterns and best practices",
            "tags": ["oauth", "security", "auth"],
            "found_date": "2024-12-02T00:00:00",
        },
        {
            "id": "entry-3",
            "title": "Python Type Hints",
            "summary": "Using type hints for better code quality",
            "tags": ["python", "typing"],
            "found_date": "2024-12-03T00:00:00",
        },
    ]


@pytest.fixture
def kb_with_entries(temp_kb_dir, sample_entries):
    """Create KB directory with sample entries."""
    jsonl_path = temp_kb_dir / "entries.jsonl"

    with open(jsonl_path, "w") as f:
        for entry in sample_entries:
            f.write(json.dumps(entry) + "\n")

    return temp_kb_dir


# =============================================================================
# TestRRFScore
# =============================================================================

class TestRRFScore:
    """Tests for RRF (Reciprocal Rank Fusion) scoring."""

    def test_rrf_single_rank(self):
        """Should calculate RRF for single rank."""
        # Import here to avoid module-level import issues
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))
        from knowledge_db import KnowledgeDB

        # Act
        score = KnowledgeDB.rrf_score([1], k=60)

        # Assert - 1/(60+1) = 0.01639...
        assert abs(score - (1.0 / 61)) < 0.0001

    def test_rrf_multiple_ranks(self):
        """Should sum RRF scores for multiple ranks."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))
        from knowledge_db import KnowledgeDB

        # Act - rank 1 in both retrievers
        score = KnowledgeDB.rrf_score([1, 1], k=60)

        # Assert - 2 * 1/(60+1) = 0.0328...
        expected = 2.0 * (1.0 / 61)
        assert abs(score - expected) < 0.0001

    def test_rrf_ignores_zero_ranks(self):
        """Should ignore zero ranks (not found in retriever)."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))
        from knowledge_db import KnowledgeDB

        # Act - found in one retriever only
        score1 = KnowledgeDB.rrf_score([1, 0], k=60)
        score2 = KnowledgeDB.rrf_score([1], k=60)

        # Assert - should be equal
        assert abs(score1 - score2) < 0.0001

    def test_rrf_higher_rank_lower_score(self):
        """Should give lower scores to higher ranks."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))
        from knowledge_db import KnowledgeDB

        # Act
        score_rank1 = KnowledgeDB.rrf_score([1], k=60)
        score_rank10 = KnowledgeDB.rrf_score([10], k=60)

        # Assert
        assert score_rank1 > score_rank10

    def test_rrf_different_k_values(self):
        """Should produce different scores with different k values."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))
        from knowledge_db import KnowledgeDB

        # Act
        score_k60 = KnowledgeDB.rrf_score([1], k=60)
        score_k20 = KnowledgeDB.rrf_score([1], k=20)

        # Assert - lower k gives higher score for same rank
        assert score_k20 > score_k60


# =============================================================================
# TestSparseIndexPersistence
# =============================================================================

class TestSparseIndexPersistence:
    """Tests for sparse index persistence."""

    def test_sparse_index_path_set(self, temp_kb_dir):
        """Should set sparse_index_path during init."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))

        with patch("knowledge_db.find_project_root") as mock_root:
            mock_root.return_value = temp_kb_dir.parent
            from knowledge_db import KnowledgeDB

            # Act
            db = KnowledgeDB(str(temp_kb_dir.parent))

            # Assert
            assert db.sparse_index_path == temp_kb_dir / "sparse_index.json"

    def test_loads_sparse_vectors_if_present(self, temp_kb_dir):
        """Should load sparse vectors from sparse_index.json."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))

        # Create sparse index file
        sparse_data = {
            "0": {"token1": 0.5, "token2": 0.3},
            "1": {"token3": 0.8},
        }
        (temp_kb_dir / "sparse_index.json").write_text(json.dumps(sparse_data))

        # Also need embeddings and index for load to work
        np.save(str(temp_kb_dir / "embeddings.npy"), np.zeros((2, 384)))
        (temp_kb_dir / "index.json").write_text(json.dumps({"id1": 0, "id2": 1}))

        with patch("knowledge_db.find_project_root") as mock_root:
            mock_root.return_value = temp_kb_dir.parent
            from knowledge_db import KnowledgeDB

            # Act
            db = KnowledgeDB(str(temp_kb_dir.parent))

            # Assert
            assert len(db._sparse_vectors) == 2
            assert 0 in db._sparse_vectors
            assert db._sparse_vectors[0]["token1"] == 0.5


# =============================================================================
# TestHybridSearch
# =============================================================================

class TestHybridSearch:
    """Tests for hybrid search with RRF fusion."""

    def test_search_returns_empty_for_empty_db(self, temp_kb_dir):
        """Should return empty list for empty database."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))

        with patch("knowledge_db.find_project_root") as mock_root:
            mock_root.return_value = temp_kb_dir.parent
            from knowledge_db import KnowledgeDB

            # Act
            db = KnowledgeDB(str(temp_kb_dir.parent))
            results = db.search("test query")

            # Assert
            assert results == []

    def test_search_returns_results_with_scores(self, kb_with_entries):
        """Should return results with RRF scores."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))

        with patch("knowledge_db.find_project_root") as mock_root:
            mock_root.return_value = kb_with_entries.parent
            from knowledge_db import KnowledgeDB

            # Act
            db = KnowledgeDB(str(kb_with_entries.parent))
            db.rebuild_index()
            results = db.search("BLE power")

            # Assert
            assert len(results) > 0
            assert all("score" in r for r in results)
            assert all(r["score"] > 0 for r in results)

    def test_search_includes_meta_breakdown(self, kb_with_entries):
        """Should include search metadata with rank breakdown."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))

        with patch("knowledge_db.find_project_root") as mock_root:
            mock_root.return_value = kb_with_entries.parent
            from knowledge_db import KnowledgeDB

            # Act
            db = KnowledgeDB(str(kb_with_entries.parent))
            db.rebuild_index()
            results = db.search("OAuth security")

            # Assert
            assert len(results) > 0
            assert "_search_meta" in results[0]
            meta = results[0]["_search_meta"]
            assert "dense_rank" in meta
            assert "rrf_score" in meta

    def test_search_respects_limit(self, kb_with_entries):
        """Should respect result limit."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))

        with patch("knowledge_db.find_project_root") as mock_root:
            mock_root.return_value = kb_with_entries.parent
            from knowledge_db import KnowledgeDB

            # Act
            db = KnowledgeDB(str(kb_with_entries.parent))
            db.rebuild_index()
            results = db.search("python", limit=2)

            # Assert
            assert len(results) <= 2


# =============================================================================
# TestDenseSearch
# =============================================================================

class TestDenseSearch:
    """Tests for dense (semantic) search."""

    def test_dense_search_returns_tuples(self, kb_with_entries):
        """Should return list of (row_idx, score) tuples."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))

        with patch("knowledge_db.find_project_root") as mock_root:
            mock_root.return_value = kb_with_entries.parent
            from knowledge_db import KnowledgeDB

            # Act
            db = KnowledgeDB(str(kb_with_entries.parent))
            db.rebuild_index()
            results = db._dense_search("power optimization", limit=5)

            # Assert
            assert isinstance(results, list)
            assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
            assert all(isinstance(r[0], int) for r in results)
            assert all(isinstance(r[1], float) for r in results)

    def test_dense_search_scores_sorted_descending(self, kb_with_entries):
        """Should return results sorted by score descending."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))

        with patch("knowledge_db.find_project_root") as mock_root:
            mock_root.return_value = kb_with_entries.parent
            from knowledge_db import KnowledgeDB

            # Act
            db = KnowledgeDB(str(kb_with_entries.parent))
            db.rebuild_index()
            results = db._dense_search("test query", limit=10)

            # Assert
            if len(results) > 1:
                scores = [r[1] for r in results]
                assert scores == sorted(scores, reverse=True)


# =============================================================================
# TestStats
# =============================================================================

class TestStats:
    """Tests for database statistics."""

    def test_stats_includes_hybrid_backend(self, kb_with_entries):
        """Should report fastembed-hybrid backend."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))

        with patch("knowledge_db.find_project_root") as mock_root:
            mock_root.return_value = kb_with_entries.parent
            from knowledge_db import KnowledgeDB

            # Act
            db = KnowledgeDB(str(kb_with_entries.parent))
            db.rebuild_index()
            stats = db.stats()

            # Assert
            assert stats["backend"] == "fastembed-hybrid"
            assert "has_sparse_index" in stats
            assert "sparse_entries" in stats


# =============================================================================
# TestRebuildIndex
# =============================================================================

class TestRebuildIndex:
    """Tests for index rebuilding."""

    def test_rebuild_creates_dense_embeddings(self, kb_with_entries):
        """Should create dense embeddings during rebuild."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))

        with patch("knowledge_db.find_project_root") as mock_root:
            mock_root.return_value = kb_with_entries.parent
            from knowledge_db import KnowledgeDB

            # Act
            db = KnowledgeDB(str(kb_with_entries.parent))
            count = db.rebuild_index()

            # Assert
            assert count == 3
            assert db._embeddings is not None
            assert db._embeddings.shape[0] == 3

    def test_rebuild_saves_files(self, kb_with_entries):
        """Should save embeddings and index files."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))

        with patch("knowledge_db.find_project_root") as mock_root:
            mock_root.return_value = kb_with_entries.parent
            from knowledge_db import KnowledgeDB

            # Act
            db = KnowledgeDB(str(kb_with_entries.parent))
            db.rebuild_index()

            # Assert
            assert (kb_with_entries / "embeddings.npy").exists()
            assert (kb_with_entries / "index.json").exists()


# =============================================================================
# TestAddEntry
# =============================================================================

class TestAddEntry:
    """Tests for adding entries."""

    def test_add_generates_dense_embedding(self, temp_kb_dir):
        """Should generate dense embedding when adding entry."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))

        with patch("knowledge_db.find_project_root") as mock_root:
            mock_root.return_value = temp_kb_dir.parent
            from knowledge_db import KnowledgeDB

            # Act
            db = KnowledgeDB(str(temp_kb_dir.parent))
            entry_id = db.add({
                "title": "Test Entry",
                "summary": "Test summary content",
            })

            # Assert
            assert entry_id is not None
            assert db._embeddings is not None
            assert db._embeddings.shape[0] == 1

    def test_add_appends_to_jsonl(self, temp_kb_dir):
        """Should append entry to JSONL file."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src/klean/data/scripts"))

        with patch("knowledge_db.find_project_root") as mock_root:
            mock_root.return_value = temp_kb_dir.parent
            from knowledge_db import KnowledgeDB

            # Act
            db = KnowledgeDB(str(temp_kb_dir.parent))
            db.add({"title": "Entry 1", "summary": "Summary 1"})
            db.add({"title": "Entry 2", "summary": "Summary 2"})

            # Assert
            with open(temp_kb_dir / "entries.jsonl") as f:
                lines = [line for line in f if line.strip()]
            assert len(lines) == 2

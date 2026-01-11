#!/usr/bin/env python3
"""
Knowledge Database - Hybrid search with fastembed (dense + sparse + reranking)

This module provides a KnowledgeDB class using fastembed for:
- Dense embeddings (BGE model) for semantic similarity
- Sparse embeddings (BM42) for learned keyword matching
- RRF (Reciprocal Rank Fusion) to combine results
- Optional cross-encoder reranking for precision

Storage:
- entries.jsonl: Source of truth (human-readable)
- embeddings.npy: Dense vectors (384-dim BGE)
- sparse_index.json: Sparse vectors (BM42 learned token weights)
- index.json: ID to row mapping

Hybrid search pipeline:
1. Dense search (semantic similarity via BGE)
2. Sparse search (keyword matching via BM42 with learned attention)
3. RRF fusion of both result sets
4. Cross-encoder reranking (enabled by default)

Usage:
    from knowledge_db import KnowledgeDB

    db = KnowledgeDB()  # Auto-detects project root
    db.add({
        "title": "BLE Optimization",
        "summary": "Nordic's guide on connection intervals",
        ...
    })
    # Hybrid search with reranking (default)
    results = db.search("power optimization")
    # Skip reranking for faster results (lower precision)
    results = db.search("power optimization", rerank=False)
"""

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np

# Import shared utilities
try:
    from kb_utils import debug_log, find_project_root, migrate_entry
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from kb_utils import debug_log, find_project_root, migrate_entry

# Fastembed imports
try:
    from fastembed import TextEmbedding
except ImportError:
    print("ERROR: fastembed not installed. Run: pip install fastembed")
    sys.exit(1)

# Optional sparse/rerank imports (lazy loaded)
SparseTextEmbedding = None
TextCrossEncoder = None


# Global model instances (singletons for performance)
_dense_model: Optional[TextEmbedding] = None
_sparse_model = None  # Optional[SparseTextEmbedding]
_reranker = None  # Optional[TextCrossEncoder]


def get_dense_model() -> TextEmbedding:
    """Get or create singleton dense embedding model."""
    global _dense_model
    if _dense_model is None:
        # BGE-small: 384 dimensions, good balance of speed and quality
        _dense_model = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _dense_model


def get_sparse_model():
    """Get or create singleton sparse embedding model (BM42).

    Uses Qdrant/bm42 (90MB) - learned attention-based token weighting.
    Better than pure BM25: learns which tokens are important.
    Much lighter than SPLADE++ (532MB).
    """
    global _sparse_model, SparseTextEmbedding
    if _sparse_model is None:
        if SparseTextEmbedding is None:
            try:
                from fastembed import SparseTextEmbedding as STE  # noqa: N817

                SparseTextEmbedding = STE
            except ImportError:
                debug_log("SparseTextEmbedding not available, falling back to dense-only")
                return None
        # BM42: learned attention weights (90MB) - better than flat BM25
        _sparse_model = SparseTextEmbedding("Qdrant/bm42-all-minilm-l6-v2-attentions")
    return _sparse_model


def get_reranker():
    """Get or create singleton cross-encoder reranker."""
    global _reranker, TextCrossEncoder
    if _reranker is None:
        if TextCrossEncoder is None:
            try:
                from fastembed.rerank.cross_encoder import TextCrossEncoder as TCE  # noqa: N817

                TextCrossEncoder = TCE
            except ImportError:
                debug_log("Cross-encoder reranker not available")
                return None
        _reranker = TextCrossEncoder("Xenova/ms-marco-MiniLM-L-6-v2")
    return _reranker


class KnowledgeDB:
    """
    Hybrid knowledge database using fastembed (dense + sparse + reranking).

    Stores entries in project's .knowledge-db/ directory with:
    - entries.jsonl: Source of truth (human-readable)
    - embeddings.npy: Dense vectors (BGE model)
    - sparse_index.json: Sparse vectors (BM42 learned token weights)
    - index.json: ID to row mapping

    Search uses RRF (Reciprocal Rank Fusion) to combine:
    - Dense search (semantic similarity)
    - Sparse search (keyword matching via BM42 with learned attention)
    - Optional cross-encoder reranking for precision
    """

    # RRF constant (standard value from literature)
    RRF_K = 60

    def __init__(self, project_path: str = None):
        """
        Initialize KnowledgeDB.

        Args:
            project_path: Path to project root. If None, auto-detects.
        """
        if project_path:
            self.project_root = Path(project_path).resolve()
        else:
            self.project_root = find_project_root()

        if not self.project_root:
            raise ValueError(
                "Could not find project root. "
                "Make sure you're in a directory with .serena, .claude, or .knowledge-db"
            )

        self.db_path = self.project_root / ".knowledge-db"
        self.embeddings_path = self.db_path / "embeddings.npy"
        self.sparse_index_path = self.db_path / "sparse_index.json"
        self.index_path = self.db_path / "index.json"
        self.jsonl_path = self.db_path / "entries.jsonl"
        self.old_txtai_path = self.db_path / "index"  # Old txtai SQLite

        # Create directory if needed
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Initialize models (lazy load on first use)
        self._dense_model: Optional[TextEmbedding] = None
        self._sparse_model = None  # Loaded lazily
        self._reranker = None  # Loaded lazily

        # In-memory index (dense)
        self._embeddings: Optional[np.ndarray] = None
        self._id_to_row: dict[str, int] = {}
        self._row_to_id: dict[int, str] = {}
        self._entries: list[dict[str, Any]] = []  # Cached entries

        # In-memory sparse index: {row_idx: {token: weight, ...}}
        self._sparse_vectors: dict[int, dict[str, float]] = {}

        # Load existing index if present
        self._load_index()

        # Auto-migrate from txtai if needed
        if self._needs_migration():
            debug_log("Detected old txtai index, migrating...")
            self.rebuild_index()

    @property
    def dense_model(self) -> TextEmbedding:
        """Lazy load dense embedding model (BGE)."""
        if self._dense_model is None:
            self._dense_model = get_dense_model()
        return self._dense_model

    @property
    def sparse_model(self):
        """Lazy load sparse embedding model (BM42). Returns None if unavailable."""
        if self._sparse_model is None:
            self._sparse_model = get_sparse_model()
        return self._sparse_model

    @property
    def reranker(self):
        """Lazy load cross-encoder reranker. Returns None if unavailable."""
        if self._reranker is None:
            self._reranker = get_reranker()
        return self._reranker

    # Backward compatibility alias
    @property
    def model(self) -> TextEmbedding:
        """Alias for dense_model (backward compatibility)."""
        return self.dense_model

    def _needs_migration(self) -> bool:
        """Check if migration from txtai is needed."""
        # Has old txtai index but no new fastembed index
        has_old = self.old_txtai_path.exists()
        has_new = self.embeddings_path.exists()
        has_entries = self.jsonl_path.exists()
        return has_old and not has_new and has_entries

    def _load_index(self) -> None:
        """Load embeddings, sparse vectors, index, and entries from disk."""
        if self.embeddings_path.exists() and self.index_path.exists():
            try:
                self._embeddings = np.load(str(self.embeddings_path))
                with open(self.index_path) as f:
                    self._id_to_row = json.load(f)
                self._row_to_id = {v: k for k, v in self._id_to_row.items()}

                # Load sparse vectors if present
                self._sparse_vectors = {}
                if self.sparse_index_path.exists():
                    with open(self.sparse_index_path) as f:
                        sparse_data = json.load(f)
                        # Convert string keys back to int
                        self._sparse_vectors = {int(k): v for k, v in sparse_data.items()}
                    debug_log(f"Loaded {len(self._sparse_vectors)} sparse vectors")

                # Load entries into memory
                self._entries = []
                if self.jsonl_path.exists():
                    with open(self.jsonl_path) as f:
                        for line in f:
                            if line.strip():
                                try:
                                    e = json.loads(line)
                                    if isinstance(e, dict):
                                        self._entries.append(migrate_entry(e))
                                except json.JSONDecodeError:
                                    pass

                # Validate consistency
                if len(self._embeddings) != len(self._entries):
                    debug_log(
                        f"WARNING: Index/entries mismatch ({len(self._embeddings)} vs {len(self._entries)})"
                    )

                debug_log(f"Loaded {len(self._id_to_row)} embeddings from disk")
            except Exception as e:
                debug_log(f"Failed to load index: {e}")
                self._embeddings = None
                self._id_to_row = {}
                self._row_to_id = {}
                self._entries = []
                self._sparse_vectors = {}

    def _save_index(self) -> None:
        """Save embeddings, sparse vectors, and index to disk."""
        if self._embeddings is not None:
            np.save(str(self.embeddings_path), self._embeddings)
            with open(self.index_path, "w") as f:
                json.dump(self._id_to_row, f)

            # Save sparse vectors if present
            if self._sparse_vectors:
                # Convert int keys to string for JSON
                sparse_data = {str(k): v for k, v in self._sparse_vectors.items()}
                with open(self.sparse_index_path, "w") as f:
                    json.dump(sparse_data, f)
                debug_log(f"Saved {len(self._sparse_vectors)} sparse vectors")

            debug_log(f"Saved {len(self._id_to_row)} embeddings to disk")

    def _build_searchable_text(self, entry: dict[str, Any]) -> str:
        """Build searchable text from entry fields."""
        searchable_parts = [
            entry.get("title", ""),
            entry.get("summary", ""),
            entry.get("atomic_insight", ""),
            entry.get("problem_solved", ""),
            " ".join(entry.get("key_concepts", [])),
            " ".join(entry.get("tags", [])),
            entry.get("what_worked", ""),
        ]
        return " ".join(filter(None, searchable_parts))

    @staticmethod
    def rrf_score(ranks: list[int], k: int = 60) -> float:
        """
        Calculate Reciprocal Rank Fusion score.

        RRF combines rankings from multiple retrieval methods.
        Formula: sum(1 / (k + rank)) for each rank

        Args:
            ranks: List of ranks from different retrievers (1-indexed, 0 means not found)
            k: Smoothing constant (default 60, standard in literature)

        Returns:
            Combined RRF score (higher is better)
        """
        return sum(1.0 / (k + rank) for rank in ranks if rank > 0)

    def _generate_sparse_embedding(self, text: str) -> dict[str, float]:
        """
        Generate sparse embedding using BM42.

        Returns dict of {token: weight} for non-zero weights.
        Returns empty dict if sparse model unavailable.
        """
        if self.sparse_model is None:
            return {}

        try:
            # BM42 returns sparse embedding with indices and values
            embeddings = list(self.sparse_model.embed([text]))
            if not embeddings:
                return {}

            sparse_emb = embeddings[0]
            # Convert to {token: weight} dict (keeping top weights)
            # sparse_emb has .indices and .values attributes
            result = {}
            for idx, val in zip(sparse_emb.indices, sparse_emb.values):
                if val > 0.01:  # Skip near-zero weights
                    result[str(idx)] = float(val)
            return result
        except Exception as e:
            debug_log(f"Sparse embedding failed: {e}")
            return {}

    def _dense_search(self, query: str, limit: int) -> list[tuple]:
        """
        Dense (semantic) search using cosine similarity.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of (row_idx, score) tuples, sorted by score descending
        """
        if self._embeddings is None or len(self._embeddings) == 0:
            return []

        # Generate query embedding
        query_embedding = list(self.dense_model.embed([query]))[0]

        # Compute cosine similarity (embeddings are normalized)
        scores = self._embeddings @ query_embedding

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:limit]

        return [(int(idx), float(scores[idx])) for idx in top_indices]

    def _sparse_search(self, query: str, limit: int) -> list[tuple]:
        """
        Sparse (keyword) search using BM42.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of (row_idx, score) tuples, sorted by score descending
        """
        if not self._sparse_vectors:
            return []

        query_sparse = self._generate_sparse_embedding(query)
        if not query_sparse:
            return []

        # Score each document by dot product of sparse vectors
        scores = []
        for row_idx, doc_sparse in self._sparse_vectors.items():
            score = 0.0
            for token, q_weight in query_sparse.items():
                if token in doc_sparse:
                    score += q_weight * doc_sparse[token]
            if score > 0:
                scores.append((row_idx, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:limit]

    def _rerank_results(
        self, query: str, results: list[dict[str, Any]], limit: int
    ) -> list[dict[str, Any]]:
        """
        Rerank results using cross-encoder.

        Args:
            query: Original query
            results: List of result dicts with 'title' and 'summary'
            limit: Maximum results to return

        Returns:
            Reranked results with updated scores
        """
        if self.reranker is None or not results:
            return results[:limit]

        try:
            # Build documents for reranking
            documents = []
            for r in results:
                text = f"{r.get('title', '')} {r.get('summary', '')}"
                documents.append(text)

            # Get reranking scores
            rerank_scores = list(self.reranker.rerank(query, documents))

            # Combine with results
            for r, score in zip(results, rerank_scores):
                r["rerank_score"] = float(score)

            # Sort by rerank score
            results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

            return results[:limit]
        except Exception as e:
            debug_log(f"Reranking failed: {e}")
            return results[:limit]

    def add(self, entry: dict[str, Any]) -> str:
        """
        Add a knowledge entry to the database.

        Args:
            entry: Dictionary with knowledge entry fields:
                - title (required): Short title
                - summary (required): What was found
                - type: web|code|solution|lesson
                - url: Source URL
                - problem_solved: What problem this solves
                - key_concepts: List of keywords/concepts
                - relevance_score: 0-1 score
                - confidence_score: 0-1 confidence
                - tags: List of searchable tags
                - etc.

        Returns:
            Entry ID (UUID)
        """
        # Generate ID if not provided
        entry_id = entry.get("id") or str(uuid.uuid4())
        entry["id"] = entry_id

        # Add timestamp
        entry["found_date"] = entry.get("found_date") or datetime.now().isoformat()

        # Ensure required fields
        if "title" not in entry:
            raise ValueError("Entry must have 'title' field")
        if "summary" not in entry:
            raise ValueError("Entry must have 'summary' field")

        # Add default metadata fields
        entry.setdefault("confidence_score", 0.7)
        entry.setdefault("tags", [])
        entry.setdefault("usage_count", 0)
        entry.setdefault("last_used", None)
        entry.setdefault("source_quality", "medium")

        # Build searchable text
        searchable_text = self._build_searchable_text(entry)

        # Generate dense embedding
        embedding = list(self.dense_model.embed([searchable_text]))[0]

        # Add to in-memory dense index
        if self._embeddings is None:
            self._embeddings = embedding.reshape(1, -1)
        else:
            self._embeddings = np.vstack([self._embeddings, embedding])

        row_idx = len(self._id_to_row)
        self._id_to_row[entry_id] = row_idx
        self._row_to_id[row_idx] = entry_id
        self._entries.append(entry)  # Add to cache

        # Generate sparse embedding (if model available)
        sparse_vec = self._generate_sparse_embedding(searchable_text)
        if sparse_vec:
            self._sparse_vectors[row_idx] = sparse_vec

        # Save to disk
        self._save_index()

        # Append to JSONL backup
        with open(self.jsonl_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return entry_id

    def search(
        self,
        query: str,
        limit: int = 5,
        rerank: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Hybrid search combining dense and sparse retrieval with RRF fusion.

        Args:
            query: Natural language search query
            limit: Maximum number of results
            rerank: Apply cross-encoder reranking for higher precision (default: True)

        Returns:
            List of matching entries with scores

        Search pipeline:
        1. Dense search (semantic similarity via BGE)
        2. Sparse search (keyword matching via BM42)
        3. RRF fusion of both result sets
        4. Cross-encoder reranking (default enabled)
        """
        if self._embeddings is None or len(self._embeddings) == 0:
            return []

        # Get more candidates for fusion (2x limit)
        candidate_limit = limit * 2

        # Layer 1: Dense search
        dense_results = self._dense_search(query, candidate_limit)

        # Layer 2: Sparse search (if available)
        sparse_results = self._sparse_search(query, candidate_limit)

        # Build rank maps (1-indexed for RRF)
        dense_ranks = {row_idx: rank + 1 for rank, (row_idx, _) in enumerate(dense_results)}
        sparse_ranks = {row_idx: rank + 1 for rank, (row_idx, _) in enumerate(sparse_results)}

        # Collect all unique row indices
        all_rows = set(dense_ranks.keys()) | set(sparse_ranks.keys())

        # Calculate RRF scores
        rrf_scores = []
        for row_idx in all_rows:
            ranks = [
                dense_ranks.get(row_idx, 0),
                sparse_ranks.get(row_idx, 0),
            ]
            score = self.rrf_score(ranks, k=self.RRF_K)
            rrf_scores.append((row_idx, score))

        # Sort by RRF score
        rrf_scores.sort(key=lambda x: x[1], reverse=True)

        # Format results from cached entries
        results = []
        for row_idx, rrf in rrf_scores[:candidate_limit]:
            if row_idx < len(self._entries):
                entry = self._entries[row_idx].copy()
                entry["score"] = rrf
                # Include breakdown for debugging
                entry["_search_meta"] = {
                    "dense_rank": dense_ranks.get(row_idx, 0),
                    "sparse_rank": sparse_ranks.get(row_idx, 0),
                    "rrf_score": rrf,
                }
                results.append(entry)

        # Layer 3: Optional reranking
        if rerank:
            results = self._rerank_results(query, results, limit)
        else:
            results = results[:limit]

        return results

    def get(self, entry_id: str) -> Optional[dict[str, Any]]:
        """
        Get a specific entry by ID.

        Args:
            entry_id: Entry UUID

        Returns:
            Entry dictionary or None if not found
        """
        if not self.jsonl_path.exists():
            return None

        with open(self.jsonl_path) as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        if isinstance(entry, dict) and entry.get("id") == entry_id:
                            return migrate_entry(entry)
                    except json.JSONDecodeError:
                        pass
        return None

    def stats(self) -> dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with count, size, last_updated
        """
        count = len(self._id_to_row) if self._id_to_row else 0
        size_bytes = 0
        last_updated = None

        # Get size
        for f in self.db_path.rglob("*"):
            if f.is_file():
                size_bytes += f.stat().st_size

        # Last modified
        if self.embeddings_path.exists():
            last_updated = datetime.fromtimestamp(self.embeddings_path.stat().st_mtime).isoformat()

        return {
            "count": count,
            "size_bytes": size_bytes,
            "size_human": f"{size_bytes / 1024:.1f} KB",
            "last_updated": last_updated,
            "db_path": str(self.db_path),
            "backend": "fastembed-hybrid",
            "has_sparse_index": len(self._sparse_vectors) > 0,
            "sparse_entries": len(self._sparse_vectors),
        }

    def rebuild_index(self, dense_only: bool = False, batch_size: int = 50) -> int:
        """
        Rebuild the index from JSONL backup.
        Migrates from txtai format or rebuilds fastembed index.

        Args:
            dense_only: If True, skip sparse embeddings (faster, less memory)
            batch_size: Batch size for sparse embedding generation (memory control)

        Returns:
            Number of entries indexed
        """
        if not self.jsonl_path.exists():
            return 0

        # Read all entries from JSONL
        entries = []
        needs_id_update = False
        with open(self.jsonl_path) as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        if isinstance(entry, dict):
                            entry = migrate_entry(entry)
                            # Ensure every entry has an ID
                            if not entry.get("id"):
                                entry["id"] = str(uuid.uuid4())
                                needs_id_update = True
                            entries.append(entry)
                    except json.JSONDecodeError:
                        pass

        if not entries:
            return 0

        # Update JSONL if we assigned new IDs
        if needs_id_update:
            debug_log("Updating entries with missing IDs...")
            with open(self.jsonl_path, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

        # Build searchable texts
        texts = [self._build_searchable_text(e) for e in entries]

        # Generate dense embeddings in batch
        debug_log(f"Generating dense embeddings for {len(texts)} entries...")
        embeddings_list = list(self.dense_model.embed(texts))
        self._embeddings = np.array(embeddings_list)

        # Generate sparse embeddings (if model available and not dense_only)
        self._sparse_vectors = {}
        if dense_only:
            debug_log("Skipping sparse embeddings (--dense-only mode)")
        elif self.sparse_model is not None:
            debug_log(
                f"Generating sparse embeddings for {len(texts)} entries (batch_size={batch_size})..."
            )
            try:
                # Process in batches to avoid memory exhaustion
                for batch_start in range(0, len(texts), batch_size):
                    batch_end = min(batch_start + batch_size, len(texts))
                    batch_texts = texts[batch_start:batch_end]
                    debug_log(f"  Processing batch {batch_start}-{batch_end}...")

                    sparse_list = list(self.sparse_model.embed(batch_texts))
                    for local_idx, sparse_emb in enumerate(sparse_list):
                        global_idx = batch_start + local_idx
                        # Convert to {token: weight} dict
                        vec = {}
                        for token_idx, val in zip(sparse_emb.indices, sparse_emb.values):
                            if val > 0.01:  # Skip near-zero weights
                                vec[str(token_idx)] = float(val)
                        if vec:
                            self._sparse_vectors[global_idx] = vec

                debug_log(f"Generated {len(self._sparse_vectors)} sparse vectors")
            except Exception as e:
                debug_log(f"Sparse embedding failed (continuing with dense only): {e}")
        else:
            debug_log("Sparse model not available, using dense-only search")

        # Build index and cache
        self._id_to_row = {}
        self._row_to_id = {}
        self._entries = entries  # Cache all entries
        for idx, entry in enumerate(entries):
            entry_id = entry["id"]  # Now guaranteed to exist
            self._id_to_row[entry_id] = idx
            self._row_to_id[idx] = entry_id

        # Save to disk
        self._save_index()

        # Remove old txtai index if present
        if self.old_txtai_path.exists():
            import shutil

            shutil.rmtree(self.old_txtai_path)
            debug_log("Removed old txtai index")

        debug_log(f"Rebuilt index with {len(entries)} entries (hybrid search enabled)")
        return len(entries)

    def list_recent(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        List most recent entries.

        Args:
            limit: Maximum number of entries

        Returns:
            List of recent entries
        """
        entries = []
        if self.jsonl_path.exists():
            with open(self.jsonl_path) as f:
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            if isinstance(entry, dict):
                                entries.append(migrate_entry(entry))
                        except json.JSONDecodeError:
                            pass

        # Sort by date descending
        entries.sort(key=lambda x: x.get("found_date", ""), reverse=True)
        return entries[:limit]

    def update_usage(self, entry_ids: list[str]) -> int:
        """
        Update usage stats for retrieved entries.

        Increments usage_count and sets last_used to now.
        This tracks which knowledge is actually being used.

        Args:
            entry_ids: List of entry IDs to update

        Returns:
            Number of entries updated
        """
        if not entry_ids or not self.jsonl_path.exists():
            return 0

        now = datetime.now().isoformat()
        updated_count = 0
        entries = []
        id_set = set(entry_ids)

        # Read all entries
        with open(self.jsonl_path) as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        if isinstance(entry, dict):
                            if entry.get("id") in id_set:
                                entry["usage_count"] = entry.get("usage_count", 0) + 1
                                entry["last_used"] = now
                                updated_count += 1
                            entries.append(entry)
                    except json.JSONDecodeError:
                        pass

        # Rewrite file with updated entries
        if updated_count > 0:
            with open(self.jsonl_path, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            # Update cached entries too
            for i, entry in enumerate(self._entries):
                if entry.get("id") in id_set:
                    self._entries[i]["usage_count"] = entry.get("usage_count", 0) + 1
                    self._entries[i]["last_used"] = now

        return updated_count

    def get_recent_important(self, limit: int = 3) -> list[dict[str, Any]]:
        """
        Get recent and/or high-priority entries for context injection.

        Prioritizes by a combination of:
        - Recency (found_date)
        - Priority (critical > high > medium > low)
        - Usage count (frequently used = valuable)

        Args:
            limit: Maximum entries to return

        Returns:
            List of important entries with title, summary, type
        """
        if not self._entries:
            return []

        # Score entries
        priority_scores = {"critical": 100, "high": 50, "medium": 20, "low": 10}
        scored = []

        for entry in self._entries:
            score = 0
            # Priority weight
            score += priority_scores.get(entry.get("priority", "medium"), 20)
            # Usage weight (each use adds 5 points)
            score += entry.get("usage_count", 0) * 5
            # Recency weight - entries from last 24h get bonus
            try:
                found = datetime.fromisoformat(entry.get("found_date", ""))
                age_hours = (datetime.now() - found).total_seconds() / 3600
                if age_hours < 24:
                    score += 30  # Recent bonus
                elif age_hours < 168:  # 1 week
                    score += 10
            except (ValueError, TypeError):
                pass

            scored.append((score, entry))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Return simplified entries
        results = []
        for _, entry in scored[:limit]:
            results.append(
                {
                    "id": entry.get("id"),
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", "")[:200],
                    "type": entry.get("type", "lesson"),
                    "priority": entry.get("priority", "medium"),
                }
            )

        return results

    def add_structured(self, data: dict) -> str:
        """
        Add a pre-structured entry (from Claude session or smart-capture).

        Returns:
            Entry ID (UUID)
        """
        entry = {
            "id": data.get("id") or str(uuid.uuid4()),
            "found_date": data.get("found_date") or datetime.now().isoformat(),
            "usage_count": data.get("usage_count", 0),
            "last_used": data.get("last_used"),
            "relevance_score": data.get("relevance_score", 0.8),
            "confidence_score": data.get("confidence_score", 0.8),
            "title": data.get("title", ""),
            "summary": data.get("summary", ""),
            "type": data.get("type", "lesson"),
            "tags": data.get("tags", []),
            "atomic_insight": data.get("atomic_insight", ""),
            "key_concepts": data.get("key_concepts", []),
            "quality": data.get("quality", "medium"),
            "source": data.get("source", "conversation"),
            "source_path": data.get("source_path", ""),
            "url": data.get("url", ""),
            "problem_solved": data.get("problem_solved", ""),
            "what_worked": data.get("what_worked", ""),
            "constraints": data.get("constraints", ""),
            "source_quality": data.get("source_quality", "medium"),
        }

        if not entry["title"] and not entry["summary"]:
            raise ValueError("Entry must have 'title' or 'summary'")

        if not entry["title"]:
            entry["title"] = entry["summary"][:100]
        if not entry["summary"]:
            entry["summary"] = entry["title"]

        return self.add(entry)

    def migrate_all(self, rewrite: bool = False) -> dict:
        """
        Migrate all entries to V2 schema.

        Args:
            rewrite: If True, rewrite entries.jsonl with migrated entries

        Returns:
            Dictionary with migration stats
        """
        if not self.jsonl_path.exists():
            return {"status": "no_entries", "total": 0, "migrated": 0}

        entries = []
        migrated_count = 0
        skipped_lines = 0

        with open(self.jsonl_path) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if not isinstance(entry, dict):
                        skipped_lines += 1
                        continue

                    original_keys = set(entry.keys())
                    migrated = migrate_entry(entry)

                    if set(migrated.keys()) != original_keys:
                        migrated_count += 1

                    entries.append(migrated)
                except json.JSONDecodeError:
                    skipped_lines += 1

        result = {
            "status": "checked",
            "total": len(entries),
            "migrated": migrated_count,
            "needs_migration": migrated_count > 0,
            "skipped_lines": skipped_lines,
        }

        if rewrite and migrated_count > 0:
            backup_path = self.jsonl_path.with_suffix(".jsonl.bak")
            import shutil

            shutil.copy(self.jsonl_path, backup_path)

            with open(self.jsonl_path, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            result["status"] = "migrated"
            result["backup"] = str(backup_path)

        return result

    def count(self) -> int:
        """Return number of entries."""
        return len(self._id_to_row) if self._id_to_row else 0


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Database CLI (fastembed)")
    parser.add_argument(
        "command",
        choices=["stats", "search", "recent", "add", "rebuild", "migrate"],
        help="Command to run",
    )
    parser.add_argument("query", nargs="?", help="Search query or entry data")
    parser.add_argument("summary", nargs="?", help="Summary text (for simple add)")
    parser.add_argument("--limit", "-n", type=int, default=5, help="Result limit")
    parser.add_argument("--project", "-p", help="Project path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--json-input", dest="json_input", help="Add structured entry from JSON")
    parser.add_argument("--check", action="store_true", help="Check migration status only")
    parser.add_argument(
        "--dense-only", action="store_true", help="Skip sparse embeddings (faster, less memory)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=50, help="Batch size for sparse embeddings"
    )
    parser.add_argument("--title", "-t", help="Entry title")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--source", "-s", help="Source identifier")
    parser.add_argument("--url", "-u", help="Source URL")

    args = parser.parse_args()

    try:
        db = KnowledgeDB(args.project)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Handle --json-input
    if args.json_input:
        try:
            data = json.loads(args.json_input)
            entry_id = db.add_structured(data)
            if args.json:
                print(json.dumps({"id": entry_id, "status": "added"}))
            else:
                print(f"Added structured entry: {entry_id}")
            sys.exit(0)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON input: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"ERROR: {e}")
            sys.exit(1)

    if args.command == "stats":
        stats = db.stats()
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print(f"Knowledge DB: {stats['db_path']}")
            print(f"Backend: {stats['backend']}")
            print(f"Entries: {stats['count']}")
            print(f"Size: {stats['size_human']}")
            print(f"Last updated: {stats['last_updated']}")

    elif args.command == "search":
        if not args.query:
            print("ERROR: Search requires a query")
            sys.exit(1)

        results = db.search(args.query, limit=args.limit)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            if not results:
                print("No results found.")
            else:
                print(f"Found {len(results)} results:\n")
                for r in results:
                    score = r.get("score", 0)
                    title = r.get("title", r.get("id", "Unknown"))
                    print(f"[{score:.2f}] {title}")
                    if r.get("url"):
                        print(f"       URL: {r['url']}")
                    if r.get("summary"):
                        print(f"       {r['summary'][:100]}...")
                    print()

    elif args.command == "recent":
        entries = db.list_recent(args.limit)

        if args.json:
            print(json.dumps(entries, indent=2))
        else:
            for e in entries:
                print(f"[{e.get('found_date', 'N/A')[:10]}] {e.get('title', 'Untitled')}")
                if e.get("url"):
                    print(f"  URL: {e['url']}")

    elif args.command == "add":
        entry = None

        if args.query and args.query.startswith("{"):
            try:
                entry = json.loads(args.query)
            except json.JSONDecodeError:
                pass

        if entry is None:
            title = args.title or args.query
            summary = args.summary or args.query

            if not title:
                print("ERROR: Add requires title")
                print('Usage: knowledge_db_fastembed.py add "Title" "Summary" [--tags t1,t2]')
                sys.exit(1)

            entry = {
                "title": title,
                "summary": summary if summary != title else title,
            }

            if args.tags:
                entry["tags"] = [t.strip() for t in args.tags.split(",")]
            if args.source:
                entry["source"] = args.source
            if args.url:
                entry["url"] = args.url

        try:
            entry_id = db.add(entry)
            print(f"Added entry: {entry_id}")
        except ValueError as e:
            print(f"ERROR: {e}")
            sys.exit(1)

    elif args.command == "rebuild":
        dense_only = getattr(args, "dense_only", False)
        batch_size = getattr(args, "batch_size", 50)
        mode = "dense-only" if dense_only else "hybrid (dense+sparse)"
        print(f"Rebuilding index from JSONL backup... (mode: {mode})")
        count = db.rebuild_index(dense_only=dense_only, batch_size=batch_size)
        backend = "fastembed" if dense_only else "fastembed-hybrid"
        print(f"Rebuilt index with {count} entries (backend: {backend})")

    elif args.command == "migrate":
        result = db.migrate_all(rewrite=not args.check)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["status"] == "no_entries":
                print("No entries to migrate.")
            elif result["status"] == "checked":
                if result["needs_migration"]:
                    print(f"Migration needed: {result['migrated']}/{result['total']} entries")
                else:
                    print(f"All {result['total']} entries have V2 schema")
            elif result["status"] == "migrated":
                print(f"Migrated {result['migrated']} entries")
                print(f"Backup: {result['backup']}")

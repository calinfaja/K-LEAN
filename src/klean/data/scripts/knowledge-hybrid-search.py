#!/usr/bin/env python3
"""
Hybrid Knowledge Search - Phase 2 Enhancement

Implements three-layer search strategy for better coverage:
1. Semantic search via txtai (embeddings)
2. Keyword search via BM25 (exact/partial matching)
3. Tag filtering and reranking

The hybrid approach catches queries that would fail with semantic-only search:
- "nrf52" (keyword) → finds "BLE power optimization in nRF52840"
- "oauth2" (keyword) → finds "OAuth implementation patterns"
- "security,oauth" (tags) → finds all OAuth-related security docs

Search pipeline:
1. Try semantic search first
2. If < 2 results, try keyword search as fallback
3. If < 2 results, try tag-based search as fallback
4. Combine and rerank all results by hybrid score
5. Filter by tags if specified

Usage:
    from knowledge_hybrid_search import HybridSearch

    db = HybridSearch()
    results = db.search(
        query="oauth2",
        strategy="hybrid",  # hybrid | semantic | keyword | tag
        tags=["security"],  # Optional tag filter
        limit=5
    )
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from knowledge_db import KnowledgeDB


class BM25:
    """Simple BM25 keyword scoring (Okapi BM25 variant)"""

    def __init__(self, documents: List[Dict[str, Any]]):
        """
        Initialize BM25 with documents.

        Args:
            documents: List of entry dictionaries with 'title' and 'summary'
        """
        self.documents = documents
        self.index = {}
        self.idf = {}
        self.avg_length = 0

        self._build_index()

    def _build_index(self):
        """Build inverted index and calculate IDF scores"""
        doc_lengths = []

        for doc_id, doc in enumerate(self.documents):
            # Tokenize document
            text = f"{doc.get('title', '')} {doc.get('summary', '')} ".lower()
            tokens = text.split()

            doc_lengths.append(len(tokens))

            # Build index
            for token in set(tokens):
                if token not in self.index:
                    self.index[token] = []
                self.index[token].append(doc_id)

        # Calculate average doc length
        self.avg_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0

        # Calculate IDF
        n_docs = len(self.documents)
        for token, doc_ids in self.index.items():
            self.idf[token] = 1.0 + __import__("math").log((n_docs - len(doc_ids) + 0.5) / (len(doc_ids) + 0.5))

    def score(self, query: str, doc_id: int) -> float:
        """
        Calculate BM25 score for query against document.

        Args:
            query: Search query string
            doc_id: Document ID (index in documents list)

        Returns:
            BM25 score (0-1 normalized)
        """
        if doc_id >= len(self.documents):
            return 0.0

        # Tokenize query
        tokens = query.lower().split()

        # BM25 parameters
        k1 = 1.5  # Term frequency saturation point
        b = 0.75  # Document length normalization

        # Get document text
        doc = self.documents[doc_id]
        text = f"{doc.get('title', '')} {doc.get('summary', '')} ".lower()
        doc_length = len(text.split())

        score = 0.0
        for token in set(tokens):
            if token not in self.index:
                continue

            # Count token occurrences in document
            tf = text.count(token)

            # BM25 formula
            idf = self.idf.get(token, 0)
            dl = doc_length
            norm = 1 - b + b * (dl / self.avg_length) if self.avg_length > 0 else 1

            score += idf * ((k1 + 1) * tf) / (k1 * norm + tf)

        # Normalize to 0-1 range
        return min(1.0, score / 100)


class HybridSearch:
    """Hybrid search combining semantic, keyword, and tag-based retrieval"""

    def __init__(self, project_path: str = None):
        """
        Initialize hybrid search engine.

        Args:
            project_path: Optional project path, auto-detects if None
        """
        self.db = KnowledgeDB(project_path)

    def search(
        self,
        query: str,
        strategy: str = "hybrid",
        tags: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search using specified strategy.

        Args:
            query: Search query string
            strategy: Search strategy (hybrid|semantic|keyword|tag)
            tags: Optional list of tags to filter by
            limit: Maximum number of results

        Returns:
            List of matching entries with scores
        """
        if strategy == "semantic":
            return self._semantic_search(query, tags, limit)
        elif strategy == "keyword":
            return self._keyword_search(query, tags, limit)
        elif strategy == "tag":
            return self._tag_search(tags, limit) if tags else []
        else:  # hybrid
            return self._hybrid_search(query, tags, limit)

    def _semantic_search(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Semantic search via txtai embeddings"""
        results = self.db.search(query, limit=limit * 2)  # Get extra to filter

        # Filter by tags if specified
        if tags:
            results = [
                r for r in results if any(t in r.get("tags", []) for t in tags)
            ]

        # Sort by semantic score and return
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:limit]

    def _keyword_search(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Keyword search via BM25"""
        # Load all entries from JSONL for keyword indexing
        if not self.db.jsonl_path.exists():
            return []

        entries = []
        with open(self.db.jsonl_path) as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        if not entries:
            return []

        # Filter by tags if specified
        if tags:
            entries = [
                e for e in entries if any(t in e.get("tags", []) for t in tags)
            ]

        # Build BM25 index and score
        bm25 = BM25(entries)
        scores = []
        for i, entry in enumerate(entries):
            score = bm25.score(query, i)
            if score > 0:
                scores.append((entry.get("id"), score, entry))

        # Sort by score and return
        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for entry_id, score, entry in scores[:limit]:
            # Enrich with txtai result format
            result = {
                "score": score,
                "id": entry.get("id"),
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "url": entry.get("url", ""),
                "type": entry.get("type", ""),
                "problem_solved": entry.get("problem_solved", ""),
                "key_concepts": entry.get("key_concepts", []),
                "relevance_score": entry.get("relevance_score", 0),
                "what_worked": entry.get("what_worked", ""),
                "constraints": entry.get("constraints", ""),
                "found_date": entry.get("found_date", ""),
                "confidence_score": entry.get("confidence_score", 0.7),
                "tags": entry.get("tags", []),
                "usage_count": entry.get("usage_count", 0),
                "last_used": entry.get("last_used"),
                "source_quality": entry.get("source_quality", "medium"),
            }
            results.append(result)

        return results

    def _tag_search(
        self,
        tags: List[str],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Tag-based search"""
        if not self.db.jsonl_path.exists():
            return []

        results = []
        with open(self.db.jsonl_path) as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    entry_tags = entry.get("tags", [])

                    # Count matching tags
                    matching = sum(1 for t in tags if t in entry_tags)
                    if matching > 0:
                        score = matching / len(tags)  # Percentage of tags matched
                        result = {
                            "score": score,
                            "id": entry.get("id"),
                            "title": entry.get("title", ""),
                            "summary": entry.get("summary", ""),
                            "url": entry.get("url", ""),
                            "type": entry.get("type", ""),
                            "problem_solved": entry.get("problem_solved", ""),
                            "key_concepts": entry.get("key_concepts", []),
                            "relevance_score": entry.get("relevance_score", 0),
                            "what_worked": entry.get("what_worked", ""),
                            "constraints": entry.get("constraints", ""),
                            "found_date": entry.get("found_date", ""),
                            "confidence_score": entry.get("confidence_score", 0.7),
                            "tags": entry.get("tags", []),
                            "usage_count": entry.get("usage_count", 0),
                            "last_used": entry.get("last_used"),
                            "source_quality": entry.get("source_quality", "medium"),
                        }
                        results.append(result)

        # Sort by score and return
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:limit]

    def _hybrid_search(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search with intelligent fallback and reranking.

        Strategy:
        1. Try semantic search first
        2. If < 2 results, try keyword search
        3. If < 2 results, try tag search
        4. Combine results and rerank by hybrid score
        5. Return top N
        """
        # Layer 1: Semantic search
        semantic_results = self._semantic_search(query, tags, limit * 2)

        # Layer 2: Keyword search (fallback if semantic weak)
        if len(semantic_results) < 2:
            keyword_results = self._keyword_search(query, tags, limit * 2)
        else:
            keyword_results = self._keyword_search(query, tags, limit * 2)

        # Layer 3: Tag search (if tags specified and still weak)
        tag_results = []
        if tags and (len(semantic_results) + len(keyword_results)) < 2:
            tag_results = self._tag_search(tags, limit * 2)

        # Combine results by ID, keeping best score from any source
        combined = {}
        for result in semantic_results:
            entry_id = result["id"]
            combined[entry_id] = {
                **result,
                "semantic_score": result.get("score", 0),
                "keyword_score": 0,
                "tag_score": 0,
            }

        for result in keyword_results:
            entry_id = result["id"]
            if entry_id not in combined:
                combined[entry_id] = {
                    **result,
                    "semantic_score": 0,
                    "keyword_score": result.get("score", 0),
                    "tag_score": 0,
                }
            else:
                combined[entry_id]["keyword_score"] = result.get("score", 0)

        for result in tag_results:
            entry_id = result["id"]
            if entry_id not in combined:
                combined[entry_id] = {
                    **result,
                    "semantic_score": 0,
                    "keyword_score": 0,
                    "tag_score": result.get("score", 0),
                }
            else:
                combined[entry_id]["tag_score"] = result.get("score", 0)

        # Rerank by hybrid score
        # Weights favor semantic but give weight to keyword matches
        for entry_id, result in combined.items():
            entry_dict = result.copy()
            semantic = entry_dict.pop("semantic_score", 0)
            keyword = entry_dict.pop("keyword_score", 0)
            tag_score = entry_dict.pop("tag_score", 0)
            usage = entry_dict.get("usage_count") or 0
            confidence = entry_dict.get("confidence_score") or 0.7

            # Hybrid ranking formula
            # 40% semantic + 30% keyword + 15% tag + 10% usage + 5% confidence
            hybrid_score = (
                0.40 * semantic
                + 0.30 * keyword
                + 0.15 * tag_score
                + 0.10 * min(usage / 10, 1.0) if usage else 0  # Cap usage at 10
                + 0.05 * confidence
            )

            result["score"] = hybrid_score
            result["hybrid_breakdown"] = {
                "semantic": round(semantic, 3),
                "keyword": round(keyword, 3),
                "tag": round(tag_score, 3),
                "usage": round(min(usage / 10, 1.0), 3),
                "confidence": round(confidence, 3),
            }

        # Sort by hybrid score
        results = list(combined.values())
        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return results[:limit]


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Hybrid knowledge search")
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--strategy",
        choices=["hybrid", "semantic", "keyword", "tag"],
        default="hybrid",
        help="Search strategy (default: hybrid)",
    )
    parser.add_argument(
        "--tags", help="Comma-separated tags to filter by"
    )
    parser.add_argument(
        "--limit", "-n", type=int, default=5, help="Result limit"
    )
    parser.add_argument(
        "--project", "-p", help="Project path"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed scores"
    )

    args = parser.parse_args()

    try:
        search = HybridSearch(args.project)
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else None

        results = search.search(
            query=args.query,
            strategy=args.strategy,
            tags=tags,
            limit=args.limit,
        )

        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            if not results:
                print("No results found.")
            else:
                print(f"Found {len(results)} results ({args.strategy} search):\n")
                for r in results:
                    score = r.get("score", 0)
                    title = r.get("title", r.get("id", "Unknown"))
                    print(f"[{score:.3f}] {title}")

                    if args.verbose and "hybrid_breakdown" in r:
                        breakdown = r["hybrid_breakdown"]
                        print(f"  Breakdown: {breakdown}")

                    if r.get("url"):
                        print(f"  URL: {r['url']}")
                    if r.get("summary"):
                        print(f"  {r['summary'][:100]}...")
                    print()

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

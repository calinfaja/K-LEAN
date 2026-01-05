"""Memory system for SmolKLN agents.

Provides session memory and Knowledge DB integration for agent execution.
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class MemoryEntry:
    """Single memory entry."""

    content: str
    timestamp: float
    entry_type: str  # "action", "result", "lesson", "error"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize entry to dictionary."""
        return {
            "content": self.content,
            "timestamp": self.timestamp,
            "entry_type": self.entry_type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        """Deserialize entry from dictionary."""
        return cls(
            content=data["content"],
            timestamp=data["timestamp"],
            entry_type=data["entry_type"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class SessionMemory:
    """Memory for current session."""

    task: str
    entries: list[MemoryEntry] = field(default_factory=list)
    max_entries: int = 50
    start_time: float = field(default_factory=time.time)

    def add(self, content: str, entry_type: str, **metadata):
        """Add entry to session memory."""
        self.entries.append(
            MemoryEntry(
                content=content, timestamp=time.time(), entry_type=entry_type, metadata=metadata
            )
        )
        # Trim if exceeds max
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]

    def get_context(self, max_tokens: int = 2000) -> str:
        """Get session context string, limited by token estimate."""
        parts = []
        tokens = 0
        for entry in reversed(self.entries):
            # Rough token estimate: 1.3 tokens per word
            entry_tokens = len(entry.content.split()) * 1.3
            if tokens + entry_tokens > max_tokens:
                break
            parts.insert(0, f"[{entry.entry_type}] {entry.content}")
            tokens += entry_tokens
        return "\n".join(parts)

    def get_history(self) -> list[dict[str, Any]]:
        """Get full history as list of dicts (for inspection/debugging)."""
        return [entry.to_dict() for entry in self.entries]

    def to_dict(self) -> dict[str, Any]:
        """Serialize session to dictionary."""
        return {
            "task": self.task,
            "start_time": self.start_time,
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionMemory":
        """Deserialize session from dictionary."""
        session = cls(
            task=data["task"],
            start_time=data.get("start_time", time.time()),
        )
        session.entries = [MemoryEntry.from_dict(e) for e in data.get("entries", [])]
        return session


class AgentMemory:
    """Complete memory system for an agent.

    Integrates:
    - Session memory (working context)
    - Knowledge DB (long-term storage)
    """

    def __init__(self, project_context):
        """Initialize memory with project context.

        Args:
            project_context: ProjectContext from context.py
        """
        self.project_context = project_context
        self.session: Optional[SessionMemory] = None
        self._knowledge_db = None

    @property
    def knowledge_db(self):
        """Lazy-load Knowledge DB connection."""
        if self._knowledge_db is None and self.project_context.has_knowledge_db:
            try:
                import sys

                scripts_dir = Path.home() / ".claude" / "scripts"
                if str(scripts_dir) not in sys.path:
                    sys.path.insert(0, str(scripts_dir))
                from knowledge_db import KnowledgeDB

                self._knowledge_db = KnowledgeDB(str(self.project_context.project_root))
            except ImportError:
                pass
            except Exception:
                pass
        return self._knowledge_db

    def start_session(self, task: str):
        """Start a new memory session for a task."""
        self.session = SessionMemory(task=task)

    def record(self, content: str, entry_type: str, **metadata):
        """Record entry to current session."""
        if self.session:
            self.session.add(content, entry_type, **metadata)

    def query_knowledge(self, query: str, limit: int = 5) -> list[dict]:
        """Query Knowledge DB for relevant information.

        Args:
            query: Search query
            limit: Max results to return

        Returns:
            List of matching entries with content and score
        """
        if self.knowledge_db is None:
            return []
        try:
            return self.knowledge_db.search(query, limit=limit)
        except Exception:
            return []

    def save_lesson(self, lesson: str, category: str = "agent_learning") -> bool:
        """Save a lesson learned to Knowledge DB.

        Args:
            lesson: The lesson content
            category: Category for the lesson

        Returns:
            True if saved successfully
        """
        if self.knowledge_db is None:
            return False
        try:
            self.knowledge_db.add(
                {
                    "content": lesson,
                    "category": category,
                    "source": "smolkln_agent",
                    "timestamp": time.time(),
                }
            )
            return True
        except Exception:
            return False

    def get_augmented_context(self) -> str:
        """Get combined context from session history and prior knowledge.

        Returns:
            Formatted context string for agent prompt
        """
        parts = []

        # Session history
        if self.session:
            history = self.session.get_context(max_tokens=1500)
            if history:
                parts.append(f"## Session History\n{history}")

        # Prior knowledge from Knowledge DB
        if self.session and self.knowledge_db:
            results = self.query_knowledge(self.session.task, limit=3)
            if results:
                knowledge_items = []
                for r in results:
                    # Filter by relevance score
                    if r.get("score", 0) > 0.3:
                        title = r.get("title", "Lesson")
                        content = r.get("content", "")[:200]
                        knowledge_items.append(f"- {title}: {content}")

                if knowledge_items:
                    knowledge = "\n".join(knowledge_items)
                    parts.append(f"## Prior Knowledge\n{knowledge}")

        return "\n\n".join(parts)

    def persist_session_to_kb(self, agent_name: str) -> int:
        """Persist meaningful session memory entries to Knowledge DB.

        Saves 'result' and 'lesson' type entries so future agents can
        learn from past executions.

        Args:
            agent_name: Name of the agent that ran

        Returns:
            Number of entries persisted
        """
        if self.knowledge_db is None or self.session is None:
            return 0

        persisted = 0
        session_id = f"{agent_name}_{int(self.session.start_time)}"

        for entry in self.session.entries:
            # Only persist meaningful entries (results and lessons)
            if entry.entry_type not in ("result", "lesson"):
                continue

            # Skip very short entries
            if len(entry.content) < 20:
                continue

            try:
                # Extract a title from the content
                content_lines = entry.content.strip().split("\n")
                title = content_lines[0][:100] if content_lines else "Agent finding"

                self.knowledge_db.add_structured(
                    {
                        "title": title,
                        "summary": entry.content[:500],
                        "type": "lesson" if entry.entry_type == "lesson" else "solution",
                        "source": f"agent_{agent_name}",
                        "tags": [agent_name, "smolkln", entry.entry_type],
                        "key_concepts": [agent_name],
                        "quality": "medium",
                        # Store session metadata
                        "source_path": session_id,
                    }
                )
                persisted += 1
            except Exception:
                # Don't fail execution if persistence fails
                pass

        return persisted

    def sync_serena_to_kb(self, serena_content: str) -> int:
        """Sync Serena lessons-learned content to Knowledge DB.

        Parses the lessons-learned markdown and imports each lesson
        as a searchable KB entry.

        Args:
            serena_content: Raw content from Serena lessons-learned memory

        Returns:
            Number of lessons synced
        """
        if self.knowledge_db is None:
            return 0

        synced = 0
        current_lesson = {}
        current_content = []

        for line in serena_content.split("\n"):
            # Detect lesson headers (### GOTCHA:, ### TIP:, ### PATTERN:, etc.)
            if line.startswith("### "):
                # Save previous lesson if exists
                if current_lesson.get("title"):
                    self._save_serena_lesson(current_lesson, "\n".join(current_content))
                    synced += 1

                # Parse new lesson header
                header = line[4:].strip()
                lesson_type = "lesson"
                if header.startswith("GOTCHA:"):
                    lesson_type = "warning"
                    header = header[7:].strip()
                elif header.startswith("TIP:"):
                    lesson_type = "tip"
                    header = header[4:].strip()
                elif header.startswith("PATTERN:"):
                    lesson_type = "pattern"
                    header = header[8:].strip()

                current_lesson = {
                    "title": header,
                    "type": lesson_type,
                }
                current_content = []

            elif line.startswith("**Date**:"):
                current_lesson["date"] = line.split(":", 1)[1].strip()
            elif line.startswith("**Context**:"):
                current_lesson["context"] = line.split(":", 1)[1].strip()
            elif current_lesson.get("title"):
                current_content.append(line)

        # Save last lesson
        if current_lesson.get("title"):
            self._save_serena_lesson(current_lesson, "\n".join(current_content))
            synced += 1

        return synced

    def _save_serena_lesson(self, lesson: dict, content: str) -> bool:
        """Save a single Serena lesson to KB."""
        if self.knowledge_db is None:
            return False

        try:
            # Check if already synced (by title + source)
            existing = self.knowledge_db.search(lesson["title"], limit=1)
            for e in existing:
                if e.get("source") == "serena" and e.get("title") == lesson["title"]:
                    return False  # Already exists

            self.knowledge_db.add_structured(
                {
                    "title": lesson["title"],
                    "summary": content.strip()[:1000],
                    "type": lesson.get("type", "lesson"),
                    "source": "serena",
                    "tags": ["serena", "lessons-learned", lesson.get("type", "lesson")],
                    "key_concepts": [lesson.get("context", "")] if lesson.get("context") else [],
                    "quality": "high",  # Serena lessons are curated
                    "source_path": f"serena:{lesson.get('date', 'unknown')}",
                }
            )
            return True
        except Exception:
            return False

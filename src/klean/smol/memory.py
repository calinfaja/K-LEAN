"""Memory system for SmolKLN agents.

Provides session memory and Knowledge DB integration for agent execution.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import time


@dataclass
class MemoryEntry:
    """Single memory entry."""
    content: str
    timestamp: float
    entry_type: str  # "action", "result", "lesson", "error"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionMemory:
    """Memory for current session."""
    task: str
    entries: List[MemoryEntry] = field(default_factory=list)
    max_entries: int = 50

    def add(self, content: str, entry_type: str, **metadata):
        """Add entry to session memory."""
        self.entries.append(MemoryEntry(
            content=content,
            timestamp=time.time(),
            entry_type=entry_type,
            metadata=metadata
        ))
        # Trim if exceeds max
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

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

    def query_knowledge(self, query: str, limit: int = 5) -> List[Dict]:
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
            self.knowledge_db.add({
                "content": lesson,
                "category": category,
                "source": "smolkln_agent",
                "timestamp": time.time()
            })
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
                    if r.get('score', 0) > 0.3:
                        title = r.get('title', 'Lesson')
                        content = r.get('content', '')[:200]
                        knowledge_items.append(f"- {title}: {content}")

                if knowledge_items:
                    knowledge = "\n".join(knowledge_items)
                    parts.append(f"## Prior Knowledge\n{knowledge}")

        return "\n\n".join(parts)

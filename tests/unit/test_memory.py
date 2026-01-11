"""Unit tests for klean.smol.memory module.

Tests memory system for agent execution:
- MemoryEntry serialization
- SessionMemory operations (add, trim, get_context)
- AgentMemory integration

ANTI-FALSE-POSITIVE MEASURES:
1. Test serialization roundtrip with actual data
2. Verify token limit truncation works correctly
3. Test max_entries trimming behavior
4. Check all dataclass fields are preserved
"""

import time
from unittest.mock import MagicMock

# Import module under test
from klean.smol.memory import (
    AgentMemory,
    MemoryEntry,
    SessionMemory,
)

# =============================================================================
# TestMemoryEntry
# =============================================================================

class TestMemoryEntry:
    """Tests for MemoryEntry dataclass."""

    def test_creates_with_required_fields(self):
        """Should create entry with required fields."""
        # Act
        entry = MemoryEntry(
            content="Test content",
            timestamp=1234567890.0,
            entry_type="action"
        )

        # Assert
        assert entry.content == "Test content"
        assert entry.timestamp == 1234567890.0
        assert entry.entry_type == "action"
        assert entry.metadata == {}

    def test_to_dict_serialization(self):
        """Should serialize to dictionary correctly."""
        # Arrange
        entry = MemoryEntry(
            content="Found issue",
            timestamp=1000.0,
            entry_type="result",
            metadata={"file": "test.py", "line": 42}
        )

        # Act
        data = entry.to_dict()

        # Assert
        assert isinstance(data, dict)
        assert data["content"] == "Found issue"
        assert data["timestamp"] == 1000.0
        assert data["entry_type"] == "result"
        assert data["metadata"]["file"] == "test.py"
        assert data["metadata"]["line"] == 42

    def test_from_dict_deserialization(self):
        """Should deserialize from dictionary correctly."""
        # Arrange
        data = {
            "content": "Lesson learned",
            "timestamp": 2000.0,
            "entry_type": "lesson",
            "metadata": {"importance": "high"}
        }

        # Act
        entry = MemoryEntry.from_dict(data)

        # Assert
        assert isinstance(entry, MemoryEntry)
        assert entry.content == "Lesson learned"
        assert entry.timestamp == 2000.0
        assert entry.entry_type == "lesson"
        assert entry.metadata["importance"] == "high"

    def test_serialization_roundtrip(self):
        """Should preserve all fields through serialization roundtrip."""
        # Arrange
        original = MemoryEntry(
            content="Complex content with\nmultiple lines",
            timestamp=time.time(),
            entry_type="error",
            metadata={"nested": {"key": "value"}, "list": [1, 2, 3]}
        )

        # Act
        data = original.to_dict()
        restored = MemoryEntry.from_dict(data)

        # Assert
        assert restored.content == original.content
        assert restored.timestamp == original.timestamp
        assert restored.entry_type == original.entry_type
        assert restored.metadata == original.metadata

    def test_handles_missing_metadata_in_dict(self):
        """Should handle dict without metadata field."""
        # Arrange
        data = {
            "content": "Test",
            "timestamp": 1000.0,
            "entry_type": "action"
        }

        # Act
        entry = MemoryEntry.from_dict(data)

        # Assert
        assert entry.metadata == {}


# =============================================================================
# TestSessionMemory
# =============================================================================

class TestSessionMemory:
    """Tests for SessionMemory class."""

    def test_creates_with_task(self):
        """Should create session with task."""
        # Act
        session = SessionMemory(task="Security audit")

        # Assert
        assert session.task == "Security audit"
        assert session.entries == []
        assert session.max_entries == 50
        assert session.start_time > 0

    def test_add_entry(self):
        """Should add entry to session."""
        # Arrange
        session = SessionMemory(task="Test")

        # Act
        session.add("Found vulnerability", "result", file="auth.py")

        # Assert
        assert len(session.entries) == 1
        assert session.entries[0].content == "Found vulnerability"
        assert session.entries[0].entry_type == "result"
        assert session.entries[0].metadata["file"] == "auth.py"
        assert session.entries[0].timestamp > 0

    def test_trims_to_max_entries(self):
        """Should trim entries when exceeding max_entries."""
        # Arrange
        session = SessionMemory(task="Test", max_entries=5)

        # Act - add 7 entries
        for i in range(7):
            session.add(f"Entry {i}", "action")

        # Assert - should only have last 5
        assert len(session.entries) == 5
        assert session.entries[0].content == "Entry 2"
        assert session.entries[-1].content == "Entry 6"

    def test_get_context_formats_entries(self):
        """Should format entries for context string."""
        # Arrange
        session = SessionMemory(task="Test")
        session.add("First action", "action")
        session.add("Result found", "result")

        # Act
        context = session.get_context()

        # Assert
        assert "[action] First action" in context
        assert "[result] Result found" in context

    def test_get_context_respects_token_limit(self):
        """Should limit context by estimated tokens."""
        # Arrange
        session = SessionMemory(task="Test")
        # Add entries with known word count
        for _ in range(10):
            session.add("word " * 50, "action")  # 50 words each

        # Act - request small token limit
        context = session.get_context(max_tokens=100)

        # Assert - should be truncated
        lines = context.strip().split("\n")
        assert len(lines) < 10, "Should limit entries by token estimate"

    def test_get_history_returns_list(self):
        """Should return list of dicts for history."""
        # Arrange
        session = SessionMemory(task="Test")
        session.add("Action 1", "action")
        session.add("Result 1", "result")

        # Act
        history = session.get_history()

        # Assert
        assert isinstance(history, list)
        assert len(history) == 2
        assert all(isinstance(h, dict) for h in history)
        assert history[0]["entry_type"] == "action"

    def test_to_dict_serialization(self):
        """Should serialize session to dict."""
        # Arrange
        session = SessionMemory(task="Audit")
        session.add("Entry 1", "action")

        # Act
        data = session.to_dict()

        # Assert
        assert data["task"] == "Audit"
        assert "start_time" in data
        assert len(data["entries"]) == 1

    def test_from_dict_deserialization(self):
        """Should deserialize session from dict."""
        # Arrange
        data = {
            "task": "Review",
            "start_time": 1000.0,
            "entries": [
                {"content": "Test", "timestamp": 1001.0, "entry_type": "action", "metadata": {}}
            ]
        }

        # Act
        session = SessionMemory.from_dict(data)

        # Assert
        assert session.task == "Review"
        assert session.start_time == 1000.0
        assert len(session.entries) == 1
        assert session.entries[0].content == "Test"

    def test_serialization_roundtrip(self):
        """Should preserve all data through serialization roundtrip."""
        # Arrange
        original = SessionMemory(task="Complex task")
        original.add("Action 1", "action", key="value")
        original.add("Result 1", "result")

        # Act
        data = original.to_dict()
        restored = SessionMemory.from_dict(data)

        # Assert
        assert restored.task == original.task
        assert len(restored.entries) == len(original.entries)
        assert restored.entries[0].content == original.entries[0].content
        assert restored.entries[0].metadata == original.entries[0].metadata


# =============================================================================
# TestAgentMemory
# =============================================================================

class TestAgentMemory:
    """Tests for AgentMemory class."""

    def _mock_project_context(self, tmp_path, has_kb=False):
        """Create mock project context."""
        mock_ctx = MagicMock()
        mock_ctx.project_root = tmp_path
        mock_ctx.has_knowledge_db = has_kb
        mock_ctx.knowledge_db_path = tmp_path / ".knowledge-db" if has_kb else None
        return mock_ctx

    def test_initialization(self, tmp_path):
        """Should initialize with project context."""
        # Arrange
        ctx = self._mock_project_context(tmp_path)

        # Act
        memory = AgentMemory(ctx)

        # Assert
        assert memory.project_context == ctx
        assert memory.session is None

    def test_start_session(self, tmp_path):
        """Should start new session with task."""
        # Arrange
        ctx = self._mock_project_context(tmp_path)
        memory = AgentMemory(ctx)

        # Act
        memory.start_session("Security audit of auth module")

        # Assert
        assert memory.session is not None
        assert memory.session.task == "Security audit of auth module"
        assert len(memory.session.entries) == 0

    def test_record_to_session(self, tmp_path):
        """Should record entry to current session."""
        # Arrange
        ctx = self._mock_project_context(tmp_path)
        memory = AgentMemory(ctx)
        memory.start_session("Test task")

        # Act
        memory.record("Found issue", "result", severity="high")

        # Assert
        assert len(memory.session.entries) == 1
        assert memory.session.entries[0].content == "Found issue"
        assert memory.session.entries[0].metadata["severity"] == "high"

    def test_record_noop_without_session(self, tmp_path):
        """Should not raise when recording without session."""
        # Arrange
        ctx = self._mock_project_context(tmp_path)
        memory = AgentMemory(ctx)

        # Act - should not raise
        memory.record("Test", "action")

        # Assert
        assert memory.session is None

    def test_query_knowledge_returns_empty_without_kb(self, tmp_path):
        """Should return empty list when no KB available."""
        # Arrange
        ctx = self._mock_project_context(tmp_path, has_kb=False)
        memory = AgentMemory(ctx)

        # Act
        results = memory.query_knowledge("test query")

        # Assert
        assert results == []
        assert isinstance(results, list)

    def test_save_lesson_returns_false_without_kb(self, tmp_path):
        """Should return False when no KB available."""
        # Arrange
        ctx = self._mock_project_context(tmp_path, has_kb=False)
        memory = AgentMemory(ctx)

        # Act
        result = memory.save_lesson("Test lesson")

        # Assert
        assert result is False

    def test_get_augmented_context_with_session(self, tmp_path):
        """Should include session history in context."""
        # Arrange
        ctx = self._mock_project_context(tmp_path)
        memory = AgentMemory(ctx)
        memory.start_session("Test task")
        memory.record("First action", "action")
        memory.record("Found something", "result")

        # Act
        context = memory.get_augmented_context()

        # Assert
        assert "Session History" in context
        assert "First action" in context
        assert "Found something" in context

    def test_get_augmented_context_empty_without_session(self, tmp_path):
        """Should return empty string without session."""
        # Arrange
        ctx = self._mock_project_context(tmp_path)
        memory = AgentMemory(ctx)

        # Act
        context = memory.get_augmented_context()

        # Assert
        assert context == ""

    def test_persist_session_returns_zero_without_kb(self, tmp_path):
        """Should return 0 when no KB available."""
        # Arrange
        ctx = self._mock_project_context(tmp_path, has_kb=False)
        memory = AgentMemory(ctx)
        memory.start_session("Test")
        memory.record("Result content here", "result")

        # Act
        count = memory.persist_session_to_kb("test-agent")

        # Assert
        assert count == 0

    def test_persist_session_returns_zero_without_session(self, tmp_path):
        """Should return 0 when no session active."""
        # Arrange
        ctx = self._mock_project_context(tmp_path, has_kb=True)
        memory = AgentMemory(ctx)

        # Act
        count = memory.persist_session_to_kb("test-agent")

        # Assert
        assert count == 0


# =============================================================================
# TestSyncSerenaToKb
# =============================================================================

class TestSyncSerenaToKb:
    """Tests for sync_serena_to_kb() method."""

    def _mock_project_context(self, tmp_path, has_kb=False):
        """Create mock project context."""
        mock_ctx = MagicMock()
        mock_ctx.project_root = tmp_path
        mock_ctx.has_knowledge_db = has_kb
        mock_ctx.knowledge_db_path = tmp_path / ".knowledge-db" if has_kb else None
        return mock_ctx

    def test_returns_zero_without_kb(self, tmp_path):
        """Should return 0 when no KB available."""
        # Arrange
        ctx = self._mock_project_context(tmp_path, has_kb=False)
        memory = AgentMemory(ctx)
        content = "### GOTCHA: Test gotcha\nSome content"

        # Act
        count = memory.sync_serena_to_kb(content)

        # Assert
        assert count == 0

    def test_parses_lesson_headers(self, tmp_path):
        """Should parse different lesson types from headers."""
        # Arrange
        ctx = self._mock_project_context(tmp_path, has_kb=True)
        memory = AgentMemory(ctx)

        # Mock KB to capture calls
        mock_kb = MagicMock()
        mock_kb.search.return_value = []  # No existing lessons
        memory._knowledge_db = mock_kb

        content = """### GOTCHA: Don't use eval
**Date**: 2024-01-01
Content about why eval is bad.

### TIP: Use pathlib
**Date**: 2024-01-02
Content about pathlib advantages.

### PATTERN: Factory pattern
**Date**: 2024-01-03
Content about factories.
"""

        # Act
        count = memory.sync_serena_to_kb(content)

        # Assert - 3 lessons parsed
        assert count == 3
        # Verify add_structured was called 3 times
        assert mock_kb.add_structured.call_count == 3

    def test_extracts_date_and_context(self, tmp_path):
        """Should extract date and context from lesson."""
        # Arrange
        ctx = self._mock_project_context(tmp_path, has_kb=True)
        memory = AgentMemory(ctx)

        mock_kb = MagicMock()
        mock_kb.search.return_value = []
        memory._knowledge_db = mock_kb

        content = """### GOTCHA: Test lesson
**Date**: 2024-12-25
**Context**: Python testing
The lesson content goes here.
"""

        # Act
        memory.sync_serena_to_kb(content)

        # Assert - verify structured data passed to KB
        call_args = mock_kb.add_structured.call_args[0][0]
        assert call_args["title"] == "Test lesson"
        assert call_args["source"] == "serena"
        assert "serena" in call_args["tags"]


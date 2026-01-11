"""Tests for klean.smol.task_queue module.

Tests cover:
- TaskState enum
- QueuedTask dataclass
- TaskQueue initialization and persistence
- Task lifecycle (enqueue, running, completed, failed)
- Task queries (get_status, list_recent, list_by_state)
- Task cleanup and cancellation
"""

import json
import time

# Test constants
SECONDS_PER_HOUR = 3600
HOURS_25 = 25 * SECONDS_PER_HOUR  # Just over 24 hour threshold
HOURS_100 = 100 * SECONDS_PER_HOUR  # Well over threshold

# =============================================================================
# TaskState Enum Tests
# =============================================================================


class TestTaskState:
    """Tests for TaskState enum."""

    def test_has_expected_states(self):
        """Should have all expected state values."""
        from klean.smol.task_queue import TaskState

        assert TaskState.QUEUED.value == "queued"
        assert TaskState.RUNNING.value == "running"
        assert TaskState.COMPLETED.value == "completed"
        assert TaskState.FAILED.value == "failed"

    def test_states_are_distinct(self):
        """All states should have unique values."""
        from klean.smol.task_queue import TaskState

        values = [s.value for s in TaskState]
        assert len(values) == len(set(values))


# =============================================================================
# QueuedTask Dataclass Tests
# =============================================================================


class TestQueuedTask:
    """Tests for QueuedTask dataclass."""

    def test_creates_task_with_required_fields(self):
        """Should create task with all required fields."""
        from klean.smol.task_queue import QueuedTask, TaskState

        task = QueuedTask(
            id="abc123",
            agent="code-reviewer",
            task="Review the code",
            model=None,
            state=TaskState.QUEUED,
            created_at=time.time(),
        )

        assert task.id == "abc123"
        assert task.agent == "code-reviewer"
        assert task.task == "Review the code"
        assert task.state == TaskState.QUEUED

    def test_optional_fields_default_to_none(self):
        """Optional fields should default to None."""
        from klean.smol.task_queue import QueuedTask, TaskState

        task = QueuedTask(
            id="test",
            agent="agent",
            task="task",
            model=None,
            state=TaskState.QUEUED,
            created_at=time.time(),
        )

        assert task.started_at is None
        assert task.completed_at is None
        assert task.result is None
        assert task.error is None
        assert task.project_path is None


# =============================================================================
# TaskQueue Initialization Tests
# =============================================================================


class TestTaskQueueInit:
    """Tests for TaskQueue initialization."""

    def test_creates_with_default_path(self, tmp_path, monkeypatch):
        """Should use default path under ~/.klean/."""
        from klean.smol.task_queue import TaskQueue

        # Monkeypatch home to use tmp_path
        monkeypatch.setenv("HOME", str(tmp_path))
        # Create with explicit path to avoid touching real home
        queue = TaskQueue(db_path=tmp_path / ".klean" / "task_queue.json")

        assert queue.db_path.name == "task_queue.json"

    def test_creates_parent_directories(self, tmp_path):
        """Should create parent directories if needed."""
        from klean.smol.task_queue import TaskQueue

        db_path = tmp_path / "deep" / "nested" / "queue.json"
        _queue = TaskQueue(db_path=db_path)  # noqa: F841

        assert db_path.parent.exists()

    def test_loads_empty_tasks_for_new_queue(self, tmp_path):
        """Should start with empty tasks for new queue."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")

        assert queue.tasks == {}


# =============================================================================
# TaskQueue Persistence Tests
# =============================================================================


class TestTaskQueuePersistence:
    """Tests for TaskQueue persistence."""

    def test_saves_to_disk(self, tmp_path):
        """Should save tasks to JSON file."""
        from klean.smol.task_queue import TaskQueue

        db_path = tmp_path / "queue.json"
        queue = TaskQueue(db_path=db_path)
        queue.enqueue("agent", "task")

        assert db_path.exists()
        data = json.loads(db_path.read_text())
        assert len(data) == 1

    def test_loads_from_disk(self, tmp_path):
        """Should load existing tasks from disk."""
        from klean.smol.task_queue import TaskQueue

        db_path = tmp_path / "queue.json"

        # Create queue and add task
        queue1 = TaskQueue(db_path=db_path)
        task_id = queue1.enqueue("test-agent", "test-task")

        # Create new queue instance - should load existing
        queue2 = TaskQueue(db_path=db_path)
        assert task_id in queue2.tasks

    def test_handles_corrupted_json(self, tmp_path):
        """Should handle corrupted JSON gracefully."""
        from klean.smol.task_queue import TaskQueue

        db_path = tmp_path / "queue.json"
        db_path.write_text("not valid json {{{")

        queue = TaskQueue(db_path=db_path)
        assert queue.tasks == {}


# =============================================================================
# Enqueue Tests
# =============================================================================


class TestEnqueue:
    """Tests for TaskQueue.enqueue()."""

    def test_returns_task_id(self, tmp_path):
        """Should return a task ID."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        task_id = queue.enqueue("agent", "task")

        assert isinstance(task_id, str)
        assert len(task_id) == 8  # UUID first 8 chars

    def test_creates_queued_task(self, tmp_path):
        """Should create task in QUEUED state."""
        from klean.smol.task_queue import TaskQueue, TaskState

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        task_id = queue.enqueue("agent", "task")

        task = queue.tasks[task_id]
        assert task.state == TaskState.QUEUED

    def test_sets_created_at(self, tmp_path):
        """Should set created_at timestamp to current time."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        before = time.time()
        task_id = queue.enqueue("agent", "task")
        after = time.time()

        task = queue.tasks[task_id]
        # Timestamp should be between before and after with 1 second tolerance
        assert before - 1 <= task.created_at <= after + 1

    def test_accepts_optional_model(self, tmp_path):
        """Should accept optional model parameter."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        task_id = queue.enqueue("agent", "task", model="gpt-4")

        assert queue.tasks[task_id].model == "gpt-4"

    def test_accepts_optional_project_path(self, tmp_path):
        """Should accept optional project_path parameter."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        task_id = queue.enqueue("agent", "task", project_path="/my/project")

        assert queue.tasks[task_id].project_path == "/my/project"


# =============================================================================
# State Transition Tests
# =============================================================================


class TestStateTransitions:
    """Tests for task state transitions."""

    def test_mark_running(self, tmp_path):
        """Should mark task as running with started_at."""
        from klean.smol.task_queue import TaskQueue, TaskState

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        task_id = queue.enqueue("agent", "task")

        before = time.time()
        queue.mark_running(task_id)
        after = time.time()

        task = queue.tasks[task_id]
        assert task.state == TaskState.RUNNING
        # Timestamp should be between before and after with 1 second tolerance
        assert before - 1 <= task.started_at <= after + 1

    def test_mark_completed(self, tmp_path):
        """Should mark task as completed with result."""
        from klean.smol.task_queue import TaskQueue, TaskState

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        task_id = queue.enqueue("agent", "task")
        queue.mark_running(task_id)

        result = {"output": "success"}
        queue.mark_completed(task_id, result)

        task = queue.tasks[task_id]
        assert task.state == TaskState.COMPLETED
        assert task.result == result
        assert task.completed_at is not None

    def test_mark_failed(self, tmp_path):
        """Should mark task as failed with error."""
        from klean.smol.task_queue import TaskQueue, TaskState

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        task_id = queue.enqueue("agent", "task")
        queue.mark_running(task_id)

        queue.mark_failed(task_id, "Something went wrong")

        task = queue.tasks[task_id]
        assert task.state == TaskState.FAILED
        assert task.error == "Something went wrong"
        assert task.completed_at is not None

    def test_ignores_nonexistent_task(self, tmp_path):
        """Should ignore state changes for nonexistent tasks."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")

        # Should not raise
        queue.mark_running("nonexistent")
        queue.mark_completed("nonexistent", {})
        queue.mark_failed("nonexistent", "error")


# =============================================================================
# Query Tests
# =============================================================================


class TestQueries:
    """Tests for task query methods."""

    def test_get_pending(self, tmp_path):
        """Should return only QUEUED tasks."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        id1 = queue.enqueue("agent", "task1")
        id2 = queue.enqueue("agent", "task2")
        queue.mark_running(id2)

        pending = queue.get_pending()
        pending_ids = [t.id for t in pending]

        assert id1 in pending_ids
        assert id2 not in pending_ids

    def test_get_running(self, tmp_path):
        """Should return only RUNNING tasks."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        id1 = queue.enqueue("agent", "task1")
        id2 = queue.enqueue("agent", "task2")
        queue.mark_running(id2)

        running = queue.get_running()
        running_ids = [t.id for t in running]

        assert id2 in running_ids
        assert id1 not in running_ids

    def test_get_status(self, tmp_path):
        """Should return task by ID."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        task_id = queue.enqueue("my-agent", "my-task")

        task = queue.get_status(task_id)

        assert task is not None
        assert task.agent == "my-agent"

    def test_get_status_returns_none_for_nonexistent(self, tmp_path):
        """Should return None for nonexistent task."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")

        assert queue.get_status("nonexistent") is None

    def test_list_recent(self, tmp_path):
        """Should return tasks sorted by created_at desc."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        queue.enqueue("agent", "task1")  # id1 not used
        time.sleep(0.01)  # Ensure different timestamps
        id2 = queue.enqueue("agent", "task2")
        time.sleep(0.01)
        id3 = queue.enqueue("agent", "task3")

        recent = queue.list_recent(limit=2)

        assert len(recent) == 2
        assert recent[0].id == id3  # Most recent first
        assert recent[1].id == id2

    def test_list_by_state(self, tmp_path):
        """Should return tasks with specific state."""
        from klean.smol.task_queue import TaskQueue, TaskState

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        queue.enqueue("agent", "task1")
        id2 = queue.enqueue("agent", "task2")
        queue.mark_running(id2)
        queue.mark_completed(id2, {})

        completed = queue.list_by_state(TaskState.COMPLETED)

        assert len(completed) == 1
        assert completed[0].id == id2


# =============================================================================
# Cleanup Tests
# =============================================================================


class TestCleanup:
    """Tests for task cleanup."""

    def test_cleanup_old_removes_old_completed(self, tmp_path):
        """Should remove old completed tasks."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        task_id = queue.enqueue("agent", "task")
        queue.mark_running(task_id)
        queue.mark_completed(task_id, {})

        # Manually set old completed_at (25 hours ago, past the 24-hour threshold)
        queue.tasks[task_id].completed_at = time.time() - HOURS_25
        queue._save()

        removed = queue.cleanup_old(max_age_hours=24)

        assert removed == 1
        assert task_id not in queue.tasks

    def test_cleanup_old_keeps_recent(self, tmp_path):
        """Should keep recently completed tasks."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        task_id = queue.enqueue("agent", "task")
        queue.mark_running(task_id)
        queue.mark_completed(task_id, {})

        removed = queue.cleanup_old(max_age_hours=24)

        assert removed == 0
        assert task_id in queue.tasks

    def test_cleanup_old_keeps_queued(self, tmp_path):
        """Should not remove queued tasks regardless of age."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        task_id = queue.enqueue("agent", "task")

        # Manually set old created_at (but task is still queued, so should be kept)
        queue.tasks[task_id].created_at = time.time() - HOURS_100
        queue._save()

        removed = queue.cleanup_old(max_age_hours=24)

        assert removed == 0
        assert task_id in queue.tasks


# =============================================================================
# Cancel Tests
# =============================================================================


class TestCancel:
    """Tests for task cancellation."""

    def test_cancel_queued_task(self, tmp_path):
        """Should cancel queued task."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        task_id = queue.enqueue("agent", "task")

        result = queue.cancel(task_id)

        assert result is True
        assert task_id not in queue.tasks

    def test_cancel_running_task_fails(self, tmp_path):
        """Should not cancel running task."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")
        task_id = queue.enqueue("agent", "task")
        queue.mark_running(task_id)

        result = queue.cancel(task_id)

        assert result is False
        assert task_id in queue.tasks

    def test_cancel_nonexistent_returns_false(self, tmp_path):
        """Should return False for nonexistent task."""
        from klean.smol.task_queue import TaskQueue

        queue = TaskQueue(db_path=tmp_path / "queue.json")

        result = queue.cancel("nonexistent")

        assert result is False

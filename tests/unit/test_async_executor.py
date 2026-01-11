"""Tests for klean.smol.async_executor module.

Tests cover:
- AsyncExecutor initialization
- Task submission
- Status queries
- Worker management
- Task cancellation and cleanup
"""

import time
from unittest.mock import MagicMock, patch

# =============================================================================
# AsyncExecutor Initialization Tests
# =============================================================================


class TestAsyncExecutorInit:
    """Tests for AsyncExecutor initialization."""

    def test_sets_default_api_base(self, tmp_path):
        """Should set default api_base to localhost:4000."""
        from klean.smol.async_executor import AsyncExecutor

        with patch("klean.smol.async_executor.TaskQueue") as mock_queue:
            mock_queue.return_value = MagicMock()
            executor = AsyncExecutor()

            assert executor._api_base == "http://localhost:4000"

    def test_accepts_custom_api_base(self, tmp_path):
        """Should accept custom api_base."""
        from klean.smol.async_executor import AsyncExecutor

        with patch("klean.smol.async_executor.TaskQueue") as mock_queue:
            mock_queue.return_value = MagicMock()
            executor = AsyncExecutor(api_base="http://custom:5000")

            assert executor._api_base == "http://custom:5000"

    def test_accepts_custom_poll_interval(self):
        """Should accept custom poll_interval."""
        from klean.smol.async_executor import AsyncExecutor

        with patch("klean.smol.async_executor.TaskQueue") as mock_queue:
            mock_queue.return_value = MagicMock()
            executor = AsyncExecutor(poll_interval=5.0)

            assert executor.poll_interval == 5.0

    def test_creates_task_queue(self):
        """Should create TaskQueue instance."""
        from klean.smol.async_executor import AsyncExecutor

        with patch("klean.smol.async_executor.TaskQueue") as mock_queue:
            mock_queue.return_value = MagicMock()
            _executor = AsyncExecutor()  # noqa: F841

            mock_queue.assert_called_once()

    def test_starts_with_no_worker(self):
        """Should start without worker thread."""
        from klean.smol.async_executor import AsyncExecutor

        with patch("klean.smol.async_executor.TaskQueue") as mock_queue:
            mock_queue.return_value = MagicMock()
            executor = AsyncExecutor()

            assert executor._worker is None


# =============================================================================
# Executor Property Tests
# =============================================================================


class TestExecutorProperty:
    """Tests for lazy executor loading."""

    def test_lazy_loads_executor(self):
        """Should create SmolKLNExecutor on first access."""
        from klean.smol.async_executor import AsyncExecutor

        with patch("klean.smol.async_executor.TaskQueue") as mock_queue:
            mock_queue.return_value = MagicMock()

            async_exec = AsyncExecutor()

            # Before access, _executor is None
            assert async_exec._executor is None

            with patch("klean.smol.executor.SmolKLNExecutor") as mock_smol:
                mock_smol.return_value = MagicMock()
                _ = async_exec.executor

                # After access, SmolKLNExecutor was called
                mock_smol.assert_called_once()

    def test_reuses_existing_executor(self):
        """Should reuse executor on subsequent accesses."""
        from klean.smol.async_executor import AsyncExecutor

        with patch("klean.smol.async_executor.TaskQueue") as mock_queue:
            mock_queue.return_value = MagicMock()

            mock_smol_exec = MagicMock()
            async_exec = AsyncExecutor(executor=mock_smol_exec)

            # Should use provided executor
            assert async_exec.executor is mock_smol_exec


# =============================================================================
# Submit Tests
# =============================================================================


class TestSubmit:
    """Tests for task submission."""

    def test_returns_task_id(self):
        """Should return task ID from queue."""
        from klean.smol.async_executor import AsyncExecutor

        mock_queue = MagicMock()
        mock_queue.enqueue.return_value = "task123"

        with patch("klean.smol.async_executor.TaskQueue", return_value=mock_queue):
            async_exec = AsyncExecutor()
            task_id = async_exec.submit("agent", "do something")

            assert task_id == "task123"

    def test_enqueues_task(self):
        """Should enqueue task with parameters."""
        from klean.smol.async_executor import AsyncExecutor

        mock_queue = MagicMock()
        mock_queue.enqueue.return_value = "task123"

        with patch("klean.smol.async_executor.TaskQueue", return_value=mock_queue):
            async_exec = AsyncExecutor()
            async_exec.submit("my-agent", "my-task", model="gpt-4", project_path="/path")

            mock_queue.enqueue.assert_called_once_with("my-agent", "my-task", "gpt-4", "/path")

    def test_ensures_worker_started(self):
        """Should start worker after submit."""
        from klean.smol.async_executor import AsyncExecutor

        mock_queue = MagicMock()
        mock_queue.enqueue.return_value = "task123"
        mock_queue.get_pending.return_value = []  # No pending for worker

        with patch("klean.smol.async_executor.TaskQueue", return_value=mock_queue):
            async_exec = AsyncExecutor()
            async_exec.submit("agent", "task")

            # Worker should be started
            assert async_exec._worker is not None
            async_exec.stop(wait=True, timeout=1)


# =============================================================================
# Get Status Tests
# =============================================================================


class TestGetStatus:
    """Tests for status queries."""

    def test_returns_task_info(self):
        """Should return task info dict."""
        from klean.smol.async_executor import AsyncExecutor
        from klean.smol.task_queue import QueuedTask, TaskState

        mock_task = QueuedTask(
            id="abc123",
            agent="code-reviewer",
            task="Review code",
            model=None,
            state=TaskState.RUNNING,
            created_at=1000.0,
            started_at=1001.0,
        )
        mock_queue = MagicMock()
        mock_queue.get_status.return_value = mock_task

        with patch("klean.smol.async_executor.TaskQueue", return_value=mock_queue):
            async_exec = AsyncExecutor()
            status = async_exec.get_status("abc123")

            assert status["id"] == "abc123"
            assert status["state"] == "running"
            assert status["agent"] == "code-reviewer"

    def test_returns_error_for_nonexistent(self):
        """Should return error for nonexistent task."""
        from klean.smol.async_executor import AsyncExecutor

        mock_queue = MagicMock()
        mock_queue.get_status.return_value = None

        with patch("klean.smol.async_executor.TaskQueue", return_value=mock_queue):
            async_exec = AsyncExecutor()
            status = async_exec.get_status("nonexistent")

            assert "error" in status
            assert status["id"] == "nonexistent"


# =============================================================================
# List Tasks Tests
# =============================================================================


class TestListTasks:
    """Tests for listing tasks."""

    def test_returns_task_list(self):
        """Should return list of task dicts."""
        from klean.smol.async_executor import AsyncExecutor
        from klean.smol.task_queue import QueuedTask, TaskState

        mock_tasks = [
            QueuedTask(
                id="task1",
                agent="agent1",
                task="Short task",
                model=None,
                state=TaskState.QUEUED,
                created_at=1000.0,
            ),
            QueuedTask(
                id="task2",
                agent="agent2",
                task="Another task",
                model=None,
                state=TaskState.COMPLETED,
                created_at=1001.0,
            ),
        ]
        mock_queue = MagicMock()
        mock_queue.list_recent.return_value = mock_tasks

        with patch("klean.smol.async_executor.TaskQueue", return_value=mock_queue):
            async_exec = AsyncExecutor()
            tasks = async_exec.list_tasks(limit=10)

            assert len(tasks) == 2
            assert tasks[0]["id"] == "task1"
            assert tasks[1]["id"] == "task2"

    def test_truncates_long_task_text(self):
        """Should truncate long task descriptions."""
        from klean.smol.async_executor import AsyncExecutor
        from klean.smol.task_queue import QueuedTask, TaskState

        long_task = "x" * 200
        mock_task = QueuedTask(
            id="task1",
            agent="agent",
            task=long_task,
            model=None,
            state=TaskState.QUEUED,
            created_at=1000.0,
        )
        mock_queue = MagicMock()
        mock_queue.list_recent.return_value = [mock_task]

        with patch("klean.smol.async_executor.TaskQueue", return_value=mock_queue):
            async_exec = AsyncExecutor()
            tasks = async_exec.list_tasks()

            # Should be truncated to 100 chars + "..."
            assert len(tasks[0]["task"]) == 103


# =============================================================================
# Cancel Tests
# =============================================================================


class TestCancel:
    """Tests for task cancellation."""

    def test_delegates_to_queue(self):
        """Should delegate cancel to queue."""
        from klean.smol.async_executor import AsyncExecutor

        mock_queue = MagicMock()
        mock_queue.cancel.return_value = True

        with patch("klean.smol.async_executor.TaskQueue", return_value=mock_queue):
            async_exec = AsyncExecutor()
            result = async_exec.cancel("task123")

            mock_queue.cancel.assert_called_once_with("task123")
            assert result is True


# =============================================================================
# Worker State Tests
# =============================================================================


class TestWorkerState:
    """Tests for worker state queries."""

    def test_is_running_false_initially(self):
        """Should return False when no worker started."""
        from klean.smol.async_executor import AsyncExecutor

        with patch("klean.smol.async_executor.TaskQueue") as mock_queue:
            mock_queue.return_value = MagicMock()
            async_exec = AsyncExecutor()

            assert async_exec.is_running() is False

    def test_pending_count(self):
        """Should return count of pending tasks."""
        from klean.smol.async_executor import AsyncExecutor

        mock_queue = MagicMock()
        mock_queue.get_pending.return_value = [1, 2, 3]  # 3 pending

        with patch("klean.smol.async_executor.TaskQueue", return_value=mock_queue):
            async_exec = AsyncExecutor()

            assert async_exec.pending_count() == 3

    def test_running_count(self):
        """Should return count of running tasks."""
        from klean.smol.async_executor import AsyncExecutor

        mock_queue = MagicMock()
        mock_queue.get_running.return_value = [1, 2]  # 2 running

        with patch("klean.smol.async_executor.TaskQueue", return_value=mock_queue):
            async_exec = AsyncExecutor()

            assert async_exec.running_count() == 2


# =============================================================================
# Stop Tests
# =============================================================================


class TestStop:
    """Tests for stopping the executor."""

    def test_sets_stop_event(self):
        """Should set stop event."""
        from klean.smol.async_executor import AsyncExecutor

        mock_queue = MagicMock()
        mock_queue.get_pending.return_value = []

        with patch("klean.smol.async_executor.TaskQueue", return_value=mock_queue):
            async_exec = AsyncExecutor()

            # Manually start worker
            async_exec._ensure_worker()
            time.sleep(0.1)  # Let worker start

            async_exec.stop(wait=True, timeout=2)

            assert async_exec._stop.is_set()


# =============================================================================
# Cleanup Tests
# =============================================================================


class TestCleanup:
    """Tests for cleanup."""

    def test_delegates_to_queue(self):
        """Should delegate cleanup to queue."""
        from klean.smol.async_executor import AsyncExecutor

        mock_queue = MagicMock()
        mock_queue.cleanup_old.return_value = 5

        with patch("klean.smol.async_executor.TaskQueue", return_value=mock_queue):
            async_exec = AsyncExecutor()
            removed = async_exec.cleanup(max_age_hours=12)

            mock_queue.cleanup_old.assert_called_once_with(12)
            assert removed == 5


# =============================================================================
# Wait For Tests
# =============================================================================


class TestWaitFor:
    """Tests for wait_for method."""

    def test_returns_completed_immediately(self):
        """Should return immediately if task already completed."""
        from klean.smol.async_executor import AsyncExecutor
        from klean.smol.task_queue import QueuedTask, TaskState

        mock_task = QueuedTask(
            id="task1",
            agent="agent",
            task="task",
            model=None,
            state=TaskState.COMPLETED,
            created_at=1000.0,
            completed_at=1001.0,
            result={"output": "done"},
        )
        mock_queue = MagicMock()
        mock_queue.get_status.return_value = mock_task

        with patch("klean.smol.async_executor.TaskQueue", return_value=mock_queue):
            async_exec = AsyncExecutor()
            start = time.time()
            status = async_exec.wait_for("task1", timeout=10)
            elapsed = time.time() - start

            assert status["state"] == "completed"
            assert elapsed < 2  # Should not wait

    def test_returns_timeout_on_slow_task(self):
        """Should return timeout error if task doesn't complete."""
        from klean.smol.async_executor import AsyncExecutor
        from klean.smol.task_queue import QueuedTask, TaskState

        mock_task = QueuedTask(
            id="task1",
            agent="agent",
            task="task",
            model=None,
            state=TaskState.RUNNING,
            created_at=1000.0,
        )
        mock_queue = MagicMock()
        mock_queue.get_status.return_value = mock_task

        with patch("klean.smol.async_executor.TaskQueue", return_value=mock_queue):
            async_exec = AsyncExecutor()
            status = async_exec.wait_for("task1", timeout=1)

            assert "error" in status
            assert "Timeout" in status["error"]
            assert status["state"] == "timeout"

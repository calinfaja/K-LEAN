"""Background async executor for SmolKLN agents.

Provides a worker thread that processes queued tasks in the background.
"""

import threading
import time
from pathlib import Path
from typing import Any, Optional

from .task_queue import TaskQueue


class AsyncExecutor:
    """Background executor for async task processing.

    Runs a worker thread that monitors the task queue and executes
    tasks as they are submitted.
    """

    def __init__(
        self, executor=None, poll_interval: float = 2.0, api_base: str = "http://localhost:4000"
    ):
        """Initialize async executor.

        Args:
            executor: SmolKLNExecutor instance (created if not provided)
            poll_interval: Seconds between queue checks
            api_base: LiteLLM proxy URL (used if executor not provided)
        """
        self._executor = executor
        self._api_base = api_base
        self.queue = TaskQueue()
        self.poll_interval = poll_interval
        self._worker: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

    @property
    def executor(self):
        """Lazy-load executor."""
        if self._executor is None:
            from .executor import SmolKLNExecutor

            self._executor = SmolKLNExecutor(api_base=self._api_base)
        return self._executor

    def submit(self, agent: str, task: str, model: str = None, project_path: str = None) -> str:
        """Submit a task for async execution.

        Args:
            agent: Agent name
            task: Task description
            model: Optional model override
            project_path: Optional project path

        Returns:
            Task ID for status checking
        """
        task_id = self.queue.enqueue(agent, task, model, project_path)
        self._ensure_worker()
        return task_id

    def get_status(self, task_id: str) -> dict[str, Any]:
        """Get status of a task.

        Args:
            task_id: Task ID from submit()

        Returns:
            Dict with id, state, result/error
        """
        task = self.queue.get_status(task_id)
        if not task:
            return {"error": "Task not found", "id": task_id}

        return {
            "id": task.id,
            "state": task.state.value,
            "agent": task.agent,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "result": task.result,
            "error": task.error,
        }

    def wait_for(self, task_id: str, timeout: float = 300) -> dict[str, Any]:
        """Wait for task to complete.

        Args:
            task_id: Task ID
            timeout: Maximum wait time in seconds

        Returns:
            Task status dict
        """
        start = time.time()
        while time.time() - start < timeout:
            status = self.get_status(task_id)
            if status.get("state") in ("completed", "failed"):
                return status
            time.sleep(1)

        return {"error": "Timeout waiting for task", "id": task_id, "state": "timeout"}

    def list_tasks(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent tasks.

        Args:
            limit: Maximum number to return

        Returns:
            List of task info dicts
        """
        return [
            {
                "id": t.id,
                "state": t.state.value,
                "agent": t.agent,
                "created_at": t.created_at,
                "task": t.task[:100] + "..." if len(t.task) > 100 else t.task,
            }
            for t in self.queue.list_recent(limit)
        ]

    def cancel(self, task_id: str) -> bool:
        """Cancel a queued task.

        Args:
            task_id: Task ID

        Returns:
            True if cancelled
        """
        return self.queue.cancel(task_id)

    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._worker is not None and self._worker.is_alive()

    def pending_count(self) -> int:
        """Get number of pending tasks."""
        return len(self.queue.get_pending())

    def running_count(self) -> int:
        """Get number of running tasks."""
        return len(self.queue.get_running())

    def _ensure_worker(self):
        """Start worker if not already running."""
        with self._lock:
            if self._worker is None or not self._worker.is_alive():
                self._stop.clear()
                self._worker = threading.Thread(
                    target=self._worker_loop, daemon=True, name="SmolKLN-AsyncWorker"
                )
                self._worker.start()

    def _worker_loop(self):
        """Main worker loop - processes tasks from queue."""
        while not self._stop.is_set():
            # Check for pending tasks
            pending = self.queue.get_pending()

            if not pending:
                # No work, sleep and retry
                self._stop.wait(self.poll_interval)
                continue

            # Process first pending task
            task = pending[0]
            self.queue.mark_running(task.id)

            try:
                # Create executor with project path if specified
                if task.project_path:
                    from .executor import SmolKLNExecutor

                    executor = SmolKLNExecutor(
                        api_base=self._api_base, project_path=Path(task.project_path)
                    )
                else:
                    executor = self.executor

                result = executor.execute(task.agent, task.task, model_override=task.model)
                self.queue.mark_completed(task.id, result)

            except Exception as e:
                self.queue.mark_failed(task.id, str(e))

        # Worker stopping
        pass

    def stop(self, wait: bool = True, timeout: float = 10):
        """Stop the worker thread.

        Args:
            wait: Whether to wait for worker to stop
            timeout: Max time to wait
        """
        self._stop.set()
        if wait and self._worker and self._worker.is_alive():
            self._worker.join(timeout)

    def cleanup(self, max_age_hours: int = 24) -> int:
        """Clean up old completed/failed tasks.

        Args:
            max_age_hours: Age threshold

        Returns:
            Number of tasks removed
        """
        return self.queue.cleanup_old(max_age_hours)


# Global async executor instance
_async_executor: Optional[AsyncExecutor] = None


def get_async_executor(api_base: str = "http://localhost:4000") -> AsyncExecutor:
    """Get or create global async executor.

    Args:
        api_base: LiteLLM proxy URL

    Returns:
        AsyncExecutor instance
    """
    global _async_executor
    if _async_executor is None:
        _async_executor = AsyncExecutor(api_base=api_base)
    return _async_executor


def submit_async(agent: str, task: str, model: str = None, project_path: str = None) -> str:
    """Quick helper to submit async task.

    Args:
        agent: Agent name
        task: Task description
        model: Optional model override
        project_path: Optional project path

    Returns:
        Task ID
    """
    executor = get_async_executor()
    return executor.submit(agent, task, model, project_path)


def get_task_status(task_id: str) -> dict[str, Any]:
    """Quick helper to get task status.

    Args:
        task_id: Task ID

    Returns:
        Status dict
    """
    executor = get_async_executor()
    return executor.get_status(task_id)

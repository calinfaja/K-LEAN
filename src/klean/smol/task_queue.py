"""Persistent task queue for async agent execution.

Provides file-based persistence for background task management.
"""

import json
import time
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class TaskState(Enum):
    """State of a queued task."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QueuedTask:
    """A task in the queue."""

    id: str
    agent: str
    task: str
    model: Optional[str]
    state: TaskState
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    project_path: Optional[str] = None


class TaskQueue:
    """Persistent task queue with file-based storage.

    Tasks are stored in a JSON file and survive restarts.
    """

    def __init__(self, db_path: Path = None):
        """Initialize task queue.

        Args:
            db_path: Path to queue database file
                     Default: ~/.klean/task_queue.json
        """
        self.db_path = db_path or (Path.home() / ".klean" / "task_queue.json")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.tasks: dict[str, QueuedTask] = {}
        self._load()

    def _load(self):
        """Load tasks from disk."""
        if self.db_path.exists():
            try:
                data = json.loads(self.db_path.read_text())
                self.tasks = {t["id"]: self._from_dict(t) for t in data}
            except (json.JSONDecodeError, KeyError):
                self.tasks = {}
        else:
            self.tasks = {}

    def _save(self):
        """Save tasks to disk."""
        data = [self._to_dict(t) for t in self.tasks.values()]
        self.db_path.write_text(json.dumps(data, indent=2))

    def _to_dict(self, task: QueuedTask) -> dict:
        """Convert task to dict for JSON serialization."""
        d = asdict(task)
        d["state"] = task.state.value
        return d

    def _from_dict(self, d: dict) -> QueuedTask:
        """Convert dict to QueuedTask."""
        d["state"] = TaskState(d["state"])
        return QueuedTask(**d)

    def enqueue(self, agent: str, task: str, model: str = None, project_path: str = None) -> str:
        """Add task to queue.

        Args:
            agent: Agent name to execute
            task: Task description
            model: Optional model override
            project_path: Optional project path

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())[:8]
        self.tasks[task_id] = QueuedTask(
            id=task_id,
            agent=agent,
            task=task,
            model=model,
            state=TaskState.QUEUED,
            created_at=time.time(),
            project_path=project_path,
        )
        self._save()
        return task_id

    def get_pending(self) -> list[QueuedTask]:
        """Get all pending (queued) tasks."""
        return [t for t in self.tasks.values() if t.state == TaskState.QUEUED]

    def get_running(self) -> list[QueuedTask]:
        """Get all currently running tasks."""
        return [t for t in self.tasks.values() if t.state == TaskState.RUNNING]

    def mark_running(self, task_id: str):
        """Mark task as running."""
        if task_id in self.tasks:
            self.tasks[task_id].state = TaskState.RUNNING
            self.tasks[task_id].started_at = time.time()
            self._save()

    def mark_completed(self, task_id: str, result: dict):
        """Mark task as completed with result."""
        if task_id in self.tasks:
            self.tasks[task_id].state = TaskState.COMPLETED
            self.tasks[task_id].completed_at = time.time()
            self.tasks[task_id].result = result
            self._save()

    def mark_failed(self, task_id: str, error: str):
        """Mark task as failed with error."""
        if task_id in self.tasks:
            self.tasks[task_id].state = TaskState.FAILED
            self.tasks[task_id].completed_at = time.time()
            self.tasks[task_id].error = error
            self._save()

    def get_status(self, task_id: str) -> Optional[QueuedTask]:
        """Get task by ID."""
        return self.tasks.get(task_id)

    def list_recent(self, limit: int = 10) -> list[QueuedTask]:
        """List most recent tasks."""
        sorted_tasks = sorted(self.tasks.values(), key=lambda t: t.created_at, reverse=True)
        return sorted_tasks[:limit]

    def list_by_state(self, state: TaskState) -> list[QueuedTask]:
        """List tasks with specific state."""
        return [t for t in self.tasks.values() if t.state == state]

    def cleanup_old(self, max_age_hours: int = 24):
        """Remove completed/failed tasks older than max_age.

        Args:
            max_age_hours: Maximum age in hours
        """
        cutoff = time.time() - (max_age_hours * 3600)
        to_remove = []

        for task_id, task in self.tasks.items():
            if task.state in (TaskState.COMPLETED, TaskState.FAILED):
                if task.completed_at and task.completed_at < cutoff:
                    to_remove.append(task_id)

        for task_id in to_remove:
            del self.tasks[task_id]

        if to_remove:
            self._save()

        return len(to_remove)

    def cancel(self, task_id: str) -> bool:
        """Cancel a queued task.

        Only works for QUEUED tasks, not running ones.

        Returns:
            True if cancelled, False if not found or not cancellable
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.state == TaskState.QUEUED:
                del self.tasks[task_id]
                self._save()
                return True
        return False

"""JSON file-based state persistence for tasks and projects."""

from datetime import datetime
from pathlib import Path

from ai_company.state.models import (
    HumanReview,
    Project,
    ReviewDecision,
    Task,
    TaskStatus,
)

# Valid state transitions: from_status -> set of allowed to_statuses
VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.IN_PROGRESS},
    TaskStatus.IN_PROGRESS: {TaskStatus.REVIEW},
    TaskStatus.REVIEW: {TaskStatus.COMPLETED, TaskStatus.REJECTED},
    TaskStatus.REJECTED: {TaskStatus.IN_PROGRESS},
    TaskStatus.APPROVED: {TaskStatus.COMPLETED},
    TaskStatus.COMPLETED: set(),
}


class InvalidTransition(Exception):
    pass


class StateStore:
    """Persist tasks and projects as JSON files."""

    def __init__(self, data_dir: Path) -> None:
        self.tasks_dir = data_dir / "state" / "tasks"
        self.projects_dir = data_dir / "state" / "projects"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    # --- Tasks ---

    def save_task(self, task: Task) -> None:
        path = self.tasks_dir / f"{task.id}.json"
        path.write_text(task.model_dump_json(indent=2))

    def transition_task(
        self,
        task_id: str,
        to_status: TaskStatus,
        *,
        feedback: str = "",
    ) -> Task:
        """Transition a task to a new status with validation.

        Returns the updated task, or raises InvalidTransition / KeyError.
        """
        task = self.load_task(task_id)
        if task is None:
            raise KeyError(f"Task '{task_id}' not found")

        allowed = VALID_TRANSITIONS.get(task.status, set())
        if to_status not in allowed:
            raise InvalidTransition(
                f"Cannot transition {task_id} from {task.status.value} to {to_status.value}. "
                f"Allowed: {', '.join(s.value for s in allowed) or 'none'}"
            )

        # Record human review decisions
        if task.status == TaskStatus.REVIEW:
            decision = (
                ReviewDecision.APPROVED
                if to_status == TaskStatus.COMPLETED
                else ReviewDecision.REJECTED
            )
            task.reviews.append(
                HumanReview(
                    decision=decision,
                    feedback=feedback,
                    iteration=task.iteration,
                )
            )

        # Bump iteration on re-run after rejection
        if task.status == TaskStatus.REJECTED and to_status == TaskStatus.IN_PROGRESS:
            task.iteration += 1

        task.status = to_status
        task.updated_at = datetime.now()
        self.save_task(task)
        return task

    def load_task(self, task_id: str) -> Task | None:
        path = self.tasks_dir / f"{task_id}.json"
        if not path.exists():
            return None
        return Task.model_validate_json(path.read_text())

    def list_tasks(
        self,
        *,
        status: TaskStatus | None = None,
        project_id: str | None = None,
    ) -> list[Task]:
        tasks = []
        for path in sorted(self.tasks_dir.glob("*.json")):
            task = Task.model_validate_json(path.read_text())
            if status and task.status != status:
                continue
            if project_id and task.project_id != project_id:
                continue
            tasks.append(task)
        return tasks

    def next_task_id(self) -> str:
        existing = list(self.tasks_dir.glob("task-*.json"))
        if not existing:
            return "task-001"
        nums = []
        for p in existing:
            try:
                nums.append(int(p.stem.split("-", 1)[1]))
            except (ValueError, IndexError):
                continue
        next_num = max(nums, default=0) + 1
        return f"task-{next_num:03d}"

    # --- Projects ---

    def save_project(self, project: Project) -> None:
        path = self.projects_dir / f"{project.id}.json"
        path.write_text(project.model_dump_json(indent=2))

    def load_project(self, project_id: str) -> Project | None:
        path = self.projects_dir / f"{project_id}.json"
        if not path.exists():
            return None
        return Project.model_validate_json(path.read_text())

    def list_projects(self) -> list[Project]:
        projects = []
        for path in sorted(self.projects_dir.glob("*.json")):
            projects.append(Project.model_validate_json(path.read_text()))
        return projects

    def next_project_id(self) -> str:
        existing = list(self.projects_dir.glob("proj-*.json"))
        if not existing:
            return "proj-001"
        nums = []
        for p in existing:
            try:
                nums.append(int(p.stem.split("-", 1)[1]))
            except (ValueError, IndexError):
                continue
        next_num = max(nums, default=0) + 1
        return f"proj-{next_num:03d}"

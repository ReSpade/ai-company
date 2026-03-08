"""JSON file-based state persistence for tasks and projects."""

import json
from pathlib import Path

from ai_company.state.models import Project, Task, TaskStatus


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

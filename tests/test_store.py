"""Tests for the StateStore."""

from ai_company.state.models import (
    AgentResult,
    AgentRole,
    Project,
    Task,
    TaskStatus,
    TaskType,
)
from ai_company.state.store import StateStore


def test_save_and_load_task(tmp_path):
    store = StateStore(tmp_path)
    task = Task(
        id="task-001",
        title="Test task",
        description="A test task",
        type=TaskType.FEATURE,
    )
    store.save_task(task)
    loaded = store.load_task("task-001")
    assert loaded is not None
    assert loaded.id == "task-001"
    assert loaded.title == "Test task"
    assert loaded.status == TaskStatus.PENDING


def test_load_nonexistent_task(tmp_path):
    store = StateStore(tmp_path)
    assert store.load_task("no-such-task") is None


def test_list_tasks(tmp_path):
    store = StateStore(tmp_path)
    for i in range(3):
        store.save_task(
            Task(
                id=f"task-{i:03d}",
                title=f"Task {i}",
                description=f"Desc {i}",
                type=TaskType.FEATURE,
                status=TaskStatus.COMPLETED if i == 0 else TaskStatus.PENDING,
            )
        )
    all_tasks = store.list_tasks()
    assert len(all_tasks) == 3

    completed = store.list_tasks(status=TaskStatus.COMPLETED)
    assert len(completed) == 1
    assert completed[0].id == "task-000"


def test_list_tasks_by_project(tmp_path):
    store = StateStore(tmp_path)
    store.save_task(
        Task(id="task-001", title="T1", description="D1", type=TaskType.FEATURE, project_id="proj-001")
    )
    store.save_task(
        Task(id="task-002", title="T2", description="D2", type=TaskType.BUG_FIX, project_id="proj-002")
    )
    result = store.list_tasks(project_id="proj-001")
    assert len(result) == 1
    assert result[0].id == "task-001"


def test_next_task_id(tmp_path):
    store = StateStore(tmp_path)
    assert store.next_task_id() == "task-001"

    store.save_task(
        Task(id="task-001", title="T", description="D", type=TaskType.FEATURE)
    )
    assert store.next_task_id() == "task-002"

    store.save_task(
        Task(id="task-010", title="T", description="D", type=TaskType.FEATURE)
    )
    assert store.next_task_id() == "task-011"


def test_task_with_results_roundtrip(tmp_path):
    store = StateStore(tmp_path)
    task = Task(
        id="task-001",
        title="With results",
        description="Test",
        type=TaskType.FEATURE,
        results=[
            AgentResult(
                agent=AgentRole.ENGINEER,
                summary="Did stuff",
                artifacts=["src/foo.py"],
            )
        ],
    )
    store.save_task(task)
    loaded = store.load_task("task-001")
    assert len(loaded.results) == 1
    assert loaded.results[0].agent == AgentRole.ENGINEER
    assert loaded.results[0].artifacts == ["src/foo.py"]


def test_save_and_load_project(tmp_path):
    store = StateStore(tmp_path)
    project = Project(
        id="proj-001",
        name="my-saas",
        description="A SaaS product",
    )
    store.save_project(project)
    loaded = store.load_project("proj-001")
    assert loaded is not None
    assert loaded.name == "my-saas"


def test_list_projects(tmp_path):
    store = StateStore(tmp_path)
    for i in range(2):
        store.save_project(
            Project(id=f"proj-{i:03d}", name=f"proj-{i}", description=f"Desc {i}")
        )
    assert len(store.list_projects()) == 2


def test_next_project_id(tmp_path):
    store = StateStore(tmp_path)
    assert store.next_project_id() == "proj-001"

    store.save_project(
        Project(id="proj-001", name="p", description="d")
    )
    assert store.next_project_id() == "proj-002"


def test_directories_created(tmp_path):
    store = StateStore(tmp_path)
    assert store.tasks_dir.exists()
    assert store.projects_dir.exists()

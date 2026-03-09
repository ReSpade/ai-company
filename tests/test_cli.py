"""Tests for CLI commands (smoke tests using CliRunner)."""

import json

from typer.testing import CliRunner

from ai_company.main import app
from ai_company.state.models import Project, ReviewDecision, Task, TaskStatus, TaskType
from ai_company.state.store import StateStore

runner = CliRunner()


def test_status_command():
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "AI Company System Status" in result.output


def test_tasks_list_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_COMPANY_DATA_DIR", str(tmp_path))
    result = runner.invoke(app, ["tasks", "list"])
    assert result.exit_code == 0
    assert "No tasks found" in result.output


def test_tasks_list_with_data(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_COMPANY_DATA_DIR", str(tmp_path))
    store = StateStore(tmp_path)
    store.save_task(
        Task(
            id="task-001",
            title="Test task",
            description="Desc",
            type=TaskType.FEATURE,
            status=TaskStatus.REVIEW,
        )
    )
    result = runner.invoke(app, ["tasks", "list"])
    assert result.exit_code == 0
    assert "task-001" in result.output


def test_tasks_show(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_COMPANY_DATA_DIR", str(tmp_path))
    store = StateStore(tmp_path)
    store.save_task(
        Task(
            id="task-001",
            title="Show me",
            description="Details here",
            type=TaskType.RESEARCH,
        )
    )
    result = runner.invoke(app, ["tasks", "show", "task-001"])
    assert result.exit_code == 0
    assert "Show me" in result.output
    assert "research" in result.output


def test_tasks_show_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_COMPANY_DATA_DIR", str(tmp_path))
    result = runner.invoke(app, ["tasks", "show", "nope"])
    assert result.exit_code == 1


def test_init_project(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_COMPANY_PROJECTS_DIR", str(tmp_path / "projects"))
    monkeypatch.setenv("AI_COMPANY_DATA_DIR", str(tmp_path / "data"))
    result = runner.invoke(app, ["init-project", "my-test", "-d", "A test project"])
    assert result.exit_code == 0
    assert "my-test" in result.output
    assert (tmp_path / "projects" / "my-test" / "src").exists()

    # Check project was registered in store
    store = StateStore(tmp_path / "data")
    projects = store.list_projects()
    assert len(projects) == 1
    assert projects[0].name == "my-test"


def test_init_project_duplicate(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_COMPANY_PROJECTS_DIR", str(tmp_path / "projects"))
    monkeypatch.setenv("AI_COMPANY_DATA_DIR", str(tmp_path / "data"))
    runner.invoke(app, ["init-project", "dup"])
    result = runner.invoke(app, ["init-project", "dup"])
    assert result.exit_code == 1


# ── approve / reject / resume CLI tests ──────────────────────────────────


def test_tasks_approve(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_COMPANY_DATA_DIR", str(tmp_path))
    store = StateStore(tmp_path)
    store.save_task(
        Task(id="task-001", title="T", description="D", type=TaskType.FEATURE, status=TaskStatus.REVIEW)
    )
    result = runner.invoke(app, ["tasks", "approve", "task-001"])
    assert result.exit_code == 0
    assert "approved" in result.output

    # Verify state persisted
    task = store.load_task("task-001")
    assert task.status == TaskStatus.COMPLETED
    assert len(task.reviews) == 1


def test_tasks_approve_with_feedback(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_COMPANY_DATA_DIR", str(tmp_path))
    store = StateStore(tmp_path)
    store.save_task(
        Task(id="task-001", title="T", description="D", type=TaskType.FEATURE, status=TaskStatus.REVIEW)
    )
    result = runner.invoke(app, ["tasks", "approve", "task-001", "-f", "Ship it!"])
    assert result.exit_code == 0
    task = store.load_task("task-001")
    assert task.reviews[0].feedback == "Ship it!"


def test_tasks_approve_wrong_status(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_COMPANY_DATA_DIR", str(tmp_path))
    store = StateStore(tmp_path)
    store.save_task(
        Task(id="task-001", title="T", description="D", type=TaskType.FEATURE, status=TaskStatus.PENDING)
    )
    result = runner.invoke(app, ["tasks", "approve", "task-001"])
    assert result.exit_code == 1
    assert "Cannot transition" in result.output


def test_tasks_approve_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_COMPANY_DATA_DIR", str(tmp_path))
    result = runner.invoke(app, ["tasks", "approve", "no-such-task"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_tasks_reject(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_COMPANY_DATA_DIR", str(tmp_path))
    store = StateStore(tmp_path)
    store.save_task(
        Task(id="task-001", title="T", description="D", type=TaskType.FEATURE, status=TaskStatus.REVIEW)
    )
    result = runner.invoke(app, ["tasks", "reject", "task-001", "-r", "Use OAuth"])
    assert result.exit_code == 0
    assert "rejected" in result.output
    assert "Use OAuth" in result.output

    task = store.load_task("task-001")
    assert task.status == TaskStatus.REJECTED
    assert task.reviews[0].feedback == "Use OAuth"


def test_tasks_reject_missing_reason(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_COMPANY_DATA_DIR", str(tmp_path))
    store = StateStore(tmp_path)
    store.save_task(
        Task(id="task-001", title="T", description="D", type=TaskType.FEATURE, status=TaskStatus.REVIEW)
    )
    # --reason is required
    result = runner.invoke(app, ["tasks", "reject", "task-001"])
    assert result.exit_code != 0


def test_tasks_show_with_reviews(tmp_path, monkeypatch):
    """tasks show displays review history."""
    monkeypatch.setenv("AI_COMPANY_DATA_DIR", str(tmp_path))
    store = StateStore(tmp_path)
    store.save_task(
        Task(id="task-001", title="T", description="D", type=TaskType.FEATURE, status=TaskStatus.REVIEW)
    )
    store.transition_task("task-001", TaskStatus.REJECTED, feedback="Fix tests")
    result = runner.invoke(app, ["tasks", "show", "task-001"])
    assert result.exit_code == 0
    assert "Review History" in result.output
    assert "Fix tests" in result.output

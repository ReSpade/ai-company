"""Tests for CLI commands (smoke tests using CliRunner)."""

import json

from typer.testing import CliRunner

from ai_company.main import app
from ai_company.state.models import Project, Task, TaskStatus, TaskType
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

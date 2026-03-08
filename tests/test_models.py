"""Tests for data models."""

from ai_company.state.models import (
    AgentResult,
    AgentRole,
    Project,
    Task,
    TaskStatus,
    TaskType,
)


def test_task_creation():
    task = Task(
        id="task-001",
        title="Build authentication",
        description="Implement user login/signup",
        type=TaskType.FEATURE,
    )
    assert task.status == TaskStatus.PENDING
    assert task.assigned_to is None
    assert task.results == []
    assert task.subtask_ids == []
    assert task.project_id is None
    assert task.cost_usd is None
    assert task.duration_ms is None
    assert task.session_id is None


def test_task_with_result():
    result = AgentResult(
        agent=AgentRole.ENGINEER,
        summary="Implemented login endpoint",
        details="Created /api/login with JWT tokens",
        artifacts=["src/auth.py", "tests/test_auth.py"],
    )
    task = Task(
        id="task-002",
        title="Login endpoint",
        description="Create login API",
        type=TaskType.FEATURE,
        status=TaskStatus.COMPLETED,
        assigned_to=AgentRole.ENGINEER,
        results=[result],
    )
    assert len(task.results) == 1
    assert task.results[0].agent == AgentRole.ENGINEER


def test_project_creation():
    project = Project(
        id="proj-001",
        name="my-saas",
        description="A SaaS product",
    )
    assert project.path is None
    assert project.tasks == []


def test_agent_roles():
    assert AgentRole.ORCHESTRATOR == "orchestrator"
    assert AgentRole.RESEARCHER == "researcher"
    assert AgentRole.PLANNER == "planner"
    assert AgentRole.ENGINEER == "engineer"
    assert AgentRole.REVIEWER == "reviewer"

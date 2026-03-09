"""Tests for data models."""

from ai_company.state.models import (
    AgentResult,
    AgentRole,
    HumanReview,
    Project,
    ReviewDecision,
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


def test_task_with_reviews():
    task = Task(
        id="task-003",
        title="Reviewed task",
        description="Task with review history",
        type=TaskType.FEATURE,
        iteration=2,
        reviews=[
            HumanReview(
                decision=ReviewDecision.REJECTED,
                feedback="Needs OAuth instead of basic auth",
                iteration=1,
            ),
            HumanReview(
                decision=ReviewDecision.APPROVED,
                feedback="Looks good now",
                iteration=2,
            ),
        ],
    )
    assert len(task.reviews) == 2
    assert task.reviews[0].decision == ReviewDecision.REJECTED
    assert task.reviews[1].decision == ReviewDecision.APPROVED
    assert task.iteration == 2


def test_task_default_iteration():
    task = Task(
        id="task-004",
        title="New task",
        description="Fresh task",
        type=TaskType.FEATURE,
    )
    assert task.iteration == 1
    assert task.reviews == []


def test_agent_result_with_iteration():
    result = AgentResult(
        agent=AgentRole.ENGINEER,
        summary="Iteration 2 fix",
        iteration=2,
    )
    assert result.iteration == 2

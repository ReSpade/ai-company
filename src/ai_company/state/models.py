"""Data models for tasks, projects, and agent results."""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class TaskType(str, Enum):
    NEW_PROJECT = "new_project"
    BUG_FIX = "bug_fix"
    FEATURE = "feature"
    RESEARCH = "research"
    BUSINESS_VALIDATION = "business_validation"


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    RESEARCHER = "researcher"
    PLANNER = "planner"
    ENGINEER = "engineer"
    REVIEWER = "reviewer"


class AgentResult(BaseModel):
    """Output from an agent's work."""

    agent: AgentRole
    summary: str
    details: str = ""
    artifacts: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class Task(BaseModel):
    """A unit of work to be processed by agents."""

    id: str
    title: str
    description: str
    type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: AgentRole | None = None
    results: list[AgentResult] = Field(default_factory=list)
    parent_id: str | None = None
    subtask_ids: list[str] = Field(default_factory=list)
    project_id: str | None = None
    cost_usd: float | None = None
    duration_ms: int | None = None
    session_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Project(BaseModel):
    """A project being developed."""

    id: str
    name: str
    description: str
    path: Path | None = None
    tasks: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)

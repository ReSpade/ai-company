"""Tests for the orchestrator agent configuration."""

from ai_company.agents.orchestrator import create_orchestrator_options
from ai_company.config.settings import Settings


def test_create_orchestrator_options():
    settings = Settings()
    options = create_orchestrator_options(
        task="test task",
        settings=settings,
    )
    assert options.max_turns == settings.max_turns
    assert "Agent" in options.allowed_tools
    assert options.agents is not None


def test_orchestrator_has_all_subagents():
    options = create_orchestrator_options(task="test")
    expected_agents = {"researcher", "planner", "engineer", "reviewer"}
    assert set(options.agents.keys()) == expected_agents


def test_orchestrator_agent_tools():
    options = create_orchestrator_options(task="test")

    # Engineer should have write/edit/bash access
    engineer = options.agents["engineer"]
    assert "Bash" in engineer.tools
    assert "Edit" in engineer.tools
    assert "Write" in engineer.tools

    # Reviewer should be read-only
    reviewer = options.agents["reviewer"]
    assert "Read" in reviewer.tools
    assert "Write" not in reviewer.tools
    assert "Edit" not in reviewer.tools
    assert "Bash" not in reviewer.tools


def test_orchestrator_system_prompt_loaded():
    options = create_orchestrator_options(task="test")
    assert "Orchestrator" in options.system_prompt
    assert len(options.system_prompt) > 100

"""Orchestrator agent - the main entry point that routes tasks to specialized agents."""

from pathlib import Path

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions

from ai_company.config.settings import Settings

PROMPTS_DIR = Path(__file__).parent.parent / "config" / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


def create_orchestrator_options(
    task: str,
    *,
    settings: Settings | None = None,
    project_dir: str | None = None,
) -> ClaudeAgentOptions:
    """Create ClaudeAgentOptions with orchestrator as the main agent and subagents defined."""
    if settings is None:
        settings = Settings()

    cwd = project_dir or str(settings.projects_dir.resolve())

    agents = {
        "researcher": AgentDefinition(
            description=(
                "Research specialist. Use for market research, competitor analysis, "
                "technology evaluation, and business validation tasks."
            ),
            prompt=_load_prompt("researcher"),
            tools=["WebSearch", "WebFetch", "Read", "Write", "Glob", "Grep"],
            model=settings.default_model,
        ),
        "planner": AgentDefinition(
            description=(
                "Technical planner. Use for requirements definition, architecture design, "
                "technical specifications, and task breakdown."
            ),
            prompt=_load_prompt("planner"),
            tools=["Read", "Write", "Glob", "Grep"],
            model=settings.default_model,
        ),
        "engineer": AgentDefinition(
            description=(
                "Software engineer. Use for code implementation, bug fixes, writing tests, "
                "and running tests. Handles both coding and testing."
            ),
            prompt=_load_prompt("engineer"),
            tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            model=settings.default_model,
        ),
        "reviewer": AgentDefinition(
            description=(
                "Code reviewer. Use for independent code review, security audit, "
                "and quality assessment. Use AFTER engineer has completed work."
            ),
            prompt=_load_prompt("reviewer"),
            tools=["Read", "Glob", "Grep"],
            model=settings.reviewer_model,
        ),
    }

    return ClaudeAgentOptions(
        system_prompt=_load_prompt("orchestrator"),
        allowed_tools=["Read", "Write", "Glob", "Grep", "Agent"],
        agents=agents,
        max_turns=settings.max_turns,
        cwd=cwd,
    )

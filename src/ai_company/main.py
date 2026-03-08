"""CLI entrypoint for the AI Company multi-agent system."""

import asyncio
import logging
from datetime import datetime

import typer
from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, query
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ai_company.agents.orchestrator import create_orchestrator_options
from ai_company.config.settings import Settings
from ai_company.logging import setup_logging
from ai_company.state.models import (
    AgentResult,
    AgentRole,
    Project,
    Task,
    TaskStatus,
    TaskType,
)
from ai_company.state.store import StateStore

app = typer.Typer(
    name="ai-company",
    help="Multi-agent autonomous system for a one-person AI company.",
)
tasks_app = typer.Typer(help="Manage tasks.")
app.add_typer(tasks_app, name="tasks")

console = Console()
log = logging.getLogger("ai_company.cli")


def _get_store(settings: Settings | None = None) -> StateStore:
    if settings is None:
        settings = Settings()
    return StateStore(settings.data_dir)


# ── run ──────────────────────────────────────────────────────────────────


async def _run_task(
    task_description: str,
    project_dir: str | None,
    task_type: TaskType,
    project_id: str | None,
) -> None:
    settings = Settings()
    setup_logging(settings.log_level, settings.data_dir / "logs")
    store = _get_store(settings)

    # Create and persist task
    task = Task(
        id=store.next_task_id(),
        title=task_description[:80],
        description=task_description,
        type=task_type,
        status=TaskStatus.IN_PROGRESS,
        project_id=project_id,
    )
    store.save_task(task)

    console.print(Panel(task_description, title=f"Task {task.id}", border_style="blue"))
    console.print()

    options = create_orchestrator_options(
        task=task_description,
        settings=settings,
        project_dir=project_dir,
    )

    collected_text: list[str] = []
    result_msg: ResultMessage | None = None

    async for message in query(prompt=task_description, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    console.print(block.text)
                    collected_text.append(block.text)
        elif isinstance(message, ResultMessage):
            result_msg = message

    # Save result
    agent_result = AgentResult(
        agent=AgentRole.ORCHESTRATOR,
        summary=task_description[:200],
        details="\n".join(collected_text),
    )
    task.results.append(agent_result)
    task.status = TaskStatus.REVIEW
    task.updated_at = datetime.now()

    if result_msg:
        task.cost_usd = result_msg.total_cost_usd
        task.duration_ms = result_msg.duration_ms
        task.session_id = result_msg.session_id

    store.save_task(task)

    console.print()
    console.print(
        Panel(
            f"[green]Task {task.id} completed.[/green]  "
            f"Cost: ${task.cost_usd or 0:.4f}  "
            f"Duration: {(task.duration_ms or 0) / 1000:.1f}s",
            border_style="green",
        )
    )


@app.command()
def run(
    task: str = typer.Argument(help="Task description for the AI agents"),
    project: str | None = typer.Option(
        None, "--project", "-p", help="Project directory to work in"
    ),
    task_type: TaskType = typer.Option(
        TaskType.FEATURE, "--type", "-t", help="Task type"
    ),
    project_id: str | None = typer.Option(
        None, "--project-id", help="Associate with a project ID"
    ),
) -> None:
    """Run a task through the multi-agent system."""
    asyncio.run(_run_task(task, project, task_type, project_id))


# ── status ───────────────────────────────────────────────────────────────


@app.command()
def status() -> None:
    """Show system status, task summary, and recent tasks."""
    settings = Settings()
    store = _get_store(settings)
    tasks = store.list_tasks()
    projects = store.list_projects()

    console.print(Panel("AI Company System Status", border_style="green"))
    console.print(f"  Projects dir:  {settings.projects_dir.resolve()}")
    console.print(f"  Data dir:      {settings.data_dir.resolve()}")
    console.print(f"  Default model: {settings.default_model}")
    console.print(f"  Reviewer model: {settings.reviewer_model}")
    console.print()

    # Task summary
    by_status: dict[str, int] = {}
    for t in tasks:
        by_status[t.status.value] = by_status.get(t.status.value, 0) + 1
    console.print(f"  Tasks: {len(tasks)} total  {by_status}" if tasks else "  Tasks: 0")
    console.print(f"  Projects: {len(projects)}")

    # Recent tasks
    if tasks:
        console.print()
        console.print("[bold]Recent Tasks:[/bold]")
        table = Table(show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Title", max_width=50)
        table.add_column("Status")
        table.add_column("Type")
        for t in tasks[-5:]:
            status_color = {
                "completed": "green",
                "review": "yellow",
                "in_progress": "blue",
                "rejected": "red",
            }.get(t.status.value, "white")
            table.add_row(
                t.id,
                t.title,
                f"[{status_color}]{t.status.value}[/{status_color}]",
                t.type.value,
            )
        console.print(table)


# ── tasks ────────────────────────────────────────────────────────────────


@tasks_app.command("list")
def tasks_list(
    task_status: TaskStatus | None = typer.Option(
        None, "--status", "-s", help="Filter by status"
    ),
    project_id: str | None = typer.Option(
        None, "--project-id", help="Filter by project"
    ),
) -> None:
    """List all tasks."""
    store = _get_store()
    tasks = store.list_tasks(status=task_status, project_id=project_id)

    if not tasks:
        console.print("[dim]No tasks found.[/dim]")
        return

    table = Table(show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Title", max_width=50)
    table.add_column("Status")
    table.add_column("Type")
    table.add_column("Cost")
    table.add_column("Created")

    for t in tasks:
        status_color = {
            "completed": "green",
            "review": "yellow",
            "in_progress": "blue",
            "rejected": "red",
        }.get(t.status.value, "white")
        cost = f"${t.cost_usd:.4f}" if t.cost_usd else "-"
        table.add_row(
            t.id,
            t.title,
            f"[{status_color}]{t.status.value}[/{status_color}]",
            t.type.value,
            cost,
            t.created_at.strftime("%Y-%m-%d %H:%M"),
        )
    console.print(table)


@tasks_app.command("show")
def tasks_show(
    task_id: str = typer.Argument(help="Task ID to show"),
) -> None:
    """Show details for a specific task."""
    store = _get_store()
    task = store.load_task(task_id)

    if not task:
        console.print(f"[red]Task '{task_id}' not found.[/red]")
        raise typer.Exit(1)

    console.print(Panel(f"Task: {task.title}", border_style="blue"))
    console.print(f"  ID:          {task.id}")
    console.print(f"  Type:        {task.type.value}")
    console.print(f"  Status:      {task.status.value}")
    console.print(f"  Project:     {task.project_id or '-'}")
    console.print(f"  Created:     {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    console.print(f"  Updated:     {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if task.cost_usd is not None:
        console.print(f"  Cost:        ${task.cost_usd:.4f}")
    if task.duration_ms is not None:
        console.print(f"  Duration:    {task.duration_ms / 1000:.1f}s")
    if task.session_id:
        console.print(f"  Session:     {task.session_id}")

    console.print(f"\n  [bold]Description:[/bold]\n  {task.description}")

    if task.results:
        console.print(f"\n  [bold]Results ({len(task.results)}):[/bold]")
        for i, r in enumerate(task.results, 1):
            console.print(f"\n  --- Result {i} ({r.agent.value}) ---")
            console.print(f"  {r.summary}")
            if r.artifacts:
                console.print(f"  Artifacts: {', '.join(r.artifacts)}")


# ── init-project ─────────────────────────────────────────────────────────


@app.command()
def init_project(
    name: str = typer.Argument(help="Project name"),
    description: str = typer.Option("", "--desc", "-d", help="Project description"),
) -> None:
    """Initialize a new project directory and register it in the store."""
    settings = Settings()
    store = _get_store(settings)
    project_path = settings.projects_dir / name

    if project_path.exists():
        console.print(f"[red]Project '{name}' already exists.[/red]")
        raise typer.Exit(1)

    # Create directory structure
    for subdir in ["docs", "docs/research", "src", "tests", "reviews"]:
        (project_path / subdir).mkdir(parents=True, exist_ok=True)

    (project_path / "docs" / "requirements.md").write_text(
        f"# {name}\n\n## Requirements\n\n(To be defined)\n"
    )
    (project_path / "docs" / "architecture.md").write_text(
        f"# {name} - Architecture\n\n(To be defined)\n"
    )

    # Register in store
    project = Project(
        id=store.next_project_id(),
        name=name,
        description=description or f"Project {name}",
        path=project_path,
    )
    store.save_project(project)

    console.print(
        f"[green]Project '{name}' initialized at {project_path} (ID: {project.id})[/green]"
    )


if __name__ == "__main__":
    app()

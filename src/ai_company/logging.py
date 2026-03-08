"""Logging setup with Rich console and file output."""

import logging
from pathlib import Path

from rich.logging import RichHandler

_configured = False


def setup_logging(level: str = "INFO", log_dir: Path | None = None) -> None:
    """Configure logging with Rich console handler and optional file handler."""
    global _configured
    if _configured:
        return
    _configured = True

    root = logging.getLogger("ai_company")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Rich console handler
    console_handler = RichHandler(
        rich_tracebacks=True,
        show_path=False,
        markup=True,
    )
    console_handler.setLevel(logging.INFO)
    root.addHandler(console_handler)

    # File handler
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "ai-company.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        root.addHandler(file_handler)

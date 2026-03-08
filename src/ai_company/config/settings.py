"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "AI_COMPANY_", "env_file": ".env"}

    # Paths
    projects_dir: Path = Path("./projects")
    data_dir: Path = Path("./data")

    # Agent defaults
    default_model: str = "sonnet"
    orchestrator_model: str = "sonnet"
    reviewer_model: str = "opus"
    max_turns: int = 30

    # Logging
    log_level: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_prefix": "AI_COMPANY_",
        "extra": "ignore",
    }


def get_settings() -> Settings:
    return Settings()

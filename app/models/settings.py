from pathlib import Path

from pydantic import validator

from framework.core.env import load_env
from framework.models.settings import PythonFastAPIBaseSettings


class Settings(PythonFastAPIBaseSettings):
    RISA_HOST_BASE_URL: str = "http://localhost:5000"
    HUB_PATH: str = ""
    EXPORT_API_KEY: str = ""
    DASHBOARD_CONFIG_PATH: str = "/app/data/config_dashboard.yaml"
    DATASET_TAGGER_WALKTHROUGH_PATH: str = "/app/data/dataset_tagger_walkthrough.yaml"

    # Job Queue
    HUEY_SQLITE_PATH: str = "/app/data/huey_jobs.db"
    IDLE_TIMEOUT_MINUTES: int = 30

    @validator("EXPORT_API_KEY")
    def validate_export_api_key(cls, v: str) -> str:
        """Validate that EXPORT_API_KEY is provided and not the default value."""
        if v == "invalid_default_value":
            raise ValueError(
                "EXPORT_API_KEY must be provided via environment variable or .env file"
            )
        return v


def get_settings(env_file_path: Path | str, version: str | None = None) -> Settings:
    load_env(env_file_path)
    return Settings(VERSION=version)

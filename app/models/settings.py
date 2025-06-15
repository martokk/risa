from pathlib import Path

from framework.core.env import load_env
from framework.models.settings import PythonFastAPIBaseSettings


class Settings(PythonFastAPIBaseSettings):
    RISA_HOST_BASE_URL: str = "http://localhost:5000"
    HUB_PATH: str = ""
    EXPORT_API_KEY: str = ""
    DASHBOARD_CONFIG_PATH: str = ""

    # Job Queue
    HUEY_SQLITE_PATH: str = ""
    IDLE_TIMEOUT_MINUTES: int = 30


def get_settings(env_file_path: Path | str, version: str | None = None) -> Settings:
    load_env(env_file_path)
    return Settings(VERSION=version)

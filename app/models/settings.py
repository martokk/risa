import os
from pathlib import Path

from pydantic import root_validator, validator

from framework.core.env import load_env
from framework.models.settings import PythonFastAPIBaseSettings


class Settings(PythonFastAPIBaseSettings):
    HUB_PATH: str = ""
    EXPORT_API_KEY: str = ""
    WORKSPACE_PATH: str = "/workspace"
    DASHBOARD_CONFIG_PATH: str = "app/data/config_dashboard.yaml"
    DATASET_TAGGER_WALKTHROUGH_PATH: str = "app/data/dataset_tagger_walkthrough.yaml"
    IDLE_TIMEOUT_MINUTES: int = 30

    @validator("EXPORT_API_KEY")
    def validate_export_api_key(cls, v: str) -> str:
        """Validate that EXPORT_API_KEY is provided and not the default value."""
        if v == "invalid_default_value":
            raise ValueError(
                "EXPORT_API_KEY must be provided via environment variable or .env file"
            )
        return v

    @root_validator(pre=True)
    def set_base_url(cls, values: dict) -> dict:
        """Set BASE_URL based on ENV_NAME."""
        env_name = values.get("ENV_NAME")
        if env_name == "playground":
            runpod_pod_id = os.environ.get("RUNPOD_POD_ID")
            port = 1000
            values["BASE_URL"] = f"https://{runpod_pod_id}-{port}.proxy.runpod.net"
        return values

    @property
    def risa_project_name(self) -> str:
        return f"r|{self.ENV_NAME.upper()}"


def get_settings(env_file_path: Path | str, version: str | None = None) -> Settings:
    load_env(env_file_path)
    return Settings(VERSION=version)

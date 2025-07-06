import yaml
from pydantic import BaseModel

from app import paths
from app.logic.app_manager import AppManagerApp


class IdleWatcherConfig(BaseModel):
    idle_timeout_minutes: int = 99


class JobsConfig(BaseModel):
    start_huey_consumers_on_start: bool = True


class AppManagerConfig(BaseModel):
    apps: list[AppManagerApp] = []

    def post_init(self) -> None:
        self.apps = [AppManagerApp.model_validate(app) for app in self.apps]


class Config(BaseModel):
    accent: str = "#0000ff"
    idle_watcher: IdleWatcherConfig
    jobs: JobsConfig
    app_manager: AppManagerConfig


def get_config() -> Config:
    """Get the config."""
    config_path = paths.RISA_CONFIG_FILE

    if not config_path.exists():
        raise ValueError(f"Risa config file `{config_path}` not found")

    with open(config_path) as f:
        config_yaml = yaml.safe_load(f)

    config = Config.model_validate(config_yaml)

    return config

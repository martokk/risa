from typing import Any

import yaml

from app import paths
from app.logic.app_manager import AppManagerApp


def get_config() -> dict[str, Any]:
    """Get the config for the dashboard."""
    config_path = paths.DASHBOARD_CONFIG_FILE

    if not config_path.exists():
        raise ValueError(f"Dashboard config file `{config_path}` not found")

    with open(config_path) as f:
        config_yaml = yaml.safe_load(f)

    app_instances = []
    if config_yaml and "app_manager" in config_yaml:
        apps_data = config_yaml["app_manager"]["apps"]
        for app in apps_data:
            app_instances.append(AppManagerApp.model_validate(app))

    config: dict[str, Any] = config_yaml
    config["apps"] = app_instances

    return config

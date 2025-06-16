# PROJECT STRUCTURE
from pathlib import Path

from app.models.settings import get_settings
from framework.paths import *
from framework.paths import DATA_PATH, ENV_FILE, PROJECT_PATH


# Load ENV File - Needed for Settings
settings = get_settings(env_file_path=ENV_FILE)


def convert_relative_path_to_absolute(path: str) -> Path:
    if str(path).startswith("/app/"):
        joined_path = f"{PROJECT_PATH}{path}"
        return Path(joined_path)
    return Path(path)


HUEY_DB_PATH = convert_relative_path_to_absolute(settings.HUEY_SQLITE_PATH)

JOB_DB_PATH = DATA_PATH / "jobs.json"
DASHBOARD_CONFIG_FILE = convert_relative_path_to_absolute(settings.DASHBOARD_CONFIG_PATH)
DATASET_TAGGER_WALKTHROUGH_PATH = convert_relative_path_to_absolute(
    settings.DATASET_TAGGER_WALKTHROUGH_PATH
)


# HUB PATHS
HUB_PATH = Path(settings.HUB_PATH)
HUB_MODELS_PATH = HUB_PATH / "models"

# PROJECT STRUCTURE
from pathlib import Path

from app.models.settings import get_settings
from framework.paths import *
from framework.paths import ENV_FILE, PROJECT_PATH


# Load ENV File - Needed for Settings
settings = get_settings(env_file_path=str(ENV_FILE))


def convert_relative_path_to_absolute(path: str) -> Path:
    if str(path).startswith("/app/"):
        joined_path = f"{PROJECT_PATH}{path}"
        return Path(joined_path)
    return Path(path)


HUEY_DB_PATH = convert_relative_path_to_absolute(settings.HUEY_SQLITE_PATH)

DASHBOARD_CONFIG_FILE = convert_relative_path_to_absolute(settings.DASHBOARD_CONFIG_PATH)
DATASET_TAGGER_WALKTHROUGH_PATH = convert_relative_path_to_absolute(
    settings.DATASET_TAGGER_WALKTHROUGH_PATH
)


# HUB PATHS
WORKSPACE_PATH = Path(settings.WORKSPACE_PATH)
INPUTS_PATH = WORKSPACE_PATH / "__INPUTS__"
OUTPUTS_PATH = WORKSPACE_PATH / "__OUTPUTS__"
CACHE_PATH = WORKSPACE_PATH / ".cache"
LOGS_PATH = WORKSPACE_PATH / ".logs"
APPS_PATH = WORKSPACE_PATH / "apps"
CONFIGS_PATH = WORKSPACE_PATH / "configs"
HUB_PATH = (
    Path(settings.HUB_PATH)
    if settings.HUB_PATH and settings.HUB_PATH != ""
    else WORKSPACE_PATH / "hub"
)

# INPUTS
INPUTS_DATASETS_PATH = INPUTS_PATH / "datasets"

# OUTPUTS
OUTPUTS_A1111_PATH = OUTPUTS_PATH / "a1111"
OUTPUTS_KOHYA_SS_PATH = OUTPUTS_PATH / "kohya_ss"

# CACHE
VENVS_PATH = CACHE_PATH / "venvs"

# LOGS

# APPS

# CONFIGS

# HUB
HUB_MODELS_PATH = HUB_PATH / "models"

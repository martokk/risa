# PROJECT STRUCTURE
from pathlib import Path

from app.models.settings import get_settings
from framework.paths import *
from framework.paths import ENV_FILE, PROJECT_PATH


def convert_relative_path_to_absolute(path: str) -> Path:  # TODO: Move to framework.paths
    if str(path).startswith("/app/"):
        joined_path = f"{PROJECT_PATH}{path}"
        return Path(joined_path)
    if str(path).startswith("app/"):
        joined_path = f"{PROJECT_PATH}/{path}"
        return Path(joined_path)
    return Path(path)


# Load ENV File - Needed for Settings
settings = get_settings(env_file_path=str(ENV_FILE))

# LOAD CONFIG
RISA_CONFIG_FILE = convert_relative_path_to_absolute(settings.RISA_CONFIG_PATH)

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

HUEY_DEFAULT_DB_PATH = convert_relative_path_to_absolute(settings.HUEY_DEFAULT_SQLITE_PATH)
HUEY_RESERVED_DB_PATH = convert_relative_path_to_absolute(settings.HUEY_RESERVED_SQLITE_PATH)
HUEY_DEFAULT_LOG_PATH = convert_relative_path_to_absolute(settings.HUEY_DEFAULT_LOG_PATH)
HUEY_RESERVED_LOG_PATH = convert_relative_path_to_absolute(settings.HUEY_RESERVED_LOG_PATH)
HUEY_DEFAULT_PID_FILE = HUEY_DEFAULT_LOG_PATH.with_suffix(".pid")
HUEY_RESERVED_PID_FILE = HUEY_RESERVED_LOG_PATH.with_suffix(".pid")

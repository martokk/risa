# PROJECT STRUCTURE
from pathlib import Path

from app.models.settings import get_settings
from framework.paths import *
from framework.paths import DATA_PATH, ENV_FILE


# Load ENV File - Needed for Settings
settings = get_settings(env_file_path=ENV_FILE)

HUEY_DB_PATH = (
    Path(settings.HUEY_SQLITE_PATH) if settings.HUEY_SQLITE_PATH else DATA_PATH / "huey.sqlite3"
)
JOB_DB_PATH = DATA_PATH / "jobs.json"
DASHBOARD_CONFIG_FILE = Path(settings.DASHBOARD_CONFIG_PATH)
DATASET_TAGGER_WALKTHROUGH_PATH = Path(settings.DATASET_TAGGER_WALKTHROUGH_PATH)


# HUB PATHS
HUB_PATH = Path(settings.HUB_PATH)
HUB_MODELS_PATH = HUB_PATH / "models"

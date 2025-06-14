# PROJECT STRUCTURE
import os
from pathlib import Path

from dotenv import load_dotenv

from app.models.settings import Settings as _Settings


# Project Path
BASE_PATH = Path(os.path.dirname(os.path.abspath(__file__)))

# Folders
DATA_PATH = BASE_PATH / "data"
FRONTEND_PATH = BASE_PATH / "frontend"

# Frontend Folder
STATIC_PATH = FRONTEND_PATH / "static"
EMAIL_TEMPLATES_PATH = FRONTEND_PATH / "email-templates"
TEMPLATES_PATH = FRONTEND_PATH / "templates"

# Data Folder
LOGS_PATH = DATA_PATH / "logs"
CACHE_PATH = DATA_PATH / "cache"
UPLOAD_PATH = DATA_PATH / "uploads"

# Job Queue Paths
JOB_LOGS_PATH = LOGS_PATH / "jobs"

# ENV File
ENV_FILE = DATA_PATH / ".env"

_env_file = os.getenv("ENV_FILE", ENV_FILE)
load_dotenv(dotenv_path=_env_file)


# Files
HUEY_DB_PATH = (
    Path(_Settings().HUEY_SQLITE_PATH)
    if _Settings().HUEY_SQLITE_PATH
    else DATA_PATH / "huey.sqlite3"
)
JOB_DB_PATH = DATA_PATH / "jobs.json"
DATABASE_FILE = DATA_PATH / "database.sqlite3"
DASHBOARD_CONFIG_FILE = Path(_Settings().DASHBOARD_CONFIG_PATH)
LOG_FILE = LOGS_PATH / "log.log"
ERROR_LOG_FILE = LOGS_PATH / "error_log.log"
DATASET_TAGGER_WALKTHROUGH_PATH = DATA_PATH / "dataset_tagger_walkthrough.yaml"


# HUB PATHS
HUB_PATH = Path(_Settings().HUB_PATH)
HUB_MODELS_PATH = HUB_PATH / "models"

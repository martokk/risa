# PROJECT STRUCTURE
import os
from pathlib import Path

from app.models.settings import Settings as _Settings


# Project Path
BASE_PATH = Path(os.path.dirname(os.path.abspath(__file__)))

# Folders
DATA_PATH = BASE_PATH / "data"
VIEWS_PATH = BASE_PATH / "views"

# Views Folder
STATIC_PATH = VIEWS_PATH / "static"
EMAIL_TEMPLATES_PATH = VIEWS_PATH / "email-templates"
TEMPLATES_PATH = VIEWS_PATH / "templates"

# Data Folder
LOGS_PATH = DATA_PATH / "logs"
CACHE_PATH = DATA_PATH / "cache"
UPLOAD_PATH = DATA_PATH / "uploads"

# Files
ENV_FILE = DATA_PATH / ".env"
DATABASE_FILE = DATA_PATH / "database.sqlite3"
LOG_FILE = LOGS_PATH / "log.log"
ERROR_LOG_FILE = LOGS_PATH / "error_log.log"


# HUB PATHS
HUB_PATH = Path(_Settings().HUB_PATH)
HUB_MODELS_PATH = HUB_PATH / "models"

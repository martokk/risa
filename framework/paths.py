# PROJECT STRUCTURE
import os
from pathlib import Path


# Project Path
PROJECT_PATH = Path(os.path.dirname(os.path.abspath(__file__))).parent

# MAIN PATHS
APP_PATH = PROJECT_PATH / "app"
FRAMEWORK_PATH = PROJECT_PATH / "framework"

# Folders
DATA_PATH = APP_PATH / "data"
FRONTEND_PATH = APP_PATH / "frontend"

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
RISA_ENV_FILE = os.environ.get("RISA_ENV_FILE")

ENV_FILES_PATHS = [
    Path(RISA_ENV_FILE) if RISA_ENV_FILE else None,
    PROJECT_PATH / RISA_ENV_FILE if RISA_ENV_FILE else None,
    DATA_PATH / ".env",
]
ENV_FILE = None
for env_file_path in ENV_FILES_PATHS:
    if env_file_path and env_file_path.exists():
        ENV_FILE = env_file_path
        break

if not ENV_FILE:
    print("No ENV file found, using default 'framework' .env file.")
    ENV_FILE = FRAMEWORK_PATH / "data" / ".env"

# Files
DATABASE_FILE = DATA_PATH / "database.sqlite3"
LOG_FILE = LOGS_PATH / "log.log"
ERROR_LOG_FILE = LOGS_PATH / "error_log.log"

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
RISA_ENV_FILE = os.environ.get("ENV_FILE")

ENV_FILES_PATHS = [
    Path(RISA_ENV_FILE) if RISA_ENV_FILE else None,
    PROJECT_PATH / RISA_ENV_FILE if RISA_ENV_FILE else None,
    DATA_PATH / ".env",
]
ENV_FILE = None

if not ENV_FILE:
    ENV_FILE = FRAMEWORK_PATH / "data" / ".env"

for env_file_path in ENV_FILES_PATHS:
    if env_file_path and env_file_path.exists():
        print(f"Found ENV file at {env_file_path}")
        ENV_FILE = env_file_path
        break


print(f"ENV_FILE={ENV_FILE}")

# Files
# DATABASE_FILE = DATA_PATH / "database.sqlite3"
PYPROJECT_FILE = PROJECT_PATH / "pyproject.toml"
LOG_FILE = LOGS_PATH / "log.log"
ERROR_LOG_FILE = LOGS_PATH / "error_log.log"

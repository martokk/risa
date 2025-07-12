import toml

from app.models.settings import get_settings
from app.paths import ENV_FILE as _ENV_FILE, PYPROJECT_FILE
from vcore.backend.core.logger import setup_logger


def get_app_version() -> str:
    pyproject = toml.load(PYPROJECT_FILE)
    return str(pyproject["tool"]["poetry"]["version"])


settings = get_settings(env_file_path=_ENV_FILE, version=get_app_version())
logger = setup_logger(settings=settings)

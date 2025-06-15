from app.models.settings import get_settings
from app.paths import ENV_FILE as _ENV_FILE
from framework.core.logger import setup_logger


settings = get_settings(env_file_path=_ENV_FILE)
logger = setup_logger(settings=settings)

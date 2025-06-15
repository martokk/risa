from os import getenv as _getenv
from pathlib import Path

from dotenv import load_dotenv as _load_dotenv


def load_env(env_file_path: Path | str) -> None:
    """
    Load the environment variables from the given file path.

    Args:
        env_file_path: The path to the environment variables file.
    """
    _env_file = _getenv("ENV_FILE", Path(env_file_path))
    _load_dotenv(dotenv_path=_env_file)
    print(f"Loaded ENV_FILE: {_env_file}")

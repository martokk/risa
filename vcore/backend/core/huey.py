from pathlib import Path

from huey import SqliteHuey

from app import paths


# Create a Huey instance using the SQLite backend.
# The path to the database is configured in `app/paths.py`.


def get_huey(file_path: str | Path) -> SqliteHuey:
    print(f"HUEY DB PATH: {file_path}")

    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    return SqliteHuey(filename=str(file_path))


huey_default = get_huey(file_path=paths.HUEY_DEFAULT_DB_PATH)
huey_reserved = get_huey(file_path=paths.HUEY_RESERVED_DB_PATH)

from pathlib import Path

from huey import SqliteHuey

from app import paths


# Create a Huey instance using the SQLite backend.
# The path to the database is configured in `app/paths.py`.


def get_huey(file_path: str | Path) -> SqliteHuey:
    print(f"HUEY_DB_PATH: {file_path}")

    Path(file_path).mkdir(parents=True, exist_ok=True)

    return SqliteHuey(filename=str(file_path))


huey = get_huey(file_path=paths.HUEY_DB_PATH)

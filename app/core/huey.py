from huey import SqliteHuey

from app import paths


# Create a Huey instance using the SQLite backend.
# The path to the database is configured in `app/paths.py`.
huey = SqliteHuey(filename=str(paths.HUEY_DB_PATH))

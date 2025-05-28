from fastapi import FastAPI

from app import logger


class TaskScheduler:
    """Scheduler for background tasks."""

    def __init__(self, app: FastAPI):
        self.app = app
        self.logger = logger

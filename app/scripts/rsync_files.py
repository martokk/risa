from typing import Any

from app import logger
from app.logic.rsync import convert_risa_rsync_options_to_text
from framework import crud, models
from framework.core.db import get_db_context
from framework.services import scripts


class ScriptRsyncFiles(scripts.Script):
    """
    This script rsyncs files from one location to another.

    It uses the following parameters:
    - source_env: The environment to rsync from.
    - source_loc: The location to rsync from.
    - dest_env: The environment to rsync to.
    - dest_loc: The location to rsync to.
    - option_u: Skip destination files that are newer.
    - option_ignore_existing: Skip destination files that already exist.
    - option_recursive: Recursively copy directories.
    """

    def _validate_input(self, *args: Any, **kwargs: Any) -> bool:
        """
        Validate the input.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if the input is valid, False otherwise.
        """
        if not kwargs.get("source_env"):
            logger.error("source_env is required")
            return False
        if not kwargs.get("source_loc"):
            logger.error("source_loc is required")
            return False
        if not kwargs.get("dest_env"):
            logger.error("dest_env is required")
            return False
        if not kwargs.get("dest_loc"):
            logger.error("dest_loc is required")
            return False
        if kwargs.get("option_u") and kwargs.get("option_ignore_existing"):
            logger.error("option_u and option_ignore_existing cannot be used together")
            return False

        return True

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """
        Run the script.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        logger.debug(f"Starting {self.__class__.__name__}._run()")
        logger.debug(f"kwargs: {kwargs}")

        # Create rsync command job
        rsync_command = generate_rsync_command_job(
            source_env=kwargs["source_env"],
            source_loc=kwargs["source_loc"],
            dest_env=kwargs["dest_env"],
            dest_loc=kwargs["dest_loc"],
            option_u=kwargs.get("option_u", False),
            option_ignore_existing=kwargs.get("option_ignore_existing", False),
            option_recursive=kwargs.get("option_recursive", False),
        )

        # Add job to queue
        with get_db_context() as db:
            db_job = crud.job.sync.create(
                db,
                obj_in=models.JobCreate(
                    env_name=kwargs["env_name"],
                    queue_name=kwargs["queue_name"],
                    name=f"Rsync Files: {kwargs['source_loc']} to {kwargs['dest_loc']}",
                    type=models.JobType.command,
                    command=rsync_command,
                    meta=kwargs,
                    status=models.JobStatus.queued,
                ),
            )

        job_on_text = convert_risa_rsync_options_to_text(
            env_name=kwargs.get("env_name"),
            queue_name=kwargs.get("queue_name"),
            source_env=kwargs.get("source_env"),
            source_loc=kwargs.get("source_loc"),
            dest_env=kwargs.get("dest_env"),
            dest_loc=kwargs.get("dest_loc"),
            option_u=kwargs.get("option_u"),
            option_ignore_existing=kwargs.get("option_ignore_existing"),
        )

        return scripts.ScriptOutput(
            success=True,
            message=f"Rsync command job created `{db_job.id}` {job_on_text}",
            data={
                "rsync_command": rsync_command,
                "job_on_text": job_on_text,
                "job_id": db_job.id,
            },
        )

import subprocess
from pathlib import Path
from typing import Any

from app import logger
from app.logic.rsync import generate_rsync_command_job
from framework.services import scripts


class ScriptRsyncFiles(scripts.Script):
    """
    This script rsyncs files from one location to another.

    It uses the following parameters:
    - source_env: The environment to rsync from.
    - source_location: The location to rsync from.
    - destination_env: The environment to rsync to.
    - destination_location: The location to rsync to.
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
        if not kwargs.get("source_location"):
            logger.error("source_location is required")
            return False
        if not kwargs.get("destination_env"):
            logger.error("destination_env is required")
            return False
        if not kwargs.get("destination_location"):
            logger.error("destination_location is required")
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
            job_env=kwargs["job_env"],
            source_env=kwargs["source_env"],
            source_location=kwargs["source_location"],
            destination_env=kwargs["destination_env"],
            destination_location=kwargs["destination_location"],
            option_u=kwargs.get("option_u", False),
            option_ignore_existing=kwargs.get("option_ignore_existing", False),
            option_recursive=kwargs.get("option_recursive", False),
        )

        # Make destination directory if it doesn't exist
        destination_location = Path(kwargs["destination_location"])  # could be file or folder
        if destination_location.is_file():
            destination_location = destination_location.parent
        if not destination_location.exists():
            destination_location.mkdir(parents=True, exist_ok=True)

        # Run command using subprocess save output to file
        try:
            process = subprocess.run(rsync_command, shell=True, capture_output=True, text=True)
            print(process.stdout)
            print(process.stderr)
            print(process.returncode)
        except Exception as e:
            logger.error(f"Error running rsync command: {e}")
            return scripts.ScriptOutput(
                success=False, message=f"Error running rsync command: {e}", data={}
            )

        # # Add job to queue
        # with get_db_context() as db:
        #     db_job = crud.job.sync.create(
        #         db,
        #         obj_in=models.JobCreate(
        #             env_name=kwargs["job_env"],
        #             queue_name=kwargs["queue_name"],
        #             name=f"Rsync Files: {kwargs['source_location']} to {kwargs['destination_location']}",
        #             type=models.JobType.command,
        #             command=rsync_command,
        #             meta=kwargs,
        #             status=models.JobStatus.queued,
        #         ),
        #     )

        # job_on_text = convert_risa_rsync_options_to_text(
        #     env_name=kwargs["job_env"],
        #     queue_name=kwargs["queue_name"],
        #     source_env=kwargs["source_env"],
        #     source_location=kwargs["source_location"],
        #     destination_env=kwargs["destination_env"],
        #     destination_location=kwargs["destination_location"],
        #     option_u=kwargs["option_u"],
        #     option_ignore_existing=kwargs["option_ignore_existing"],
        # )

        return scripts.ScriptOutput(
            success=True,
            message="Rsync completed.",
            data={
                "rsync_command": rsync_command,
            },
        )

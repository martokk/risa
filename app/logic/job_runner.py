"""
This module contains the core logic for executing jobs.
"""

import subprocess

import requests

from app import logger, models, paths


def write_job_log(job: models.Job, output: str) -> None:
    """
    Writes the output of a job to a versioned log file.

    Args:
        job: The job that was executed.
        output: The stdout/stderr output from the job execution.
    """
    log_file_name = f"job_{job.id}_retry_{job.retry_count}.txt"
    log_path = paths.JOB_LOGS_PATH / log_file_name

    # Ensure the logs directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, "w") as f:
        f.write(output)
    logger.info(f"Wrote log for job {job.id} to {log_path}")


def run_command_job(job: models.Job) -> None:
    """
    Executes a command-line job using subprocess.

    Args:
        job: The job to execute.
    """
    try:
        # Execute the command and capture output
        result = subprocess.run(
            job.command,
            shell=True,
            capture_output=True,
            text=True,
            check=True,  # Raise CalledProcessError for non-zero exit codes
        )
        output = result.stdout
        logger.info(f"Command job {job.id} executed successfully.")
    except subprocess.CalledProcessError as e:
        # Handle cases where the command returns a non-zero exit code
        output = f"Error executing command: {e.stderr}\n{e.stdout}"
        logger.error(f"Command job {job.id} failed: {output}")
    except Exception as e:
        output = f"An unexpected error occurred: {str(e)}"
        logger.error(f"Unexpected error in command job {job.id}: {output}")

    write_job_log(job, output)


def run_api_post_job(job: models.Job) -> None:
    """
    Executes an API POST job using requests.

    Args:
        job: The job to execute.
    """
    try:
        response = requests.post(job.command, json=job.meta)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        output = response.text
        logger.info(f"API POST job {job.id} executed successfully.")
    except requests.exceptions.RequestException as e:
        output = f"Error executing API POST job: {str(e)}"
        logger.error(f"API POST job {job.id} failed: {output}")
    except Exception as e:
        output = f"An unexpected error occurred: {str(e)}"
        logger.error(f"Unexpected error in API POST job {job.id}: {output}")

    write_job_log(job, output)


def execute_job(job: models.Job) -> None:
    """
    Central function to execute a job based on its type.

    Args:
        job: The job to execute.
    """
    logger.info(f"Executing job {job.id} of type {job.type.value}")

    if job.type == models.JobType.command:
        run_command_job(job)
    elif job.type == models.JobType.api_post:
        run_api_post_job(job)

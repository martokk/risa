"""
This module contains the core logic for executing jobs.
"""

import subprocess

import requests
from tinydb import Query, TinyDB

from app import logger, paths
from framework import schemas


def run_command_job(job: schemas.Job) -> None:
    """
    Executes a command-line job using subprocess and logs output in real-time.

    Args:
        job: The job to execute.
    """
    log_file_name = f"job_{job.id}_retry_{job.retry_count}.txt"
    log_path = paths.JOB_LOGS_PATH / log_file_name

    # Ensure the logs directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize the TinyDB database for jobs
    db = TinyDB(paths.JOB_DB_PATH)

    try:
        # Open the log file for writing
        with open(log_path, "w") as log_file:
            # Execute the command and stream output in real-time
            process = subprocess.Popen(
                job.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Redirect stderr to stdout
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True,
            )

            pid = process.pid
            logger.info(f"Command job {job.id} started with PID {pid}")

            db.update({"pid": pid}, Query().id == str(job.id))

            print("\n\n\n--------------------------------")
            print("JOB")
            print(f"job: {job}")
            print(f"job.id: {job.id}")
            print(f"pid: {pid}")
            print("--------------------------------\n\n\n")
            print(f"db: {db}")
            print("--------------------------------")
            print("DB JOB")
            db_job = db.get(Query().id == str(job.id))
            db_job_object = schemas.Job(**db_job)

            print(f"db_job_object: {db_job_object}")
            print(f"db_job_object.id: {db_job_object.id if db_job_object else 'None'}")
            print(f"db_job_object.pid: {db_job_object.pid if db_job_object else 'None'}")
            print("--------------------------------")

            # Read and write output in real-time
            if process.stdout:
                for line in process.stdout:
                    log_file.write(line)
                    log_file.flush()  # Ensure immediate writing to disk
                logger.debug(f"Job {job.id} output: {line.strip()}")

            # Wait for the process to complete
            return_code = process.wait()

            if return_code == 0:
                logger.info(f"Command job {job.id} executed successfully.")
            else:
                error_msg = f"Command job {job.id} failed with exit code {return_code}"
                logger.error(error_msg)
                raise subprocess.CalledProcessError(return_code, job.command)

    except subprocess.CalledProcessError as e:
        logger.error(f"Command job {job.id} failed: {str(e)}")

        with open(log_path, "a") as log_file:
            log_file.write(f"Command job {job.id} failed: {str(e)}\n")
        raise  # Re-raise the exception to be caught by the Huey task
    except Exception as e:
        logger.error(f"Unexpected error in command job {job.id}: {str(e)}")
        raise


def run_api_post_job(job: schemas.Job) -> None:
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
        raise  # Re-raise
    except Exception as e:
        output = f"An unexpected error occurred: {str(e)}"
        logger.error(f"Unexpected error in API POST job {job.id}: {output}")
        raise

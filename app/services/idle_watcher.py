"""
This service monitors GPU activity and triggers jobs when the system is idle.
"""

import subprocess
import threading
import time

from app import logger, settings
from app.services import job_queue


class IdleWatcher(threading.Thread):
    """
    A background thread that monitors GPU utilization and triggers jobs
    from the queue when the system is determined to be idle.
    """

    def __init__(self, poll_interval: int = 60):
        super().__init__(daemon=True)
        self.poll_interval = poll_interval
        self.idle_start_time: float | None = None
        self.wake_flag = threading.Event()
        self.stop_event = threading.Event()

    def is_gpu_idle(self) -> bool:
        """
        Checks if the GPU is currently idle by querying nvidia-smi.
        A GPU is considered idle if its utilization is 0%.
        """
        try:
            # This command queries GPU utilization and returns it.
            # It's a common way to check GPU status on NVIDIA hardware.
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                check=True,
            )
            utilization = int(result.stdout.strip())
            return utilization == 0
        except (FileNotFoundError, subprocess.CalledProcessError, ValueError) as e:
            # Handle cases where nvidia-smi is not found or fails.
            logger.warning(f"Could not check GPU status: {e}. Assuming not idle.")
            return False

    def run(self):
        """
        The main loop for the watcher thread.
        """
        logger.info("Idle Watcher thread started.")
        while not self.stop_event.is_set():
            if self.wake_flag.is_set():
                logger.info("Wake flag is set. Idle watcher is paused.")
                self.idle_start_time = None
                # Wait until the wake_flag is cleared before resuming checks
                self.wake_flag.wait()
                logger.info("Wake flag cleared. Resuming idle checks.")

            if self.is_gpu_idle():
                if self.idle_start_time is None:
                    # Mark the time when the system first became idle
                    self.idle_start_time = time.time()
                    logger.info("System is now idle. Starting idle timer.")

                idle_duration = time.time() - self.idle_start_time
                idle_timeout_seconds = settings.IDLE_TIMEOUT_MINUTES * 60

                if idle_duration >= idle_timeout_seconds:
                    logger.info(
                        f"Idle timeout of {settings.IDLE_TIMEOUT_MINUTES} minutes reached. Triggering next job."
                    )
                    # Trigger the next job from the queue
                    job_queue.trigger_next_job()
                    # Reset the idle timer after triggering a job to wait again
                    self.idle_start_time = None
            else:
                # If the GPU is active, reset the idle timer
                if self.idle_start_time is not None:
                    logger.info("GPU is active. Resetting idle timer.")
                self.idle_start_time = None

            # Wait for the next poll interval
            self.stop_event.wait(self.poll_interval)

    def wake(self):
        """
        Sets the wake flag to pause idle-triggered execution and resets the timer.
        """
        logger.info("Waking up! Pausing idle job execution.")
        self.wake_flag.set()
        self.idle_start_time = None

    def resume(self):
        """
        Clears the wake flag to allow the idle watcher to resume.
        """
        logger.info("Resuming idle watcher.")
        self.wake_flag.clear()

    def stop(self):
        """
        Stops the watcher thread gracefully.
        """
        logger.info("Stopping idle watcher thread.")
        self.stop_event.set()


# Singleton instance of the watcher
idle_watcher = IdleWatcher()


def start_idle_watcher():
    """Starts the global idle watcher thread."""
    if not idle_watcher.is_alive():
        idle_watcher.start()


def stop_idle_watcher():
    """Stops the global idle watcher thread."""
    idle_watcher.stop()

import httpx

from app import logger, settings


def push_jobs_to_websocket() -> None:
    """
    Push all jobs to the websocket.
    """
    try:
        with httpx.Client() as client:
            client.post(
                f"{settings.BASE_URL}/api/v1/jobs/push-jobs-to-websocket",
            )

        logger.debug("Pushed jobs to websocket via api call")

    except Exception as e:
        logger.error(f"Failed to push jobs to websocket via api call: {e}")

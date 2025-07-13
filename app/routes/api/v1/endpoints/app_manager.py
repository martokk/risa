import subprocess

from fastapi import APIRouter, Depends, HTTPException, status

from app import models
from app.logic.config import get_config
from vcore.backend.templating.deps import get_current_active_user


router = APIRouter(prefix="/app_manager", tags=["App Manager"])


@router.post("/{app_id}/start", status_code=status.HTTP_200_OK)
async def start_app(
    app_id: str,
    current_user: models.User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Start an application."""
    config = get_config()
    app = next((app for app in config.app_manager.apps if app.id == app_id), None)

    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")

    try:
        # Using Popen to run in the background
        app.start()
        return {"status": "starting", "app_id": app_id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.post("/{app_id}/restart", status_code=status.HTTP_200_OK)
async def restart_app(
    app_id: str,
    current_user: models.User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Restart an application."""
    config = get_config()
    app = next((app for app in config.app_manager.apps if app.id == app_id), None)

    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")

    try:
        # Using Popen to run in the background
        app.restart()
        return {"status": "restarting", "app_id": app_id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.post("/{app_id}/stop", status_code=status.HTTP_200_OK)
async def stop_app(
    app_id: str,
    current_user: models.User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Stop an application."""
    config = get_config()
    app = next((app for app in config.app_manager.apps if app.id == app_id), None)

    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")

    try:
        app.stop()
        return {"status": "stopped", "app_id": app_id}
    except subprocess.CalledProcessError as e:
        # If the process isn't running, the stop command might fail. This is not necessarily an error we want to bubble up.
        return {
            "status": "already_stopped_or_error",
            "app_id": app_id,
            "detail": e.stderr.decode() if e.stderr else "",
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

import subprocess

from fastapi import APIRouter, Depends, HTTPException, status

from app import models
from app.logic.dashboard import get_config
from framework.api.deps import get_current_active_user


router = APIRouter(prefix="/app_manager", tags=["App Manager"])


@router.post("/{app_name}/start", status_code=status.HTTP_200_OK)
async def start_app(
    app_name: str,
    current_user: models.User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Start an application."""
    config = get_config()
    app_config = next((app for app in config["apps"] if app.name == app_name), None)

    if not app_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")

    try:
        # Using Popen to run in the background
        subprocess.Popen(app_config["start_command"], shell=True)
        return {"status": "starting", "app_name": app_name}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.post("/{app_name}/stop", status_code=status.HTTP_200_OK)
async def stop_app(
    app_name: str,
    current_user: models.User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Stop an application."""
    config = get_config()
    app_config = next((app for app in config["apps"] if app.name == app_name), None)

    if not app_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")

    try:
        subprocess.run(app_config["stop_command"], shell=True, check=True)
        return {"status": "stopped", "app_name": app_name}
    except subprocess.CalledProcessError as e:
        # If the process isn't running, the stop command might fail. This is not necessarily an error we want to bubble up.
        return {
            "status": "already_stopped_or_error",
            "app_name": app_name,
            "detail": e.stderr.decode() if e.stderr else "",
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

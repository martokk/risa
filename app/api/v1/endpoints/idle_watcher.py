"""
API endpoints for managing the idle watcher.
"""

from fastapi import APIRouter, HTTPException


router = APIRouter()


@router.post("/idle-watcher/wake", status_code=501)
def wake_watcher() -> None:
    """
    Interrupt idle-driven execution. (Not Implemented)
    """
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.post("/idle-watcher/config", status_code=501)
def configure_watcher() -> None:
    """
    Change idle timeout duration. (Not Implemented)
    """
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("/idle-watcher/status", status_code=501)
def get_watcher_status() -> None:
    """
    Returns the current idle state of the GPU. (Not Implemented)
    """
    raise HTTPException(status_code=501, detail="Not Implemented")

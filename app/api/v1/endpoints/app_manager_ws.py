import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlmodel import Session

from app.logic.config import get_config
from app.services.app_manager_ws_manager import app_manager_ws_manager
from framework.core.db import get_db


router = APIRouter()


def get_app_status():
    return {
        "app1": True,
        "app2": False,
    }


def get_log():
    return "Hello World"


@router.websocket("/ws/app_manager")
async def websocket_app_manager(websocket: WebSocket, db: Session = Depends(get_db)) -> None:
    await app_manager_ws_manager.connect(websocket)

    # Send initial state
    app_status = get_app_status()
    await websocket.send_json(
        {
            "app_status": app_status,
        }
    )
    log_task = None
    try:
        while True:
            data = await websocket.receive_text()
            # Try to parse as JSON for log subscription
            try:
                import json

                msg = json.loads(data)
            except Exception:
                msg = None
            if msg and msg.get("type") == "subscribe_app_log":
                if log_task:
                    log_task.cancel()
                topic = msg.get("topic")
                log_task = asyncio.create_task(stream_app_log(websocket=websocket, topic=topic))

            # Otherwise, just keep alive
    except WebSocketDisconnect:
        app_manager_ws_manager.disconnect(websocket)
    except Exception:
        app_manager_ws_manager.disconnect(websocket)
    finally:
        if log_task:
            log_task.cancel()


# async def stream_job_log(websocket: WebSocket, job_id: str) -> None:
#     """Stream the job log file to the websocket client in real-time."""
#     log_file_name = f"job_{job_id}_retry_0.txt"
#     from app import paths

#     log_path = paths.JOB_LOGS_PATH / log_file_name
#     last_pos = 0
#     try:
#         while True:
#             if not log_path.exists():
#                 await asyncio.sleep(0.5)
#                 continue
#             with open(log_path) as f:
#                 f.seek(last_pos)
#                 new_content = f.read()
#                 if new_content:
#                     await websocket.send_json(
#                         {"type": "log_update", "job_id": job_id, "content": new_content}
#                     )
#                     last_pos = f.tell()
#             await asyncio.sleep(0.5)
#     except asyncio.CancelledError:
#         pass
#     except Exception as e:
#         try:
#             await websocket.send_json({"type": "log_error", "job_id": job_id, "error": str(e)})
#         except Exception:
#             pass


async def stream_log(websocket: WebSocket, file_path: Path | str, topic: str) -> None:
    """Stream the log file to the websocket client."""
    file_path = Path(file_path)
    last_pos = 0
    try:
        # Send existing content first
        if file_path.exists():
            with open(file_path) as f:
                content = f.read()
                if content:
                    await websocket.send_json(
                        {"type": "log_update", "topic": topic, "content": content}
                    )
                last_pos = f.tell()

        # Now, tail the file for new content
        while True:
            if not file_path.exists():
                await asyncio.sleep(0.5)
                continue
            with open(file_path) as f:
                f.seek(last_pos)
                new_content = f.read()
                if new_content:
                    await websocket.send_json(
                        {"type": "log_update", "topic": topic, "content": new_content}
                    )
                    last_pos = f.tell()
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "log_error", "topic": topic, "error": str(e)})
        except Exception:
            pass


async def stream_app_log(websocket: WebSocket, topic: str) -> None:
    """Stream the main application log file to the websocket client."""

    config = get_config()
    app = next((app for app in config.app_manager.apps if app.id == topic), None)
    if not app:
        raise ValueError(f"App with id `{topic}` not found")

    file_path = app.log_file
    return await stream_log(websocket, file_path=file_path, topic=topic)

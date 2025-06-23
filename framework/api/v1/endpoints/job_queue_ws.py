import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlmodel import Session

from framework import crud
from framework.core.db import get_db
from framework.services import job_queue
from framework.services.job_queue_ws_manager import job_queue_ws_manager


router = APIRouter()


@router.websocket("/ws/job-queue")
async def websocket_job_queue(websocket: WebSocket, db: Session = Depends(get_db)) -> None:
    await job_queue_ws_manager.connect(websocket)

    # Send initial state
    jobs = await crud.job.get_all(db=db)
    consumer_status = "running" if job_queue.is_consumer_running() else "stopped"
    print(f"Consumer status: {consumer_status}")
    await websocket.send_json(
        {
            "jobs": [j.model_dump(mode="json") for j in jobs],
            "consumer_status": consumer_status,
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
            if msg and msg.get("type") == "subscribe_log" and "job_id" in msg:
                # Cancel any previous log task
                if log_task:
                    log_task.cancel()
                job_id = msg["job_id"]
                log_task = asyncio.create_task(stream_job_log(websocket, job_id))
            elif msg and msg.get("type") == "subscribe_consumer_log":
                if log_task:
                    log_task.cancel()
                log_task = asyncio.create_task(stream_consumer_log(websocket))
            # Otherwise, just keep alive
    except WebSocketDisconnect:
        job_queue_ws_manager.disconnect(websocket)
    except Exception:
        job_queue_ws_manager.disconnect(websocket)
    finally:
        if log_task:
            log_task.cancel()


async def stream_job_log(websocket: WebSocket, job_id: str) -> None:
    """Stream the job log file to the websocket client in real-time."""
    log_file_name = f"job_{job_id}_retry_0.txt"
    from app import paths

    log_path = paths.JOB_LOGS_PATH / log_file_name
    last_pos = 0
    try:
        while True:
            if not log_path.exists():
                await asyncio.sleep(0.5)
                continue
            with open(log_path) as f:
                f.seek(last_pos)
                new_content = f.read()
                if new_content:
                    await websocket.send_json(
                        {"type": "log_update", "job_id": job_id, "content": new_content}
                    )
                    last_pos = f.tell()
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "log_error", "job_id": job_id, "error": str(e)})
        except Exception:
            pass


async def stream_consumer_log(websocket: WebSocket) -> None:
    """Stream the main application log file to the websocket client."""
    from app.paths import LOG_FILE

    last_pos = 0
    try:
        # Send existing content first
        if LOG_FILE.exists():
            with open(LOG_FILE) as f:
                content = f.read()
                if content:
                    await websocket.send_json(
                        {"type": "log_update", "job_id": "consumer", "content": content}
                    )
                last_pos = f.tell()

        # Now, tail the file for new content
        while True:
            if not LOG_FILE.exists():
                await asyncio.sleep(0.5)
                continue
            with open(LOG_FILE) as f:
                f.seek(last_pos)
                new_content = f.read()
                if new_content:
                    await websocket.send_json(
                        {"type": "log_update", "job_id": "consumer", "content": new_content}
                    )
                    last_pos = f.tell()
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "log_error", "job_id": "consumer", "error": str(e)})
        except Exception:
            pass

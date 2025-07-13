import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlmodel import Session

from app import logger, paths, settings
from vcore.backend import crud
from vcore.backend.core.db import get_db
from vcore.backend.services.job_queue import get_consumer_status_map
from vcore.backend.services.job_queue_ws_manager import job_queue_ws_manager


router = APIRouter()


@router.websocket("/ws/job-queue")
async def websocket_job_queue(websocket: WebSocket, db: Session = Depends(get_db)) -> None:
    await job_queue_ws_manager.connect(websocket)

    # Send initial state
    jobs = await crud.job.get_all_jobs_for_env_name(db=db, env_name=settings.ENV_NAME)
    consumer_status = get_consumer_status_map()
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
            if msg and msg.get("type") == "subscribe_log" and "topic" in msg:
                # Cancel any previous log task
                if log_task:
                    log_task.cancel()
                topic = msg["topic"]
                log_task = asyncio.create_task(stream_job_log(websocket, topic))
            elif msg and msg.get("type") == "subscribe_consumer_log":
                if log_task:
                    log_task.cancel()
                topic = msg["topic"]
                log_task = asyncio.create_task(stream_consumer_log(websocket, topic))
            # Otherwise, just keep alive
    except WebSocketDisconnect:
        job_queue_ws_manager.disconnect(websocket)
    except Exception:
        job_queue_ws_manager.disconnect(websocket)
    finally:
        if log_task:
            log_task.cancel()


async def stream_job_log(websocket: WebSocket, topic: str) -> None:
    """Stream the job log file to the websocket client in real-time."""
    log_file_name = f"job_{topic}_retry_0.txt"
    from app import paths

    log_path = paths.JOB_LOGS_PATH / log_file_name
    logger.debug(f"log_path: {log_path}")
    last_pos = 0
    try:
        while True:
            if not log_path.exists():
                await asyncio.sleep(0.5)
                logger.warning(f"log_path does not exist: {log_path}")
                continue
            with open(log_path) as f:
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


async def stream_consumer_log(websocket: WebSocket, topic: str) -> None:
    """Stream the main application log file to the websocket client."""
    log_path = paths.HUEY_DEFAULT_LOG_PATH if topic == "default" else paths.HUEY_RESERVED_LOG_PATH

    last_pos = 0
    try:
        # Send existing content first
        if log_path.exists():
            with open(log_path) as f:
                content = f.read()
                if content:
                    await websocket.send_json(
                        {"type": "log_update", "topic": topic, "content": content}
                    )
                last_pos = f.tell()

        # Now, tail the file for new content
        while True:
            if not log_path.exists():
                await asyncio.sleep(0.5)
                continue
            with open(log_path) as f:
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

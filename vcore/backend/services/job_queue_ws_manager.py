from vcore.backend.core.websocket import WebSocketManager


class JobQueueConnectionManager(WebSocketManager):
    pass


job_queue_ws_manager = JobQueueConnectionManager()

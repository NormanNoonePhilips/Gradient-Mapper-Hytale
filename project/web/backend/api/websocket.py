"""WebSocket handler for real-time progress updates"""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

logger = logging.getLogger(__name__)

router = APIRouter()

# This will be set by main app
job_queue = None


def set_job_queue(queue):
    """Set job queue dependency"""
    global job_queue
    job_queue = queue


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_message(self, websocket: WebSocket, message: dict):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates"""
    await manager.connect(websocket)
    subscriptions = {}

    try:
        # Keep connection alive and listen for messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "subscribe":
                    # Subscribe to job progress
                    job_id = message.get("job_id")
                    if job_id and job_queue:
                        # Create callback for this WebSocket
                        if job_id in subscriptions:
                            job_queue.unsubscribe_progress(job_id, subscriptions[job_id])

                        async def progress_callback(progress_data):
                            await manager.send_message(websocket, progress_data)

                        job_queue.subscribe_progress(job_id, progress_callback)
                        subscriptions[job_id] = progress_callback
                        logger.info(f"WebSocket subscribed to job {job_id}")

                        # Send acknowledgment
                        await manager.send_message(websocket, {
                            "type": "subscribed",
                            "job_id": job_id
                        })

                elif message.get("type") == "ping":
                    # Respond to ping
                    await manager.send_message(websocket, {"type": "pong"})

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if job_queue:
            for job_id, callback in subscriptions.items():
                job_queue.unsubscribe_progress(job_id, callback)
        manager.disconnect(websocket)

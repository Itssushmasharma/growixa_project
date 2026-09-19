import asyncio
import json
import uuid
from typing import Dict, List, Any
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # account_id -> list of active WebSockets
        self.active_connections: Dict[uuid.UUID, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, account_id: uuid.UUID):
        await websocket.accept()
        if account_id not in self.active_connections:
            self.active_connections[account_id] = []
        self.active_connections[account_id].append(websocket)

    def disconnect(self, websocket: WebSocket, account_id: uuid.UUID):
        if account_id in self.active_connections:
            if websocket in self.active_connections[account_id]:
                self.active_connections[account_id].remove(websocket)
            if not self.active_connections[account_id]:
                del self.active_connections[account_id]

    async def broadcast_to_account(self, account_id: uuid.UUID, event_type: str, data: Any):
        """
        Broadcast a JSON payload to all active websockets belonging to a specific account.
        """
        if account_id in self.active_connections:
            payload = json.dumps({"type": event_type, "payload": data})
            # Iterate over a copy to safely handle disconnections mid-broadcast
            for connection in list(self.active_connections[account_id]):
                try:
                    await connection.send_text(payload)
                except Exception:
                    # Ignore failed sends (e.g. disconnected client not yet cleaned up)
                    self.disconnect(connection, account_id)

manager = ConnectionManager()

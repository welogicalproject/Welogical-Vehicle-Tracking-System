import logging
import asyncio
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger("vts.websocket")

class WebSocketManager:
    """
    Manages active WebSocket connections, processes subscription requests,
    performs periodic ping heartbeats, and dispatches real-time broadcast payloads.
    """
    def __init__(self):
        # Maps active WebSocket instances to their set of subscribed topics
        self.active_connections: Dict[WebSocket, Set[str]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """
        Accepts a new WebSocket connection and registers it in the connection pool.
        """
        await websocket.accept()
        async with self.lock:
            self.active_connections[websocket] = set()
        logger.info(f"[WebSocket] Connected. Active client count: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """
        Removes a disconnected WebSocket connection from the connection pool.
        """
        async with self.lock:
            if websocket in self.active_connections:
                del self.active_connections[websocket]
        logger.info(f"[WebSocket] Disconnected. Active client count: {len(self.active_connections)}")

    async def subscribe(self, websocket: WebSocket, topic: str):
        """
        Subscribes a client connection to a specific topic channel.
        """
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections[websocket].add(topic)
                logger.info(f"[WebSocket] Subscribed connection to topic '{topic}'.")

    async def unsubscribe(self, websocket: WebSocket, topic: str):
        """
        Unsubscribes a client connection from a specific topic channel.
        """
        async with self.lock:
            if websocket in self.active_connections and topic in self.active_connections[websocket]:
                self.active_connections[websocket].remove(topic)
                logger.info(f"[WebSocket] Unsubscribed connection from topic '{topic}'.")

    async def broadcast(self, topic: str, data: dict):
        """
        Broadcasts a JSON payload to all active connections subscribed to the topic.
        Supports wildcard matching for the 'fleet' operational topic.
        """
        async with self.lock:
            targets = []
            for ws, topics in self.active_connections.items():
                # Direct match, wildcard matching or fleet broad scope matching
                if topic in topics or "fleet" in topics or "*" in topics:
                    targets.append(ws)

            if not targets:
                return

            payload = {
                "topic": topic,
                "data": data
            }

            # Gather broadcast tasks concurrently
            tasks = [ws.send_json(payload) for ws in targets]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for res, ws in zip(results, targets):
                if isinstance(res, Exception):
                    logger.warning(f"[WebSocket] Broadcast delivery failure to client: {res}")

    async def run_heartbeat_loop(self):
        """
        Asynchronous loop periodically checking connection health by sending ping packets.
        """
        while True:
            try:
                await asyncio.sleep(30)
                async with self.lock:
                    dead_clients = []
                    for ws in list(self.active_connections.keys()):
                        try:
                            # Send standard ping heartbeat
                            await ws.send_json({"type": "ping"})
                        except Exception:
                            dead_clients.append(ws)
                    
                    for ws in dead_clients:
                        if ws in self.active_connections:
                            del self.active_connections[ws]
                            logger.info("[WebSocket] Cleaned up stale offline connection.")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[WebSocket] Heartbeat loop encountered error: {e}", exc_info=True)

# Singleton manager instance
ws_manager = WebSocketManager()

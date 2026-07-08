import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import ws_manager

router = APIRouter(tags=["Real-time"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint handling incoming connections, topic registrations,
    and disconnection cleanup.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Process command messages from connected client
            message = await websocket.receive_text()
            message = message.strip()
            
            # Parse command actions, e.g. "subscribe telemetry"
            parts = message.split(maxsplit=1)
            if len(parts) == 2:
                command, topic = parts[0].lower(), parts[1]
                if command == "subscribe":
                    await ws_manager.subscribe(websocket, topic)
                    await websocket.send_json({
                        "status": "success", 
                        "message": f"Subscribed to channel '{topic}'."
                    })
                elif command == "unsubscribe":
                    await ws_manager.unsubscribe(websocket, topic)
                    await websocket.send_json({
                        "status": "success", 
                        "message": f"Unsubscribed from channel '{topic}'."
                    })
                else:
                    await websocket.send_json({
                        "status": "error", 
                        "message": f"Invalid command '{command}'. Expected: subscribe / unsubscribe"
                    })
            else:
                # Handle direct JSON pongs or bad formatted texts
                if message.lower() == "pong":
                    continue
                await websocket.send_json({
                    "status": "error", 
                    "message": "Malformed message. Expected format: subscribe/unsubscribe <topic>"
                })
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        await ws_manager.disconnect(websocket)

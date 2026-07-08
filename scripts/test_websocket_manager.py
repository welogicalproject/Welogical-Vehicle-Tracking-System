import os
import sys
import asyncio
from unittest.mock import AsyncMock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.services.websocket_manager import ws_manager

async def test_websocket_broadcasts():
    print("======================================================================")
    print("                 VTS WEBSOCKET MANAGER UNIT TESTS                     ")
    print("======================================================================")

    # 1. Mock WebSocket client instances
    ws1 = AsyncMock()
    ws2 = AsyncMock()

    # 2. Register mock connections
    await ws_manager.connect(ws1)
    await ws_manager.connect(ws2)
    assert len(ws_manager.active_connections) == 2
    print("[PASS] Successfully registered mock connections.")

    # 3. Handle subscriptions
    await ws_manager.subscribe(ws1, "telemetry")
    await ws_manager.subscribe(ws2, "notifications")
    
    # 4. Perform broadcast
    telemetry_data = {"lat": 12.97, "lon": 77.59}
    await ws_manager.broadcast("telemetry", telemetry_data)
    
    # Verify ws1 (subscribed to telemetry) received it, but ws2 did not
    ws1.send_json.assert_called_once_with({"topic": "telemetry", "data": telemetry_data})
    ws2.send_json.assert_not_called()
    print("[PASS] Topic-specific channel routing is verified.")

    # 5. Test Disconnect
    await ws_manager.disconnect(ws1)
    assert len(ws_manager.active_connections) == 1
    print("[PASS] Successfully handled disconnection cleanup.")

    print("\n======================================================================")
    print("                 WEBSOCKET MANAGER TESTS PASSED                       ")
    print("======================================================================")

if __name__ == "__main__":
    asyncio.run(test_websocket_broadcasts())

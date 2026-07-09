from typing import Dict, Any, Protocol, runtime_checkable
from datetime import datetime

@runtime_checkable
class IVehicleTwin(Protocol):
    """
    Protocol describing a simulated vehicle digital twin in VTS.
    Allows coexistence with real physical tracking devices under a common interface.
    """
    device_uid: str
    is_running: bool
    last_tick_time: datetime
    uptime_seconds: float

    async def start(self) -> None:
        """Starts the twin's async simulation loop."""
        ...

    async def stop(self) -> None:
        """Gracefully stops the twin's async simulation loop."""
        ...

    def get_status(self) -> Dict[str, Any]:
        """Returns the current runtime diagnostic state of this twin."""
        ...

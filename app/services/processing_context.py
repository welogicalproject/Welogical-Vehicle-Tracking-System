from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.vehicle import Vehicle

@dataclass
class TelemetryProcessingContext:
    session: AsyncSession
    vehicle_id: int
    device_uid: str
    packet_data: Dict[str, Any]
    timestamp: datetime
    msgid: Optional[int] = None
    processing_start_time: float = field(default_factory=datetime.utcnow().timestamp) # placeholder or time.perf_counter()
    packet_latency: float = 0.0 # seconds
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

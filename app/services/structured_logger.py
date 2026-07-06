import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("app.telemetry")

def log_telemetry_stage(
    device_uid: str,
    vehicle_id: Optional[int],
    msgid: Optional[int],
    processing_stage: str,
    start_time: float,
    status: str,
    extra: Optional[Dict[str, Any]] = None,
    exception: Optional[Exception] = None
):
    """
    Structured logger for the telemetry ingestion pipeline.
    Calculates execution duration and logs metadata consistently.
    """
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    
    log_data = {
        "device_uid": device_uid,
        "vehicle_id": vehicle_id,
        "msgid": msgid,
        "stage": processing_stage,
        "elapsed_ms": round(elapsed_ms, 2),
        "status": status,
    }
    
    if extra:
        log_data.update(extra)
        
    log_msg = (
        f"[Telemetry] UID={device_uid} | Vehicle={vehicle_id} | MsgID={msgid} | "
        f"Stage={processing_stage} | Duration={elapsed_ms:.2f}ms | Status={status}"
    )

    if exception:
        log_data["error"] = str(exception)
        logger.error(f"{log_msg} | Error: {exception}", exc_info=True)
    elif status == "FAILED" or status == "REJECTED":
        logger.warning(log_msg)
    else:
        logger.info(log_msg)

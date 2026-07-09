from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.services.simulator.simulator_service import simulator_service

router = APIRouter(prefix="/simulator", tags=["Simulator"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class TwinStatusResponse(BaseModel):
    vehicle_uid: str
    vehicle_name: Optional[str] = None
    vehicle_type: Optional[str] = None
    db_vehicle_id: Optional[int] = None
    running: bool
    task_alive: bool = True
    task_id: Optional[str] = None
    last_tick: Optional[str] = None
    uptime: float
    packets_sent: int = 0
    packets_per_second: float = 0.0
    commands_processed: int = 0
    error_count: int = 0
    avg_pipeline_latency_ms: float = 0.0
    avg_db_latency_ms: float = 0.0


class ServiceStatusResponse(BaseModel):
    status: str
    twins: List[TwinStatusResponse]


class ServiceMetricsResponse(BaseModel):
    service_running: bool
    uptime_seconds: float
    twins_total: int
    twins_running: int
    packets_sent: int
    packets_per_second: float
    commands_processed: int
    error_count: int
    average_pipeline_latency_ms: float
    average_db_latency_ms: float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status", response_model=ServiceStatusResponse, summary="Simulator service status")
async def get_simulator_status():
    """
    Returns the running state of the SimulatorService and a brief status
    summary for every managed VehicleTwin.
    """
    twins_status = simulator_service.status()
    return {
        "status": "active" if simulator_service.is_running else "inactive",
        "twins": twins_status,
    }


@router.get("/twins", response_model=List[TwinStatusResponse], summary="All twin details")
async def get_simulator_twins():
    """
    Returns the full status detail for every managed VehicleTwin,
    including DB vehicle ID, uptime, packet counters, and latency metrics.
    """
    return simulator_service.status()


@router.get("/metrics", response_model=ServiceMetricsResponse, summary="Fleet-level simulator metrics")
async def get_simulator_metrics():
    """
    Returns aggregated fleet-level metrics: total packets sent, PPS, average
    pipeline and DB latencies, error counts, and service uptime.
    """
    return simulator_service.metrics()


@router.post("/start", summary="Start simulator or a specific twin")
async def start_simulator(device_uid: Optional[str] = None):
    """
    Start the entire SimulatorService, or pass ?device_uid= to start a single twin.
    """
    if device_uid:
        if device_uid not in simulator_service.twins:
            raise HTTPException(status_code=404, detail=f"Twin {device_uid} not found")
        await simulator_service.twins[device_uid].start()
        return {"status": "success", "message": f"Started twin {device_uid}"}
    await simulator_service.start()
    return {"status": "success", "message": "Simulator service started"}


@router.post("/stop", summary="Stop simulator or a specific twin")
async def stop_simulator(device_uid: Optional[str] = None):
    """
    Stop the entire SimulatorService, or pass ?device_uid= to stop a single twin.
    """
    if device_uid:
        if device_uid not in simulator_service.twins:
            raise HTTPException(status_code=404, detail=f"Twin {device_uid} not found")
        await simulator_service.twins[device_uid].stop()
        return {"status": "success", "message": f"Stopped twin {device_uid}"}
    await simulator_service.stop()
    return {"status": "success", "message": "Simulator service stopped"}


@router.post("/restart", summary="Restart simulator or a specific twin")
async def restart_simulator(device_uid: Optional[str] = None):
    """
    Restart the entire SimulatorService, or pass ?device_uid= to restart a single twin.
    """
    if device_uid and device_uid not in simulator_service.twins:
        raise HTTPException(status_code=404, detail=f"Twin {device_uid} not found")
    await simulator_service.restart(device_uid)
    return {
        "status": "success",
        "message": f"Restarted {device_uid if device_uid else 'all twins'}",
    }


class UpdateRouteRequest(BaseModel):
    device_uid: str
    coordinates: List[List[float]]


@router.post("/update-route", summary="Dynamically assign a custom trip path to a running twin")
async def update_twin_route(payload: UpdateRouteRequest):
    """
    Assigns a custom road-snapped geometry path to the specified twin dynamically.
    The twin resets its GPS/Motion status to begin driving along this new path immediately.
    """
    device_uid = payload.device_uid
    if device_uid not in simulator_service.twins:
        raise HTTPException(status_code=404, detail=f"VehicleTwin {device_uid} not found")
    
    # Convert lists of floats [lat, lon] to list of tuples
    route_coords = [(c[0], c[1]) for c in payload.coordinates]
    
    try:
        simulator_service.twins[device_uid].set_custom_route(route_coords)
        return {
            "status": "success",
            "message": f"Assigned new custom route of {len(route_coords)} points to twin {device_uid}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

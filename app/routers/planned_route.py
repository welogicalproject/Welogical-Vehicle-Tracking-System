from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.planned_route import (
    PlannedRouteCreate,
    PlannedRouteResponse,
    VehicleRouteAssignmentResponse,
    PlannedRouteStatusUpdate,
)
from app.crud.planned_route import (
    create_route,
    get_route,
    get_all_routes,
    assign_route_to_vehicle,
    get_assigned_route,
    update_route_status,
)
from app.exceptions import EntityNotFoundError
from pydantic import BaseModel, Field

router = APIRouter(tags=["Planned Routes"])


class RouteAssignmentRequest(BaseModel):
    route_id: int = Field(..., description="The ID of the planned route to assign")


@router.post("/routes", response_model=PlannedRouteResponse, status_code=status.HTTP_201_CREATED)
async def create_new_planned_route(route_in: PlannedRouteCreate, db: AsyncSession = Depends(get_db)):
    """Create a new planned route with ordered coordinates."""
    return await create_route(db, route_in)


@router.get("/routes", response_model=List[PlannedRouteResponse])
async def list_planned_routes(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Retrieve a list of all planned routes."""
    return await get_all_routes(db, skip=skip, limit=limit)


@router.get("/routes/{route_id}", response_model=PlannedRouteResponse)
async def get_planned_route_by_id(route_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve complete details of a planned route including points."""
    route = await get_route(db, route_id)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Planned route with ID {route_id} not found",
        )
    return route


@router.get("/vehicles/{vehicle_id}/assigned-route", response_model=PlannedRouteResponse)
async def get_vehicle_assigned_route(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve the active assigned planned route for a vehicle."""
    route = await get_assigned_route(db, vehicle_id)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active route assignment found for vehicle ID {vehicle_id}",
        )
    return route


@router.post("/vehicles/{vehicle_id}/assign-route", response_model=VehicleRouteAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_planned_route(
    vehicle_id: int,
    payload: RouteAssignmentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Assign a planned route to a vehicle, replacing any currently active route assignment."""
    try:
        assignment = await assign_route_to_vehicle(db, vehicle_id, payload.route_id)

        # Notify simulator twin and broadcast WS event
        try:
            from app.models.vehicle import Vehicle
            from app.services.simulator.simulator_service import simulator_service
            from app.services.websocket_manager import ws_manager
            from sqlalchemy import select

            stmt = select(Vehicle).where(Vehicle.id == vehicle_id)
            res = await db.execute(stmt)
            veh = res.scalars().first()
            if veh and veh.device_uid in simulator_service.twins:
                twin = simulator_service.twins[veh.device_uid]
                await twin.load_assigned_route()

            # Broadcast assignment event
            await ws_manager.broadcast("vehicles", {
                "event": "route_assigned",
                "vehicle_id": vehicle_id,
                "route_id": payload.route_id
            })
        except Exception as sim_err:
            pass

        return assignment
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/routes/{route_id}/status", response_model=PlannedRouteResponse)
async def patch_planned_route_status(
    route_id: int,
    payload: PlannedRouteStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update the status of a planned route (Pending, Assigned, Running, Completed) with valid transitions."""
    try:
        return await update_route_status(db, route_id, payload.status)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


from app.schemas.planned_route import RouteProgressUpdate
from app.models.planned_route import VehicleRouteAssignment
from datetime import datetime, timezone

@router.patch("/vehicles/{vehicle_id}/route-progress", response_model=VehicleRouteAssignmentResponse)
async def patch_vehicle_route_progress(
    vehicle_id: int,
    payload: RouteProgressUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update progress tracking fields on the active route assignment for a vehicle."""
    from sqlalchemy import select
    stmt = (
        select(VehicleRouteAssignment)
        .where(VehicleRouteAssignment.vehicle_id == vehicle_id, VehicleRouteAssignment.is_active == True)
    )
    result = await db.execute(stmt)
    assignment = result.scalars().first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active route assignment found for vehicle ID {vehicle_id}"
        )
    
    assignment.current_point_index = payload.current_point_index
    assignment.progress_percentage = payload.progress_percentage
    assignment.last_coordinate_index = payload.last_coordinate_index
    assignment.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    
    await db.commit()
    await db.refresh(assignment)
    return assignment


from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.planned_route import PlannedRoute, PlannedRoutePoint, VehicleRouteAssignment
from app.schemas.planned_route import PlannedRouteCreate
from app.exceptions import EntityNotFoundError, DuplicateEntityError


async def create_route(db: AsyncSession, route_in: PlannedRouteCreate) -> PlannedRoute:
    # Create the PlannedRoute record
    db_route = PlannedRoute(
        name=route_in.name,
        start_location=route_in.start_location,
        destination=route_in.destination,
        distance=route_in.distance,
        estimated_duration=route_in.estimated_duration,
        status="Pending",
    )
    db.add(db_route)
    await db.flush()  # Flush to get the auto-generated route ID

    # Create the PlannedRoutePoint records
    for pt in route_in.points:
        db_point = PlannedRoutePoint(
            route_id=db_route.id,
            sequence_number=pt.sequence_number,
            latitude=pt.latitude,
            longitude=pt.longitude,
        )
        db.add(db_point)

    await db.commit()
    # Refresh to load relationships and points
    result = await db.execute(
        select(PlannedRoute)
        .options(selectinload(PlannedRoute.points))
        .where(PlannedRoute.id == db_route.id)
    )
    return result.scalars().first()


async def get_route(db: AsyncSession, route_id: int) -> Optional[PlannedRoute]:
    result = await db.execute(
        select(PlannedRoute)
        .options(selectinload(PlannedRoute.points))
        .where(PlannedRoute.id == route_id)
    )
    return result.scalars().first()


async def get_all_routes(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PlannedRoute]:
    result = await db.execute(
        select(PlannedRoute)
        .options(selectinload(PlannedRoute.points))
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def assign_route_to_vehicle(db: AsyncSession, vehicle_id: int, route_id: int) -> VehicleRouteAssignment:
    # Verify that the route exists
    result_route = await db.execute(select(PlannedRoute).where(PlannedRoute.id == route_id))
    route = result_route.scalars().first()
    if not route:
        raise EntityNotFoundError(f"PlannedRoute with ID {route_id} not found")

    # Set all other assignments for this vehicle to inactive
    await db.execute(
        update(VehicleRouteAssignment)
        .where(VehicleRouteAssignment.vehicle_id == vehicle_id)
        .values(is_active=False)
    )

    # Create the new assignment
    db_assignment = VehicleRouteAssignment(
        vehicle_id=vehicle_id,
        route_id=route_id,
        is_active=True,
    )
    db.add(db_assignment)

    # Update the route status to "Assigned"
    route.status = "Assigned"
    await db.commit()
    await db.refresh(db_assignment)
    return db_assignment


async def get_assigned_route(db: AsyncSession, vehicle_id: int) -> Optional[PlannedRoute]:
    # Query the active assignment for the vehicle
    stmt = (
        select(VehicleRouteAssignment)
        .where(VehicleRouteAssignment.vehicle_id == vehicle_id, VehicleRouteAssignment.is_active == True)
    )
    result = await db.execute(stmt)
    assignment = result.scalars().first()

    if not assignment:
        return None

    # Retrieve the full route details
    return await get_route(db, assignment.route_id)


async def update_route_status(db: AsyncSession, route_id: int, status: str) -> PlannedRoute:
    result = await db.execute(
        select(PlannedRoute)
        .options(selectinload(PlannedRoute.points))
        .where(PlannedRoute.id == route_id)
    )
    route = result.scalars().first()
    if not route:
        raise EntityNotFoundError(f"PlannedRoute with ID {route_id} not found")

    # Validate state transitions
    valid_transitions = {
        "Pending": ["Assigned"],
        "Assigned": ["Running", "Pending"],
        "Running": ["Completed", "Assigned"],
        "Completed": [],
    }
    
    current_status = route.status
    if status not in ["Pending", "Assigned", "Running", "Completed"]:
        raise ValueError(f"Invalid status '{status}'. Valid statuses: Pending, Assigned, Running, Completed")

    # If the transition is invalid, raise ValueError
    if current_status != status and status not in valid_transitions.get(current_status, []):
        raise ValueError(f"Invalid transition from '{current_status}' to '{status}'")

    route.status = status
    await db.commit()
    await db.refresh(route)
    return route

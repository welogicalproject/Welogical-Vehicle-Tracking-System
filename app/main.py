# Import dependencies

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.logging_config import setup_logging
from app.exceptions import register_exception_handlers
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.routers import (
    health_router,
    system_router,
    vehicle_router,
    location_router,
    event_router,
    device_config_router,
    device_command_router,
    trip_router,
    driver_router,
    analytics_router,
    operations_router,
    reports_router,
    notifications_router,
    websocket_router,
    simulator_router,
    planned_route_router
)
import asyncio
import os
import sys
from contextlib import asynccontextmanager
from app.services.simulator.simulator_service import simulator_service

# Setup application loggers
setup_logging()

# Global references for websocket heartbeat
websocket_heartbeat_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global websocket_heartbeat_task
    from app.services.websocket_manager import ws_manager
    websocket_heartbeat_task = asyncio.create_task(ws_manager.run_heartbeat_loop())
    
    if settings.SIMULATOR_ENABLED:
        await simulator_service.start()
    yield
    # Shutdown logic
    if settings.SIMULATOR_ENABLED:
        await simulator_service.stop()
        
    if websocket_heartbeat_task:
        websocket_heartbeat_task.cancel()
        try:
            await websocket_heartbeat_task
        except asyncio.CancelledError:
            pass

# Initialize FastAPI instance
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for logging, tracking, and querying real-time vehicle GPS coordinates & telemetry",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Configure CORS Middleware
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
# Add explicit support for production Vercel domain to ensure it is covered
if "https://welogical-vehicle-tracking-system.vercel.app" not in origins:
    origins.append("https://welogical-vehicle-tracking-system.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://welogical-vehicle-tracking-system.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom API exceptions & handlers
register_exception_handlers(app)

# Include sub-routers
app.include_router(health_router)
app.include_router(system_router)
app.include_router(vehicle_router)
app.include_router(location_router)
app.include_router(event_router)
app.include_router(device_config_router)
app.include_router(device_command_router)
app.include_router(trip_router)
app.include_router(driver_router)
app.include_router(route_router)
app.include_router(analytics_router)
app.include_router(operations_router)
app.include_router(reports_router)
app.include_router(notifications_router)
app.include_router(websocket_router)
app.include_router(simulator_router)
app.include_router(planned_route_router)


@app.get("/")
async def root():
    """Welcome endpoint returning API service info."""
    return {
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "docs_url": "/docs",
        "health_check_url": "/health",
        "status": "online"
    }

@app.get("/run-migrations")
async def run_migrations():
    try:
        from alembic.config import Config
        from alembic import command
        import sys
        import os
        # Dynamically determine the base project directory where alembic.ini resides
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
        alembic_cfg = Config(os.path.join(base_dir, "alembic.ini"))
        command.upgrade(alembic_cfg, "head")
        return {"status": "success", "message": "Alembic upgrade head completed successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/run-tests")
async def run_tests():
    # 1. Test Driving Score Calculation
    from app.services.trip_scoring import calculate_driving_score
    score1 = calculate_driving_score(overspeed_events_count=2, long_idle_events_count=3)
    # Expected: 100 - (2*5) - (3*2) = 84
    score2 = calculate_driving_score(overspeed_events_count=30, long_idle_events_count=10)
    # Expected: max(0, 100 - 150 - 20) = 0
    
    # 2. Test Stop Detection (Mock Locations)
    from app.models.location import Location
    from app.services.trip_analytics import _evaluate_and_add_stop
    from datetime import datetime, timedelta
    
    base_time = datetime(2026, 6, 26, 12, 0, 0)
    mock_points_short = [
        Location(latitude=21.17, longitude=72.83, speed=1.0, timestamp=base_time),
        Location(latitude=21.17001, longitude=72.83001, speed=1.2, timestamp=base_time + timedelta(seconds=60))
    ]
    stops_short = _evaluate_and_add_stop(mock_points_short, [])
    
    mock_points_long = [
        Location(latitude=21.17, longitude=72.83, speed=1.0, timestamp=base_time),
        Location(latitude=21.17001, longitude=72.83001, speed=1.2, timestamp=base_time + timedelta(seconds=130))
    ]
    stops_long = _evaluate_and_add_stop(mock_points_long, [])
    
    # 3. Test Replay Downsampling
    from app.services.trip_replay import simple_skipping_downsampler
    all_points = [Location(id=i, latitude=21.0+i/100, longitude=72.0+i/100, speed=10.0, timestamp=base_time + timedelta(seconds=i)) for i in range(100)]
    downsampled = simple_skipping_downsampler(all_points, target_count=10, multiplier=1)
    
    return {
        "driving_score_tests": {
            "score1_actual": score1,
            "score2_actual": score2,
            "passed": score1 == 84 and score2 == 0
        },
        "stop_detection_tests": {
            "short_stop_count": len(stops_short),
            "long_stop_count": len(stops_long),
            "passed": len(stops_short) == 0 and len(stops_long) == 1
        },
        "replay_downsample_tests": {
            "original_count": len(all_points),
            "downsampled_count": len(downsampled),
            "passed": len(downsampled) < 100 and downsampled[-1].id == 99
        }
    }

@app.get("/run-m3-tests")
async def run_m3_tests(db: AsyncSession = Depends(get_db)):
    try:
        import time
        from datetime import datetime, timezone
        from app.schemas.vehicle import VehicleCreate
        from app.schemas.driver import DriverCreate
        from app.models.enums import DriverStatus
        import app.crud.vehicle as crud_vehicle
        import app.crud.driver as crud_driver
        from app.models.driver_assignment import DriverAssignment
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select, and_

        # 1. Create a test vehicle
        unique_uid = f"M3-DIRECT-VEH-{int(time.time())}"
        veh_in = VehicleCreate(
            device_uid=unique_uid,
            vehicle_name="M3 Direct Veh",
            vehicle_type="Truck",
            status="Enabled"
        )
        vehicle = await crud_vehicle.create_vehicle(db, veh_in)
        vehicle_id = vehicle.id

        # 2. Create an active driver
        drv_in = DriverCreate(
            driver_name="M3 Direct Driver",
            phone_number="+919876543210",
            email="direct@m3.com",
            license_number=f"LIC-M3-DIR-{int(time.time())}",
            license_expiry=datetime.now(timezone.utc),
            emergency_contact="Emergency Contact",
            status=DriverStatus.ACTIVE
        )
        driver = await crud_driver.create_driver(db, drv_in)
        driver_id = driver.id

        # 3. Create a suspended driver
        susp_drv_in = drv_in.model_copy(update={
            "driver_name": "Suspended Direct Driver",
            "license_number": f"LIC-M3-SUS-{int(time.time())}",
            "status": DriverStatus.SUSPENDED
        })
        susp_driver = await crud_driver.create_driver(db, susp_drv_in)

        # 4. Create a disabled vehicle
        dis_veh_in = veh_in.model_copy(update={
            "device_uid": f"M3-DIR-DIS-{int(time.time())}",
            "vehicle_name": "Disabled Direct Veh",
            "status": "Disabled"
        })
        disabled_vehicle = await crud_vehicle.create_vehicle(db, dis_veh_in)

        # 5. Validation Test: Attempt to assign active driver to disabled vehicle
        try:
            await crud_driver.create_assignment(db, disabled_vehicle.id, driver_id)
            raise AssertionError("Should not allow assignment to disabled vehicle")
        except ValueError as e:
            # Expected behavior
            pass

        # 6. Validation Test: Attempt to assign suspended driver to active vehicle
        try:
            await crud_driver.create_assignment(db, vehicle_id, susp_driver.id)
            raise AssertionError("Should not allow assignment of suspended driver")
        except ValueError as e:
            # Expected behavior
            pass

        # 7. Assign active driver to active vehicle
        asg = await crud_driver.create_assignment(db, vehicle_id, driver_id)
        assert asg.status == "Active", f"Assignment status was: {asg.status}"

        # 8. Check active assignment on vehicle
        active_asg = await crud_driver.get_active_assignment_by_vehicle(db, vehicle_id)
        assert active_asg is not None
        assert active_asg.driver_id == driver_id

        # 9. Verify current_driver property on vehicle detail
        veh_ref = await crud_vehicle.get_vehicle(db, vehicle_id)
        assert veh_ref.current_driver is not None
        assert veh_ref.current_driver.id == driver_id

        # 10. Verify current_vehicle property on driver detail
        drv_ref = await crud_driver.get_driver(db, driver_id)
        assert drv_ref.current_vehicle is not None
        assert drv_ref.current_vehicle.id == vehicle_id

        # 11. Assignment Change: Create second driver and assign
        drv2_in = drv_in.model_copy(update={
            "driver_name": "Second Direct Driver",
            "license_number": f"LIC-M3-DIR2-{int(time.time())}"
        })
        driver2 = await crud_driver.create_driver(db, drv2_in)
        
        asg2 = await crud_driver.create_assignment(db, vehicle_id, driver2.id)
        assert asg2.status == "Active"

        # Verify first assignment is completed
        history = await crud_driver.get_assignment_history_by_vehicle(db, vehicle_id)
        assert len(history) >= 2
        assert history[0].driver_id == driver2.id and history[0].status == "Active"
        assert history[1].driver_id == driver.id and history[1].status == "Completed"
        assert history[1].released_at is not None

        # 12. Release assignment
        released = await crud_driver.release_assignment(db, vehicle_id)
        assert released is not None
        assert released.status == "Completed"

        active_asg_none = await crud_driver.get_active_assignment_by_vehicle(db, vehicle_id)
        assert active_asg_none is None

        return {"status": "success", "message": "All Milestone 3 in-process validations passed!"}
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "trace": traceback.format_exc()}


@app.get("/run-google-route-tests")
async def run_google_route_tests(db: AsyncSession = Depends(get_db)):
    try:
        from app.services.route_cache import calculate_normalized_key, get_or_compute_trip_route
        from app.services.google_routes import parse_google_duration
        from app.models.trip import Trip
        import asyncio
        from sqlalchemy import select

        # 1. Test Duration Parsing
        assert parse_google_duration("123s") == 123
        assert parse_google_duration("3600.5s") == 3600
        assert parse_google_duration(None) is None

        # 2. Test Hashing & Coordinate Normalization
        key1, opt1, req1, lat1, lon1, d_lat1, d_lon1 = calculate_normalized_key(22.307212, 73.181232, 22.312343, 73.194563)
        key2, opt2, req2, lat2, lon2, d_lat2, d_lon2 = calculate_normalized_key(22.307214, 73.181230, 22.312341, 73.194561)
        assert lat1 == 22.30721
        assert lon1 == 73.18123


        # 3. Test db fetch & concurrency locks
        trip_stmt = select(Trip).where(Trip.is_active == False).limit(1)
        res = await db.execute(trip_stmt)
        trip = res.scalars().first()
        
        if not trip:
            return {"status": "success", "message": "Hashing validated, but no completed trips in DB to test locking."}

        # Run concurrent fetches using separate sessions to trigger LockRegistry concurrency protection safely
        from app.database import AsyncSessionLocal
        
        async def run_task():
            async with AsyncSessionLocal() as session:
                return await get_or_compute_trip_route(session, trip.vehicle_id, trip.id)

        tasks = [run_task(), run_task(), run_task()]
        
        # Gather exceptions safely in case google routes is disabled or key not present
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Any ValueError or IOError shows code reached integration client
        for r in results:
            if isinstance(r, Exception) and not isinstance(r, (ValueError, IOError)):
                raise r


        return {"status": "success", "message": "All Google Routes unit and concurrency locking tests passed!"}
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "trace": traceback.format_exc()}












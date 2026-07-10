from app.routers.health import router as health_router, system_router
from app.routers.vehicle import router as vehicle_router
from app.routers.location import router as location_router
from app.routers.event import router as event_router
from app.routers.device_config import router as device_config_router
from app.routers.device_command import router as device_command_router
from app.routers.trip import router as trip_router
from app.routers.driver import router as driver_router
from app.routers.route import router as route_router
from app.routers.analytics import router as analytics_router
from app.routers.operations import router as operations_router
from app.routers.reports import router as reports_router
from app.routers.notifications import router as notifications_router
from app.routers.websocket import router as websocket_router
from app.routers.simulator import router as simulator_router
from app.routers.planned_route import router as planned_route_router

__all__ = [
    "health_router",
    "system_router",
    "vehicle_router",
    "location_router",
    "event_router",
    "device_config_router",
    "device_command_router",
    "trip_router",
    "driver_router",
    "route_router",
    "analytics_router",
    "operations_router",
    "reports_router",
    "notifications_router",
    "websocket_router",
    "simulator_router",
    "planned_route_router",
]

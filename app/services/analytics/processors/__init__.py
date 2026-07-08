from app.services.analytics.processors.vehicle_stats import VehicleStatsProcessor
from app.services.analytics.processors.driver_stats import DriverStatsProcessor
from app.services.analytics.processors.maintenance import MaintenanceProcessor
from app.services.analytics.processors.fleet_stats import FleetStatsProcessor
from app.services.analytics.processors.fleet_ops import FleetOperationsProcessor

__all__ = [
    "VehicleStatsProcessor",
    "DriverStatsProcessor",
    "MaintenanceProcessor",
    "FleetStatsProcessor",
    "FleetOperationsProcessor",
]

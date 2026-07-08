from app.services.reports.base import BaseReportBuilder, ReportContext
from app.services.reports.manager import ReportManager
from app.services.reports.builders import (
    DailyFleetReportBuilder,
    VehicleReportBuilder,
    DriverReportBuilder,
    MaintenanceReportBuilder,
    HealthReportBuilder,
    FuelReportBuilder,
    EventReportBuilder,
)

def get_report_manager() -> ReportManager:
    """
    Factory function instantiating a ReportManager pre-registered with all
    standard fleet business intelligence report builders.
    """
    manager = ReportManager()
    manager.register_builder(DailyFleetReportBuilder())
    manager.register_builder(VehicleReportBuilder())
    manager.register_builder(DriverReportBuilder())
    manager.register_builder(MaintenanceReportBuilder())
    manager.register_builder(HealthReportBuilder())
    manager.register_builder(FuelReportBuilder())
    manager.register_builder(EventReportBuilder())
    return manager

__all__ = [
    "BaseReportBuilder",
    "ReportContext",
    "ReportManager",
    "get_report_manager",
]

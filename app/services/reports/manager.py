import logging
from typing import Dict
from app.services.reports.base import BaseReportBuilder, ReportContext

logger = logging.getLogger("vts.reports")

class ReportManager:
    """
    Coordinates and handles execution of registered business intelligence report builders.
    """
    def __init__(self):
        self.builders: Dict[str, BaseReportBuilder] = {}

    def register_builder(self, builder: BaseReportBuilder):
        """
        Registers a report builder to the manager.
        """
        self.builders[builder.name.lower()] = builder
        logger.info(f"Registered report builder '{builder.name}' for report type: '{builder.title}'.")

    def generate_report(self, report_name: str, context: ReportContext) -> dict:
        """
        Executes the matching report builder and returns the structured result payload.
        """
        key = report_name.lower()
        if key not in self.builders:
            raise KeyError(f"Report builder for '{report_name}' is not registered.")
        
        builder = self.builders[key]
        logger.info(f"Generating report: '{builder.title}' (Builder: {builder.name}).")
        return builder.build(context)

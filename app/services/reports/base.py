from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

class ReportContext:
    """
    Context parameters passed to report builders containing date filters,
    target resource identifiers, and active database sessions.
    """
    def __init__(
        self,
        db: Session,
        report_date: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        vehicle_id: Optional[int] = None,
        driver_id: Optional[int] = None
    ):
        self.db = db
        self.date = report_date or date.today()
        self.start_date = start_date or self.date
        self.end_date = end_date or self.date
        self.vehicle_id = vehicle_id
        self.driver_id = driver_id


class BaseReportBuilder:
    """
    Base report builder interface. Every report type implements a custom
    builder to query daily summaries and format structured JSON blocks.
    """
    name: str = "BaseReport"
    title: str = "Base Report Description"

    def build(self, context: ReportContext) -> dict:
        raise NotImplementedError("Report builders must override build().")

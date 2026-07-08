import logging
from datetime import date
from sqlalchemy.orm import Session
from typing import Set, Dict, Any

logger = logging.getLogger("vts.analytics")

class PipelineContext:
    """
    Holds variables and execution markers shared across all pipeline processors.
    """
    def __init__(self, run_date: date, start_id: int, end_id: int):
        self.date = run_date
        self.start_location_id = start_id
        self.end_location_id = end_id
        self.processed_vehicle_ids: Set[int] = set()
        self.metrics_cache: Dict[str, Any] = {}

    def __repr__(self) -> str:
        return (f"<PipelineContext date={self.date} "
                f"range=({self.start_location_id} -> {self.end_location_id}) "
                f"vehicles={len(self.processed_vehicle_ids)}>")


class BaseProcessor:
    """
    Abstract interface for modular analytics processors.
    """
    name: str = "BaseProcessor"
    stage: int = 1  # 1: Independent stats, 2: Derived metrics, 3: Fleet aggregates

    def process(self, context: PipelineContext, db: Session) -> bool:
        """
        Executes calculations. Returns True if calculations committed successfully.
        """
        raise NotImplementedError("Processors must implement process().")

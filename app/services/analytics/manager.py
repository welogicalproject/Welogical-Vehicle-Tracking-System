import logging
from datetime import datetime, date
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.location import Location
from app.models.analytics_checkpoint import AnalyticsCheckpoint
from app.services.analytics.base import BaseProcessor, PipelineContext

logger = logging.getLogger("vts.analytics")

class AnalyticsPipelineManager:
    """
    Coordinates execution of registered analytics processors.
    Manages transaction isolation and advances processing cursor checkpoints.
    """
    def __init__(self, group_name: str = "default_fleet"):
        self.group_name = group_name
        self.processors: List[BaseProcessor] = []

    def register_processor(self, processor: BaseProcessor):
        """
        Registers a processor module to the analytics pipeline chain.
        """
        self.processors.append(processor)
        logger.info(f"Registered analytics processor '{processor.name}' to stage {processor.stage}.")

    def get_checkpoint_cursor(self, db: Session) -> int:
        """
        Retrieves the last processed Location ID checkpoint index for this pipeline.
        """
        checkpoint = db.query(AnalyticsCheckpoint).filter_by(processor_group=self.group_name).first()
        if not checkpoint:
            # Lazy initialize starting at location 0
            checkpoint = AnalyticsCheckpoint(processor_group=self.group_name, last_processed_id=0)
            db.add(checkpoint)
            db.commit()
            return 0
        return checkpoint.last_processed_id

    def update_checkpoint_cursor(self, db: Session, last_id: int):
        """
        Advances the database checkpoint cursor.
        """
        checkpoint = db.query(AnalyticsCheckpoint).filter_by(processor_group=self.group_name).first()
        if checkpoint:
            checkpoint.last_processed_id = last_id
            db.add(checkpoint)
            db.flush()

    def run_pipeline(self, db: Session) -> int:
        """
        Executes processors in order of their stage values for unprocessed locations.
        Rolls back the entire transaction if any processor encounters an error.
        Returns the count of processed locations.
        """
        last_id = self.get_checkpoint_cursor(db)
        
        # Check maximum available ID
        max_id = db.query(func.max(Location.id)).scalar()
        if not max_id or max_id <= last_id:
            logger.debug(f"Pipeline '{self.group_name}' is fully caught up (Last processed ID: {last_id}).")
            return 0

        # Identify starting calendar date from the next unprocessed location
        first_unprocessed = db.query(Location).filter(Location.id > last_id).order_by(Location.id.asc()).first()
        if not first_unprocessed:
            return 0
            
        run_date = first_unprocessed.timestamp.date()
        
        # Bound processing window to the same day to simplify daily aggregates
        end_location = db.query(Location).filter(
            Location.id > last_id,
            func.date(Location.timestamp) == run_date
        ).order_by(Location.id.desc()).first()
        
        if not end_location:
            return 0
            
        end_id = end_location.id
        
        logger.info(f"Starting analytics pipeline '{self.group_name}' for date {run_date} (IDs: {last_id + 1} -> {end_id}).")
        
        context = PipelineContext(run_date=run_date, start_id=last_id + 1, end_id=end_id)
        
        # Sort execution order by Stage Priority
        sorted_processors = sorted(self.processors, key=lambda p: p.stage)
        
        try:
            # Execute processor chain sequentially
            for processor in sorted_processors:
                logger.info(f"Executing Stage {processor.stage} processor: '{processor.name}'...")
                success = processor.process(context, db)
                if not success:
                    raise Exception(f"Processor '{processor.name}' reported failure.")
            
            # Commit cursor update
            self.update_checkpoint_cursor(db, end_id)
            db.commit()
            logger.info(f"Pipeline '{self.group_name}' committed successfully. advanced checkpoint cursor to {end_id}.")
            return (end_id - last_id)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Pipeline '{self.group_name}' failed at stage execution: {str(e)}. Transaction rolled back.", exc_info=True)
            raise e

from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from app.database import Base

class AnalyticsCheckpoint(Base):
    __tablename__ = "analytics_checkpoints"

    processor_group = Column(String(50), primary_key=True, index=True)
    last_processed_id = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AnalyticsCheckpoint group={self.processor_group} last_id={self.last_processed_id}>"

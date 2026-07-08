from datetime import date
from sqlalchemy import Column, Integer, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class DriverDailySummary(Base):
    __tablename__ = "driver_daily_summaries"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    distance_driven_km = Column(Float, default=0.0, nullable=False)
    driving_hours = Column(Float, default=0.0, nullable=False)
    idle_hours = Column(Float, default=0.0, nullable=False)
    engine_hours = Column(Float, default=0.0, nullable=False)
    fuel_used_l = Column(Float, default=0.0, nullable=False)
    avg_fuel_economy_kpl = Column(Float, default=0.0, nullable=False)
    max_speed_kmh = Column(Float, default=0.0, nullable=False)
    avg_speed_kmh = Column(Float, default=0.0, nullable=False)

    overspeed_count = Column(Integer, default=0, nullable=False)
    overspeed_duration_sec = Column(Integer, default=0, nullable=False)
    harsh_braking_count = Column(Integer, default=0, nullable=False)
    harsh_acceleration_count = Column(Integer, default=0, nullable=False)
    sharp_turn_count = Column(Integer, default=0, nullable=False)
    ignition_cycles = Column(Integer, default=0, nullable=False)
    refueling_count = Column(Integer, default=0, nullable=False)

    safety_score = Column(Float, default=100.0, nullable=False)
    eco_score = Column(Float, default=100.0, nullable=False)

    # Relationships
    driver = relationship("Driver")

    def __repr__(self):
        return f"<DriverDailySummary id={self.id} driver_id={self.driver_id} date={self.date} safety_score={self.safety_score}>"

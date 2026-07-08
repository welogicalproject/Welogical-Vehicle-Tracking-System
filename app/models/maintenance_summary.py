from datetime import date
from sqlalchemy import Column, Integer, Float, Date, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class MaintenanceSummary(Base):
    __tablename__ = "maintenance_summaries"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    remaining_service_distance_km = Column(Float, default=10000.0, nullable=False)
    remaining_service_days = Column(Integer, default=365, nullable=False)
    estimated_next_service_date = Column(Date, nullable=True)

    oil_life_pct = Column(Float, default=100.0, nullable=False)
    brake_wear_pct = Column(Float, default=0.0, nullable=False)  # 0% is new, 100% is completely worn out
    tyre_health_pct = Column(Float, default=100.0, nullable=False)
    battery_health_pct = Column(Float, default=100.0, nullable=False)
    cooling_system_health = Column(String, default="Good", nullable=False) # "Good", "Fair", "Critical"
    engine_health_index = Column(Float, default=100.0, nullable=False)
    overall_vehicle_health_score = Column(Float, default=100.0, nullable=False)

    # Relationships
    vehicle = relationship("Vehicle")

    def __repr__(self):
        return f"<MaintenanceSummary id={self.id} vehicle_id={self.vehicle_id} date={self.date} health_score={self.overall_vehicle_health_score}>"

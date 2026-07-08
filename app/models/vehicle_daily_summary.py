from sqlalchemy import Column, Integer, Float, Date, ForeignKey, UniqueConstraint
from app.database import Base

class VehicleDailySummary(Base):
    __tablename__ = "vehicle_daily_summaries"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    distance_gps_km = Column(Float, nullable=False, default=0.0)
    fuel_consumed_liters = Column(Float, nullable=False, default=0.0)
    engine_runtime_hours = Column(Float, nullable=False, default=0.0)
    driving_hours = Column(Float, nullable=False, default=0.0)
    idle_hours = Column(Float, nullable=False, default=0.0)
    max_speed = Column(Float, nullable=False, default=0.0)
    
    # Placeholder columns for future analytic calculations
    fuel_efficiency_l100km = Column(Float, nullable=True)
    co2_emissions_kg = Column(Float, nullable=True)
    utilization_ratio = Column(Float, nullable=True)
    min_voltage = Column(Float, nullable=True)
    avg_driver_score = Column(Float, nullable=True)
    overspeeding_seconds = Column(Float, nullable=True)
    harsh_brake_count = Column(Integer, nullable=True)
    harsh_accel_count = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint("vehicle_id", "date", name="uq_vehicle_daily_summary"),
    )

    def __repr__(self):
        return f"<VehicleDailySummary vehicle_id={self.vehicle_id} date={self.date} dist={self.distance_gps_km}>"

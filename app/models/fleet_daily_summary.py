from sqlalchemy import Column, Integer, Float, Date, UniqueConstraint
from app.database import Base

class FleetDailySummary(Base):
    __tablename__ = "fleet_daily_summaries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    
    total_distance_km = Column(Float, nullable=False, default=0.0)
    total_fuel_consumed_l = Column(Float, nullable=False, default=0.0)
    total_engine_hours = Column(Float, nullable=False, default=0.0)
    total_driving_hours = Column(Float, nullable=False, default=0.0)
    total_idle_hours = Column(Float, nullable=False, default=0.0)
    active_vehicles = Column(Integer, nullable=False, default=0)
    fleet_max_speed = Column(Float, nullable=False, default=0.0)
    
    # Placeholder fields for future analytics
    avg_fuel_efficiency = Column(Float, nullable=True)
    total_co2_emissions = Column(Float, nullable=True)
    avg_driver_score = Column(Float, nullable=True)

    def __repr__(self):
        return f"<FleetDailySummary date={self.date} active_vehicles={self.active_vehicles} dist={self.total_distance_km}>"

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class VehicleOperations(Base):
    __tablename__ = "vehicle_operations"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    status = Column(String, default="Offline", nullable=False) # "Driving", "Idling", "Parked", "Offline"
    gps_lost = Column(Boolean, default=False, nullable=False)
    low_fuel = Column(Boolean, default=False, nullable=False)
    low_battery = Column(Boolean, default=False, nullable=False)
    maintenance_due = Column(Boolean, default=False, nullable=False)
    power_failure = Column(Boolean, default=False, nullable=False)
    engine_overheat = Column(Boolean, default=False, nullable=False)
    
    active_trip_id = Column(Integer, nullable=True)
    current_driver_name = Column(String, nullable=True)
    current_health_score = Column(Float, default=100.0, nullable=False)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    # Relationships
    vehicle = relationship("Vehicle")

    def __repr__(self):
        return f"<VehicleOperations vehicle_id={self.vehicle_id} status={self.status}>"


class FleetOperationsLive(Base):
    """
    Holds a single row representing the overall, real-time fleet operations summary KPI state.
    """
    __tablename__ = "fleet_operations_live"

    id = Column(Integer, primary_key=True, index=True)
    vehicles_driving = Column(Integer, default=0, nullable=False)
    vehicles_idling = Column(Integer, default=0, nullable=False)
    vehicles_parked = Column(Integer, default=0, nullable=False)
    vehicles_offline = Column(Integer, default=0, nullable=False)
    
    active_trips = Column(Integer, default=0, nullable=False)
    fleet_availability_pct = Column(Float, default=100.0, nullable=False)
    fleet_utilization_pct = Column(Float, default=0.0, nullable=False)
    vehicles_requiring_attention = Column(Integer, default=0, nullable=False)
    critical_alerts_count = Column(Integer, default=0, nullable=False)
    warning_alerts_count = Column(Integer, default=0, nullable=False)
    
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    def __repr__(self):
        return f"<FleetOperationsLive driving={self.vehicles_driving} offline={self.vehicles_offline}>"

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Boolean, Enum, Index, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.enums import TripStatus

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration = Column(Float, nullable=False, default=0.0)  # seconds
    distance = Column(Float, nullable=False, default=0.0)  # kilometers
    average_speed = Column(Float, nullable=False, default=0.0)  # km/h
    maximum_speed = Column(Float, nullable=False, default=0.0)  # km/h
    idle_time = Column(Float, nullable=False, default=0.0)  # seconds
    start_lat = Column(Float, nullable=False)
    start_lon = Column(Float, nullable=False)
    end_lat = Column(Float, nullable=False)
    end_lon = Column(Float, nullable=False)
    packet_count = Column(Integer, nullable=False, default=1)
    overspeed_count = Column(Integer, nullable=False, default=0)
    status = Column(Enum(TripStatus), nullable=False, default=TripStatus.ACTIVE)
    is_active = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Placeholders for future extensibility
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True)
    driver_snapshot = Column(JSONB, nullable=True)
    fuel_used = Column(Float, nullable=True)
    engine_hours = Column(Float, nullable=True)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="trips")
    driver = relationship("Driver", back_populates="trips")
    route_cache_links = relationship("TripRouteCacheLink", back_populates="trip", cascade="all, delete-orphan")

    # Composite indexes for fast reports/queries
    __table_args__ = (
        Index("ix_trips_vehicle_is_active", "vehicle_id", "is_active"),
        Index("ix_trips_vehicle_start_time", "vehicle_id", "start_time"),
        Index("ix_trips_vehicle_end_time", "vehicle_id", "end_time"),
    )

    def __repr__(self):
        return f"<Trip id={self.id} vehicle_id={self.vehicle_id} distance={self.distance} status={self.status}>"

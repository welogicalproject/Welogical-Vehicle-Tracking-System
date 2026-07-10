from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class PlannedRoute(Base):
    __tablename__ = "planned_routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    start_location = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    distance = Column(Float, nullable=False)  # distance in kilometers or meters
    estimated_duration = Column(Integer, nullable=False)  # duration in seconds
    status = Column(String, nullable=False, default="Pending")  # e.g., "Pending", "Assigned", "Running", "Completed"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
    )

    # Relationships
    points = relationship(
        "PlannedRoutePoint",
        back_populates="route",
        order_by="PlannedRoutePoint.sequence_number",
        cascade="all, delete-orphan",
    )
    assignments = relationship(
        "VehicleRouteAssignment",
        back_populates="route",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<PlannedRoute id={self.id} name='{self.name}' status='{self.status}'>"


class PlannedRoutePoint(Base):
    __tablename__ = "planned_route_points"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("planned_routes.id", ondelete="CASCADE"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Relationships
    route = relationship("PlannedRoute", back_populates="points")

    def __repr__(self):
        return f"<PlannedRoutePoint id={self.id} route_id={self.route_id} seq={self.sequence_number} lat={self.latitude} lon={self.longitude}>"


class VehicleRouteAssignment(Base):
    __tablename__ = "vehicle_route_assignments"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    route_id = Column(Integer, ForeignKey("planned_routes.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    route = relationship("PlannedRoute", back_populates="assignments")
    vehicle = relationship("Vehicle")

    def __repr__(self):
        return f"<VehicleRouteAssignment id={self.id} vehicle_id={self.vehicle_id} route_id={self.route_id} active={self.is_active}>"

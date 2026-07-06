from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float, nullable=False)
    altitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    extra_data = Column(JSONB, nullable=True) # stores VTS 'io', 'pwr', 'dbg', etc.

    # Relationships
    vehicle = relationship("Vehicle", back_populates="locations")

    def __repr__(self):
        return f"<Location id={self.id} vehicle_id={self.vehicle_id} coords=({self.latitude}, {self.longitude})>"

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.enums import DriverStatus

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    driver_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    email = Column(String, nullable=True)
    license_number = Column(String, nullable=False)
    license_expiry = Column(DateTime, nullable=False)
    emergency_contact = Column(String, nullable=False)
    status = Column(Enum(DriverStatus), default=DriverStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    # Relationships
    assignments = relationship("DriverAssignment", back_populates="driver", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="driver")

    @property
    def current_vehicle(self):
        for asg in self.assignments:
            if asg.status == "Active":
                return asg.vehicle
        return None

    def __repr__(self):
        return f"<Driver id={self.id} name='{self.driver_name}' license='{self.license_number}'>"

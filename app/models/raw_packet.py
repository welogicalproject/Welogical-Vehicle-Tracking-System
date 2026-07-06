from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class RawPacket(Base):
    __tablename__ = "raw_packets"

    id = Column(Integer, primary_key=True, index=True)
    device_uid = Column(String, index=True, nullable=True)
    message_id = Column(Integer, index=True, nullable=True) # VTS 'msgid' for duplicate checking
    packet_data = Column(JSONB, nullable=False) # store the full JSON payload
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True, nullable=False)

    def __repr__(self):
        return f"<RawPacket id={self.id} device_uid='{self.device_uid}' msgid={self.message_id}>"

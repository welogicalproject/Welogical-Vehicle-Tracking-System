import enum


class CommandStatus(str, enum.Enum):
    Queued = "Queued"
    Sending = "Sending"
    Delivered = "Delivered"
    Acknowledged = "Acknowledged"
    Executing = "Executing"
    Completed = "Completed"
    Failed = "Failed"
    Timed_Out = "Timed Out"
    Cancelled = "Cancelled"
    # Legacy aliases
    PENDING = "PENDING"
    SENT = "SENT"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class TripStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class DriverStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"



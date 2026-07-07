from datetime import datetime, timezone
from typing import Optional

def normalize_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Normalizes an incoming datetime from FastAPI/Pydantic:
    - returns None if input is None
    - converts timezone-aware datetime to UTC
    - removes tzinfo (makes it naive)
    - leaves already-naive UTC values unchanged
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

from pydantic import BaseModel
from datetime import datetime


class FlightAssignment(BaseModel):
    id: int
    flight_id: int
    crew_member_id: int
    assigned_by: int
    assigned_at: datetime
    status: str  # ASSIGNED | CONFIRMED | CANCELLED
    notes: str | None = None

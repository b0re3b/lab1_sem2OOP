from pydantic import BaseModel
from datetime import datetime


class Flight(BaseModel):
    id: int
    flight_number: str
    departure_city: str
    arrival_city: str
    departure_time: datetime
    arrival_time: datetime
    aircraft_type: str
    status: str  # SCHEDULED | DELAYED | CANCELLED | COMPLETED
    crew_required: int
    created_by: int
    created_at: datetime
    updated_at: datetime

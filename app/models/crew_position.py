from pydantic import BaseModel
from datetime import datetime


class CrewPosition(BaseModel):
    id: int
    position_name: str
    description: str | None = None
    is_required: bool
    created_at: datetime

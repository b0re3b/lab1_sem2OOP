from pydantic import BaseModel, EmailStr
from datetime import datetime


class CrewMember(BaseModel):
    id: int
    employee_id: str
    first_name: str
    last_name: str
    position_id: int
    experience_years: int
    certification_level: str  # JUNIOR | SENIOR | CAPTAIN
    is_available: bool = True
    phone: str | None = None
    email: EmailStr | None = None
    created_at: datetime
    updated_at: datetime

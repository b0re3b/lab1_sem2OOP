from pydantic import BaseModel, EmailStr
from datetime import datetime


class User(BaseModel):
    id: int
    keycloak_id: str
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    role: str  # ADMIN | DISPATCHER
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

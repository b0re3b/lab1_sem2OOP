from pydantic import BaseModel
from datetime import datetime
from typing import Any


class OperationLog(BaseModel):
    id: int
    user_id: int | None = None
    operation_type: str
    table_name: str
    record_id: int | None = None
    old_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None
    description: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime

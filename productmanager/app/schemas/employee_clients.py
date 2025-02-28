# app/schemas/employee_clients.py
from pydantic import BaseModel, field_serializer
from datetime import date, datetime
from typing import Optional

class EmployeeClientCreate(BaseModel):
    """
    Many-to-Many 관계 등록용 (사원ID, 거래처ID, start_date 등)
    """
    employee_id: int
    client_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class EmployeeClientOut(BaseModel):
    id: int
    employee_id: int
    client_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime  # ✅ 추가
    updated_at: datetime  # ✅ 추가

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(value: datetime, _info) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""

    class Config:
        from_attributes = True
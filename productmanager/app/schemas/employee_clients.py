# app/schemas/employee_clients.py
from pydantic import BaseModel
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
    start_date: Optional[date]
    end_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
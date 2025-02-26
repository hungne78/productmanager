# app/schemas/lent.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LentCreate(BaseModel):
    client_id: int
    brand: str
    serial_number: str
    year: int

class LentOut(BaseModel):
    id: int
    client_id: int
    brand: str
    serial_number: str
    year: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

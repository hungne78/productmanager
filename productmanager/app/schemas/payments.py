# app/schemas/payments.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PaymentCreate(BaseModel):
    client_id: int
    payment_date: datetime
    amount: float
    payment_method: str
    note: Optional[str] = None

class PaymentOut(BaseModel):
    id: int
    client_id: int
    payment_date: datetime
    amount: float
    payment_method: str
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

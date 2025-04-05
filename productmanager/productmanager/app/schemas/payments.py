from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class PaymentCreate(BaseModel):
    """ 결제 등록 요청 스키마 (KST 값 그대로 사용) """
    client_id: int
    payment_date: datetime
    amount: float
    payment_method: str
    note: Optional[str] = None

class PaymentOut(BaseModel):
    """ 결제 조회 응답 스키마 (KST 값 그대로 사용) """
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

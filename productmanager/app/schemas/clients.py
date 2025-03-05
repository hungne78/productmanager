# app/schemas/clients.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime


class ClientCreate(BaseModel):
    """ 거래처 등록 요청 스키마 (KST 값 그대로 사용) """
    client_name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    outstanding_amount: float = 0
    regular_price: Optional[float] = None
    fixed_price: Optional[float] = None
    business_number: Optional[str] = None
    email: Optional[str] = None

class ClientOut(BaseModel):
    """ 거래처 조회 응답 스키마 (KST 값 그대로 사용) """
    id: int
    client_name: str
    address: Optional[str]
    phone: Optional[str]
    outstanding_amount: float
    regular_price: Optional[float] = None
    fixed_price: Optional[float] = None
    business_number: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime  # ✅ 변환 없이 KST 값 그대로 사용
    updated_at: datetime  # ✅ 변환 없이 KST 값 그대로 사용

    class Config:
        from_attributes = True  # ✅ ORM 모델을 Pydantic 스키마로 변환
# app/schemas/clients.py
from pydantic import BaseModel, field_validator
from typing import Optional
from decimal import Decimal

class ClientCreate(BaseModel):
    client_name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    outstanding_amount: float = 0  # 기본값 0

class ClientOut(BaseModel):
    id: int
    client_name: str
    address: Optional[str]
    phone: Optional[str]
    outstanding_amount: float

    # Pydantic v2용 검증자: 필드 값이 Decimal이면 float으로 변환
    @field_validator("outstanding_amount", mode="before")
    @classmethod
    def convert_decimal(cls, value):
        if value is None:
            return 0
        if isinstance(value, Decimal):
            return int(value)  # 소수점 이하 버림
        if isinstance(value, float):
            return int(value)
        return value
    
    class Config:
        from_attributes = True

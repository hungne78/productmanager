from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ClientCreate(BaseModel):
    """ 거래처 등록 요청 스키마 """
    client_name: str
    representative_name: Optional[str] = None  # ✅ 대표자 이름 추가
    address: Optional[str] = None
    phone: Optional[str] = None
    outstanding_amount: float = 0
    regular_price: Optional[float] = None
    fixed_price: Optional[float] = None
    business_number: Optional[str] = None
    email: Optional[str] = None

class ClientOut(BaseModel):
    """ 거래처 조회 응답 스키마 """
    id: int
    client_name: str
    representative_name: Optional[str]  # ✅ 대표자 이름 추가
    address: Optional[str]
    phone: Optional[str]
    outstanding_amount: float
    regular_price: Optional[float] = None
    fixed_price: Optional[float] = None
    business_number: Optional[str] = None
    email: Optional[str] = None
    virtual_account: Optional[str] = None  # ✅ 추가됨
    password_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ClientUpdate(BaseModel):
    client_name: str
    representative_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    outstanding_amount: float
    regular_price: Optional[float] = None
    fixed_price: Optional[float] = None
    business_number: Optional[str] = None
    email: Optional[str] = None
    virtual_account: Optional[str] = None  # ✅ 추가됨
    password: Optional[str] = None  # ✅ 추가
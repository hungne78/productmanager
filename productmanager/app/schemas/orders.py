# app/schemas/orders.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
from app.utils.time_utils import get_kst_now, get_kst_today, convert_utc_to_kst  # ✅ KST 변환 함수 추가

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    line_total: float
    incentive: float = 0.0

class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    line_total: float
    incentive: float
    created_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    updated_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    client_id: int
    employee_id: int
    items: List[OrderItemCreate] = []  # 주문 항목
    status: Optional[str] = "pending"
    order_date: Optional[date] = Field(default_factory=get_kst_today)  # ✅ KST 변환 적용

class OrderOut(BaseModel):
    id: int
    client_id: int
    employee_id: int
    total_amount: float
    status: str
    order_date: date = Field(default_factory=get_kst_today)  # ✅ KST 변환 적용
    order_items: List[OrderItemOut]
    created_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    updated_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

    @staticmethod
    def convert_kst(obj):
        """ UTC → KST 변환 함수 (Pydantic 자동 변환) """
        return convert_utc_to_kst(obj) if obj else None

    class Config:
        from_attributes = True

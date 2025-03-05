from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date

class OrderItemCreate(BaseModel):
    """ 주문 항목 등록 요청 스키마 """
    product_id: int
    quantity: int
    unit_price: float
    line_total: float
    incentive: float = 0.0

class OrderItemOut(BaseModel):
    """ 주문 항목 조회 응답 스키마 """
    id: int
    product_id: int
    quantity: int
    unit_price: float
    line_total: float
    incentive: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    """ 주문 등록 요청 스키마 (KST 값 그대로 사용) """
    client_id: int
    employee_id: int
    items: List[OrderItemCreate] = []
    status: Optional[str] = "pending"
    order_date: Optional[date] = None  # ✅ 기본값 제거

class OrderOut(BaseModel):
    """ 주문 조회 응답 스키마 (KST 값 그대로 사용) """
    id: int
    client_id: int
    employee_id: int
    total_amount: float
    status: str
    order_date: date
    order_items: List[OrderItemOut]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# app/schemas/orders.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    client_id: int
    employee_id: int
    # 주문 항목
    items: List[OrderItemCreate] = []
    # 상태, 주문일자 등은 선택적으로 입력 가능
    status: Optional[str] = "pending"
    order_date: Optional[date] = None

class OrderOut(BaseModel):
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

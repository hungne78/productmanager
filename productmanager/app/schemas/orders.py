# app/schemas/orders.py
from pydantic import BaseModel
from typing import List
from datetime import datetime

# 주문 품목 입력용 (OrderItemCreate) – 필요 시
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    line_total: float
    # 인센티브(절대 금액), 선택적으로 입력 (없으면 0)
    incentive: float = 0

# 주문 품목 출력용 (OrderItemOut)
class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    line_total: float
    incentive: float  # 추가된 인센티브 필드
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 주문 생성 입력 스키마
class OrderCreate(BaseModel):
    client_id: int
    employee_id: int
    items: List[OrderItemCreate]

# 주문 출력 스키마
class OrderOut(BaseModel):
    id: int
    client_id: int
    employee_id: int
    order_date: datetime
    total_amount: float
    status: str
    order_items: List[OrderItemOut]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

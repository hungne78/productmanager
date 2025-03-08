from pydantic import BaseModel
from datetime import date
from typing import List, Optional

# ✅ 주문 항목(OrderItem) 스키마
class OrderItemSchema(BaseModel):
    product_id: int
    quantity: int

    class Config:
        from_attributes = True

# ✅ 주문(Order) 스키마
class OrderSchema(BaseModel):
    id: int
    employee_id: int
    order_date: date
    status: str
    total_amount: float
    total_incentive: float
    total_boxes: int
    order_items: List[OrderItemSchema]  # ✅ 주문 항목 포함

    class Config:
        from_attributes = True

# ✅ 주문 생성 스키마 (id 없이)
class OrderCreateSchema(BaseModel):
    employee_id: int
    order_date: date
    total_amount: float  # ✅ 총 주문 금액 추가
    total_incentive: float  # ✅ 총 인센티브 추가
    total_boxes: int  # ✅ 총 박스 수량 추가
    order_items: List[OrderItemSchema]  # ✅ 주문 항목

# ✅ 특정 직원의 특정 날짜 주문 요약 스키마
class OrderSummarySchema(BaseModel):
    total_amount: float
    total_incentive: float
    total_boxes: int

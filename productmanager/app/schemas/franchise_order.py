from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

class FranchiseOrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class FranchiseOrderCreate(BaseModel):
    client_id: int
    order_date: date
    shipment_round: int = 0
    items: List[FranchiseOrderItemCreate]

class FranchiseOrderItemOut(BaseModel):
    product_id: int
    quantity: int
    product_name: Optional[str] = None  # 조회 시 이름도 같이

    class Config:
        from_attributes = True

class FranchiseOrderOut(BaseModel):
    id: int
    client_id: int
    client_name: str
    employee_id: int
    order_date: date
    shipment_round: int
    is_transferred: bool
    is_read: bool
    created_at: datetime
    items: List[FranchiseOrderItemOut]

    class Config:
        
        from_attributes = True
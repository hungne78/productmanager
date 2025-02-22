# app/schemas/products.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductCreate(BaseModel):
    brand_id: int
    product_name: str
    barcode: Optional[str] = None
    default_price: float = 0
    incentive: float = 0   
    stock: int = 0
    is_active: int = 1
    box_quantity: int = 1  # ✅ 박스당 제품 개수 추가
    category: Optional[str] = None  # ✅ 상품 분류 추가
    
class ProductOut(BaseModel):
    id: int
    brand_id: int
    product_name: str
    barcode: Optional[str]
    default_price: float
    incentive: float
    stock: int
    is_active: int
    box_quantity: int  # ✅ 박스당 제품 개수 추가
    category: Optional[str]  # ✅ 상품 분류 추가
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

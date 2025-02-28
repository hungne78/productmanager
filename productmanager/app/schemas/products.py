# app/schemas/products.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pydantic import field_serializer
class ProductBase(BaseModel):
    product_name: str
    is_fixed_price: bool  # ✅ 상품이 고정가인지 여부

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
    is_fixed_price: bool  # ✅ 상품이 고정가인지 여부
    
class ProductOut(BaseModel):
    id: int
    brand_id: int
    product_name: str
    barcode: Optional[str]
    default_price: float
    incentive: float
    stock: int
    is_active: int
    box_quantity: int
    category: Optional[str]
    is_fixed_price: bool
    created_at: datetime
    updated_at: datetime

    # ✅ datetime 값을 문자열로 변환하는 함수
    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime, _info) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return ""  # 혹시 None 값이 있으면 빈 문자열 반환

    class Config:
        from_attributes = True


class ProductUpdate(ProductBase):
    pass
class ProductResponse(ProductBase):
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
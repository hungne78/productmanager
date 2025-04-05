# app/schemas/products.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.utils.time_utils import convert_utc_to_kst, get_kst_now


# ✅ 공통 필드 정의
class ProductBase(BaseModel):
    product_name: str
    is_fixed_price: bool  # 고정가 여부
    default_price: float = 0
    incentive: float = 0
    stock: int = 0
    is_active: int = 1
    box_quantity: int = 1
    category: Optional[str] = None
    barcodes: List[str] = []

    class Config:
        from_attributes = True


# ✅ 상품 생성 시 사용
class ProductCreate(ProductBase):
    brand_name: str


# ✅ 상품 응답용 (id는 없고, brand_name 문자열만 표시)
class ProductOut(ProductBase):
    id: int
    brand_name: str
    created_at: datetime = Field(default_factory=get_kst_now)
    updated_at: datetime = Field(default_factory=get_kst_now)

    class Config:
        from_attributes = True


# ✅ 상품 수정 시 사용
class ProductUpdate(ProductBase):
    pass


# ✅ 단일 상품 상세 응답 (id 포함)
class ProductResponse(ProductBase):
    id: int
    brand_name: str
    created_at: datetime = Field(default_factory=get_kst_now)
    updated_at: datetime = Field(default_factory=get_kst_now)

    class Config:
        from_attributes = True

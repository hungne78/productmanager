# app/schemas/products.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.utils.time_utils import get_kst_now, convert_utc_to_kst  # ✅ KST 변환 함수 추가

class ProductBase(BaseModel):
    product_name: str
    is_fixed_price: bool  # ✅ 상품이 고정가인지 여부

class ProductCreate(BaseModel):
    brand_id: int
    product_name: str
    barcodes: List[str] = []
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
    barcodes: List[str] = []
    default_price: float
    incentive: float
    stock: int
    is_active: int
    box_quantity: int
    category: Optional[str]
    is_fixed_price: bool
    created_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    updated_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

    @staticmethod
    def convert_kst(obj):
        """ UTC → KST 변환 함수 (Pydantic 자동 변환) """
        return convert_utc_to_kst(obj) if obj else None

    class Config:
        from_attributes = True

class ProductUpdate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    updated_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

    class Config:
        from_attributes = True

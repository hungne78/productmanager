from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.utils.time_utils import get_kst_now, convert_utc_to_kst  # ✅ KST 변환 함수 추가

class ProductSalesOut(BaseModel):
    """ 거래처별 판매 상품 정보 """
    product_name: str
    quantity: int

class EmployeeClientSalesOut(BaseModel):
    """ 특정 직원이 담당하는 거래처별 매출 데이터 """
    client_id: int
    total_sales: float
    products: List[ProductSalesOut]

class SalesRecordCreate(BaseModel):
    """ 매출 등록 요청 스키마 (단가 제외) """
    employee_id: int  # ✅ 직원 ID는 선택적으로 받을 수 있음
    client_id: int
    product_id: int
    quantity: int
    sale_datetime: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

class TotalSalesOut(BaseModel):
    """ 거래처별 당일 총매출 출력 스키마 """
    client_id: int
    total_sales: float

class SalesOut(BaseModel):
    """ 거래처별 당일 판매 품목 출력 스키마 """
    client_id: int
    product_id: int
    product_name: str
    quantity: int

class SalesRecordOut(BaseModel):
    """ 매출 데이터 반환 스키마 """
    id: int
    employee_id: Optional[int] = None  # ✅ 직원 ID 추가
    client_id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    total_amount: float
    sale_date: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

    @staticmethod
    def convert_kst(obj):
        """ UTC → KST 변환 함수 (Pydantic 자동 변환) """
        return convert_utc_to_kst(obj) if obj else None

    class Config:
        from_attributes = True  # ✅ Pydantic V2에서는 from_attributes 사용

class OutstandingUpdate(BaseModel):
    outstanding_amount: float  # ✅ FastAPI가 기대하는 데이터 타입

class SaleItem(BaseModel):
    product_id: int
    quantity: int

class SalesAggregateCreate(BaseModel):
    employee_id: int
    client_id: int
    items: List[SaleItem]  # 여러 상품
    sale_datetime: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
import pytz
KST = pytz.timezone("Asia/Seoul")
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
    """ 매출 등록 요청 스키마 (KST 값 그대로 사용) """
    employee_id: int
    client_id: int
    product_id: int
    quantity: int
    sale_datetime: datetime
    return_amount: float = 0.0  # ✅ 기본값 0.0
    subsidy_amount: float = 0.0  # ✅ 지원금 필드 추가   
    client_price: Optional[float] = None         # ✅ 프론트에서 보낸 단가
    box_unit_count: Optional[int] = None

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
    """ 매출 데이터 반환 스키마 (KST 값 그대로 사용) """
    id: int
    employee_id: Optional[int] = None
    client_id: int
    product_id: int
    quantity: int
    sale_datetime: datetime
    return_amount: float  # ✅ 반품 금액 추가

    class Config:
        from_attributes = True  # ✅ ORM 모델을 Pydantic 스키마로 변환

class OutstandingUpdate(BaseModel):
    outstanding_amount: float  # ✅ FastAPI가 기대하는 데이터 타입

class SaleItem(BaseModel):
    product_id: int
    quantity: int

class SalesAggregateCreate(BaseModel):
    employee_id: int
    client_id: int
    items: List[SaleItem]  # 여러 상품
    sale_datetime: datetime 

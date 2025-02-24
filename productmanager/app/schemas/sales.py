from pydantic import BaseModel
from typing import List
from datetime import date, datetime

class ProductSalesOut(BaseModel):
    """
    거래처별 판매 상품 정보
    """
    product_name: str
    quantity: int

class EmployeeClientSalesOut(BaseModel):
    """
    특정 직원이 담당하는 거래처별 매출 데이터
    """
    client_id: int
    total_sales: float
    products: List[ProductSalesOut]
    
class SalesRecordCreate(BaseModel):
    """
    매출 등록 요청 스키마 (단가 제외)
    """
    client_id: int
    product_id: int
    quantity: int
    sale_date: date

class TotalSalesOut(BaseModel):
    """
    거래처별 당일 총매출 출력 스키마
    """
    client_id: int
    total_sales: float

class SalesOut(BaseModel):
    """
    거래처별 당일 판매 품목 출력 스키마
    """
    client_id: int
    product_id: int
    product_name: str
    quantity: int
    
class SalesRecordCreate(BaseModel):
    """
    매출 데이터 생성 시 사용되는 스키마
    """
    client_id: int
    product_id: int
    quantity: int
    sale_date: date
    
class SalesRecordOut(BaseModel):
    """
    매출 등록 응답 스키마 (단가 및 총매출 포함)
    """
    id: int
    client_id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    total_amount: float
    sale_date: date

    class Config:
        from_attributes = True
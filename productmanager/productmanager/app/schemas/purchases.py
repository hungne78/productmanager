from pydantic import BaseModel, Field
from datetime import datetime, date

class PurchaseOut(BaseModel):
    """ 매입 내역 조회 응답 스키마 (KST 값 그대로 사용) """
    id: int
    product_id: int
    quantity: int
    unit_price: float
    purchase_date: date  # ✅ 변환 없이 KST 값 그대로 사용

    class Config:
        from_attributes = True

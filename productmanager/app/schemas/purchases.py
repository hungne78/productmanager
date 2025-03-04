from pydantic import BaseModel, Field
from datetime import datetime
from app.utils.time_utils import get_kst_now, convert_utc_to_kst  # ✅ KST 변환 함수 추가

class PurchaseOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    purchase_date: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

    @staticmethod
    def convert_kst(obj):
        """ UTC → KST 변환 함수 (Pydantic 자동 변환) """
        return convert_utc_to_kst(obj) if obj else None

    class Config:
        from_attributes = True

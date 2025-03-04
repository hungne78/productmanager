from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.utils.time_utils import get_kst_now, convert_utc_to_kst  # ✅ KST 변환 함수 추가

class ClientVisitCreate(BaseModel):
    id: int 
    client_id: int
    visit_datetime: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    order_id: Optional[int] = None

class ClientVisitOut(BaseModel):
    id: int
    id_employee: int
    client_id: int
    visit_datetime: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    order_id: Optional[int]
    created_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    updated_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

    @staticmethod
    def convert_kst(obj):
        """ UTC → KST 변환 함수 (Pydantic 자동 변환) """
        return convert_utc_to_kst(obj) if obj else None

    class Config:
        from_attributes = True

# app/schemas/employee_clients.py
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime
from typing import Optional
from app.utils.time_utils import get_kst_now, convert_utc_to_kst  # ✅ KST 변환 함수 추가

class EmployeeClientCreate(BaseModel):
    """
    Many-to-Many 관계 등록용 (사원ID, 거래처ID, start_date 등)
    """
    employee_id: int
    client_id: int
    start_date: Optional[datetime] = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    end_date: Optional[datetime] = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

class EmployeeClientOut(BaseModel):
    id: int
    employee_id: int
    client_id: int
    start_date: Optional[datetime] = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    end_date: Optional[datetime] = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    created_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    updated_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

    @staticmethod
    def convert_kst(obj):
        """ UTC → KST 변환 함수 (Pydantic 자동 변환) """
        return convert_utc_to_kst(obj) if obj else None

    class Config:
        from_attributes = True

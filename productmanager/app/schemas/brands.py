# app/schemas/brands.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.utils.time_utils import get_kst_now, convert_utc_to_kst  # ✅ KST 변환 함수 추가

class BrandCreate(BaseModel):
    """ 브랜드 생성 요청 스키마 """
    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=255)

class BrandOut(BaseModel):
    """ 브랜드 조회 응답 스키마 (KST 변환 적용) """
    id: int
    name: str
    description: Optional[str]
    created_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    updated_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

    @staticmethod
    def convert_kst(obj):
        """ UTC → KST 변환 함수 (Pydantic 자동 변환) """
        return convert_utc_to_kst(obj) if obj else None

    class Config:
        from_attributes = True

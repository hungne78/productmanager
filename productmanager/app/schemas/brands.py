# app/schemas/brands.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BrandCreate(BaseModel):
    """ 브랜드 생성 요청 스키마 """
    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=255)

class BrandOut(BaseModel):
    """ 브랜드 조회 응답 스키마 """
    id: int
    name: str
    description: Optional[str]
    created_at: datetime  # ✅ str → datetime 변경
    updated_at: datetime  # ✅ str → datetime 변경

    class Config:
        from_attributes = True

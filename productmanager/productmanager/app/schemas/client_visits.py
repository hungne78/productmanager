from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ClientVisitCreate(BaseModel):
    """ 방문 기록 생성 요청 스키마 (FastAPI에서 UTC 저장 후 변환) """
    id: int 
    client_id: int
    visit_datetime: datetime  # ✅ UTC로 저장 (KST 변환 없음)
    order_id: Optional[int] = None

class ClientVisitOut(BaseModel):
    """ 방문 기록 응답 스키마 (FastAPI에서 변환된 KST 값 반환) """
    id: int
    id_employee: int
    client_id: int
    visit_datetime: str  # ✅ FastAPI 라우터에서 변환된 KST 값을 그대로 받음
    order_id: Optional[int]
    created_at: str  # ✅ UTC → KST 변환 후 문자열로 저장
    updated_at: str  # ✅ UTC → KST 변환 후 문자열로 저장

    class Config:
        from_attributes = True  # ✅ ORM 모델을 Pydantic 스키마로 변환

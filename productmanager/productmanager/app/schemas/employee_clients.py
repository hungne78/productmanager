from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class EmployeeClientCreate(BaseModel):
    """ 사원과 거래처 연결 등록 요청 스키마 (기본값 제거) """
    employee_id: int
    client_id: int
    start_date: Optional[datetime] = None  # ✅ 기본값 제거
    end_date: Optional[datetime] = None  # ✅ 기본값 제거

class EmployeeClientOut(BaseModel):
    """ 사원과 거래처 연결 응답 스키마 (KST 값 그대로 사용) """
    id: int
    employee_id: int
    client_id: int
    start_date: Optional[datetime]  # ✅ 변환 없이 그대로 반환
    end_date: Optional[datetime]  # ✅ 변환 없이 그대로 반환
    created_at: datetime  # ✅ 변환 없이 그대로 반환
    updated_at: datetime  # ✅ 변환 없이 그대로 반환

    class Config:
        from_attributes = True  # ✅ ORM 모델을 Pydantic 스키마로 변환

# app/schemas/employees.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from app.utils.time_utils import get_kst_now, convert_utc_to_kst  # ✅ KST 변환 함수 추가

class EmployeeCreate(BaseModel):
    password: str
    name: str
    phone: Optional[str] = None
    role: Optional[str] = "sales"
    birthday: Optional[date] = None      
    address: Optional[str] = None         

class EmployeeOut(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    role: str
    birthday: Optional[date] = None       
    address: Optional[str] = None         
    created_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    updated_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

    @staticmethod
    def convert_kst(obj):
        """ UTC → KST 변환 함수 (Pydantic 자동 변환) """
        return convert_utc_to_kst(obj) if obj else None

    class Config:
        from_attributes = True

class EmployeeUpdate(BaseModel):
    password: Optional[str]
    name: Optional[str]
    phone: Optional[str]
    role: Optional[str]
    birthday: Optional[date] = None       
    address: Optional[str] = None         

class EmployeeLogin(BaseModel):
    id: int
    password: str

class EmployeeLoginResponse(BaseModel):
    """
    로그인 시에만 쓰일 응답 스키마.
    Employee 정보 + token
    """
    
    id: int
    name: str
    phone: Optional[str]
    role: str
    token: str

    class Config:
        from_attributes = True

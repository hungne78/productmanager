# app/schemas/employees.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


class EmployeeCreate(BaseModel):
    """ 직원 등록 요청 스키마 (KST 값 그대로 사용) """
    password: str
    name: str
    phone: Optional[str] = None
    role: Optional[str] = "sales"
    birthday: Optional[date] = None
    address: Optional[str] = None

class EmployeeOut(BaseModel):
    """ 직원 조회 응답 스키마 (KST 값 그대로 사용) """
    id: int
    name: str
    phone: Optional[str]
    role: str
    birthday: Optional[date] = None
    address: Optional[str] = None
    created_at: datetime = None # ✅ 변환 없이 KST 값 그대로 사용
    updated_at: datetime = None # ✅ 변환 없이 KST 값 그대로 사용

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
    phone: Optional[str] = Field(None, example="010-1234-5678")
    role: str
    token: str

    class Config:
        from_attributes = True

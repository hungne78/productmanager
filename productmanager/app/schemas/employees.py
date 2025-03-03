# app/schemas/employees.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EmployeeUpdate(BaseModel):
    password: Optional[str]
    name: Optional[str]
    phone: Optional[str]
    role: Optional[str]
    birthday: Optional[date] = None       # 새 필드
    address: Optional[str] = None          # 새 필드
    
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
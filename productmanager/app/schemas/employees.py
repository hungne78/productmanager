# app/schemas/employees.py
from pydantic import BaseModel
from typing import Optional

class EmployeeCreate(BaseModel):
    
    password: str
    name: str
    phone: Optional[str] = None
    role: Optional[str] = "sales"

class EmployeeOut(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    role: str

    class Config:
        from_attributes = True

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
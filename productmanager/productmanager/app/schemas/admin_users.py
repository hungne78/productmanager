# app/schemas/admin_users.py
from pydantic import BaseModel, EmailStr

class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class AdminUserLogin(BaseModel):
    email: EmailStr
    password: str

class AdminUserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str

    class Config:
        from_attributes = True

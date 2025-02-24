# app/schemas/brands.py
from pydantic import BaseModel
from datetime import datetime

class BrandCreate(BaseModel):
    brand_name: str

class BrandOut(BaseModel):
    id: int
    brand_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

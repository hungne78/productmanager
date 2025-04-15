# schemas/category_price_override.py

from pydantic import BaseModel
from datetime import date

class CategoryPriceOverrideBase(BaseModel):
    client_id: int
    category_name: str
    price_type: str  # "normal" 또는 "fixed"
    override_price: float
    start_date: date
    end_date: date

class CategoryPriceOverrideCreate(CategoryPriceOverrideBase):
    pass

class CategoryPriceOverrideUpdate(CategoryPriceOverrideBase):
    pass

class CategoryPriceOverrideOut(CategoryPriceOverrideBase):
    id: int

    class Config:
        from_attributes = True 

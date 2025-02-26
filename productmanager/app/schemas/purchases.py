from pydantic import BaseModel
from datetime import datetime

class PurchaseOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    purchase_date: datetime

    class Config:
        from_attributes = True

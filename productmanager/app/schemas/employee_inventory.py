from pydantic import BaseModel
from typing import List

class InventoryItem(BaseModel):
    product_id: int
    quantity: int

class InventoryUpdate(BaseModel):
    employee_id: int
    items: List[InventoryItem]

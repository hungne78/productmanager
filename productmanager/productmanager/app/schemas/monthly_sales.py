from pydantic import BaseModel
from typing import Optional

class MonthlySalesBase(BaseModel):
    client_id: Optional[int]
    employee_id: Optional[int]
    year: int
    month: int
    total_sales: float
    total_returns: float = 0.0
    total_subsidy: float = 0.0

class MonthlySalesCreate(MonthlySalesBase):
    pass

class MonthlySalesOut(MonthlySalesBase):
    id: int

    class Config:
        from_attributes = True

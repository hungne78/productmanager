from pydantic import BaseModel
from datetime import date
from typing import Optional

class EmployeeVehicleCreate(BaseModel):
    id: int
    monthly_fuel_cost: float = 0
    current_mileage: int = 0
    last_engine_oil_change: Optional[date] = None

class EmployeeVehicleOut(BaseModel):
    id: int
    id_employee: int
    monthly_fuel_cost: float
    current_mileage: int
    last_engine_oil_change: Optional[date]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

# app/schemas/employee_vehicle.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from app.utils.time_utils import get_kst_now, convert_utc_to_kst  # ✅ KST 변환 함수 추가
from datetime import date
class EmployeeVehicleCreate(BaseModel):
    employee_id: int
    monthly_fuel_cost: float
    current_mileage: int
    last_engine_oil_change: Optional[datetime] = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

    @field_validator("last_engine_oil_change", mode="before")
    @classmethod
    def parse_date(cls, value):
        if value is None or value == "":
            return None
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Expected YYYY-MM-DD.")
        return value

class EmployeeVehicleOut(BaseModel):
    id: int
    employee_id: int  # ✅ 이 필드가 누락되어 있었다면 추가해야 함
    monthly_fuel_cost: float
    current_mileage: int
    last_engine_oil_change: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
class EmployeeVehicleUpdate(BaseModel):
    monthly_fuel_cost: Optional[float] = 0  # ✅ 기본값 0 설정
    current_mileage: Optional[int] = 0  # ✅ 기본값 0 설정
    last_engine_oil_change: Optional[date] = None  # ✅ `None` 허용
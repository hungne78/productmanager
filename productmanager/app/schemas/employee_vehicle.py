# app/schemas/employee_vehicle.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from app.utils.time_utils import get_kst_now, convert_utc_to_kst  # ✅ KST 변환 함수 추가

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
    monthly_fuel_cost: Optional[float] = None
    current_mileage: Optional[int] = None
    last_engine_oil_change: Optional[datetime] = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    created_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용
    updated_at: datetime = Field(default_factory=get_kst_now)  # ✅ KST 변환 적용

    @staticmethod
    def convert_kst(obj):
        """ UTC → KST 변환 함수 (Pydantic 자동 변환) """
        return convert_utc_to_kst(obj) if obj else None

    class Config:
        from_attributes = True

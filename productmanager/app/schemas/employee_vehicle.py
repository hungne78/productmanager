from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional

class EmployeeVehicleCreate(BaseModel):
    employee_id: int
    monthly_fuel_cost: float
    current_mileage: int
    last_engine_oil_change: Optional[date]  # ✅ `date` 타입 유지

    # ✅ 날짜 형식 검증 (YYYY-MM-DD)
    @field_validator("last_engine_oil_change", mode="before")
    @classmethod
    def parse_date(cls, value):
        if value is None or value == "":
            return None  # ✅ 빈 값 허용
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()  # ✅ YYYY-MM-DD 형식 변환
            except ValueError:
                raise ValueError("Invalid date format. Expected YYYY-MM-DD.")
        return value

class EmployeeVehicleOut(BaseModel):
    id: int
    monthly_fuel_cost: Optional[float] = None
    current_mileage: Optional[int] = None
    last_engine_oil_change: Optional[str] = None  # ✅ datetime → str로 변경
    created_at: Optional[str] = None  # ✅ datetime → str로 변경
    updated_at: Optional[str] = None  # ✅ datetime → str로 변경

    class Config:
        from_attributes = True

    # ✅ from_orm을 오버라이드하여 datetime을 변환
    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            monthly_fuel_cost=obj.monthly_fuel_cost,
            current_mileage=obj.current_mileage,
            last_engine_oil_change=obj.last_engine_oil_change.strftime("%Y-%m-%d") if obj.last_engine_oil_change else None,
            created_at=obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            updated_at=obj.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
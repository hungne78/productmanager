from sqlalchemy import Column, Integer, DECIMAL, Date, DateTime, ForeignKey, Float
from datetime import datetime, date
from app.db.base import Base

class EmployeeVehicle(Base):
    __tablename__ = "employee_vehicles"

    id = Column(Integer, primary_key=True, index=True)  # 기존 employee_id 대신 id 사용
    monthly_fuel_cost = Column(Float, nullable=False, default=0)
    current_mileage = Column(Integer, nullable=False, default=0)
    last_engine_oil_change = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


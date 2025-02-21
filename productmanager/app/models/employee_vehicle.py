from sqlalchemy import Column, Integer, DECIMAL, Date, DateTime, ForeignKey
from datetime import datetime, date
from app.db.base import Base

class EmployeeVehicle(Base):
    __tablename__ = "employee_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, unique=True)
    monthly_fuel_cost = Column(DECIMAL(10,2), default=0, nullable=False)
    current_mileage = Column(Integer, default=0, nullable=False)
    last_engine_oil_change = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

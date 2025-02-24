from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, Float
from datetime import datetime
from app.db.base import Base
from sqlalchemy.orm import relationship

class EmployeeVehicle(Base):
    __tablename__ = "employee_vehicles"

    id = Column(Integer, primary_key=True, index=True)  
    employee_id = Column(Integer, ForeignKey("employees.id"), unique=True, nullable=False)  # ✅ 외래 키 추가
    monthly_fuel_cost = Column(Float, nullable=False, default=0)
    current_mileage = Column(Integer, nullable=False, default=0)
    last_engine_oil_change = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ Employee 관계 설정
    employee = relationship("Employee", back_populates="vehicle")

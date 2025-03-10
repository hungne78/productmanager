from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, Float
from datetime import datetime
from app.db.base import Base
from sqlalchemy.orm import relationship
from pytz import timezone

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환 """
    kst = timezone("Asia/Seoul")
    return datetime.utcnow().astimezone(kst)

class EmployeeVehicle(Base):
    __tablename__ = "employee_vehicles"

    id = Column(Integer, primary_key=True, index=True)  
    employee_id = Column(Integer, ForeignKey("employees.id"), unique=True, nullable=False)  # ✅ 외래 키 추가
    monthly_fuel_cost = Column(Float, nullable=False, default=0)
    current_mileage = Column(Integer, nullable=False, default=0)
    last_engine_oil_change = Column(Date, nullable=True)

    # ✅ KST 기준으로 생성/수정 시간 저장
    created_at = Column(DateTime, default=get_kst_now)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now)

    # ✅ Employee 관계 설정
    employee = relationship("Employee", back_populates="vehicle")

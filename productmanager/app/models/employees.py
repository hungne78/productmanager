from sqlalchemy import Column, Integer, String, DateTime, Date
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz
from app.db.base import Base

KST = pytz.timezone("Asia/Seoul")

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환하여 반환 """
    return datetime.now(KST)

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    phone = Column(String(20))
    role = Column(String(20), default="sales")
    birthday = Column(Date, nullable=True)
    address = Column(String(255), nullable=True)

    # ✅ KST 기준으로 생성/수정 시간 저장
    created_at = Column(DateTime, default=get_kst_now)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now)

    # 관계 설정
    sales = relationship("Sales", back_populates="employee")
    employee_clients = relationship("EmployeeClient", back_populates="employee", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="employee")
    vehicle = relationship("EmployeeVehicle", back_populates="employee", uselist=False)
    client_visits = relationship("ClientVisit", back_populates="employee")
    clients = relationship("Client", secondary="employee_clients", back_populates="employees", overlaps="employee_clients")
    sales_records = relationship("SalesRecord", back_populates="employee")

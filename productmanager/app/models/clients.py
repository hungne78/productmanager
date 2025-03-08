from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz
from app.db.base import Base

KST = pytz.timezone("Asia/Seoul")

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환하여 반환 """
    return datetime.now(KST)

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(100), nullable=False)
    representative_name = Column(String(100), nullable=True)
    address = Column(String(255))
    phone = Column(String(50))
    outstanding_amount = Column(DECIMAL(10,2), default=0)
    
    regular_price = Column(Float, nullable=True)  # 일반가
    fixed_price = Column(Float, nullable=True)    # 고정가
    
    business_number = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)

    # ✅ KST 기준으로 생성/수정 시간 저장
    created_at = Column(DateTime, default=get_kst_now)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now)

    # 관계 설정
    employee_clients = relationship("EmployeeClient", back_populates="client")
    orders = relationship("Order", back_populates="client")
    client_visits = relationship("ClientVisit", back_populates="client")
    client_product_prices = relationship("ClientProductPrice", back_populates="client")
    lents = relationship("Lent", back_populates="client")
    sales = relationship("Sales", back_populates="client", cascade="all, delete-orphan")
    employees = relationship("Employee", secondary="employee_clients", back_populates="clients", overlaps="employee_clients")
    sales_records = relationship("SalesRecord", back_populates="client", cascade="all, delete-orphan")

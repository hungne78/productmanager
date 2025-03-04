from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Float
from datetime import datetime
from app.db.base import Base
from sqlalchemy.orm import relationship
from pytz import timezone

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환 """
    kst = timezone("Asia/Seoul")
    return datetime.utcnow().astimezone(kst)

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(100), nullable=False)
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

    # ✅ EmployeeClient와 관계 설정 (다대다)
    employee_clients = relationship("EmployeeClient", back_populates="client")

    # ✅ Order와 관계 설정 (1:N)
    orders = relationship("Order", back_populates="client")

    # ✅ ClientVisit과 관계 설정 (1:N)
    client_visits = relationship("ClientVisit", back_populates="client")
    
    client_product_prices = relationship("ClientProductPrice", back_populates="client")
    lents = relationship("Lent", back_populates="client")
    sales = relationship("Sales", back_populates="client", cascade="all, delete-orphan")
    # ✅ `overlaps="employee_clients"` 추가하여 중복 관계 해결
    employees = relationship("Employee", secondary="employee_clients", back_populates="clients", overlaps="employee_clients")
    sales_records = relationship("SalesRecord", back_populates="client", cascade="all, delete-orphan")  # ✅ 삭제 연쇄 적용

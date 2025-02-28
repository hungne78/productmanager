from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Float
from datetime import datetime
from app.db.base import Base
from sqlalchemy.orm import relationship

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ EmployeeClient와 관계 설정 (다대다)
    employee_clients = relationship("EmployeeClient", back_populates="client")

    # ✅ Order와 관계 설정 (1:N)
    orders = relationship("Order", back_populates="client")

    # ✅ ClientVisit과 관계 설정 (1:N)
    client_visits = relationship("ClientVisit", back_populates="client")
    sales_records = relationship("SalesRecord", back_populates="client")
    client_product_prices = relationship("ClientProductPrice", back_populates="client")
    lents = relationship("Lent", back_populates="client")
    
    # ✅ `overlaps="employee_clients"` 추가하여 중복 관계 해결
    employees = relationship("Employee", secondary="employee_clients", back_populates="clients", overlaps="employee_clients")



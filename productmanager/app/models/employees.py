from sqlalchemy import Column, Integer, String, DateTime, Date
from datetime import datetime
from sqlalchemy.orm import relationship
from app.db.base import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    phone = Column(String(20))
    role = Column(String(20), default="sales")
    birthday = Column(Date, nullable=True)
    address = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # ✅ `SalesRecord`가 아니라 `Sales`와 관계를 설정해야 함
    sales = relationship("Sales", back_populates="employee")  # 🔥 여기 수정

    # Many-to-Many 중간테이블과 관계
    employee_clients = relationship("EmployeeClient", back_populates="employee", cascade="all, delete-orphan")
    
    # # orders 관계 (사원 - 주문 : 1대다)
    orders = relationship("Order", back_populates="employee")

    # 차량 관계는 employee_vehicle.py에서 id=employee_id로 직접 매핑 or 외래키
    vehicle = relationship("EmployeeVehicle", back_populates="employee", uselist=False)
    client_visits = relationship("ClientVisit", back_populates="employee")
    
    # ✅ `overlaps="employee_clients"` 추가하여 중복 관계 해결
    clients = relationship("Client", secondary="employee_clients", back_populates="employees", overlaps="employee_clients")
    sales_records = relationship("SalesRecord", back_populates="employee")
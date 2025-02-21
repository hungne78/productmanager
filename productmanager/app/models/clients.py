# app/models/clients.py
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime
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
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Many-to-Many 중간테이블과 관계
    employee_clients = relationship("EmployeeClient", back_populates="client", cascade="all, delete-orphan")
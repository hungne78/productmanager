# app/models/employee_clients.py

from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.db.base import Base
from sqlalchemy.sql import func

class EmployeeClient(Base):
    __tablename__ = "employee_clients"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)  # ✅ ON DELETE CASCADE 추가
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)  # ✅ 자동 생성
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)  # ✅ 자동 갱신

    employee = relationship("Employee", back_populates="employee_clients", overlaps="clients,employees")
    client = relationship("Client", back_populates="employee_clients", overlaps="clients,employees")




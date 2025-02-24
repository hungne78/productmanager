# app/models/employee_clients.py

from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.db.base import Base

class EmployeeClient(Base):
    __tablename__ = "employee_clients"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    start_date = Column(Date, default=date.today)  # 담당 시작일 (선택)
    end_date = Column(Date, nullable=True)         # 담당 종료일 (선택)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 관계 설정
    # employee = relationship("Employee", back_populates="employee_clients")
    # client = relationship("Client", back_populates="employee_clients")

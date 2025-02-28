# app/models/employee_clients.py

from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.db.base import Base

class EmployeeClient(Base):
    __tablename__ = "employee_clients"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)  # ✅ ON DELETE CASCADE 추가
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    employee = relationship("Employee", back_populates="employee_clients", overlaps="clients,employees")
    client = relationship("Client", back_populates="employee_clients", overlaps="clients,employees")




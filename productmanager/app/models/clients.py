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

    # employee_clients (다대다)
    # employee_clients = relationship("EmployeeClient", back_populates="client")
    # # orders (1대다)
    # orders = relationship("Order", back_populates="client")
    # # client visits (1대다)
    # client_visits = relationship("ClientVisit", back_populates="client")
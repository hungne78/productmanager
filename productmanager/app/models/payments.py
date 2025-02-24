# app/models/payments.py
from sqlalchemy import Column, BigInteger, Integer, DECIMAL, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    payment_date = Column(DateTime, default=datetime.now)
    amount = Column(DECIMAL(12,2), default=0)
    payment_method = Column(String(20), default="cash")
    note = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    client = relationship("Client", backref="payments") # optional

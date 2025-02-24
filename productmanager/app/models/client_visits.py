from sqlalchemy import Column, Integer, DateTime, ForeignKey
from datetime import datetime
from app.db.base import Base
from sqlalchemy.orm import relationship

class ClientVisit(Base):
    __tablename__ = "client_visits"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    # visit_datetime: 방문 날짜와 시간을 모두 기록 (UTC 기준)
    visit_datetime = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    # 방문 시 주문이 있으면 연결 (없으면 NULL)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    employee = relationship("Employee", back_populates="...") 
    client = relationship("Client", back_populates="client_visits")
    order = relationship("Order", back_populates="...")
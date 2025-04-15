# app/models/monthly_sales.py

from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class MonthlySales(Base):
    __tablename__ = "monthly_sales"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    total_sales = Column(Float, nullable=False, default=0.0)   # 월간 총 매출
    total_returns = Column(Float, nullable=False, default=0.0) # 월간 반품 금액 (선택)
    total_subsidy = Column(Float, nullable=False, default=0.0) # 월간 지원금 (선택)
    
    # 관계 (조회용)
    client = relationship("Client", lazy="joined")
    employee = relationship("Employee", lazy="joined")

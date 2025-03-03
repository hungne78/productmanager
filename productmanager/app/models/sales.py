# app/models/sales.py (모델 파일)
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from app.models.clients import Client
from app.models.employees import Employee

class Sales(Base):
    __tablename__ = "sales"
    __table_args__ = {'extend_existing': True} 

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)  # or nullable=False
    product = relationship("Product", back_populates="sales")
    # 🟢 새로 추가할 컬럼들
    category = Column(String(50), nullable=True)           # 카테고리
    total_quantity = Column(Integer, nullable=True, default=0)  # 해당 카테고리의 총 수량
    total_amount = Column(Float, nullable=True, default=0.0)    # 해당 카테고리의 총 금액
    sale_datetime = Column(DateTime, default=datetime.utcnow)   # 날짜 + 시간

    # 🟢 기존에 쓰던 직원/거래처 참조
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    client_id   = Column(Integer, ForeignKey("clients.id"), nullable=False)

    # (기존 product_id, quantity, unit_price, sale_date 등이 있다면
    #  카테고리 집계를 위해서는 사용 안 한다면 주석 혹은 삭제할 수도 있음)

    # 관계 설정
    employee = relationship("Employee", back_populates="sales")
    client   = relationship("Client", back_populates="sales")

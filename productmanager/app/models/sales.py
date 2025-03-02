from sqlalchemy import Column, Integer, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.clients import Client  # ✅ Client 명확하게 가져오기
from app.models.products import Product

class Sales(Base):
    """
    판매 데이터 모델
    """
    __tablename__ = "sales"
    __table_args__ = {'extend_existing': True} 

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)  # 직원 ID (옵션)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)  # 거래처 ID
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)  # 판매된 상품 ID
    quantity = Column(Integer, nullable=False)  # 판매 수량
    unit_price = Column(Float, nullable=False)  # 단가
    total_amount = Column(Float, nullable=False)  # 총 판매 금액 (수량 * 단가)
    sale_date = Column(Date, nullable=False)  # 판매 날짜

    # 관계 설정 (ForeignKey 연결)
    client = relationship("Client", back_populates="sales")
    employee = relationship("Employee", back_populates="sales")  # ✅ 관계 유지
    product = relationship("Product", back_populates="sales")
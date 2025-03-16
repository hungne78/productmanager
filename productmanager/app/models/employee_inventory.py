from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class EmployeeInventory(Base):
    __tablename__ = "employee_inventory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=0)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # ✅ 최신 업데이트 시간 추가
    # ✅ (employee_id, product_id) 조합이 유니크하도록 설정
    __table_args__ = (UniqueConstraint('employee_id', 'product_id', name='_employee_product_uc'),)

    employee = relationship("Employee", back_populates="inventory")
    product = relationship("Product", back_populates="inventory")

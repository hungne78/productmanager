from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class EmployeeInventory(Base):
    __tablename__ = "employee_inventory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True)  # ✅ 같은 제품 중복 불가
    quantity = Column(Integer, default=0)  # ✅ 차량에 있는 제품의 현재 재고 수량

    employee = relationship("Employee", back_populates="inventory")
    product = relationship("Product", back_populates="inventory")

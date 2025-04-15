# app/models/sales_record_archive.py

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from pytz import timezone

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환 """
    kst = timezone("Asia/Seoul")
    return datetime.utcnow().astimezone(kst)

class SalesRecordArchive(Base):
    __tablename__ = "sales_records_archive"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)

    quantity = Column(Integer, default=0)
    return_amount = Column(Float, nullable=False, default=0.0)
    subsidy_amount = Column(Float, nullable=False, default=0.0)
    sale_datetime = Column(DateTime, nullable=False, default=get_kst_now)

    # 관계 (단방향 참조만 사용)
    employee = relationship("Employee", lazy="joined")
    client = relationship("Client")
    product = relationship("Product")

from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz
from app.db.base import Base

KST = pytz.timezone("Asia/Seoul")

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환하여 반환 """
    return datetime.now(KST)

class EmployeeClient(Base):
    __tablename__ = "employee_clients"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)

    # ✅ KST 기준으로 저장
    start_date = Column(DateTime, default=get_kst_now, nullable=True)
    end_date = Column(DateTime, default=get_kst_now, nullable=True)

    # ✅ KST 기준으로 생성/수정 시간 저장
    created_at = Column(DateTime, default=get_kst_now, nullable=False)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now, nullable=False)

    employee = relationship("Employee", back_populates="employee_clients", overlaps="clients,employees")
    client = relationship("Client", back_populates="employee_clients", overlaps="clients,employees")

from sqlalchemy import Column, Integer, DateTime, ForeignKey
from datetime import datetime
from app.db.base import Base
from sqlalchemy.orm import relationship
from pytz import timezone

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환 """
    kst = timezone("Asia/Seoul")
    return datetime.utcnow().astimezone(kst)

class ClientVisit(Base):
    __tablename__ = "client_visits"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    # ✅ 방문 기록을 KST 기준으로 저장
    visit_datetime = Column(DateTime, nullable=False, default=get_kst_now)

    # 방문 시 주문이 있으면 연결 (없으면 NULL)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    # ✅ KST 기준으로 생성/수정 시간 저장
    created_at = Column(DateTime, default=get_kst_now)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now)

    # 관계 설정
    employee = relationship("Employee", back_populates="client_visits") 
    client = relationship("Client", back_populates="client_visits")

# app/models/client_visit_archive.py

from sqlalchemy import Column, Integer, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
import pytz

KST = pytz.timezone("Asia/Seoul")

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환하여 반환 """
    return datetime.now(KST)

class ClientVisitArchive(Base):
    __tablename__ = "client_visits_archive"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)

    visit_datetime = Column(DateTime(timezone=True), nullable=False, default=get_kst_now)
    visit_date = Column(Date, nullable=False, default=get_kst_now().date)
    visit_count = Column(Integer, nullable=False, default=1)

    # 단방향 관계 (아카이브는 대부분 단방향이면 충분함)
    employee = relationship("Employee", lazy="joined")
    client = relationship("Client")

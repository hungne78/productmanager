# app/models/lent.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.db.base import Base
from sqlalchemy.orm import relationship

class Lent(Base):
    __tablename__ = "lents"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    brand = Column(String(255), nullable=False)           # 단순 상표 이름
    serial_number = Column(String(255), nullable=False)     # 시리얼 번호
    year = Column(Integer, nullable=False)                  # 년식
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 필요하다면 Client와의 관계 설정도 추가 가능:
    client = relationship("Client", back_populates="lents")

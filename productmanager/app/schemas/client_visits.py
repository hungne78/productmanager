from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ClientVisitCreate(BaseModel):
    id: int 
    client_id: int
    # 방문 시각을 입력받거나 클라이언트에서 생략하면 서버의 default가 적용되도록 할 수 있음.
    visit_datetime: datetime  
    order_id: Optional[int] = None

class ClientVisitOut(BaseModel):
    id: int
    id_employee: int
    client_id: int
    visit_datetime: datetime
    order_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

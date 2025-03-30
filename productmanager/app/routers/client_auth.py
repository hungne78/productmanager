from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt

from app.models.clients import Client
from app.db.database import get_db


router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "1234"
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60 * 24  # 하루

class ClientLoginRequest(BaseModel):
    business_number: str
    password: str

class ClientLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

from fastapi.responses import JSONResponse

@router.post("/login")
def login_client(data: ClientLoginRequest, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.business_number == data.business_number).first()
    if not client:
        raise HTTPException(status_code=404, detail="해당 사업자번호의 거래처가 없습니다.")
    
    if not client.password_hash or not pwd_context.verify(data.password, client.password_hash):
        raise HTTPException(status_code=401, detail="비밀번호가 올바르지 않습니다.")

    token_data = {
        "sub": str(client.id),
        "type": "client",
        "exp": datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    }
    access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    # ✅ Flutter에서 필요한 정보 함께 내려주기
    return JSONResponse(content={
        "token": access_token,
        "client_id": client.id,
        "client_name": client.client_name
    })

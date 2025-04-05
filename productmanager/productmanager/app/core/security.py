# app/core/security.py
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "YOUR_SECRET_KEY"  # 실제 운영환경에서는 외부 .env로 분리
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 토큰 유효기간(예: 60분)

def get_password_hash(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):  # ✅ timedelta 사용 가능
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=1)  # ✅ 기본 만료 시간 1일 설정
    to_encode.update({"exp": expire.timestamp()})

    print(f"🔹 [DEBUG] JWT 생성 - SECRET_KEY: {settings.SECRET_KEY}, ALGORITHM: {settings.ALGORITHM}")

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
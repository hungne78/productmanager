FROM python:3.11-slim

WORKDIR /app

# requirements.txt와 app 폴더를 모두 복사
COPY requirements.txt .
COPY app ./app
COPY .env .env
COPY app/utils/firebase_key.json app/utils/firebase_key.json

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

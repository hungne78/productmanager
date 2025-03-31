# push_service.py
import os
import firebase_admin
from firebase_admin import credentials, messaging

# 서비스 계정 초기화 (최초 한 번만 실행)
if not firebase_admin._apps:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(base_dir, "firebase_key.json")

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

def send_push(fcm_token: str, client_name: str, client_id: int, order_id: int):
    message = messaging.Message(
        notification=messaging.Notification(
            title=f"{client_name} 주문 도착",
            body="프랜차이즈 주문이 도착했습니다.",
        ),
        token=fcm_token,
        data={
            "type": "new_franchise_order",
            "client_id": str(client_id),
            "client_name": client_name,
            "order_id": str(order_id)
        }
    )

    try:
        response = messaging.send(message)
        print("✅ FCM 전송 완료:", response)
        return response
    except Exception as e:
        print("❌ FCM 전송 실패:", e)
        return None


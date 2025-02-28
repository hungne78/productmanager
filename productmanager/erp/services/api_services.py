import requests
from datetime import datetime
import json
from datetime import date
BASE_URL = "http://127.0.0.1:8000"  # FastAPI 서버 주소
HEADERS = {"Content-Type": "application/json"}

# 🔹 로그인관련 API 함수들
# 🔹 직원 로그인 (JWT 토큰 반환)
def api_login_employee(emp_id, password):
    """ 직원 로그인 (JWT 반환) """
    global TOKEN
    try:
        response = requests.post(f"{BASE_URL}/employees/login", json={"id": emp_id, "password": password}, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        TOKEN = data["token"]  # 로그인 성공 시 토큰 저장
        return data
    except requests.RequestException as e:
        print(f"❌ 직원 로그인 실패: {e}")
        return None

# 🔹 로그인 후 API 호출 시 JWT 토큰 포함
def get_auth_headers():
    """ JWT 토큰을 포함한 헤더 반환 """
    if TOKEN:
        return {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    return HEADERS

# 🔹 직원 관련 API 함수들

def api_unassign_employee_client(token, client_id, emp_id):
    """ 특정 직원과 거래처의 연결을 해제하는 API 요청 (POST 사용) """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{BASE_URL}/employee_clients/unassign"
    data = {"client_id": client_id, "employee_id": emp_id}

    try:
        # ✅ DELETE 대신 POST 요청을 사용하여 전송
        response = requests.post(url, json=data, headers=headers)
        print(f"🚀 담당 직원 해제 요청: {url}")
        print(f"🚀 서버 응답 코드: {response.status_code}")
        print(f"🚀 서버 응답 내용: {response.text}")

        response.raise_for_status()
        return response  # ✅ API 응답 반환

    except requests.RequestException as e:
        print(f"❌ 담당 직원 해제 실패: {e}")
        return None





def api_fetch_employees(token, name_keyword=""):
    url = f"{BASE_URL}/employees/"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"search": name_keyword} if name_keyword else {}

    try:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()  # ✅ JSON 변환 후 반환
    except Exception as e:
        print("api_fetch_employees error:", e)
        return []

def api_create_employee(token, data):
    """ 직원 추가 """
    try:
        url = f"{BASE_URL}/employees/"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        return requests.post(url, json=data, headers=headers)
    except requests.RequestException as e:
        print(f"❌ 직원 추가 실패: {e}")
        return None

def api_update_employee(token, emp_id, data):
    """ 직원 정보 수정 """
    try:
        url = f"{BASE_URL}/employees/{emp_id}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        return requests.put(url, json=data, headers=headers)
    except requests.RequestException as e:
        print(f"❌ 직원 수정 실패: {e}")
        return None

def api_delete_employee(token, emp_id):
    """ 직원 삭제 """
    try:
        url = f"{BASE_URL}/employees/{emp_id}"
        headers = {"Authorization": f"Bearer {token}"}
        return requests.delete(url, headers=headers)
    except requests.RequestException as e:
        print(f"❌ 직원 삭제 실패: {e}")
        return None
def api_fetch_employee_vehicle_info(employee_id):
    """
    직원 차량 정보 GET /employee_vehicles?emp_id=...
    (실제로는 그런 endpoint를 만들거나, 필터 구현해야 함)
    """
    url = f"{BASE_URL}/employee_vehicles/"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        vehicles = resp.json()
        found = [v for v in vehicles if v.get("id") == employee_id]
        return found[0] if found else None
    except Exception as e:
        print("api_fetch_employee_vehicle_info error:", e)
        return None
    
def api_fetch_vehicle(token, emp_id):
    """ 특정 직원의 차량 정보 조회 """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{BASE_URL}/employee_vehicles/{emp_id}"
    print(f"🚀 차량 정보 요청: {url}")  # 요청 URL 로그 출력
    try:
        response = requests.get(url, headers=headers)
        print(f"🚀 서버 응답 코드: {response.status_code}")  # 응답 코드 출력
        print(f"🚀 서버 응답 내용: {response.text}")  # 응답 데이터 출력

        response.raise_for_status()

        # ✅ 응답을 JSON 형식으로 변환하여 반환
        return response.json()

    except requests.RequestException as e:
        print(f"❌ 차량 정보 조회 실패: {e}")
        return None




def api_create_vehicle(token, data):
    """ 직원 차량 정보 등록/수정 """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        response = requests.post(f"{BASE_URL}/employee_vehicles/", json=data, headers=headers)
        print(f"🚀 차량 등록 요청: {response.status_code}")  # 응답 코드 출력
        print(f"🚀 서버 응답 내용: {response.text}")  # 응답 내용 출력

        if response is None:
            raise ValueError("❌ 서버 응답이 없습니다. (None)")

        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"❌ 차량 정보 등록 실패: {e}")
        return None


# 🔹 거래처 관련 API 함수들

def api_fetch_lent_freezers(token, client_id):
    """
    특정 거래처의 대여 냉동고 정보를 조회하는 API 요청 함수
    """
    url = f"{BASE_URL}/lents/{client_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()  # JSON 데이터 반환
    except requests.RequestException as e:
        print(f"❌ 대여 냉동고 조회 실패: {e}")
        return []
    
def api_fetch_clients(token):
    """ 전체 거래처 목록 조회 """
    try:
        url = f"{BASE_URL}/clients/"
        headers = {"Authorization": f"Bearer {token}"}
        return requests.get(url, headers=headers)
    except requests.RequestException as e:
        print(f"❌ 거래처 목록 조회 실패: {e}")
        return []

def api_create_client(token, data):
    """ 거래처 추가 """
    try:
        url = f"{BASE_URL}/clients/"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        return requests.post(url, json=data, headers=headers)
    except requests.RequestException as e:
        print(f"❌ 거래처 추가 실패: {e}")
        return None

import requests

def api_update_client(token, client_id, data):
    """
    거래처 정보를 업데이트하는 API 요청 함수
    """
    url = f"{BASE_URL}/clients/{client_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.put(url, json=data, headers=headers)

        # ✅ 응답 상태 코드 출력
        print(f"📡 요청 URL: {url}")
        print(f"📡 요청 데이터: {data}")
        print(f"📡 응답 코드: {resp.status_code}")
        print(f"📡 응답 본문: {resp.text}")

        resp.raise_for_status()
        return resp
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 오류 발생: {e}")
    except requests.exceptions.ConnectionError as e:
        print("❌ 서버에 연결할 수 없습니다.")
    except requests.exceptions.Timeout as e:
        print("❌ 요청 시간이 초과되었습니다.")
    except requests.exceptions.RequestException as e:
        print(f"❌ 거래처 업데이트 실패: {e}")

    return None


def api_delete_client(token, client_id):
    """ 특정 거래처 삭제 요청 """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{BASE_URL}/clients/{client_id}"

    try:
        response = requests.delete(url, headers=headers)
        print(f"🚀 거래처 삭제 요청: {url}")
        print(f"🚀 서버 응답 코드: {response.status_code}")
        print(f"🚀 서버 응답 내용: {response.text}")

        response.raise_for_status()
        return response

    except requests.RequestException as e:
        print(f"❌ 거래처 삭제 실패: {e}")
        return None

def api_assign_employee_client(token, client_id, employee_id):
    """ 거래처에 직원 배정 """
    url = f"{BASE_URL}/employee_clients/"
    
    # ✅ 오늘 날짜를 기본 `start_date`로 설정
    today_date = date.today().isoformat()

    data = {
        "client_id": client_id,
        "employee_id": employee_id,
        "start_date": today_date,  # ✅ 기본값 추가
        "end_date": None           # ✅ 기본값 추가
    }

    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        return requests.post(url, json=data, headers=headers)
    except requests.RequestException as e:
        print(f"❌ 직원 배정 실패: {e}")
        return None



def api_fetch_employee_clients_all(token):
    """ 모든 직원-거래처 관계 조회 """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{BASE_URL}/employee_clients/"
    print(f"🚀 직원-거래처 관계 요청: {url}")  # 요청 URL 로그 출력
    try:
        response = requests.get(url, headers=headers)
        print(f"🚀 서버 응답 코드: {response.status_code}")  # 응답 코드 출력
        print(f"🚀 서버 응답 내용: {response.text}")  # 응답 데이터 출력

        response.raise_for_status()

        # ✅ 응답이 문자열 또는 bytes라면 JSON 변환
        if isinstance(response.text, str):
            return json.loads(response.text)

        return response.json()  # ✅ JSON 반환

    except requests.RequestException as e:
        print(f"❌ 직원-거래처 관계 조회 실패: {e}")
        return []


# 🔹 상품 관련 API 함수들
def api_update_product_by_id(token, product_id, data):
    url = f"{BASE_URL}/products/{product_id}"  # ✅ 상품 ID로 업데이트 요청
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.put(url, json=data, headers=headers)
def api_delete_product_by_id(token, product_id):
    url = f"{BASE_URL}/products/{product_id}"  # ✅ 상품 ID로 삭제 요청
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)
def api_update_product_by_name(token, product_name, data):
    url = f"{BASE_URL}/products/name/{product_name}"  # ✅ 상품명으로 업데이트 요청
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.put(url, json=data, headers=headers)



def api_fetch_products(token, search_name=None):
    """ 상품 목록을 가져오는 API 요청 함수 (이름 검색 가능) """
    url = f"{BASE_URL}/products/"
    
    # ✅ 검색어가 있으면 URL에 `?search=이름` 추가
    if search_name:
        url += f"?search={search_name}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        print("📡 [상품 목록 조회 요청]")  # ✅ 디버깅 로그 추가
        print(f"📡 요청 URL: {url}")

        response = requests.get(url, headers=headers)

        print(f"📡 응답 코드: {response.status_code}")  # ✅ 응답 코드 확인
        print(f"📡 응답 본문: {response.text}")  # ✅ 응답 본문 출력

        response.raise_for_status()
        return response.json()  # ✅ JSON 데이터 반환

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 오류 발생: {e}")
    except requests.exceptions.ConnectionError as e:
        print("❌ 서버에 연결할 수 없습니다.")
    except requests.exceptions.Timeout as e:
        print("❌ 요청 시간이 초과되었습니다.")
    except requests.exceptions.RequestException as e:
        print(f"❌ 상품 목록 조회 실패: {e}")

    return {}  # ✅ 실패 시 빈 `dict` 반환하여 오류 방지





def api_create_product(token, data):
    """ 상품 추가 API 요청 함수 """
    url = f"{BASE_URL}/products/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        print("📡 [상품 등록 요청]")  # ✅ 디버깅 로그 추가
        print(f"📡 요청 URL: {url}")
        print(f"📡 요청 데이터: {data}")

        response = requests.post(url, json=data, headers=headers)

        print(f"📡 응답 코드: {response.status_code}")  # ✅ 응답 코드 확인
        print(f"📡 응답 본문: {response.text}")  # ✅ 응답 본문 출력

        response.raise_for_status()
        return response

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 오류 발생: {e}")
    except requests.exceptions.ConnectionError as e:
        print("❌ 서버에 연결할 수 없습니다.")
    except requests.exceptions.Timeout as e:
        print("❌ 요청 시간이 초과되었습니다.")
    except requests.exceptions.RequestException as e:
        print(f"❌ 상품 추가 실패: {e}")

    return None



def api_update_product(token, product_id, data):
    """ 상품 정보 수정 API 요청 함수 """
    url = f"{BASE_URL}/products/{product_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        print("📡 [상품 수정 요청]")  # ✅ 디버깅 로그 추가
        print(f"📡 요청 URL: {url}")
        print(f"📡 요청 데이터: {data}")

        response = requests.put(url, json=data, headers=headers)

        print(f"📡 응답 코드: {response.status_code}")  # ✅ 응답 코드 확인
        print(f"📡 응답 본문: {response.text}")  # ✅ 응답 본문 출력

        response.raise_for_status()
        return response

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 오류 발생: {e}")
    except requests.exceptions.ConnectionError as e:
        print("❌ 서버에 연결할 수 없습니다.")
    except requests.exceptions.Timeout as e:
        print("❌ 요청 시간이 초과되었습니다.")
    except requests.exceptions.RequestException as e:
        print(f"❌ 상품 수정 실패: {e}")

    return None



def api_delete_product(token, product_id):
    """ 상품 삭제 API 요청 함수 """
    url = f"{BASE_URL}/products/{product_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        print(f"📡 [상품 삭제 요청] ID: {product_id}")  # ✅ 디버깅 로그 추가
        response = requests.delete(url, headers=headers)

        print(f"📡 응답 코드: {response.status_code}")  # ✅ 응답 코드 확인
        print(f"📡 응답 본문: {response.text}")  # ✅ 응답 본문 출력

        response.raise_for_status()
        return response

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 오류 발생: {e}")
    except requests.exceptions.ConnectionError as e:
        print("❌ 서버에 연결할 수 없습니다.")
    except requests.exceptions.Timeout as e:
        print("❌ 요청 시간이 초과되었습니다.")
    except requests.exceptions.RequestException as e:
        print(f"❌ 상품 삭제 실패: {e}")

    return None


# 직원방문지도탭
def api_fetch_employee_visits(employee_id):
    """ 특정 직원이 방문한 거래처 목록 조회 """
    url = f"{BASE_URL}/client_visits/today_visits?employee_id={employee_id}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ 직원 방문 정보 가져오기 실패: {e}")
        return []

def api_fetch_client_coordinates(client_id):
    """ 특정 거래처의 GPS 좌표 조회 """
    url = f"{BASE_URL}/clients/{client_id}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        client_data = response.json()
        return client_data.get("latitude"), client_data.get("longitude"), client_data.get("client_name")
    except requests.RequestException as e:
        print(f"❌ 거래처 좌표 가져오기 실패: {e}")
        return None

#주문 관련api
# 🔹 주문 목록 조회
def api_fetch_orders():
    """ 전체 주문 목록 조회 """
    try:
        response = requests.get(f"{BASE_URL}/orders/", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ 주문 목록 조회 실패: {e}")
        return []

# 🔹 특정 주문 조회
def api_fetch_order(order_id):
    """ 특정 주문 조회 """
    try:
        response = requests.get(f"{BASE_URL}/orders/{order_id}", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ 주문 조회 실패: {e}")
        return None

# 🔹 주문 추가
def api_create_order(data):
    """ 주문 추가 """
    try:
        response = requests.post(f"{BASE_URL}/orders/", json=data, headers=HEADERS)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"❌ 주문 추가 실패: {e}")
        return None

# 🔹 주문 수정 (예: 상태 변경, 품목 수정 등)
def api_update_order(order_id, data):
    """ 주문 정보 수정 """
    try:
        response = requests.put(f"{BASE_URL}/orders/{order_id}", json=data, headers=HEADERS)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"❌ 주문 수정 실패: {e}")
        return None

# 🔹 주문 삭제
def api_delete_order(order_id):
    """ 주문 삭제 """
    try:
        response = requests.delete(f"{BASE_URL}/orders/{order_id}", headers=HEADERS)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"❌ 주문 삭제 실패: {e}")
        return None

# 🔹 특정 직원이 담당한 주문 목록 조회
def api_fetch_employee_orders(employee_id):
    """ 특정 직원이 담당한 주문 조회 """
    try:
        response = requests.get(f"{BASE_URL}/orders/employee/{employee_id}", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ 직원 주문 조회 실패: {e}")
        return []

# 🔹 특정 거래처의 주문 목록 조회
def api_fetch_client_orders(client_id):
    """ 특정 거래처의 주문 조회 """
    try:
        response = requests.get(f"{BASE_URL}/orders/client/{client_id}", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ 거래처 주문 조회 실패: {e}")
        return []

# 🔹 주문 상태 변경
def api_update_order_status(order_id, status):
    """ 주문 상태 변경 """
    try:
        response = requests.patch(f"{BASE_URL}/orders/{order_id}/status", json={"status": status}, headers=HEADERS)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"❌ 주문 상태 변경 실패: {e}")
        return None
    
# 구매관련

# 🔹 구매 목록 조회
def api_fetch_purchases(token):
    """
    매입 내역을 서버에서 가져오는 API 요청
    """
    url = f"{BASE_URL}/purchases"  # Corrected endpoint for purchases
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 오류 발생 시 예외 처리
        return response.json()  # Return the purchase data from the backend
    except requests.RequestException as e:
        print(f"API 요청 실패: {e}")
        return []

# 🔹 특정 구매 조회
def api_fetch_purchase(purchase_id):
    """ 특정 구매 조회 """
    try:
        response = requests.get(f"{BASE_URL}/purchases/{purchase_id}", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ 구매 조회 실패: {e}")
        return None

# 🔹 구매 추가
def api_create_purchase(data):
    """ 구매 추가 """
    try:
        response = requests.post(f"{BASE_URL}/purchases/", json=data, headers=HEADERS)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"❌ 구매 추가 실패: {e}")
        return None

# 🔹 구매 수정 (예: 수량 변경, 공급업체 변경 등)
def api_update_purchase(purchase_id, data):
    """ 구매 정보 수정 """
    try:
        response = requests.put(f"{BASE_URL}/purchases/{purchase_id}", json=data, headers=HEADERS)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"❌ 구매 수정 실패: {e}")
        return None

# 🔹 구매 삭제
def api_delete_purchase(purchase_id):
    """ 구매 삭제 """
    try:
        response = requests.delete(f"{BASE_URL}/purchases/{purchase_id}", headers=HEADERS)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"❌ 구매 삭제 실패: {e}")
        return None

# 🔹 특정 공급업체의 구매 목록 조회
def api_fetch_supplier_purchases(supplier_id):
    """ 특정 공급업체의 구매 조회 """
    try:
        response = requests.get(f"{BASE_URL}/purchases/supplier/{supplier_id}", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ 공급업체 구매 조회 실패: {e}")
        return []

# 🔹 특정 상품의 구매 목록 조회
def api_fetch_product_purchases(product_id):
    """ 특정 상품의 구매 조회 """
    try:
        response = requests.get(f"{BASE_URL}/purchases/product/{product_id}", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ 상품 구매 조회 실패: {e}")
        return []

# 🔹 구매 상태 변경
def api_update_purchase_status(purchase_id, status):
    """ 구매 상태 변경 """
    try:
        response = requests.patch(f"{BASE_URL}/purchases/{purchase_id}/status", json={"status": status}, headers=HEADERS)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"❌ 구매 상태 변경 실패: {e}")
        return None
def api_update_product_stock(token, product_id, stock_increase):
    """
    상품 재고 업데이트 (매입 후 증가)
    """
    url = f"{BASE_URL}/products/{product_id}/stock?stock_increase={stock_increase}"  # ✅ Query 방식으로 변경
    headers = {"Authorization": f"Bearer {token}"}

    print(f"📌 API 요청: {url}")  # 🔍 디버깅 출력

    try:
        response = requests.patch(url, headers=headers)  # ✅ Query Parameter 방식으로 요청
        response.raise_for_status()
        return response
    except requests.HTTPError as e:
        print(f"❌ 서버 오류: {e.response.status_code} {e.response.text}")
    except requests.RequestException as e:
        print(f"❌ API 요청 실패: {e}")
    return None
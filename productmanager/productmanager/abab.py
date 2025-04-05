#!/usr/bin/env python
import sys
import json
import requests
import openpyxl
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QListWidget,
    QLabel, QLineEdit, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QGridLayout, QSpinBox, QScrollArea,
    QMessageBox, QFileDialog, QHeaderView, QComboBox, QInputDialog, QDateEdit, QGroupBox, QAction, QStackedWidget, QToolBar
    
)
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QIcon, QColor,QFont, QResizeEvent,QFontMetrics
import os
from datetime import datetime
from PyQt5.QtWebEngineWidgets import QWebEngineView
import folium
import io
# ----------------------------
# Global Variables and API Base
# ----------------------------
BASE_URL = "http://127.0.0.1:8000"  # 실제 서버 URL
global_token = None  # 로그인 토큰 (Bearer 인증)

# ----------------------------
# 다크 테마
# ----------------------------
def load_dark_theme():
    return """
    QMainWindow {
        background-color: #2B2B2B;
    }
    QToolBar {
        background-color: #3C3F41;
        border-bottom: 2px solid #555;
    }
    QToolBar QToolButton {
        color: white;
        padding: 8px;
    }
    QWidget {
        background-color: #2B2B2B;
        color: white;
    }
    QLineEdit {
        background-color: #3C3F41;
        color: white;
        border: 1px solid #555;
        padding: 5px;
    }
    QPushButton {
        background-color: #555;
        color: white;
        border-radius: 5px;
        padding: 5px;
    }
    QPushButton:hover {
        background-color: #777;
    }
    QLabel {
        color: white;
    }
    QTableWidget {
        background-color: #2B2B2B;
        color: white;
        gridline-color: #555;
    }
    QHeaderView::section {
        background-color: #3C3F41;
        color: white;
        border: 1px solid #555;name_keyword
    }
    """

# ----------------------------
# API Service Functions
# ----------------------------
def api_login(employee_id, password):
    """
    로그인 예시: POST /login
    """
    url = f"{BASE_URL}/login"
    data = {"id": employee_id, "password": password}
    headers = {"Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

# 직원
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

def api_delete_product_by_name(token, product_name):
    url = f"{BASE_URL}/products/name/{product_name}"  # ✅ 상품명으로 삭제 요청
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

def api_create_employee(token, data):
    url = f"{BASE_URL}/employees/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_update_employee(token, emp_id, data):
    url = f"{BASE_URL}/employees/{emp_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.put(url, json=data, headers=headers)

def api_delete_employee(token, emp_id):
    url = f"{BASE_URL}/employees/{emp_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

def api_import_employees_from_excel(token, filepath):
    headers = {"Authorization": f"Bearer {token}"}
    wb = openpyxl.load_workbook(filepath)
    sheet = wb.active
    for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
        if row_idx == 1:  # header
            continue
        emp_number, emp_pw, emp_name, emp_phone, emp_role = row
        data = {
            "employee_number": str(emp_number),
            "password": str(emp_pw),
            "name": str(emp_name),
            "phone": str(emp_phone),
            "role": str(emp_role)
        }
        resp = requests.post(f"{BASE_URL}/employees", json=data, headers=headers)
        resp.raise_for_status()

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
    
# 거래처
def api_fetch_clients(token):
    url = f"{BASE_URL}/clients/"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_create_client(token, data):
    url = f"{BASE_URL}/clients/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_delete_client(token, client_id):
    url = f"{BASE_URL}/clients/{client_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

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
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        print(f"❌ 거래처 업데이트 실패: {e}")
        return None

# 제품
def api_fetch_products(token, search_name=None):
    """
    상품 목록을 가져오는 API 요청 (검색어 적용 가능)
    """
    url = f"{BASE_URL}/products/"
    headers = {"Authorization": f"Bearer {token}"}
    params = {}

    if search_name:
        params["name"] = search_name  
   

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        return {"status_code": response.status_code, "data": response.json()}  # ✅ `status_code` 포함
    except requests.RequestException as e:
        print(f"❌ 상품 목록 조회 실패: {e}")
        return {"status_code": 500, "data": {}}  # ✅ 오류 발생 시 `500` 코드 반환




def api_create_product(token, data):
    url = f"{BASE_URL}/products/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_update_product(token, prod_id, data):
    url = f"{BASE_URL}/products/{prod_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.put(url, json=data, headers=headers)

def api_delete_product(token, prod_id):
    url = f"{BASE_URL}/products/{prod_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

# def api_fetch_all_products(token):
#     """
#     전체 상품 목록을 가져오는 함수 (OrdersTab 용)
#     """
#     url = f"{BASE_URL}/products/all"
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     }

#     try:
#         response = requests.get(url, headers=headers)
#         response.raise_for_status()
#         return response.json()  # ✅ JSON 응답 반환
#     except requests.RequestException as e:
#         print(f"❌ 전체 상품 목록 조회 실패: {e}")
#         return []

# 주문
def api_fetch_orders(token):
    url = f"{BASE_URL}/orders/"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_create_order(token, data):
    url = f"{BASE_URL}/orders/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_update_order(token, order_id, data):
    url = f"{BASE_URL}/orders/{order_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.put(url, json=data, headers=headers)

def api_delete_order(token, order_id):
    url = f"{BASE_URL}/orders/{order_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

# 매출
def api_fetch_sales(token):
    url = f"{BASE_URL}/sales"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_create_sales(token, data):
    url = f"{BASE_URL}/sales"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_delete_sales(token, sales_id):
    url = f"{BASE_URL}/sales/{sales_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

# 직원-거래처
def api_assign_employee_client(token, employee_id, client_id):
    url = f"{BASE_URL}/employee_clients/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"employee_id": employee_id, "client_id": client_id}
    return requests.post(url, json=data, headers=headers)

def api_fetch_employee_clients_all(token):
    url = f"{BASE_URL}/employee_clients/"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

# 직원 차량
def api_fetch_vehicle(token):
    url = f"{BASE_URL}/employee_vehicles/"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_create_vehicle(token, data):
    url = f"{BASE_URL}/employee_vehicles/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_update_vehicle(token, vehicle_id, data):
    url = f"{BASE_URL}/employee_vehicles/{vehicle_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.put(url, json=data, headers=headers)

def api_delete_vehicle(token, vehicle_id):
    url = f"{BASE_URL}/employee_vehicles/{vehicle_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

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


# def api_fetch_brand_products(token, brand_id):
#     """
#     특정 브랜드 ID에 해당하는 상품 목록을 가져오는 함수.

#     :param brand_id: 브랜드 ID
#     :param token: 인증 토큰 (JWT)
#     :return: 해당 브랜드의 상품 목록 (JSON)
#     """
#     url = f"{BASE_URL}/products/"
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     }

#     params = {"brand_id": int(brand_id) } # ✅ brand_id를 query parameter로 추가

#     try:
#         response = requests.get(url, headers=headers, params=params)  # ✅ params로 전달
#         response.raise_for_status()  # ✅ 오류 발생 시 예외 처리
#         data = response.json()

#         if isinstance(data, dict):  # ✅ 응답이 list인지 확인
#             return data
#         else:
#             print("❌ 응답 형식 오류: 리스트가 아님", data)
#             return []

#     except requests.RequestException as e:
#         print(f"❌ 브랜드 상품 목록 조회 실패: {e}")
#         return []
def fetch_employee_visits(employee_id):
    """
    직원 ID를 받아서 해당 직원이 오늘 방문한 거래처 목록 조회
    """
    global global_token
    url = f"{BASE_URL}/client_visits/today_visits?employee_id={employee_id}"
    headers = {"Authorization": f"Bearer {global_token}"}

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        visits = resp.json()

        # 필요 데이터만 정리 (client_id, visit_datetime, today_sales)
        processed_visits = []
        for visit in visits:
            processed_visits.append({
                "client_id": visit["client_id"],
                "visit_datetime": visit["visit_datetime"],
                "today_sales": visit["today_sales"]
            })

        return processed_visits
    except Exception as e:
        print(f"❌ 직원 방문 정보 가져오기 실패: {e}")
        return []

def fetch_client_coordinates(client_id):
    """
    거래처 ID를 받아서 해당 거래처의 위도, 경도를 가져옴
    """
    global global_token
    url = f"{BASE_URL}/clients/{client_id}"
    headers = {"Authorization": f"Bearer {global_token}"}

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        client_data = resp.json()
        return (
            client_data.get("latitude"), 
            client_data.get("longitude"), 
            client_data.get("client_name")
        )
    except Exception as e:
        print(f"❌ 거래처 좌표 가져오기 실패: {e}")
        return None

def api_update_product(token, product_id, data):
    """
    상품의 재고 업데이트 (매입 후 반영)
    """
    url = f"{BASE_URL}/products/{product_id}"  # 올바른 URL 확인
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()  # Return the updated product data from the backend
    except requests.RequestException as e:
        print(f"API 요청 실패: {e}")
        return None


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




class EmployeeMapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)
        self.setLayout(layout)

    def update_map(self, client_locations):
        """
        거래처 위치 데이터를 받아 지도 업데이트
        client_locations = [(위도, 경도, "거래처명"), ...]
        """
        if not client_locations:
            return
        
        # 기본 지도 위치 설정 (첫 번째 거래처 위치를 기준으로)
        lat, lon = client_locations[0][:2]
        map_object = folium.Map(location=[lat, lon], zoom_start=13)
        
        for lat, lon, name in client_locations:
            folium.Marker([lat, lon], popup=name).add_to(map_object)

        # 지도 HTML 저장 및 표시
        map_html = io.BytesIO()
        map_object.save(map_html, close_file=False)
        self.map_view.setHtml(map_html.getvalue().decode())



class EmployeesMapTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """
        직원 검색 + 지도 UI 초기화
        """
        main_layout = QVBoxLayout()

        
        # 지도 UI
        self.map_view = QWebEngineView()
        main_layout.addWidget(self.map_view)

        self.setLayout(main_layout)

       

        # 기본 지도 설정 (서울·경기권 중심)
        self.load_default_map()

    def load_default_map(self):
        """
        기본 지도 설정 (서울·경기권 중심)
        """
        map_object = folium.Map(location=[37.5665, 126.9780], zoom_start=11)  # 서울 시청 기준
        self.display_map(map_object)

    def do_search(self, keyword):
        """
        MainApp에서 직원 검색 시 호출되는 함수 (기존 검색창을 활용)
        """
        if not keyword:
            QMessageBox.warning(self, "경고", "검색어를 입력하세요.")
            return

        global global_token
        employees = api_fetch_employees(global_token, keyword)

        if not employees:
            QMessageBox.information(self, "검색 결과", "검색 결과가 없습니다.")
            return

        if len(employees) == 1:
            self.display_employee_map(employees[0])
        else:
            dialog = EmployeeSelectionDialog(employees, parent=self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_employee:
                self.display_employee_map(dialog.selected_employee)
                
    def search_employee(self):
        """
        직원 검색 후 해당 직원이 방문한 거래처를 지도에 표시
        """
        keyword = self.search_edit.text().strip()
        if not keyword:
            QMessageBox.warning(self, "경고", "직원 이름을 입력하세요.")
            return

        global global_token
        employees = api_fetch_employees(global_token, keyword)

        if not employees:
            QMessageBox.information(self, "검색 결과", "검색 결과가 없습니다.")
            return

        if len(employees) == 1:
            self.display_employee_map(employees[0])
        else:
            dialog = EmployeeSelectionDialog(employees, parent=self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_employee:
                self.display_employee_map(dialog.selected_employee)

    def display_employee_map(self, employee):
        """
        직원의 방문 거래처를 지도에 표시
        """
        visits = fetch_employee_visits(employee["id"])

        # 방문 데이터 정렬 (방문시간 기준)
        visits.sort(key=lambda x: x["visit_datetime"])  

        client_locations = []
        for idx, visit in enumerate(visits, start=1):  # 방문 순서 부여
            client_id = visit["client_id"]
            coords = fetch_client_coordinates(client_id)
            if coords:
                # 방문순서 포함 (순번, 거래처 이름, 방문시간, 당일 매출)
                client_locations.append((idx, coords[0], coords[1], coords[2], visit["visit_datetime"], visit["today_sales"]))

        if client_locations:
            self.update_map(client_locations)
        else:
            QMessageBox.information(self, "정보", f"{employee['name']} 직원의 방문 거래처가 없습니다.")

    def update_map(self, client_locations):
        """
        방문한 거래처들의 위치를 지도에 표시
        """
        if not client_locations:
            return

        # 기본 지도 설정 (서울·경기권 중심)
        map_object = folium.Map(location=[37.5665, 126.9780], zoom_start=10)

        for order, lat, lon, name, visit_time, today_sales in client_locations:
            popup_content = f"""
            <b>방문 순서:</b> {order}<br>
            <b>거래처명:</b> {name}<br>
            <b>방문 시간:</b> {visit_time}<br>
            <b>당일 매출:</b> {today_sales}원
            """
            folium.Marker([lat, lon], popup=popup_content, icon=folium.Icon(color="blue")).add_to(map_object)

        self.display_map(map_object)

    def display_map(self, map_object):
        """
        지도 HTML 변환 후 표시
        """
        map_html = io.BytesIO()
        map_object.save(map_html, close_file=False)
        self.map_view.setHtml(map_html.getvalue().decode())


# ----------------------------
# 로그인 다이얼로그
# ----------------------------
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("로그인")
        self.setFixedSize(300, 150)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("사원 ID (예: 1)")
        form_layout.addRow("사원 ID:", self.id_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("비밀번호")
        self.password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("비밀번호:", self.password_edit)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.login_btn = QPushButton("로그인")
        self.login_btn.clicked.connect(self.attempt_login)
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.login_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def attempt_login(self):
        global global_token
        id_text = self.id_edit.text().strip()
        password = self.password_edit.text().strip()
        if not id_text or not password:
            QMessageBox.warning(self, "경고", "사원 ID와 비밀번호를 입력하세요.")
            return
        try:
            employee_id = int(id_text)
        except ValueError:
            QMessageBox.warning(self, "경고", "사원 ID는 정수로 입력하세요.")
            return

        if employee_id != 1:
            QMessageBox.critical(self, "접근 거부", "Only ID=1 is allowed in this test!")
            return
        try:
            resp = api_login(employee_id, password)
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("token")
                if not token:
                    QMessageBox.critical(self, "오류", "로그인 응답에 token이 없습니다.")
                    return
                global_token = token
                QMessageBox.information(self, "성공", "로그인 성공!")
                self.accept()
            else:
                QMessageBox.critical(self, "로그인 실패", f"로그인 실패: {resp.status_code}\n{resp.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"로그인 중 오류: {e}")

class LentDialog(QDialog):
    def __init__(self, lent_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("대여 냉동고 목록")
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["상표", "시리얼 번호", "년식"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.table)

        self.populate_table(lent_data)

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def populate_table(self, lent_data):
        self.table.setRowCount(len(lent_data))
        for i, record in enumerate(lent_data):
            self.table.setItem(i, 0, QTableWidgetItem(record.get("brand", "")))
            self.table.setItem(i, 1, QTableWidgetItem(record.get("serial_number", "")))
            self.table.setItem(i, 2, QTableWidgetItem(str(record.get("year", ""))))

##############################################################################
# 왼쪽 정보창도 표 형태로 만들고, 아래 "신규등록", "수정" 버튼
##############################################################################
class BaseLeftTableWidget(QWidget):
    def __init__(self, row_count, labels, parent=None):
        super().__init__(parent)
        self.row_count = row_count
        self.labels = labels  # ["ID","Name", ...]

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # ✅ `QTableWidget` 추가
        self.table_info = QTableWidget(self.row_count, 2)
        
        self.table_info.setHorizontalHeaderLabels(["항목", "값"])
        self.table_info.verticalHeader().setVisible(False)
        self.table_info.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_info.setEditTriggers(QTableWidget.DoubleClicked)  # 더블클릭 편집 가능
        
        if not hasattr(self, "table_info") or self.table_info is None:
            print("Error: table_info is None or deleted")
            return
        for r in range(self.row_count):
            # 항목명 셀
            item_label = QTableWidgetItem(self.labels[r])
            item_label.setFlags(Qt.ItemIsEnabled)  # 편집불가
            self.table_info.setItem(r, 0, item_label)
            # 값은 비워둠 (나중에 setItem(r,1,...) 혹은 setText)
            self.table_info.setItem(r, 1, QTableWidgetItem(""))

        main_layout.addWidget(self.table_info)

        # 버튼 (신규등록, 수정)
        btn_layout = QHBoxLayout()
        self.btn_new = QPushButton("신규등록")
        self.btn_edit = QPushButton("수정")
        btn_layout.addWidget(self.btn_new)
        btn_layout.addWidget(self.btn_edit)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def get_value(self, row):
        """row 행의 '값' 칸 텍스트"""
        if not hasattr(self, "table_info") or self.table_info is None:
            print("Error: table_info is None or deleted")
            return ""
        item = self.table_info.item(row, 1)
        return item.text().strip() if item and item.text() else "" 
        

    def set_value(self, row, text):
        """row 행의 '값' 칸을 설정"""
        if not hasattr(self, "table_info") or self.table_info is None:
            print("Error: table_info is None or deleted")
            return
        self.table_info.setItem(row, 1, QTableWidgetItem(text))

# ----------------------------
# 탭들 (직원, 거래처, 제품, 주문, 매출, 총매출, 차량, EMP-CLIENT, 브랜드-제품)
# ----------------------------
# 이하 동일: EmployeesTab, ClientsTab, ProductsTab, OrdersTab, SalesTab, 
#           TotalSalesTab, EmployeeVehicleTab, EmployeeClientTab, BrandProductTab
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QHBoxLayout, QPushButton, QMessageBox

class EmployeeSelectionDialog(QDialog):
    def __init__(self, employees, parent=None):
        super().__init__(parent)
        self.setWindowTitle("검색 결과")
        self.resize(300, 400)
        self.employees = employees  # 직원 목록 (dict 리스트)
        self.selected_employee = None

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        # "ID - 이름" 형식으로 항목 추가
        for emp in employees:
            display_text = f"{emp.get('id')} - {emp.get('name')}"
            self.list_widget.addItem(display_text)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("선택")
        self.cancel_button = QPushButton("취소")
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

        self.ok_button.clicked.connect(self.on_ok)
        self.cancel_button.clicked.connect(self.reject)

    def on_ok(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            index = self.list_widget.row(selected_items[0])
            self.selected_employee = self.employees[index]
            self.accept()
        else:
            QMessageBox.warning(self, "선택", "직원을 선택해주세요.")


class EmployeeDialog(QDialog):
    def __init__(self, title, employee=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(300, 200)

        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.role_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.birthday_edit = QDateEdit()
        self.birthday_edit.setCalendarPopup(True)
        self.birthday_edit.setDisplayFormat("yyyy-MM-dd")
        self.address_edit = QLineEdit()
        
        form_layout.addRow("이름:", self.name_edit)
        form_layout.addRow("전화번호:", self.phone_edit)
        form_layout.addRow("직책:", self.role_edit)
        form_layout.addRow("생일:", self.birthday_edit)
        form_layout.addRow("주소:", self.address_edit)
        form_layout.addRow("비밀번호:", self.password_edit)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("확인")
        self.cancel_button = QPushButton("취소")
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        # 수정 시 기존 정보를 미리 채워줌 (비밀번호는 빈 상태로 둠)
        if employee:
            self.name_edit.setText(employee.get("name", ""))
            self.phone_edit.setText(employee.get("phone", ""))
            self.role_edit.setText(employee.get("role", ""))
            if employee.get("birthday"):
                date_obj = QDate.fromString(employee.get("birthday"), "yyyy-MM-dd")
                self.birthday_edit.setDate(date_obj)
            self.address_edit.setText(employee.get("address", ""))
            
class EmployeeLeftWidget(BaseLeftTableWidget):
    def __init__(self, parent=None):
        """
        7행(직원ID, 이름, 전화번호, 직책, 차량_주유비, 주행거리, 엔진오일교체일)을
        테이블 형태로 배치하는 UI.
        """
        labels = [
            "직원ID", "이름", "전화번호", "직책", "생일", "주소",
            "차량_주유비", "차량_주행거리", "엔진오일교체일"
        ]
        super().__init__(row_count=len(labels), labels=labels, parent=parent)

        # 상위 BaseLeftTableWidget에서 table_info + "신규등록/수정" 버튼 생성
        self.btn_new.clicked.connect(self.create_employee)
        self.btn_edit.clicked.connect(self.update_employee)
        self.btn_delete = QPushButton("삭제")
        # BaseLeftTableWidget의 레이아웃(버튼이 들어있는 레이아웃)에 추가합니다.
        # (BaseLeftTableWidget의 init_ui()에서 마지막에 addLayout(btn_layout)을 호출함)
        self.layout().itemAt(1).layout().addWidget(self.btn_delete)
        self.btn_delete.clicked.connect(self.delete_employee)

    def display_employee(self, employee):
        """
        검색된 직원 정보(또는 None)를 받아,
        테이블의 각 행(0~6)에 값을 채워넣음.
        """
        # 혹시 위젯이 이미 파괴된 상태인지 체크 (wrapped c++ object 삭제 방지)
        if not hasattr(self, "table_info") or self.table_info is None:
            print("Error: table_info is None or deleted")
            return

        if not employee:
            # 검색 결과가 없으면 모든 칸 초기화
            for r in range(self.row_count):
                self.set_value(r, "")
            return

        # 직원 정보 세팅
        emp_id = str(employee.get("id", ""))
        self.set_value(0, emp_id)
        self.set_value(1, employee.get("name", ""))
        self.set_value(2, employee.get("phone", ""))
        self.set_value(3, employee.get("role", ""))
        birthday = employee.get("birthday")
        if birthday:
            # 만약 이미 문자열이면 그대로 사용, 아니면 날짜 객체를 문자열로 변환
            if isinstance(birthday, (str,)):
                birthday_str = birthday
            else:
                birthday_str = birthday.strftime("%Y-%m-%d")
        else:
            birthday_str = ""
        self.set_value(4, birthday_str)

        # 주소
        address = employee.get("address") or ""
        self.set_value(5, address)
        
        # 차량 정보 (예: monthly_fuel_cost, current_mileage, last_engine_oil_change)
        # api_fetch_employee_vehicle_info(...) 로 불러와 추가 표시
        veh = api_fetch_employee_vehicle_info(employee["id"])
        if veh:
            self.set_value(6, str(veh.get("monthly_fuel_cost", "")))
            self.set_value(7, str(veh.get("current_mileage", "")))
            self.set_value(8, str(veh.get("last_engine_oil_change", "")))
        else:
            self.set_value(6, "")
            self.set_value(7, "")
            self.set_value(8, "")

    def create_employee(self):
        """
        '신규등록' 버튼 클릭 시 팝업 다이얼로그를 띄워서 새 직원 정보를 입력받고,
        서버에 등록.
        """
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        dialog = EmployeeDialog("신규 직원 등록")
        if dialog.exec_() == QDialog.Accepted:
            data = {
                "password": dialog.password_edit.text() or "1234",
                "name": dialog.name_edit.text(),
                "phone": dialog.phone_edit.text(),
                "role": dialog.role_edit.text(),
                "birthday": dialog.birthday_edit.date().toString("yyyy-MM-dd"),
                "address": dialog.address_edit.text()
            }
            resp = api_create_employee(global_token, data)
            if resp and resp.status_code in (200, 201):
                QMessageBox.information(self, "성공", "직원 등록 완료!")
            else:
                status = resp.status_code if resp else "None"
                text = resp.text if resp else "No response"
                QMessageBox.critical(self, "실패", f"직원 등록 실패: {status}\n{text}")

    def update_employee(self):
        """
        '수정' 버튼 클릭 시 팝업 다이얼로그를 띄워서 현재 직원 정보를 수정하고,
        서버에 업데이트.
        """
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        emp_id = self.get_value(0).strip()
        if not emp_id:
            QMessageBox.warning(self, "주의", "수정할 직원 ID가 없습니다.")
            return

        # 현재 테이블에 표시된 정보를 미리 불러옴
        current_employee = {
            "name": self.get_value(1),
            "phone": self.get_value(2),
            "role": self.get_value(3),
            "birthday": self.get_value(4),
            "address": self.get_value(5)
        }
        dialog = EmployeeDialog("직원 수정", employee=current_employee)
        if dialog.exec_() == QDialog.Accepted:
            data = {
                "password": dialog.password_edit.text() or "1234",
                "name": dialog.name_edit.text(),
                "phone": dialog.phone_edit.text(),
                "role": dialog.role_edit.text(),
                "birthday": dialog.birthday_edit.date().toString("yyyy-MM-dd"),
                "address": dialog.address_edit.text()
            }
            resp = api_update_employee(global_token, emp_id, data)
            if resp and resp.status_code == 200:
                QMessageBox.information(self, "성공", "직원 수정 완료!")
            else:
                status = resp.status_code if resp else "None"
                text = resp.text if resp else "No response"
                QMessageBox.critical(self, "실패", f"직원 수정 실패: {status}\n{text}")

    def delete_employee(self):
        global global_token
        emp_id = self.get_value(0).strip()
        if not emp_id:
            QMessageBox.warning(self, "주의", "삭제할 직원 ID가 없습니다.")
            return

        reply = QMessageBox.question(
            self,
            "직원 삭제 확인",
            f"정말 직원 ID {emp_id}를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            resp = api_delete_employee(global_token, emp_id)
            if resp and resp.status_code == 200:
                QMessageBox.information(self, "성공", "직원 삭제 완료!")
                # 삭제 후, 테이블을 초기화
                for r in range(self.row_count):
                    self.set_value(r, "")
            else:
                status = resp.status_code if resp else "None"
                text = resp.text if resp else "No response"
                QMessageBox.critical(self, "실패", f"직원 삭제 실패: {status}\n{text}")

class RightFourBoxWidget(QWidget):
    """
    - QVBoxLayout으로 4개 QGroupBox (세로)
    - 1) 월별 매출, 2) 월별 방문, 3) 이번달 일별 매출(2줄), 4) 당일 방문정보
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        # 1) box1
        self.box1 = QGroupBox("당해년도 월별 매출")
        self.tbl_box1 = QTableWidget(2, 12)  # 2행 12열
        # box1 (월별 매출)에서,
        # - 열 헤더가 "1월"~"12월"
        # - row=0 (첫 행)에 매출값을 쓰고 싶다.
        self.tbl_box1.setRowCount(1)          # 1행
        self.tbl_box1.setColumnCount(12)      # 12열
        self.tbl_box1.setHorizontalHeaderLabels([
            "1월","2월","3월","4월","5월","6월",
            "7월","8월","9월","10월","11월","12월"
        ])

        # 그다음에 update_data_example 등에서 데이터 넣기:
        # sales_data = [100,200,300,400,500,600,700,800,900,1000,1100,1200]
        # for c in range(12):
        #     # row=0, col=c 위치에 매출값 쓰기
        #     self.tbl_box1.setItem(0, c, QTableWidgetItem(str(sales_data[c])))

        self.tbl_box1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box1.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tbl_box1.setHorizontalHeaderLabels([""]*12)
        box1_layout = QVBoxLayout()
        box1_layout.addWidget(self.tbl_box1)
        self.box1.setLayout(box1_layout)
        main_layout.addWidget(self.box1)

        # 2) box2
        self.box2 = QGroupBox("당해년도 월별 방문횟수")
        self.tbl_box2 = QTableWidget(2, 12)
        # box1 (월별 매출)에서,
        # - 열 헤더가 "1월"~"12월"
        # - row=0 (첫 행)에 매출값을 쓰고 싶다.
        self.tbl_box2.setRowCount(1)          # 1행
        self.tbl_box2.setColumnCount(12)      # 12열
        self.tbl_box2.setHorizontalHeaderLabels([
            "1월","2월","3월","4월","5월","6월",
            "7월","8월","9월","10월","11월","12월"
        ])

        # 그다음에 update_data_example 등에서 데이터 넣기:
        # sales_data = [100,200,300,400,500,600,700,800,900,1000,1100,1200]
        # for c in range(12):
        #     # row=0, col=c 위치에 매출값 쓰기
        #     self.tbl_box2.setItem(0, c, QTableWidgetItem(str(sales_data[c])))
        self.tbl_box2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box2.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        box2_layout = QVBoxLayout()
        box2_layout.addWidget(self.tbl_box2)
        self.box2.setLayout(box2_layout)
        main_layout.addWidget(self.box2)

        # 3) box3: 이번달 일별 매출 (2줄)
        #    - 첫 번째 테이블: 1~15일
        #    - 두 번째 테이블: 16~31일
        self.box3 = QGroupBox("이번달 일별 매출 (2줄)")
        v = QVBoxLayout()


        self.tbl_box3_top = QTableWidget(2, 15)  # 1~15일
        self.tbl_box3_top.setRowCount(1)          # 1행
        self.tbl_box3_top.setColumnCount(15)      # 12열
        self.tbl_box3_top.setHorizontalHeaderLabels([
            "1일","2일","3일","4일","5일","6일",
            "7일","8일","9일","10일","11일","12일","13일","14일","15일"
        ])

        self.tbl_box3_top.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box3_top.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tbl_box3_top.setHorizontalHeaderLabels([""]*15)

        self.tbl_box3_bottom = QTableWidget(2, 16)  # 16~31일
        self.tbl_box3_bottom.setRowCount(1)          # 1행
        self.tbl_box3_bottom.setColumnCount(16)      # 12열
        self.tbl_box3_bottom.setHorizontalHeaderLabels([
            "16일","17일","18일","19일","20일","21일",
            "22일","23일","24일","25일","26일","27일","28일","29일","30일","31일"
        ])
        self.tbl_box3_bottom.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box3_bottom.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tbl_box3_bottom.setHorizontalHeaderLabels([""]*16)

        v.addWidget(self.tbl_box3_top)
        v.addWidget(self.tbl_box3_bottom)
        self.box3.setLayout(v)
        main_layout.addWidget(self.box3)

        # 4) box4
        self.box4 = QGroupBox("당일 방문 거래처 정보")
        box4_layout = QVBoxLayout()
        self.tbl_box4_main = QTableWidget(10, 5)
        self.tbl_box4_main.setRowCount(50)  # 원하는 만큼
        self.tbl_box4_main.setColumnCount(5)
        self.tbl_box4_main.setHorizontalHeaderLabels(["거래처","오늘 매출","미수금","방문시간","기타"])
        self.tbl_box4_main.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box4_main.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        box4_layout.addWidget(self.tbl_box4_main)
        
        self.tbl_box4_footer = QTableWidget()
        self.tbl_box4_footer.setRowCount(1)
        self.tbl_box4_footer.setColumnCount(5)
        # 헤더 감추기 (가로/세로 둘 다)
        self.tbl_box4_footer.horizontalHeader().setVisible(False)
        # self.tbl_box4_footer.verticalHeader().setVisible(False)
        self.tbl_box4_footer.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # 가로 스크롤은 필요하지만, 세로 스크롤은 필요없음
        self.tbl_box4_footer.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 푸터 테이블 높이 제한 (1행이므로 크게 필요없음)
        self.tbl_box4_footer.setFixedHeight(35)  # 원하는 높이로 조절. 예: 35px
        # 또는 self.tbl_box4_footer.setRowHeight(0, 30) 등으로 높이를 조절 가능

        # 헤더도 보이게 할 수 있지만, 합계 행만 있으므로 세로헤더는 안 보이게
        self.tbl_box4_footer.verticalHeader().setVisible(False)
        box4_layout.addWidget(self.tbl_box4_footer)
        # 메인테이블 스크롤 동기화
        self.tbl_box4_main.horizontalScrollBar().valueChanged.connect(
            self.tbl_box4_footer.horizontalScrollBar().setValue
        )
        item = QTableWidgetItem("합계")
        item.setBackground(QColor("#333333"))
        item.setForeground(QColor("white"))
        self.tbl_box4_footer.setItem(0, 0, item)
        # box4_layout = QVBoxLayout()
        # box4_layout.addWidget(self.tbl_box4)
        self.box4.setLayout(box4_layout)
        main_layout.addWidget(self.box4)

        main_layout.setStretchFactor(self.box1, 1)
        main_layout.setStretchFactor(self.box2, 1)
        main_layout.setStretchFactor(self.box3, 3)
        main_layout.setStretchFactor(self.box4, 10)
        
        self.setLayout(main_layout)

    def update_data_from_db(self, employee_id: int, year: int, month: int):
        """
        실제 DB에서 월별 매출, 월별 방문, 일별 매출, 일별 방문 기록을 가져와서
        각각 box1, box2, box3, box4 테이블에 채워넣는다.
        """
        global global_token
        if not global_token:
            # 로그인 토큰 없으면 그냥 종료(실제 앱에선 안내창 띄우면 됨)
            return

        headers = {"Authorization": f"Bearer {global_token}"}

        # 1) 월별 매출
        url_monthly_sales = f"{BASE_URL}/sales/monthly_sales/{employee_id}/{year}"
        try:
            resp = requests.get(url_monthly_sales, headers=headers)
            resp.raise_for_status()
            monthly_sales = resp.json()  # 길이 12의 리스트
        except:
            monthly_sales = [0]*12
        for c in range(12):
            # monthly_sales[c] 값 → row=0, col=c 셀에 표시
            self.tbl_box1.setItem(0, c, QTableWidgetItem(str(monthly_sales[c])))
        # 2) 월별 방문
        url_monthly_visits = f"{BASE_URL}/client_visits/monthly_visits/{employee_id}/{year}"
        try:
            resp = requests.get(url_monthly_visits, headers=headers)
            resp.raise_for_status()
            monthly_visits = resp.json()  # 길이 12의 리스트
        except:
            monthly_visits = [0]*12
        # [BOX2] 월별 방문 테이블 채우기
        # self.tbl_box2 역시 1행 12열
        for c in range(12):
            self.tbl_box2.setItem(0, c, QTableWidgetItem(str(monthly_visits[c])))


        # 3) 일별 매출 (해당 월)
        url_daily_sales = f"{BASE_URL}/sales/daily_sales/{employee_id}/{year}/{month}"
        try:
            resp = requests.get(url_daily_sales, headers=headers)
            resp.raise_for_status()
            daily_sales = resp.json()  # 길이 31(최대)의 리스트
        except:
            daily_sales = [0]*31

       
        for day_index in range(15):  # 0~14
            val = daily_sales[day_index]   # day_index=0 → 1일, 1 → 2일 ...
            self.tbl_box3_top.setItem(0, day_index, QTableWidgetItem(str(val)))

       
        for day_index in range(15, 31):  # 15~30
            val = daily_sales[day_index]
            # 아래 테이블에서는 col=day_index-15
            self.tbl_box3_bottom.setItem(0, day_index - 15, QTableWidgetItem(str(val)))
        # -----------------------------
        # (4) 당일 방문 + 미수금 + 오늘 매출 (box4)
        # -----------------------------
        url_today_visits = f"{BASE_URL}/client_visits/today_visits_details?employee_id={employee_id}"
        try:
            resp = requests.get(url_today_visits, headers=headers)
            resp.raise_for_status()
            visits_data = resp.json()
        except Exception as e:
            print("오늘 방문 데이터 조회 오류:", e)
            visits_data = []

        # (4-1) 오늘 매출 합계, 미수금 합계를 계산
        total_today_sales = sum(item.get("today_sales", 0) for item in visits_data)
        total_outstanding = sum(item.get("outstanding_amount", 0) for item in visits_data)

        # (4-2) 테이블 행 갯수를 visits_data 길이+1 로 지정
        #       마지막 행을 '합계'로 쓸 것이므로 +1
        self.tbl_box4_main.setRowCount(len(visits_data) + 1)

        # (4-3) 각 방문 데이터를 행별로 표시
        for row_index, info in enumerate(visits_data):
            client_name = info.get("client_name", "N/A")
            today_sales = info.get("today_sales", 0)
            outstanding = info.get("outstanding_amount", 0)
            visit_time  = info.get("visit_datetime", "")

            self.tbl_box4_main.setItem(row_index, 0, QTableWidgetItem(client_name))
            self.tbl_box4_main.setItem(row_index, 1, QTableWidgetItem(str(today_sales)))
            self.tbl_box4_main.setItem(row_index, 2, QTableWidgetItem(str(outstanding)))
            self.tbl_box4_main.setItem(row_index, 3, QTableWidgetItem(visit_time))
            self.tbl_box4_main.setItem(row_index, 4, QTableWidgetItem(""))

        # (4-4) 마지막 행(합계 행)을 표시
        total_row = len(visits_data)
        self.tbl_box4_main.setItem(total_row, 0, QTableWidgetItem("합계"))
        self.tbl_box4_main.setItem(total_row, 1, QTableWidgetItem(str(total_today_sales)))
        self.tbl_box4_main.setItem(total_row, 2, QTableWidgetItem(str(total_outstanding)))
        # 나머지 열(방문시간, 기타)은 비워둠
        self.tbl_box4_main.setItem(total_row, 3, QTableWidgetItem(""))
        self.tbl_box4_main.setItem(total_row, 4, QTableWidgetItem(""))

         # 합계 계산
        total_sales = sum(x["today_sales"] for x in visits_data)
        total_outstanding = sum(x["outstanding_amount"] for x in visits_data)

        # 푸터 테이블(1행 5열) → 첫 번째 셀에 "합계"
        self.tbl_box4_footer.setItem(0, 0, QTableWidgetItem("합계"))
        self.tbl_box4_footer.setItem(0, 1, QTableWidgetItem(str(total_sales)))
        self.tbl_box4_footer.setItem(0, 2, QTableWidgetItem(str(total_outstanding)))
        self.tbl_box4_footer.setItem(0, 3, QTableWidgetItem(""))  # 방문시간 칸은 비움
        self.tbl_box4_footer.setItem(0, 4, QTableWidgetItem(""))  # 기타 칸 비움    

class EmployeesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout()

        # 왼쪽(1) : 오른쪽(10)
        self.left_widget = EmployeeLeftWidget()
        main_layout.addWidget(self.left_widget, 1)

        self.right_four = RightFourBoxWidget()
        main_layout.addWidget(self.right_four, 5)

        self.setLayout(main_layout)

    def do_search(self, keyword):
        """
        검색어(부분 일치)로 직원 목록을 조회하고,
        검색 결과가 여러 건이면 선택 다이얼로그를 띄워서 사용자가 선택하도록 함.
        """
        global global_token
        employees = api_fetch_employees(global_token, keyword)

        # API가 단일 객체를 반환하면 리스트로 변경
        if isinstance(employees, dict):
            employees = [employees]

        # 만약 결과가 없으면
        if not isinstance(employees, list) or len(employees) == 0:
            self.left_widget.display_employee(None)
            QMessageBox.information(self, "검색 결과", "검색 결과가 없습니다.")
            return

        # 부분 일치를 기준으로 필터링 (대소문자 구분없이)
        filtered_employees = [emp for emp in employees if keyword.lower() in emp.get("name", "").lower()]

        if not filtered_employees:
            self.left_widget.display_employee(None)
            QMessageBox.information(self, "검색 결과", "검색 결과가 없습니다.")
        elif len(filtered_employees) == 1:
            self.left_widget.display_employee(filtered_employees[0])
        else:
            # 여러 건일 경우 팝업 다이얼로그 띄우기
            dialog = EmployeeSelectionDialog(filtered_employees, parent=self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_employee:
                self.left_widget.display_employee(dialog.selected_employee)

class ClientDialog(QDialog):
    def __init__(self, title, client=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(350, 250)

        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.outstanding_edit = QLineEdit("0")
        self.unit_price_edit = QLineEdit("35")
        self.business_edit = QLineEdit()
        self.email_edit = QLineEdit()
        
        form_layout.addRow("거래처명:", self.name_edit)
        form_layout.addRow("주소:", self.address_edit)
        form_layout.addRow("전화번호:", self.phone_edit)
        form_layout.addRow("미수금:", self.outstanding_edit)
        form_layout.addRow("거래처 단가:", self.unit_price_edit)
        form_layout.addRow("사업자번호:", self.business_edit)
        form_layout.addRow("이메일:", self.email_edit)

        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("확인")
        self.cancel_button = QPushButton("취소")
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        if client:
            self.name_edit.setText(client.get("client_name", ""))
            self.address_edit.setText(client.get("address", ""))
            self.phone_edit.setText(client.get("phone", ""))
            self.outstanding_edit.setText(str(client.get("outstanding_amount", "0")))
            self.unit_price_edit.setText(str(client.get("unit_price", "0")))
            self.business_edit.setText(client.get("business_number", ""))
            self.email_edit.setText(client.get("email", ""))

class ClientRightFourBoxWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        # 1) box1
        self.box1 = QGroupBox("해당거래처 월별 매출")
        self.tbl_box1 = QTableWidget(2, 12)  # 2행 12열
        # box1 (월별 매출)에서,
        # - 열 헤더가 "1월"~"12월"
        # - row=0 (첫 행)에 매출값을 쓰고 싶다.
        self.tbl_box1.setRowCount(1)          # 1행
        self.tbl_box1.setColumnCount(12)      # 12열
        self.tbl_box1.setHorizontalHeaderLabels([
            "1월","2월","3월","4월","5월","6월",
            "7월","8월","9월","10월","11월","12월"
        ])

        # 그다음에 update_data_example 등에서 데이터 넣기:
        # sales_data = [100,200,300,400,500,600,700,800,900,1000,1100,1200]
        # for c in range(12):
        #     # row=0, col=c 위치에 매출값 쓰기
        #     self.tbl_box1.setItem(0, c, QTableWidgetItem(str(sales_data[c])))

        self.tbl_box1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box1.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tbl_box1.setHorizontalHeaderLabels([""]*12)
        box1_layout = QVBoxLayout()
        box1_layout.addWidget(self.tbl_box1)
        self.box1.setLayout(box1_layout)
        main_layout.addWidget(self.box1)

        # 2) box2
        self.box2 = QGroupBox("해당거래처 영업사원 방문횟수")
        self.tbl_box2 = QTableWidget(2, 12)
        # box1 (월별 매출)에서,
        # - 열 헤더가 "1월"~"12월"
        # - row=0 (첫 행)에 매출값을 쓰고 싶다.
        self.tbl_box2.setRowCount(1)          # 1행
        self.tbl_box2.setColumnCount(12)      # 12열
        self.tbl_box2.setHorizontalHeaderLabels([
            "1월","2월","3월","4월","5월","6월",
            "7월","8월","9월","10월","11월","12월"
        ])

        # 그다음에 update_data_example 등에서 데이터 넣기:
        # sales_data = [100,200,300,400,500,600,700,800,900,1000,1100,1200]
        # for c in range(12):
        #     # row=0, col=c 위치에 매출값 쓰기
        #     self.tbl_box2.setItem(0, c, QTableWidgetItem(str(sales_data[c])))
        self.tbl_box2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box2.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        box2_layout = QVBoxLayout()
        box2_layout.addWidget(self.tbl_box2)
        self.box2.setLayout(box2_layout)
        main_layout.addWidget(self.box2)

        # 3) box3: 이번달 일별 매출 (2줄)
        #    - 첫 번째 테이블: 1~15일
        #    - 두 번째 테이블: 16~31일
        self.box3 = QGroupBox("이번달 일별 매출")
        v = QVBoxLayout()


        self.tbl_box3_top = QTableWidget(2, 15)  # 1~15일
        self.tbl_box3_top.setRowCount(1)          # 1행
        self.tbl_box3_top.setColumnCount(15)      # 12열
        self.tbl_box3_top.setHorizontalHeaderLabels([
            "1일","2일","3일","4일","5일","6일",
            "7일","8일","9일","10일","11일","12일","13일","14일","15일"
        ])

        self.tbl_box3_top.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box3_top.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tbl_box3_top.setHorizontalHeaderLabels([""]*15)

        self.tbl_box3_bottom = QTableWidget(2, 16)  # 16~31일
        self.tbl_box3_bottom.setRowCount(1)          # 1행
        self.tbl_box3_bottom.setColumnCount(16)      # 12열
        self.tbl_box3_bottom.setHorizontalHeaderLabels([
            "16일","17일","18일","19일","20일","21일",
            "22일","23일","24일","25일","26일","27일","28일","29일","30일","31일"
        ])
        self.tbl_box3_bottom.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box3_bottom.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tbl_box3_bottom.setHorizontalHeaderLabels([""]*16)

        v.addWidget(self.tbl_box3_top)
        v.addWidget(self.tbl_box3_bottom)
        self.box3.setLayout(v)
        main_layout.addWidget(self.box3)

        # 4) box4
        self.box4 = QGroupBox("당일 분류별 판매내용용")
        box4_layout = QVBoxLayout()
        self.tbl_box4_main = QTableWidget(10, 5)
        self.tbl_box4_main.setRowCount(50)  # 원하는 만큼
        self.tbl_box4_main.setColumnCount(5)
        self.tbl_box4_main.setHorizontalHeaderLabels(["분류","판매금액","수량","직원","기타"])
        self.tbl_box4_main.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box4_main.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        box4_layout.addWidget(self.tbl_box4_main)
        
        self.tbl_box4_footer = QTableWidget()
        self.tbl_box4_footer.setRowCount(1)
        self.tbl_box4_footer.setColumnCount(5)
        # 헤더 감추기 (가로/세로 둘 다)
        self.tbl_box4_footer.horizontalHeader().setVisible(False)
        # self.tbl_box4_footer.verticalHeader().setVisible(False)
        self.tbl_box4_footer.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # 가로 스크롤은 필요하지만, 세로 스크롤은 필요없음
        self.tbl_box4_footer.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 푸터 테이블 높이 제한 (1행이므로 크게 필요없음)
        self.tbl_box4_footer.setFixedHeight(35)  # 원하는 높이로 조절. 예: 35px
        # 또는 self.tbl_box4_footer.setRowHeight(0, 30) 등으로 높이를 조절 가능

        # 헤더도 보이게 할 수 있지만, 합계 행만 있으므로 세로헤더는 안 보이게
        self.tbl_box4_footer.verticalHeader().setVisible(False)
        box4_layout.addWidget(self.tbl_box4_footer)
        # 메인테이블 스크롤 동기화
        self.tbl_box4_main.horizontalScrollBar().valueChanged.connect(
            self.tbl_box4_footer.horizontalScrollBar().setValue
        )
        item = QTableWidgetItem("합계")
        item.setBackground(QColor("#333333"))
        item.setForeground(QColor("white"))
        self.tbl_box4_footer.setItem(0, 0, item)
        # box4_layout = QVBoxLayout()
        # box4_layout.addWidget(self.tbl_box4)
        self.box4.setLayout(box4_layout)
        main_layout.addWidget(self.box4)

        main_layout.setStretchFactor(self.box1, 1)
        main_layout.setStretchFactor(self.box2, 1)
        main_layout.setStretchFactor(self.box3, 3)
        main_layout.setStretchFactor(self.box4, 10)
        
        self.setLayout(main_layout)

    def update_data_for_client(self, client_id: int):
        """
        실제로 client_id를 받아서 서버에서
        - 월별 매출
        - 영업사원 월별 방문횟수
        - 이번달 일별 매출
        - 당일 분류별 판매 내용
        등을 가져와 테이블에 채우는 로직.
        """
        global global_token
        if not global_token:
            return

        # 예시(더미 데이터):
        monthly_sales = [200,300,400,500,100,150,700,250,300,600,900,1000]
        for c, value in enumerate(monthly_sales):
            self.tbl_box1.setItem(0, c, QTableWidgetItem(str(value)))

        monthly_visits = [2,1,3,0,5,2,7,1,0,2,1,3]
        for c, val in enumerate(monthly_visits):
            self.tbl_box2.setItem(0, c, QTableWidgetItem(str(val)))

        # 이번달 일별 매출
        #   1~15일
        daily_sales_1to15 = [50,60,0,0,100,300,150,200,80,120,40,60,70,110,90]
        for c, val in enumerate(daily_sales_1to15):
            self.tbl_box3_top.setItem(0, c, QTableWidgetItem(str(val)))

        #   16~31일
        daily_sales_16to31 = [0,50,70,80,20,40,30,10,100,200,150,90,110,80,0,60]
        for c, val in enumerate(daily_sales_16to31):
            self.tbl_box3_bottom.setItem(0, c, QTableWidgetItem(str(val)))

        # 당일 분류별 판매 내용 (예: 분류 / 판매금액 / 수량 / 직원 / 기타)
        category_data = [
            ("음료", 300, 15, "김영업", ""),
            ("과자", 200, 10, "김영업", ""),
            ("식품", 150, 5,  "이사원", ""),
            ("기타", 500, 25, "박사원", ""),
        ]
        for row, cat in enumerate(category_data):
            self.tbl_box4_main.setItem(row, 0, QTableWidgetItem(cat[0]))  # 분류
            self.tbl_box4_main.setItem(row, 1, QTableWidgetItem(str(cat[1])))  # 판매금액
            self.tbl_box4_main.setItem(row, 2, QTableWidgetItem(str(cat[2])))  # 수량
            self.tbl_box4_main.setItem(row, 3, QTableWidgetItem(cat[3]))       # 직원
            self.tbl_box4_main.setItem(row, 4, QTableWidgetItem(cat[4]))       # 기타

class ClientSelectionDialog(QDialog):
    def __init__(self, clients, parent=None):
        super().__init__(parent)
        self.setWindowTitle("검색 결과")
        self.resize(300, 400)
        self.clients = clients  # 거래처 목록 (dict 리스트)
        self.selected_client = None

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        
        # "ID - 거래처명" 형식으로 항목 추가
        for client in clients:
            display_text = f"{client.get('id')} - {client.get('client_name')}"
            self.list_widget.addItem(display_text)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("선택")
        self.cancel_button = QPushButton("취소")
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

        self.ok_button.clicked.connect(self.on_ok)
        self.cancel_button.clicked.connect(self.reject)

    def on_ok(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            index = self.list_widget.row(selected_items[0])
            self.selected_client = self.clients[index]
            self.accept()
        else:
            QMessageBox.warning(self, "선택", "거래처를 선택해주세요.")
            
class ClientLeftWidget(BaseLeftTableWidget):
    def __init__(self, parent=None):
        # 이제 8행: 거래처ID, 거래처명, 주소, 전화번호, 미수금, 거래처단가, 사업자번호, 메일주소
        labels = [
            "거래처ID",    # 0
            "거래처명",    # 1
            "주소",        # 2
            "전화번호",    # 3
            "미수금",      # 4
            "거래처단가",  # 5
            "사업자번호",  # 6
            "메일주소"     # 7
        ]
        
        super().__init__(row_count=len(labels), labels=labels, parent=parent)
        # ✅ 현재 레이아웃을 가져옴 (None 방지)
        main_layout = self.layout()
        if main_layout is None:
            main_layout = QVBoxLayout()
            self.setLayout(main_layout)

        # ✅ "대여 냉동고" 버튼을 개별 레이아웃으로 추가
        btn_layout_top = QHBoxLayout()
        self.btn_lent = QPushButton("대여 냉동고")
        btn_layout_top.addWidget(self.btn_lent)

        # ✅ 부모 클래스의 버튼 레이아웃이 있는지 확인하고 가져오기
        if main_layout.count() > 1 and main_layout.itemAt(1) is not None:
            btn_layout_bottom = main_layout.itemAt(1).layout()
        else:
            btn_layout_bottom = QHBoxLayout()
            main_layout.addLayout(btn_layout_bottom)

        # ✅ 기존 버튼 줄에 "삭제" 버튼 추가
        self.btn_delete = QPushButton("삭제")
        btn_layout_bottom.addWidget(self.btn_delete)

        # ✅ "대여 냉동고" 버튼을 최상단에 추가
        main_layout.insertLayout(0, btn_layout_top)

        # ✅ 버튼 이벤트 연결
        self.btn_lent.clicked.connect(self.show_lent_freezers)
        self.btn_new.clicked.connect(self.create_client)
        self.btn_edit.clicked.connect(self.update_client)
        self.btn_delete.clicked.connect(self.delete_client)
    def show_lent_freezers(self):
        """
        대여 냉동고 버튼 클릭 시 팝업 창을 띄우는 함수
        """
        global global_token
        client_id = self.get_value(0).strip()  # 거래처 ID 가져오기
        if not client_id:
            QMessageBox.warning(self, "경고", "조회할 거래처 ID가 없습니다.")
            return

        # 대여 냉동고 정보 가져오기
        lent_data = api_fetch_lent_freezers(global_token, client_id)

        if not lent_data:
            QMessageBox.information(self, "정보", "이 거래처에는 대여 냉동고가 없습니다.")
            return

        # 팝업 창 띄우기
        dialog = LentDialog(lent_data, self)
        dialog.exec_()
           
    def display_client(self, client):
        """
        검색된 거래처 정보를 왼쪽 패널에 표시하는 함수
        """
        if not hasattr(self, "table_info") or self.table_info is None:
            print("Error: table_info is None or deleted")
            return

        if not client:
            # 검색 결과가 없으면 모든 칸 초기화
            for r in range(self.row_count):
                self.set_value(r, "")
            return

        # client가 dict 형태라고 가정 (키: id, client_name, address, phone, outstanding_amount, unit_price, business_number, email)
        self.set_value(0, str(client.get("id", "")))
        self.set_value(1, client.get("client_name", ""))
        self.set_value(2, client.get("address", ""))
        self.set_value(3, client.get("phone", ""))
        self.set_value(4, str(client.get("outstanding_amount", "")))
        self.set_value(5, str(client.get("unit_price", "")))
        self.set_value(6, client.get("business_number", ""))
        self.set_value(7, client.get("email", ""))

    def create_client(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        dialog = ClientDialog("신규 거래처 등록")
        if dialog.exec_() == QDialog.Accepted:
            data = {
                "client_name": dialog.name_edit.text(),
                "address": dialog.address_edit.text(),
                "phone": dialog.phone_edit.text(),
                "outstanding_amount": float(dialog.outstanding_edit.text() or 0),
                "unit_price": float(dialog.unit_price_edit.text() or 0),
                "business_number": dialog.business_edit.text(),
                "email": dialog.email_edit.text(),
            }
            resp = api_create_client(global_token, data)
            if resp and resp.status_code in (200, 201):
                QMessageBox.information(self, "성공", "거래처 등록 완료!")
            else:
                QMessageBox.critical(self, "실패", f"거래처 등록 실패: {resp.status_code}\n{resp.text}")

    def update_client(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        client_id = self.get_value(0).strip()
        if not client_id:
            QMessageBox.warning(self, "주의", "수정할 거래처 ID가 없습니다.")
            return

        current_client = {
            "client_name": self.get_value(1),
            "address": self.get_value(2),
            "phone": self.get_value(3),
            "outstanding_amount": self.get_value(4),
            "unit_price": self.get_value(5),
            "business_number": self.get_value(6),
            "email": self.get_value(7),
        }
        
        dialog = ClientDialog("거래처 수정", client=current_client)
        if dialog.exec_() == QDialog.Accepted:
            data = {
                "client_name": dialog.name_edit.text(),
                "address": dialog.address_edit.text(),
                "phone": dialog.phone_edit.text(),
                "outstanding_amount": float(dialog.outstanding_edit.text() or 0),
                "unit_price": float(dialog.unit_price_edit.text() or 0),
                "business_number": dialog.business_edit.text(),
                "email": dialog.email_edit.text(),
            }
            resp = api_update_client(global_token, client_id, data)
            if resp and resp.status_code == 200:
                QMessageBox.information(self, "성공", "거래처 수정 완료!")
            else:
                QMessageBox.critical(self, "실패", f"거래처 수정 실패: {resp.status_code}\n{resp.text}")

    def delete_client(self):
        global global_token
        client_id = self.get_value(0).strip()
        if not client_id:
            QMessageBox.warning(self, "주의", "삭제할 거래처 ID가 없습니다.")
            return

        reply = QMessageBox.question(
            self,
            "거래처 삭제 확인",
            f"정말 거래처 ID {client_id}를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            resp = api_delete_client(global_token, client_id)
            if resp and resp.status_code == 200:
                QMessageBox.information(self, "성공", "거래처 삭제 완료!")
                for r in range(self.row_count):
                    self.set_value(r, "")
            else:
                QMessageBox.critical(self, "실패", f"거래처 삭제 실패: {resp.status_code}\n{resp.text}")

class LentDialog(QDialog):
    def __init__(self, lent_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("냉동고대여상황")
        self.resize(500, 400)
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["상표", "시리얼 번호", "년식"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.populate_table(lent_data)
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
  
    def populate_table(self, lent_data):
        self.table.setRowCount(len(lent_data))
        for i, record in enumerate(lent_data):
            self.table.setItem(i, 0, QTableWidgetItem(record.get("brand", "")))
            self.table.setItem(i, 1, QTableWidgetItem(record.get("serial_number", "")))
            self.table.setItem(i, 2, QTableWidgetItem(str(record.get("year", ""))))
            
class ClientsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout()

        # 왼쪽: ClientLeftWidget
        self.left_widget = ClientLeftWidget()
        main_layout.addWidget(self.left_widget, 1)

        # 오른쪽: 4분할 위젯(월별매출, 월별방문, 일별매출, 당일분류판매)
        self.right_four = ClientRightFourBoxWidget()
        main_layout.addWidget(self.right_four, 5)

        self.setLayout(main_layout)

    def do_search(self, keyword):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        resp = api_fetch_clients(global_token)
        if not resp or resp.status_code != 200:
            QMessageBox.critical(self, "실패", "거래처 목록 불러오기 실패!")
            return

        clients = resp.json()

        # 검색어 포함된 거래처 찾기 (대소문자 구분 없이 검색)
        filtered_clients = [c for c in clients if keyword.lower() in c["client_name"].lower()]

        if not filtered_clients:
            self.left_widget.display_client(None)
            QMessageBox.information(self, "검색 결과", "검색 결과가 없습니다.")
            return

        if len(filtered_clients) == 1:
            # 검색 결과가 1개면 바로 선택
            self.left_widget.display_client(filtered_clients[0])
        else:
            # 검색 결과가 여러 개면 팝업창 띄우기
            dialog = ClientSelectionDialog(filtered_clients, parent=self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_client:
                self.left_widget.display_client(dialog.selected_client)

    # def __init__(self, parent=None):
    #     super().__init__(parent)
    #     self.init_ui()

    # def init_ui(self):
    #     main_layout = QHBoxLayout()

    #     left_panel = QGroupBox("거래처 입력")
    #     left_layout = QFormLayout()
    #     self.client_name_edit = QLineEdit()
    #     left_layout.addRow("Client Name:", self.client_name_edit)
    #     self.client_address_edit = QLineEdit()
    #     left_layout.addRow("Address:", self.client_address_edit)
    #     self.client_phone_edit = QLineEdit()
    #     left_layout.addRow("Phone:", self.client_phone_edit)
    #     self.client_outstanding_edit = QLineEdit("0")
    #     left_layout.addRow("Outstanding Amount:", self.client_outstanding_edit)
    #     create_btn = QPushButton("Create Client")
    #     create_btn.clicked.connect(self.create_client)
    #     left_layout.addRow(create_btn)
    #     left_panel.setLayout(left_layout)

    #     right_panel = QGroupBox("거래처 목록")
    #     right_layout = QVBoxLayout()
    #     self.client_table = QTableWidget()
    #     self.client_table.setColumnCount(5)
    #     self.client_table.setHorizontalHeaderLabels(["ID", "Name", "Address", "Phone", "Outstanding"])
    #     self.client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    #     right_layout.addWidget(self.client_table)
    #     refresh_btn = QPushButton("Refresh Clients")
    #     refresh_btn.clicked.connect(self.list_clients)
    #     right_layout.addWidget(refresh_btn)
    #     right_panel.setLayout(right_layout)

    #     main_layout.addWidget(left_panel,1)
    #     main_layout.addWidget(right_panel,4)
    #     self.setLayout(main_layout)

    # def create_client(self):
    #     global global_token
    #     if not global_token:
    #         QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
    #         return
    #     data = {
    #         "client_name": self.client_name_edit.text(),
    #         "address": self.client_address_edit.text(),
    #         "phone": self.client_phone_edit.text(),
    #         "outstanding_amount": float(self.client_outstanding_edit.text() or 0)
    #     }
    #     try:
    #         resp = api_create_client(global_token, data)
    #         if resp.status_code in (200,201):
    #             QMessageBox.information(self, "성공", "거래처 생성 완료!")
    #             self.list_clients()
    #         else:
    #             QMessageBox.critical(self, "실패", f"Create client failed: {resp.status_code}\n{resp.text}")
    #     except Exception as ex:
    #         QMessageBox.critical(self, "오류", str(ex))

    # def list_clients(self):
    #     global global_token
    #     if not global_token:
    #         QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
    #         return
    #     try:
    #         resp = api_fetch_clients(global_token)
    #         if resp.status_code == 200:
    #             data = resp.json()
    #             self.client_table.setRowCount(0)
    #             for c in data:
    #                 row = self.client_table.rowCount()
    #                 self.client_table.insertRow(row)
    #                 self.client_table.setItem(row, 0, QTableWidgetItem(str(c.get("id",""))))
    #                 self.client_table.setItem(row, 1, QTableWidgetItem(c.get("client_name","")))
    #                 self.client_table.setItem(row, 2, QTableWidgetItem(c.get("address","")))
    #                 self.client_table.setItem(row, 3, QTableWidgetItem(c.get("phone","")))
    #                 self.client_table.setItem(row, 4, QTableWidgetItem(str(c.get("outstanding_amount",""))))
    #         else:
    #             QMessageBox.critical(self, "실패", f"List clients failed: {resp.status_code}\n{resp.text}")
    #     except Exception as ex:
    #         QMessageBox.critical(self, "오류", str(ex))


class ProductSelectionDialog(QDialog):
    def __init__(self, products, parent=None):
        super().__init__(parent)
        self.setWindowTitle("상품 검색 결과")
        self.resize(300, 400)
        self.products = products  # 상품 목록 (dict 리스트)
        self.selected_product = None

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()

        # "ID - 상품명" 형식으로 리스트 추가
        for product in products:
            display_text = f"{product.get('id')} - {product.get('product_name')}"
            self.list_widget.addItem(display_text)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("선택")
        self.cancel_button = QPushButton("취소")
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

        self.ok_button.clicked.connect(self.on_ok)
        self.cancel_button.clicked.connect(self.reject)

    def on_ok(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            index = self.list_widget.row(selected_items[0])
            self.selected_product = self.products[index]
            self.accept()
        else:
            QMessageBox.warning(self, "선택", "상품을 선택해주세요.")


class ProductDialog(QDialog):
    def __init__(self, title, product=None, parent=None):
        """
        상품 등록 및 수정 다이얼로그
        :param title: 다이얼로그 제목 ("신규 상품 등록" or "상품 수정")
        :param product: 기존 상품 정보 (수정 시)
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 350)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # ✅ 브랜드 ID (숫자 입력)
        self.brand_id_edit = QLineEdit()
        form_layout.addRow("브랜드 ID:", self.brand_id_edit)

        # ✅ 상품명
        self.name_edit = QLineEdit()
        form_layout.addRow("상품명:", self.name_edit)

        # ✅ 바코드
        self.barcode_edit = QLineEdit()
        form_layout.addRow("바코드:", self.barcode_edit)

        # ✅ 기본 가격
        self.price_edit = QLineEdit()
        form_layout.addRow("기본 가격:", self.price_edit)

        # ✅ 인센티브
        self.incentive_edit = QLineEdit()
        form_layout.addRow("인센티브:", self.incentive_edit)

        # ✅ 재고 수량
        self.stock_edit = QLineEdit()
        form_layout.addRow("재고 수량:", self.stock_edit)

        # ✅ 박스당 수량
        self.box_quantity_edit = QLineEdit()
        form_layout.addRow("박스당 수량:", self.box_quantity_edit)

        # ✅ 활성 여부 (1: 활성, 0: 비활성)
        self.active_edit = QComboBox()
        self.active_edit.addItems(["1 - 활성", "0 - 비활성"])
        form_layout.addRow("활성 여부:", self.active_edit)

        # ✅ 카테고리
        self.category_edit = QLineEdit()
        form_layout.addRow("카테고리:", self.category_edit)

        layout.addLayout(form_layout)

        # ✅ 버튼 추가
        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("확인")
        self.cancel_button = QPushButton("취소")
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # ✅ 버튼 이벤트 연결
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # ✅ 기존 상품 정보가 있으면 값 채우기 (수정 모드)
        if product:
            self.brand_id_edit.setText(str(product.get("brand_id", "")))
            self.name_edit.setText(product.get("product_name", ""))
            self.barcode_edit.setText(product.get("barcode", ""))
            self.price_edit.setText(str(product.get("default_price", "0")))
            self.incentive_edit.setText(str(product.get("incentive", "0")))
            self.stock_edit.setText(str(product.get("stock", "0")))
            self.box_quantity_edit.setText(str(product.get("box_quantity", "1")))
            self.active_edit.setCurrentIndex(0 if product.get("is_active", 1) == 1 else 1)
            self.category_edit.setText(product.get("category", ""))


class ProductLeftWidget(BaseLeftTableWidget):
    def __init__(self, parent=None):
        labels = [
            "상품 ID",        # 0
            "브랜드 ID",      # 1
            "상품명",         # 2
            "바코드",         # 3
            "기본 가격",      # 4
            "인센티브",       # 5
            "재고 수량",      # 6
            "박스당 수량",    # 7
            "카테고리"       # 8
        ]
        super().__init__(row_count=len(labels), labels=labels, parent=parent)
         # ✅ "삭제" 버튼 추가 (BaseLeftTableWidget의 btn_layout에 추가)
        self.btn_delete = QPushButton("삭제")
        self.layout().itemAt(1).layout().addWidget(self.btn_delete)

        # ✅ 버튼 클릭 이벤트 연결
        self.btn_new.clicked.connect(self.create_product)
        self.btn_edit.clicked.connect(self.update_product)
        self.btn_delete.clicked.connect(self.delete_product)
    def display_product(self, product):
        """
        검색된 상품 정보를 왼쪽 패널에 표시하는 함수
        """
        if not hasattr(self, "table_info") or self.table_info is None:
            print("Error: table_info is None or deleted")
            return

        if not product:
            # 검색 결과가 없으면 모든 칸 초기화
            for r in range(self.row_count):
                self.set_value(r, "")
            return

        # ✅ 상품 정보 표시 (id 및 brand_id 추가)
        self.set_value(0, str(product.get("id", "")))  # 상품 ID
        self.set_value(1, str(product.get("brand_id", "")))  # 브랜드 ID
        self.set_value(2, product.get("product_name", ""))
        self.set_value(3, product.get("barcode", ""))
        self.set_value(4, str(product.get("default_price", "")))
        self.set_value(5, str(product.get("incentive", "")))
        self.set_value(6, str(product.get("stock", "")))
        self.set_value(7, str(product.get("box_quantity", "")))
        self.set_value(8, product.get("category", ""))
        
    def create_product(self):
        """
        상품 신규 등록
        """
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        dialog = ProductDialog("신규 상품 등록")  # ✅ `ProductDialog` 사용
        if dialog.exec_() == QDialog.Accepted:
            data = {
                "brand_id": int(dialog.brand_id_edit.text() or 0),
                "product_name": dialog.name_edit.text(),
                "barcode": dialog.barcode_edit.text(),
                "default_price": float(dialog.price_edit.text() or 0),
                "stock": int(dialog.stock_edit.text() or 0),
                "is_active": 1 if "1" in dialog.active_edit.currentText() else 0,
                "incentive": float(dialog.incentive_edit.text() or 0),
                "box_quantity": int(dialog.box_quantity_edit.text() or 1),
                "category": dialog.category_edit.text()
            }
            resp = api_create_product(global_token, data)
            if resp and resp.status_code in (200, 201):
                QMessageBox.information(self, "성공", "상품 등록 완료!")
            else:
                QMessageBox.critical(self, "실패", f"상품 등록 실패: {resp.status_code}\n{resp.text}")
        
    def update_product(self):
        """
        상품 ID를 기준으로 수정
        """
        global global_token
        product_id = self.get_value(0).strip()  # ✅ 상품 ID 가져오기
        if not product_id:
            QMessageBox.warning(self, "주의", "수정할 상품 ID가 없습니다.")
            return

        # ✅ 기존 상품 정보 불러오기
        current_product = {
            "id": self.get_value(0),  # ✅ 상품 ID 유지
            "brand_id": self.get_value(1),  # ✅ 브랜드 ID 유지
            "product_name": self.get_value(2),
            "barcode": self.get_value(3),
            "default_price": self.get_value(4) or "0",
            "incentive": self.get_value(5) or "0",
            "stock": self.get_value(6) or "0",
            "box_quantity": self.get_value(7) or "1",
            "is_active": 1,
            "category": self.get_value(8) or "",
            
        }

        # ✅ 상품 수정 다이얼로그 실행
        dialog = ProductDialog("상품 수정", product=current_product)
        if dialog.exec_() == QDialog.Accepted:
            try:
                data = {
                    "id": int(product_id),  # ✅ 상품 ID 유지
                    "product_name": dialog.name_edit.text().strip(),
                    "barcode": dialog.barcode_edit.text().strip(),
                    "default_price": float(dialog.price_edit.text().strip() or 0),
                    "stock": int(dialog.stock_edit.text().strip() or 0),
                    "is_active": 1 if "1" in dialog.active_edit.currentText() else 0,
                    "incentive": float(dialog.incentive_edit.text().strip() or 0),
                    "box_quantity": int(dialog.box_quantity_edit.text().strip() or 1),
                    "category": dialog.category_edit.text().strip(),
                    "brand_id": int(dialog.brand_id_edit.text().strip() or 0)  # ✅ 브랜드 ID 유지
                }
            except ValueError as e:
                QMessageBox.critical(self, "오류", f"잘못된 입력값: {e}")
                return

            # ✅ 상품 ID로 업데이트 요청
            resp = api_update_product_by_id(global_token, product_id, data)
            if resp and resp.status_code == 200:
                QMessageBox.information(self, "성공", "상품 수정 완료!")
            else:
                QMessageBox.critical(self, "실패", f"상품 수정 실패: {resp.status_code}\n{resp.text}")

    def delete_product(self):
        """
        상품 ID를 기준으로 삭제
        """
        global global_token
        product_id = self.get_value(0).strip()  # ✅ 상품 ID 가져오기
        if not product_id:
            QMessageBox.warning(self, "주의", "삭제할 상품 ID가 없습니다.")
            return

        reply = QMessageBox.question(
            self,
            "상품 삭제 확인",
            f"정말 상품 ID {product_id}를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            resp = api_delete_product_by_id(global_token, product_id)  # ✅ 상품 ID로 삭제 요청
            if resp and resp.status_code == 200:
                QMessageBox.information(self, "성공", f"상품 ID {product_id} 삭제 완료!")
                # 삭제 후, 테이블 초기화
                for r in range(self.row_count):
                    self.set_value(r, "")
            else:
                QMessageBox.critical(self, "실패", f"상품 삭제 실패: {resp.status_code}\n{resp.text}")

                
class ProductRightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()

        # 향후 상품 관련 데이터 및 통계를 표시할 공간
        self.box1 = QGroupBox("상품 매출 통계")
        self.label1 = QLabel("여기에 상품별 매출 분석을 표시할 예정")
        layout.addWidget(self.box1)
        self.box1_layout = QVBoxLayout()
        self.box1_layout.addWidget(self.label1)
        self.box1.setLayout(self.box1_layout)

        self.box2 = QGroupBox("상품 재고 현황")
        self.label2 = QLabel("여기에 상품 재고 데이터를 표시할 예정")
        layout.addWidget(self.box2)
        self.box2_layout = QVBoxLayout()
        self.box2_layout.addWidget(self.label2)
        self.box2.setLayout(self.box2_layout)

        self.setLayout(layout)

class ProductsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout()

        # 왼쪽 패널: 상품 정보 표시 (검색 후 선택된 상품 정보)
        self.left_widget = ProductLeftWidget()
        main_layout.addWidget(self.left_widget, 1)  # 왼쪽 패널 크기 비율 1

        # 오른쪽 패널: 상품 관련 데이터 (통계 및 분석)
        self.right_panel = ProductRightPanel()
        main_layout.addWidget(self.right_panel, 5)  # 오른쪽 패널 크기 비율 5

        self.setLayout(main_layout)

    
    def do_search(self, search_text):
        """
        상품명 또는 바코드로 검색 기능 수행
        """
        global global_token
        search_text = search_text.strip()
        if not search_text:
            QMessageBox.warning(self, "경고", "검색어를 입력하세요.")
            return

        try:
            products = api_fetch_products(global_token, search_name=search_text)  # ✅ `dict` 반환 확인
            if not isinstance(products, dict):  # ✅ `dict`인지 확인
                QMessageBox.critical(self, "오류", "상품 목록 응답이 잘못되었습니다.")
                return

            self.left_widget.table_info.setRowCount(0)  

            for category, items in products.items():
                row = self.left_widget.table_info.rowCount()
                self.left_widget.table_info.insertRow(row)
                category_item = QTableWidgetItem(category)
                category_item.setFont(QFont("Arial", 9, QFont.Bold))
                category_item.setTextAlignment(Qt.AlignCenter)
                self.left_widget.table_info.setSpan(row, 0, 1, 3)
                self.left_widget.table_info.setItem(row, 0, category_item)

                for prod in items:
                    row = self.left_widget.table_info.rowCount()
                    self.left_widget.table_info.insertRow(row)
                    self.left_widget.table_info.setItem(row, 0, QTableWidgetItem(str(prod.get("id", "N/A"))))
                    self.left_widget.table_info.setItem(row, 1, QTableWidgetItem(prod.get("product_name", "Unknown")))
                    self.left_widget.table_info.setItem(row, 2, QTableWidgetItem(prod.get("barcode", "-")))

        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))


        # Filter products based on the keyword
        filtered_products = [p for p in products if "product_name" in p and search_text.lower() in p["product_name"].lower()]

        if not filtered_products:
            self.left_widget.display_product(None)
            QMessageBox.information(self, "검색 결과", "검색 결과가 없습니다.")
            return

        if len(filtered_products) == 1:
            # 검색 결과가 1개면 자동 선택
            self.left_widget.display_product(filtered_products[0])
        else:
            # 검색 결과가 여러 개일 경우 팝업 창 띄우기
            dialog = ProductSelectionDialog(filtered_products, parent=self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_product:
                self.left_widget.display_product(dialog.selected_product)




class OrderLeftWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()

        # 직원 목록 (세로 버튼)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.employee_container = QWidget()
        self.employee_layout = QVBoxLayout(self.employee_container)

        # ✅ 서버에서 직원 목록 불러오기
        self.employee_buttons = []  # 버튼 목록 저장
        self.load_employees()

        self.scroll_area.setWidget(self.employee_container)
        layout.addWidget(self.scroll_area)

        # ✅ 전체 주문 버튼
        self.total_label = QLabel("전체 주문 조회")
        self.total_date_picker = QDateEdit()
        self.total_date_picker.setCalendarPopup(True)
        self.total_date_picker.setDate(QDate.currentDate())

        self.total_button = QPushButton("전체 주문 보기")
        layout.addWidget(self.total_label)
        layout.addWidget(self.total_date_picker)
        layout.addWidget(self.total_button)

        self.setLayout(layout)

    def load_employees(self):
        """
        서버에서 직원 목록을 가져와 버튼을 생성
        """
        global global_token
        url = f"{BASE_URL}/employees/"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                employees = resp.json()
            else:
                employees = []
        except Exception as e:
            print(f"❌ 직원 목록 가져오기 실패: {e}")
            employees = []

        # ✅ 직원 목록 버튼 추가
        for employee in employees:
            btn = QPushButton(employee.get("name", "알 수 없음"))
            btn.clicked.connect(lambda checked, n=employee["name"]: self.select_employee(n))
            self.employee_layout.addWidget(btn)
            self.employee_buttons.append(btn)

    def select_employee(self, employee_name):
        """
        특정 직원의 주문을 조회 (추후 기능 추가 예정)
        """
        print(f"직원 {employee_name}의 주문을 조회합니다.")



class OrderRightWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.current_products = []  # ✅ 상품 목록 저장 (resizeEvent에서 참조 가능)

        # ✅ 타이틀 + 새로고침 버튼 추가
        self.header_layout = QVBoxLayout()
        self.title = QLabel("📋 주문 내역")
        self.title.setFont(QFont("Arial", 9, QFont.Bold))  # ✅ 폰트 크기 9로 설정 (헤더)
        self.refresh_button = QPushButton("🔄 새로고침")
        self.refresh_button.setFont(QFont("Arial", 8))
        self.refresh_button.clicked.connect(self.refresh_orders)  # ✅ 새로고침 기능 연결
        self.header_layout.addWidget(self.title)
        self.header_layout.addWidget(self.refresh_button)
        self.layout.addLayout(self.header_layout)

        # ✅ 상품 목록을 배치할 레이아웃
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)  # ✅ 창 크기에 따라 동적 정렬
        self.layout.addWidget(self.container)

        self.setLayout(self.layout)
        self.load_products()  # ✅ 서버에서 상품 목록 로드

    def load_products(self):
        """
        서버에서 상품 목록을 가져와 `카테고리`별로 정리 후 표시
        """
        global global_token
        url = f"{BASE_URL}/products/all"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                self.current_products = [p for p in resp.json() if p["is_active"] == 1]  # ✅ 상품 목록 저장
            else:
                self.current_products = []
        except Exception as e:
            print(f"❌ 상품 목록 가져오기 실패: {e}")
            self.current_products = []

        self.populate_table()

    def populate_table(self):
        """
        하나의 테이블에서 `카테고리 -> 품명 -> 갯수` 순으로 정렬,
        세로 공간이 부족하면 자동으로 옆 칸으로 이동하며 빈 행 제거,
        글씨 크기를 자동 조정하여 모든 내용을 표시
        """
        # ✅ 기존 테이블 초기화
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        # ✅ 사용 가능한 세로 공간 계산 (제목, 버튼, 빈 공간 제외)
        available_height = self.height() - self.header_layout.sizeHint().height() - 80  # ✅ 정확한 여백 적용
        row_height = 30  # ✅ 행 높이를 수동 설정 (20px)
        max_rows_per_section = max(5, available_height // row_height)  # ✅ 세로 공간에 맞는 최대 행 수 결정

        row = 0  # ✅ 오류 해결: `row, col = 0` → `row = 0, col = 0`
        col = 0  # ✅ 오류 해결

        # ✅ 상품을 `카테고리 -> 품명` 순으로 정리
        sorted_products = []
        for p in self.current_products:
            sorted_products.append((p["category"], p["brand_id"], p["product_name"]))

        sorted_products.sort()  # ✅ 카테고리 순으로 정렬

        # ✅ 테이블 초기화 (처음에 빈 표 만들지 않음)
        table = None
        row_index = 0
        current_category = None
        current_brand = None
        for category, brand, product_name in sorted_products:
            # ✅ 새로운 칸이 필요하면 테이블 생성
            if row_index == 0 or table is None:
                table = QTableWidget()
                table.setColumnCount(2)  # ✅ [품명, 갯수]만 표시
                table.setHorizontalHeaderLabels(["품명", "갯수"])
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # ✅ 열 크기 자동 조정 (가로)
                table.setFont(QFont("Arial", 9))  # ✅ 기본 글씨 크기 7
                table.verticalHeader().setVisible(False)  # ✅ 왼쪽 숫자(인덱스) 헤더 제거
                table.setRowCount(0)  # ✅ 빈 행 제거

            if current_category != category:
                # ✅ 카테고리 변경 시 새로운 행 추가 (2열 병합)
                table.insertRow(table.rowCount())
                category_item = QTableWidgetItem(category)
                category_item.setFont(QFont("Arial", 9, QFont.Bold))
                category_item.setTextAlignment(Qt.AlignCenter)
                table.setSpan(table.rowCount() - 1, 0, 1, 2)  # ✅ 2열 병합
                table.setItem(table.rowCount() - 1, 0, category_item)
                current_category = category

            if current_brand != brand:
                # ✅ 브랜드 변경 시 새로운 행 추가
                # table.insertRow(table.rowCount())
                # brand_item = QTableWidgetItem(f"브랜드 {brand}")
                # brand_item.setFont(QFont("Arial", 7, QFont.Bold))
                # table.setItem(table.rowCount() - 1, 0, brand_item)
                current_brand = brand

            # ✅ 상품 추가
            table.insertRow(table.rowCount())
            table.setItem(table.rowCount() - 1, 0, self.create_resized_text(product_name, table))
            table.setItem(table.rowCount() - 1, 1, QTableWidgetItem(""))  # ✅ 주문 수량 (추후 서버에서 가져올 예정)

            # ✅ 행 높이를 수동으로 설정 (20px)
            table.setRowHeight(table.rowCount() - 1, 12)

            row_index += 1

            # ✅ 현재 세로 공간을 초과하면 오른쪽 칸으로 이동
            if row_index >= max_rows_per_section:
                self.grid_layout.addWidget(table, row, col, 1, 1)
                row_index = 0
                col += 1  # ✅ 다음 칸으로 이동
                table = None  # ✅ 새 테이블 생성 필요

        # ✅ 마지막 테이블 추가
        if table is not None:
            self.grid_layout.addWidget(table, row, col, 1, 1)

    def create_resized_text(self, text, table):
        """
        칸 크기에 맞춰 글씨 크기를 자동으로 조정하여 텍스트가 잘리지 않도록 함
        """
        font = QFont("Arial", 9)  # 기본 글씨 크기 7
        metrics = QFontMetrics(font)
        max_width = table.columnWidth(0) - 5  # 셀 너비 계산

        while metrics.width(text) > max_width and font.pointSize() > 5:
            font.setPointSize(font.pointSize() - 1)
            metrics = QFontMetrics(font)

        item = QTableWidgetItem(text)
        item.setFont(font)
        return item

    def resizeEvent(self, event: QResizeEvent):
        """
        창 크기 변경 시 자동으로 정렬 조정
        """
        self.populate_table()
        event.accept()

    def refresh_orders(self):
        """
        새로고침 버튼 클릭 시 상품 목록 갱신
        """
        self.load_products()



class OrdersTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout()

        # 왼쪽 패널: 직원 목록 (세로 버튼 + 날짜 선택)
        self.left_widget = OrderLeftWidget()
        main_layout.addWidget(self.left_widget, 1)  # 왼쪽 패널 크기 비율 1

        # 오른쪽 패널: 상품 분류별, 브랜드별 정리 + 주문 갯수 입력
        self.right_panel = OrderRightWidget()
        main_layout.addWidget(self.right_panel, 5)  # 오른쪽 패널 크기 비율 5

        self.setLayout(main_layout)
    def do_search(self, keyword):
        pass
class PurchasesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """
        매입 UI 초기화
        """
        main_layout = QHBoxLayout()

        # 왼쪽 패널 (상품 검색 + 매입 입력)
        self.left_panel = QGroupBox("상품 매입")
        left_layout = QVBoxLayout()

        # 검색창
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("상품명 입력")
        self.search_button = QPushButton("검색")
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.search_button)
        left_layout.addLayout(search_layout)

        # 상품 목록
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(["ID", "상품명", "재고", "가격"])
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        left_layout.addWidget(self.product_table)

        # 매입 입력 (상품 ID, 매입 수량)
        self.selected_product_id = QLineEdit()
        self.selected_product_id.setPlaceholderText("선택된 상품 ID")
        self.selected_product_id.setReadOnly(True)
        self.purchase_quantity = QSpinBox()
        self.purchase_quantity.setMinimum(1)
        self.purchase_quantity.setMaximum(1000)

        left_layout.addWidget(QLabel("매입 상품 ID:"))
        left_layout.addWidget(self.selected_product_id)
        left_layout.addWidget(QLabel("매입 수량:"))
        left_layout.addWidget(self.purchase_quantity)

        # 매입 버튼
        self.purchase_button = QPushButton("매입 등록")
        left_layout.addWidget(self.purchase_button)

        self.left_panel.setLayout(left_layout)
        main_layout.addWidget(self.left_panel, 2)

        # ✅ 오른쪽 패널 (매입 내역 조회)
        self.right_panel = QGroupBox("매입 내역")
        right_layout = QVBoxLayout()

        # ✅ 매입 내역 테이블 추가
        self.purchase_history_table = QTableWidget()
        self.purchase_history_table.setColumnCount(5)
        self.purchase_history_table.setHorizontalHeaderLabels(["ID", "상품명", "매입 수량", "단가", "매입일"])
        self.purchase_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.purchase_history_table)

        self.right_panel.setLayout(right_layout)
        main_layout.addWidget(self.right_panel, 3)

        self.setLayout(main_layout)

        # 이벤트 연결
        self.search_button.clicked.connect(self.search_products)
        self.product_table.itemSelectionChanged.connect(self.select_product)
        self.purchase_button.clicked.connect(self.register_purchase)

        # ✅ 매입 내역 불러오기
        self.load_purchase_history()
        # 초기 상품 목록 로드
        self.search_products()
        
    def load_purchase_history(self):
        """
        최근 매입 내역 조회 (서버에서 가져오기)
        """
        global global_token
        purchases = api_fetch_purchases(global_token)  # ✅ 매입 내역 가져오기

        self.purchase_history_table.setRowCount(0)
        purchases.sort(key=lambda x: x["purchase_date"], reverse=True)  # ✅ 최신순 정렬

        for purchase in purchases:
            row = self.purchase_history_table.rowCount()
            self.purchase_history_table.insertRow(row)
            self.purchase_history_table.setItem(row, 0, QTableWidgetItem(str(purchase.get("id", ""))))
            self.purchase_history_table.setItem(row, 1, QTableWidgetItem(purchase.get("product_name", "N/A")))
            self.purchase_history_table.setItem(row, 2, QTableWidgetItem(str(purchase.get("quantity", 0))))
            self.purchase_history_table.setItem(row, 3, QTableWidgetItem(str(purchase.get("unit_price", 0))))
            self.purchase_history_table.setItem(row, 4, QTableWidgetItem(purchase.get("purchase_date", "N/A")))
        

    def search_products(self):
        """
        상품 검색 (서버에서 가져오기)
        """
        global global_token
        keyword = self.search_edit.text().strip()

        try:
            response = api_fetch_products(global_token)
            products = response.json()  # ✅ API 응답을 JSON으로 변환
        except Exception as e:
            print(f"❌ 상품 목록 불러오기 실패: {e}")
            QMessageBox.critical(self, "실패", "상품 목록을 불러올 수 없습니다.")
            return

        # 🔹 API 응답이 딕셔너리인 경우, 모든 카테고리의 상품을 리스트로 합침
        if isinstance(products, dict):
            all_products = []
            for category, product_list in products.items():
                if isinstance(product_list, list):  # ✅ 각 카테고리의 상품 리스트가 올바른지 확인
                    all_products.extend(product_list)  # ✅ 전체 리스트에 추가

            products = all_products  # ✅ 최종적으로 리스트 형태로 변환

        # 🔹 검색어 필터링 (상품명이 존재하는 경우만)
        filtered_products = [p for p in products if isinstance(p, dict) and keyword.lower() in p.get("product_name", "").lower()]

        self.product_table.setRowCount(0)
        for product in filtered_products:
            row = self.product_table.rowCount()
            self.product_table.insertRow(row)
            self.product_table.setItem(row, 0, QTableWidgetItem(str(product.get("id", ""))))
            self.product_table.setItem(row, 1, QTableWidgetItem(product.get("product_name", "N/A")))
            self.product_table.setItem(row, 2, QTableWidgetItem(str(product.get("stock", 0))))
            self.product_table.setItem(row, 3, QTableWidgetItem(str(product.get("default_price", 0))))

    def select_product(self):
        """
        선택한 상품 정보를 가져옴
        """
        selected_items = self.product_table.selectedItems()
        if not selected_items:
            return

        product_id = selected_items[0].text()
        self.selected_product_id.setText(product_id)

    def register_purchase(self):
        """
        상품 매입 등록 (서버로 전송)
        """
        global global_token
        product_id = self.selected_product_id.text().strip()
        quantity = self.purchase_quantity.value()

        if not product_id:
            QMessageBox.warning(self, "경고", "상품을 선택하세요.")
            return

        try:
            product_id = int(product_id)
        except ValueError:
            QMessageBox.warning(self, "경고", "잘못된 상품 ID입니다.")
            return

        print("📌 서버로 보낼 데이터:", {"product_id": product_id, "stock_increase": quantity})  # 🔍 디버깅 출력

        resp = api_update_product_stock(global_token, product_id, quantity)  # ✅ 재고 업데이트 API 호출

        if resp is None:
            QMessageBox.critical(self, "실패", "매입 등록 실패: 서버 응답 없음")
            return

        if resp.status_code == 200:
            QMessageBox.information(self, "성공", "매입이 등록되었습니다.")
            self.search_products()  # 상품 목록 새로고침
            self.load_purchase_history()  # 매입 내역 새로고침
        else:
            print(f"❌ 매입 등록 실패: {resp.status_code} {resp.text}")
            QMessageBox.critical(self, "실패", f"매입 등록 실패: {resp.status_code}\n{resp.text}")

    def load_purchase_history(self):
        """
        최근 매입 내역 조회 (서버에서 가져오기)
        """
        global global_token
        purchases = api_fetch_purchases(global_token)  # 서버에서 매입 내역 가져오기

        self.purchase_history_table.setRowCount(0)
        for purchase in purchases:
            row = self.purchase_history_table.rowCount()
            self.purchase_history_table.insertRow(row)
            self.purchase_history_table.setItem(row, 0, QTableWidgetItem(str(purchase["id"])))
            self.purchase_history_table.setItem(row, 1, QTableWidgetItem(purchase["product_name"]))
            self.purchase_history_table.setItem(row, 2, QTableWidgetItem(str(purchase["quantity"])))
            self.purchase_history_table.setItem(row, 3, QTableWidgetItem(str(purchase["unit_price"])))
            self.purchase_history_table.setItem(row, 4, QTableWidgetItem(purchase["purchase_date"]))


class TotalSalesTab(QWidget):
    """
    총매출 탭 (예시)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        left_panel = QGroupBox("총 매출 조회")
        left_layout = QFormLayout()

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        left_layout.addRow("날짜(예: 2025-03-01):", self.date_edit)

        self.btn_fetch_total = QPushButton("Fetch Total Sales (Example)")
        self.btn_fetch_total.clicked.connect(self.fetch_total_sales)
        left_layout.addRow(self.btn_fetch_total)

        left_panel.setLayout(left_layout)

        right_panel = QGroupBox("총매출 결과")
        right_layout = QVBoxLayout()

        self.total_sales_table = QTableWidget()
        self.total_sales_table.setColumnCount(2)
        self.total_sales_table.setHorizontalHeaderLabels(["ClientID","TotalSales"])
        self.total_sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.total_sales_table)

        right_panel.setLayout(right_layout)

        main_layout.addWidget(left_panel,1)
        main_layout.addWidget(right_panel,4)
        self.setLayout(main_layout)

    def fetch_total_sales(self):
        global global_token
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        try:
            # 예: /sales/total/{YYYY-MM-DD}
            url = f"{BASE_URL}/sales/total/{date_str}"
            headers = {"Authorization": f"Bearer {global_token}"}
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                self.total_sales_table.setRowCount(0)
                for item in data:
                    row = self.total_sales_table.rowCount()
                    self.total_sales_table.insertRow(row)
                    self.total_sales_table.setItem(row, 0, QTableWidgetItem(str(item.get("client_id",""))))
                    self.total_sales_table.setItem(row, 1, QTableWidgetItem(str(item.get("total_sales",""))))
            else:
                QMessageBox.critical(self, "실패", f"Fetch total sales failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

class EmployeeVehicleTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        search_group = QGroupBox("직원 차량 관리 조회")
        search_layout = QFormLayout()
        self.emp_id_search_edit = QLineEdit()
        search_layout.addRow("Employee ID:", self.emp_id_search_edit)
        self.search_btn = QPushButton("조회")
        self.search_btn.clicked.connect(self.fetch_vehicle)
        search_layout.addRow(self.search_btn)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        info_group = QGroupBox("직원 차량 관리 정보")
        info_layout = QFormLayout()
        self.emp_id_edit = QLineEdit()
        info_layout.addRow("Employee ID:", self.emp_id_edit)
        self.monthly_fuel_edit = QLineEdit()
        info_layout.addRow("1달 주유비:", self.monthly_fuel_edit)
        self.current_mileage_edit = QLineEdit()
        info_layout.addRow("현재 주행거리:", self.current_mileage_edit)
        self.oil_change_date_edit = QDateEdit()
        self.oil_change_date_edit.setCalendarPopup(True)
        self.oil_change_date_edit.setDate(QDate.currentDate())
        info_layout.addRow("엔진오일 교체일:", self.oil_change_date_edit)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        btn_layout = QHBoxLayout()
        self.btn_create = QPushButton("생성")
        self.btn_create.clicked.connect(self.create_vehicle)
        self.btn_update = QPushButton("수정")
        self.btn_update.clicked.connect(self.update_vehicle)
        self.btn_delete = QPushButton("삭제")
        self.btn_delete.clicked.connect(self.delete_vehicle)
        btn_layout.addWidget(self.btn_create)
        btn_layout.addWidget(self.btn_update)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

        self.vehicle_table = QTableWidget()
        self.vehicle_table.setColumnCount(5)
        self.vehicle_table.setHorizontalHeaderLabels(["ID","Employee ID","주유비","주행거리","오일교체일"])
        self.vehicle_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.vehicle_table)

        self.setLayout(layout)

    
    def create_vehicle(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "No token.")
            return
        try:
            data = {
                "employee_id": int(self.emp_id_edit.text() or 0),  # ✅ id 대신 employee_id 사용
                "monthly_fuel_cost": float(self.monthly_fuel_edit.text() or 0),
                "current_mileage": int(self.current_mileage_edit.text() or 0),
                "last_engine_oil_change": self.oil_change_date_edit.date().toString("yyyy-MM-dd")
            }
            resp = api_create_vehicle(global_token, data)
            resp.raise_for_status()
            QMessageBox.information(self, "성공", "차량 정보 생성/갱신")
            self.fetch_vehicle()
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))


    def fetch_vehicle(self):
        global global_token
        emp_id = self.emp_id_search_edit.text().strip()
        if not emp_id:
            QMessageBox.warning(self, "경고", "직원ID를 입력하세요.")
            return
        try:
            resp = api_fetch_vehicle(global_token)
            resp.raise_for_status()
            vehicles = resp.json()
            filtered = [v for v in vehicles if v.get("id") == int(emp_id)]
            self.vehicle_table.setRowCount(0)
            for v in filtered:
                row = self.vehicle_table.rowCount()
                self.vehicle_table.insertRow(row)
                self.vehicle_table.setItem(row, 0, QTableWidgetItem(str(v.get("id",""))))
                self.vehicle_table.setItem(row, 1, QTableWidgetItem(str(v.get("id","")))) 
                self.vehicle_table.setItem(row, 2, QTableWidgetItem(str(v.get("monthly_fuel_cost",""))))
                self.vehicle_table.setItem(row, 3, QTableWidgetItem(str(v.get("current_mileage",""))))
                self.vehicle_table.setItem(row, 4, QTableWidgetItem(str(v.get("last_engine_oil_change",""))))
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

    def update_vehicle(self):
        global global_token
        vehicle_id, ok = QInputDialog.getInt(self, "차량 수정", "차량(ID=직원ID):")
        if not ok:
            return
        try:
            data = {
                "id": vehicle_id,
                "monthly_fuel_cost": float(self.monthly_fuel_edit.text() or 0),
                "current_mileage": int(self.current_mileage_edit.text() or 0),
                "last_engine_oil_change": self.oil_change_date_edit.date().toString("yyyy-MM-dd")
            }
            resp = api_update_vehicle(global_token, vehicle_id, data)
            resp.raise_for_status()
            QMessageBox.information(self, "성공", "차량 수정 완료")
            self.fetch_vehicle()
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

    def delete_vehicle(self):
        global global_token
        vehicle_id, ok = QInputDialog.getInt(self, "차량 삭제", "차량ID(직원ID)")
        if not ok:
            return
        try:
            resp = api_delete_vehicle(global_token, vehicle_id)
            resp.raise_for_status()
            QMessageBox.information(self, "성공", "차량 삭제 완료!")
            self.fetch_vehicle()
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

class EmployeeClientTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        left_panel = QGroupBox("직원-거래처 연결")
        left_layout = QFormLayout()
        self.emp_id_edit = QLineEdit()
        left_layout.addRow("직원 ID:", self.emp_id_edit)
        self.client_id_edit = QLineEdit()
        left_layout.addRow("거래처 ID:", self.client_id_edit)

        self.btn_assign = QPushButton("연결(Assign)")
        self.btn_assign.clicked.connect(self.assign_emp_client)
        left_layout.addRow(self.btn_assign)

        left_panel.setLayout(left_layout)

        right_panel = QGroupBox("직원-거래처 목록")
        right_layout = QVBoxLayout()
        self.ec_table = QTableWidget()
        self.ec_table.setColumnCount(4)
        self.ec_table.setHorizontalHeaderLabels(["ID","EmployeeID","ClientID","StartDate"])
        self.ec_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.ec_table)

        self.btn_refresh_ec = QPushButton("Refresh Emp-Client")
        self.btn_refresh_ec.clicked.connect(self.load_ec_relations)
        right_layout.addWidget(self.btn_refresh_ec)

        right_panel.setLayout(right_layout)

        main_layout.addWidget(left_panel,1)
        main_layout.addWidget(right_panel,4)
        self.setLayout(main_layout)

    def assign_emp_client(self):
        global global_token
        emp_id = self.emp_id_edit.text().strip()
        client_id = self.client_id_edit.text().strip()
        if not emp_id or not client_id:
            QMessageBox.warning(self, "경고", "직원ID, 거래처ID 모두 입력하세요.")
            return
        try:
            resp = api_assign_employee_client(global_token, int(emp_id), int(client_id))
            if resp.status_code in (200,201):
                QMessageBox.information(self, "성공", "연결 완료!")
                self.load_ec_relations()
            else:
                QMessageBox.critical(self, "실패", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

    def load_ec_relations(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "No token.")
            return
        try:
            resp = api_fetch_employee_clients_all(global_token)
            if resp.status_code == 200:
                data = resp.json()
                self.ec_table.setRowCount(0)
                for ec in data:
                    row = self.ec_table.rowCount()
                    self.ec_table.insertRow(row)
                    self.ec_table.setItem(row, 0, QTableWidgetItem(str(ec.get("id",""))))
                    self.ec_table.setItem(row, 1, QTableWidgetItem(str(ec.get("employee_id",""))))
                    self.ec_table.setItem(row, 2, QTableWidgetItem(str(ec.get("client_id",""))))
                    self.ec_table.setItem(row, 3, QTableWidgetItem(str(ec.get("start_date",""))))
            else:
                QMessageBox.critical(self, "실패", f"load relations fail: {resp.status_code}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

class BrandProductTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        left_panel = QGroupBox("브랜드별 제품조회")
        left_layout = QFormLayout()
        self.brand_id_edit = QLineEdit()
        left_layout.addRow("브랜드 ID:", self.brand_id_edit)
        self.btn_show = QPushButton("Show Products")
        self.btn_show.clicked.connect(self.show_brand_products)
        left_layout.addRow(self.btn_show)
        left_panel.setLayout(left_layout)

        right_panel = QGroupBox("브랜드 상품 목록")
        right_layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID","ProductName","Barcode"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.table)
        right_panel.setLayout(right_layout)

        main_layout.addWidget(left_panel,1)
        main_layout.addWidget(right_panel,4)
        self.setLayout(main_layout)

    def show_brand_products(self):
        global global_token
        brand_id = self.brand_id_edit.text().strip()
        if not brand_id:
            QMessageBox.warning(self, "경고", "브랜드ID를 입력하세요.")
            return
        try:
            categorized_products = api_fetch_brand_products(global_token, int(brand_id))  # ✅ 카테고리별 데이터

            if not isinstance(categorized_products, dict):  # ✅ 올바른 형식인지 확인
                QMessageBox.critical(self, "실패", "브랜드 상품 목록을 가져오는 데 실패했습니다.")
                return

            self.table.setRowCount(0)

            for category, products in categorized_products.items():
                # ✅ 카테고리 헤더 추가
                row = self.table.rowCount()
                self.table.insertRow(row)
                category_item = QTableWidgetItem(category)
                category_item.setFont(QFont("Arial", 9, QFont.Bold))
                category_item.setTextAlignment(Qt.AlignCenter)
                self.table.setSpan(row, 0, 1, 3)  # ✅ 카테고리 제목을 3열 전체에 적용
                self.table.setItem(row, 0, category_item)

                for prod in products:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(str(prod.get("id", "N/A"))))
                    self.table.setItem(row, 1, QTableWidgetItem(prod.get("product_name", "Unknown")))
                    self.table.setItem(row, 2, QTableWidgetItem(prod.get("barcode", "-")))

        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))



# ----------------------------
# Main Window
# ----------------------------
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Merged UI")
        self.setGeometry(0,0,1980,1080)
        self.setStyleSheet(load_dark_theme())

        self.init_ui()

    def init_ui(self):
        ## 1) 상단 아이콘 툴바
        self.toolbar = QToolBar("메인 메뉴")
        self.toolbar.setIconSize(QSize(50,100))
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # 예시 아이콘
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_employee = QIcon(os.path.join(current_dir,"icons","employee.png"))
        icon_client   = QIcon(os.path.join(current_dir,"icons","correspondent.png"))
        icon_product  = QIcon(os.path.join(current_dir,"icons","product.png"))
        icon_order    = QIcon(os.path.join(current_dir,"icons","orders.png"))
        icon_sales    = QIcon(os.path.join(current_dir,"icons","sales.png"))
        icon_totalsales=QIcon(os.path.join(current_dir,"icons","totalsales.png"))
        icon_vehicle  = QIcon(os.path.join(current_dir,"icons","vehicle.png"))
        icon_empclient= QIcon(os.path.join(current_dir,"icons","empclient.png"))
        icon_brand    = QIcon(os.path.join(current_dir,"icons","brand.png"))
        icon_employee_map = QIcon(os.path.join(current_dir, "icons", "map.png"))
        # 액션
        self.add_toolbar_action("직원", icon_employee, lambda: self.switch_tab(0))
        self.add_toolbar_action("거래처", icon_client, lambda: self.switch_tab(1))
        self.add_toolbar_action("제품", icon_product, lambda: self.switch_tab(2))
        self.add_toolbar_action("주문", icon_order, lambda: self.switch_tab(3))
        self.add_toolbar_action("매출", icon_sales, lambda: self.switch_tab(4))
        self.add_toolbar_action("총매출", icon_totalsales, lambda: self.switch_tab(5))
        self.add_toolbar_action("차량", icon_vehicle, lambda: self.switch_tab(6))
        self.add_toolbar_action("EMP-CLIENT", icon_empclient, lambda: self.switch_tab(7))
        self.add_toolbar_action("Brand", icon_brand, lambda: self.switch_tab(8))
        self.add_toolbar_action("직원 방문 지도", icon_employee_map, lambda: self.switch_tab(9))
        ## 2) 검색창 툴바
        self.search_toolbar = QToolBar("검색창")
        self.search_toolbar.setIconSize(QSize(16,16))
        self.addToolBar(Qt.TopToolBarArea, self.search_toolbar)

        self.search_label = QLabel("검색:")
        self.search_edit = QLineEdit()
        self.search_button = QPushButton("검색")

        self.search_toolbar.addWidget(self.search_label)
        self.search_toolbar.addWidget(self.search_edit)
        self.search_toolbar.addWidget(self.search_button)

        self.search_button.clicked.connect(self.on_search_clicked)  # ✅ 버튼 클릭 시 검색 실행
        self.search_edit.returnPressed.connect(self.on_search_clicked)  # ✅ Enter 키 입력 시 검색 실행 추가

        ## 3) 메인 스택
        self.stacked = QStackedWidget()
        self.setCentralWidget(self.stacked)

        # 탭들
        self.employee_tab = EmployeesTab()      # idx=0
        self.clients_tab = ClientsTab()         # idx=1
        self.products_tab = ProductsTab()       # idx=2
        self.orders_tab = OrdersTab()           # idx=3
        self.purchases_tab = PurchasesTab()             # idx=4
        self.total_sales_tab = TotalSalesTab()  # idx=5
        self.vehicle_tab = EmployeeVehicleTab() # idx=6
        self.empclient_tab = EmployeeClientTab()# idx=7
        self.brand_tab = BrandProductTab()      # idx=8
        self.employee_map_tab = EmployeesMapTab() 
        
        self.stacked.addWidget(self.employee_tab)
        self.stacked.addWidget(self.clients_tab)
        self.stacked.addWidget(self.products_tab)
        self.stacked.addWidget(self.orders_tab)
        self.stacked.addWidget(self.purchases_tab)
        self.stacked.addWidget(self.total_sales_tab)
        self.stacked.addWidget(self.vehicle_tab)
        self.stacked.addWidget(self.empclient_tab)
        self.stacked.addWidget(self.brand_tab)
        self.stacked.addWidget(self.employee_map_tab) 
        self.stacked.setCurrentIndex(0)
        self.update_search_placeholder(0)

    def add_toolbar_action(self, name, icon, callback):
        act = QAction(icon, name, self)
        act.triggered.connect(callback)
        self.toolbar.addAction(act)

    def switch_tab(self, idx):
        self.stacked.setCurrentIndex(idx)
        self.update_search_placeholder(idx)

    def on_search_clicked(self):
        idx = self.stacked.currentIndex()
        keyword = self.search_edit.text().strip()

        if idx == 0:
            self.employee_tab.do_search(keyword)
        elif idx == 1:
            self.clients_tab.do_search(keyword)
        elif idx == 2:
            self.products_tab.do_search(keyword)
        elif idx == 3:
            self.orders_tab.do_search(keyword)
        elif idx == 4:
            self.purchases_tab.do_search(keyword)
        elif idx == 5:
            self.total_sales_tab.do_search(keyword)
        elif idx == 6:
            self.vehicle_tab.do_search(keyword)
        elif idx == 7:
            self.empclient_tab.do_search(keyword)
        elif idx == 8:
            self.brand_tab.do_search(keyword)
        elif idx == 9:
            self.employee_map_tab.do_search(keyword)

    def update_search_placeholder(self, idx):
        if idx == 0:
            self.search_edit.setPlaceholderText("직원이름 검색")
        elif idx == 1:
            self.search_edit.setPlaceholderText("거래처 이름 검색")
        elif idx == 2:
            self.search_edit.setPlaceholderText("제품명 검색")
        elif idx == 3:
            self.search_edit.setPlaceholderText("주문 검색 (ex: 날짜)")
        elif idx == 4:
            self.search_edit.setPlaceholderText("매출 검색 (ex: 날짜)")
        elif idx == 5:
            self.search_edit.setPlaceholderText("총매출 검색 (ex: 날짜)")
        elif idx == 6:
            self.search_edit.setPlaceholderText("차량 검색 (직원ID?)")
        elif idx == 7:
            self.search_edit.setPlaceholderText("EMP-CLIENT 검색?")
        elif idx == 8:
            self.search_edit.setPlaceholderText("브랜드 검색?")

def main():
    app = QApplication(sys.argv)
    # 로그인
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.Accepted:
        window = MainApp()
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit()

if __name__ == "__main__":
    main()

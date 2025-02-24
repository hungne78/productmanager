#!/usr/bin/env python
import sys
import json
import requests
import openpyxl
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QGridLayout,
    QMessageBox, QFileDialog, QHeaderView, QComboBox, QInputDialog, QDateEdit, QGroupBox, QAction, QStackedWidget, QToolBar
)
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QIcon
import os

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
        border: 1px solid #555;
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
    url = f"{BASE_URL}/employees"
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
    url = f"{BASE_URL}/employees"
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
    url = f"{BASE_URL}/employee_vehicles"
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
    url = f"{BASE_URL}/clients"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_create_client(token, data):
    url = f"{BASE_URL}/clients"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_delete_client(token, client_id):
    url = f"{BASE_URL}/clients/{client_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

# 제품
def api_fetch_products(token):
    url = f"{BASE_URL}/products"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_create_product(token, data):
    url = f"{BASE_URL}/products"
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

# 주문
def api_fetch_orders(token):
    url = f"{BASE_URL}/orders"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_create_order(token, data):
    url = f"{BASE_URL}/orders"
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
    url = f"{BASE_URL}/employee_clients"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"employee_id": employee_id, "client_id": client_id}
    return requests.post(url, json=data, headers=headers)

def api_fetch_employee_clients_all(token):
    url = f"{BASE_URL}/employee_clients"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

# 직원 차량
def api_fetch_vehicle(token):
    url = f"{BASE_URL}/employee_vehicles"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_create_vehicle(token, data):
    url = f"{BASE_URL}/employee_vehicles"
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
        return self.table_info.item(row,1).text()

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
# (생략 없이 복붙)
class EmployeeLeftWidget(BaseLeftTableWidget):
    def __init__(self, parent=None):
        """
        7행(직원ID, 이름, 전화번호, 직책, 차량_주유비, 주행거리, 엔진오일교체일)을
        테이블 형태로 배치하는 UI.
        """
        labels = [
            "직원ID", "이름", "전화번호", "직책",
            "차량_주유비", "차량_주행거리", "엔진오일교체일"
        ]
        super().__init__(row_count=len(labels), labels=labels, parent=parent)

        # 상위 BaseLeftTableWidget에서 table_info + "신규등록/수정" 버튼 생성
        self.btn_new.clicked.connect(self.create_employee)
        self.btn_edit.clicked.connect(self.update_employee)

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

        # 차량 정보 (예: monthly_fuel_cost, current_mileage, last_engine_oil_change)
        # api_fetch_employee_vehicle_info(...) 로 불러와 추가 표시
        veh = api_fetch_employee_vehicle_info(employee["id"])
        if veh:
            self.set_value(4, str(veh.get("monthly_fuel_cost", "")))
            self.set_value(5, str(veh.get("current_mileage", "")))
            self.set_value(6, str(veh.get("last_engine_oil_change", "")))
        else:
            self.set_value(4, "")
            self.set_value(5, "")
            self.set_value(6, "")

    def create_employee(self):
        """
        '신규등록' 버튼 → 테이블 항목(0~6) 중 일부만 사용해서
        /employees POST 호출.
        """
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        # 테이블의 각 행의 '값'을 읽어, dict 구성
        data = {
            "password": "1234",  # 실제로는 다른 방법으로 PW 입력 받는 게 좋음
            "name": self.get_value(1),
            "phone": self.get_value(2),
            "role": self.get_value(3),
        }
        resp = api_create_employee(global_token, data)
        if resp and resp.status_code in (200, 201):
            QMessageBox.information(self, "성공", "직원 등록 완료!")
        else:
            # 실패 시 메시지
            status = resp.status_code if resp else "None"
            text = resp.text if resp else "No response"
            QMessageBox.critical(self, "실패", f"직원 등록 실패: {status}\n{text}")

    def update_employee(self):
        """
        '수정' 버튼 → table_info[0]행의 '직원ID'를 emp_id로 보고 /employees/{emp_id} PUT 호출
        """
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        emp_id = self.get_value(0).strip()
        if not emp_id:
            QMessageBox.warning(self, "주의", "수정할 직원 ID가 없습니다.")
            return

        data = {
            "password": "1234",
            "name": self.get_value(1),
            "phone": self.get_value(2),
            "role": self.get_value(3),
        }
        resp = api_update_employee(global_token, emp_id, data)
        if resp and resp.status_code == 200:
            QMessageBox.information(self, "성공", "직원 수정 완료!")
        else:
            status = resp.status_code if resp else "None"
            text = resp.text if resp else "No response"
            QMessageBox.critical(self, "실패", f"직원 수정 실패: {status}\n{text}")


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
        self.tbl_box1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box1.setHorizontalHeaderLabels([""]*12)
        box1_layout = QVBoxLayout()
        box1_layout.addWidget(self.tbl_box1)
        self.box1.setLayout(box1_layout)
        main_layout.addWidget(self.box1)

        # 2) box2
        self.box2 = QGroupBox("당해년도 월별 방문횟수")
        self.tbl_box2 = QTableWidget(2, 12)
        self.tbl_box2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box2.setHorizontalHeaderLabels([""]*12)
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
        self.tbl_box3_top.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box3_top.setHorizontalHeaderLabels([""]*15)

        self.tbl_box3_bottom = QTableWidget(2, 16)  # 16~31일
        self.tbl_box3_bottom.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box3_bottom.setHorizontalHeaderLabels([""]*16)

        v.addWidget(self.tbl_box3_top)
        v.addWidget(self.tbl_box3_bottom)
        self.box3.setLayout(v)
        main_layout.addWidget(self.box3)

        # 4) box4
        self.box4 = QGroupBox("당일 방문 거래처 정보")
        self.tbl_box4 = QTableWidget(2, 5)
        self.tbl_box4.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box4.setHorizontalHeaderLabels([""]*5)
        box4_layout = QVBoxLayout()
        box4_layout.addWidget(self.tbl_box4)
        self.box4.setLayout(box4_layout)
        main_layout.addWidget(self.box4)

        self.setLayout(main_layout)

    def update_data_example(self):
        # box1
        months = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
        sales_data = [100,200,300,400,500,600,700,800,900,1000,1100,1200]
        for c in range(12):
            self.tbl_box1.setItem(0, c, QTableWidgetItem(months[c]))
            self.tbl_box1.setItem(1, c, QTableWidgetItem(str(sales_data[c])))

        # box2
        visits_data = [5,4,7,3,8,10,5,6,3,9,12,11]
        for c in range(12):
            self.tbl_box2.setItem(0, c, QTableWidgetItem(months[c]))
            self.tbl_box2.setItem(1, c, QTableWidgetItem(str(visits_data[c])))

        # box3_top: 1~15일
        for c in range(15):
            day = c+1
            self.tbl_box3_top.setItem(0, c, QTableWidgetItem(f"{day}일"))
            self.tbl_box3_top.setItem(1, c, QTableWidgetItem(str(day*10)))
        # box3_bottom: 16~31일
        for c in range(16):
            day = c+16
            self.tbl_box3_bottom.setItem(0, c, QTableWidgetItem(f"{day}일"))
            self.tbl_box3_bottom.setItem(1, c, QTableWidgetItem(str(day*10)))

        # box4
        dummy_clients = ["ABC","XYZ","하하","Test1","Test2"]
        dummy_vals = [300,500,200,100,900]
        for c in range(5):
            self.tbl_box4.setItem(0, c, QTableWidgetItem(dummy_clients[c]))
            self.tbl_box4.setItem(1, c, QTableWidgetItem(str(dummy_vals[c])))
            
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
        global global_token
        employees = api_fetch_employees(global_token, keyword)

        if isinstance(employees, dict):  # 🚨 단일 객체가 반환된 경우
            employees = [employees]

        if not isinstance(employees, list):  # 🚨 응답이 리스트가 아닐 경우 예외 처리
            print("Error: Unexpected response format")
            self.left_widget.display_employee(None)
            return

        if employees:  # ✅ 검색 결과가 있을 경우
            self.left_widget.display_employee(employees[0])
        else:
            self.left_widget.display_employee(None)  # 검색 결과 없음 처리

        self.right_four.update_data_example()


    # def __init__(self, parent=None):
    #     super().__init__(parent)
    #     self.init_ui()

    # def init_ui(self):
    #     main_layout = QHBoxLayout()

    #     # 왼쪽 패널
    #     left_panel = QGroupBox("직원 입력")
    #     left_layout = QFormLayout()
    #     self.emp_number_edit = QLineEdit()
    #     left_layout.addRow("사원번호:", self.emp_number_edit)

    #     self.emp_password_edit = QLineEdit()
    #     self.emp_password_edit.setEchoMode(QLineEdit.Password)
    #     left_layout.addRow("Password:", self.emp_password_edit)

    #     self.emp_name_edit = QLineEdit()
    #     left_layout.addRow("이름:", self.emp_name_edit)

    #     self.emp_phone_edit = QLineEdit()
    #     left_layout.addRow("전화번호:", self.emp_phone_edit)

    #     self.emp_role_edit = QLineEdit("sales")
    #     left_layout.addRow("직책:", self.emp_role_edit)
        
    #     self.btn_create = QPushButton("Create")
    #     self.btn_create.clicked.connect(self.create_employee)
    #     self.btn_update = QPushButton("Update")
    #     self.btn_update.clicked.connect(self.update_employee)
    #     self.btn_delete = QPushButton("Delete by ID")
    #     self.btn_delete.clicked.connect(self.delete_employee)

    #     left_layout.addRow(self.btn_create, self.btn_update)
    #     left_layout.addRow(self.btn_delete)

    #     self.emp_id_delete_edit = QLineEdit()
    #     self.emp_id_delete_edit.setPlaceholderText("Employee ID to delete")
    #     left_layout.addRow("Delete ID:", self.emp_id_delete_edit)

    #     left_panel.setLayout(left_layout)

    #     # 오른쪽 패널
    #     right_panel = QGroupBox("직원 목록")
    #     right_layout = QVBoxLayout()
    #     self.emp_table = QTableWidget()
    #     self.emp_table.setColumnCount(4)
    #     self.emp_table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Role"])
    #     self.emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    #     right_layout.addWidget(self.emp_table)

    #     self.btn_refresh = QPushButton("Refresh List")
    #     self.btn_refresh.clicked.connect(self.list_employees)
    #     right_layout.addWidget(self.btn_refresh)

    #     right_panel.setLayout(right_layout)

    #     main_layout.addWidget(left_panel, 1)
    #     main_layout.addWidget(right_panel, 4)
    #     self.setLayout(main_layout)

    # def create_employee(self):
    #     global global_token
    #     if not global_token:
    #         QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
    #         return
    #     data = {
    #         "employee_number": self.emp_number_edit.text(),
    #         "password": self.emp_password_edit.text(),
    #         "name": self.emp_name_edit.text(),
    #         "phone": self.emp_phone_edit.text(),
    #         "role": self.emp_role_edit.text(),
    #     }
    #     try:
    #         resp = api_create_employee(global_token, data)
    #         if resp.status_code in (200,201):
    #             QMessageBox.information(self, "성공", "직원 생성 완료!")
    #             self.list_employees()
    #         else:
    #             QMessageBox.critical(self, "실패", f"Create failed: {resp.status_code}\n{resp.text}")
    #     except Exception as ex:
    #         QMessageBox.critical(self, "오류", str(ex))

    # def update_employee(self):
    #     global global_token
    #     if not global_token:
    #         QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
    #         return

    #     emp_number = self.emp_number_edit.text()
    #     data = {
    #         "employee_number": emp_number,
    #         "password": self.emp_password_edit.text(),
    #         "name": self.emp_name_edit.text(),
    #         "phone": self.emp_phone_edit.text(),
    #         "role": self.emp_role_edit.text(),
    #     }
    #     try:
    #         resp = api_update_employee(global_token, emp_number, data)
    #         if resp.status_code == 200:
    #             QMessageBox.information(self, "성공", "직원 수정 완료!")
    #             self.list_employees()
    #         else:
    #             QMessageBox.critical(self, "실패", f"Update failed: {resp.status_code}\n{resp.text}")
    #     except Exception as ex:
    #         QMessageBox.critical(self, "오류", str(ex))

    # def delete_employee(self):
    #     global global_token
    #     emp_id = self.emp_id_delete_edit.text().strip()
    #     if not emp_id:
    #         QMessageBox.warning(self, "경고", "삭제할 Employee ID를 입력하세요.")
    #         return
    #     try:
    #         resp = api_delete_employee(global_token, emp_id)
    #         if resp.status_code == 200:
    #             QMessageBox.information(self, "성공", "직원 삭제 완료!")
    #             self.list_employees()
    #         else:
    #             QMessageBox.critical(self, "실패", f"Delete failed: {resp.status_code}\n{resp.text}")
    #     except Exception as ex:
    #         QMessageBox.critical(self, "오류", str(ex))

    # def list_employees(self):
    #     global global_token
    #     if not global_token:
    #         QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
    #         return
    #     try:
    #         resp = api_fetch_employees(global_token)
    #         if resp and resp.status_code == 200:
    #             data = resp.json()
    #             self.emp_table.setRowCount(0)
    #             for e in data:
    #                 row = self.emp_table.rowCount()
    #                 self.emp_table.insertRow(row)
    #                 self.emp_table.setItem(row, 0, QTableWidgetItem(str(e.get("id",""))))
    #                 self.emp_table.setItem(row, 1, QTableWidgetItem(e.get("name","")))
    #                 self.emp_table.setItem(row, 2, QTableWidgetItem(e.get("phone","")))
    #                 self.emp_table.setItem(row, 3, QTableWidgetItem(e.get("role","")))
    #         else:
    #             QMessageBox.critical(self, "실패", f"List employees failed: {resp.status_code if resp else 'NoResp'}")
    #     except Exception as ex:
    #         QMessageBox.critical(self, "오류", str(ex))

class ClientsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        left_panel = QGroupBox("거래처 입력")
        left_layout = QFormLayout()
        self.client_name_edit = QLineEdit()
        left_layout.addRow("Client Name:", self.client_name_edit)
        self.client_address_edit = QLineEdit()
        left_layout.addRow("Address:", self.client_address_edit)
        self.client_phone_edit = QLineEdit()
        left_layout.addRow("Phone:", self.client_phone_edit)
        self.client_outstanding_edit = QLineEdit("0")
        left_layout.addRow("Outstanding Amount:", self.client_outstanding_edit)
        create_btn = QPushButton("Create Client")
        create_btn.clicked.connect(self.create_client)
        left_layout.addRow(create_btn)
        left_panel.setLayout(left_layout)

        right_panel = QGroupBox("거래처 목록")
        right_layout = QVBoxLayout()
        self.client_table = QTableWidget()
        self.client_table.setColumnCount(5)
        self.client_table.setHorizontalHeaderLabels(["ID", "Name", "Address", "Phone", "Outstanding"])
        self.client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.client_table)
        refresh_btn = QPushButton("Refresh Clients")
        refresh_btn.clicked.connect(self.list_clients)
        right_layout.addWidget(refresh_btn)
        right_panel.setLayout(right_layout)

        main_layout.addWidget(left_panel,1)
        main_layout.addWidget(right_panel,4)
        self.setLayout(main_layout)

    def create_client(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        data = {
            "client_name": self.client_name_edit.text(),
            "address": self.client_address_edit.text(),
            "phone": self.client_phone_edit.text(),
            "outstanding_amount": float(self.client_outstanding_edit.text() or 0)
        }
        try:
            resp = api_create_client(global_token, data)
            if resp.status_code in (200,201):
                QMessageBox.information(self, "성공", "거래처 생성 완료!")
                self.list_clients()
            else:
                QMessageBox.critical(self, "실패", f"Create client failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

    def list_clients(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        try:
            resp = api_fetch_clients(global_token)
            if resp.status_code == 200:
                data = resp.json()
                self.client_table.setRowCount(0)
                for c in data:
                    row = self.client_table.rowCount()
                    self.client_table.insertRow(row)
                    self.client_table.setItem(row, 0, QTableWidgetItem(str(c.get("id",""))))
                    self.client_table.setItem(row, 1, QTableWidgetItem(c.get("client_name","")))
                    self.client_table.setItem(row, 2, QTableWidgetItem(c.get("address","")))
                    self.client_table.setItem(row, 3, QTableWidgetItem(c.get("phone","")))
                    self.client_table.setItem(row, 4, QTableWidgetItem(str(c.get("outstanding_amount",""))))
            else:
                QMessageBox.critical(self, "실패", f"List clients failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

class ProductsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        left_panel = QGroupBox("상품 입력")
        left_layout = QFormLayout()

        self.prod_brand_id_edit = QLineEdit()
        left_layout.addRow("Brand ID:", self.prod_brand_id_edit)
        self.prod_name_edit = QLineEdit()
        left_layout.addRow("Product Name:", self.prod_name_edit)
        self.prod_barcode_edit = QLineEdit()
        left_layout.addRow("Barcode:", self.prod_barcode_edit)
        self.prod_price_edit = QLineEdit("0")
        left_layout.addRow("Default Price:", self.prod_price_edit)
        self.prod_stock_edit = QLineEdit("0")
        left_layout.addRow("Stock:", self.prod_stock_edit)
        self.prod_active_edit = QLineEdit("1")
        left_layout.addRow("Is Active (1/0):", self.prod_active_edit)

        create_btn = QPushButton("Create Product")
        create_btn.clicked.connect(self.create_product)
        left_layout.addRow(create_btn)
        left_panel.setLayout(left_layout)

        right_panel = QGroupBox("상품 목록")
        right_layout = QVBoxLayout()
        self.prod_table = QTableWidget()
        self.prod_table.setColumnCount(6)
        self.prod_table.setHorizontalHeaderLabels(["ID","BrandID","Name","Barcode","Price","Stock"])
        self.prod_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.prod_table)

        btn_refresh = QPushButton("Refresh Products")
        btn_refresh.clicked.connect(self.list_products)
        right_layout.addWidget(btn_refresh)
        right_panel.setLayout(right_layout)

        main_layout.addWidget(left_panel,1)
        main_layout.addWidget(right_panel,4)
        self.setLayout(main_layout)

    def create_product(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        data = {
            "brand_id": int(self.prod_brand_id_edit.text() or 0),
            "product_name": self.prod_name_edit.text(),
            "barcode": self.prod_barcode_edit.text(),
            "default_price": float(self.prod_price_edit.text() or 0),
            "stock": int(self.prod_stock_edit.text() or 0),
            "is_active": bool(int(self.prod_active_edit.text() or 1))
        }
        try:
            resp = api_create_product(global_token, data)
            if resp.status_code in (200,201):
                QMessageBox.information(self, "성공", "상품 생성 완료!")
                self.list_products()
            else:
                QMessageBox.critical(self, "실패", f"Create product failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

    def list_products(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        try:
            resp = api_fetch_products(global_token)
            if resp.status_code == 200:
                data = resp.json()
                self.prod_table.setRowCount(0)
                for p in data:
                    row = self.prod_table.rowCount()
                    self.prod_table.insertRow(row)
                    self.prod_table.setItem(row, 0, QTableWidgetItem(str(p.get("id",""))))
                    self.prod_table.setItem(row, 1, QTableWidgetItem(str(p.get("brand_id",""))))
                    self.prod_table.setItem(row, 2, QTableWidgetItem(p.get("product_name","")))
                    self.prod_table.setItem(row, 3, QTableWidgetItem(p.get("barcode","")))
                    self.prod_table.setItem(row, 4, QTableWidgetItem(str(p.get("default_price",""))))
                    self.prod_table.setItem(row, 5, QTableWidgetItem(str(p.get("stock",""))))
            else:
                QMessageBox.critical(self, "실패", f"List products failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

class OrdersTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        left_panel = QGroupBox("주문 입력")
        left_layout = QFormLayout()

        self.order_client_id_edit = QLineEdit()
        left_layout.addRow("Client ID:", self.order_client_id_edit)

        self.order_employee_id_edit = QLineEdit()
        left_layout.addRow("Employee ID:", self.order_employee_id_edit)

        self.order_status_edit = QLineEdit("pending")
        left_layout.addRow("Status:", self.order_status_edit)

        self.create_order_btn = QPushButton("Create Order")
        self.create_order_btn.clicked.connect(self.create_order)
        left_layout.addRow(self.create_order_btn)

        left_panel.setLayout(left_layout)

        right_panel = QGroupBox("주문 목록")
        right_layout = QVBoxLayout()
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels(["ID","ClientID","EmployeeID","Total","Status"])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.orders_table)

        self.btn_refresh_orders = QPushButton("Refresh Orders")
        self.btn_refresh_orders.clicked.connect(self.load_orders)
        right_layout.addWidget(self.btn_refresh_orders)

        right_panel.setLayout(right_layout)

        main_layout.addWidget(left_panel,1)
        main_layout.addWidget(right_panel,4)
        self.setLayout(main_layout)

    def create_order(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        data = {
            "client_id": int(self.order_client_id_edit.text() or 0),
            "employee_id": int(self.order_employee_id_edit.text() or 0),
            "status": self.order_status_edit.text(),
            "items": []
        }
        try:
            resp = api_create_order(global_token, data)
            if resp.status_code in (200,201):
                QMessageBox.information(self, "성공", "주문 생성 완료!")
                self.load_orders()
            else:
                QMessageBox.critical(self, "실패", f"Create Order failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

    def load_orders(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        try:
            resp = api_fetch_orders(global_token)
            if resp.status_code == 200:
                data = resp.json()
                self.orders_table.setRowCount(0)
                for o in data:
                    row = self.orders_table.rowCount()
                    self.orders_table.insertRow(row)
                    self.orders_table.setItem(row, 0, QTableWidgetItem(str(o.get("id",""))))
                    self.orders_table.setItem(row, 1, QTableWidgetItem(str(o.get("client_id",""))))
                    self.orders_table.setItem(row, 2, QTableWidgetItem(str(o.get("employee_id",""))))
                    self.orders_table.setItem(row, 3, QTableWidgetItem(str(o.get("total_amount",""))))
                    self.orders_table.setItem(row, 4, QTableWidgetItem(o.get("status","")))
            else:
                QMessageBox.critical(self, "실패", f"List orders failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

class SalesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        left_panel = QGroupBox("매출 조회(예시)")
        left_layout = QFormLayout()

        self.btn_fetch_sales = QPushButton("Fetch Sales (Example)")
        self.btn_fetch_sales.clicked.connect(self.fetch_sales_example)
        left_layout.addRow(self.btn_fetch_sales)

        left_panel.setLayout(left_layout)

        right_panel = QGroupBox("매출 목록")
        right_layout = QVBoxLayout()

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(5)
        self.sales_table.setHorizontalHeaderLabels(["ID","ClientID","ProductID","Quantity","SaleDate"])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.sales_table)

        self.btn_create_sales = QPushButton("Create Sales Example")
        self.btn_create_sales.clicked.connect(self.create_sales_example)
        right_layout.addWidget(self.btn_create_sales)

        self.btn_delete_sales = QPushButton("Delete Sales by ID")
        self.btn_delete_sales.clicked.connect(self.delete_sales_example)
        right_layout.addWidget(self.btn_delete_sales)

        self.sales_id_edit = QLineEdit()
        self.sales_id_edit.setPlaceholderText("Sales ID to delete")
        right_layout.addWidget(self.sales_id_edit)

        right_panel.setLayout(right_layout)

        main_layout.addWidget(left_panel,1)
        main_layout.addWidget(right_panel,4)
        self.setLayout(main_layout)

    def fetch_sales_example(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        try:
            resp = api_fetch_sales(global_token)
            if resp.status_code == 200:
                data = resp.json()
                self.sales_table.setRowCount(0)
                for s in data:
                    row = self.sales_table.rowCount()
                    self.sales_table.insertRow(row)
                    self.sales_table.setItem(row, 0, QTableWidgetItem(str(s.get("id",""))))
                    self.sales_table.setItem(row, 1, QTableWidgetItem(str(s.get("client_id",""))))
                    self.sales_table.setItem(row, 2, QTableWidgetItem(str(s.get("product_id",""))))
                    self.sales_table.setItem(row, 3, QTableWidgetItem(str(s.get("quantity",""))))
                    self.sales_table.setItem(row, 4, QTableWidgetItem(str(s.get("sale_date",""))))
            else:
                QMessageBox.critical(self, "실패", f"Fetch sales failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

    def create_sales_example(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        data = {
            "client_id": 2,
            "product_id": 1,
            "quantity": 5,
            "sale_date": "2025-03-01"
        }
        try:
            resp = api_create_sales(global_token, data)
            if resp.status_code in (200,201):
                QMessageBox.information(self, "성공", "매출 생성 완료!")
                self.fetch_sales_example()
            else:
                QMessageBox.critical(self, "실패", f"Create sales failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

    def delete_sales_example(self):
        global global_token
        sid = self.sales_id_edit.text().strip()
        if not sid:
            QMessageBox.warning(self, "경고", "Sales ID를 입력하세요.")
            return
        try:
            resp = api_delete_sales(global_token, sid)
            if resp.status_code == 200:
                QMessageBox.information(self, "성공", "매출 삭제 완료!")
                self.fetch_sales_example()
            else:
                QMessageBox.critical(self, "실패", f"Delete sales failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

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
                "id": int(self.emp_id_edit.text() or 0),
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
            resp = api_fetch_brand_products(global_token, int(brand_id))
            if resp.status_code == 200:
                data = resp.json()
                self.table.setRowCount(0)
                for prod in data:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(str(prod.get("id",""))))
                    self.table.setItem(row, 1, QTableWidgetItem(prod.get("product_name","")))
                    self.table.setItem(row, 2, QTableWidgetItem(prod.get("barcode","")))
            else:
                QMessageBox.critical(self, "실패", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

# ----------------------------
# Main Window
# ----------------------------
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Merged UI")
        self.setGeometry(100,100,1600,900)
        self.setStyleSheet(load_dark_theme())

        self.init_ui()

    def init_ui(self):
        ## 1) 상단 아이콘 툴바
        self.toolbar = QToolBar("메인 메뉴")
        self.toolbar.setIconSize(QSize(32,32))
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

        self.search_button.clicked.connect(self.on_search_clicked)

        ## 3) 메인 스택
        self.stacked = QStackedWidget()
        self.setCentralWidget(self.stacked)

        # 탭들
        self.employee_tab = EmployeesTab()      # idx=0
        self.clients_tab = ClientsTab()         # idx=1
        self.products_tab = ProductsTab()       # idx=2
        self.orders_tab = OrdersTab()           # idx=3
        self.sales_tab = SalesTab()             # idx=4
        self.total_sales_tab = TotalSalesTab()  # idx=5
        self.vehicle_tab = EmployeeVehicleTab() # idx=6
        self.empclient_tab = EmployeeClientTab()# idx=7
        self.brand_tab = BrandProductTab()      # idx=8

        self.stacked.addWidget(self.employee_tab)
        self.stacked.addWidget(self.clients_tab)
        self.stacked.addWidget(self.products_tab)
        self.stacked.addWidget(self.orders_tab)
        self.stacked.addWidget(self.sales_tab)
        self.stacked.addWidget(self.total_sales_tab)
        self.stacked.addWidget(self.vehicle_tab)
        self.stacked.addWidget(self.empclient_tab)
        self.stacked.addWidget(self.brand_tab)

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
            self.sales_tab.do_search(keyword)
        elif idx == 5:
            self.total_sales_tab.do_search(keyword)
        elif idx == 6:
            self.vehicle_tab.do_search(keyword)
        elif idx == 7:
            self.empclient_tab.do_search(keyword)
        elif idx == 8:
            self.brand_tab.do_search(keyword)

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

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

# =============== 직원(Employees) ===============
def api_fetch_employees(token):
    """
    GET /employees
    """
    url = f"{BASE_URL}/employees"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_create_employee(token, data):
    """
    POST /employees
    """
    url = f"{BASE_URL}/employees"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_update_employee(token, emp_id, data):
    """
    PUT /employees/{emp_id}
    """
    url = f"{BASE_URL}/employees/{emp_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.put(url, json=data, headers=headers)

def api_delete_employee(token, emp_id):
    """
    DELETE /employees/{emp_id}
    """
    url = f"{BASE_URL}/employees/{emp_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

def api_import_employees_from_excel(token, filepath):
    """
    엑셀 파일에서 직원 정보 일괄 등록
    (예시로 API POST /employees 반복 호출)
    """
    headers = {"Authorization": f"Bearer {token}"}
    wb = openpyxl.load_workbook(filepath)
    sheet = wb.active
    for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
        if row_idx == 1:
            continue  # 헤더
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

# =============== 거래처(Clients) ===============
def api_fetch_clients(token):
    """
    GET /clients
    """
    url = f"{BASE_URL}/clients"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_create_client(token, data):
    """
    POST /clients
    """
    url = f"{BASE_URL}/clients"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_delete_client(token, client_id):
    """
    DELETE /clients/{client_id}
    """
    url = f"{BASE_URL}/clients/{client_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

# =============== 제품(Products) + 브랜드(Brands) ===============
def api_fetch_products(token):
    """
    GET /products
    """
    url = f"{BASE_URL}/products"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_create_product(token, data):
    """
    POST /products
    """
    url = f"{BASE_URL}/products"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_update_product(token, prod_id, data):
    """
    PUT /products/{prod_id}
    """
    url = f"{BASE_URL}/products/{prod_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.put(url, json=data, headers=headers)

def api_delete_product(token, prod_id):
    """
    DELETE /products/{prod_id}
    """
    url = f"{BASE_URL}/products/{prod_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

def api_fetch_brand_products(token, brand_id):
    """
    GET /brands/{brand_id}/products
    """
    url = f"{BASE_URL}/brands/{brand_id}/products"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

# =============== 주문(Orders) ===============
def api_fetch_orders(token):
    """
    GET /orders
    """
    url = f"{BASE_URL}/orders"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_create_order(token, data):
    """
    POST /orders
    """
    url = f"{BASE_URL}/orders"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_update_order(token, order_id, data):
    """
    PUT /orders/{order_id}
    """
    url = f"{BASE_URL}/orders/{order_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.put(url, json=data, headers=headers)

def api_delete_order(token, order_id):
    """
    DELETE /orders/{order_id}
    """
    url = f"{BASE_URL}/orders/{order_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

# =============== 매출(Sales) ===============
# 아래 엔드포인트들은 예시: 실제 /sales/{id} 등에 맞춰 수정
def api_fetch_sales(token):
    """
    GET /sales
    """
    url = f"{BASE_URL}/sales"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_create_sales(token, data):
    """
    POST /sales
    """
    url = f"{BASE_URL}/sales"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_delete_sales(token, sales_id):
    """
    DELETE /sales/{sales_id}
    """
    url = f"{BASE_URL}/sales/{sales_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

# 예시: /sales/total/{date}, /sales/by_employee/{emp_id}/{date} 등은 별도 정의 필요

# =============== 직원-거래처(EMP-CLIENT) ===============
def api_assign_employee_client(token, employee_id, client_id):
    """
    POST /employee_clients
    """
    url = f"{BASE_URL}/employee_clients"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"employee_id": employee_id, "client_id": client_id}
    return requests.post(url, json=data, headers=headers)

def api_fetch_employee_clients_all(token):
    """
    GET /employee_clients
    """
    url = f"{BASE_URL}/employee_clients"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

# =============== 직원 차량(EmployeeVehicle) ===============
def api_fetch_vehicle(token):
    """
    GET /employee_vehicles
    """
    url = f"{BASE_URL}/employee_vehicles"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_create_vehicle(token, data):
    """
    POST /employee_vehicles
    """
    url = f"{BASE_URL}/employee_vehicles"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_update_vehicle(token, vehicle_id, data):
    """
    PUT /employee_vehicles/{vehicle_id}
    """
    url = f"{BASE_URL}/employee_vehicles/{vehicle_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return requests.put(url, json=data, headers=headers)

def api_delete_vehicle(token, vehicle_id):
    """
    DELETE /employee_vehicles/{vehicle_id}
    """
    url = f"{BASE_URL}/employee_vehicles/{vehicle_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(url, headers=headers)

# =============== 추가 예시 (상품 바코드 등) ===============
def api_fetchProductByBarcode(token, barcode):
    """
    GET /products/barcode/{barcode}
    """
    url = f"{BASE_URL}/products/barcode/{barcode}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_fetchClientPrice(token, clientId, productId):
    """
    예시: GET /client_product_prices?client_id=...&product_id=...
    (서버에 따라 구현)
    """
    url = f"{BASE_URL}/client_product_prices?client_id={clientId}&product_id={productId}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

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

        # 간단 예시: 오직 ID=1만 허용
        if employee_id != 1:
            QMessageBox.critical(self, "접근 거부", "Only ID=1 is allowed in this test!")
            return
        try:
            response = api_login(employee_id, password)
            if response.status_code == 200:
                data = response.json()
                token = data.get("token")
                if not token:
                    QMessageBox.critical(self, "오류", "로그인 응답에 token이 없습니다.")
                    return
                global_token = token
                QMessageBox.information(self, "성공", "로그인 성공!")
                self.accept()
            else:
                QMessageBox.critical(self, "로그인 실패", f"로그인 실패: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"로그인 중 오류: {e}")

# ----------------------------
# 탭 구현 (직원, 거래처, 제품, 주문, 매출, 총매출, 차량, EMP-CLIENT, 브랜드-제품)
# ----------------------------
# 아래부터는 기존 UI 구조(왼쪽/오른쪽) 혹은 단순 목록형태를 비슷하게 유지


# 1) EmployeesTab
class EmployeesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        # 왼쪽 패널(직원 입력)
        left_panel = QGroupBox("직원 입력")
        left_layout = QFormLayout()
        self.emp_number_edit = QLineEdit()
        left_layout.addRow("사원번호:", self.emp_number_edit)

        self.emp_password_edit = QLineEdit()
        self.emp_password_edit.setEchoMode(QLineEdit.Password)
        left_layout.addRow("Password:", self.emp_password_edit)

        self.emp_name_edit = QLineEdit()
        left_layout.addRow("이름:", self.emp_name_edit)

        self.emp_phone_edit = QLineEdit()
        left_layout.addRow("전화번호:", self.emp_phone_edit)

        self.emp_role_edit = QLineEdit("sales")
        left_layout.addRow("직책:", self.emp_role_edit)

        self.btn_create = QPushButton("Create")
        self.btn_create.clicked.connect(self.create_employee)
        self.btn_update = QPushButton("Update")
        self.btn_update.clicked.connect(self.update_employee)
        self.btn_delete = QPushButton("Delete by ID")
        self.btn_delete.clicked.connect(self.delete_employee)

        left_layout.addRow(self.btn_create, self.btn_update)
        left_layout.addRow(self.btn_delete)

        self.emp_id_delete_edit = QLineEdit()
        self.emp_id_delete_edit.setPlaceholderText("Employee ID to delete")
        left_layout.addRow("Delete ID:", self.emp_id_delete_edit)

        left_panel.setLayout(left_layout)

        # 오른쪽 패널(직원 목록)
        right_panel = QGroupBox("직원 목록")
        right_layout = QVBoxLayout()
        self.emp_table = QTableWidget()
        self.emp_table.setColumnCount(4)
        self.emp_table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Role"])
        self.emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.emp_table)

        self.btn_refresh = QPushButton("Refresh List")
        self.btn_refresh.clicked.connect(self.list_employees)
        right_layout.addWidget(self.btn_refresh)

        right_panel.setLayout(right_layout)

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 4)
        self.setLayout(main_layout)

    def create_employee(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        data = {
            "employee_number": self.emp_number_edit.text(),
            "password": self.emp_password_edit.text(),
            "name": self.emp_name_edit.text(),
            "phone": self.emp_phone_edit.text(),
            "role": self.emp_role_edit.text(),
        }
        try:
            resp = api_create_employee(global_token, data)
            if resp.status_code in (200,201):
                QMessageBox.information(self, "성공", "직원 생성 완료!")
                self.list_employees()
            else:
                QMessageBox.critical(self, "실패", f"Create failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

    def update_employee(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return

        emp_number = self.emp_number_edit.text()
        data = {
            "employee_number": emp_number,
            "password": self.emp_password_edit.text(),
            "name": self.emp_name_edit.text(),
            "phone": self.emp_phone_edit.text(),
            "role": self.emp_role_edit.text(),
        }
        try:
            resp = api_update_employee(global_token, emp_number, data)
            if resp.status_code == 200:
                QMessageBox.information(self, "성공", "직원 수정 완료!")
                self.list_employees()
            else:
                QMessageBox.critical(self, "실패", f"Update failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

    def delete_employee(self):
        global global_token
        emp_id = self.emp_id_delete_edit.text().strip()
        if not emp_id:
            QMessageBox.warning(self, "경고", "삭제할 Employee ID를 입력하세요.")
            return
        try:
            resp = api_delete_employee(global_token, emp_id)
            if resp.status_code == 200:
                QMessageBox.information(self, "성공", "직원 삭제 완료!")
                self.list_employees()
            else:
                QMessageBox.critical(self, "실패", f"Delete failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

    def list_employees(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        try:
            resp = api_fetch_employees(global_token)
            if resp.status_code == 200:
                data = resp.json()
                self.emp_table.setRowCount(0)
                for e in data:
                    row = self.emp_table.rowCount()
                    self.emp_table.insertRow(row)
                    self.emp_table.setItem(row, 0, QTableWidgetItem(str(e.get("id",""))))
                    self.emp_table.setItem(row, 1, QTableWidgetItem(e.get("name","")))
                    self.emp_table.setItem(row, 2, QTableWidgetItem(e.get("phone","")))
                    self.emp_table.setItem(row, 3, QTableWidgetItem(e.get("role","")))
            else:
                QMessageBox.critical(self, "실패", f"List employees failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))


# 2) ClientsTab
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


# 3) ProductsTab
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

        refresh_btn = QPushButton("Refresh Products")
        refresh_btn.clicked.connect(self.list_products)
        right_layout.addWidget(refresh_btn)
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


# 4) OrdersTab
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
            "items": []  # 아이템은 예시
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


# 5) SalesTab
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
        """
        GET /sales
        """
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
        """
        POST /sales
        """
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
                QMessageBox.information(self, "성공", "매출 생성!")
                self.fetch_sales_example()
            else:
                QMessageBox.critical(self, "실패", f"Create sales failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

    def delete_sales_example(self):
        """
        DELETE /sales/{id}
        """
        global global_token
        sid = self.sales_id_edit.text().strip()
        if not sid:
            QMessageBox.warning(self, "경고", "Sales ID를 입력하세요.")
            return
        try:
            resp = api_delete_sales(global_token, sid)
            if resp.status_code == 200:
                QMessageBox.information(self, "성공", "매출 삭제!")
                self.fetch_sales_example()
            else:
                QMessageBox.critical(self, "실패", f"Delete sales failed: {resp.status_code}\n{resp.text}")
        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))


# 6) TotalSalesTab
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
        """
        예시: /sales/total/{date} (서버에서 구현해야 함)
        """
        global global_token
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        try:
            # GET /sales/total/{date_str}
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


# 7) EmployeeVehicleTab (이미 작성된 예시)
class EmployeeVehicleTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # 조회 부분
        search_group = QGroupBox("직원 차량 관리 조회")
        search_layout = QFormLayout()
        self.emp_id_search_edit = QLineEdit()
        search_layout.addRow("Employee ID:", self.emp_id_search_edit)
        self.search_btn = QPushButton("조회")
        self.search_btn.clicked.connect(self.fetch_vehicle)
        search_layout.addRow(self.search_btn)
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)

        # 정보 입력
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
        main_layout.addWidget(info_group)

        # 버튼
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
        main_layout.addLayout(btn_layout)

        # 테이블
        self.vehicle_table = QTableWidget()
        self.vehicle_table.setColumnCount(5)
        self.vehicle_table.setHorizontalHeaderLabels(["ID","Employee ID","주유비","주행거리","오일교체일"])
        self.vehicle_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.vehicle_table)

        self.setLayout(main_layout)

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
            # emp_id 필터
            filtered = [v for v in vehicles if v.get("id") == int(emp_id)]
            self.vehicle_table.setRowCount(0)
            for v in filtered:
                row = self.vehicle_table.rowCount()
                self.vehicle_table.insertRow(row)
                self.vehicle_table.setItem(row, 0, QTableWidgetItem(str(v.get("id",""))))
                self.vehicle_table.setItem(row, 1, QTableWidgetItem(str(v.get("id",""))))  # 같은 값
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


# 8) EMP-CLIENT Tab
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


# 9) BrandProductTab
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
# MainApp (QMainWindow)
# ----------------------------
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("업무 관리 시스템")
        self.setGeometry(0,0,1650,1000)
        self.setStyleSheet(self.load_dark_theme())

        self.init_ui()

    def init_ui(self):
        # 툴바
        self.toolbar = QToolBar("메인 메뉴")
        self.addToolBar(self.toolbar)
        self.toolbar.setIconSize(QSize(100,100))

        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 아이콘 경로 (임의)
        employee_path = os.path.join(current_dir,"icons","employee.png")
        client_path = os.path.join(current_dir,"icons","correspondent.png")
        product_path = os.path.join(current_dir,"icons","product.png")
        orders_path = os.path.join(current_dir,"icons","orders.png")
        sales_path = os.path.join(current_dir,"icons","sales.png")
        totalsales_path = os.path.join(current_dir,"icons","totalsales.png")
        vehicle_path = os.path.join(current_dir,"icons","vehicle.png")
        empclient_path = os.path.join(current_dir,"icons","empclient.png")
        brand_path = os.path.join(current_dir,"icons","brand.png")

        # 액션
        self.add_toolbar_action("직원 관리", employee_path, self.show_employee_tab)
        self.add_toolbar_action("거래처 관리", client_path, self.show_clients_tab)
        self.add_toolbar_action("상품 관리", product_path, self.show_products_tab)
        self.add_toolbar_action("주문 관리", orders_path, self.show_orders_tab)
        self.add_toolbar_action("매출 관리", sales_path, self.show_sales_tab)
        self.add_toolbar_action("총매출", totalsales_path, self.show_total_sales_tab)
        self.add_toolbar_action("차량 관리", vehicle_path, self.show_vehicle_tab)
        self.add_toolbar_action("EMP-CLIENT", empclient_path, self.show_emp_client_tab)
        self.add_toolbar_action("Brand-Product", brand_path, self.show_brand_product_tab)

        # 스택
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 탭 생성
        self.employee_tab = EmployeesTab()
        self.clients_tab = ClientsTab()
        self.products_tab = ProductsTab()
        self.orders_tab = OrdersTab()
        self.sales_tab = SalesTab()
        self.total_sales_tab = TotalSalesTab()
        self.vehicle_tab = EmployeeVehicleTab()
        self.emp_client_tab = EmployeeClientTab()
        self.brand_product_tab = BrandProductTab()

        # 스택에 등록
        self.stacked_widget.addWidget(self.employee_tab)
        self.stacked_widget.addWidget(self.clients_tab)
        self.stacked_widget.addWidget(self.products_tab)
        self.stacked_widget.addWidget(self.orders_tab)
        self.stacked_widget.addWidget(self.sales_tab)
        self.stacked_widget.addWidget(self.total_sales_tab)
        self.stacked_widget.addWidget(self.vehicle_tab)
        self.stacked_widget.addWidget(self.emp_client_tab)
        self.stacked_widget.addWidget(self.brand_product_tab)

        self.stacked_widget.setCurrentWidget(self.employee_tab)

    def add_toolbar_action(self, name, icon_path, callback):
        action = QAction(QIcon(icon_path), name, self)
        action.triggered.connect(callback)
        self.toolbar.addAction(action)

    def show_employee_tab(self):
        self.stacked_widget.setCurrentWidget(self.employee_tab)

    def show_clients_tab(self):
        self.stacked_widget.setCurrentWidget(self.clients_tab)

    def show_products_tab(self):
        self.stacked_widget.setCurrentWidget(self.products_tab)

    def show_orders_tab(self):
        self.stacked_widget.setCurrentWidget(self.orders_tab)

    def show_sales_tab(self):
        self.stacked_widget.setCurrentWidget(self.sales_tab)

    def show_total_sales_tab(self):
        self.stacked_widget.setCurrentWidget(self.total_sales_tab)

    def show_vehicle_tab(self):
        self.stacked_widget.setCurrentWidget(self.vehicle_tab)

    def show_emp_client_tab(self):
        self.stacked_widget.setCurrentWidget(self.emp_client_tab)

    def show_brand_product_tab(self):
        self.stacked_widget.setCurrentWidget(self.brand_product_tab)

    def load_dark_theme(self):
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
# Main
# ----------------------------
def main():
    app = QApplication(sys.argv)

    # 로그인
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.Accepted:
        # 로그인 성공 후 메인 윈도우
        main_window = MainApp()
        main_window.show()
        sys.exit(app.exec_())
    else:
        sys.exit()

if __name__ == "__main__":
    main()

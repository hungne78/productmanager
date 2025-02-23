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
BASE_URL = "http://127.0.0.1:8000"
global_token = None

# ----------------------------
# API Service Functions
# ----------------------------
def api_login(employee_id, password):
    url = f"{BASE_URL}/login"
    data = {"id": employee_id, "password": password}
    headers = {"Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_fetch_employees(token):
    url = f"{BASE_URL}/employees"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

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

def api_assign_employee_client(token, employee_id, client_id):
    url = f"{BASE_URL}/employee_clients"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"employee_id": employee_id, "client_id": client_id}
    return requests.post(url, json=data, headers=headers)

def api_fetch_employee_clients(token, employee_id):
    url = f"{BASE_URL}/employees/{employee_id}/clients"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_fetch_brand_products(token, brand_id):
    url = f"{BASE_URL}/brands/{brand_id}/products"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

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

def api_fetchProductByBarcode(token, barcode):
    url = f"{BASE_URL}/products/barcode/{barcode}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

def api_fetchClientPrice(token, clientId, productId):
    url = f"{BASE_URL}/client_product_prices?client_id={clientId}&product_id={productId}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)


# 이 예제에서는 별도의 QDialog로 구현하여, 스캔 결과(바코드 문자열)를 반환합니다.
class CustomFormRow(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout()
        self.label = QLabel(label_text)
        self.input = QLineEdit()
        self.layout.addWidget(self.label, 0, 0)
        self.layout.addWidget(self.input, 0, 1)
        # 첫 번째 열(라벨)은 1, 두 번째 열(입력 필드)는 3의 비율
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 3)
        self.setLayout(self.layout)

# ----------------------------
# Login Dialog
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
        btn_layout.addWidget(self.login_btn)
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def attempt_login(self):
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
        # 테스트용: Only allow ID 1
        if employee_id != 1:
            QMessageBox.critical(self, "접근 거부", "Only ID=1 is allowed!")
            return
        try:
            response = api_login(employee_id, password)
            if response.status_code == 200:
                data = response.json()
                if "token" not in data:
                    QMessageBox.critical(self, "오류", "로그인 응답에 token이 없습니다.")
                    return
                global global_token
                global_token = data["token"]
                QMessageBox.information(self, "성공", "로그인 성공!")
                self.accept()
            else:
                QMessageBox.critical(self, "로그인 실패", f"로그인 실패: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"로그인 중 오류 발생: {e}")

class EmployeeVehicleTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # 조회 부분: 직원 ID 입력 후 조회 버튼
        search_group = QGroupBox("직원 차량 관리 조회")
        search_layout = QFormLayout()
        self.emp_id_search_edit = QLineEdit()
        search_layout.addRow("Employee ID:", self.emp_id_search_edit)
        self.search_btn = QPushButton("조회")
        self.search_btn.clicked.connect(self.fetch_vehicle)
        search_layout.addRow(self.search_btn)
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)
        
        # 정보 입력 및 수정 부분
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
        
        # 버튼: 생성, 수정, 삭제
        btn_layout = QHBoxLayout()
        self.create_vehicle_btn = QPushButton("생성")
        self.create_vehicle_btn.clicked.connect(self.create_vehicle)
        btn_layout.addWidget(self.create_vehicle_btn)
        self.update_vehicle_btn = QPushButton("수정")
        self.update_vehicle_btn.clicked.connect(self.update_vehicle)
        btn_layout.addWidget(self.update_vehicle_btn)
        self.delete_vehicle_btn = QPushButton("삭제")
        self.delete_vehicle_btn.clicked.connect(self.delete_vehicle)
        btn_layout.addWidget(self.delete_vehicle_btn)
        main_layout.addLayout(btn_layout)
        
        # 조회 결과 테이블
        self.vehicle_table = QTableWidget()
        self.vehicle_table.setColumnCount(5)
        self.vehicle_table.setHorizontalHeaderLabels(["ID", "Employee ID", "1달 주유비", "주행거리", "엔진오일 교체일"])
        self.vehicle_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.vehicle_table)
        
        self.setLayout(main_layout)

    def create_vehicle(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        try:
            data = {
                "employee_id": int(self.emp_id_edit.text()),
                "monthly_fuel_cost": float(self.monthly_fuel_edit.text() or 0),
                "current_mileage": int(self.current_mileage_edit.text() or 0),
                "last_engine_oil_change": self.oil_change_date_edit.date().toString("yyyy-MM-dd")
            }
            response = requests.post(f"{BASE_URL}/employee_vehicles", json=data,
                                     headers={"Authorization": f"Bearer {global_token}", "Content-Type": "application/json"})
            response.raise_for_status()
            QMessageBox.information(self, "성공", "차량 관리 정보 생성 완료!")
            self.fetch_vehicle()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"차량 관리 정보 생성 오류: {e}")

    def fetch_vehicle(self):
        global global_token
        emp_id = self.emp_id_search_edit.text().strip()
        if not emp_id:
            QMessageBox.warning(self, "경고", "조회할 직원 ID를 입력하세요.")
            return
        try:
            response = requests.get(f"{BASE_URL}/employee_vehicles", headers={"Authorization": f"Bearer {global_token}"})
            response.raise_for_status()
            vehicles = response.json()
            filtered = [v for v in vehicles if v.get("employee_id") == int(emp_id)]
            self.vehicle_table.setRowCount(0)
            for v in filtered:
                row = self.vehicle_table.rowCount()
                self.vehicle_table.insertRow(row)
                self.vehicle_table.setItem(row, 0, QTableWidgetItem(str(v.get("id"))))
                self.vehicle_table.setItem(row, 1, QTableWidgetItem(str(v.get("employee_id"))))
                self.vehicle_table.setItem(row, 2, QTableWidgetItem(str(v.get("monthly_fuel_cost"))))
                self.vehicle_table.setItem(row, 3, QTableWidgetItem(str(v.get("current_mileage"))))
                self.vehicle_table.setItem(row, 4, QTableWidgetItem(v.get("last_engine_oil_change") or ""))
        except Exception as e:
            QMessageBox.critical(self, "오류", f"차량 관리 정보 조회 오류: {e}")

    def update_vehicle(self):
        global global_token
        vehicle_id, ok = QInputDialog.getInt(self, "차량 정보 수정", "수정할 차량 관리 정보 ID:")
        if not ok:
            return
        try:
            data = {
                "employee_id": int(self.emp_id_edit.text()),
                "monthly_fuel_cost": float(self.monthly_fuel_edit.text() or 0),
                "current_mileage": int(self.current_mileage_edit.text() or 0),
                "last_engine_oil_change": self.oil_change_date_edit.date().toString("yyyy-MM-dd")
            }
            response = requests.put(f"{BASE_URL}/employee_vehicles/{vehicle_id}", json=data,
                                    headers={"Authorization": f"Bearer {global_token}", "Content-Type": "application/json"})
            response.raise_for_status()
            QMessageBox.information(self, "성공", "차량 관리 정보 수정 완료!")
            self.fetch_vehicle()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"차량 관리 정보 수정 오류: {e}")

    def delete_vehicle(self):
        global global_token
        vehicle_id, ok = QInputDialog.getInt(self, "차량 정보 삭제", "삭제할 차량 관리 정보 ID:")
        if not ok:
            return
        try:
            response = requests.delete(f"{BASE_URL}/employee_vehicles/{vehicle_id}",
                                       headers={"Authorization": f"Bearer {global_token}"})
            response.raise_for_status()
            QMessageBox.information(self, "성공", "차량 관리 정보 삭제 완료!")
            self.fetch_vehicle()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"차량 관리 정보 삭제 오류: {e}")

# ----------------------------
# 각 탭: 좌측 입력 / 우측 테이블 레이아웃 구현
# ----------------------------

# Employees Tab
class EmployeesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        main_layout = QHBoxLayout()
        # 왼쪽: 입력 폼
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
        self.emp_role_edit = QLineEdit()
        self.emp_role_edit.setText("sales")
        left_layout.addRow("직책:", self.emp_role_edit)
        self.create_btn = QPushButton("Create")
        self.create_btn.clicked.connect(self.create_employee)
        self.update_btn = QPushButton("Update")
        self.update_btn.clicked.connect(self.update_employee)
        self.delete_btn = QPushButton("Delete by ID")
        self.delete_btn.clicked.connect(self.delete_employee)
        left_layout.addRow(self.create_btn, self.update_btn)
        left_layout.addRow(self.delete_btn)
        self.emp_id_delete_edit = QLineEdit()
        self.emp_id_delete_edit.setPlaceholderText("Employee ID to delete")
        left_layout.addRow("Delete ID:", self.emp_id_delete_edit)
        left_panel.setLayout(left_layout)
        # 오른쪽: 데이터 테이블
        right_panel = QGroupBox("직원 목록")
        right_layout = QVBoxLayout()
        self.emp_table = QTableWidget()
        self.emp_table.setColumnCount(4)
        self.emp_table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Role"])
        self.emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.emp_table)
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.list_employees)
        right_layout.addWidget(refresh_btn)
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
            response = api_create_employee(global_token, data)
            if response.status_code in (200, 201):
                QMessageBox.information(self, "성공", "Employee created!")
                self.list_employees()
            else:
                QMessageBox.critical(self, "실패", f"Create failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Create employee error: {e}")
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
            response = api_update_employee(global_token, emp_number, data)
            if response.status_code == 200:
                QMessageBox.information(self, "성공", "Employee updated!")
                self.list_employees()
            else:
                QMessageBox.critical(self, "실패", f"Update failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Update employee error: {e}")
    def delete_employee(self):
        global global_token
        emp_id = self.emp_id_delete_edit.text().strip()
        if not emp_id:
            QMessageBox.warning(self, "경고", "삭제할 Employee ID를 입력하세요.")
            return
        try:
            response = api_delete_employee(global_token, emp_id)
            if response.status_code == 200:
                QMessageBox.information(self, "성공", "Employee deleted!")
                self.list_employees()
            else:
                QMessageBox.critical(self, "실패", f"Delete failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Delete employee error: {e}")
    def list_employees(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        try:
            response = api_fetch_employees(global_token)
            if response.status_code == 200:
                employees = response.json()
                self.emp_table.setRowCount(0)
                for emp in employees:
                    row = self.emp_table.rowCount()
                    self.emp_table.insertRow(row)
                    self.emp_table.setItem(row, 0, QTableWidgetItem(str(emp.get("id"))))
                    
                    self.emp_table.setItem(row, 1, QTableWidgetItem(emp.get("name") or ""))
                    self.emp_table.setItem(row, 2, QTableWidgetItem(emp.get("phone") or ""))
                    self.emp_table.setItem(row, 3, QTableWidgetItem(emp.get("role") or ""))
            else:
                QMessageBox.critical(self, "실패", f"List failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"List employee error: {e}")

# Clients Tab
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
        self.client_outstanding_edit = QLineEdit()
        self.client_outstanding_edit.setText("0")
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
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 4)
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
            response = api_create_client(global_token, data)
            if response.status_code in (200, 201):
                QMessageBox.information(self, "성공", "Client created!")
                self.list_clients()
            else:
                QMessageBox.critical(self, "실패", f"Create client failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Create client error: {e}")
    def list_clients(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        try:
            response = api_fetch_clients(global_token)
            if response.status_code == 200:
                clients = response.json()
                self.client_table.setRowCount(0)
                for client in clients:
                    row = self.client_table.rowCount()
                    self.client_table.insertRow(row)
                    self.client_table.setItem(row, 0, QTableWidgetItem(str(client.get("id"))))
                    self.client_table.setItem(row, 1, QTableWidgetItem(client.get("client_name") or ""))
                    self.client_table.setItem(row, 2, QTableWidgetItem(client.get("address") or ""))
                    self.client_table.setItem(row, 3, QTableWidgetItem(client.get("phone") or ""))
                    self.client_table.setItem(row, 4, QTableWidgetItem(str(client.get("outstanding_amount"))))
            else:
                QMessageBox.critical(self, "실패", f"List clients failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"List client error: {e}")

# Products Tab
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
        self.prod_price_edit = QLineEdit()
        self.prod_price_edit.setText("0")
        left_layout.addRow("Default Price:", self.prod_price_edit)
        self.prod_stock_edit = QLineEdit()
        self.prod_stock_edit.setText("0")
        left_layout.addRow("Stock:", self.prod_stock_edit)
        self.prod_active_edit = QLineEdit()
        self.prod_active_edit.setText("1")
        left_layout.addRow("Is Active (1/0):", self.prod_active_edit)
        self.prod_category_edit = QLineEdit()
        left_layout.addRow("상품 분류:", self.prod_category_edit)
        self.prod_box_quantity_edit = QLineEdit()
        left_layout.addRow("박스당 개수:", self.prod_box_quantity_edit)
        btn_create = QPushButton("Create Product")
        btn_create.clicked.connect(self.create_product)
        left_layout.addRow(btn_create)
        left_panel.setLayout(left_layout)
        right_panel = QGroupBox("상품 목록")
        right_layout = QVBoxLayout()
        self.prod_table = QTableWidget()
        self.prod_table.setColumnCount(9)
        self.prod_table.setHorizontalHeaderLabels([
            "ID", "브랜드 ID", "상품명", "바코드", "가격", "재고", "박스당 개수", "분류", "활성화 여부"
        ])
        self.prod_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.prod_table)
        btn_refresh = QPushButton("Refresh Products")
        btn_refresh.clicked.connect(self.list_products)
        right_layout.addWidget(btn_refresh)
        right_panel.setLayout(right_layout)
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 4)
        self.setLayout(main_layout)
    def create_product(self):
        global global_token
        data = {
            "brand_id": int(self.prod_brand_id_edit.text() or 0),
            "product_name": self.prod_name_edit.text(),
            "barcode": self.prod_barcode_edit.text(),
            "default_price": float(self.prod_price_edit.text() or 0),
            "stock": int(self.prod_stock_edit.text() or 0),
            "box_quantity": int(self.prod_box_quantity_edit.text() or 1),
            "category": self.prod_category_edit.text(),
            "is_active": int(self.prod_active_edit.text() or 1),
        }
        try:
            response = api_create_product(global_token, data)
            if response.status_code in (200, 201):
                QMessageBox.information(self, "성공", "Product created!")
                self.list_products()
            else:
                QMessageBox.critical(self, "실패", f"Create product failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Create product error: {e}")
    def list_products(self):
        global global_token
        try:
            response = api_fetch_products(global_token)
            if response.status_code == 200:
                products = response.json()
                self.prod_table.setRowCount(0)
                for p in products:
                    row = self.prod_table.rowCount()
                    self.prod_table.insertRow(row)
                    self.prod_table.setItem(row, 0, QTableWidgetItem(str(p.get("id"))))
                    self.prod_table.setItem(row, 1, QTableWidgetItem(str(p.get("brand_id"))))
                    self.prod_table.setItem(row, 2, QTableWidgetItem(p.get("product_name") or ""))
                    self.prod_table.setItem(row, 3, QTableWidgetItem(p.get("barcode") or ""))
                    self.prod_table.setItem(row, 4, QTableWidgetItem(str(p.get("default_price"))))
                    self.prod_table.setItem(row, 5, QTableWidgetItem(str(p.get("stock"))))
                    self.prod_table.setItem(row, 6, QTableWidgetItem(str(p.get("box_quantity"))))
                    self.prod_table.setItem(row, 7, QTableWidgetItem(p.get("category") or "미분류"))
                    self.prod_table.setItem(row, 8, QTableWidgetItem("O" if p.get("is_active") else "X"))
            else:
                QMessageBox.critical(self, "실패", f"List products failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"List product error: {e}")
    def update_product(self):
        global global_token
        prod_id = self.prod_id_update_edit.text()
        if not prod_id:
            QMessageBox.warning(self, "경고", "Product ID를 입력하세요.")
            return
        data = {
            "brand_id": int(self.prod_brand_id_edit.text() or 0),
            "product_name": self.prod_name_edit.text(),
            "barcode": self.prod_barcode_edit.text(),
            "default_price": float(self.prod_price_edit.text() or 0),
            "stock": int(self.prod_stock_edit.text() or 0),
            "box_quantity": int(self.prod_box_quantity_edit.text() or 1),
            "category": self.prod_category_edit.text(),
            "is_active": int(self.prod_active_edit.text() or 1),
        }
        try:
            response = api_update_product(global_token, prod_id, data)
            if response.status_code == 200:
                QMessageBox.information(self, "성공", "Product updated!")
                self.list_products()
            else:
                QMessageBox.critical(self, "실패", f"Update product failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Update product error: {e}")
    def delete_product(self):
        global global_token
        prod_id = self.prod_id_delete_edit.text()
        if not prod_id:
            QMessageBox.warning(self, "경고", "Product ID를 입력하세요.")
            return
        try:
            response = api_delete_product(global_token, prod_id)
            if response.status_code == 200:
                QMessageBox.information(self, "성공", "Product deleted!")
                self.list_products()
            else:
                QMessageBox.critical(self, "실패", f"Delete product failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Delete product error: {e}")

# Orders Tab
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
        self.order_total_amount_edit = QLineEdit()
        left_layout.addRow("Total Amount:", self.order_total_amount_edit)
        self.order_status_edit = QLineEdit()
        self.order_status_edit.setPlaceholderText("예: pending, completed 등")
        left_layout.addRow("Status:", self.order_status_edit)
        self.create_order_btn = QPushButton("Create Order")
        self.create_order_btn.clicked.connect(self.create_order)
        left_layout.addRow(self.create_order_btn)
        left_panel.setLayout(left_layout)
        right_panel = QGroupBox("주문 목록")
        right_layout = QVBoxLayout()
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Client ID", "Employee ID", "Total Amount", "Status"])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.orders_table)
        refresh_btn = QPushButton("Refresh Orders")
        refresh_btn.clicked.connect(self.list_orders)
        right_layout.addWidget(refresh_btn)
        right_panel.setLayout(right_layout)
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 4)
        self.setLayout(main_layout)
    def create_order(self):
        global global_token
        data = {
            "client_id": int(self.order_client_id_edit.text() or 0),
            "employee_id": int(self.order_employee_id_edit.text() or 0),
            "total_amount": float(self.order_total_amount_edit.text() or 0),
            "status": self.order_status_edit.text(),
            "items": []  # 주문 항목은 필요에 따라 추가 구현
        }
        try:
            response = api_create_order(global_token, data)
            if response.status_code in (200, 201):
                QMessageBox.information(self, "성공", "Order created!")
                self.list_orders()
            else:
                QMessageBox.critical(self, "실패", f"Create order failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Create order error: {e}")
    def list_orders(self):
        global global_token
        try:
            response = api_fetch_orders(global_token)
            if response.status_code == 200:
                orders = response.json()
                self.orders_table.setRowCount(0)
                for order in orders:
                    row = self.orders_table.rowCount()
                    self.orders_table.insertRow(row)
                    self.orders_table.setItem(row, 0, QTableWidgetItem(str(order.get("id"))))
                    self.orders_table.setItem(row, 1, QTableWidgetItem(str(order.get("client_id"))))
                    self.orders_table.setItem(row, 2, QTableWidgetItem(str(order.get("employee_id"))))
                    self.orders_table.setItem(row, 3, QTableWidgetItem(str(order.get("total_amount"))))
                    self.orders_table.setItem(row, 4, QTableWidgetItem(order.get("status") or ""))
            else:
                QMessageBox.critical(self, "실패", f"List orders failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"List orders error: {e}")

# Sales Tab
class SalesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        main_layout = QHBoxLayout()
        left_panel = QGroupBox("매출 조회 입력")
        left_layout = QFormLayout()
        self.sale_employee_id_edit = QLineEdit()
        left_layout.addRow("Employee ID:", self.sale_employee_id_edit)
        self.sale_date_edit = QDateEdit()
        self.sale_date_edit.setCalendarPopup(True)
        self.sale_date_edit.setDate(QDate.currentDate())
        left_layout.addRow("Sale Date:", self.sale_date_edit)
        fetch_btn = QPushButton("Fetch Sales")
        fetch_btn.clicked.connect(self.fetch_sales)
        left_layout.addRow(fetch_btn)
        left_panel.setLayout(left_layout)
        right_panel = QGroupBox("매출 목록")
        right_layout = QVBoxLayout()
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(5)
        self.sales_table.setHorizontalHeaderLabels(["ID", "Client ID", "Employee ID", "Total Amount", "Sale Date"])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.sales_table)
        right_panel.setLayout(right_layout)
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 4)
        self.setLayout(main_layout)
    def fetch_sales(self):
        global global_token
        emp_id = self.sale_employee_id_edit.text().strip()
        sale_date = self.sale_date_edit.date().toString("yyyy-MM-dd")
        if not emp_id:
            QMessageBox.warning(self, "경고", "Employee ID를 입력하세요.")
            return
        try:
            # 예시: /sales/by_employee/{emp_id}/{sale_date} 엔드포인트 (API 구현 필요)
            response = requests.get(f"{BASE_URL}/sales/by_employee/{emp_id}/{sale_date}",
                                    headers={"Authorization": f"Bearer {global_token}"})
            if response.status_code == 200:
                sales = response.json()
                self.sales_table.setRowCount(0)
                for sale in sales:
                    row = self.sales_table.rowCount()
                    self.sales_table.insertRow(row)
                    self.sales_table.setItem(row, 0, QTableWidgetItem(str(sale.get("id"))))
                    self.sales_table.setItem(row, 1, QTableWidgetItem(str(sale.get("client_id"))))
                    self.sales_table.setItem(row, 2, QTableWidgetItem(str(sale.get("employee_id"))))
                    self.sales_table.setItem(row, 3, QTableWidgetItem(str(sale.get("total_amount"))))
                    self.sales_table.setItem(row, 4, QTableWidgetItem(sale.get("sale_date") or ""))
            else:
                QMessageBox.critical(self, "오류", f"Fetch sales failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Fetch sales error: {e}")

# Total Sales Tab
class TotalSalesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        main_layout = QHBoxLayout()
        left_panel = QGroupBox("총 매출 조회 입력")
        left_layout = QFormLayout()
        self.total_sale_date_edit = QDateEdit()
        self.total_sale_date_edit.setCalendarPopup(True)
        self.total_sale_date_edit.setDate(QDate.currentDate())
        left_layout.addRow("Sale Date:", self.total_sale_date_edit)
        fetch_btn = QPushButton("Fetch Total Sales")
        fetch_btn.clicked.connect(self.fetch_total_sales)
        left_layout.addRow(fetch_btn)
        left_panel.setLayout(left_layout)
        right_panel = QGroupBox("총 매출 목록")
        right_layout = QVBoxLayout()
        self.total_sales_table = QTableWidget()
        self.total_sales_table.setColumnCount(2)
        self.total_sales_table.setHorizontalHeaderLabels(["Client ID", "Total Sales"])
        self.total_sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.total_sales_table)
        right_panel.setLayout(right_layout)
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 4)
        self.setLayout(main_layout)
    def fetch_total_sales(self):
        global global_token
        sale_date = self.total_sale_date_edit.date().toString("yyyy-MM-dd")
        try:
            # 예시: /sales/total/{sale_date} 엔드포인트 (API 구현 필요)
            response = requests.get(f"{BASE_URL}/sales/total/{sale_date}",
                                    headers={"Authorization": f"Bearer {global_token}"})
            if response.status_code == 200:
                sales = response.json()
                self.total_sales_table.setRowCount(0)
                for sale in sales:
                    row = self.total_sales_table.rowCount()
                    self.total_sales_table.insertRow(row)
                    self.total_sales_table.setItem(row, 0, QTableWidgetItem(str(sale.get("client_id"))))
                    self.total_sales_table.setItem(row, 1, QTableWidgetItem(str(sale.get("total_sales"))))
            else:
                QMessageBox.critical(self, "오류", f"Fetch total sales failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Fetch total sales error: {e}")

# Employee Client Tab (Many-to-Many)
class EmployeeClientTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        main_layout = QHBoxLayout()
        left_panel = QGroupBox("Employee-Client 입력")
        left_layout = QFormLayout()
        self.emp_client_emp_id_edit = QLineEdit()
        left_layout.addRow("Employee ID:", self.emp_client_emp_id_edit)
        self.emp_client_client_id_edit = QLineEdit()
        left_layout.addRow("Client ID:", self.emp_client_client_id_edit)
        assign_btn = QPushButton("Assign Relationship")
        assign_btn.clicked.connect(self.assign_relationship)
        left_layout.addRow(assign_btn)
        left_panel.setLayout(left_layout)
        right_panel = QGroupBox("Employee-Client 관계 목록")
        right_layout = QVBoxLayout()
        self.emp_client_table = QTableWidget()
        self.emp_client_table.setColumnCount(4)
        self.emp_client_table.setHorizontalHeaderLabels(["ID", "Employee ID", "Client ID", "Start Date"])
        self.emp_client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.emp_client_table)
        refresh_btn = QPushButton("Refresh Relationships")
        refresh_btn.clicked.connect(self.list_relationships)
        right_layout.addWidget(refresh_btn)
        right_panel.setLayout(right_layout)
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 4)
        self.setLayout(main_layout)
    def assign_relationship(self):
        global global_token
        emp_id = self.emp_client_emp_id_edit.text().strip()
        client_id = self.emp_client_client_id_edit.text().strip()
        if not emp_id or not client_id:
            QMessageBox.warning(self, "경고", "Employee ID와 Client ID를 모두 입력하세요.")
            return
        try:
            response = api_assign_employee_client(global_token, int(emp_id), int(client_id))
            if response.status_code in (200, 201):
                QMessageBox.information(self, "성공", "Relationship assigned!")
                self.list_relationships()
            else:
                QMessageBox.critical(self, "실패", f"Assignment failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Assignment error: {e}")
    def list_relationships(self):
        global global_token
        # 예시: 직원별 관계 목록은 모든 관계를 불러온 후 필터링하거나 별도 API가 필요
        try:
            response = requests.get(f"{BASE_URL}/employee_clients", headers={"Authorization": f"Bearer {global_token}"})
            if response.status_code == 200:
                relationships = response.json()
                self.emp_client_table.setRowCount(0)
                for rel in relationships:
                    row = self.emp_client_table.rowCount()
                    self.emp_client_table.insertRow(row)
                    self.emp_client_table.setItem(row, 0, QTableWidgetItem(str(rel.get("id"))))
                    self.emp_client_table.setItem(row, 1, QTableWidgetItem(str(rel.get("employee_id"))))
                    self.emp_client_table.setItem(row, 2, QTableWidgetItem(str(rel.get("client_id"))))
                    self.emp_client_table.setItem(row, 3, QTableWidgetItem(rel.get("start_date") or ""))
            else:
                QMessageBox.critical(self, "실패", f"List relationships failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"List relationships error: {e}")

# Brand Product Tab
class BrandProductTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        main_layout = QHBoxLayout()
        left_panel = QGroupBox("브랜드 입력")
        left_layout = QFormLayout()
        self.brand_id_edit = QLineEdit()
        left_layout.addRow("Brand ID:", self.brand_id_edit)
        show_btn = QPushButton("Show Products")
        show_btn.clicked.connect(self.show_brand_products)
        left_layout.addRow(show_btn)
        left_panel.setLayout(left_layout)
        right_panel = QGroupBox("브랜드 상품 목록")
        right_layout = QVBoxLayout()
        self.brand_prod_table = QTableWidget()
        self.brand_prod_table.setColumnCount(3)
        self.brand_prod_table.setHorizontalHeaderLabels(["ID", "Product Name", "Barcode"])
        self.brand_prod_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.brand_prod_table)
        right_panel.setLayout(right_layout)
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 4)
        self.setLayout(main_layout)
    def show_brand_products(self):
        global global_token
        brand_id = self.brand_id_edit.text().strip()
        if not brand_id:
            QMessageBox.warning(self, "경고", "Brand ID를 입력하세요.")
            return
        try:
            response = api_fetch_brand_products(global_token, int(brand_id))
            if response.status_code == 200:
                products = response.json()
                self.brand_prod_table.setRowCount(0)
                for prod in products:
                    row = self.brand_prod_table.rowCount()
                    self.brand_prod_table.insertRow(row)
                    self.brand_prod_table.setItem(row, 0, QTableWidgetItem(str(prod.get("id"))))
                    self.brand_prod_table.setItem(row, 1, QTableWidgetItem(prod.get("product_name") or ""))
                    self.brand_prod_table.setItem(row, 2, QTableWidgetItem(prod.get("barcode") or ""))
            else:
                QMessageBox.critical(self, "실패", f"List failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Error: {e}")

# ----------------------------
# Main Window
# ----------------------------
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("업무 관리 시스템")
        self.setGeometry(0, 0, 1650, 1000)
        self.setStyleSheet(self.load_dark_theme())
        self.init_ui()
    def init_ui(self):
        self.toolbar = QToolBar("메인 메뉴")
        self.addToolBar(self.toolbar)
        self.toolbar.setIconSize(QSize(100, 100))
        current_dir = os.path.dirname(os.path.abspath(__file__))
        employee_path = os.path.join(current_dir, "icons", "employee.png")
        correspondent_path = os.path.join(current_dir, "icons", "correspondent.png")
        product_path = os.path.join(current_dir, "icons", "product.png")
        orders_path = os.path.join(current_dir, "icons", "orders.png")
        sales_path = os.path.join(current_dir, "icons", "sales.png")
        totalsales_path = os.path.join(current_dir, "icons", "totalsales.png")
        vehicle_path = os.path.join(current_dir, "icons", "vehicle.png")
        brand_path = os.path.join(current_dir, "icons", "brand.png")
        employee = QIcon(employee_path)
        correspondent = QIcon(correspondent_path)
        product = QIcon(product_path)
        orders = QIcon(orders_path)
        sales = QIcon(sales_path)
        totalsales = QIcon(totalsales_path)
        vehicle = QIcon(vehicle_path)
        brand = QIcon(brand_path)
        self.add_toolbar_action("직원 관리", employee, self.show_employee_tab)
        self.add_toolbar_action("거래처 관리", correspondent, self.show_client_tab)
        self.add_toolbar_action("상품 관리", product, self.show_product_tab)
        self.add_toolbar_action("주문 관리", orders, self.show_orders_tab)
        self.add_toolbar_action("매출 관리", sales, self.show_sales_tab)
        self.add_toolbar_action("총매출", totalsales, self.show_total_sales_tab)
        self.add_toolbar_action("차량 관리", vehicle, self.show_vehicle_tab)
        self.add_toolbar_action("EMP-CLIENT", "icons/empclient.png", self.show_employee_client_tab)
        self.add_toolbar_action("Brand-Product", brand, self.show_brand_product_tab)
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        # 각 탭 생성 (좌측 입력, 우측 출력 형태)
        self.employee_tab = EmployeesTab()
        self.clients_tab = ClientsTab()
        self.products_tab = ProductsTab()
        self.orders_tab = OrdersTab()
        self.sales_tab = SalesTab()
        self.total_sales_tab = TotalSalesTab()
        self.vehicle_tab = EmployeeVehicleTab()
        self.emp_client_tab = EmployeeClientTab()
        self.brand_prod_tab = BrandProductTab()
        self.stacked_widget.addWidget(self.employee_tab)
        self.stacked_widget.addWidget(self.clients_tab)
        self.stacked_widget.addWidget(self.products_tab)
        self.stacked_widget.addWidget(self.orders_tab)
        self.stacked_widget.addWidget(self.sales_tab)
        self.stacked_widget.addWidget(self.total_sales_tab)
        self.stacked_widget.addWidget(self.vehicle_tab)
        self.stacked_widget.addWidget(self.emp_client_tab)
        self.stacked_widget.addWidget(self.brand_prod_tab)
        self.stacked_widget.setCurrentWidget(self.employee_tab)
    def add_toolbar_action(self, name, icon_path, callback):
        action = QAction(QIcon(icon_path), name, self)
        action.triggered.connect(callback)
        self.toolbar.addAction(action)
    def show_employee_tab(self):
        self.stacked_widget.setCurrentWidget(self.employee_tab)
    def show_client_tab(self):
        self.stacked_widget.setCurrentWidget(self.clients_tab)
    def show_product_tab(self):
        self.stacked_widget.setCurrentWidget(self.products_tab)
    def show_orders_tab(self):
        self.stacked_widget.setCurrentWidget(self.orders_tab)
    def show_sales_tab(self):
        self.stacked_widget.setCurrentWidget(self.sales_tab)
    def show_total_sales_tab(self):
        self.stacked_widget.setCurrentWidget(self.total_sales_tab)
    def show_vehicle_tab(self):
        self.stacked_widget.setCurrentWidget(self.vehicle_tab)
    def show_employee_client_tab(self):
        self.stacked_widget.setCurrentWidget(self.emp_client_tab)
    def show_brand_product_tab(self):
        self.stacked_widget.setCurrentWidget(self.brand_prod_tab)
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
# Main Function
# ----------------------------
def main():
    app = QApplication(sys.argv)
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.Accepted:
        main_window = MainApp()
        main_window.show()
        sys.exit(app.exec_())
    else:
        sys.exit()

if __name__ == "__main__":
    main()

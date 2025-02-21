#!/usr/bin/env python
import sys
import json
import requests
import openpyxl
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QMessageBox, QFileDialog, QHeaderView, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGroupBox  

# --- 글로벌 변수 및 API base ---
BASE_URL = "http://127.0.0.1:8000"
global_token = None

# --- API Service functions ---
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
        # 열 순서: employee_number, password, name, phone, role
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

# --- Login Dialog ---
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
        # 제한: Only allow ID 1
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

# --- Employees Tab ---
class EmployeesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.emp_number_edit = QLineEdit()
        form_layout.addRow("Employee Number:", self.emp_number_edit)
        self.emp_password_edit = QLineEdit()
        self.emp_password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.emp_password_edit)
        self.emp_name_edit = QLineEdit()
        form_layout.addRow("Name:", self.emp_name_edit)
        self.emp_phone_edit = QLineEdit()
        form_layout.addRow("Phone:", self.emp_phone_edit)
        self.emp_role_edit = QLineEdit()
        self.emp_role_edit.setText("sales")
        form_layout.addRow("Role:", self.emp_role_edit)
        main_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.create_btn = QPushButton("Create")
        self.create_btn.clicked.connect(self.create_employee)
        btn_layout.addWidget(self.create_btn)
        self.update_btn = QPushButton("Update")
        self.update_btn.clicked.connect(self.update_employee)
        btn_layout.addWidget(self.update_btn)
        self.delete_btn = QPushButton("Delete by ID")
        self.delete_btn.clicked.connect(self.delete_employee)
        btn_layout.addWidget(self.delete_btn)
        main_layout.addLayout(btn_layout)

        self.emp_id_delete_edit = QLineEdit()
        self.emp_id_delete_edit.setPlaceholderText("Employee ID to delete")
        main_layout.addWidget(self.emp_id_delete_edit)

        self.refresh_btn = QPushButton("Refresh List")
        self.refresh_btn.clicked.connect(self.list_employees)
        main_layout.addWidget(self.refresh_btn)

        self.emp_table = QTableWidget()
        self.emp_table.setColumnCount(5)
        self.emp_table.setHorizontalHeaderLabels(["ID", "Employee #", "Name", "Phone", "Role"])
        self.emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.emp_table)

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
            "role": self.emp_role_edit.text()
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
            "role": self.emp_role_edit.text()
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
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        emp_id = self.emp_id_delete_edit.text().strip()
        if not emp_id:
            QMessageBox.warning(self, "경고", "삭제할 Employee의 ID를 입력하세요.")
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
                    row_position = self.emp_table.rowCount()
                    self.emp_table.insertRow(row_position)
                    self.emp_table.setItem(row_position, 0, QTableWidgetItem(str(emp.get("id"))))
                    self.emp_table.setItem(row_position, 1, QTableWidgetItem(emp.get("employee_number") or ""))
                    self.emp_table.setItem(row_position, 2, QTableWidgetItem(emp.get("name") or ""))
                    self.emp_table.setItem(row_position, 3, QTableWidgetItem(emp.get("phone") or ""))
                    self.emp_table.setItem(row_position, 4, QTableWidgetItem(emp.get("role") or ""))
            else:
                QMessageBox.critical(self, "실패", f"List failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"List employee error: {e}")

    def import_employees_from_excel(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
        if not filepath:
            return
        try:
            api_import_employees_from_excel(global_token, filepath)
            QMessageBox.information(self, "성공", "Excel import completed!")
            self.list_employees()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Excel import failed: {e}")

# --- Clients Tab ---
class ClientsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.client_name_edit = QLineEdit()
        form_layout.addRow("Client Name:", self.client_name_edit)
        self.client_address_edit = QLineEdit()
        form_layout.addRow("Address:", self.client_address_edit)
        self.client_phone_edit = QLineEdit()
        form_layout.addRow("Phone:", self.client_phone_edit)
        self.client_outstanding_edit = QLineEdit()
        self.client_outstanding_edit.setText("0")
        form_layout.addRow("Outstanding Amount:", self.client_outstanding_edit)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.create_client_btn = QPushButton("Create Client")
        self.create_client_btn.clicked.connect(self.create_client)
        btn_layout.addWidget(self.create_client_btn)
        self.list_client_btn = QPushButton("List Clients")
        self.list_client_btn.clicked.connect(self.list_clients)
        btn_layout.addWidget(self.list_client_btn)
        layout.addLayout(btn_layout)

        self.client_table = QTableWidget()
        self.client_table.setColumnCount(5)
        self.client_table.setHorizontalHeaderLabels(["ID", "Name", "Address", "Phone", "Outstanding"])
        self.client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.client_table)

        self.setLayout(layout)

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
                    row_position = self.client_table.rowCount()
                    self.client_table.insertRow(row_position)
                    self.client_table.setItem(row_position, 0, QTableWidgetItem(str(client.get("id"))))
                    self.client_table.setItem(row_position, 1, QTableWidgetItem(client.get("client_name") or ""))
                    self.client_table.setItem(row_position, 2, QTableWidgetItem(client.get("address") or ""))
                    self.client_table.setItem(row_position, 3, QTableWidgetItem(client.get("phone") or ""))
                    self.client_table.setItem(row_position, 4, QTableWidgetItem(str(client.get("outstanding_amount"))))
            else:
                QMessageBox.critical(self, "실패", f"List clients failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"List client error: {e}")

# --- Products Tab ---
class ProductsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.prod_brand_id_edit = QLineEdit()
        form_layout.addRow("Brand ID:", self.prod_brand_id_edit)
        self.prod_name_edit = QLineEdit()
        form_layout.addRow("Product Name:", self.prod_name_edit)
        self.prod_barcode_edit = QLineEdit()
        form_layout.addRow("Barcode:", self.prod_barcode_edit)
        self.prod_price_edit = QLineEdit()
        self.prod_price_edit.setText("0")
        form_layout.addRow("Default Price:", self.prod_price_edit)
        self.prod_stock_edit = QLineEdit()
        self.prod_stock_edit.setText("0")
        form_layout.addRow("Stock:", self.prod_stock_edit)
        self.prod_active_edit = QLineEdit()
        self.prod_active_edit.setText("1")
        form_layout.addRow("Is Active (1/0):", self.prod_active_edit)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.create_prod_btn = QPushButton("Create Product")
        self.create_prod_btn.clicked.connect(self.create_product)
        btn_layout.addWidget(self.create_prod_btn)
        self.list_prod_btn = QPushButton("List Products")
        self.list_prod_btn.clicked.connect(self.list_products)
        btn_layout.addWidget(self.list_prod_btn)
        layout.addLayout(btn_layout)

        form_layout2 = QFormLayout()
        self.prod_id_update_edit = QLineEdit()
        form_layout2.addRow("Prod ID to update:", self.prod_id_update_edit)
        self.update_prod_btn = QPushButton("Update Product")
        self.update_prod_btn.clicked.connect(self.update_product)
        form_layout2.addRow(self.update_prod_btn)
        self.prod_id_delete_edit = QLineEdit()
        form_layout2.addRow("Prod ID to delete:", self.prod_id_delete_edit)
        self.delete_prod_btn = QPushButton("Delete Product")
        self.delete_prod_btn.clicked.connect(self.delete_product)
        form_layout2.addRow(self.delete_prod_btn)
        layout.addLayout(form_layout2)

        self.prod_table = QTableWidget()
        self.prod_table.setColumnCount(7)
        self.prod_table.setHorizontalHeaderLabels(["ID", "Brand ID", "Product Name", "Barcode", "Default Price", "Stock", "Is Active"])
        self.prod_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.prod_table)

        self.setLayout(layout)

    def create_product(self):
        global global_token
        data = {
            "brand_id": int(self.prod_brand_id_edit.text() or 0),
            "product_name": self.prod_name_edit.text(),
            "barcode": self.prod_barcode_edit.text(),
            "default_price": float(self.prod_price_edit.text() or 0),
            "stock": int(self.prod_stock_edit.text() or 0),
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
                    row_position = self.prod_table.rowCount()
                    self.prod_table.insertRow(row_position)
                    self.prod_table.setItem(row_position, 0, QTableWidgetItem(str(p.get("id"))))
                    self.prod_table.setItem(row_position, 1, QTableWidgetItem(str(p.get("brand_id"))))
                    self.prod_table.setItem(row_position, 2, QTableWidgetItem(p.get("product_name") or ""))
                    self.prod_table.setItem(row_position, 3, QTableWidgetItem(p.get("barcode") or ""))
                    self.prod_table.setItem(row_position, 4, QTableWidgetItem(str(p.get("default_price"))))
                    self.prod_table.setItem(row_position, 5, QTableWidgetItem(str(p.get("stock"))))
                    self.prod_table.setItem(row_position, 6, QTableWidgetItem(str(p.get("is_active"))))
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

# --- Employee-Client Tab (Many-to-Many) ---
class EmployeeClientTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # 관계 등록 부분
        assign_group = QGroupBox("Assign Relationship")
        assign_layout = QFormLayout()
        self.emp_id_edit = QLineEdit()
        assign_layout.addRow("Employee ID:", self.emp_id_edit)
        self.client_id_edit = QLineEdit()
        assign_layout.addRow("Client ID:", self.client_id_edit)
        self.assign_btn = QPushButton("Assign")
        self.assign_btn.clicked.connect(self.assign_relationship)
        assign_layout.addRow(self.assign_btn)
        assign_group.setLayout(assign_layout)
        main_layout.addWidget(assign_group)

        # 사원별 거래처 조회 부분
        list_group = QGroupBox("List Clients of Employee")
        list_layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.emp_id_list_edit = QLineEdit()
        form_layout.addRow("Employee ID:", self.emp_id_list_edit)
        self.show_clients_btn = QPushButton("Show Clients")
        self.show_clients_btn.clicked.connect(self.show_clients)
        form_layout.addRow(self.show_clients_btn)
        list_layout.addLayout(form_layout)

        self.emp_clients_table = QTableWidget()
        self.emp_clients_table.setColumnCount(4)
        self.emp_clients_table.setHorizontalHeaderLabels(["ID", "Name", "Address", "Phone"])
        self.emp_clients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        list_layout.addWidget(self.emp_clients_table)
        list_group.setLayout(list_layout)
        main_layout.addWidget(list_group)

        self.setLayout(main_layout)

    def assign_relationship(self):
        global global_token
        emp_id = self.emp_id_edit.text().strip()
        client_id = self.client_id_edit.text().strip()
        if not emp_id or not client_id:
            QMessageBox.warning(self, "경고", "Employee ID와 Client ID를 입력하세요.")
            return
        try:
            data = {"employee_id": int(emp_id), "client_id": int(client_id)}
            response = api_assign_employee_client(global_token, data["employee_id"], data["client_id"])
            if response.status_code in (200, 201):
                QMessageBox.information(self, "성공", "Employee-Client relationship assigned!")
            else:
                QMessageBox.critical(self, "실패", f"Assignment failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Assignment error: {e}")

    def show_clients(self):
        global global_token
        emp_id = self.emp_id_list_edit.text().strip()
        if not emp_id:
            QMessageBox.warning(self, "경고", "Employee ID를 입력하세요.")
            return
        try:
            response = api_fetch_employee_clients(global_token, emp_id)
            if response.status_code == 200:
                clients = response.json()
                self.emp_clients_table.setRowCount(0)
                for client in clients:
                    row = self.emp_clients_table.rowCount()
                    self.emp_clients_table.insertRow(row)
                    self.emp_clients_table.setItem(row, 0, QTableWidgetItem(str(client.get("id"))))
                    self.emp_clients_table.setItem(row, 1, QTableWidgetItem(client.get("client_name") or ""))
                    self.emp_clients_table.setItem(row, 2, QTableWidgetItem(client.get("address") or ""))
                    self.emp_clients_table.setItem(row, 3, QTableWidgetItem(client.get("phone") or ""))
            else:
                QMessageBox.critical(self, "실패", f"List failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"List error: {e}")



class BrandProductTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        group = QGroupBox("Brand → Products")
        layout = QFormLayout()
        self.brand_id_edit = QLineEdit()
        layout.addRow("Brand ID:", self.brand_id_edit)
        self.show_prod_btn = QPushButton("Show Products")
        self.show_prod_btn.clicked.connect(self.show_brand_products)
        layout.addRow(self.show_prod_btn)
        group.setLayout(layout)
        main_layout.addWidget(group)

        self.prod_table = QTableWidget()
        self.prod_table.setColumnCount(3)
        self.prod_table.setHorizontalHeaderLabels(["ID", "Product Name", "Barcode"])
        self.prod_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.prod_table)
        self.setLayout(main_layout)

    def show_brand_products(self):
        brand_id = self.brand_id_edit.text().strip()
        if not brand_id:
            QMessageBox.warning(self, "경고", "Brand ID를 입력하세요.")
            return
        try:
            response = api_fetch_brand_products(global_token, brand_id)
            if response.status_code == 200:
                products = response.json()
                self.prod_table.setRowCount(0)
                for prod in products:
                    row = self.prod_table.rowCount()
                    self.prod_table.insertRow(row)
                    self.prod_table.setItem(row, 0, QTableWidgetItem(str(prod.get("id"))))
                    self.prod_table.setItem(row, 1, QTableWidgetItem(prod.get("product_name") or ""))
                    self.prod_table.setItem(row, 2, QTableWidgetItem(prod.get("barcode") or ""))
            else:
                QMessageBox.critical(self, "실패", f"List failed: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Error: {e}")

# --- Main Window ---
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("API Data Manager (PyQt5)")
        self.setGeometry(100, 100, 1000, 600)
        self.init_ui()

    def init_ui(self):
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.emp_tab = EmployeesTab()
        self.client_tab = ClientsTab()
        self.prod_tab = ProductsTab()
        self.emp_client_tab = EmployeeClientTab()
        self.brand_prod_tab = BrandProductTab()

        self.tab_widget.addTab(self.emp_client_tab, "Emp-Client (M2M)")
        self.tab_widget.addTab(self.emp_tab, "Employees")
        self.tab_widget.addTab(self.client_tab, "Clients")
        self.tab_widget.addTab(self.prod_tab, "Products")
        self.tab_widget.addTab(self.brand_prod_tab, "Brand-Products")

# --- Main ---
def main():
    app = QApplication(sys.argv)
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.Accepted:
        main_window = MainApp()
        main_window.show()
        sys.exit(app.exec())
    else:
        sys.exit()

if __name__ == "__main__":
    main()

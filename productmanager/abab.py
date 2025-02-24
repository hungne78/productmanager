#!/usr/bin/env python
import sys
import requests
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QToolBar, QAction,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QHBoxLayout, QHeaderView, QMessageBox, QStackedWidget,
    QLabel, QDialog, QFormLayout, QComboBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

# ----------------------------
# SERVER BASE
# ----------------------------
BASE_URL = "http://127.0.0.1:8000"

# ----------------------------
# DARK THEME
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
# API calls (직원, 거래처, 제품, 브랜드, 주문, 매출, 직원-거래처, 직원차량, 거래처방문 등)
# ----------------------------
def api_get_employees():
    return requests.get(f"{BASE_URL}/employees")

def api_get_clients():
    return requests.get(f"{BASE_URL}/clients")

def api_get_brands():
    return requests.get(f"{BASE_URL}/brands")

def api_get_products():
    return requests.get(f"{BASE_URL}/products")

def api_get_orders():
    return requests.get(f"{BASE_URL}/orders")

def api_search_orders(date_query=None, employee_id=None):
    params = {}
    if date_query:
        params["date_query"] = date_query
    if employee_id:
        params["employee_id"] = employee_id
    return requests.get(f"{BASE_URL}/orders/search", params=params)

def api_create_order(payload):
    return requests.post(f"{BASE_URL}/orders", json=payload)

def api_update_order(order_id, payload):
    return requests.put(f"{BASE_URL}/orders/{order_id}", json=payload)

def api_delete_order(order_id):
    return requests.delete(f"{BASE_URL}/orders/{order_id}")

def api_get_sales():
    return requests.get(f"{BASE_URL}/sales")

def api_create_sales(payload):
    return requests.post(f"{BASE_URL}/sales", json=payload)

def api_delete_sales(sales_id):
    return requests.delete(f"{BASE_URL}/sales/{sales_id}")

def api_get_employee_clients():
    return requests.get(f"{BASE_URL}/employee_clients")

def api_create_employee_client(payload):
    return requests.post(f"{BASE_URL}/employee_clients", json=payload)

def api_get_vehicle():
    return requests.get(f"{BASE_URL}/employee_vehicles")

def api_create_vehicle(payload):
    return requests.post(f"{BASE_URL}/employee_vehicles", json=payload)

def api_get_client_visits():
    return requests.get(f"{BASE_URL}/client_visits")

def api_create_client_visit(payload):
    return requests.post(f"{BASE_URL}/client_visits", json=payload)

# ... (필요시 update, delete 등도 추가)

# ----------------------------
# Tabs
# ----------------------------

class EmployeeTab(QWidget):
    """
    간단: 직원 목록 + CRUD
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID","Name","Phone","Role"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("Load Employees")
        btn_layout.addWidget(self.btn_load)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.btn_load.clicked.connect(self.load_employees)

    def load_employees(self):
        try:
            resp = api_get_employees()
            if resp.status_code == 200:
                emps = resp.json()
                self.table.setRowCount(0)
                for e in emps:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(str(e.get("id",""))))
                    self.table.setItem(row, 1, QTableWidgetItem(e.get("name","")))
                    self.table.setItem(row, 2, QTableWidgetItem(e.get("phone","")))
                    self.table.setItem(row, 3, QTableWidgetItem(e.get("role","")))
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

class ClientTab(QWidget):
    """
    거래처 목록
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID","Name","Address","Phone","Outstanding"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.btn_load = QPushButton("Load Clients")
        layout.addWidget(self.btn_load)

        self.setLayout(layout)
        self.btn_load.clicked.connect(self.load_clients)

    def load_clients(self):
        try:
            resp = api_get_clients()
            if resp.status_code == 200:
                data = resp.json()
                self.table.setRowCount(0)
                for c in data:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(str(c.get("id",""))))
                    self.table.setItem(row, 1, QTableWidgetItem(c.get("client_name","")))
                    self.table.setItem(row, 2, QTableWidgetItem(c.get("address","")))
                    self.table.setItem(row, 3, QTableWidgetItem(c.get("phone","")))
                    self.table.setItem(row, 4, QTableWidgetItem(str(c.get("outstanding_amount",""))))
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

class BrandTab(QWidget):
    """
    브랜드 목록 + 각 브랜드별 제품
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID","BrandName","..."])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.btn_load = QPushButton("Load Brands")
        layout.addWidget(self.btn_load)

        self.setLayout(layout)
        self.btn_load.clicked.connect(self.load_brands)

    def load_brands(self):
        try:
            resp = api_get_brands()
            if resp.status_code == 200:
                data = resp.json()
                self.table.setRowCount(0)
                for b in data:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(str(b.get("id",""))))
                    self.table.setItem(row, 1, QTableWidgetItem(b.get("brand_name","")))
                    self.table.setItem(row, 2, QTableWidgetItem("..."))
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

class ProductTab(QWidget):
    """
    제품 목록(brand_id, product_name, etc.)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID","BrandID","Name","Price","Stock","Active"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.btn_load = QPushButton("Load Products")
        layout.addWidget(self.btn_load)

        self.setLayout(layout)
        self.btn_load.clicked.connect(self.load_products)

    def load_products(self):
        try:
            resp = api_get_products()
            if resp.status_code == 200:
                data = resp.json()
                self.table.setRowCount(0)
                for p in data:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(str(p.get("id",""))))
                    self.table.setItem(row, 1, QTableWidgetItem(str(p.get("brand_id",""))))
                    self.table.setItem(row, 2, QTableWidgetItem(p.get("product_name","")))
                    self.table.setItem(row, 3, QTableWidgetItem(str(p.get("default_price",""))))
                    self.table.setItem(row, 4, QTableWidgetItem(str(p.get("stock",""))))
                    self.table.setItem(row, 5, QTableWidgetItem("Yes" if p.get("is_active") else "No"))
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

class OrderTab(QWidget):
    """
    주문관리 탭
    - 오른쪽을 4등분하지 않고,
    - 날짜 + 직원 검색
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()

        # 검색 부분
        filter_layout = QHBoxLayout()
        self.date_edit = QLineEdit()
        self.date_edit.setPlaceholderText("YYYY-MM-DD")
        self.emp_edit = QLineEdit()
        self.emp_edit.setPlaceholderText("직원ID")
        self.btn_search = QPushButton("Search Orders")

        filter_layout.addWidget(QLabel("날짜:"))
        filter_layout.addWidget(self.date_edit)
        filter_layout.addWidget(QLabel("직원ID:"))
        filter_layout.addWidget(self.emp_edit)
        filter_layout.addWidget(self.btn_search)
        layout.addLayout(filter_layout)

        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID","ClientID","EmployeeID","Total","Status","OrderDate"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # 버튼
        btn_layout = QHBoxLayout()
        self.btn_load_all = QPushButton("Load All")
        self.btn_create = QPushButton("Create(Order) - Example")
        self.btn_update = QPushButton("Update(Order) - Example")
        self.btn_delete = QPushButton("Delete(Order)")
        btn_layout.addWidget(self.btn_load_all)
        btn_layout.addWidget(self.btn_create)
        btn_layout.addWidget(self.btn_update)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("Order ID for update/delete")
        layout.addWidget(self.id_edit)

        self.setLayout(layout)

        self.btn_search.clicked.connect(self.search_orders)
        self.btn_load_all.clicked.connect(self.load_all_orders)
        self.btn_create.clicked.connect(self.create_order_example)
        self.btn_update.clicked.connect(self.update_order_example)
        self.btn_delete.clicked.connect(self.delete_order)

    def search_orders(self):
        d = self.date_edit.text().strip()
        e = self.emp_edit.text().strip()
        try:
            resp = api_search_orders(date_query=d or None, employee_id=e or None)
            if resp.status_code == 200:
                orders = resp.json()
                self.show_orders(orders)
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def load_all_orders(self):
        try:
            resp = api_get_orders()
            if resp.status_code == 200:
                self.show_orders(resp.json())
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def show_orders(self, orders):
        self.table.setRowCount(0)
        for o in orders:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(o.get("id",""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(o.get("client_id",""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(o.get("employee_id",""))))
            self.table.setItem(row, 3, QTableWidgetItem(str(o.get("total_amount",""))))
            self.table.setItem(row, 4, QTableWidgetItem(o.get("status","")))
            self.table.setItem(row, 5, QTableWidgetItem(str(o.get("order_date",""))))

    def create_order_example(self):
        payload = {
            "client_id": 2,
            "employee_id": 1,
            "items": [
                {
                    "product_id": 1,
                    "quantity": 3,
                    "unit_price": 1000,
                    "line_total": 3000,
                    "incentive": 0
                }
            ],
            "status": "pending"
        }
        try:
            resp = api_create_order(payload)
            if resp.status_code in (200,201):
                QMessageBox.information(self, "Success", "Order created")
                self.load_all_orders()
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def update_order_example(self):
        oid = self.id_edit.text().strip()
        if not oid:
            QMessageBox.warning(self, "Warning", "Enter order ID to update")
            return
        payload = {
            "client_id": 2,
            "employee_id": 1,
            "status": "updated",
            "items": [
                {
                    "product_id": 1,
                    "quantity": 5,
                    "unit_price": 1200,
                    "line_total": 6000,
                    "incentive": 100
                }
            ]
        }
        try:
            resp = api_update_order(oid, payload)
            if resp.status_code == 200:
                QMessageBox.information(self, "Success", "Order updated")
                self.load_all_orders()
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def delete_order(self):
        oid = self.id_edit.text().strip()
        if not oid:
            QMessageBox.warning(self, "Warn", "Enter ID to delete")
            return
        try:
            resp = api_delete_order(oid)
            if resp.status_code == 200:
                QMessageBox.information(self, "Success", "Order deleted")
                self.load_all_orders()
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

class SalesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID","ClientID","ProductID","Quantity","SaleDate"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("Load Sales")
        self.btn_create = QPushButton("Create Sales(Example)")
        self.btn_delete = QPushButton("Delete Sales(by ID)")
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_create)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("Sales ID to delete")
        layout.addWidget(self.id_edit)

        self.setLayout(layout)

        self.btn_load.clicked.connect(self.load_sales)
        self.btn_create.clicked.connect(self.create_sales_example)
        self.btn_delete.clicked.connect(self.delete_sales)

    def load_sales(self):
        try:
            resp = api_get_sales()
            if resp.status_code == 200:
                sales_data = resp.json()
                self.table.setRowCount(0)
                for s in sales_data:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(str(s.get("id",""))))
                    self.table.setItem(row, 1, QTableWidgetItem(str(s.get("client_id",""))))
                    self.table.setItem(row, 2, QTableWidgetItem(str(s.get("product_id",""))))
                    self.table.setItem(row, 3, QTableWidgetItem(str(s.get("quantity",""))))
                    self.table.setItem(row, 4, QTableWidgetItem(str(s.get("sale_date",""))))
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def create_sales_example(self):
        payload = {
            "client_id": 2,
            "product_id": 1,
            "quantity": 10,
            "sale_date": "2025-03-15"
        }
        try:
            resp = api_create_sales(payload)
            if resp.status_code in (200,201):
                QMessageBox.information(self, "Success", "Sales created")
                self.load_sales()
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def delete_sales(self):
        sid = self.id_edit.text().strip()
        if not sid:
            QMessageBox.warning(self, "Warning", "Enter sales ID")
            return
        try:
            resp = api_delete_sales(sid)
            if resp.status_code == 200:
                QMessageBox.information(self, "Success", "Sales deleted")
                self.load_sales()
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

class EmployeeClientTab(QWidget):
    """
    직원-거래처 다대다 관계
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID","EmployeeID","ClientID","StartDate","EndDate"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("Load Employee-Clients")
        self.btn_create = QPushButton("Assign Employee->Client")
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_create)
        layout.addLayout(btn_layout)

        # 입력
        self.emp_edit = QLineEdit()
        self.emp_edit.setPlaceholderText("EmployeeID")
        self.client_edit = QLineEdit()
        self.client_edit.setPlaceholderText("ClientID")
        layout.addWidget(self.emp_edit)
        layout.addWidget(self.client_edit)

        self.setLayout(layout)

        self.btn_load.clicked.connect(self.load_relations)
        self.btn_create.clicked.connect(self.assign_relation)

    def load_relations(self):
        try:
            resp = api_get_employee_clients()
            if resp.status_code == 200:
                data = resp.json()
                self.table.setRowCount(0)
                for ec in data:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(str(ec.get("id",""))))
                    self.table.setItem(row, 1, QTableWidgetItem(str(ec.get("employee_id",""))))
                    self.table.setItem(row, 2, QTableWidgetItem(str(ec.get("client_id",""))))
                    self.table.setItem(row, 3, QTableWidgetItem(str(ec.get("start_date",""))))
                    self.table.setItem(row, 4, QTableWidgetItem(str(ec.get("end_date",""))))
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def assign_relation(self):
        payload = {
            "employee_id": int(self.emp_edit.text() or 0),
            "client_id": int(self.client_edit.text() or 0),
            "start_date": None,
            "end_date": None
        }
        try:
            resp = api_create_employee_client(payload)
            if resp.status_code in (200,201):
                QMessageBox.information(self, "Success", "Assigned!")
                self.load_relations()
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

class VehicleTab(QWidget):
    """
    직원차량
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["EmpID","MonthlyFuel","Mileage","LastOilChange"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("Load Vehicles")
        self.btn_create = QPushButton("Create/Update Vehicle")
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_create)
        layout.addLayout(btn_layout)

        self.emp_edit = QLineEdit()
        self.emp_edit.setPlaceholderText("EmployeeID")
        self.fuel_edit = QLineEdit()
        self.fuel_edit.setPlaceholderText("MonthlyFuel")
        self.mileage_edit = QLineEdit()
        self.mileage_edit.setPlaceholderText("Mileage")
        self.oil_edit = QLineEdit()
        self.oil_edit.setPlaceholderText("YYYY-MM-DD")

        layout.addWidget(self.emp_edit)
        layout.addWidget(self.fuel_edit)
        layout.addWidget(self.mileage_edit)
        layout.addWidget(self.oil_edit)

        self.setLayout(layout)

        self.btn_load.clicked.connect(self.load_vehicles)
        self.btn_create.clicked.connect(self.create_vehicle)

    def load_vehicles(self):
        try:
            resp = api_get_vehicle()
            if resp.status_code == 200:
                data = resp.json()
                self.table.setRowCount(0)
                for v in data:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(str(v.get("id",""))))
                    self.table.setItem(row, 1, QTableWidgetItem(str(v.get("monthly_fuel_cost",""))))
                    self.table.setItem(row, 2, QTableWidgetItem(str(v.get("current_mileage",""))))
                    self.table.setItem(row, 3, QTableWidgetItem(str(v.get("last_engine_oil_change",""))))
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def create_vehicle(self):
        payload = {
            "id": int(self.emp_edit.text() or 0),
            "monthly_fuel_cost": float(self.fuel_edit.text() or 0),
            "current_mileage": int(self.mileage_edit.text() or 0),
            "last_engine_oil_change": self.oil_edit.text() or None
        }
        try:
            resp = api_create_vehicle(payload)
            if resp.status_code in (200,201):
                QMessageBox.information(self, "Success", "Vehicle created/updated")
                self.load_vehicles()
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

class ClientVisitTab(QWidget):
    """
    거래처 방문
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID","EmpID","ClientID","VisitTime","OrderID"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.btn_load = QPushButton("Load Visits")
        layout.addWidget(self.btn_load)

        # Create
        self.emp_edit = QLineEdit()
        self.emp_edit.setPlaceholderText("EmpID")
        self.client_edit = QLineEdit()
        self.client_edit.setPlaceholderText("ClientID")
        self.visit_edit = QLineEdit()
        self.visit_edit.setPlaceholderText("YYYY-MM-DD HH:MM")
        self.order_edit = QLineEdit()
        self.order_edit.setPlaceholderText("OrderID(optional)")

        layout.addWidget(self.emp_edit)
        layout.addWidget(self.client_edit)
        layout.addWidget(self.visit_edit)
        layout.addWidget(self.order_edit)

        self.btn_create = QPushButton("Create Visit")
        layout.addWidget(self.btn_create)

        self.setLayout(layout)

        self.btn_load.clicked.connect(self.load_visits)
        self.btn_create.clicked.connect(self.create_visit)

    def load_visits(self):
        try:
            resp = api_get_client_visits()
            if resp.status_code == 200:
                data = resp.json()
                self.table.setRowCount(0)
                for v in data:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(str(v.get("id",""))))
                    self.table.setItem(row, 1, QTableWidgetItem(str(v.get("employee_id",""))))
                    self.table.setItem(row, 2, QTableWidgetItem(str(v.get("client_id",""))))
                    self.table.setItem(row, 3, QTableWidgetItem(str(v.get("visit_datetime",""))))
                    self.table.setItem(row, 4, QTableWidgetItem(str(v.get("order_id",""))))
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def create_visit(self):
        payload = {
            "employee_id": int(self.emp_edit.text() or 0),
            "client_id": int(self.client_edit.text() or 0),
            "visit_datetime": self.visit_edit.text() or None,
            "order_id": int(self.order_edit.text() or 0) if self.order_edit.text() else None
        }
        try:
            resp = api_create_client_visit(payload)
            if resp.status_code in (200,201):
                QMessageBox.information(self, "Success", "Visit created")
                self.load_visits()
            else:
                QMessageBox.critical(self, "Fail", resp.text)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

# ----------------------------
# MAIN WINDOW
# ----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Integrated PC App with All Data")
        self.setGeometry(50, 50, 1600, 900)
        self.setStyleSheet(load_dark_theme())

        self.init_ui()

    def init_ui(self):
        # 상단 아이콘 메뉴
        self.toolbar = QToolBar("Main Menu")
        self.toolbar.setIconSize(QSize(32,32))
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # 액션들
        action_employee = QAction(QIcon("icons/employee.png"), "직원", self)
        action_client = QAction(QIcon("icons/client.png"), "거래처", self)
        action_brand = QAction(QIcon("icons/brand.png"), "브랜드", self)
        action_product = QAction(QIcon("icons/product.png"), "제품", self)
        action_order = QAction(QIcon("icons/orders.png"), "주문", self)
        action_sales = QAction(QIcon("icons/sales.png"), "매출", self)
        action_empclient = QAction(QIcon("icons/empclient.png"), "직원-거래처", self)
        action_vehicle = QAction(QIcon("icons/vehicle.png"), "차량", self)
        action_visit = QAction(QIcon("icons/visit.png"), "거래처방문", self)

        self.toolbar.addAction(action_employee)
        self.toolbar.addAction(action_client)
        self.toolbar.addAction(action_brand)
        self.toolbar.addAction(action_product)
        self.toolbar.addAction(action_order)
        self.toolbar.addAction(action_sales)
        self.toolbar.addAction(action_empclient)
        self.toolbar.addAction(action_vehicle)
        self.toolbar.addAction(action_visit)

        # 스택
        self.stacked = QStackedWidget()
        self.setCentralWidget(self.stacked)

        # 탭들
        self.emp_tab = EmployeeTab()
        self.client_tab = ClientTab()
        self.brand_tab = BrandTab()
        self.product_tab = ProductTab()
        self.order_tab = OrderTab()
        self.sales_tab = SalesTab()
        self.empclient_tab = EmployeeClientTab()
        self.vehicle_tab = VehicleTab()
        self.visit_tab = ClientVisitTab()

        self.stacked.addWidget(self.emp_tab)       # idx 0
        self.stacked.addWidget(self.client_tab)    # idx 1
        self.stacked.addWidget(self.brand_tab)     # idx 2
        self.stacked.addWidget(self.product_tab)   # idx 3
        self.stacked.addWidget(self.order_tab)     # idx 4
        self.stacked.addWidget(self.sales_tab)     # idx 5
        self.stacked.addWidget(self.empclient_tab) # idx 6
        self.stacked.addWidget(self.vehicle_tab)   # idx 7
        self.stacked.addWidget(self.visit_tab)     # idx 8

        # 액션 연결
        action_employee.triggered.connect(lambda: self.show_tab(0))
        action_client.triggered.connect(lambda: self.show_tab(1))
        action_brand.triggered.connect(lambda: self.show_tab(2))
        action_product.triggered.connect(lambda: self.show_tab(3))
        action_order.triggered.connect(lambda: self.show_tab(4))
        action_sales.triggered.connect(lambda: self.show_tab(5))
        action_empclient.triggered.connect(lambda: self.show_tab(6))
        action_vehicle.triggered.connect(lambda: self.show_tab(7))
        action_visit.triggered.connect(lambda: self.show_tab(8))

        self.show_tab(0)

    def show_tab(self, idx):
        self.stacked.setCurrentIndex(idx)

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


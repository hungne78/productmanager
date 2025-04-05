import sys
import os
import requests

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QPushButton,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QGroupBox, QHeaderView, QStackedWidget, QMessageBox, QFormLayout, QDialog,
    QInputDialog
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

##############################################################################
# 다크테마 (sales.py 예시를 참조하여 작성)
##############################################################################
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

##############################################################################
# 서버 연동 설정 (실제로는 FastAPI + test.db 등)
##############################################################################
BASE_URL = "http://127.0.0.1:8000"

# ---------------------
# 예시 API 함수들 (등록/수정 포함)
# ---------------------
def api_fetch_employees(name_keyword=""):
    """
    직원 목록 GET /employees
    """
    url = f"{BASE_URL}/employees"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        employees = resp.json()
        if name_keyword:
            employees = [e for e in employees if name_keyword in e["name"]]
        return employees
    except Exception as e:
        print("api_fetch_employees error:", e)
        return []

def api_create_employee(data):
    """
    신규 직원 등록 (예시)
    """
    url = f"{BASE_URL}/employees"
    try:
        resp = requests.post(url, json=data)
        return resp
    except Exception as e:
        print("api_create_employee error:", e)
        return None

def api_update_employee(emp_id, data):
    """
    직원 수정 (예시)
    """
    url = f"{BASE_URL}/employees/{emp_id}"
    try:
        resp = requests.put(url, json=data)
        return resp
    except Exception as e:
        print("api_update_employee error:", e)
        return None

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

def api_fetch_clients(name_keyword=""):
    url = f"{BASE_URL}/clients"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        clients = resp.json()
        if name_keyword:
            clients = [c for c in clients if name_keyword in c["client_name"]]
        return clients
    except Exception as e:
        print("api_fetch_clients error:", e)
        return []

def api_create_client(data):
    url = f"{BASE_URL}/clients"
    try:
        resp = requests.post(url, json=data)
        return resp
    except Exception as e:
        print("api_create_client error:", e)
        return None

def api_update_client(client_id, data):
    url = f"{BASE_URL}/clients/{client_id}"
    try:
        resp = requests.put(url, json=data)
        return resp
    except Exception as e:
        print("api_update_client error:", e)
        return None

def api_fetch_products(name_keyword=""):
    url = f"{BASE_URL}/products"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        products = resp.json()
        if name_keyword:
            products = [p for p in products if name_keyword in p["product_name"]]
        return products
    except Exception as e:
        print("api_fetch_products error:", e)
        return []

def api_create_product(data):
    url = f"{BASE_URL}/products"
    try:
        resp = requests.post(url, json=data)
        return resp
    except Exception as e:
        print("api_create_product error:", e)
        return None

def api_update_product(prod_id, data):
    url = f"{BASE_URL}/products/{prod_id}"
    try:
        resp = requests.put(url, json=data)
        return resp
    except Exception as e:
        print("api_update_product error:", e)
        return None

def api_fetch_orders_by_date(date_keyword=""):
    url = f"{BASE_URL}/orders"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        orders = resp.json()
        if date_keyword:
            orders = [o for o in orders if date_keyword in str(o.get("order_date",""))]
        return orders
    except Exception as e:
        print("api_fetch_orders_by_date error:", e)
        return []

def api_create_order(data):
    url = f"{BASE_URL}/orders"
    try:
        resp = requests.post(url, json=data)
        return resp
    except Exception as e:
        print("api_create_order error:", e)
        return None

def api_update_order(order_id, data):
    url = f"{BASE_URL}/orders/{order_id}"
    try:
        resp = requests.put(url, json=data)
        return resp
    except Exception as e:
        print("api_update_order error:", e)
        return None

def api_fetch_sales_by_date(date_keyword=""):
    url = f"{BASE_URL}/sales"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        sales = resp.json()
        if date_keyword:
            sales = [s for s in sales if date_keyword in str(s.get("sale_date",""))]
        return sales
    except Exception as e:
        print("api_fetch_sales_by_date error:", e)
        return []

def api_create_sales(data):
    url = f"{BASE_URL}/sales"
    try:
        resp = requests.post(url, json=data)
        return resp
    except Exception as e:
        print("api_create_sales error:", e)
        return None

def api_update_sales(sales_id, data):
    # 예시. 실제로는 /sales/{id} 등에 PUT
    pass


##############################################################################
# 오른쪽 4개 영역(세로배치), 세 번째 일별 부분은 2줄로(2개 테이블)
##############################################################################
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

##############################################################################
# 왼쪽 정보창도 표 형태로 만들고, 아래 "신규등록", "수정" 버튼
##############################################################################
class BaseLeftTableWidget(QWidget):
    """
    공통 부모클래스처럼 써서, '표 + 버튼' 구조만 잡고
    실제 필드(행 갯수)는 상속해서 구성
    """
    def __init__(self, row_count, labels, parent=None):
        super().__init__(parent)
        self.row_count = row_count
        self.labels = labels  # ["ID","Name", ...]
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # 표
        self.table_info = QTableWidget(self.row_count, 2)
        self.table_info.setHorizontalHeaderLabels(["항목", "값"])
        self.table_info.verticalHeader().setVisible(False)
        self.table_info.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_info.setEditTriggers(QTableWidget.DoubleClicked)  # 더블클릭 편집
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
        return self.table_info.item(row,1).text()

    def set_value(self, row, text):
        self.table_info.setItem(row, 1, QTableWidgetItem(text))

##############################################################################
# 1) 직원관리 LeftWidget
##############################################################################
class EmployeeLeftWidget(BaseLeftTableWidget):
    def __init__(self, parent=None):
        labels = [
            "직원ID", "이름", "전화번호", "직책",
            "차량_주유비", "차량_주행거리", "엔진오일교체일"
        ]
        super().__init__(row_count=len(labels), labels=labels, parent=parent)

        self.btn_new.clicked.connect(self.create_employee)
        self.btn_edit.clicked.connect(self.update_employee)

    def display_employee(self, employee):
        """
        employee + vehicle
        """
        if not employee:
            for r in range(self.row_count):
                self.set_value(r, "")
            return

        emp_id = str(employee.get("id",""))
        self.set_value(0, emp_id)
        self.set_value(1, employee.get("name",""))
        self.set_value(2, employee.get("phone",""))
        self.set_value(3, employee.get("role",""))

        # 차량정보
        veh = api_fetch_employee_vehicle_info(employee["id"])
        if veh:
            self.set_value(4, str(veh.get("monthly_fuel_cost","")))
            self.set_value(5, str(veh.get("current_mileage","")))
            self.set_value(6, str(veh.get("last_engine_oil_change","")))
        else:
            self.set_value(4, "")
            self.set_value(5, "")
            self.set_value(6, "")

    def create_employee(self):
        """
        신규등록 버튼 클릭 → 테이블의 값 읽어서 POST 전송 (간단 예시)
        """
        data = {
            "password": "1234",  # 실제로는 따로 받아야 하지만 예시
            "name": self.get_value(1),
            "phone": self.get_value(2),
            "role": self.get_value(3),
        }
        resp = api_create_employee(data)
        if resp and resp.status_code in (200,201):
            QMessageBox.information(self, "성공", "직원 등록 완료")
        else:
            QMessageBox.critical(self, "실패", f"직원 등록 실패: {resp.status_code if resp else 'None'}")

    def update_employee(self):
        """
        수정 버튼 클릭 → PUT /employees/{id}
        """
        emp_id = self.get_value(0)
        if not emp_id:
            QMessageBox.warning(self, "주의", "수정할 직원 ID가 없습니다.")
            return
        data = {
            "password": "1234",  # 예시
            "name": self.get_value(1),
            "phone": self.get_value(2),
            "role": self.get_value(3),
        }
        resp = api_update_employee(emp_id, data)
        if resp and resp.status_code == 200:
            QMessageBox.information(self, "성공", "직원 수정 완료")
        else:
            QMessageBox.critical(self, "실패", f"직원 수정 실패: {resp.status_code if resp else 'None'}")


class EmployeePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout()

        # 왼쪽(1) : 오른쪽(10)
        self.left_widget = EmployeeLeftWidget()
        main_layout.addWidget(self.left_widget, 1)

        self.right_four = RightFourBoxWidget()
        main_layout.addWidget(self.right_four, 10)

        self.setLayout(main_layout)

    def do_search(self, keyword):
        employees = api_fetch_employees(keyword)
        if employees:
            self.left_widget.display_employee(employees[0])
        else:
            self.left_widget.display_employee(None)
        self.right_four.update_data_example()

##############################################################################
# 2) 거래처관리 LeftWidget
##############################################################################
class ClientLeftWidget(BaseLeftTableWidget):
    def __init__(self, parent=None):
        labels = ["거래처ID","거래처명","주소","전화","미수금"]
        super().__init__(row_count=len(labels), labels=labels, parent=parent)

        self.btn_new.clicked.connect(self.create_client)
        self.btn_edit.clicked.connect(self.update_client)

    def display_client(self, client):
        if not client:
            for r in range(self.row_count):
                self.set_value(r, "")
            return
        self.set_value(0, str(client.get("id","")))
        self.set_value(1, client.get("client_name",""))
        self.set_value(2, client.get("address",""))
        self.set_value(3, client.get("phone",""))
        self.set_value(4, str(client.get("outstanding_amount","")))

    def create_client(self):
        data = {
            "client_name": self.get_value(1),
            "address": self.get_value(2),
            "phone": self.get_value(3),
            "outstanding_amount": float(self.get_value(4) or 0)
        }
        resp = api_create_client(data)
        if resp and resp.status_code in (200,201):
            QMessageBox.information(self, "성공", "거래처 등록 완료")
        else:
            QMessageBox.critical(self, "실패", f"거래처 등록 실패: {resp.status_code if resp else 'None'}")

    def update_client(self):
        client_id = self.get_value(0)
        if not client_id:
            QMessageBox.warning(self, "주의", "수정할 거래처 ID 없음")
            return
        data = {
            "client_name": self.get_value(1),
            "address": self.get_value(2),
            "phone": self.get_value(3),
            "outstanding_amount": float(self.get_value(4) or 0)
        }
        resp = api_update_client(client_id, data)
        if resp and resp.status_code == 200:
            QMessageBox.information(self, "성공", "거래처 수정 완료")
        else:
            QMessageBox.critical(self, "실패", f"거래처 수정 실패: {resp.status_code if resp else 'None'}")

class ClientPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout()
        self.left_widget = ClientLeftWidget()
        main_layout.addWidget(self.left_widget, 1)

        self.right_four = RightFourBoxWidget()
        main_layout.addWidget(self.right_four, 10)

        self.setLayout(main_layout)

    def do_search(self, keyword):
        clients = api_fetch_clients(keyword)
        if clients:
            self.left_widget.display_client(clients[0])
        else:
            self.left_widget.display_client(None)
        self.right_four.update_data_example()

##############################################################################
# 3) 제품관리 LeftWidget
##############################################################################
class ProductLeftWidget(BaseLeftTableWidget):
    def __init__(self, parent=None):
        labels = ["제품ID","제품명","바코드","가격","재고"]
        super().__init__(row_count=len(labels), labels=labels, parent=parent)

        self.btn_new.clicked.connect(self.create_product)
        self.btn_edit.clicked.connect(self.update_product)

    def display_product(self, product):
        if not product:
            for r in range(self.row_count):
                self.set_value(r, "")
            return
        self.set_value(0, str(product.get("id","")))
        self.set_value(1, product.get("product_name",""))
        self.set_value(2, product.get("barcode",""))
        self.set_value(3, str(product.get("default_price","")))
        self.set_value(4, str(product.get("stock","")))

    def create_product(self):
        data = {
            "brand_id": 1,  # 예시
            "product_name": self.get_value(1),
            "barcode": self.get_value(2),
            "default_price": float(self.get_value(3) or 0),
            "stock": int(self.get_value(4) or 0)
        }
        resp = api_create_product(data)
        if resp and resp.status_code in (200,201):
            QMessageBox.information(self, "성공", "제품 등록 완료")
        else:
            QMessageBox.critical(self, "실패", f"제품 등록 실패: {resp.status_code if resp else 'None'}")

    def update_product(self):
        prod_id = self.get_value(0)
        if not prod_id:
            QMessageBox.warning(self, "주의", "수정할 제품 ID 없음")
            return
        data = {
            "brand_id": 1,  # 예시
            "product_name": self.get_value(1),
            "barcode": self.get_value(2),
            "default_price": float(self.get_value(3) or 0),
            "stock": int(self.get_value(4) or 0)
        }
        resp = api_update_product(prod_id, data)
        if resp and resp.status_code == 200:
            QMessageBox.information(self, "성공", "제품 수정 완료")
        else:
            QMessageBox.critical(self, "실패", f"제품 수정 실패: {resp.status_code if resp else 'None'}")

class ProductPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout()
        self.left_widget = ProductLeftWidget()
        main_layout.addWidget(self.left_widget, 1)

        self.right_four = RightFourBoxWidget()
        main_layout.addWidget(self.right_four, 10)
        self.setLayout(main_layout)

    def do_search(self, keyword):
        products = api_fetch_products(keyword)
        if products:
            self.left_widget.display_product(products[0])
        else:
            self.left_widget.display_product(None)
        self.right_four.update_data_example()

##############################################################################
# 4) 주문관리 LeftWidget
##############################################################################
class OrderLeftWidget(BaseLeftTableWidget):
    def __init__(self, parent=None):
        labels = ["주문ID","거래처ID","직원ID","총액","상태","주문일자"]
        super().__init__(len(labels), labels=labels, parent=parent)

        self.btn_new.clicked.connect(self.create_order)
        self.btn_edit.clicked.connect(self.update_order)

    def display_order(self, order):
        if not order:
            for r in range(self.row_count):
                self.set_value(r, "")
            return
        self.set_value(0, str(order.get("id","")))
        self.set_value(1, str(order.get("client_id","")))
        self.set_value(2, str(order.get("employee_id","")))
        self.set_value(3, str(order.get("total_amount","")))
        self.set_value(4, order.get("status",""))
        self.set_value(5, str(order.get("order_date","")))

    def create_order(self):
        data = {
            "client_id": int(self.get_value(1) or 0),
            "employee_id": int(self.get_value(2) or 0),
            "items": [],
            "status": self.get_value(4)
        }
        resp = api_create_order(data)
        if resp and resp.status_code in (200,201):
            QMessageBox.information(self, "성공", "주문 등록 완료")
        else:
            QMessageBox.critical(self, "실패", f"주문 등록 실패: {resp.status_code if resp else 'None'}")

    def update_order(self):
        order_id = self.get_value(0)
        if not order_id:
            QMessageBox.warning(self, "주의", "수정할 주문 ID 없음")
            return
        data = {
            "client_id": int(self.get_value(1) or 0),
            "employee_id": int(self.get_value(2) or 0),
            "status": self.get_value(4),
            "items": []
        }
        resp = api_update_order(order_id, data)
        if resp and resp.status_code == 200:
            QMessageBox.information(self, "성공", "주문 수정 완료")
        else:
            QMessageBox.critical(self, "실패", f"주문 수정 실패: {resp.status_code if resp else 'None'}")

class OrderPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout()
        self.left_widget = OrderLeftWidget()
        main_layout.addWidget(self.left_widget, 1)

        self.right_four = RightFourBoxWidget()
        main_layout.addWidget(self.right_four, 10)
        self.setLayout(main_layout)

    def do_search(self, date_keyword):
        orders = api_fetch_orders_by_date(date_keyword)
        if orders:
            self.left_widget.display_order(orders[0])
        else:
            self.left_widget.display_order(None)
        self.right_four.update_data_example()

##############################################################################
# 5) 매출관리 LeftWidget
##############################################################################
class SalesLeftWidget(BaseLeftTableWidget):
    def __init__(self, parent=None):
        labels = ["매출ID","거래처ID","제품ID","수량","매출일자"]
        super().__init__(len(labels), labels=labels, parent=parent)

        self.btn_new.clicked.connect(self.create_sales)
        self.btn_edit.clicked.connect(self.update_sales)

    def display_sales(self, sales_record):
        if not sales_record:
            for r in range(self.row_count):
                self.set_value(r, "")
            return
        # 예시로 id, client_id, product_id, quantity, sale_date
        self.set_value(0, str(sales_record.get("id","")))
        self.set_value(1, str(sales_record.get("client_id","")))
        self.set_value(2, str(sales_record.get("product_id","")))
        self.set_value(3, str(sales_record.get("quantity","")))
        self.set_value(4, str(sales_record.get("sale_date","")))

    def create_sales(self):
        data = {
            "client_id": int(self.get_value(1) or 0),
            "product_id": int(self.get_value(2) or 0),
            "quantity": int(self.get_value(3) or 0),
            "sale_date": self.get_value(4)
        }
        resp = api_create_sales(data)
        if resp and resp.status_code in (200,201):
            QMessageBox.information(self, "성공", "매출 등록 완료")
        else:
            QMessageBox.critical(self, "실패", f"매출 등록 실패: {resp.status_code if resp else 'None'}")

    def update_sales(self):
        sales_id = self.get_value(0)
        if not sales_id:
            QMessageBox.warning(self, "주의", "수정할 매출 ID 없음")
            return
        # 실제로는 /sales/{sales_id}에 PUT 등이 필요
        QMessageBox.information(self, "미구현", "매출 수정 로직은 예시로 생략했습니다.")


class SalesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout()
        self.left_widget = SalesLeftWidget()
        main_layout.addWidget(self.left_widget, 1)

        self.right_four = RightFourBoxWidget()
        main_layout.addWidget(self.right_four, 10)
        self.setLayout(main_layout)

    def do_search(self, date_keyword):
        sales = api_fetch_sales_by_date(date_keyword)
        if sales:
            self.left_widget.display_sales(sales[0])
        else:
            self.left_widget.display_sales(None)
        self.right_four.update_data_example()

##############################################################################
# 대쉬보드 (옵션)
##############################################################################
class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        label = QLabel("대쉬보드 페이지(예시)")
        layout.addWidget(label)
        self.setLayout(layout)

    def do_search(self, keyword):
        pass

##############################################################################
# 메인 윈도우
##############################################################################
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("업무 관리 시스템 - 수정된 레이아웃")
        self.setGeometry(100, 100, 1600, 900)

        # 다크테마 적용
        self.setStyleSheet(load_dark_theme())

        self.init_ui()

    def init_ui(self):
        # --- 상단 아이콘 메뉴 툴바 ---
        self.menu_toolbar = QToolBar("메인 메뉴")
        self.menu_toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(Qt.TopToolBarArea, self.menu_toolbar)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_dashboard = QIcon(os.path.join(current_dir, "icons", "dashboard.png"))
        icon_employee = QIcon(os.path.join(current_dir, "icons", "employee.png"))
        icon_client = QIcon(os.path.join(current_dir, "icons", "client.png"))
        icon_product = QIcon(os.path.join(current_dir, "icons", "product.png"))
        icon_order = QIcon(os.path.join(current_dir, "icons", "orders.png"))
        icon_sales = QIcon(os.path.join(current_dir, "icons", "sales.png"))

        self.action_dashboard = QAction(icon_dashboard, "대쉬보드", self)
        self.action_employee = QAction(icon_employee, "직원관리", self)
        self.action_client = QAction(icon_client, "거래처관리", self)
        self.action_product = QAction(icon_product, "제품관리", self)
        self.action_order = QAction(icon_order, "주문관리", self)
        self.action_sales = QAction(icon_sales, "매출관리", self)

        self.menu_toolbar.addAction(self.action_dashboard)
        self.menu_toolbar.addAction(self.action_employee)
        self.menu_toolbar.addAction(self.action_client)
        self.menu_toolbar.addAction(self.action_product)
        self.menu_toolbar.addAction(self.action_order)
        self.menu_toolbar.addAction(self.action_sales)

        # --- 검색창 툴바 (메뉴 아래) ---
        self.search_toolbar = QToolBar("검색창")
        self.search_toolbar.setIconSize(QSize(16,16))
        self.addToolBar(Qt.TopToolBarArea, self.search_toolbar)

        self.search_label = QLabel("검색:")
        self.search_edit = QLineEdit()
        self.search_button = QPushButton("검색")

        self.search_toolbar.addWidget(self.search_label)
        self.search_toolbar.addWidget(self.search_edit)
        self.search_toolbar.addWidget(self.search_button)

        # --- 메인 스택 ---
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 페이지들
        self.dashboard_page = DashboardPage()
        self.employee_page = EmployeePage()
        self.client_page = ClientPage()
        self.product_page = ProductPage()
        self.order_page = OrderPage()
        self.sales_page = SalesPage()

        self.stacked_widget.addWidget(self.dashboard_page)  # idx 0
        self.stacked_widget.addWidget(self.employee_page)   # idx 1
        self.stacked_widget.addWidget(self.client_page)     # idx 2
        self.stacked_widget.addWidget(self.product_page)    # idx 3
        self.stacked_widget.addWidget(self.order_page)      # idx 4
        self.stacked_widget.addWidget(self.sales_page)      # idx 5

        # 액션 연결
        self.action_dashboard.triggered.connect(lambda: self.switch_page(0))
        self.action_employee.triggered.connect(lambda: self.switch_page(1))
        self.action_client.triggered.connect(lambda: self.switch_page(2))
        self.action_product.triggered.connect(lambda: self.switch_page(3))
        self.action_order.triggered.connect(lambda: self.switch_page(4))
        self.action_sales.triggered.connect(lambda: self.switch_page(5))

        self.search_button.clicked.connect(self.on_search_clicked)

        # 초기 페이지 대쉬보드
        self.switch_page(0)

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        # 검색창 Placeholder
        if index == 0:
            self.search_edit.setPlaceholderText("대쉬보드 검색X")
        elif index == 1:
            self.search_edit.setPlaceholderText("직원 이름 검색")
        elif index == 2:
            self.search_edit.setPlaceholderText("거래처 이름 검색")
        elif index == 3:
            self.search_edit.setPlaceholderText("제품명 검색")
        elif index == 4:
            self.search_edit.setPlaceholderText("주문 날짜(YYYY-MM-DD)")
        elif index == 5:
            self.search_edit.setPlaceholderText("매출 날짜(YYYY-MM-DD)")

    def on_search_clicked(self):
        keyword = self.search_edit.text().strip()
        idx = self.stacked_widget.currentIndex()
        if idx == 0:
            self.dashboard_page.do_search(keyword)
        elif idx == 1:
            self.employee_page.do_search(keyword)
        elif idx == 2:
            self.client_page.do_search(keyword)
        elif idx == 3:
            self.product_page.do_search(keyword)
        elif idx == 4:
            self.order_page.do_search(keyword)
        elif idx == 5:
            self.sales_page.do_search(keyword)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

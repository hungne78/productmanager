import sys
import os

# 프로젝트 루트 경로를 모듈 검색 경로에 추가
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QMainWindow, QToolBar, QAction, QStackedWidget, QLineEdit, QPushButton, QLabel
from employee_ui import EmployeesTab
from clients_ui import ClientsTab
from products_ui import ProductsTab
from orders_ui import OrdersTab
from purchase_ui import PurchaseTab
from employee_map_ui import EmployeeMapTab
from sales_ui import SalesTab
from PyQt5.QtCore import Qt
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


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wholesale Management System")
        self.setGeometry(100, 100, 1980, 1080)
        self.setStyleSheet(load_dark_theme())

        self.toolbar = self.addToolBar("Main Toolbar")
        self.toolbar_icons = [
            ("직원", "icons/employee.png", self.show_employees_tab),
            ("거래처", "icons/client.png", self.show_clients_tab),
            ("제품", "icons/product.png", self.show_products_tab),
            ("주문", "icons/order.png", self.show_orders_tab),
            ("매입", "icons/purchase.png", self.show_purchase_tab),
            ("직원 지도", "icons/map.png", self.show_employee_map_tab),
            ("총매출", "icon/sales.png", self.show_sales_tab)
        ]

        for name, icon_path, handler in self.toolbar_icons:
            action = QAction(name, self)
            action.triggered.connect(handler)
            self.toolbar.addAction(action)

        self.search_toolbar = QToolBar("검색창")
        self.addToolBar(self.search_toolbar)
        self.addToolBar(Qt.TopToolBarArea, self.search_toolbar)

        self.search_label = QLabel("검색:")
        self.search_edit = QLineEdit()
        self.search_button = QPushButton("검색")

        self.search_toolbar.addWidget(self.search_label)
        self.search_toolbar.addWidget(self.search_edit)
        self.search_toolbar.addWidget(self.search_button)

        self.search_button.clicked.connect(self.on_search_clicked)
        self.search_edit.returnPressed.connect(self.on_search_clicked)

        self.stacked = QStackedWidget()
        self.setCentralWidget(self.stacked)

        self.tabs = {
            "employees": EmployeesTab(),
            "clients": ClientsTab(),
            "products": ProductsTab(),
            "orders": OrdersTab(),
            "purchase": PurchaseTab(),
            "employee_map": EmployeeMapTab(),
            "sales": SalesTab()
        }

        for tab in self.tabs.values():
            self.stacked.addWidget(tab)

        self.stacked.setCurrentWidget(self.tabs["employees"])
        self.update_search_placeholder("employees")

    def show_employees_tab(self):
        self.stacked.setCurrentWidget(self.tabs["employees"])
        self.update_search_placeholder("employees")

    def show_clients_tab(self):
        self.stacked.setCurrentWidget(self.tabs["clients"])
        self.update_search_placeholder("clients")

    def show_products_tab(self):
        self.stacked.setCurrentWidget(self.tabs["products"])
        self.update_search_placeholder("products")

    def show_orders_tab(self):
        self.stacked.setCurrentWidget(self.tabs["orders"])
        self.update_search_placeholder("orders")

    def show_purchase_tab(self):
        self.stacked.setCurrentWidget(self.tabs["purchase"])
        self.update_search_placeholder("purchase")

    def show_employee_map_tab(self):
        self.stacked.setCurrentWidget(self.tabs["employee_map"])
        self.update_search_placeholder("employee_map")

    def show_sales_tab(self):
        self.stacked.setCurrentWidget(self.tabs["sales"])
        self.update_search_placeholder("sales")
        
    def on_search_clicked(self):
        keyword = self.search_edit.text().strip()
        current_tab = self.stacked.currentWidget()

        if not keyword:
            return

        if isinstance(current_tab, EmployeesTab):
            current_tab.do_search(keyword)
        elif isinstance(current_tab, ClientsTab):
            current_tab.do_search(keyword)
        elif isinstance(current_tab, ProductsTab):
            current_tab.do_search(keyword)
        elif isinstance(current_tab, OrdersTab):
            current_tab.do_search(keyword)
        elif isinstance(current_tab, PurchaseTab):
            current_tab.do_search(keyword)
        elif isinstance(current_tab, EmployeeMapTab):
            current_tab.do_search(keyword)
        elif isinstance(current_tab, SalesTab):
            current_tab.do_search(keyword)
            
    def update_search_placeholder(self, tab_name):
        placeholders = {
            "employees": "직원이름 검색",
            "clients": "거래처명 검색",
            "products": "제품명 검색",
            "orders": "주문 검색 (ex: 날짜)",
            "purchase": "매입 검색 (ex: 거래처명, 제품명)",
            "employee_map": "직원 ID 입력",
            "sales": "매출날짜입력"
        }
        self.search_edit.setPlaceholderText(placeholders.get(tab_name, "검색"))

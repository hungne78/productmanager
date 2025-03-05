import sys
import os

# 프로젝트 루트 경로를 모듈 검색 경로에 추가
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QMainWindow, QToolBar, QAction, QStackedWidget, QLineEdit, QPushButton, QLabel, QWidget, QHBoxLayout, QMenuBar, QMenu, QAction, QDialog, QFormLayout,QLineEdit, QDialogButtonBox
from employee_ui import EmployeesTab
from clients_ui import ClientsTab
from products_ui import ProductsTab
from orders_ui import OrdersTab
from purchase_ui import PurchaseTab
from employee_map_ui import EmployeeMapTab
from sales_ui import SalesTab
from payments_ui import PaymentsTab
from invoices_ui import InvoicesTab
from employee_sales_ui import EmployeeSalesTab
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
import json
from PyQt5.QtGui import QIcon
from pathlib import Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 스크립트 파일의 절대 경로
ICONS_DIR = os.path.join(BASE_DIR, "assets/icons")  # icons 폴더 경로 설정
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
class CompanyInfoDialog(QDialog):
    """
    우리 회사 정보(상호, 대표자, 사업자번호 등)를 입력받는 다이얼로그
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("회사 정보 등록/수정")
        self.company_name_edit = QLineEdit()
        self.ceo_edit = QLineEdit()
        self.business_num_edit = QLineEdit()
        self.address_edit = QLineEdit()

        layout = QFormLayout()
        layout.addRow("회사명:", self.company_name_edit)
        layout.addRow("대표자명:", self.ceo_edit)
        layout.addRow("사업자번호:", self.business_num_edit)
        layout.addRow("주소:", self.address_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.setLayout(layout)

    def get_company_info(self):
        return {
            "company_name": self.company_name_edit.text(),
            "ceo": self.ceo_edit.text(),
            "business_number": self.business_num_edit.text(),
            "address": self.address_edit.text(),
        }

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wholesale Management System")
        self.setGeometry(100, 100, 1980, 1080)
        self.setStyleSheet(load_dark_theme())
        self.company_info = self.load_company_info()
        if self.company_info:
            print("▶ 프로그램 시작 시 회사 정보 로드:", self.company_info)
        else:
            print("▶ 회사 정보 파일이 없거나 비어 있습니다.")
                
        self.toolbar = self.addToolBar("Main Toolbar")
        self.toolbar_icons = [
            ("직원관리", os.path.join(ICONS_DIR, "employee.png"), self.show_employees_tab),
            ("거래처관리", os.path.join(ICONS_DIR, "client.png"), self.show_clients_tab),
            ("제품관리", os.path.join(ICONS_DIR, "product.png"), self.show_products_tab),
            ("주문관리", os.path.join(ICONS_DIR, "order.png"), self.show_orders_tab),
            ("매입관리", os.path.join(ICONS_DIR, "purchase.png"), self.show_purchase_tab),
            ("직원 지도", os.path.join(ICONS_DIR, "map.png"), self.show_employee_map_tab),
            ("총매출", os.path.join(ICONS_DIR, "sales.png"), self.show_sales_tab),
            ("방문주기", os.path.join(ICONS_DIR, "sales.png"), self.show_employee_sales_tab),
            ("월급여", os.path.join(ICONS_DIR, "payments.png"), self.show_payments_tab),
            ("세금계산서", os.path.join(ICONS_DIR, "invoices.png"), self.show_invoices_tab)
        ]

        # 툴바 스타일 설정 추가
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # ✅ 아이콘 아래 텍스트 표시

        for name, icon_path, handler in self.toolbar_icons:
            if os.path.exists(icon_path):  # 아이콘 파일이 존재하는지 확인
                action = QAction(QIcon(icon_path), name, self)  # ✅ 아이콘과 텍스트 함께 추가
            else:
                print(f"⚠️ 아이콘 파일 없음: {icon_path}")
                action = QAction(name, self)  # 아이콘 없이 액션 추가
            
            action.triggered.connect(handler)
            self.toolbar.addAction(action)

        self.search_toolbar = QToolBar("검색창")
        self.addToolBar(self.search_toolbar)
        self.addToolBar(Qt.TopToolBarArea, self.search_toolbar)

        self.search_label = QLabel("검색:")
        self.search_edit = QLineEdit()
        self.search_button = QPushButton("검색")
        # ✅ 검색창 크기 조정
        self.search_edit.setFixedWidth(250)

        # ✅ 가로 레이아웃 생성 (오른쪽 정렬)
        search_layout = QHBoxLayout()
        search_layout.addStretch(1)  # 왼쪽 빈 공간 추가
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.search_button)

        # ✅ 빈 위젯을 만들어 툴바에 추가
        search_widget = QWidget()
        search_widget.setLayout(search_layout)
        self.search_toolbar.addWidget(search_widget)

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
            "sales": SalesTab(),
            "employee_sales" : EmployeeSalesTab(),
            "payments": PaymentsTab(),
            "invoices": InvoicesTab()
        }
        
        self.tabs["invoices"].right_panel.set_company_info(self.company_info)
        for tab in self.tabs.values():
            self.stacked.addWidget(tab)

        self.stacked.setCurrentWidget(self.tabs["employees"])
        self.update_search_placeholder("employees")
        self.company_info = {}  # 우리 회사 정보 저장할 dict

        # ── 메뉴바 생성 ─────────────────
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("설정(&S)")

        register_action = QAction("회사 정보 등록", self)
        register_action.triggered.connect(self.open_company_info_dialog)
        settings_menu.addAction(register_action)
        
        
    def open_company_info_dialog(self):
        dialog = CompanyInfoDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            info = dialog.get_company_info()
            self.company_info = info
            print("▶ 우리 회사 정보 등록 완료:", self.company_info)
            self.save_company_info(self.company_info, "company_info.json")
            # 혹시 우측 패널에 바로 반영하고 싶다면:
            self.tabs["invoices"].right_panel.set_company_info(self.company_info)
    
    def save_company_info(self, info: dict, filename="company_info.json"):
        """
        회사 정보를 JSON 파일로 저장
        """
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
            print(f"회사 정보가 '{filename}'에 저장되었습니다.")
        except Exception as e:
            print(f"회사 정보 저장 실패: {e}")
        
    def load_company_info(self, filename="company_info.json") -> dict:
        """
        JSON 파일에서 회사 정보를 로드 (없으면 빈 딕셔너리 반환)
        """
        if not os.path.exists(filename):
            return {}
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                else:
                    return {}
        except Exception as e:
            print(f"회사 정보 로드 실패: {e}")
            return {}

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

    def show_employee_sales_tab(self):
        self.stacked.setCurrentWidget(self.tabs["employee_sales"])
        self.update_search_placeholder("employee_sales")
        
    def show_payments_tab(self):
        self.stacked.setCurrentWidget(self.tabs["payments"])
        self.update_search_placeholder("payments")

    def show_invoices_tab(self):
        self.stacked.setCurrentWidget(self.tabs["invoices"])
        self.update_search_placeholder("invoices")
        
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
        elif isinstance(current_tab, EmployeeSalesTab):
            current_tab.do_search(keyword)
        elif isinstance(current_tab, PaymentsTab):
            current_tab.do_search(keyword) 
        elif isinstance(current_tab, InvoicesTab):
            current_tab.do_search(keyword)

    def update_search_placeholder(self, tab_name):
        placeholders = {
            "employees": "직원이름 검색",
            "clients": "거래처명 검색",
            "products": "제품명 검색",
            "orders": "주문 검색 (ex: 날짜)",
            "purchase": "매입 검색 (ex: 거래처명, 제품명)",
            "employee_map": "직원 ID 입력",
            "sales": "매출날짜입력",
            "employee_sales": "직원이름 검색",
            "payments" : "직원이름 검색",
            "invoices" : "거래처명 검색"
        }
        self.search_edit.setPlaceholderText(placeholders.get(tab_name, "검색"))

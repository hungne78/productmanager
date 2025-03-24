import sys
import os

# 프로젝트 루트 경로를 모듈 검색 경로에 추가
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QLineEdit, QStackedWidget, QFrame, QAction, QDialog,
    QFormLayout, QDialogButtonBox, QMenuBar, QMenu\
)
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
from employee_vehicle_inventory_tab import EmployeeVehicleInventoryTab
from PyQt5.QtCore import Qt, QDateTime, QTimer, QPoint
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
import json
from PyQt5.QtGui import QIcon
from pathlib import Path
import requests
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 스크립트 파일의 절대 경로
ICONS_DIR = os.path.join(BASE_DIR, "assets/icons")  # icons 폴더 경로 설정

def load_erp_style():
    return """
    QMainWindow {
        background-color: #f4f6f5;
        font-family: 'Segoe UI', sans-serif;
    }

    #LeftPanel {
        background-color: #1e3932;
    }

    #LeftPanelButton {
        background-color: transparent;
        color: white;
        font-size: 15px;
        padding: 12px 20px;
        border: none;
        text-align: left;
    }

    #LeftPanelButton:hover {
        background-color: #274c41;
    }

    #InfoPanel {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 8px;
    }

    #ContentPanel {
        background-color: #ffffff;
        border: 1px solid #dddddd;
        border-radius: 6px;
        padding: 12px;
    }

    QTableWidget {
        border: 1px solid #dddddd;
        background-color: #ffffff;
        alternate-background-color: #f9f9f9;
        gridline-color: #e0e0e0;
        font-size: 13px;
        selection-background-color: #cce5ff;
        selection-color: #000000;
    }

    QTableWidget::item {
        padding: 6px;
        height: 32px;
    }

    QHeaderView::section {
        background-color: #f0f0f0;
        padding: 6px;
        font-weight: bold;
        border: 1px solid #d0d0d0;
        font-size: 13px;
    }

    QPushButton {
        background-color: #ffffff;
        border: 1px solid #bbbbbb;
        border-radius: 4px;
        padding: 6px 12px;
    }

    QPushButton:hover {
        background-color: #e8e8e8;
    }

    QLabel {
        color: #333333;
        font-size: 14px;
    }
    """

def load_dark_theme():
    """
    (기존) 다크 테마. user가 제공한 코드 그대로 둠
    """
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

def load_flat_theme():
    """
    1) 라이트 & 플랫 스타일 (미니멀리즘 / Flat Design)
    """
    return """
    QMainWindow {
        background-color: #FAFAFA;
    }
    QToolBar {
        background-color: #FFFFFF;
        border-bottom: 1px solid #E0E0E0;
    }
    QToolBar QToolButton {
        color: #333333;
        font-size: 14px;
    }
    QWidget {
        background-color: #FAFAFA;
        color: #222222;
        font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif;
    }
    QLineEdit {
        border: 1px solid #CCCCCC;
        padding: 5px;
        border-radius: 5px;
        background-color: #FFFFFF;
    }
    QPushButton {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #CCCCCC;
        border-radius: 5px;
        padding: 6px 12px;
    }
    QPushButton:hover {
        background-color: #F5F5F5;
        border: 1px solid #BBBBBB;
    }
    QLabel {
        color: #333333;
        font-size: 14px;
    }
    QTableWidget {
        background-color: #FFFFFF;
        color: #333333;
        gridline-color: #DDDDDD;
    }
    QHeaderView::section {
        background-color: #FAFAFA;
        color: #333333;
        border: 1px solid #E0E0E0;
    }
    QTabWidget::pane {
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        margin-top: -1px;
    }
    QTabBar::tab {
        background: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 8px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    QTabBar::tab:selected,
    QTabBar::tab:hover {
        background: #F5F5F5;
        border-bottom: 1px solid #F5F5F5;
    }
    """

def load_glasslike_theme():
    """
    2) 다크 & 모노톤 스타일 (세미 투명 / 유리 느낌)
    """
    return """
    QMainWindow {
        background-color: #2E2E2E; /* 다크 배경 */
    }
    QToolBar {
        background-color: rgba(50, 50, 50, 0.6); /* 반투명 다크 */
        border: none;
    }
    QToolBar QToolButton {
        color: #EEEEEE;
        font-weight: 500;
        padding: 6px 10px;
    }
    QWidget {
        background-color: rgba(40, 40, 40, 0.4);
        color: #EEEEEE;
        font-family: '나눔고딕', sans-serif;
    }
    QLineEdit {
        background-color: rgba(80, 80, 80, 0.8);
        color: #FFFFFF;
        border: 1px solid #555555;
        border-radius: 4px;
        padding: 4px;
    }
    QPushButton {
        background-color: rgba(100, 100, 100, 0.3);
        color: #FFFFFF;
        border: 1px solid #777777;
        border-radius: 4px;
        padding: 6px 12px;
    }
    QPushButton:hover {
        background-color: rgba(150, 150, 150, 0.3);
        border: 1px solid #BBBBBB;
    }
    QLabel {
        color: #CCCCCC;
        font-size: 14px;
    }
    QTabWidget::pane {
        border: 1px solid rgba(255, 255, 255, 0.2);
        background-color: rgba(40, 40, 40, 0.3);
        border-radius: 4px;
    }
    QTabBar::tab {
        background: rgba(60, 60, 60, 0.4);
        color: #FFFFFF;
        padding: 8px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background: rgba(80, 80, 80, 0.6);
        border-bottom: 1px solid rgba(80, 80, 80, 0.6);
    }
    """

def load_material_theme():
    """
    3) 컬러 포인트 & 머티리얼 느낌
    """
    return """
    QMainWindow {
        background-color: #F2F2F2;
    }
    QToolBar {
        background-color: #FFFFFF;
        border-bottom: 1px solid #DDDDDD;
    }
    QToolBar QToolButton {
        color: #333333;
        font-weight: 500;
        padding: 6px 10px;
    }
    QWidget {
        background-color: #F2F2F2;
        color: #333333;
        font-family: 'Roboto', sans-serif;
    }
    QLineEdit {
        border: 1px solid #CCCCCC;
        border-radius: 4px;
        padding: 6px;
    }
    QPushButton {
        background-color: #4CAF50;
        color: #FFFFFF;
        border: none;
        border-radius: 4px;
        padding: 8px 12px;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: #66BB6A;
    }
    QPushButton:pressed {
        background-color: #388E3C;
    }
    QLabel {
        color: #333333;
        font-size: 14px;
    }
    QTabWidget::pane {
        border: 1px solid #DDDDDD;
        padding: 5px;
    }
    QTabBar::tab {
        background: #FFFFFF;
        color: #333333;
        padding: 8px 14px;
        border: 1px solid #DDDDDD;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-right: 4px;
        font-weight: 500;
    }
    QTabBar::tab:selected {
        background: #4CAF50;
        color: #FFFFFF;
        border-bottom: 2px solid #388E3C;
    }
    """

def load_lightblue_theme():
    return """
QMainWindow {
    background: #f9f9f9;  /* 전체 배경 */
    font-family: 'Segoe UI', sans-serif;
}
QFrame#LeftPanel {
    background-color: #283e5b; /* 좌측 사이드 패널 배경(진한 블루) */
}
QLabel {
    color: #333333;
    font-size: 14px;
}
QLabel#LeftPanelLabel {
    color: white;
    font-weight: bold;
    font-size: 14px;
}
QPushButton#LeftPanelButton {
    background-color: transparent;
    color: #ffffff;
    text-align: left;
    padding: 8px 16px;
    border: none;
}
QPushButton#LeftPanelButton:hover {
    background-color: #3b5172;
}
QLineEdit#SearchEdit {
    background-color: white;
    border-radius: 4px;
    padding: 5px 8px;
    margin: 0px 8px;
}
QPushButton#SearchButton {
    background-color: #4c6d9c;
    color: #ffffff;
    border: none;
    border-radius: 3px;
    padding: 6px 12px;
    margin-right: 8px;
}
QPushButton#SearchButton:hover {
    background-color: #5d7fae;
}
QTabBar {
    background: #2196F3;  /* 상단 탭 바의 파란 배경 */
}
QTabBar::tab {
    background: #2196F3;
    color: white;
    font-weight: 500;
    font-size: 13px;
    padding: 8px 12px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #1976D2; /* 선택된 탭은 좀 더 진한 파랑 */
}
"""

def load_pastel_purple_theme():
    """
    5) 추가된 예시 - 파스텔 퍼플/핑크 계열 테마
    """
    return """
    QMainWindow {
        background-color: #F6F0FA;
    }
    QToolBar {
        background-color: #EDE2F4;
        border: 1px solid #D3C2E5;
    }
    QToolBar QToolButton {
        color: #4B295D;
        font-weight: 500;
        padding: 6px 12px;
    }
    QWidget {
        background-color: #F6F0FA;
        color: #4B295D;
        font-family: 'Malgun Gothic', sans-serif;
    }
    QLineEdit {
        background-color: #FFFFFF;
        color: #4B295D;
        border: 1px solid #D3C2E5;
        padding: 5px;
        border-radius: 4px;
    }
    QPushButton {
        background-color: #DCC6EA;
        color: #4B295D;
        border: 1px solid #C9ACDF;
        border-radius: 4px;
        padding: 6px 12px;
    }
    QPushButton:hover {
        background-color: #C9ACDF;
    }
    QLabel {
        color: #4B295D;
        font-size: 13px;
        font-weight: normal;
    }
    QTableWidget {
        background-color: #FFFFFF;
        color: #4B295D;
        gridline-color: #C9ACDF;
    }
    QHeaderView::section {
        background-color: #EDE2F4;
        color: #4B295D;
        border: 1px solid #C9ACDF;
    }
    """
class CompanyInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("회사 정보 등록/수정")
        self.company_name_edit = QLineEdit()
        self.ceo_edit = QLineEdit()
        self.business_num_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.bank_edit = QLineEdit()

        layout = QFormLayout()
        layout.addRow("회사명:", self.company_name_edit)
        layout.addRow("대표자명:", self.ceo_edit)
        layout.addRow("사업자번호:", self.business_num_edit)
        layout.addRow("주소:", self.address_edit)
        layout.addRow("전화번호:", self.phone_edit)              # ✅ 추가
        layout.addRow("입금 계좌번호:", self.bank_edit)         # ✅ 추가

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.setLayout(layout)

    def get_company_info(self):
        return {
            "company_name": self.company_name_edit.text(),
            "ceo_name": self.ceo_edit.text(),
            "business_number": self.business_num_edit.text(),
            "address": self.address_edit.text(),
            "phone": self.phone_edit.text(),             # ✅ 포함
            "bank_account": self.bank_edit.text(),       # ✅ 포함
        }

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)  # 🔷 제목 표시줄 제거
        self.setGeometry(0, 0, 1900, 1200)
        self.setStyleSheet(load_erp_style())
        self.company_info = self.load_company_info()
        
        self.old_pos = self.pos()  # 드래그 시작 위치 저장용

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)  
        self.setCentralWidget(main_widget)

        # ▶ 커스텀 타이틀 바
        self.header = QFrame()
        self.header.setFixedHeight(42)
        self.header.setStyleSheet("background-color: #2d3147;")

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 0, 10, 0)

        title_label = QLabel("성심유통 ERP")
        title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")

        user_label = QLabel("로그인: 관리자")
        user_label.setStyleSheet("color: white; font-size: 13px;")

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 28)
        close_btn.setStyleSheet(""
            "QPushButton { color: white; background-color: transparent; border: none; }"
            "QPushButton:hover { background-color: #e63946; border-radius: 4px; }"
        )
        close_btn.clicked.connect(self.close)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(user_label)
        header_layout.addSpacing(12)
        header_layout.addWidget(close_btn)

        # ▶ 아래쪽 UI (기존 레이아웃)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # ... 이하 기존 self.left_panel, self.right_panel 설정 유지 ...

        

        
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0) 
        self.setCentralWidget(main_widget)

        # ▶ 좌측 메뉴 패널
        self.left_panel = QFrame()
        self.left_panel.setObjectName("LeftPanel")
        self.left_panel.setFixedWidth(180)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 20, 0, 0)

        # 🔷 상단 로고 텍스트
        title_label = QLabel("성심유통")
        title_label.setObjectName("LeftPanelLabel")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        left_layout.addWidget(title_label)
        left_layout.addSpacing(20)

        self.toolbar_icons = [
            ("직원관리", "employee", self.show_employees_tab),
            ("거래처관리", "client", self.show_clients_tab),
            ("제품관리", "product", self.show_products_tab),
            ("주문관리", "order", self.show_orders_tab),
            ("매입관리", "purchase", self.show_purchase_tab),
            ("직원 지도", "map", self.show_employee_map_tab),
            ("총매출", "sales", self.show_sales_tab),
            ("방문주기", "sales", self.show_employee_sales_tab),
            ("월급여", "payments", self.show_payments_tab),
            ("세금계산서", "invoices", self.show_invoices_tab),
            ("차량재고", "inventory", self.show_inventory_tab)
        ]

        for name, icon, handler in self.toolbar_icons:
            btn = QPushButton(name)
            btn.setObjectName("LeftPanelButton")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(handler)
            left_layout.addWidget(btn)

        left_layout.addStretch()

        # 🔷 검색창 하단 배치
        self.search_label = QLabel("검색:")
        self.search_label.setStyleSheet("color: white; padding-left: 8px;")
        self.search_edit = QLineEdit()
        self.search_button = QPushButton("검색")
        self.custom_button = QPushButton("모든 검색")

        self.search_edit.setPlaceholderText("검색")
        self.search_edit.setFixedWidth(140)
        self.search_button.setFixedWidth(60)
        self.custom_button.setFixedWidth(140)

        left_layout.addWidget(self.search_label)
        left_layout.addWidget(self.search_edit)
        left_layout.addWidget(self.search_button)
        left_layout.addWidget(self.custom_button)

        # ▶ 오른쪽 전체 패널
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(0)

        # 🔷 상단 날짜 및 시간 (디자인 + 업데이트)
        self.datetime_label = QLabel()
        self.datetime_label.setStyleSheet("font-size: 18px; color: #333; font-weight: bold;")
        self.datetime_label.setContentsMargins(0, 0, 0, 0)
        self.update_datetime()
        timer = QTimer(self)
        timer.timeout.connect(self.update_datetime)
        timer.start(1000)  # 매 초마다 업데이트
        right_layout.addWidget(self.datetime_label, alignment=Qt.AlignLeft)

        # ▶ 버튼 영역
        button_row = QHBoxLayout()
        button_row.addStretch()
        for label in ["저장", "조회", "삭제"]:
            btn = QPushButton(label)
            btn.setFixedWidth(80)
            button_row.addWidget(btn)
        right_layout.addLayout(button_row)

        # ▶ 정보 패널
        self.info_panel = QFrame()
        self.info_panel.setObjectName("InfoPanel")
        self.info_panel.setFixedHeight(1)
        right_layout.addWidget(self.info_panel)

        # ▶ 콘텐츠 영역
        self.stacked = QStackedWidget()
        self.stacked.setObjectName("ContentPanel")
        right_layout.addWidget(self.stacked)

        # ▶ 전체 배치
        # ▶ 좌우 본문 UI
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 좌우 패널은 여기에 추가하면 됨
        content_layout.addWidget(self.left_panel)
        content_layout.addWidget(self.right_panel)

        # ▶ 전체 배치
        main_layout.addWidget(self.header)
        main_layout.addWidget(content_widget)

        # ▶ 탭 등록
        self.tabs = {
            "employees": EmployeesTab(),
            "clients": ClientsTab(),
            "products": ProductsTab(),
            "orders": OrdersTab(),
            "purchase": PurchaseTab(),
            "employee_map": EmployeeMapTab(),
            "sales": SalesTab(),
            "employee_sales": EmployeeSalesTab(),
            "payments": PaymentsTab(),
            "invoices": InvoicesTab(),
            "inventory": EmployeeVehicleInventoryTab()
        }

        for tab in self.tabs.values():
            self.stacked.addWidget(tab)

        self.tabs["invoices"].right_panel.set_company_info(self.company_info)

        self.stacked.setCurrentWidget(self.tabs["employees"])
        self.update_search_placeholder("employees")
        self.update_custom_button("employees")

    def update_datetime(self):
        current = QDateTime.currentDateTime()
        self.datetime_label.setText(current.toString("yyyy-MM-dd hh:mm:ss"))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

        
    def update_custom_button(self, tab_name):
        """ 현재 UI에 따라 버튼 기능을 변경 """
        current_tab = self.stacked.currentWidget()  # 현재 선택된 UI 가져오기

        # ✅ 기존 이벤트 해제 (예외 방지)
        try:
            self.custom_button.clicked.disconnect()
        except TypeError:
            pass  # 연결된 슬롯이 없으면 무시

        # ✅ `do_custom_action()`이 존재하면 실행하도록 설정
        if hasattr(current_tab, "do_custom_action"):
            self.custom_button.clicked.connect(current_tab.do_custom_action)
            self.custom_button.setText(f"모든 검색")
        else:
            self.custom_button.setText("기능 없음")
            self.custom_button.clicked.connect(lambda: print("❌ 이 UI에서는 기능이 없습니다."))

                
    def open_company_info_dialog(self):
        dialog = CompanyInfoDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            info = dialog.get_company_info()
            self.company_info = info
            print("▶ 우리 회사 정보 등록 완료:", self.company_info)

            # ✅ 서버에 저장하도록 변경
            self.save_company_info_to_server(self.company_info)

            # ✅ UI 반영 (예: 거래명세서 오른쪽 패널)
            self.tabs["invoices"].right_panel.set_company_info(self.company_info)

    
    def save_company_info_to_server(self, info: dict):
        """
        회사 정보를 FastAPI 서버에 POST로 전송
        """
        try:
            url = "http://localhost:8000/company"  # 서버 주소에 맞게 조정
            response = requests.post(url, json=info)

            if response.status_code in [200, 201]:
                print("✅ 서버에 회사 정보 저장 성공!")
            else:
                print(f"❌ 서버 저장 실패: {response.status_code} / {response.text}")
        except Exception as e:
            print(f"❌ 서버 전송 오류: {e}")
        
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
        self.update_custom_button("employees")

    def show_clients_tab(self):
        self.stacked.setCurrentWidget(self.tabs["clients"])
        self.update_search_placeholder("clients")
        self.update_custom_button("clients")

    def show_products_tab(self):
        self.stacked.setCurrentWidget(self.tabs["products"])
        self.update_search_placeholder("products")
        self.update_custom_button("products")

    def show_orders_tab(self):
        self.stacked.setCurrentWidget(self.tabs["orders"])
        self.update_search_placeholder("orders")
        self.update_custom_button("orders")

    def show_purchase_tab(self):
        self.stacked.setCurrentWidget(self.tabs["purchase"])
        self.update_search_placeholder("purchase")
        self.update_custom_button("purchase")

    def show_employee_map_tab(self):
        self.stacked.setCurrentWidget(self.tabs["employee_map"])
        self.update_search_placeholder("employee_map")
        self.update_custom_button("employee_map")

    def show_sales_tab(self):
        self.stacked.setCurrentWidget(self.tabs["sales"])
        self.update_search_placeholder("sales")
        self.update_custom_button("sales")

    def show_employee_sales_tab(self):
        self.stacked.setCurrentWidget(self.tabs["employee_sales"])
        self.update_search_placeholder("employee_sales")
        self.update_custom_button("employee_sales")

    def show_payments_tab(self):
        self.stacked.setCurrentWidget(self.tabs["payments"])
        self.update_search_placeholder("payments")
        self.update_custom_button("payments")

    def show_invoices_tab(self):
        self.stacked.setCurrentWidget(self.tabs["invoices"])
        self.update_search_placeholder("invoices")
        self.update_custom_button("invoices")

    def show_inventory_tab(self):
        self.stacked.setCurrentWidget(self.tabs["inventory"])
        self.update_search_placeholder("inventory")
        self.update_custom_button("inventory")

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
        elif isinstance(current_tab, EmployeeVehicleInventoryTab):
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
            "invoices" : "거래처명 검색",
            "inventory" : "직원이름 검색"
        }
        self.search_edit.setPlaceholderText(placeholders.get(tab_name, "검색"))

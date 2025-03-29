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
from PyQt5.QtWidgets import QCalendarWidget, QInputDialog
from PyQt5.QtWidgets import QGraphicsOpacityEffect
from PyQt5.QtCore import QPropertyAnimation

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 스크립트 파일의 절대 경로
ICONS_DIR = os.path.join(BASE_DIR, "assets/icons")  # icons 폴더 경로 설정

MEMO_FILE = "memo.json"

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
def load_modern_light_theme():
    """
    새로운 QSS: 밝고 모던한 테마 (둥근 모서리, 약간의 그림자, 파스텔포인트)
    """
    return """
    QMainWindow {
        background-color: #F7F9FC; /* 전체 배경 */
        font-family: 'Segoe UI', sans-serif;
    }
    /* 커스텀 타이틀바 */
    QFrame#TitleBar {
        background-color: rgba(255, 255, 255, 0.7);
        border-bottom: 1px solid #d2d6dc;
    }
    QLabel#TitleLabel {
        color: #333333;
        font-size: 16px;
        font-weight: 600;
    }
    QPushButton#CloseButton {
        color: #333333;
        background-color: transparent;
        border: none;
        font-size: 14px;
        margin-right: 4px;
    }
    QPushButton#CloseButton:hover {
        background-color: #FF5C5C;
        color: white;
        border-radius: 4px;
    }

    /* 좌측 패널 */
    QFrame#LeftPanel {
        background: #2F3A66; /* 좀 더 진한 블루/퍼플 톤 */
    }
    QLabel#LeftPanelLabel {
        color: #ffffff;
        font-weight: bold;
        font-size: 20px; 
    }
    QPushButton#NavButton {
        background-color: transparent;
        color: #ffffff;
        text-align: left;
        padding: 10px 20px;
        border: none;
        font-size: 14px;
    }
    QPushButton#NavButton:hover {
        background-color: #3f4b7b;
        border-radius: 6px;
    }

    /* 우측 패널 */
    QWidget#RightPanel {
        background: #F7F9FC; 
    }
    QLabel#TopInfoLabel {
        font-size: 18px;
        font-weight: bold;
        color: #2F3A66;
    }
    QFrame#InfoPanel {
        background-color: white;
        border: 1px solid #DDDDDD;
        border-radius: 10px;
    }
    QLineEdit {
        border: 1px solid #cccccc;
        border-radius: 6px;
        padding: 6px 10px;
    }
    QPushButton {
        background-color: #E2E8F0;
        color: #2F3A66;
        border: 1px solid #CBD5E0;
        border-radius: 6px;
        padding: 8px 14px;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: #CBD5E0;
    }
    QTableWidget {
        background-color: #ffffff;
        border: 1px solid #d2d6dc;
        border-radius: 8px;
        gridline-color: #e2e2e2;
        font-size: 13px;
        color: #333;
        alternate-background-color: #fdfdfd;
        selection-background-color: #c8dafc;
        selection-color: #000000;
    }
    QHeaderView::section {
        background-color: #EEF1F5;
        color: #333333;
        font-weight: bold;
        padding: 8px;
        border: none;
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
        self.memo_dict = {}
        
        self.load_memos_from_file()
        # ◆ 프레임 없애서 커스텀 타이틀바 사용
        self.setWindowFlags(Qt.FramelessWindowHint)  
        self.setGeometry(0, 0, 1900, 1200)

        # ◆ 새로운 모던 라이트 테마(QSS) 적용
        self.setStyleSheet(load_modern_light_theme())

        # ◆ 회사 정보 JSON 로드 (기능 유지)
        self.company_info = self.load_company_info()

        # ◆ 드래그 이동용
        self.old_pos = self.pos()

        # ◆ 메인 위젯 + 레이아웃
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(main_widget)

        # ─────────────────────────────────────────────────────────────────
        # 1) 커스텀 타이틀 바 (header)
        # ─────────────────────────────────────────────────────────────────
        self.header = QFrame()
        self.header.setObjectName("TitleBar")  # QSS에서 #TitleBar 로 스타일 지정
        self.header.setFixedHeight(42)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 0, 10, 0)

        # 타이틀 라벨
        title_label = QLabel("아이스크림 ERP ")
        title_label.setObjectName("TitleLabel")  # QSS: #TitleLabel
        # 우측에 관리자 표기
        user_label = QLabel("로그인: 관리자")
        user_label.setStyleSheet("color: white; font-size: 13px;")

        # 🔷 최소화 버튼
        min_btn = QPushButton("―")
        min_btn.setFixedSize(32, 28)
        min_btn.setStyleSheet("color: white; background: transparent; font-size: 16px;")
        min_btn.clicked.connect(self.showMinimized)

        # 🔷 최대화 버튼 (토글)
        self.max_btn = QPushButton("⬜")
        self.max_btn.setFixedSize(32, 28)
        self.max_btn.setStyleSheet("color: white; background: transparent; font-size: 14px;")
        self.max_btn.clicked.connect(self.toggle_max_restore)

        # 🔷 닫기 버튼 (더 잘 보이게 수정)
        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseButton")
        close_btn.setFixedSize(32, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #E11D48;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        close_btn.clicked.connect(self.close)

        # 헤더 레이아웃 배치
        header_layout.addWidget(title_label)
        header_layout.addStretch()
       
        header_layout.addWidget(user_label)
        header_layout.addSpacing(10)
        header_layout.addWidget(min_btn)
        header_layout.addWidget(self.max_btn)
        header_layout.addWidget(close_btn)

        # ─────────────────────────────────────────────────────────────────
        # 2) 본문 레이아웃: 좌측 패널 + 우측 컨텐츠
        # ─────────────────────────────────────────────────────────────────
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 2-1) 왼쪽 패널
        self.left_panel = QFrame()
        self.left_panel.setObjectName("LeftPanel")  # QSS: #LeftPanel
        self.left_panel.setFixedWidth(180)

        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 20, 0, 0)
        left_layout.setSpacing(10)

        # 좌측 상단 로고
        title_label_left = QLabel("성심유통")
        title_label_left.setObjectName("LeftPanelLabel")  # QSS: #LeftPanelLabel
        title_label_left.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title_label_left)
        left_layout.addSpacing(20)

        # 메뉴 버튼 목록
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
            btn.setObjectName("LeftPanelButton")  # QSS: #LeftPanelButton
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(handler)
            left_layout.addWidget(btn)

        left_layout.addStretch()

        # 하단에 검색창
        
        self.search_label = QLabel("검색:")
        self.search_label.setStyleSheet("color: white; padding-left: 8px;")
        self.search_edit = QLineEdit()
        self.search_button = QPushButton("검색")
        self.custom_button = QPushButton("모든 검색")

        self.search_edit.setPlaceholderText("검색")
        self.search_edit.setFixedWidth(180)
        self.search_button.setFixedWidth(180)
        self.custom_button.setFixedWidth(180)
        self.search_button.clicked.connect(self.on_search_clicked)
        self.search_edit.returnPressed.connect(self.on_search_clicked)
        left_layout.addWidget(self.search_label)
        left_layout.addWidget(self.search_edit)
        left_layout.addWidget(self.search_button)
        left_layout.addWidget(self.custom_button)

        # 2-2) 오른쪽 패널
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(1, 1, 0, 0)
        right_layout.setSpacing(1)  # 약간 여백

        # 🔷 날짜/시간 라벨
        # 시계/요일 라벨
        self.datetime_label = QLabel()
        self.datetime_label.setObjectName("DateTimeLabel")
        self.datetime_label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.9);
            color: #2F3A66;
            font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
            font-size: 20px;
            font-weight: 600;
            border: 1px solid #CBD5E0;
            border-radius: 8px;
            padding: 6px 14px;
        """)

        self.day_label = QLabel()
        self.day_label.setStyleSheet("""
            color: #4B5563;
            font-size: 12px;
            font-weight: 500;
            padding-left: 6px;
        """)

        # ⏱️ 타이머로 시계/요일 갱신
        self.update_datetime()
        timer = QTimer(self)
        timer.timeout.connect(self.update_datetime)
        timer.start(1000)

        # 📅 달력 팝업 버튼
        self.calendar_toggle_btn = QPushButton("📅")
        self.calendar_toggle_btn.setFixedSize(45, 45)
        self.calendar_toggle_btn.setStyleSheet("""
            font-size: 40px;
            background-color: #E2E8F0;
            border: 1px solid #CBD5E0;
            border-radius: 8px;
        """)
        self.calendar_toggle_btn.clicked.connect(self.show_calendar_popup)

        # 🧭 시계 + 요일 + 버튼 한 줄에 배치
        clock_row = QHBoxLayout()
        clock_col = QVBoxLayout()
        clock_col.addWidget(self.datetime_label)
        clock_col.addWidget(self.day_label)

        clock_row.addLayout(clock_col)
        clock_row.addSpacing(12)
        clock_row.addWidget(self.calendar_toggle_btn)
        clock_row.addStretch()

        
        
        self.sales_label = QLabel("📊 매출 정보 불러오는 중...")
        self.sales_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.sales_label.setContentsMargins(12, 4, 12, 4)

        self.sales_label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.25);
            color: #1E3A8A;
            font-size: 14px;
            font-weight: 600;
            padding: 8px 16px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.4);
            margin: 4px;
        """)
        
        right_layout.addLayout(clock_row)
        self.sales_timer = QTimer(self)
        self.sales_timer.timeout.connect(self.update_sales_message)
        self.sales_timer.start(4000)  # 4초 간격
        clock_row.addSpacing(12)
        
        clock_row.addWidget(self.sales_label)
        self.load_monthly_sales()

        # # 버튼 영역
        # button_row = QHBoxLayout()
        # button_row.addStretch()
        # for label in ["저장", "조회", "삭제"]:
        #     btn = QPushButton(label)
        #     btn.setFixedWidth(80)
        #     button_row.addWidget(btn)
        # right_layout.addLayout(button_row)

        # 정보 패널(얇은 구분선 등)
        self.info_panel = QFrame()
        self.info_panel.setObjectName("InfoPanel")
        self.info_panel.setFixedHeight(1)
        right_layout.addWidget(self.info_panel)

        # QStackedWidget (탭 컨텐츠)
        self.stacked = QStackedWidget()
        self.stacked.setObjectName("ContentPanel")  # QSS: #ContentPanel
        right_layout.addWidget(self.stacked)

        # 본문 레이아웃에 좌우 패널 배치
        content_layout.addWidget(self.left_panel)
        content_layout.addWidget(self.right_panel)

        # ─────────────────────────────────────────────────────────────────
        # 3) 전체 메인 레이아웃 배치
        # ─────────────────────────────────────────────────────────────────
        main_layout.addWidget(self.header)
        main_layout.addWidget(content_widget)

        # ─────────────────────────────────────────────────────────────────
        # 4) 탭 등록 (기존 코드 그대로)
        # ─────────────────────────────────────────────────────────────────
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

        # 만약 세금계산서(invoices) 탭에서 회사 정보 필요하다면:
        if "invoices" in self.tabs:
            if hasattr(self.tabs["invoices"], "right_panel"):
                self.tabs["invoices"].right_panel.set_company_info(self.company_info)

        # 첫 화면 employees
        self.stacked.setCurrentWidget(self.tabs["employees"])
        self.update_search_placeholder("employees")
        self.update_custom_button("employees")


        self.memo_dict = {}  # 날짜: 메모 저장용 딕셔너리

    def fade_in_sales_label(self):
        self.opacity_effect = QGraphicsOpacityEffect()
        self.sales_label.setGraphicsEffect(self.opacity_effect)

        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(500)  # 0.5초
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()

    def update_sales_message(self):
        if hasattr(self, 'sales_messages') and self.sales_messages:
            self.sales_label.setText(self.sales_messages[self.sales_index])
            self.sales_index = (self.sales_index + 1) % len(self.sales_messages)
            self.fade_in_sales_label()


    def load_monthly_sales(self):
        from datetime import datetime
        import requests

        try:
            now = datetime.now()
            year = now.year
            month = now.month

            # 시작일과 종료일 (이번 달 1일부터 오늘까지)
            start_date = f"{year}-{month:02d}-01"
            end_date = now.strftime("%Y-%m-%d")

            url = f"http://localhost:8000/sales/by_client_range?start_date={start_date}&end_date={end_date}"
            res = requests.get(url)
            if res.status_code == 200:
                sales_data = res.json()  # [{"client_name": "...", "total_sales": ...}, ...]
                if not sales_data:
                    self.sales_messages = ["📭 이번 달 매출 데이터가 없습니다."]
                else:
                    self.sales_messages = [
                        f"📊 {item['client_name']} - {int(item['total_sales']):,}원"
                        for item in sales_data
                    ]
            else:
                self.sales_messages = ["❌ 매출 정보 불러오기 실패"]
        except Exception as e:
            self.sales_messages = [f"❌ 연결 실패: {e}"]

        self.sales_index = 0
        self.update_sales_message()


    def show_calendar_popup(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("📅 달력")
        dialog.setFixedSize(400, 500)

        layout = QVBoxLayout(dialog)
        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        calendar.clicked.connect(self.on_date_clicked)
        layout.addWidget(calendar)

        dialog.exec_()


    def toggle_calendar(self):
        if self.calendar.isVisible():
            self.calendar.hide()
        else:
            self.calendar.show()
            
    def on_date_clicked(self, qdate):
        key = qdate.toString("yyyy-MM-dd")
        current = self.memo_dict.get(key, "")
        text, ok = QInputDialog.getMultiLineText(self, "메모 작성", f"{key} 메모:", current)
        if ok:
            self.memo_dict[key] = text
            self.save_memos_to_file()


    def toggle_max_restore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()


    def save_memos_to_file(self):
        try:
            with open(MEMO_FILE, "w", encoding="utf-8") as f:
                json.dump(self.memo_dict, f, ensure_ascii=False, indent=2)
            print("✅ 메모 저장 완료")
        except Exception as e:
            print(f"❌ 메모 저장 실패: {e}")

    def load_memos_from_file(self):
        try:
            if not os.path.exists(MEMO_FILE):
                self.memo_dict = {}
                return
            with open(MEMO_FILE, "r", encoding="utf-8") as f:
                self.memo_dict = json.load(f)
            print("✅ 메모 불러오기 완료")
        except Exception as e:
            print(f"❌ 메모 로딩 실패: {e}")
            self.memo_dict = {}

    # ─────────────────────────────────────────────────────────────────
    # 5) 시그널/슬롯 & 기존 기능들
    # ─────────────────────────────────────────────────────────────────
    def update_datetime(self):
        from datetime import datetime
        now = datetime.now()
        self.datetime_label.setText(now.strftime("%Y-%m-%d %H:%M:%S"))
        self.day_label.setText(now.strftime("%A"))  # Friday, Saturday...



    def mousePressEvent(self, event):
        """
        마우스로 타이틀바를 드래그하여 창 이동
        """
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def update_custom_button(self, tab_name):
        """ 현재 탭에 따라 '모든 검색' 버튼 기능을 다르게 연결 """
        current_tab = self.stacked.currentWidget()

        try:
            self.custom_button.clicked.disconnect()
        except TypeError:
            pass  # 이미 연결된 슬롯이 없으면 무시

        # do_custom_action()이 있으면 연결
        if hasattr(current_tab, "do_custom_action"):
            self.custom_button.clicked.connect(current_tab.do_custom_action)
            self.custom_button.setText("모든 검색")
        else:
            self.custom_button.setText("기능 없음")
            self.custom_button.clicked.connect(lambda: print("❌ 이 UI에서는 기능이 없습니다."))

    def open_company_info_dialog(self):
        
        dialog = CompanyInfoDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            info = dialog.get_company_info()
            self.company_info = info
            print("▶ 우리 회사 정보 등록 완료:", self.company_info)
            # 서버에 저장:
            self.save_company_info_to_server(self.company_info)
            # 탭 갱신 (예: 세금계산서 패널 등)
            if "invoices" in self.tabs:
                if hasattr(self.tabs["invoices"], "right_panel"):
                    self.tabs["invoices"].right_panel.set_company_info(self.company_info)

    def save_company_info_to_server(self, info: dict):
        try:
            url = "http://localhost:8000/company"
            response = requests.post(url, json=info)
            if response.status_code in [200, 201]:
                print("✅ 서버에 회사 정보 저장 성공!")
            else:
                print(f"❌ 서버 저장 실패: {response.status_code} / {response.text}")
        except Exception as e:
            print(f"❌ 서버 전송 오류: {e}")

    def load_company_info(self, filename="company_info.json") -> dict:
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

    # ─────────────────────────────────────────────────────────────────
    # 6) 사이드바 탭 전환 함수 (기존 기능 그대로)
    # ─────────────────────────────────────────────────────────────────
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
        """
        검색 버튼 클릭 시 현재 탭에 맞춰 검색 수행
        """
        keyword = self.search_edit.text().strip()
        if not keyword:
            return

        current_tab = self.stacked.currentWidget()
        # 각 탭 클래스에 'do_search' 메서드가 있다면 호출
        if hasattr(current_tab, "do_search"):
            current_tab.do_search(keyword)
        else:
            print(f"❌ 현재 탭에 do_search 메서드가 없습니다: {type(current_tab)}")
            
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
            "payments": "직원이름 검색",
            "invoices": "거래처명 검색",
            "inventory": "직원이름 검색"
        }
        self.search_edit.setPlaceholderText(placeholders.get(tab_name, "검색"))
import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QLineEdit, QStackedWidget, QTabBar,
    QTabWidget, QListWidget, QListWidgetItem, QFrame
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon

# 좌측 패널과 상단 탭 영역을 위한 스타일
# (원하시면 여기서 색상이나 폰트, 크기 등을 세부 조정하세요)
STYLE_SHEET = """
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

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wholesale Management System (New Layout)")
        self.resize(1400, 900)
        self.setStyleSheet(STYLE_SHEET)

        # ------------------------------
        # 1) 전체 메인 레이아웃: 수평
        #    [LeftPanel] | [CenterWidget(상단 탭 + 중앙 스택)]
        # ------------------------------
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        # 2) 왼쪽 사이드 패널
        self.left_panel = QFrame()
        self.left_panel.setObjectName("LeftPanel")
        self.left_panel.setFixedWidth(250)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.setSpacing(0)

        # (2-1) 왼쪽 패널 맨 위: '검색' 영역
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("SearchEdit")
        self.search_edit.setPlaceholderText("검색어 입력...")
        self.search_button = QPushButton("검색")
        self.search_button.setObjectName("SearchButton")
        # 수평 배치
        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 10, 0, 10)
        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(self.search_button)
        left_layout.addLayout(search_row)

        # (2-2) 좌측 메뉴 버튼들
        # (아이콘 없이 텍스트만 표시. 필요하면 추가)
        btn_employees = QPushButton("직원관리", self.left_panel)
        btn_employees.setObjectName("LeftPanelButton")
        btn_employees.clicked.connect(self.show_employees_tab)

        btn_clients = QPushButton("거래처관리", self.left_panel)
        btn_clients.setObjectName("LeftPanelButton")
        btn_clients.clicked.connect(self.show_clients_tab)

        btn_products = QPushButton("제품관리", self.left_panel)
        btn_products.setObjectName("LeftPanelButton")
        btn_products.clicked.connect(self.show_products_tab)

        btn_orders = QPushButton("주문관리", self.left_panel)
        btn_orders.setObjectName("LeftPanelButton")
        btn_orders.clicked.connect(self.show_orders_tab)

        # 필요한 만큼 계속 추가 가능
        left_layout.addWidget(btn_employees)
        left_layout.addWidget(btn_clients)
        left_layout.addWidget(btn_products)
        left_layout.addWidget(btn_orders)

        left_layout.addStretch(1)  # 아래로 공간 확보

        main_layout.addWidget(self.left_panel)

        # 3) 중앙 영역
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0,0,0,0)
        center_layout.setSpacing(0)

        # (3-1) 상단 탭 (QTabWidget)
        self.tab_widget = QTabWidget()
        # 탭 위치를 상단으로 (기본값) / 아이콘 없이 텍스트만
        self.tab_widget.setTabPosition(QTabWidget.North)

        # 여기서 탭을 추가 - 실제로는 EmployeesTab, ClientsTab 등을 붙일 예정
        self.tab_widget.addTab(QWidget(), "직원관리")
        self.tab_widget.addTab(QWidget(), "거래처관리")
        self.tab_widget.addTab(QWidget(), "제품관리")
        self.tab_widget.addTab(QWidget(), "주문관리")

        # 탭 변화 시그널
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        center_layout.addWidget(self.tab_widget)

        # (3-2) 실제 컨텐츠 스택
        self.stack = QStackedWidget()
        center_layout.addWidget(self.stack)

        # 예시: 탭별로 표시할 QWidget들
        # [실제 코드]에서는 from employee_ui import EmployeesTab, etc...
        # 예시로 간단히
        from PyQt5.QtWidgets import QTextEdit
        self.stack_widget_employees = QTextEdit("직원관리 화면 예시")
        self.stack_widget_clients = QTextEdit("거래처관리 화면 예시")
        self.stack_widget_products = QTextEdit("제품관리 화면 예시")
        self.stack_widget_orders = QTextEdit("주문관리 화면 예시")

        # stack에 위젯 등록
        self.stack.addWidget(self.stack_widget_employees)  # index=0
        self.stack.addWidget(self.stack_widget_clients)    # index=1
        self.stack.addWidget(self.stack_widget_products)   # index=2
        self.stack.addWidget(self.stack_widget_orders)     # index=3

        # 기본은 0번(직원관리) 표시
        self.stack.setCurrentIndex(0)

        main_layout.addWidget(center_widget)

        # -----------------------------
        # JSON 로딩 등 기존 초기화 코드
        # -----------------------------
        self.company_info = {}
        # (원하는 로직 추가)

        # 검색 버튼 클릭
        self.search_button.clicked.connect(self.on_search_clicked)

    # ------------------------------------------
    # 탭 변경 시, 스택의 페이지도 같이 바꿔준다
    # ------------------------------------------
    def on_tab_changed(self, index):
        self.stack.setCurrentIndex(index)

    # ------------------------------------------
    # 왼쪽 버튼들 클릭 → 탭 전환
    # ------------------------------------------
    def show_employees_tab(self):
        self.tab_widget.setCurrentIndex(0)

    def show_clients_tab(self):
        self.tab_widget.setCurrentIndex(1)

    def show_products_tab(self):
        self.tab_widget.setCurrentIndex(2)

    def show_orders_tab(self):
        self.tab_widget.setCurrentIndex(3)

    # ------------------------------------------
    # 검색 버튼 이벤트
    # ------------------------------------------
    def on_search_clicked(self):
        keyword = self.search_edit.text().strip()
        if not keyword:
            print("검색어가 비어 있음")
            return
        # 여기서 실제 검색 로직 연결(어느 탭인지 파악 후 do_search 등 호출)
        # 예시
        current_index = self.tab_widget.currentIndex()
        print(f"현재 탭: {current_index}, 검색어: {keyword}")

# 실행 예시
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())

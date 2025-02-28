from PyQt5.QtWidgets import QWidget, QHBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel, QComboBox, QVBoxLayout, QGridLayout, QScrollArea, QDateEdit
import os
import sys
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QResizeEvent,QFontMetrics
import requests
# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_orders, api_create_order, api_update_order, api_delete_order, get_auth_headers

BASE_URL = "http://127.0.0.1:8000"  # 실제 서버 URL
global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)

class OrderLeftWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()

        # 직원 목록 (세로 버튼)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.employee_container = QWidget()
        self.employee_layout = QVBoxLayout(self.employee_container)

        # ✅ 서버에서 직원 목록 불러오기
        self.employee_buttons = []  # 버튼 목록 저장
        self.load_employees()

        self.scroll_area.setWidget(self.employee_container)
        layout.addWidget(self.scroll_area)

        # ✅ 전체 주문 버튼
        self.total_label = QLabel("전체 주문 조회")
        self.total_date_picker = QDateEdit()
        self.total_date_picker.setCalendarPopup(True)
        self.total_date_picker.setDate(QDate.currentDate())

        self.total_button = QPushButton("전체 주문 보기")
        layout.addWidget(self.total_label)
        layout.addWidget(self.total_date_picker)
        layout.addWidget(self.total_button)

        self.setLayout(layout)

    def load_employees(self):
        """
        서버에서 직원 목록을 가져와 버튼을 생성
        """
        global global_token
        url = f"{BASE_URL}/employees/"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                employees = resp.json()
            else:
                employees = []
        except Exception as e:
            print(f"❌ 직원 목록 가져오기 실패: {e}")
            employees = []

        # ✅ 직원 목록 버튼 추가
        for employee in employees:
            btn = QPushButton(employee.get("name", "알 수 없음"))
            btn.clicked.connect(lambda checked, n=employee["name"]: self.select_employee(n))
            self.employee_layout.addWidget(btn)
            self.employee_buttons.append(btn)

    def select_employee(self, employee_name):
        """
        특정 직원의 주문을 조회 (추후 기능 추가 예정)
        """
        print(f"직원 {employee_name}의 주문을 조회합니다.")


class OrderRightWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.current_products = []  # ✅ 상품 목록 저장 (resizeEvent에서 참조 가능)

        # ✅ 타이틀 + 새로고침 버튼 추가
        self.header_layout = QVBoxLayout()
        self.title = QLabel("📋 주문 내역")
        self.title.setFont(QFont("Arial", 9, QFont.Bold))  # ✅ 폰트 크기 9로 설정 (헤더)
        self.refresh_button = QPushButton("🔄 새로고침")
        self.refresh_button.setFont(QFont("Arial", 8))
        self.refresh_button.clicked.connect(self.refresh_orders)  # ✅ 새로고침 기능 연결
        self.header_layout.addWidget(self.title)
        self.header_layout.addWidget(self.refresh_button)
        self.layout.addLayout(self.header_layout)

        # ✅ 상품 목록을 배치할 레이아웃
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)  # ✅ 창 크기에 따라 동적 정렬
        self.layout.addWidget(self.container)

        self.setLayout(self.layout)
        self.load_products()  # ✅ 서버에서 상품 목록 로드

    def load_products(self):
        """
        서버에서 상품 목록을 가져와 `카테고리`별로 정리 후 표시
        """
        global global_token
        url = f"{BASE_URL}/products/all"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                self.current_products = [p for p in resp.json() if p["is_active"] == 1]  # ✅ 상품 목록 저장
            else:
                self.current_products = []
        except Exception as e:
            print(f"❌ 상품 목록 가져오기 실패: {e}")
            self.current_products = []

        self.populate_table()

    def populate_table(self):
        """
        하나의 테이블에서 `카테고리 -> 품명 -> 갯수` 순으로 정렬,
        세로 공간이 부족하면 자동으로 옆 칸으로 이동하며 빈 행 제거,
        글씨 크기를 자동 조정하여 모든 내용을 표시
        """
        # ✅ 기존 테이블 초기화
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        # ✅ 사용 가능한 세로 공간 계산 (제목, 버튼, 빈 공간 제외)
        available_height = self.height() - self.header_layout.sizeHint().height() - 80  # ✅ 정확한 여백 적용
        row_height = 30  # ✅ 행 높이를 수동 설정 (20px)
        max_rows_per_section = max(5, available_height // row_height)  # ✅ 세로 공간에 맞는 최대 행 수 결정

        row = 0  # ✅ 오류 해결: `row, col = 0` → `row = 0, col = 0`
        col = 0  # ✅ 오류 해결

        # ✅ 상품을 `카테고리 -> 품명` 순으로 정리
        sorted_products = []
        for p in self.current_products:
            sorted_products.append((p["category"], p["brand_id"], p["product_name"]))

        sorted_products.sort()  # ✅ 카테고리 순으로 정렬

        # ✅ 테이블 초기화 (처음에 빈 표 만들지 않음)
        table = None
        row_index = 0
        current_category = None
        current_brand = None
        for category, brand, product_name in sorted_products:
            # ✅ 새로운 칸이 필요하면 테이블 생성
            if row_index == 0 or table is None:
                table = QTableWidget()
                table.setColumnCount(2)  # ✅ [품명, 갯수]만 표시
                table.setHorizontalHeaderLabels(["품명", "갯수"])
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # ✅ 열 크기 자동 조정 (가로)
                table.setFont(QFont("Arial", 9))  # ✅ 기본 글씨 크기 7
                table.verticalHeader().setVisible(False)  # ✅ 왼쪽 숫자(인덱스) 헤더 제거
                table.setRowCount(0)  # ✅ 빈 행 제거

            if current_category != category:
                # ✅ 카테고리 변경 시 새로운 행 추가 (2열 병합)
                table.insertRow(table.rowCount())
                category_item = QTableWidgetItem(category)
                category_item.setFont(QFont("Arial", 9, QFont.Bold))
                category_item.setTextAlignment(Qt.AlignCenter)
                table.setSpan(table.rowCount() - 1, 0, 1, 2)  # ✅ 2열 병합
                table.setItem(table.rowCount() - 1, 0, category_item)
                current_category = category

            if current_brand != brand:
                # ✅ 브랜드 변경 시 새로운 행 추가
                # table.insertRow(table.rowCount())
                # brand_item = QTableWidgetItem(f"브랜드 {brand}")
                # brand_item.setFont(QFont("Arial", 7, QFont.Bold))
                # table.setItem(table.rowCount() - 1, 0, brand_item)
                current_brand = brand

            # ✅ 상품 추가
            table.insertRow(table.rowCount())
            table.setItem(table.rowCount() - 1, 0, self.create_resized_text(product_name, table))
            table.setItem(table.rowCount() - 1, 1, QTableWidgetItem(""))  # ✅ 주문 수량 (추후 서버에서 가져올 예정)

            # ✅ 행 높이를 수동으로 설정 (20px)
            table.setRowHeight(table.rowCount() - 1, 12)

            row_index += 1

            # ✅ 현재 세로 공간을 초과하면 오른쪽 칸으로 이동
            if row_index >= max_rows_per_section:
                self.grid_layout.addWidget(table, row, col, 1, 1)
                row_index = 0
                col += 1  # ✅ 다음 칸으로 이동
                table = None  # ✅ 새 테이블 생성 필요

        # ✅ 마지막 테이블 추가
        if table is not None:
            self.grid_layout.addWidget(table, row, col, 1, 1)

    def create_resized_text(self, text, table):
        """
        칸 크기에 맞춰 글씨 크기를 자동으로 조정하여 텍스트가 잘리지 않도록 함
        """
        font = QFont("Arial", 9)  # 기본 글씨 크기 7
        metrics = QFontMetrics(font)
        max_width = table.columnWidth(0) - 5  # 셀 너비 계산

        while metrics.width(text) > max_width and font.pointSize() > 5:
            font.setPointSize(font.pointSize() - 1)
            metrics = QFontMetrics(font)

        item = QTableWidgetItem(text)
        item.setFont(font)
        return item

    def resizeEvent(self, event: QResizeEvent):
        """
        창 크기 변경 시 자동으로 정렬 조정
        """
        self.populate_table()
        event.accept()

    def refresh_orders(self):
        """
        새로고침 버튼 클릭 시 상품 목록 갱신
        """
        self.load_products()


class OrdersTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout()

        # 왼쪽 패널: 직원 목록 (세로 버튼 + 날짜 선택)
        self.left_widget = OrderLeftWidget()
        main_layout.addWidget(self.left_widget, 1)  # 왼쪽 패널 크기 비율 1

        # 오른쪽 패널: 상품 분류별, 브랜드별 정리 + 주문 갯수 입력
        self.right_panel = OrderRightWidget()
        main_layout.addWidget(self.right_panel, 5)  # 오른쪽 패널 크기 비율 5

        self.setLayout(main_layout)
    def do_search(self, keyword):
        pass
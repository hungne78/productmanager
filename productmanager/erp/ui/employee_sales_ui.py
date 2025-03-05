from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QLabel, QComboBox, QGroupBox
from PyQt5.QtCore import Qt
import sys
import requests
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_employees, get_auth_headers

BASE_URL = "http://127.0.0.1:8000"  # FastAPI 서버 주소
global_token = get_auth_headers  # 로그인 토큰 필요

class EmployeeSalesTab(QWidget):
    """ 직원별 매출 조회 탭 """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        # 🔹 왼쪽 패널 (검색 필터)
        self.left_panel = QWidget()
        # 🔹 왼쪽 패널 (검색 필터) - QGroupBox로 테두리 추가
        self.left_panel = QGroupBox("검색 옵션")  # ✅ 테두리 추가
        self.left_panel.setStyleSheet(
            "border: 1px solid gray; border-radius: 5px; padding: 10px;"
        )
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)  # ✅ 모든 요소를 위쪽 정렬

        # ✅ 연도 선택 (올해 기준 -10년)
        self.label_year = QLabel("조회 연도:")
        self.year_combo = QComboBox()
        current_year = datetime.now().year
        for y in range(current_year, current_year - 10, -1):
            self.year_combo.addItem(str(y))

        # ✅ 월 선택 (1월~12월)
        self.label_month = QLabel("조회 월:")
        self.month_combo = QComboBox()
        for m in range(1, 13):
            self.month_combo.addItem(f"{m}월", m)

        # ✅ 직원 선택 드롭다운
        self.label_employee = QLabel("직원 선택:")
        self.employee_combo = QComboBox()
        self.load_employees()  # 직원 목록 불러오기

        # ✅ 조회 버튼
        self.search_button = QPushButton("조회")
        self.search_button.clicked.connect(self.fetch_sales_data)

        # 🔹 왼쪽 패널 레이아웃 설정
        left_layout.addWidget(self.label_year)
        left_layout.addWidget(self.year_combo)
        left_layout.addWidget(self.label_month)
        left_layout.addWidget(self.month_combo)
        left_layout.addWidget(self.label_employee)
        left_layout.addWidget(self.employee_combo)
        left_layout.addWidget(self.search_button)
        self.left_panel.setLayout(left_layout)

        # 🔹 오른쪽 패널 (거래처별 매출 데이터)
        self.right_panel = QWidget()
        right_layout = QVBoxLayout()

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(5)
        self.sales_table.setHorizontalHeaderLabels(["거래처명", "전월 매출", "전년도 매출", "현재월 매출", "평균 방문주기"])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        right_layout.addWidget(self.sales_table)
        self.right_panel.setLayout(right_layout)

        # 🔹 메인 레이아웃 설정
        self.left_panel.setFixedWidth(350)
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)
        self.setLayout(main_layout)

    def load_employees(self):
        """ 직원 목록 로드 """
        global global_token
        if not global_token:
            print("⚠️ 로그인 토큰이 없습니다.")
            return

        try:
            employees = api_fetch_employees(global_token)
            if employees:
                self.employee_combo.clear()
                self.employee_combo.addItem("직원 선택", None)  # 기본 선택 항목 추가
                for emp in employees:
                    self.employee_combo.addItem(f"{emp['name']} (ID: {emp['id']})", emp['id'])
        except Exception as e:
            print(f"🚨 직원 목록 로드 오류: {e}")

    def fetch_sales_data(self):
        """ 선택한 직원의 매출 데이터 조회 """
        global global_token
        if not global_token:
            print("⚠️ 로그인 토큰이 없습니다.")
            return

        employee_id = self.employee_combo.currentData()
        if employee_id is None:
            print("⚠️ 직원이 선택되지 않았습니다.")
            return

        selected_year = int(self.year_combo.currentText())  # ✅ 선택된 연도 가져오기
        selected_month = self.month_combo.currentData()  # ✅ 선택된 월 가져오기

        url = f"{BASE_URL}/sales/employee_sales/{employee_id}/{selected_year}/{selected_month}"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            sales_data = response.json()
            self.update_sales_table(sales_data)
        except Exception as e:
            print(f"🚨 매출 데이터 조회 오류: {e}")

    def update_sales_table(self, data):
        """ 매출 데이터 테이블 업데이트 """
        self.sales_table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.sales_table.setItem(row, 0, QTableWidgetItem(item["client_name"]))
            self.sales_table.setItem(row, 1, QTableWidgetItem(str(item["prev_month_sales"])))
            self.sales_table.setItem(row, 2, QTableWidgetItem(str(item["last_year_sales"])))
            self.sales_table.setItem(row, 3, QTableWidgetItem(str(item["current_month_sales"])))
            self.sales_table.setItem(row, 4, QTableWidgetItem(str(item["visit_frequency"])))

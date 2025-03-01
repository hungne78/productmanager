from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QCheckBox,\
    QHeaderView, QFormLayout, QDateEdit, QLabel, QGroupBox
from PyQt5.QtChart import QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis, QLineSeries
import sys
import os
from datetime import datetime, timedelta
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import  get_auth_headers
from PyQt5.QtWidgets import QSizePolicy

global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)



class SalesLeftPanel(QWidget):
    """
    왼쪽 패널 - 기간 선택 & 거래처별 매출 기여도 분석 (비율 추가)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # ✅ 기간 선택 UI
        date_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(datetime.today().date())
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(datetime.today().date())

        self.filter_button = QPushButton("조회")
        self.filter_button.clicked.connect(self.fetch_sales_data)

        date_layout.addWidget(QLabel("시작 날짜:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("종료 날짜:"))
        date_layout.addWidget(self.end_date)
        date_layout.addWidget(self.filter_button)

        layout.addLayout(date_layout)

        # ✅ 이전 기간과 비교 체크박스
        self.compare_checkbox = QCheckBox("📊 이전 기간과 비교")
        layout.addWidget(self.compare_checkbox)

        # ✅ 거래처별 매출 기여도 분석 테이블 (3열로 수정)
        self.client_sales_table = QTableWidget()
        self.client_sales_table.setColumnCount(3)  # ✅ 3열 추가 (거래처, 총 매출, 기여도 %)
        self.client_sales_table.setHorizontalHeaderLabels(["거래처", "총 매출", "기여도(%)"])
        self.client_sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("🏆 거래처별 매출 기여도"))
        layout.addWidget(self.client_sales_table)

        self.setLayout(layout)

    def fetch_sales_data(self):
        """
        FastAPI에서 기간별 매출 데이터 가져오기
        """
        if self.parent_widget:
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            compare = self.compare_checkbox.isChecked()  # ✅ 이전 기간 비교 여부 확인

            self.parent_widget.load_sales_data(start_date, end_date, compare)

    def update_client_sales_data(self, client_sales):
        """
        거래처별 매출 기여도 테이블 업데이트
        """
        # ✅ 전체 매출 합계 계산 (0일 경우 대비 1로 설정)
        total_sales_sum = sum([s["total_sales"] for s in client_sales]) if client_sales else 1

        self.client_sales_table.setRowCount(0)
        for client in client_sales:
            row = self.client_sales_table.rowCount()
            self.client_sales_table.insertRow(row)

            # ✅ 거래처명
            self.client_sales_table.setItem(row, 0, QTableWidgetItem(str(client["client_id"])))

            # ✅ 총 매출
            self.client_sales_table.setItem(row, 1, QTableWidgetItem(f"₩{client['total_sales']:,}"))

            # ✅ 기여도 계산 후 추가 (소수점 2자리 반올림)
            contribution = (client["total_sales"] / total_sales_sum) * 100
            self.client_sales_table.setItem(row, 2, QTableWidgetItem(f"{round(contribution, 2)}%"))


class SalesRightPanel(QWidget):
    """
    오른쪽 패널 - 좌우 1:3 비율로 나눈 매출 데이터 및 그래프
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()  # 좌우 레이아웃으로 변경

        # 🔹 왼쪽 (1) - 기존 테이블
        self.left_section = QVBoxLayout()

        # ✅ 직원별 매출 테이블
        self.employee_sales_table = QTableWidget()
        self.employee_sales_table.setColumnCount(3)
        self.employee_sales_table.setHorizontalHeaderLabels(["직원 ID", "직원 이름", "총 매출"])
        self.employee_sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.left_section.addWidget(QLabel("📌 직원별 매출"))
        self.left_section.addWidget(self.employee_sales_table)

        # ✅ 기간별 전체 매출 테이블
        self.total_sales_table = QTableWidget()
        self.total_sales_table.setColumnCount(2)
        self.total_sales_table.setHorizontalHeaderLabels(["날짜", "총 매출"])
        self.total_sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.left_section.addWidget(QLabel("📊 기간별 전체 매출"))
        self.left_section.addWidget(self.total_sales_table)

        # ✅ 이전 기간 대비 매출 변화 테이블
        self.previous_sales_table = QTableWidget()
        self.previous_sales_table.setColumnCount(3)
        self.previous_sales_table.setHorizontalHeaderLabels(["날짜", "현재 매출", "이전 매출"])
        self.previous_sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.left_section.addWidget(QLabel("📉 이전 기간 대비 매출 변화"))
        self.left_section.addWidget(self.previous_sales_table)

        main_layout.addLayout(self.left_section, 1)  # 📌 좌측 1 비율

        # 🔹 오른쪽 (3) - 그래프 영역
        self.right_section = QVBoxLayout()

        # ✅ 직원별 매출 그래프
        self.employee_sales_chart = QChartView()
        self.right_section.addWidget(QLabel("📊 직원별 매출 그래프"))
        self.right_section.addWidget(self.employee_sales_chart)

        # ✅ 기간별 전체 매출 그래프
        self.total_sales_chart = QChartView()
        self.right_section.addWidget(QLabel("📊 기간별 전체 매출 그래프"))
        self.right_section.addWidget(self.total_sales_chart)

        # ✅ 이전 기간 대비 매출 비교 그래프
        self.comparison_chart = QChartView()
        self.right_section.addWidget(QLabel("📊 이전 기간 대비 매출 비교"))
        self.right_section.addWidget(self.comparison_chart)

        main_layout.addLayout(self.right_section, 3)  # 📌 우측 3 비율

        self.setLayout(main_layout)

    def update_sales_data(self, employee_sales, total_sales, client_sales, previous_sales):
        """
        직원별, 전체, 거래처별 매출 데이터 업데이트 + 그래프 생성
        """
        # ✅ 직원별 매출 테이블 업데이트
        self.employee_sales_table.setRowCount(0)
        for emp in employee_sales:
            row = self.employee_sales_table.rowCount()
            self.employee_sales_table.insertRow(row)
            self.employee_sales_table.setItem(row, 0, QTableWidgetItem(str(emp["employee_id"])))
            self.employee_sales_table.setItem(row, 1, QTableWidgetItem(emp["employee_name"]))
            self.employee_sales_table.setItem(row, 2, QTableWidgetItem(f"₩{emp['total_sales']:,}"))

        # ✅ 기간별 전체 매출 테이블 업데이트
        self.total_sales_table.setRowCount(0)
        for sales in total_sales:
            row = self.total_sales_table.rowCount()
            self.total_sales_table.insertRow(row)
            self.total_sales_table.setItem(row, 0, QTableWidgetItem(sales["date"]))
            self.total_sales_table.setItem(row, 1, QTableWidgetItem(f"₩{sales['total_sales']:,}"))

        # ✅ 이전 기간 대비 매출 변화 테이블 업데이트
        self.previous_sales_table.setRowCount(0)
        for current, previous in zip(total_sales, previous_sales):
            row = self.previous_sales_table.rowCount()
            self.previous_sales_table.insertRow(row)
            self.previous_sales_table.setItem(row, 0, QTableWidgetItem(current["date"]))
            self.previous_sales_table.setItem(row, 1, QTableWidgetItem(f"₩{current['total_sales']:,}"))
            self.previous_sales_table.setItem(row, 2, QTableWidgetItem(f"₩{previous['total_sales']:,}"))

        # ✅ 그래프 업데이트
        self.update_employee_sales_chart(employee_sales)
        self.update_total_sales_chart(total_sales)
        self.update_comparison_chart(total_sales, previous_sales)

    def update_employee_sales_chart(self, data):
        """
        직원별 매출 그래프 업데이트 (막대 그래프)
        """
        chart = QChart()
        series = QBarSeries()
        categories = []

        for emp in data:
            bar_set = QBarSet(emp["employee_name"])
            bar_set.append(emp["total_sales"])
            series.append(bar_set)
            categories.append(emp["employee_name"])

        chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.setAxisX(axis_x, series)

        self.employee_sales_chart.setChart(chart)

    def update_total_sales_chart(self, data):
        """
        기간별 전체 매출 그래프 업데이트 (막대 그래프)
        """
        chart = QChart()
        series = QBarSeries()
        categories = []

        for sales in data:
            bar_set = QBarSet(sales["date"])
            bar_set.append(sales["total_sales"])
            series.append(bar_set)
            categories.append(sales["date"])

        chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.setAxisX(axis_x, series)

        self.total_sales_chart.setChart(chart)

    def update_comparison_chart(self, current_sales, previous_sales):
        """
        현재 vs 이전 기간 비교 그래프 업데이트 (선 그래프)
        """
        chart = QChart()
        series_current = QLineSeries()
        series_previous = QLineSeries()

        axis_x = QBarCategoryAxis()
        categories = []

        for current, previous in zip(current_sales, previous_sales):
            date = current["date"]
            categories.append(date)
            series_current.append(len(categories), current["total_sales"])
            series_previous.append(len(categories), previous["total_sales"])

        chart.addSeries(series_current)
        chart.addSeries(series_previous)

        axis_x.append(categories)
        chart.createDefaultAxes()
        chart.setAxisX(axis_x, series_current)
        chart.setAxisX(axis_x, series_previous)

        self.comparison_chart.setChart(chart)


class SalesTab(QWidget):
    """
    총매출 탭
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        self.left_panel = SalesLeftPanel(self)
        self.right_panel = SalesRightPanel()

        # ✅ 크기 정책 설정
        self.left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ✅ 고정 크기 설정
        self.left_panel.setFixedWidth(350)  # 1 비율
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)

        self.setLayout(main_layout)

    def load_sales_data(self, start_date, end_date, compare):
        """
        FastAPI에서 직원별 및 기간별 매출 데이터 가져오기 (작년 같은 기간과 비교 가능)
        """
        headers = {"Authorization": f"Bearer {global_token}"}

        employee_sales_url = f"http://127.0.0.1:8000/sales/employees?start_date={start_date}&end_date={end_date}"
        total_sales_url = f"http://127.0.0.1:8000/sales/total?start_date={start_date}&end_date={end_date}"
        client_sales_url = f"http://127.0.0.1:8000/sales/by_client/{end_date}"

        try:
            emp_response = requests.get(employee_sales_url, headers=headers)
            total_response = requests.get(total_sales_url, headers=headers)
            client_response = requests.get(client_sales_url, headers=headers)

            emp_response.raise_for_status()
            total_response.raise_for_status()
            client_response.raise_for_status()

            employee_sales = emp_response.json()
            total_sales = total_response.json()
            client_sales = client_response.json()  # ✅ 거래처별 매출 데이터

            # ✅ 전체 매출 총합 계산 (거래처별 매출 기여도 계산용)
            total_sales_sum = sum([s["total_sales"] for s in client_sales]) if client_sales else 1

            # ✅ 거래처별 매출 기여도 계산
            for client in client_sales:
                client["contribution"] = round((client["total_sales"] / total_sales_sum) * 100, 2)

            previous_sales = []
            if compare:
                # ✅ "작년 같은 기간"을 비교 대상으로 설정
                prev_start_date = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")
                prev_end_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")

                previous_url = f"http://127.0.0.1:8000/sales/total?start_date={prev_start_date}&end_date={prev_end_date}"
                prev_response = requests.get(previous_url, headers=headers)
                prev_response.raise_for_status()
                previous_sales = prev_response.json()

            self.left_panel.update_client_sales_data(client_sales)
            self.right_panel.update_sales_data(employee_sales, total_sales, client_sales, previous_sales)

        except requests.RequestException as e:
            print(f"❌ 매출 데이터 조회 실패: {e}")


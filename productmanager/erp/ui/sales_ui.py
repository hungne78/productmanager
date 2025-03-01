from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QFormLayout, QDateEdit, QLabel, QGroupBox
from PyQt5.QtChart import QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis
import sys
import os
from datetime import datetime
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import  get_auth_headers

global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)

class SalesLeftPanel(QWidget):
    """
    왼쪽 패널 - 기간 선택
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # ✅ 기간 선택 위젯
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

        self.setLayout(layout)

    def fetch_sales_data(self):
        """
        FastAPI에서 기간별 매출 데이터 가져오기
        """
        if self.parent_widget:
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            self.parent_widget.load_sales_data(start_date, end_date)


class SalesRightPanel(QWidget):
    """
    오른쪽 패널 - 직원별 매출 및 기간별 전체 매출 (표 + 그래프)
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # ✅ 직원별 매출 테이블
        self.employee_sales_table = QTableWidget()
        self.employee_sales_table.setColumnCount(3)
        self.employee_sales_table.setHorizontalHeaderLabels(["직원 ID", "직원 이름", "총 매출"])
        self.employee_sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("직원별 매출"))
        layout.addWidget(self.employee_sales_table)

        # ✅ 직원별 매출 그래프
        self.employee_sales_chart = QChartView()
        layout.addWidget(self.employee_sales_chart)

        # ✅ 기간별 전체 매출 테이블
        self.total_sales_table = QTableWidget()
        self.total_sales_table.setColumnCount(2)
        self.total_sales_table.setHorizontalHeaderLabels(["날짜", "총 매출"])
        self.total_sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("기간별 전체 매출"))
        layout.addWidget(self.total_sales_table)

        # ✅ 기간별 매출 그래프
        self.total_sales_chart = QChartView()
        layout.addWidget(self.total_sales_chart)

        self.setLayout(layout)

    def update_sales_data(self, employee_sales, total_sales):
        """
        직원별 매출 및 전체 매출 데이터 업데이트
        """
        # ✅ 직원별 매출 테이블 업데이트
        self.employee_sales_table.setRowCount(0)
        for emp in employee_sales:
            row = self.employee_sales_table.rowCount()
            self.employee_sales_table.insertRow(row)
            self.employee_sales_table.setItem(row, 0, QTableWidgetItem(str(emp["employee_id"])))
            self.employee_sales_table.setItem(row, 1, QTableWidgetItem(emp["employee_name"]))
            self.employee_sales_table.setItem(row, 2, QTableWidgetItem(f"₩{emp['total_sales']:,}"))

        # ✅ 직원별 매출 그래프 업데이트
        self.update_employee_sales_chart(employee_sales)

        # ✅ 기간별 전체 매출 테이블 업데이트
        self.total_sales_table.setRowCount(0)
        for sales in total_sales:
            row = self.total_sales_table.rowCount()
            self.total_sales_table.insertRow(row)
            self.total_sales_table.setItem(row, 0, QTableWidgetItem(sales["date"]))
            self.total_sales_table.setItem(row, 1, QTableWidgetItem(f"₩{sales['total_sales']:,}"))

        # ✅ 기간별 전체 매출 그래프 업데이트
        self.update_total_sales_chart(total_sales)

    def update_employee_sales_chart(self, data):
        """
        직원별 매출 그래프 업데이트
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
        axis = QBarCategoryAxis()
        axis.append(categories)
        chart.setAxisX(axis, series)

        self.employee_sales_chart.setChart(chart)

    def update_total_sales_chart(self, data):
        """
        기간별 매출 그래프 업데이트
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
        axis = QBarCategoryAxis()
        axis.append(categories)
        chart.setAxisX(axis, series)

        self.total_sales_chart.setChart(chart)


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

        main_layout.addWidget(self.left_panel, 2)
        main_layout.addWidget(self.right_panel, 5)

        self.setLayout(main_layout)

    def load_sales_data(self, start_date, end_date):
        """
        FastAPI에서 직원별 및 기간별 매출 데이터 가져오기
        """
        headers = {"Authorization": f"Bearer {global_token}"}

        # ✅ 직원별 매출 API 호출
        employee_sales_url = f"http://127.0.0.1:8000/sales/employees?start_date={start_date}&end_date={end_date}"
        total_sales_url = f"http://127.0.0.1:8000/sales/total?start_date={start_date}&end_date={end_date}"

        try:
            emp_response = requests.get(employee_sales_url, headers=headers)
            total_response = requests.get(total_sales_url, headers=headers)

            emp_response.raise_for_status()
            total_response.raise_for_status()

            employee_sales = emp_response.json()
            total_sales = total_response.json()

            self.right_panel.update_sales_data(employee_sales, total_sales)

        except requests.RequestException as e:
            print(f"❌ 매출 데이터 조회 실패: {e}")

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QLabel, QComboBox, QLineEdit
import requests
from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import get_auth_headers
from PyQt5.QtWidgets import QSizePolicy
BASE_URL = "http://127.0.0.1:8000"  # 실제 서버 URL
global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)

class PaymentsLeftPanel(QWidget):
    """
    왼쪽 패널 - 직원 목록, 비율 조정, 조회 기능 (년도 & 월 선택 자유롭게, 비율 float 입력)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # ✅ 년도 선택 드롭다운 (최근 5년 ~ 향후 5년 선택 가능)
        self.year_selector = QComboBox()
        current_year = datetime.today().year
        years = [str(y) for y in range(current_year - 5, current_year + 6)]
        self.year_selector.addItems(years)

        # ✅ 월 선택 드롭다운 (1월 ~ 12월)
        self.month_selector = QComboBox()
        months = [str(m).zfill(2) for m in range(1, 13)]
        self.month_selector.addItems(months)

        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("📅 연도:"))
        date_layout.addWidget(self.year_selector)
        date_layout.addWidget(QLabel("🗓 월:"))
        date_layout.addWidget(self.month_selector)

        layout.addLayout(date_layout)

        # ✅ 직원 목록 + 비율 입력 (float 값 입력 가능)
        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(2)
        self.employee_table.setHorizontalHeaderLabels(["직원", "비율(%)"])
        self.employee_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("👥 직원별 급여 비율"))
        layout.addWidget(self.employee_table)

        # ✅ 조회 버튼
        self.search_button = QPushButton("📊 조회")
        self.search_button.clicked.connect(self.fetch_payments)
        layout.addWidget(self.search_button)

        self.setLayout(layout)

        # ✅ 직원 목록 불러오기
        self.load_employees()

    def load_employees(self):
        """
        직원 목록을 불러와 테이블에 추가 (비율 입력란을 float으로 변경)
        """
        global global_token
        url = "http://127.0.0.1:8000/employees/"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            employees = resp.json()
        except:
            employees = []

        self.employee_table.setRowCount(0)
        for emp in employees:
            row = self.employee_table.rowCount()
            self.employee_table.insertRow(row)
            self.employee_table.setItem(row, 0, QTableWidgetItem(emp["name"]))

            # ✅ 비율 입력란 (float 가능하도록 변경)
            percentage_input = QLineEdit()
            percentage_input.setPlaceholderText("8.0")  # 기본값 8%
            self.employee_table.setCellWidget(row, 1, percentage_input)

    def fetch_payments(self):
        """
        직원별 급여 계산 및 결과 전송
        """
        if self.parent_widget:
            selected_year = self.year_selector.currentText()
            selected_month = self.month_selector.currentText()
            selected_period = f"{selected_year}-{selected_month}"

            employee_ratios = {}

            for row in range(self.employee_table.rowCount()):
                name = self.employee_table.item(row, 0).text()
                percentage = self.employee_table.cellWidget(row, 1).text()

                try:
                    percentage = float(percentage)  # ✅ float 변환
                except ValueError:
                    percentage = 8.0  # 기본값 8.0%

                employee_ratios[name] = percentage

            self.parent_widget.load_payments(selected_period, employee_ratios)



class PaymentsRightPanel(QWidget):
    """
    오른쪽 패널 - 직원별 급여 테이블 (세부 정보 추가)
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.salary_table = QTableWidget()
        self.salary_table.setColumnCount(6)  # ✅ 컬럼 수 증가
        self.salary_table.setHorizontalHeaderLabels(["직원명", "월매출", "비율(%)", "인센티브", "계산과정", "월급"])
        self.salary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(QLabel("💰 직원별 급여 내역"))
        layout.addWidget(self.salary_table)

        self.setLayout(layout)

    def update_salary_data(self, salary_data):
        """
        직원별 급여 업데이트
        """
        self.salary_table.setRowCount(0)

        for emp, data in salary_data.items():
            row = self.salary_table.rowCount()
            self.salary_table.insertRow(row)

            monthly_sales = data.get("monthly_sales", 0)  # ✅ 월매출 (없으면 0)
            percentage = data.get("percentage", 8.0)  # ✅ 비율 (기본 8%)
            incentive = data.get("incentive", 0)  # ✅ 인센티브 (없으면 0)
            calculated_salary = round((monthly_sales * (percentage / 100)) + incentive, 2)  # ✅ 월급 계산
            calculation_process = f"({monthly_sales} × {percentage/100:.2f}) + {incentive}"  # ✅ 계산과정

            # ✅ 테이블에 값 추가
            self.salary_table.setItem(row, 0, QTableWidgetItem(emp))  # 직원명
            self.salary_table.setItem(row, 1, QTableWidgetItem(f"₩{monthly_sales:,.0f}"))  # 월매출
            self.salary_table.setItem(row, 2, QTableWidgetItem(f"{percentage:.1f}%"))  # 비율
            self.salary_table.setItem(row, 3, QTableWidgetItem(f"₩{incentive:,.0f}"))  # 인센티브
            self.salary_table.setItem(row, 4, QTableWidgetItem(calculation_process))  # 계산과정
            self.salary_table.setItem(row, 5, QTableWidgetItem(f"₩{calculated_salary:,.0f}"))  # 월급


class PaymentsTab(QWidget):
    """
    급여 관리 탭
    """
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        self.left_panel = PaymentsLeftPanel(self)
        self.right_panel = PaymentsRightPanel()
        # ✅ 크기 정책 설정
        self.left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ✅ 고정 크기 설정
        self.left_panel.setFixedWidth(350)  # 1 비율
        layout.addWidget(self.left_panel)
        layout.addWidget(self.right_panel)
        self.setLayout(layout)

    def load_payments(self, period, employee_ratios):
        """
        직원별 급여 계산 API 호출
        """
        global global_token
        year, month = period.split("-")
        url = f"http://127.0.0.1:8000/payments/salary/{year}/{int(month)}"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            salary_data = resp.json()  # ✅ FastAPI에서 반환한 Dict[str, float] 받음

            # ✅ 사용자 입력 비율 적용하여 최종 급여 계산
            final_salary_data = {}
            for name, base_salary in salary_data.items():
                percentage = employee_ratios.get(name, 8.0) / 100  # ✅ 사용자 입력 비율 적용
                final_salary_data[name] = round(base_salary * percentage, 2)

            self.right_panel.update_salary_data(final_salary_data)
        except Exception as e:
            print(f"❌ 급여 데이터 조회 실패: {e}")



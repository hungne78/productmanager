from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QLabel, QComboBox, QLineEdit, QMessageBox
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
    왼쪽 패널:
    - 연/월 선택
    - 직원 목록 + 급여 비율(%) 입력
    - 조회 버튼
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # (A) 연/월 선택
        date_layout = QHBoxLayout()
        self.year_combo = QComboBox()
        current_year = datetime.now().year
        for y in range(current_year - 5, current_year + 6):
            self.year_combo.addItem(str(y))

        self.month_combo = QComboBox()
        for m in range(1, 13):
            self.month_combo.addItem(str(m).zfill(2))

        date_layout.addWidget(QLabel("연도:"))
        date_layout.addWidget(self.year_combo)
        date_layout.addWidget(QLabel("월:"))
        date_layout.addWidget(self.month_combo)

        layout.addLayout(date_layout)

        # (B) 직원별 비율 입력 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["직원명", "급여 비율(%)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("직원별 급여 비율 설정"))
        layout.addWidget(self.table)

        # (C) 조회 버튼
        self.btn_search = QPushButton("조회")
        self.btn_search.clicked.connect(self.on_search)
        layout.addWidget(self.btn_search)

        self.setLayout(layout)

        # 직원 목록 로딩
        self.load_employees()

    def load_employees(self):
        """
        직원 목록을 /employees로부터 가져온 뒤, 테이블 행을 생성
        각 행마다 '직원명' 표시, '비율(%)'은 디폴트 8.0
        """
        global global_token
        url = f"{BASE_URL}/employees/"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            employees = resp.json()  # list[dict]
        except Exception as e:
            print(f"직원 목록 조회 실패: {e}")
            employees = []

        self.table.setRowCount(0)
        for emp in employees:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # (1) 직원명
            emp_name = emp.get("name", "")
            self.table.setItem(row, 0, QTableWidgetItem(emp_name))

            # (2) 비율 입력칸 (default 8.0)
            line_edit = QLineEdit()
            line_edit.setText("8.0")  # 기본값
            self.table.setCellWidget(row, 1, line_edit)

    def on_search(self):
        """
        '조회' 버튼 클릭 → year, month, 각 직원별 비율을 가져와
        parent_widget.load_payments(...) 호출
        """
        if not self.parent_widget:
            return

        sel_year = self.year_combo.currentText()
        sel_month = self.month_combo.currentText()

        try:
            year = int(sel_year)
            month = int(sel_month)
        except ValueError:
            QMessageBox.warning(self, "주의", "연도/월이 숫자가 아닙니다.")
            return

        # 직원별 비율 dict
        ratio_dict = {}
        row_count = self.table.rowCount()
        for row in range(row_count):
            emp_item = self.table.item(row, 0)
            if not emp_item:
                continue
            emp_name = emp_item.text()

            widget = self.table.cellWidget(row, 1)
            ratio_str = widget.text() if widget else "8.0"
            try:
                ratio_val = float(ratio_str)
            except ValueError:
                ratio_val = 8.0

            ratio_dict[emp_name] = ratio_val

        # 부모로 넘김
        self.parent_widget.load_payments(year, month, ratio_dict)


class PaymentsRightPanel(QWidget):
    """
    오른쪽 패널:
    - 테이블에 (직원명 / 월매출 / 비율 / 계산식 / 결과) 표시
    - 인센티브 = 월매출 × (비율/100)
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["직원명", "월매출", "비율(%)", "계산식", "급여/인센티브"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(QLabel("직원별 계산 결과"))
        layout.addWidget(self.table)

        self.setLayout(layout)

    def update_data(self, monthly_sales: dict, ratio_dict: dict):
        """
        monthly_sales: { 직원명: 월매출 }
        ratio_dict: { 직원명: 비율(%) }
        계산 = 월매출 × (비율/100)
        """
        self.table.setRowCount(0)

        for emp_name, sales_amt in monthly_sales.items():
            row = self.table.rowCount()
            self.table.insertRow(row)

            # 1) 직원명
            self.table.setItem(row, 0, QTableWidgetItem(emp_name))
            # 2) 월매출 (ex: 200000)
            sales_val = float(sales_amt or 0)
            self.table.setItem(row, 1, QTableWidgetItem(f"{sales_val:,.0f}"))

            # 3) 비율(%) (없으면 8%)
            ratio_val = ratio_dict.get(emp_name, 8.0)
            self.table.setItem(row, 2, QTableWidgetItem(f"{ratio_val:.1f}%"))

            # 4) 계산식
            calc_expr = f"{sales_val:,.0f} × {ratio_val/100:.3f}"
            self.table.setItem(row, 3, QTableWidgetItem(calc_expr))

            # 5) 최종 인센티브/급여
            final_pay = round(sales_val * (ratio_val/100), 2)
            self.table.setItem(row, 4, QTableWidgetItem(f"{final_pay:,.0f}"))


class PaymentsTab(QWidget):
    """
    메인 탭
    - 왼쪽 패널(PaymentsLeftPanel) / 오른쪽 패널(PaymentsRightPanel)
    """
    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout()

        self.left_panel = PaymentsLeftPanel(self)
        self.right_panel = PaymentsRightPanel()

        self.left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.left_panel.setFixedWidth(350)

        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)

        self.setLayout(main_layout)

    def load_payments(self, year: int, month: int, ratio_dict: dict):
        """
        왼쪽에서 (연/월, 직원별 비율 dict) 전달 → 이 메서드에서
        1) GET /payments/salary/{year}/{month} 호출 (월매출 dict)
        2) 오른쪽 패널 update_data(월매출, ratio_dict) 호출
        """
        global global_token
        url = f"{BASE_URL}/payments/salary/{year}/{month}"
        headers = {"Authorization": f"Bearer {global_token}"}
        
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            monthly_sales = resp.json()  # { "김영업": 500000, "이사원": 300000, ...}
        except Exception as e:
            QMessageBox.critical(self, "오류", f"급여 계산 실패: {str(e)}")
            return

        # 오른쪽 패널에 업데이트 (월매출 + 사용자가 입력한 ratio_dict)
        self.right_panel.update_data(monthly_sales, ratio_dict)

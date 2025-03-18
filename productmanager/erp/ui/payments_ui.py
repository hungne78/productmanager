from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QComboBox, QLineEdit,
    QMessageBox, QSizePolicy
)
import os
import json
from datetime import datetime
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

### 추가: api_services 임포트
from services.api_services import (
    get_auth_headers,
    api_fetch_employees,
    api_fetch_monthly_sales,
    api_fetch_incentives
)

BASE_URL = "http://127.0.0.1:8000"  # 실제 서버 URL (사용 안 할 수도 있음)
global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)

### (A) 직원 비율 로컬 파일
RATIO_FILE = "ratio_data.json"

def load_ratio_data() -> dict:
    """로컬 JSON에서 {직원명: 비율}을 로딩"""
    if not os.path.exists(RATIO_FILE):
        return {}
    try:
        with open(RATIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[load_ratio_data] 실패: {e}")
        return {}

def save_ratio_data(ratio_dict: dict):
    """로컬 JSON에 {직원명: 비율} 저장"""
    try:
        with open(RATIO_FILE, "w", encoding="utf-8") as f:
            json.dump(ratio_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[save_ratio_data] 실패: {e}")


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
        current_month = datetime.now().month
        for y in range(current_year - 5, current_year + 6):
            self.year_combo.addItem(str(y))

        self.month_combo = QComboBox()
        for m in range(1, 13):
            self.month_combo.addItem(str(m).zfill(2))

        # ✅ 기본값을 현재 연도/월로 설정
        self.year_combo.setCurrentText(str(current_year))
        self.month_combo.setCurrentText(str(current_month).zfill(2))


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
        직원 목록을 api_services.api_fetch_employees()로부터 가져온 뒤, 테이블 행을 생성
        각 행마다 '직원명' 표시, '비율(%)'은 로컬파일에서 읽어온 값을 우선 (기본 8.0)
        """
        # 토큰 획득
        token_headers = global_token()
        token_str = token_headers.get("Authorization", "").replace("Bearer ", "")

        try:
            employees = api_fetch_employees(token_str)  # list[dict], [{'id':..., 'name':...}, ...]
        except Exception as e:
            print(f"직원 목록 조회 실패: {e}")
            employees = []

        # 로컬 파일에서 저장된 직원 비율을 불러옴
        saved_ratios = load_ratio_data()

        self.table.setRowCount(0)
        for emp in employees:
            row = self.table.rowCount()
            self.table.insertRow(row)

            emp_name = emp.get("name", "")

            self.table.setItem(row, 0, QTableWidgetItem(emp_name))

            # default ratio (기본 8.0) or saved_ratios
            ratio_val = saved_ratios.get(emp_name, 8.0)
            line_edit = QLineEdit()
            line_edit.setText(str(ratio_val))
            self.table.setCellWidget(row, 1, line_edit)

    def on_search(self):
        """
        '조회' 버튼 클릭
        → year, month, 각 직원별 비율을 가져와 JSON파일 저장
        → parent_widget.load_payments(...) 호출
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

        # 로컬 파일에 저장
        save_ratio_data(ratio_dict)

        # 부모(메인 탭)으로 넘김
        self.parent_widget.load_payments(year, month, ratio_dict)


class PaymentsRightPanel(QWidget):
    """
    오른쪽 패널:
    - 테이블에 (직원명 / 월매출 / 비율 / 계산식 / 결과) 표시
    - (인센티브 포함) 급여 = 월매출 × (비율/100) + 인센티브합
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

    def update_data(self, monthly_sales: dict, ratio_dict: dict, incentives: dict):
        """
        monthly_sales: { "김영업": 500000, "이사원": 300000, ...}
        ratio_dict   : { "김영업": 8.0,     "이사원": 10.0, ...}
        incentives   : { "김영업": 20000,   "이사원": 5000, ...}

        최종 급여 = 월매출 × (비율/100) + 인센티브
        """
        self.table.setRowCount(0)

        # 직원명을 합쳐서 loop
        all_names = set(monthly_sales.keys()) | set(incentives.keys()) | set(ratio_dict.keys())
        for emp_name in sorted(all_names):
            row = self.table.rowCount()
            self.table.insertRow(row)

            # (1) 직원명
            self.table.setItem(row, 0, QTableWidgetItem(emp_name))

            # (2) 월매출
            sales_val = float(monthly_sales.get(emp_name, 0))
            self.table.setItem(row, 1, QTableWidgetItem(f"{sales_val:,.0f}"))

            # (3) 비율
            ratio_val = float(ratio_dict.get(emp_name, 8.0))
            self.table.setItem(row, 2, QTableWidgetItem(f"{ratio_val:.1f}%"))

            # (4) 계산식
            incentive_val = float(incentives.get(emp_name, 0))
            calc_expr = f"{sales_val:,.0f} × {ratio_val/100:.3f} + {incentive_val:,.0f}"
            self.table.setItem(row, 3, QTableWidgetItem(calc_expr))

            # (5) 최종 급여
            final_pay = round(sales_val*(ratio_val/100) + incentive_val, 2)
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
        왼쪽에서 (연/월, 직원별 비율 dict) 받음
        → api_services를 통해 월매출 + 인센티브 조회
        → 오른쪽 패널로 전달
        """
        # 토큰 추출
        token_headers = global_token()
        token_str = token_headers.get("Authorization", "").replace("Bearer ", "")

        # (1) 월매출 불러오기
        monthly_sales = api_fetch_monthly_sales(year, month, token_str)

        # (2) 인센티브 불러오기
        incentives = api_fetch_incentives(year, month, token_str)

        # (3) 오른쪽 패널 업데이트
        self.right_panel.update_data(monthly_sales, ratio_dict, incentives)

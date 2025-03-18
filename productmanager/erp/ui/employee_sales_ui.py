# employee_monthly_sales_tab.py

import sys
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QSizePolicy
)
from PyQt5.QtCore import Qt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# api_services import
from services.api_services import (
    get_auth_headers,
    api_fetch_employees,
    api_fetch_monthly_sales_with_prev_and_last_year
)

class EmployeeSalesTab(QWidget):
    """
    - 왼쪽: 직원/연/월 선택
    - 오른쪽: [거래처명] + [1..31] + [월매출, 전월매출, 전년도매출] (총 35열)
    - 창이 작으면 스크롤, 창이 커지면 오른쪽 여백 없이 확장
    """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        # 왼쪽 패널 (검색)
        self.left_panel = QGroupBox("검색 옵션")
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)

        # (1) 연도 선택
        self.label_year = QLabel("조회 연도:")
        self.year_combo = QComboBox()
        current_year = datetime.now().year
        for y in range(current_year, current_year - 10, -1):
            self.year_combo.addItem(str(y))

        # (2) 월 선택
        self.label_month = QLabel("조회 월:")
        self.month_combo = QComboBox()
        for m in range(1, 13):
            self.month_combo.addItem(f"{m}월", m)

        # (3) 직원 선택
        self.label_employee = QLabel("직원 선택:")
        self.employee_combo = QComboBox()
        self.load_employees()

        # (4) 조회 버튼
        self.search_button = QPushButton("조회")
        self.search_button.clicked.connect(self.on_search)

        left_layout.addWidget(self.label_year)
        left_layout.addWidget(self.year_combo)
        left_layout.addWidget(self.label_month)
        left_layout.addWidget(self.month_combo)
        left_layout.addWidget(self.label_employee)
        left_layout.addWidget(self.employee_combo)
        left_layout.addWidget(self.search_button)
        self.left_panel.setLayout(left_layout)
        self.left_panel.setFixedWidth(300)

        # 오른쪽 패널 (테이블)
        self.right_panel = QWidget()
        right_layout = QVBoxLayout()

        col_count = 1 + 31 + 3  # 거래처명 + 31일 + (월/전월/전년도)
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(col_count)
        
        # 테이블 헤더
        headers = (
            ["거래처명"]
            + [f"{d}일" for d in range(1, 32)]
            + ["월매출", "전월매출", "전년도매출"]
        )
        self.sales_table.setHorizontalHeaderLabels(headers)

        # (★) 스크롤 + 확장 설정
        # 1) 모든 컬럼은 기본적으로 ResizeToContents (혹은 Interactive)
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # 2) 마지막 컬럼은 스트레치 (창이 남으면 확장, 모자라면 스크롤)
        #    또는 setStretchLastSection(True)도 비슷한 효과
        #    단, 이때 '전년도매출'이 마지막 컬럼이라서 확장됨.
        self.sales_table.horizontalHeader().setStretchLastSection(True)

        # (★) 테이블 자체도 Expand 가능하도록
        self.sales_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # (★) 수평/수직 스크롤바는 필요 시 나타나도록
        # 기본값도 AsNeeded이지만, 명시하면 더 분명
        self.sales_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.sales_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # QScrollArea로 감싸기
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.sales_table)
        scroll_area.setWidgetResizable(True)

        right_layout.addWidget(scroll_area)
        self.right_panel.setLayout(right_layout)

        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)
        self.setLayout(main_layout)

    def load_employees(self):
        token_headers = get_auth_headers()
        token_str = token_headers.get("Authorization", "").replace("Bearer ", "")
        employees = api_fetch_employees(token_str)
        self.employee_combo.clear()
        self.employee_combo.addItem("직원 선택", None)
        for emp in employees:
            emp_id = emp.get("id")
            name = emp.get("name", "")
            self.employee_combo.addItem(f"{name} (ID:{emp_id})", emp_id)

    def on_search(self):
        token_headers = get_auth_headers()
        token_str = token_headers.get("Authorization", "").replace("Bearer ", "")

        emp_id = self.employee_combo.currentData()
        if emp_id is None:
            print("직원이 선택되지 않았습니다.")
            return

        try:
            year = int(self.year_combo.currentText())
        except:
            print("연도 선택 오류")
            return

        month = self.month_combo.currentData()  # 1..12

        # 한 번에 현재/전월/전년도 계산 + 1..31일
        data_list = api_fetch_monthly_sales_with_prev_and_last_year(
            token_str, emp_id, year, month
        )
        self.update_sales_table(data_list)

    def update_sales_table(self, data_list):
        """
        data_list 예시:
        [
          {
            "client_name": "홍길동상회",
            "1": 10, "2": 20, ..., "31": 5,
            "monthly_sales": 500000,
            "prev_month_sales": 300000,
            "last_year_sales": 800000
          },
          ...
        ]
        """
        self.sales_table.setRowCount(len(data_list))

        for row_idx, row_data in enumerate(data_list):
            cname = row_data.get("client_name", "")
            daily_vals = [row_data.get(str(d), 0) for d in range(1,32)]
            monthly_sales = row_data.get("monthly_sales", 0)
            prev_sales    = row_data.get("prev_month_sales", 0)
            last_sales    = row_data.get("last_year_sales", 0)

            col_idx = 0
            # 거래처명
            self.sales_table.setItem(row_idx, col_idx, QTableWidgetItem(str(cname)))
            col_idx += 1

            # 1..31
            for val in daily_vals:
                self.sales_table.setItem(row_idx, col_idx, QTableWidgetItem(str(val)))
                col_idx += 1

            # 월매출
            self.sales_table.setItem(row_idx, col_idx, QTableWidgetItem(str(monthly_sales)))
            col_idx += 1

            # 전월매출
            self.sales_table.setItem(row_idx, col_idx, QTableWidgetItem(str(prev_sales)))
            col_idx += 1

            # 전년도매출
            self.sales_table.setItem(row_idx, col_idx, QTableWidgetItem(str(last_sales)))
            col_idx += 1

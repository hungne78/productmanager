import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QSizePolicy, QDialog
)
from PyQt5.QtCore import Qt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ✅ API 서비스 호출 함수 가져오기
from services.api_services import (
    get_auth_headers,
    api_fetch_employees,
    api_fetch_employee_inventory
)

class EmployeeVehicleInventoryTab(QWidget):
    """
    - 왼쪽: 직원 선택
    - 오른쪽: 차량 재고 조회
    - 아래: "인쇄" 버튼
    """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        # ✅ 왼쪽 패널 (직원 선택)
        self.left_panel = QGroupBox("직원 선택")
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)

        # (1) 직원 선택 드롭다운
        self.label_employee = QLabel("직원 선택:")
        self.employee_combo = QComboBox()
        self.load_employees()

        # (2) 조회 버튼
        self.search_button = QPushButton("조회")
        self.search_button.clicked.connect(self.on_search)

        left_layout.addWidget(self.label_employee)
        left_layout.addWidget(self.employee_combo)
        left_layout.addWidget(self.search_button)
        self.left_panel.setLayout(left_layout)
        self.left_panel.setFixedWidth(300)

        # ✅ 오른쪽 패널 (재고 테이블)
        self.right_panel = QWidget()
        right_layout = QVBoxLayout()

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(4)  # 상품명, 분류, 재고 수량
        self.inventory_table.setHorizontalHeaderLabels(["상품명", "분류", "재고 수량"])

        # 🔹 컬럼 설정: ResizeToContents + 마지막 컬럼은 확장
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.inventory_table.horizontalHeader().setStretchLastSection(True)

        # 🔹 수평 스크롤 및 가변 크기 적용
        self.inventory_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ✅ 스크롤 추가
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.inventory_table)
        scroll_area.setWidgetResizable(True)

        right_layout.addWidget(scroll_area)
        self.right_panel.setLayout(right_layout)

        # ✅ 인쇄 버튼 추가 (아래쪽)
        self.print_button = QPushButton("인쇄")
        self.print_button.clicked.connect(self.print_inventory)
        right_layout.addWidget(self.print_button)

        # ✅ 레이아웃 배치
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)
        self.setLayout(main_layout)

    def load_employees(self):
        """ 직원 목록 로드 """
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
        """ 선택된 직원의 차량 재고 조회 """
        token_headers = get_auth_headers()
        token_str = token_headers.get("Authorization", "").replace("Bearer ", "")

        emp_id = self.employee_combo.currentData()
        if emp_id is None:
            print("직원이 선택되지 않았습니다.")
            return

        # ✅ 차량 재고 API 호출
        inventory_list = api_fetch_employee_inventory(token_str, emp_id)
        self.update_inventory_table(inventory_list)

    def update_inventory_table(self, inventory_list):
        """
        - inventory_list 예시:
        [
          {"product_name": "초코 아이스크림", "category": "아이스크림", "quantity": 50},
          {"product_name": "바닐라 아이스크림", "category": "아이스크림", "quantity": 30},
          ...
        ]
        """
        self.inventory_table.setRowCount(len(inventory_list))

        for row_idx, item in enumerate(inventory_list):
            product_name = item.get("product_name", "")
            category = item.get("category", "미분류")
            quantity = item.get("quantity", 0)

            # 데이터 삽입
            self.inventory_table.setItem(row_idx, 0, QTableWidgetItem(str(product_name)))
            self.inventory_table.setItem(row_idx, 1, QTableWidgetItem(str(category)))
            self.inventory_table.setItem(row_idx, 2, QTableWidgetItem(str(quantity)))

    def print_inventory(self):
        """ 차량 재고 인쇄 기능 (단순히 확인 다이얼로그 출력) """
        print_data = []
        row_count = self.inventory_table.rowCount()
        for row in range(row_count):
            product_name = self.inventory_table.item(row, 0).text()
            category = self.inventory_table.item(row, 1).text()
            quantity = self.inventory_table.item(row, 2).text()
            print_data.append(f"{product_name} ({category}): {quantity} 개")

        inventory_text = "\n".join(print_data)
        dialog = QDialog(self)
        dialog.setWindowTitle("재고 출력 미리보기")
        dialog.resize(400, 300)
        layout = QVBoxLayout()
        label = QLabel(f"🚗 차량 재고 목록\n\n{inventory_text}")
        layout.addWidget(label)
        btn_close = QPushButton("닫기")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)
        dialog.setLayout(layout)
        dialog.exec_()

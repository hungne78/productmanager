import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QSizePolicy, QDialog
)
from PyQt5.QtGui import QTextDocument
from PyQt5.QtCore import Qt
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter  # ✅ 여기서 import 해야 함
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
        self.selected_employee_name = "선택된 직원 없음"
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
        self.inventory_table.setColumnCount(7)  # 상품명, 분류, 박스당 개수, 상품 가격, 박스 가격, 차량 재고, 총 가격
        self.inventory_table.setHorizontalHeaderLabels(
            ["상품명", "분류", "박스당 개수", "상품 가격", "박스 가격", "차량 재고", "총 가격"]
        )

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

        # ✅ 총 박스 수 및 총 가격 합계 표시
        self.total_boxes_label = QLabel("📦 총 박스 수: 0")
        self.total_price_label = QLabel("💰 총 가격 합: 0 원")

        right_layout.addWidget(self.total_boxes_label)
        right_layout.addWidget(self.total_price_label)

        # ✅ 인쇄 버튼 추가
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
        emp_name = self.employee_combo.currentText() 
        if emp_id is None:
            print("직원이 선택되지 않았습니다.")
            return
        self.selected_employee_name = emp_name 
        
        # ✅ 차량 재고 API 호출
        inventory_list = api_fetch_employee_inventory(token_str, emp_id)
        self.update_inventory_table(inventory_list)

    def update_inventory_table(self, inventory_list):
        self.inventory_table.setRowCount(len(inventory_list))

        total_boxes = 0
        total_price = 0

        for row_idx, item in enumerate(inventory_list):
            product_name = item.get("product_name", "")
            category = item.get("category", "미분류")
            box_quantity = item.get("box_quantity", 1)  # 박스당 개수
            product_price = item.get("price", 0)  # 개당 가격
            vehicle_stock = item.get("quantity", 0)  # 차량 재고

            # ✅ 박스 가격 = 상품 가격 * 박스당 개수
            box_price = product_price * box_quantity

            # ✅ 총 가격 = 박스 가격 * 차량 재고
            total_item_price = box_price * vehicle_stock

            # ✅ 합계 계산
            total_boxes += vehicle_stock
            total_price += total_item_price

            # 데이터 삽입
            self.inventory_table.setItem(row_idx, 0, QTableWidgetItem(str(product_name)))
            self.inventory_table.setItem(row_idx, 1, QTableWidgetItem(str(category)))
            self.inventory_table.setItem(row_idx, 2, QTableWidgetItem(str(box_quantity)))
            self.inventory_table.setItem(row_idx, 3, QTableWidgetItem(f"{product_price:,} 원"))
            self.inventory_table.setItem(row_idx, 4, QTableWidgetItem(f"{box_price:,} 원"))
            self.inventory_table.setItem(row_idx, 5, QTableWidgetItem(str(vehicle_stock)))
            self.inventory_table.setItem(row_idx, 6, QTableWidgetItem(f"{total_item_price:,} 원"))

        # ✅ 총 박스 수 및 총 가격 갱신
        self.total_boxes_label.setText(f"📦 총 박스 수: {total_boxes}")
        self.total_price_label.setText(f"💰 총 가격 합: {total_price:,} 원")

    def print_inventory(self):
        """ 직원 차량 재고 프린트 기능 """
        printer = QPrinter(QPrinter.HighResolution)
        print_dialog = QPrintDialog(printer, self)

        if print_dialog.exec_() == QPrintDialog.Accepted:
            document = QTextDocument()
            text = f"<h2>🚗 {self.selected_employee_name} 차량 재고 목록</h2>"

            # ✅ 테이블 데이터 수집
            row_count = self.inventory_table.rowCount()
            text += "<table border='1' width='100%' cellpadding='5'><tr>"
            headers = ["상품명", "분류", "박스당 개수", "상품 가격", "박스 가격", "차량 재고", "총 가격"]
            for header in headers:
                text += f"<th>{header}</th>"
            text += "</tr>"

            for row in range(row_count):
                text += "<tr>"
                for col in range(7):
                    item = self.inventory_table.item(row, col)
                    text += f"<td>{item.text() if item else ''}</td>"
                text += "</tr>"
            text += "</table>"

            # ✅ 합계 정보 추가
            text += f"<h3>{self.total_boxes_label.text()}</h3>"
            text += f"<h3>{self.total_price_label.text()}</h3>"

            document.setHtml(text)
            document.print_(printer)

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel, QComboBox
import sys
import os

# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_orders, api_create_order, api_update_order, api_delete_order


class OrderLeftPanel(QWidget):
    """ 주문 상세 정보 및 조작 패널 (왼쪽 패널) """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.id_edit = QLineEdit()
        self.client_edit = QLineEdit()
        self.employee_edit = QLineEdit()
        self.status_combo = QComboBox()
        self.status_combo.addItems(["pending", "confirmed", "shipped", "delivered", "canceled"])
        self.total_edit = QLineEdit()

        form_layout.addRow("주문 ID:", self.id_edit)
        form_layout.addRow("고객 ID:", self.client_edit)
        form_layout.addRow("직원 ID:", self.employee_edit)
        form_layout.addRow("주문 상태:", self.status_combo)
        form_layout.addRow("총 금액:", self.total_edit)

        self.id_edit.setReadOnly(True)  # ID는 수정 불가

        layout.addLayout(form_layout)

        self.btn_add = QPushButton("신규 등록")
        self.btn_edit = QPushButton("수정")
        self.btn_delete = QPushButton("삭제")

        layout.addWidget(self.btn_add)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_delete)

        self.btn_add.clicked.connect(self.add_order)
        self.btn_edit.clicked.connect(self.edit_order)
        self.btn_delete.clicked.connect(self.delete_order)

        self.setLayout(layout)

    def display_order(self, order):
        """ 검색된 주문 정보를 왼쪽 패널에 표시 """
        self.id_edit.setText(str(order.get("id", "")))
        self.client_edit.setText(str(order.get("client_id", "")))
        self.employee_edit.setText(str(order.get("employee_id", "")))
        self.status_combo.setCurrentText(order.get("status", "pending"))
        self.total_edit.setText(str(order.get("total_amount", 0)))

    def add_order(self):
        client_id = self.client_edit.text().strip()
        employee_id = self.employee_edit.text().strip()
        status = self.status_combo.currentText()
        total = self.total_edit.text().strip()

        if not client_id or not employee_id:
            QMessageBox.warning(self, "경고", "고객 ID와 직원 ID를 입력하세요.")
            return

        data = {
            "client_id": int(client_id),
            "employee_id": int(employee_id),
            "status": status,
            "total_amount": float(total or 0),
            "items": []  # 기본적으로 빈 주문으로 생성
        }
        response = api_create_order(data)
        if response and response.status_code in [200, 201]:
            QMessageBox.information(self, "성공", "주문이 추가되었습니다.")

    def edit_order(self):
        order_id = self.id_edit.text().strip()
        status = self.status_combo.currentText()

        if not order_id:
            QMessageBox.warning(self, "경고", "수정할 주문을 선택하세요.")
            return

        data = {"status": status}
        response = api_update_order(order_id, data)
        if response and response.status_code == 200:
            QMessageBox.information(self, "성공", "주문 정보가 수정되었습니다.")

    def delete_order(self):
        order_id = self.id_edit.text().strip()
        if not order_id:
            QMessageBox.warning(self, "경고", "삭제할 주문을 선택하세요.")
            return

        confirm = QMessageBox.question(self, "삭제 확인", f"정말 주문 ID {order_id}를 삭제하시겠습니까?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            response = api_delete_order(order_id)
            if response and response.status_code == 200:
                QMessageBox.information(self, "성공", "주문이 삭제되었습니다.")


class OrderRightPanel(QWidget):
    """ 주문의 상세 품목 및 상태 정보 (오른쪽 패널) """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["상품 ID", "수량", "단가", "합계"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(QLabel("주문 상세 품목"))
        layout.addWidget(self.items_table)

        self.setLayout(layout)

    def update_order_items(self, items):
        """ 주문별 상세 품목 데이터 표시 """
        self.items_table.setRowCount(0)
        for item in items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            self.items_table.setItem(row, 0, QTableWidgetItem(str(item.get("product_id", ""))))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(item.get("quantity", ""))))
            self.items_table.setItem(row, 2, QTableWidgetItem(str(item.get("unit_price", ""))))
            self.items_table.setItem(row, 3, QTableWidgetItem(str(item.get("line_total", ""))))


class OrdersTab(QWidget):
    """ 주문 관리 메인 탭 """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.left_panel = OrderLeftPanel()
        self.right_panel = OrderRightPanel()

        main_layout.addWidget(self.left_panel, 2)  # 주문 정보 (좌)
        main_layout.addWidget(self.right_panel, 3)  # 상세 품목 및 상태 (우)

        self.setLayout(main_layout)

        self.load_orders()

    def load_orders(self):
        """ 주문 목록을 가져와 테이블에 로드 """
        orders = api_fetch_orders()
        if orders:
            first_order = orders[0]
            self.left_panel.display_order(first_order)
            self.right_panel.update_order_items(first_order.get("order_items", []))

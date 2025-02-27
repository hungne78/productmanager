from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel, QComboBox, QSpinBox
import sys
import os

# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_purchases, api_create_purchase, api_update_purchase, api_delete_purchase


class PurchaseLeftPanel(QWidget):
    """ 매입 상세 정보 및 조작 패널 (왼쪽 패널) """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.id_edit = QLineEdit()
        self.supplier_edit = QLineEdit()
        self.product_edit = QLineEdit()
        self.quantity_edit = QSpinBox()
        self.quantity_edit.setMinimum(1)
        self.unit_price_edit = QLineEdit()
        self.total_price_edit = QLineEdit()

        form_layout.addRow("매입 ID:", self.id_edit)
        form_layout.addRow("공급업체 ID:", self.supplier_edit)
        form_layout.addRow("상품 ID:", self.product_edit)
        form_layout.addRow("수량:", self.quantity_edit)
        form_layout.addRow("단가:", self.unit_price_edit)
        form_layout.addRow("총액:", self.total_price_edit)

        self.id_edit.setReadOnly(True)  # ID는 수정 불가
        self.total_price_edit.setReadOnly(True)  # 총액은 자동 계산됨

        layout.addLayout(form_layout)

        self.btn_add = QPushButton("신규 등록")
        self.btn_edit = QPushButton("수정")
        self.btn_delete = QPushButton("삭제")

        layout.addWidget(self.btn_add)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_delete)

        self.btn_add.clicked.connect(self.add_purchase)
        self.btn_edit.clicked.connect(self.edit_purchase)
        self.btn_delete.clicked.connect(self.delete_purchase)
        self.quantity_edit.valueChanged.connect(self.update_total_price)
        self.unit_price_edit.textChanged.connect(self.update_total_price)

        self.setLayout(layout)

    def display_purchase(self, purchase):
        """ 검색된 매입 정보를 왼쪽 패널에 표시 """
        self.id_edit.setText(str(purchase.get("id", "")))
        self.supplier_edit.setText(str(purchase.get("supplier_id", "")))
        self.product_edit.setText(str(purchase.get("product_id", "")))
        self.quantity_edit.setValue(int(purchase.get("quantity", 1)))
        self.unit_price_edit.setText(str(purchase.get("unit_price", 0)))
        self.total_price_edit.setText(str(purchase.get("total_amount", 0)))

    def update_total_price(self):
        """ 수량과 단가 변경 시 총액 자동 계산 """
        try:
            quantity = self.quantity_edit.value()
            unit_price = float(self.unit_price_edit.text() or 0)
            self.total_price_edit.setText(str(quantity * unit_price))
        except ValueError:
            self.total_price_edit.setText("0")

    def add_purchase(self):
        supplier_id = self.supplier_edit.text().strip()
        product_id = self.product_edit.text().strip()
        quantity = self.quantity_edit.value()
        unit_price = float(self.unit_price_edit.text().strip() or 0)
        total_price = quantity * unit_price

        if not supplier_id or not product_id:
            QMessageBox.warning(self, "경고", "공급업체 ID와 상품 ID를 입력하세요.")
            return

        data = {
            "supplier_id": int(supplier_id),
            "product_id": int(product_id),
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": total_price
        }
        response = api_create_purchase(data)
        if response and response.status_code in [200, 201]:
            QMessageBox.information(self, "성공", "매입이 추가되었습니다.")

    def edit_purchase(self):
        purchase_id = self.id_edit.text().strip()
        quantity = self.quantity_edit.value()
        unit_price = float(self.unit_price_edit.text().strip() or 0)
        total_price = quantity * unit_price

        if not purchase_id:
            QMessageBox.warning(self, "경고", "수정할 매입을 선택하세요.")
            return

        data = {
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": total_price
        }
        response = api_update_purchase(purchase_id, data)
        if response and response.status_code == 200:
            QMessageBox.information(self, "성공", "매입 정보가 수정되었습니다.")

    def delete_purchase(self):
        purchase_id = self.id_edit.text().strip()
        if not purchase_id:
            QMessageBox.warning(self, "경고", "삭제할 매입을 선택하세요.")
            return

        confirm = QMessageBox.question(self, "삭제 확인", f"정말 매입 ID {purchase_id}를 삭제하시겠습니까?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            response = api_delete_purchase(purchase_id)
            if response and response.status_code == 200:
                QMessageBox.information(self, "성공", "매입이 삭제되었습니다.")


class PurchaseRightPanel(QWidget):
    """ 매입의 상세 품목 및 재고 변화 정보 (오른쪽 패널) """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(2)
        self.stock_table.setHorizontalHeaderLabels(["월", "재고 변화"])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.purchase_table = QTableWidget()
        self.purchase_table.setColumnCount(2)
        self.purchase_table.setHorizontalHeaderLabels(["월", "매입량"])
        self.purchase_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(QLabel("월별 재고 변화"))
        layout.addWidget(self.stock_table)
        layout.addWidget(QLabel("월별 매입량"))
        layout.addWidget(self.purchase_table)

        self.setLayout(layout)

    def update_stock_data(self, stock_data):
        """ 상품별 월별 재고 데이터 표시 """
        self.stock_table.setRowCount(0)
        for month, amount in stock_data.items():
            row = self.stock_table.rowCount()
            self.stock_table.insertRow(row)
            self.stock_table.setItem(row, 0, QTableWidgetItem(month))
            self.stock_table.setItem(row, 1, QTableWidgetItem(str(amount)))

    def update_purchase_data(self, purchase_data):
        """ 상품별 월별 매입량 표시 """
        self.purchase_table.setRowCount(0)
        for month, purchases in purchase_data.items():
            row = self.purchase_table.rowCount()
            self.purchase_table.insertRow(row)
            self.purchase_table.setItem(row, 0, QTableWidgetItem(month))
            self.purchase_table.setItem(row, 1, QTableWidgetItem(str(purchases)))


class PurchaseTab(QWidget):
    """ 매입 관리 메인 탭 """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.left_panel = PurchaseLeftPanel()
        self.right_panel = PurchaseRightPanel()

        main_layout.addWidget(self.left_panel, 2)  # 매입 정보 (좌)
        main_layout.addWidget(self.right_panel, 3)  # 재고 및 매입량 (우)

        self.setLayout(main_layout)

        self.load_purchases()

    def load_purchases(self):
        """ 매입 목록을 가져와 테이블에 로드 """
        purchases = api_fetch_purchases()
        if purchases:
            first_purchase = purchases[0]
            self.left_panel.display_purchase(first_purchase)

            # 테스트용 데이터
            sample_stock_data = {"1월": 300, "2월": 400, "3월": 500}
            sample_purchase_data = {"1월": 50, "2월": 60, "3월": 70}
            self.right_panel.update_stock_data(sample_stock_data)
            self.right_panel.update_purchase_data(sample_purchase_data)

    
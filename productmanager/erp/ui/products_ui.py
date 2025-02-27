from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel
import sys
import os

# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_products, api_create_product, api_update_product, api_delete_product


class ProductLeftPanel(QWidget):
    """ 상품 상세 정보 및 조작 패널 (왼쪽 패널) """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.id_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.barcode_edit = QLineEdit()
        self.price_edit = QLineEdit()
        self.stock_edit = QLineEdit()

        form_layout.addRow("ID:", self.id_edit)
        form_layout.addRow("상품명:", self.name_edit)
        form_layout.addRow("바코드:", self.barcode_edit)
        form_layout.addRow("가격:", self.price_edit)
        form_layout.addRow("재고:", self.stock_edit)

        self.id_edit.setReadOnly(True)  # ID는 수정 불가

        layout.addLayout(form_layout)

        self.btn_add = QPushButton("신규 등록")
        self.btn_edit = QPushButton("수정")
        self.btn_delete = QPushButton("삭제")

        layout.addWidget(self.btn_add)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_delete)

        self.btn_add.clicked.connect(self.add_product)
        self.btn_edit.clicked.connect(self.edit_product)
        self.btn_delete.clicked.connect(self.delete_product)

        self.setLayout(layout)

    def display_product(self, product):
        """ 검색된 상품 정보를 왼쪽 패널에 표시 """
        self.id_edit.setText(str(product.get("id", "")))
        self.name_edit.setText(product.get("product_name", ""))
        self.barcode_edit.setText(product.get("barcode", ""))
        self.price_edit.setText(str(product.get("default_price", 0)))
        self.stock_edit.setText(str(product.get("stock", 0)))

    def add_product(self):
        name = self.name_edit.text().strip()
        barcode = self.barcode_edit.text().strip()
        price = self.price_edit.text().strip()
        stock = self.stock_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "경고", "상품명을 입력하세요.")
            return

        data = {
            "product_name": name,
            "barcode": barcode,
            "default_price": float(price or 0),
            "stock": int(stock or 0)
        }
        response = api_create_product(data)
        if response and response.status_code in [200, 201]:
            QMessageBox.information(self, "성공", "상품이 추가되었습니다.")

    def edit_product(self):
        product_id = self.id_edit.text().strip()
        name = self.name_edit.text().strip()
        barcode = self.barcode_edit.text().strip()
        price = self.price_edit.text().strip()
        stock = self.stock_edit.text().strip()

        if not product_id:
            QMessageBox.warning(self, "경고", "수정할 상품을 선택하세요.")
            return

        data = {
            "product_name": name,
            "barcode": barcode,
            "default_price": float(price or 0),
            "stock": int(stock or 0)
        }
        response = api_update_product(product_id, data)
        if response and response.status_code == 200:
            QMessageBox.information(self, "성공", "상품 정보가 수정되었습니다.")

    def delete_product(self):
        product_id = self.id_edit.text().strip()
        if not product_id:
            QMessageBox.warning(self, "경고", "삭제할 상품을 선택하세요.")
            return

        confirm = QMessageBox.question(self, "삭제 확인", f"정말 상품 ID {product_id}를 삭제하시겠습니까?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            response = api_delete_product(product_id)
            if response and response.status_code == 200:
                QMessageBox.information(self, "성공", "상품이 삭제되었습니다.")


class ProductRightPanel(QWidget):
    """ 상품의 재고 현황 및 매출 정보 (오른쪽 패널) """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(2)
        self.stock_table.setHorizontalHeaderLabels(["월", "재고 변화"])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(2)
        self.sales_table.setHorizontalHeaderLabels(["월", "판매량"])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(QLabel("월별 재고 변화"))
        layout.addWidget(self.stock_table)
        layout.addWidget(QLabel("월별 판매량"))
        layout.addWidget(self.sales_table)

        self.setLayout(layout)

    def update_stock_data(self, stock_data):
        """ 상품별 월별 재고 데이터 표시 """
        self.stock_table.setRowCount(0)
        for month, amount in stock_data.items():
            row = self.stock_table.rowCount()
            self.stock_table.insertRow(row)
            self.stock_table.setItem(row, 0, QTableWidgetItem(month))
            self.stock_table.setItem(row, 1, QTableWidgetItem(str(amount)))

    def update_sales_data(self, sales_data):
        """ 상품별 월별 판매량 표시 """
        self.sales_table.setRowCount(0)
        for month, sales in sales_data.items():
            row = self.sales_table.rowCount()
            self.sales_table.insertRow(row)
            self.sales_table.setItem(row, 0, QTableWidgetItem(month))
            self.sales_table.setItem(row, 1, QTableWidgetItem(str(sales)))


class ProductsTab(QWidget):
    """ 상품 관리 메인 탭 """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.left_panel = ProductLeftPanel()
        self.right_panel = ProductRightPanel()

        main_layout.addWidget(self.left_panel, 2)  # 상품 정보 (좌)
        main_layout.addWidget(self.right_panel, 3)  # 재고 및 판매량 (우)

        self.setLayout(main_layout)

        self.load_products()

    def load_products(self):
        """ 상품 목록을 가져와 테이블에 로드 """
        products = api_fetch_products()
        if products:
            first_product = products[0]
            self.left_panel.display_product(first_product)

            # 테스트용 데이터
            sample_stock_data = {"1월": 500, "2월": 450, "3월": 400}
            sample_sales_data = {"1월": 50, "2월": 60, "3월": 70}
            self.right_panel.update_stock_data(sample_stock_data)
            self.right_panel.update_sales_data(sample_sales_data)

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel, QGroupBox, QSpinBox
import sys
import os

# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_purchases, api_create_purchase, api_update_purchase, api_delete_purchase, api_fetch_products, api_update_product_stock, get_auth_headers

global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)

class PurchaseLeftPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """
        매입 UI 초기화
        """
        main_layout = QVBoxLayout()

        # 왼쪽 패널 (상품 검색 + 매입 입력)
        self.left_panel = QGroupBox("상품 매입")
        left_layout = QVBoxLayout()

        # 검색창
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("상품명 입력")
        self.search_button = QPushButton("검색")
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.search_button)
        left_layout.addLayout(search_layout)

        # 상품 목록
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(["ID", "상품명", "재고", "가격"])
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        left_layout.addWidget(self.product_table)

        # 매입 입력 (상품 ID, 매입 수량)
        self.selected_product_id = QLineEdit()
        self.selected_product_id.setPlaceholderText("선택된 상품 ID")
        self.selected_product_id.setReadOnly(True)
        self.purchase_quantity = QSpinBox()
        self.purchase_quantity.setMinimum(1)
        self.purchase_quantity.setMaximum(1000)

        left_layout.addWidget(QLabel("매입 상품 ID:"))
        left_layout.addWidget(self.selected_product_id)
        left_layout.addWidget(QLabel("매입 수량:"))
        left_layout.addWidget(self.purchase_quantity)

        # 매입 버튼
        self.purchase_button = QPushButton("매입 등록")
        left_layout.addWidget(self.purchase_button)

        self.left_panel.setLayout(left_layout)
        main_layout.addWidget(self.left_panel, 2)

        # ✅ 오른쪽 패널 (매입 내역 조회)
        self.right_panel = QGroupBox("매입 내역")
        right_layout = QVBoxLayout()

        # ✅ 매입 내역 테이블 추가
        self.purchase_history_table = QTableWidget()
        self.purchase_history_table.setColumnCount(5)
        self.purchase_history_table.setHorizontalHeaderLabels(["ID", "상품명", "매입 수량", "단가", "매입일"])
        self.purchase_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.purchase_history_table)

        self.right_panel.setLayout(right_layout)
        main_layout.addWidget(self.right_panel, 3)

        self.setLayout(main_layout)

        # 이벤트 연결
        self.search_button.clicked.connect(self.search_products)
        self.product_table.itemSelectionChanged.connect(self.select_product)
        self.purchase_button.clicked.connect(self.register_purchase)

        # ✅ 매입 내역 불러오기
        self.load_purchase_history()
        # 초기 상품 목록 로드
        self.search_products()
        
    def load_purchase_history(self):
        """
        최근 매입 내역 조회 (서버에서 가져오기)
        """
        global global_token
        purchases = api_fetch_purchases(global_token)  # ✅ 매입 내역 가져오기

        self.purchase_history_table.setRowCount(0)
        purchases.sort(key=lambda x: x["purchase_date"], reverse=True)  # ✅ 최신순 정렬

        for purchase in purchases:
            row = self.purchase_history_table.rowCount()
            self.purchase_history_table.insertRow(row)
            self.purchase_history_table.setItem(row, 0, QTableWidgetItem(str(purchase.get("id", ""))))
            self.purchase_history_table.setItem(row, 1, QTableWidgetItem(purchase.get("product_name", "N/A")))
            self.purchase_history_table.setItem(row, 2, QTableWidgetItem(str(purchase.get("quantity", 0))))
            self.purchase_history_table.setItem(row, 3, QTableWidgetItem(str(purchase.get("unit_price", 0))))
            self.purchase_history_table.setItem(row, 4, QTableWidgetItem(purchase.get("purchase_date", "N/A")))
        

    def search_products(self):
        """
        상품 검색 (서버에서 가져오기)
        """
        global global_token
        keyword = self.search_edit.text().strip()

        try:
            response = api_fetch_products(global_token)
            products = response  # ✅ API 응답을 JSON으로 변환
        except Exception as e:
            print(f"❌ 상품 목록 불러오기 실패: {e}")
            QMessageBox.critical(self, "실패", "상품 목록을 불러올 수 없습니다.")
            return

        # 🔹 API 응답이 딕셔너리인 경우, 모든 카테고리의 상품을 리스트로 합침
        if isinstance(products, dict):
            all_products = []
            for category, product_list in products.items():
                if isinstance(product_list, list):  # ✅ 각 카테고리의 상품 리스트가 올바른지 확인
                    all_products.extend(product_list)  # ✅ 전체 리스트에 추가

            products = all_products  # ✅ 최종적으로 리스트 형태로 변환

        # 🔹 검색어 필터링 (상품명이 존재하는 경우만)
        filtered_products = [p for p in products if isinstance(p, dict) and keyword.lower() in p.get("product_name", "").lower()]

        self.product_table.setRowCount(0)
        for product in filtered_products:
            row = self.product_table.rowCount()
            self.product_table.insertRow(row)
            self.product_table.setItem(row, 0, QTableWidgetItem(str(product.get("id", ""))))
            self.product_table.setItem(row, 1, QTableWidgetItem(product.get("product_name", "N/A")))
            self.product_table.setItem(row, 2, QTableWidgetItem(str(product.get("stock", 0))))
            self.product_table.setItem(row, 3, QTableWidgetItem(str(product.get("default_price", 0))))

    def select_product(self):
        """
        선택한 상품 정보를 가져옴
        """
        selected_items = self.product_table.selectedItems()
        if not selected_items:
            return

        product_id = selected_items[0].text()
        self.selected_product_id.setText(product_id)

    def register_purchase(self):
        """
        상품 매입 등록 (서버로 전송)
        """
        global global_token
        product_id = self.selected_product_id.text().strip()
        quantity = self.purchase_quantity.value()

        if not product_id:
            QMessageBox.warning(self, "경고", "상품을 선택하세요.")
            return

        try:
            product_id = int(product_id)
        except ValueError:
            QMessageBox.warning(self, "경고", "잘못된 상품 ID입니다.")
            return

        print("📌 서버로 보낼 데이터:", {"product_id": product_id, "stock_increase": quantity})  # 🔍 디버깅 출력

        resp = api_update_product_stock(global_token, product_id, quantity)  # ✅ 재고 업데이트 API 호출

        if resp is None:
            QMessageBox.critical(self, "실패", "매입 등록 실패: 서버 응답 없음")
            return

        if resp.status_code == 200:
            QMessageBox.information(self, "성공", "매입이 등록되었습니다.")
            self.search_products()  # 상품 목록 새로고침
            self.load_purchase_history()  # 매입 내역 새로고침
        else:
            print(f"❌ 매입 등록 실패: {resp.status_code} {resp.text}")
            QMessageBox.critical(self, "실패", f"매입 등록 실패: {resp.status_code}\n{resp.text}")

    def load_purchase_history(self):
        """
        최근 매입 내역 조회 (서버에서 가져오기)
        """
        global global_token
        purchases = api_fetch_purchases(global_token)  # 서버에서 매입 내역 가져오기

        self.purchase_history_table.setRowCount(0)
        for purchase in purchases:
            row = self.purchase_history_table.rowCount()
            self.purchase_history_table.insertRow(row)
            self.purchase_history_table.setItem(row, 0, QTableWidgetItem(str(purchase["id"])))
            self.purchase_history_table.setItem(row, 1, QTableWidgetItem(purchase["product_name"]))
            self.purchase_history_table.setItem(row, 2, QTableWidgetItem(str(purchase["quantity"])))
            self.purchase_history_table.setItem(row, 3, QTableWidgetItem(str(purchase["unit_price"])))
            self.purchase_history_table.setItem(row, 4, QTableWidgetItem(purchase["purchase_date"]))



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
        main_layout = QHBoxLayout()

        self.left_panel = PurchaseLeftPanel()
        self.right_panel = PurchaseRightPanel()

        main_layout.addWidget(self.left_panel, 1)  # 매입 정보 (좌)
        main_layout.addWidget(self.right_panel, 5)  # 재고 및 매입량 (우)

        self.setLayout(main_layout)

        self.load_purchases()

    def load_purchases(self):
        """ 매입 목록을 가져와 테이블에 로드 """
        purchases = api_fetch_purchases(global_token)
        if purchases:
            first_purchase = purchases[0]
            self.left_panel.display_purchase(first_purchase)

            # 테스트용 데이터
            sample_stock_data = {"1월": 300, "2월": 400, "3월": 500}
            sample_purchase_data = {"1월": 50, "2월": 60, "3월": 70}
            self.right_panel.update_stock_data(sample_stock_data)
            self.right_panel.update_purchase_data(sample_purchase_data)

    
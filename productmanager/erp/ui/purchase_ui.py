from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel, QGroupBox, QSpinBox, QDateEdit, QInputDialog
import sys
import os
from datetime import datetime
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_purchases, api_fetch_products, api_update_product_stock, get_auth_headers

global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)

class PurchaseLeftPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.init_ui()

    def init_ui(self):
        """
        매입 UI 초기화
        """
        main_layout = QVBoxLayout()

        # 날짜 선택 추가 (기간 조회)
        date_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(datetime.today().date())
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(datetime.today().date())

        self.filter_button = QPushButton("조회")
        self.filter_button.clicked.connect(self.filter_purchases_by_date)

        date_layout.addWidget(QLabel("시작 날짜:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("종료 날짜:"))
        date_layout.addWidget(self.end_date)
        date_layout.addWidget(self.filter_button)

        main_layout.addLayout(date_layout)

        # 상품 검색 및 매입 입력 UI 추가
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("상품명 입력")
        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self.search_products)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.search_button)
        main_layout.addLayout(search_layout)

        self.product_table = QTableWidget()
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(["ID", "상품명", "재고", "가격"])
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.product_table.itemSelectionChanged.connect(self.select_product)
        main_layout.addWidget(self.product_table)

        # 매입 입력 (상품 ID, 매입 수량)
        self.selected_product_id = QLineEdit()
        self.selected_product_id.setPlaceholderText("선택된 상품 ID")
        self.selected_product_id.setReadOnly(True)
        self.purchase_quantity = QSpinBox()
        self.purchase_quantity.setMinimum(1)
        self.purchase_quantity.setMaximum(10000)
        self.purchase_price = QSpinBox()  # ✅ 단가 입력 추가
        self.purchase_price.setMinimum(1)
        self.purchase_price.setMaximum(100000)
        self.purchase_price.setPrefix("₩")
        main_layout.addWidget(QLabel("매입 상품 ID:"))
        main_layout.addWidget(self.selected_product_id)
        main_layout.addWidget(QLabel("매입 수량:"))
        main_layout.addWidget(self.purchase_quantity)
        main_layout.addWidget(QLabel("단가 (₩):"))  # ✅ 단가 입력 추가
        main_layout.addWidget(self.purchase_price)
        # 매입 버튼
        self.purchase_button = QPushButton("매입 등록")
        self.purchase_button.clicked.connect(self.register_purchase)
        main_layout.addWidget(self.purchase_button)

        # ✅ 매입 수정 및 삭제 버튼 추가
        self.update_button = QPushButton("매입 수정")
        self.delete_button = QPushButton("매입 삭제")
        self.update_button.clicked.connect(self.update_selected_purchase)
        self.delete_button.clicked.connect(self.delete_selected_purchase)
        main_layout.addWidget(self.update_button)
        main_layout.addWidget(self.delete_button)

        self.setLayout(main_layout)

        # 초기 상품 목록 로드
        # self.search_products()

    def search_products(self):
        """
        상품 검색
        """
        keyword = self.search_edit.text().strip()
        products = api_fetch_products(global_token)

        if isinstance(products, dict):
            all_products = []
            for category, product_list in products.items():
                if isinstance(product_list, list):
                    all_products.extend(product_list)
            products = all_products

        filtered_products = [p for p in products if keyword.lower() in p.get("product_name", "").lower()]
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
        선택한 상품 정보를 가져옴 (어느 열을 클릭해도 ID가 선택됨)
        """
        selected_items = self.product_table.selectedItems()
        if not selected_items:
            return

        # ✅ 클릭한 셀의 행(row) 번호를 가져옴
        selected_row = selected_items[0].row()

        # ✅ 해당 행의 첫 번째 열(ID)을 가져옴
        product_id = self.product_table.item(selected_row, 0).text()

        self.selected_product_id.setText(product_id)  # ✅ ID 업데이트


    def register_purchase(self):
        """
        상품 매입 등록 (재고 업데이트 포함)
        """
        product_id = self.selected_product_id.text().strip()
        quantity = self.purchase_quantity.value()
        unit_price = self.purchase_price.value()  # ✅ 사용자가 입력한 단가 포함

        if not product_id:
            QMessageBox.warning(self, "경고", "상품을 선택하세요.")
            return

        try:
            product_id = int(product_id)
        except ValueError:
            QMessageBox.warning(self, "경고", "잘못된 상품 ID입니다.")
            return

        # ✅ 요청 데이터 확인
        purchase_data = {
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "purchase_date": datetime.today().strftime("%Y-%m-%d")
        }
        print(f"📡 매입 등록 요청 데이터: {purchase_data}")  # ✅ 디버깅 출력

        # ✅ FastAPI 매입 등록 API 호출
        url = "http://127.0.0.1:8000/purchases"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            response = requests.post(url, json=purchase_data, headers=headers)
            response.raise_for_status()
            print(f"📡 매입 등록 응답: {response.json()}")  # ✅ 응답 확인

            QMessageBox.information(self, "성공", "매입이 등록되었습니다.")
            self.search_products()  # ✅ 상품 목록 새로고침 (재고 업데이트 적용)
            self.parent_widget.load_purchase_history()  # ✅ 매입 내역 새로고침
        except requests.RequestException as e:
            print(f"❌ 매입 등록 실패: {e}")
            QMessageBox.critical(self, "실패", f"매입 등록 실패: {e}")




   

    def filter_purchases_by_date(self):
        """
        선택한 날짜 또는 기간별 매입 내역을 서버에서 조회하여 업데이트
        """
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")

        # FastAPI 서버에 날짜별 조회 요청
        url = f"http://127.0.0.1:8000/purchases?start_date={start_date}&end_date={end_date}"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # 오류 발생 시 예외 처리
            purchases = response.json()

            print(f"📌 서버에서 받은 매입 내역 개수: {len(purchases)}")  # ✅ 데이터 개수 확인
            print(purchases)  # ✅ 실제 데이터를 확인
            
            # UI 업데이트
            self.parent_widget.right_panel.update_purchase_history(purchases)

        except requests.RequestException as e:
            QMessageBox.critical(self, "오류", f"매입 내역 조회 실패: {e}")

    def update_selected_purchase(self):
        """
        선택한 매입 내역 수정
        """
        purchase_id, ok = QInputDialog.getInt(self, "매입 수정", "수정할 매입 ID를 입력하세요:")
        if not ok:
            return

        quantity, ok = QInputDialog.getInt(self, "매입 수정", "새로운 수량을 입력하세요:", min=1, max=1000)
        if not ok:
            return

        unit_price, ok = QInputDialog.getInt(self, "매입 수정", "새로운 단가를 입력하세요:", min=1, max=100000)
        if not ok:
            return

        url = f"http://127.0.0.1:8000/purchases/{purchase_id}"
        headers = {"Authorization": f"Bearer {global_token}"}
        purchase_data = {"quantity": quantity, "unit_price": unit_price, "product_id": self.selected_product_id.text(), "purchase_date": datetime.today().strftime("%Y-%m-%d")}

        response = requests.put(url, json=purchase_data, headers=headers)
        if response.status_code == 200:
            QMessageBox.information(self, "성공", "매입 내역이 수정되었습니다.")
            self.parent_widget.load_purchase_history()
        else:
            QMessageBox.critical(self, "실패", f"매입 수정 실패: {response.text}")

    def delete_selected_purchase(self):
        """
        선택한 매입 내역 삭제
        """
        purchase_id, ok = QInputDialog.getInt(self, "매입 삭제", "삭제할 매입 ID를 입력하세요:")
        if not ok:
            return

        url = f"http://127.0.0.1:8000/purchases/{purchase_id}"
        headers = {"Authorization": f"Bearer {global_token}"}

        response = requests.delete(url, headers=headers)
        if response.status_code == 200:
            QMessageBox.information(self, "성공", "매입 내역이 삭제되었습니다.")
            self.parent_widget.load_purchase_history()
        else:
            QMessageBox.critical(self, "실패", f"매입 삭제 실패: {response.text}")

class PurchaseRightPanel(QWidget):
    """
    매입 내역 조회 패널 (오른쪽)
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.purchase_history_table = QTableWidget()
        self.purchase_history_table.setColumnCount(5)
        self.purchase_history_table.setHorizontalHeaderLabels(["ID", "상품명", "매입 수량", "단가", "매입일"])
        self.purchase_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.purchase_history_table)
        
        # ✅ 매입 합계 테이블
        self.total_summary_table = QTableWidget()
        self.total_summary_table.setRowCount(1)
        self.total_summary_table.setColumnCount(2)
        self.total_summary_table.setHorizontalHeaderLabels(["총 매입 수량", "총 매입 금액"])
        self.total_summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.total_summary_table)
        
        self.setLayout(layout)

    def update_purchase_history(self, purchases):
        """
        테이블 업데이트 (UI 강제 새로고침)
        """
        print(f"📌 업데이트할 매입 내역 개수: {len(purchases)}")

        self.purchase_history_table.clearContents()  # ✅ 기존 데이터 삭제
        self.purchase_history_table.setRowCount(0)   # ✅ 테이블 초기화
        total_quantity = 0
        total_price = 0
        for purchase in purchases:
            row = self.purchase_history_table.rowCount()
            self.purchase_history_table.insertRow(row)
            self.purchase_history_table.setItem(row, 0, QTableWidgetItem(str(purchase.get("id", ""))))
            self.purchase_history_table.setItem(row, 1, QTableWidgetItem(purchase.get("product_name", "N/A")))
            self.purchase_history_table.setItem(row, 2, QTableWidgetItem(str(purchase.get("quantity", 0))))
            self.purchase_history_table.setItem(row, 3, QTableWidgetItem(str(purchase.get("unit_price", 0))))
            self.purchase_history_table.setItem(row, 4, QTableWidgetItem(str(purchase.get("purchase_date", "N/A"))))

            # 합계 계산
            total_quantity += purchase.get("quantity", 0)
            total_price += purchase.get("quantity", 0) * purchase.get("unit_price", 0)
        # ✅ 합계 테이블 업데이트
        self.total_summary_table.setItem(0, 0, QTableWidgetItem(str(total_quantity)))
        self.total_summary_table.setItem(0, 1, QTableWidgetItem(f"₩{total_price:,}"))

        self.purchase_history_table.viewport().update()  # ✅ 강제 UI 새로고침
        print("✅ 테이블 업데이트 완료")


class PurchaseTab(QWidget):
    """
    매입 관리 탭
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.left_panel = PurchaseLeftPanel(self)
        self.right_panel = PurchaseRightPanel()
        main_layout.addWidget(self.left_panel, 1)
        main_layout.addWidget(self.right_panel, 5)
        self.setLayout(main_layout)
        self.load_purchase_history()

    def load_purchase_history(self, start_date=None, end_date=None):
        purchases = api_fetch_purchases(global_token)
        if start_date and end_date:
            purchases = [p for p in purchases if start_date <= p["purchase_date"] <= end_date]
        self.right_panel.update_purchase_history(purchases)

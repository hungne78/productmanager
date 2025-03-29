from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel, QGroupBox, QSpinBox, QDateEdit, QInputDialog
import sys
import os
from datetime import datetime
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_purchases, api_fetch_products, api_update_product_stock, get_auth_headers
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import QSize, Qt

global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)

class PurchaseLeftPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # ---------- 🔼 위쪽: 기존 매입 등록/조회 영역 ----------
        top_section = QWidget()
        top_layout = QVBoxLayout()

        # 날짜 선택
        date_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(datetime.today().date())
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(datetime.today().date())
        self.filter_button = QPushButton("조회")
        self.filter_button.clicked.connect(self.filter_purchases_by_date)
        date_layout.addWidget(QLabel("시작:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("종료:"))
        date_layout.addWidget(self.end_date)
        date_layout.addWidget(self.filter_button)
        top_layout.addLayout(date_layout)

        # 상품 검색
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("상품명 입력")
        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self.search_products)
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.search_button)
        top_layout.addLayout(search_layout)

        # 상품 테이블
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(["ID", "상품명", "재고", "가격"])
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.product_table.itemSelectionChanged.connect(self.select_product)
        top_layout.addWidget(self.product_table)

        # 매입 입력
        self.selected_product_id = QLineEdit()
        self.selected_product_id.setPlaceholderText("선택된 상품 ID")
        self.selected_product_id.setReadOnly(True)
        self.purchase_quantity = QSpinBox()
        
        self.purchase_price = QSpinBox()
        
        

        top_layout.addWidget(QLabel("매입 상품 ID:"))
        top_layout.addWidget(self.selected_product_id)
        top_layout.addWidget(QLabel("매입 수량:"))
        top_layout.addWidget(self.purchase_quantity)
        top_layout.addWidget(QLabel("단가"))
        top_layout.addWidget(self.purchase_price)

        # 버튼들
        self.purchase_button = QPushButton("매입 등록")
        self.purchase_button.clicked.connect(self.register_purchase)
        self.update_button = QPushButton("매입 수정")
        self.delete_button = QPushButton("매입 삭제")
        self.update_button.clicked.connect(self.update_selected_purchase)
        self.delete_button.clicked.connect(self.delete_selected_purchase)

        top_layout.addWidget(self.purchase_button)
        top_layout.addWidget(self.update_button)
        top_layout.addWidget(self.delete_button)

        top_section.setLayout(top_layout)

        # ▼ 재고 필터링 그룹박스
        # ▼ 재고 필터링 그룹박스
        bottom_section = QWidget()
        bottom_layout = QVBoxLayout()

        stock_group = QGroupBox("📦 재고 필터링")
        stock_layout = QVBoxLayout()

        # (1) 수량 입력 + 조회 버튼
        input_layout = QHBoxLayout()
        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("💡 재고 수량 입력 (예: 10)")
        self.stock_input.setMinimumSize(QSize(150, 30))
        self.stock_input.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #C0C0C0;
                border-radius: 6px;
                font-size: 13px;
            }
        """)

        self.stock_search_button = QPushButton("🔍 재고 적은 품목 조회")
        self.stock_search_button.setMinimumSize(QSize(150, 30))
        self.stock_search_button.setStyleSheet("""
            QPushButton {
                background-color: #4B7BEC;
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3A5FDB;
            }
        """)
        self.stock_search_button.clicked.connect(self.search_low_stock_items)

        input_layout.addWidget(self.stock_input)
        input_layout.addWidget(self.stock_search_button)
        stock_layout.addLayout(input_layout)

        # (2) 결과 출력용 테이블
        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(2)
        self.low_stock_table.setHorizontalHeaderLabels(["📦 상품명", "🔢 재고 수량"])
        self.low_stock_table.setAlternatingRowColors(True)
        self.low_stock_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.low_stock_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.low_stock_table.verticalHeader().setVisible(False)
        self.low_stock_table.setShowGrid(False)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.low_stock_table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #D6DDE8;
                border-radius: 8px;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #F1F3F9;
                padding: 6px;
                font-weight: bold;
                color: #333;
                border: 1px solid #D6DDE8;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #C8DAFC;
            }
        """)

        stock_layout.addWidget(self.low_stock_table)

        # 그룹박스에 레이아웃 설정
        stock_group.setLayout(stock_layout)

        # 그룹박스를 아래쪽 섹션에 추가
        bottom_layout.addWidget(stock_group)


        # ✅ 이 줄이 꼭 필요! → 아래쪽 위젯에 레이아웃 적용
        bottom_section.setLayout(bottom_layout)
        main_layout = QVBoxLayout()
        main_layout.addWidget(top_section, 1)
        main_layout.addWidget(bottom_section, 1)
        self.setLayout(main_layout)


        # 초기 상품 목록 로드
        # self.search_products()
    def search_low_stock_items(self):
        try:
            threshold = int(self.stock_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "유효한 숫자를 입력하세요.")
            return

        try:
            # 🔹 FastAPI 서버에서 창고 재고 불러오기
            url = "http://localhost:8000/products/warehouse_stock"  # 실제 주소/포트로 교체
            headers = {"Authorization": f"Bearer {global_token}"}  # 필요 시만
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            products = response.json()  # 리스트 형태

            # 🔹 재고 부족 항목 필터링
            low_stock_items = [p for p in products if p.get("quantity", 0) < threshold]

            # 🔹 테이블 초기화
            self.low_stock_table.setRowCount(0)

            if not low_stock_items:
                QMessageBox.information(self, "조회 결과", "재고 부족 상품이 없습니다.")
                return

            # 🔹 결과 테이블에 표시
            self.low_stock_table.setRowCount(len(low_stock_items))
            for row, item in enumerate(low_stock_items):
                name_item = QTableWidgetItem(item["product_name"])
                qty_item = QTableWidgetItem(str(item["quantity"]))
                name_item.setTextAlignment(Qt.AlignCenter)
                qty_item.setTextAlignment(Qt.AlignCenter)
                self.low_stock_table.setItem(row, 0, name_item)
                self.low_stock_table.setItem(row, 1, qty_item)

        except Exception as e:
            QMessageBox.critical(self, "오류", f"서버 요청 중 오류 발생:\n{e}")

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
        # ✅ 크기 정책 설정
        self.left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ✅ 고정 크기 설정
        self.left_panel.setFixedWidth(350)  # 1 비율
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)
        self.setLayout(main_layout)
        self.load_purchase_history()
        self.setStyleSheet("""
QWidget {
    background-color: #F7F9FC; /* 좀 더 밝은 배경 */
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
    color: #2F3A66;
}
QGroupBox {
    background-color: rgba(255,255,255, 0.8);
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px;
    margin-top: 12px;
}
QGroupBox::title {
    font-size: 15px;
    font-weight: 600;
    color: #4B5D88;
    padding: 6px 12px;
}
QPushButton {
    background-color: #E2E8F0;
    border: 2px solid #CBD5E0;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 500;
    color: #2F3A66;
}
QPushButton:hover {
    background-color: #CBD5E0;
}
QTableWidget {
    background-color: #FFFFFF;
    border: 3px solid #D2D6DC;
    border-radius: 8px;
    gridline-color: #E2E2E2;
    font-size: 15px;
    color: #333333;
    alternate-background-color: #fafafa;
    selection-background-color: #c8dafc;
}
QHeaderView::section {
    background-color: #EEF1F5;
    color: #333333;
    font-weight: 600;
    padding: 6px;
    border: 1px solid #D2D6DC;
    border-radius: 0;
    border-bottom: 2px solid #ddd;
}
""")
    def load_purchase_history(self, start_date=None, end_date=None):
        purchases = api_fetch_purchases(global_token)
        if start_date and end_date:
            purchases = [p for p in purchases if start_date <= p["purchase_date"] <= end_date]
        self.right_panel.update_purchase_history(purchases)

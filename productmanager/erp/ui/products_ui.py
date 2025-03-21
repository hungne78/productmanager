from PyQt5.QtWidgets import QWidget, QHBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel, QDialog, QVBoxLayout, QListWidget, QComboBox, QGroupBox
import sys
import os

# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_products, api_create_product, api_update_product, api_delete_product, get_auth_headers, api_delete_product_by_id, api_update_product_by_id, api_update_product_by_id
from baselefttabwidget import BaseLeftTableWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy

from PyQt5.QtChart import QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis, QLineSeries
from PyQt5.QtWidgets import QHeaderView  # 추가 필요
import requests
from datetime import datetime
global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)

class ProductDialog(QDialog):
    def __init__(self, title, product=None, parent=None):
        """
        상품 등록 및 수정 다이얼로그
        :param title: 다이얼로그 제목 ("신규 상품 등록" or "상품 수정")
        :param product: 기존 상품 정보 (수정 시)
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(500, 600)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # ✅ 브랜드 ID (숫자 입력)
        self.brand_id_edit = QLineEdit()
        form_layout.addRow("브랜드 ID:", self.brand_id_edit)

        # ✅ 상품명
        self.name_edit = QLineEdit()
        form_layout.addRow("상품명:", self.name_edit)

        # ✅ 바코드
        self.barcode_edit = QLineEdit()
        form_layout.addRow("바코드:", self.barcode_edit)

        # ✅ 기본 가격
        self.price_edit = QLineEdit()
        form_layout.addRow("기본 가격:", self.price_edit)

        # ✅ 인센티브
        self.incentive_edit = QLineEdit()
        form_layout.addRow("인센티브:", self.incentive_edit)

        # ✅ 재고 수량
        self.stock_edit = QLineEdit()
        form_layout.addRow("재고 수량:", self.stock_edit)

        # ✅ 박스당 수량
        self.box_quantity_edit = QLineEdit()
        form_layout.addRow("박스당 수량:", self.box_quantity_edit)

        # ✅ 활성 여부 (1: 활성, 0: 비활성)
        self.active_edit = QComboBox()
        self.active_edit.addItems(["1 - 활성", "0 - 비활성"])
        form_layout.addRow("활성 여부:", self.active_edit)

        # ✅ 카테고리
        self.category_edit = QLineEdit()
        form_layout.addRow("카테고리:", self.category_edit)

        # ✅ 일반가 / 고정가 여부 (Bool → 드롭다운)
        self.price_type_edit = QComboBox()
        self.price_type_edit.addItems(["일반가", "고정가"])  # ✅ 0: 일반가 (False), 1: 고정가 (True)
        form_layout.addRow("가격 유형:", self.price_type_edit)


        layout.addLayout(form_layout)

        # ✅ 버튼 추가
        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("확인")
        self.cancel_button = QPushButton("취소")
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # ✅ 버튼 이벤트 연결
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # ✅ 기존 상품 정보가 있으면 값 채우기 (수정 모드)
        if product:
            self.brand_id_edit.setText(str(product.get("brand_id", "")))
            self.name_edit.setText(product.get("product_name", ""))
            self.barcode_edit.setText(product.get("barcode", ""))
            self.price_edit.setText(str(product.get("default_price", "0")))
            self.incentive_edit.setText(str(product.get("incentive", "0")))
            self.stock_edit.setText(str(product.get("stock", "0")))
            self.box_quantity_edit.setText(str(product.get("box_quantity", "1")))
            self.active_edit.setCurrentIndex(0 if product.get("is_active", 1) == 1 else 1)
            self.category_edit.setText(product.get("category", ""))
            self.price_type_edit.setCurrentIndex(1 if product.get("is_fixed_price", False) else 0)  # ✅ bool → index 변환

class ProductSelectionDialog(QDialog):
    def __init__(self, products, parent=None):
        super().__init__(parent)
        self.setWindowTitle("상품 검색 결과")
        self.resize(300, 400)
        self.products = products  # 상품 목록 (dict 리스트)
        self.selected_product = None

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()

        # "ID - 상품명" 형식으로 리스트 추가
        for product in products:
            display_text = f"{product.get('id')} - {product.get('product_name')}"
            self.list_widget.addItem(display_text)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("선택")
        self.cancel_button = QPushButton("취소")
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

        self.ok_button.clicked.connect(self.on_ok)
        self.cancel_button.clicked.connect(self.reject)

    def on_ok(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            index = self.list_widget.row(selected_items[0])
            self.selected_product = self.products[index]
            self.accept()
        else:
            QMessageBox.warning(self, "선택", "상품을 선택해주세요.")

class ProductRightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()

        # 향후 상품 관련 데이터 및 통계를 표시할 공간
        self.box1 = QGroupBox("상품 매출 통계")
        self.label1 = QLabel("여기에 상품별 매출 분석을 표시할 예정")
        layout.addWidget(self.box1)
        self.box1_layout = QVBoxLayout()
        self.box1_layout.addWidget(self.label1)
        self.box1.setLayout(self.box1_layout)

        self.box2 = QGroupBox("상품 재고 현황")
        self.label2 = QLabel("여기에 상품 재고 데이터를 표시할 예정")
        layout.addWidget(self.box2)
        self.box2_layout = QVBoxLayout()
        self.box2_layout.addWidget(self.label2)
        self.box2.setLayout(self.box2_layout)

        self.setLayout(layout)            
                        
class ProductLeftPanel(BaseLeftTableWidget):
    def __init__(self, parent=None):
        labels = [
            
            "브랜드 ID",      # 1
            "상품명",         # 2
            "바코드",         # 3
            "기본 가격",      # 4
            "인센티브",       # 5
            "재고 수량",      # 6
            "박스당 수량",    # 7
            "카테고리",
            "활성화여부",       # 8
            "가격유형"
        ]
        super().__init__(row_count=len(labels), labels=labels, parent=parent)
         # ✅ "삭제" 버튼 추가 (BaseLeftTableWidget의 btn_layout에 추가)
        self.btn_delete = QPushButton("삭제")
        self.layout().itemAt(1).layout().addWidget(self.btn_delete)

        # ✅ 버튼 클릭 이벤트 연결
        self.btn_new.clicked.connect(self.create_product)
        self.btn_edit.clicked.connect(self.update_product)
        self.btn_delete.clicked.connect(self.delete_product)

    def display_product(self, product: dict):
        """
        검색된 상품 정보를 왼쪽 패널에 표시
        """
        if not product:
            for r in range(self.row_count):
                self.set_value(r, "")
            self.current_product_id = None
            return

        self.current_product_id = product.get("id")
        self.set_value(0, str(product.get("brand_id", "")))
        self.set_value(1, product.get("product_name", ""))
        self.set_value(2, product.get("barcode", ""))
        self.set_value(3, str(product.get("default_price", 0)))
        self.set_value(4, str(product.get("incentive", 0)))
        self.set_value(5, str(product.get("stock", 0)))
        self.set_value(6, str(product.get("box_quantity", 1)))
        self.set_value(7, product.get("category", ""))
        is_active = product.get("is_active", 1)
        self.set_value(8, "활성" if is_active == 1 else "비활성")
        is_fixed_price = product.get("is_fixed_price", False)
        self.set_value(9, "고정가" if is_fixed_price else "일반가")

        # --- (4.1) 여기서 오른쪽 패널 업데이트 시점 (상품 선택 시) ---
        # parent: ProductsTab
        if hasattr(self.parent(), "product_selected"):
            # 호출
            self.parent().product_selected(product)  
            # 또는 바로 parent().fetch_and_update_stock(product["id"]) 형식으로 해도 됨



    def create_product(self):
        """
        상품 신규 등록 (직원별 차량 재고도 자동 추가)
        """
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        dialog = ProductDialog("신규 상품 등록")  # ✅ `ProductDialog` 사용
        if dialog.exec_() == QDialog.Accepted:
            data = {
                "brand_id": int(dialog.brand_id_edit.text() or 0),
                "product_name": dialog.name_edit.text(),
                "barcode": dialog.barcode_edit.text(),
                "default_price": float(dialog.price_edit.text() or 0),
                "stock": int(dialog.stock_edit.text() or 0),
                "is_active": 1 if "1" in dialog.active_edit.currentText() else 0,
                "incentive": float(dialog.incentive_edit.text() or 0),
                "box_quantity": int(dialog.box_quantity_edit.text() or 1),
                "category": dialog.category_edit.text(),
                "is_fixed_price": True if dialog.price_type_edit.currentIndex() == 1 else False
            }

            resp = api_create_product(global_token, data)
            if resp and resp.status_code in (200, 201):
                QMessageBox.information(self, "성공", "상품 등록 완료!")

                # ✅ 직원별 차량 재고 업데이트 상태 확인
                product_id = resp.json().get("id")
                if product_id:
                    QMessageBox.information(self, "성공", "직원 차량 재고도 정상적으로 추가되었습니다.")

            else:
                QMessageBox.critical(self, "실패", f"상품 등록 실패: {resp.status_code}\n{resp.text}")

        
    def update_product(self):
        """
        상품 ID를 기준으로 수정
        """
        global global_token
        if not hasattr(self, "current_product_id") or not self.current_product_id:
            QMessageBox.warning(self, "주의", "수정할 상품이 선택되지 않았습니다.")
            return

        product_id = self.current_product_id  # ✅ 저장된 상품 ID 사용

        # ✅ 기존 상품 정보 불러오기
        current_product = {
            "brand_id": self.get_value(0),  # ✅ 기존 브랜드 ID 가져오기
            "product_name": self.get_value(1),
            "barcode": self.get_value(2),
            "default_price": self.get_value(3) or "0",
            "incentive": self.get_value(4) or "0",
            "stock": self.get_value(5) or "0",
            "box_quantity": self.get_value(6) or "1",
            "category": self.get_value(7) or "",
            "is_active": 1 if self.get_value(8) == "활성" else 0,  # ✅ 리스트 값 가져오기
            "is_fixed_price": True if self.get_value(9) == "고정가" else False
        }

        # ✅ 상품 수정 다이얼로그 실행
        dialog = ProductDialog("상품 수정", product=current_product)
        if dialog.exec_() == QDialog.Accepted:
            try:
                brand_id_text = dialog.brand_id_edit.text().strip()
                brand_id = int(brand_id_text) if brand_id_text.isdigit() else None  # ✅ 브랜드 ID가 숫자인지 확인

                data = {
                    "brand_id": brand_id,
                    "product_name": dialog.name_edit.text().strip(),
                    "barcode": dialog.barcode_edit.text().strip(),
                    "default_price": float(dialog.price_edit.text().strip() or 0),
                    "stock": int(dialog.stock_edit.text().strip() or 0),
                    "is_active": 1 if "1" in dialog.active_edit.currentText() else 0,  # ✅ 수정 다이얼로그에서 가져오기
                    "incentive": float(dialog.incentive_edit.text().strip() or 0),
                    "box_quantity": int(dialog.box_quantity_edit.text().strip() or 1),
                    "category": dialog.category_edit.text().strip(),
                    "is_fixed_price": True if dialog.price_type_edit.currentIndex() == 1 else False
                }
            except ValueError as e:
                QMessageBox.critical(self, "오류", f"잘못된 입력값: {e}")
                return

            # ✅ 상품 ID로 업데이트 요청
            resp = api_update_product_by_id(global_token, product_id, data)
            if resp and resp.status_code == 200:
                QMessageBox.information(self, "성공", "상품 수정 완료!")
            else:
                QMessageBox.critical(self, "실패", f"상품 수정 실패: {resp.status_code}\n{resp.text}")


    def delete_product(self):
        """
        상품 ID를 기준으로 삭제
        """
        global global_token
        if not hasattr(self, "current_product_id") or not self.current_product_id:
            QMessageBox.warning(self, "주의", "삭제할 상품이 선택되지 않았습니다.")
            return

        product_id = self.current_product_id  # ✅ 저장된 상품 ID 사용

        reply = QMessageBox.question(
            self,
            "상품 삭제 확인",
            f"정말 상품 ID {product_id}를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            resp = api_delete_product_by_id(global_token, product_id)  # ✅ 상품 ID로 삭제 요청
            if resp and resp.status_code == 200:
                QMessageBox.information(self, "성공", f"상품 ID {product_id} 삭제 완료!")
                # 삭제 후, 테이블 초기화
                for r in range(self.row_count):
                    self.set_value(r, "")
                self.current_product_id = None  # ✅ ID 초기화
            else:
                QMessageBox.critical(self, "실패", f"상품 삭제 실패: {resp.status_code}\n{resp.text}")




class ProductRightPanel(QWidget):
    """
    오른쪽 패널 - 좌우 1:3 비율로 나눈 상품 재고 & 판매량 테이블 및 그래프
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()  # 좌우 레이아웃

        # 왼쪽 영역(테이블들)
        self.left_section = QVBoxLayout()

        # (A) 월별 재고 변화 테이블
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(2)
        self.stock_table.setHorizontalHeaderLabels(["월", "매입수량"])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.left_section.addWidget(QLabel("📌 월별 재고(매입) 변화"))
        self.left_section.addWidget(self.stock_table)

        # (B) 월별 판매량 테이블 (주문 기능이 없으면 일단 빈 상태)
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(2)
        self.sales_table.setHorizontalHeaderLabels(["월", "판매량(가정)"])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.left_section.addWidget(QLabel("📊 월별 판매량 (미구현)"))
        self.left_section.addWidget(self.sales_table)

        main_layout.addLayout(self.left_section, 1)  # 왼쪽은 비율 1

        # 오른쪽 영역(그래프들)
        self.right_section = QVBoxLayout()

        # (A) 재고(매입) 변화 그래프
        self.stock_chart = QChartView()
        self.right_section.addWidget(QLabel("📊 월별 매입(재고) 그래프"))
        self.right_section.addWidget(self.stock_chart)

        # (B) 판매량 그래프
        self.sales_chart = QChartView()
        self.right_section.addWidget(QLabel("📊 월별 판매량 그래프 (미구현)"))
        self.right_section.addWidget(self.sales_chart)

        # (C) 비교 그래프
        self.comparison_chart = QChartView()
        self.right_section.addWidget(QLabel("📊 재고 vs 판매량 비교 그래프 (미구현)"))
        self.right_section.addWidget(self.comparison_chart)

        main_layout.addLayout(self.right_section, 3)  # 오른쪽은 비율 3

        self.setLayout(main_layout)

    def update_stock_data(self, stock_data: dict):
        """
        stock_data: { '1월': 10, '2월': 0, ... } 형식
        여기서는 '재고'라기보다 '매입수량'을 예시로 표시.
        """
        # 1) 테이블 채우기
        self.stock_table.setRowCount(0)
        for month, qty in stock_data.items():
            row = self.stock_table.rowCount()
            self.stock_table.insertRow(row)
            self.stock_table.setItem(row, 0, QTableWidgetItem(month))
            self.stock_table.setItem(row, 1, QTableWidgetItem(str(qty)))

        # 2) 그래프 업데이트
        chart = QChart()
        series = QBarSeries()
        categories = []

        for month, qty in stock_data.items():
            bar_set = QBarSet(month)
            bar_set.append(qty)
            series.append(bar_set)
            categories.append(month)

        chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.setAxisX(axis_x, series)
        self.stock_chart.setChart(chart)

    def update_sales_data(self, sales_data):
        """
        상품별 월별 판매량 표시 & 그래프 업데이트
        """
        self.sales_table.setRowCount(0)
        for month, sales in sales_data.items():
            row = self.sales_table.rowCount()
            self.sales_table.insertRow(row)
            self.sales_table.setItem(row, 0, QTableWidgetItem(month))
            self.sales_table.setItem(row, 1, QTableWidgetItem(str(sales)))

        # ✅ 그래프 업데이트
        self.update_sales_chart(sales_data)

    def update_stock_chart(self, data):
        """
        월별 재고 변화 그래프 (막대 그래프)
        """
        chart = QChart()
        series = QBarSeries()
        categories = []

        for month, amount in data.items():
            bar_set = QBarSet(month)
            bar_set.append(amount)
            series.append(bar_set)
            categories.append(month)

        chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.setAxisX(axis_x, series)

        self.stock_chart.setChart(chart)

    def update_sales_chart(self, data):
        """
        월별 판매량 그래프 (막대 그래프)
        """
        chart = QChart()
        series = QBarSeries()
        categories = []

        for month, sales in data.items():
            bar_set = QBarSet(month)
            bar_set.append(sales)
            series.append(bar_set)
            categories.append(month)

        chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.setAxisX(axis_x, series)

        self.sales_chart.setChart(chart)

    def update_comparison_chart(self, stock_data, sales_data):
        """
        재고 변화 vs 판매량 비교 그래프 (선 그래프)
        """
        chart = QChart()
        series_stock = QLineSeries()
        series_sales = QLineSeries()
        axis_x = QBarCategoryAxis()
        categories = []

        for month in stock_data.keys():
            stock_amount = stock_data.get(month, 0)
            sales_amount = sales_data.get(month, 0)

            categories.append(month)
            series_stock.append(len(categories), stock_amount)
            series_sales.append(len(categories), sales_amount)

        chart.addSeries(series_stock)
        chart.addSeries(series_sales)

        axis_x.append(categories)
        chart.createDefaultAxes()
        chart.setAxisX(axis_x, series_stock)
        chart.setAxisX(axis_x, series_sales)

        self.comparison_chart.setChart(chart)



class ProductsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout()

        # 왼쪽 패널: 상품 정보 표시 (검색 후 선택된 상품 정보)
        self.left_panel = ProductLeftPanel()
        

        # 오른쪽 패널: 상품 관련 데이터 (통계 및 분석)
        self.right_panel = ProductRightPanel()
        # ✅ 크기 정책 설정
        self.left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ✅ 고정 크기 설정
        self.left_panel.setFixedWidth(350)  # 1 비율
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)

        self.setLayout(main_layout)

    
    def do_search(self, search_text):
        """
        기존 검색 로직
        """
        global global_token
        search_text = search_text.strip()
        if not search_text:
            QMessageBox.warning(self, "경고", "검색어를 입력하세요.")
            return

        try:
            response = api_fetch_products(global_token, search_name=search_text)
            if not isinstance(response, dict):
                QMessageBox.critical(self, "오류", "상품 목록 응답이 잘못되었습니다.")
                return

            products = []
            for category, items in response.items():
                if isinstance(items, list):
                    for item in items:
                        item["category"] = category
                        products.append(item)

            if not products:
                self.left_panel.display_product(None)
                QMessageBox.information(self, "검색 결과", "검색 결과가 없습니다.")
                return

            # 부분 일치 필터
            filtered_products = [
                p for p in products
                if "product_name" in p and search_text.lower() in p["product_name"].lower()
            ]

            if len(filtered_products) == 1:
                self.left_panel.display_product(filtered_products[0])
            else:
                from PyQt5.QtWidgets import QDialog
                dialog = ProductSelectionDialog(filtered_products, parent=self)
                if dialog.exec_() == QDialog.Accepted and dialog.selected_product:
                    self.left_panel.display_product(dialog.selected_product)

        except Exception as ex:
            QMessageBox.critical(self, "오류", str(ex))

    # ========== (5.1) “상품 선택 시” → fetch_and_update_stock_data ==========
    def product_selected(self, product: dict):
        """
        왼쪽 패널에서 display_product 후에 호출됨.
        여기서 오른쪽 패널의 stock(=매입) 그래프를 업데이트.
        """
        product_id = product.get("id", None)
        if not product_id:
            return

        # 예시: 올해 기준
        year = datetime.now().year

        # 1) 서버에서 월별 매입량 가져오기
        monthly_purchases = self.fetch_monthly_purchases(product_id, year)

        # 2) “1월..12월” label + 수량으로 dict 변환
        month_labels = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
        purchase_dict = {}
        for i, qty in enumerate(monthly_purchases):
            purchase_dict[month_labels[i]] = qty

        # 3) 오른쪽 패널에 전달
        self.right_panel.update_stock_data(purchase_dict)

    # ========== (5.2) “fetch_monthly_purchases” 함수 ==========
    def fetch_monthly_purchases(self, product_id: int, year: int):
        """
        서버로부터 /purchases/monthly_purchases/{product_id}/{year} 라우트 호출해
        [10,0,5,20,...12개] 형태를 반환받는다.
        """
        url = f"http://127.0.0.1:8000/purchases/monthly_purchases/{product_id}/{year}"
        headers = {"Authorization": f"Bearer {global_token}"}
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()  # ex: [10,0,5,20, ...]
            if not isinstance(data, list) or len(data) != 12:
                # 형식 체크
                print("❌ 형식 오류: 월별 매입 데이터가 12개 배열이 아님:", data)
                return [0]*12
            return data
        except Exception as e:
            print("❌ 월별 매입 데이터 조회 실패:", e)
            return [0]*12


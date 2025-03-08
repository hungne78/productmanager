from PyQt5.QtWidgets import QWidget, QHBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel, QComboBox, QVBoxLayout, QGridLayout, QScrollArea, QDateEdit
import os
import sys
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QResizeEvent,QFontMetrics
import requests
# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_orders, api_create_order, api_update_order, api_delete_order, get_auth_headers
from PyQt5.QtWidgets import QSizePolicy

BASE_URL = "http://127.0.0.1:8000"  # 실제 서버 URL
global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)

class OrderLeftWidget(QWidget):
    def __init__(self, parent=None, order_right_widget=None):
        super().__init__(parent)
        self.order_right_widget = order_right_widget  # ✅ 오른쪽 패널을 저장

        layout = QVBoxLayout()

        # ✅ 1. 날짜 선택을 가장 위로 이동
        self.order_date_label = QLabel("주문 날짜 선택")
        self.order_date_picker = QDateEdit()
        self.order_date_picker.setCalendarPopup(True)
        self.order_date_picker.setDate(QDate.currentDate())

        layout.addWidget(self.order_date_label)
        layout.addWidget(self.order_date_picker)

        # ✅ 2. 직원 목록 (세로 버튼)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.employee_container = QWidget()
        self.employee_layout = QVBoxLayout(self.employee_container)

        # ✅ 3. 서버에서 직원 목록 불러오기
        self.employee_buttons = []
        self.load_employees()

        self.scroll_area.setWidget(self.employee_container)
        layout.addWidget(self.scroll_area)

        # ✅ 4. "전체 주문 조회" 버튼 추가
        self.order_button = QPushButton("전체 주문 조회")
        self.order_button.clicked.connect(self.fetch_orders_for_all_employees)  # ✅ 전체 주문 조회
        layout.addWidget(self.order_button)

        self.setLayout(layout)


    def fetch_orders_by_date(self):
        """
        선택한 날짜와 직원 ID를 기반으로 주문 데이터 가져오기
        """
        selected_date = self.order_date_picker.date().toString("yyyy-MM-dd")
        selected_employee_id = 2  # ✅ 실제 로그인한 직원 ID로 변경 필요

        url = f"{BASE_URL}/orders/orders_with_items?employee_id={selected_employee_id}&date={selected_date}"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                orders = resp.json()
                print(f"📌 주문 데이터 조회 성공: {orders}")  # ✅ 주문 데이터 확인 로그
                self.display_orders(orders)  # ✅ 주문 데이터 넘김
            else:
                print(f"❌ 주문 조회 실패: {resp.status_code}, 응답: {resp.text}")
                QMessageBox.warning(self, "주문 조회 실패", "주문 데이터를 불러오지 못했습니다.")
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            QMessageBox.warning(self, "오류 발생", f"주문 조회 중 오류 발생: {e}")

    def display_orders(self, orders):
        """
        주문 데이터를 오른쪽 패널의 테이블에 표시
        """
        print(f"📌 [display_orders] 호출됨, 받은 데이터: {orders}")  # ✅ 로그 추가
        if self.order_right_widget:
            print("✅ [display_orders] → update_orders() 호출")  # ✅ 로그 추가
            self.order_right_widget.update_orders(orders)  # ✅ 업데이트 실행
        else:
            print("❌ order_right_widget가 None입니다.")



    def load_employees(self):
        """
        서버에서 직원 목록을 가져와 버튼을 생성
        """
        global global_token
        url = f"{BASE_URL}/employees/"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                employees = resp.json()
            else:
                employees = []
        except Exception as e:
            print(f"❌ 직원 목록 가져오기 실패: {e}")
            employees = []

        # ✅ 기존 버튼 제거 후 다시 생성
        for btn in self.employee_buttons:
            btn.setParent(None)

        self.employee_buttons.clear()

        # ✅ 직원 목록 버튼 추가
        for employee in employees:
            btn = QPushButton(employee.get("name", "알 수 없음"))
            btn.clicked.connect(lambda checked, emp_id=employee["id"]: self.fetch_orders_by_employee(emp_id))
            self.employee_layout.addWidget(btn)
            self.employee_buttons.append(btn)


    def fetch_orders_by_employee(self, employee_id):
        """
        선택한 날짜와 직원 ID를 기반으로 주문 데이터 가져오기
        """
        selected_date = self.order_date_picker.date().toString("yyyy-MM-dd")

        url = f"{BASE_URL}/orders/orders_with_items?employee_id={employee_id}&date={selected_date}"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                orders = resp.json()
                print(f"📌 직원 {employee_id}의 주문 조회 성공: {orders}")  # ✅ 주문 데이터 확인 로그
                self.display_orders(orders)
            else:
                print(f"❌ 주문 조회 실패: {resp.status_code}, 응답: {resp.text}")
                QMessageBox.warning(self, "주문 조회 실패", "주문 데이터를 불러오지 못했습니다.")
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            QMessageBox.warning(self, "오류 발생", f"주문 조회 중 오류 발생: {e}")

    def fetch_orders_for_all_employees(self):
        """
        모든 직원의 주문을 개별 조회 후, 상품별로 합산하여 표시
        """
        selected_date = self.order_date_picker.date().toString("yyyy-MM-dd")

        url = f"{BASE_URL}/employees/"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            # ✅ 1. 직원 목록을 가져오기
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                employees = resp.json()
            else:
                print(f"❌ 직원 목록 조회 실패: {resp.status_code}, 응답: {resp.text}")
                return

            aggregated_orders = {}

            # ✅ 2. 모든 직원의 주문을 개별 조회
            for employee in employees:
                employee_id = employee["id"]
                order_url = f"{BASE_URL}/orders/orders_with_items?employee_id={employee_id}&date={selected_date}"
                order_resp = requests.get(order_url, headers=headers)

                if order_resp.status_code == 200:
                    orders = order_resp.json()
                    for order in orders:
                        for item in order["items"]:
                            product_id = item["product_id"]
                            quantity = item["quantity"]

                            if product_id in aggregated_orders:
                                aggregated_orders[product_id]["quantity"] += quantity
                            else:
                                aggregated_orders[product_id] = {
                                    "product_id": product_id,
                                    "product_name": item["product_name"],
                                    "quantity": quantity
                                }
                else:
                    print(f"❌ 직원 {employee_id}의 주문 조회 실패: {order_resp.status_code}")

            # ✅ 3. 주문 데이터를 오른쪽 패널에 업데이트
            aggregated_order_list = list(aggregated_orders.values())
            print(f"📌 최종 합산된 주문 데이터: {aggregated_order_list}")
            self.display_orders([{"order_id": "all", "items": aggregated_order_list}])

        except Exception as e:
            print(f"❌ 오류 발생: {e}")

    def aggregate_orders_by_product(self, orders):
        """
        모든 직원의 주문을 `product_id`별로 그룹화하여 총 수량을 합산
        """
        aggregated_orders = {}

        for order in orders:
            for item in order["items"]:
                product_id = item["product_id"]
                quantity = item["quantity"]

                if product_id in aggregated_orders:
                    aggregated_orders[product_id]["quantity"] += quantity
                else:
                    aggregated_orders[product_id] = {
                        "product_id": product_id,
                        "product_name": item["product_name"],
                        "quantity": quantity
                    }

        # ✅ 주문 데이터를 오른쪽 패널에 업데이트
        aggregated_order_list = list(aggregated_orders.values())
        print(f"📌 최종 합산된 주문 데이터: {aggregated_order_list}")  # ✅ 확인 로그
        self.display_orders([{"order_id": "all", "items": aggregated_order_list}])


    def select_employee(self, employee_name):
        """
        특정 직원의 주문을 조회 (추후 기능 추가 예정)
        """
        print(f"직원 {employee_name}의 주문을 조회합니다.")


class OrderRightWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.current_products = []  # ✅ 상품 목록 저장

        # ✅ 타이틀 + 새로고침 버튼 추가
        self.header_layout = QVBoxLayout()
        self.title = QLabel("📋 주문 내역")
        self.title.setFont(QFont("Arial", 9, QFont.Bold))
        self.refresh_button = QPushButton("🔄 새로고침")
        self.refresh_button.setFont(QFont("Arial", 8))
        self.refresh_button.clicked.connect(self.refresh_orders)
        self.header_layout.addWidget(self.title)
        self.header_layout.addWidget(self.refresh_button)
        self.layout.addLayout(self.header_layout)

        # ✅ 상품 목록을 배치할 컨테이너 및 레이아웃 (grid_layout 추가)
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)  # ✅ 창 크기에 따라 동적 정렬
        self.layout.addWidget(self.container)

        self.setLayout(self.layout)
        self.load_products()  # ✅ 서버에서 상품 목록 로드

    def populate_table(self):
        """
        상품 목록을 `카테고리 -> 품명 -> 갯수` 순으로 정렬하여 표시
        """
        # ✅ grid_layout 초기화 (기존 위젯 제거)
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # ✅ 사용 가능한 세로 공간 계산
        available_height = self.height() - self.header_layout.sizeHint().height() - 80  
        row_height = 30  
        max_rows_per_section = max(5, available_height // row_height)  

        row = 0  
        col = 0  

        # ✅ 상품을 `카테고리 -> 품명` 순으로 정리
        sorted_products = sorted(self.current_products, key=lambda p: (p["category"], p["brand_id"], p["product_name"]))

        table = None
        row_index = 0
        current_category = None
        current_brand = None

        for product in sorted_products:
            category, brand, product_name = product["category"], product["brand_id"], product["product_name"]

            if row_index == 0 or table is None:
                table = QTableWidget()
                table.setColumnCount(2)
                table.setHorizontalHeaderLabels(["품명", "갯수"])
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                table.setFont(QFont("Arial", 9))
                table.verticalHeader().setVisible(False)
                table.setRowCount(0)

            if current_category != category:
                table.insertRow(table.rowCount())
                category_item = QTableWidgetItem(category)
                category_item.setFont(QFont("Arial", 9, QFont.Bold))
                category_item.setTextAlignment(Qt.AlignCenter)
                table.setSpan(table.rowCount() - 1, 0, 1, 2)
                table.setItem(table.rowCount() - 1, 0, category_item)
                current_category = category

            if current_brand != brand:
                current_brand = brand

            table.insertRow(table.rowCount())
            table.setItem(table.rowCount() - 1, 0, self.create_resized_text(product_name, table))
            table.setItem(table.rowCount() - 1, 1, QTableWidgetItem(""))  

            table.setRowHeight(table.rowCount() - 1, 12)
            row_index += 1

            if row_index >= max_rows_per_section:
                self.grid_layout.addWidget(table, row, col, 1, 1)
                row_index = 0
                col += 1
                table = None  

        if table is not None:
            self.grid_layout.addWidget(table, row, col, 1, 1)

    def create_resized_text(self, text, table):
        """
        칸 크기에 맞춰 글씨 크기를 자동 조정
        """
        font = QFont("Arial", 9)
        metrics = QFontMetrics(font)
        max_width = table.columnWidth(0) - 5

        while metrics.width(text) > max_width and font.pointSize() > 5:
            font.setPointSize(font.pointSize() - 1)
            metrics = QFontMetrics(font)

        item = QTableWidgetItem(text)
        item.setFont(font)
        return item

    def update_orders(self, orders):
        """
        주문 데이터를 받아서 기존 테이블의 두 번째 열(수량)에 반영
        """
        print("\n🔹 [update_orders] 호출됨")
        print(f"🔹 받은 주문 데이터: {orders}")

        # ✅ 주문된 상품 ID와 수량을 매핑
        order_quantity_map = {item["product_id"]: item["quantity"] for order in orders for item in order["items"]}
        print(f"📌 주문 ID → 수량 매핑 결과: {order_quantity_map}")

        # ✅ 현재 로드된 상품 목록 출력
        print(f"📌 현재 로드된 상품 목록 (self.current_products):")
        for p in self.current_products:
            print(f"   - ID: {p['id']}, 이름: {p['product_name']}")

        # ✅ 테이블 위젯을 순회하며 상품 ID와 주문 ID를 비교하여 수량 업데이트
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, QTableWidget):
                print(f"🟢 테이블 발견: {widget.objectName()} (행 개수: {widget.rowCount()})")

                for row in range(widget.rowCount()):
                    product_name_item = widget.item(row, 0)  # 첫 번째 열 (품명)
                    quantity_item = widget.item(row, 1)  # 두 번째 열 (수량)

                    if product_name_item is not None and quantity_item is not None:
                        product_name = product_name_item.text().strip()
                        print(f"🔍 테이블 행 {row}: 품명 = {product_name}")

                        # ✅ 기존 상품 목록에서 해당 `product_name`을 가진 제품 찾기
                        matching_product = next((p for p in self.current_products if p["product_name"] == product_name), None)

                        if matching_product:
                            product_id = matching_product["id"]
                            print(f"   ✅ 상품 매칭됨 → ID: {product_id}, 이름: {product_name}")

                            # ✅ 주문 목록에 있는 상품이면 수량 업데이트, 없으면 0으로 설정
                            if product_id in order_quantity_map:
                                quantity = order_quantity_map[product_id]
                                quantity_item.setText(str(quantity))
                                print(f"   📝 수량 업데이트: {quantity}")
                            else:
                                quantity_item.setText("")  # 주문이 없으면 빈 값 유지
                                print(f"   ❌ 주문 없음 → 수량 비움")
                        else:
                            print(f"   ❌ {product_name}에 해당하는 상품을 찾을 수 없음 (self.current_products에 없음)")

                    else:
                        print(f"   ❗ row={row}에서 product_name_item 또는 quantity_item이 없음")


    def refresh_orders(self):
        """
        새로고침 버튼 클릭 시 주문 목록 갱신
        """
        self.orders_table.clearContents()
        self.orders_table.setRowCount(0)


    def load_products(self):
        """
        서버에서 상품 목록을 가져와 `카테고리`별로 정리 후 표시
        """
        global global_token
        url = f"{BASE_URL}/products/all"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                self.current_products = [p for p in resp.json() if p["is_active"] == 1]  # ✅ 상품 목록 저장
            else:
                self.current_products = []
        except Exception as e:
            print(f"❌ 상품 목록 가져오기 실패: {e}")
            self.current_products = []

        self.populate_table()

    
    def create_resized_text(self, text, table):
        """
        칸 크기에 맞춰 글씨 크기를 자동으로 조정하여 텍스트가 잘리지 않도록 함
        """
        font = QFont("Arial", 9)  # 기본 글씨 크기 7
        metrics = QFontMetrics(font)
        max_width = table.columnWidth(0) - 5  # 셀 너비 계산

        while metrics.width(text) > max_width and font.pointSize() > 5:
            font.setPointSize(font.pointSize() - 1)
            metrics = QFontMetrics(font)

        item = QTableWidgetItem(text)
        item.setFont(font)
        return item

    def resizeEvent(self, event: QResizeEvent):
        """
        창 크기 변경 시 자동으로 정렬 조정
        """
        self.populate_table()
        event.accept()

    def refresh_orders(self):
        """
        새로고침 버튼 클릭 시 상품 목록 갱신
        """
        self.load_products()


class OrdersTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout()

        # 오른쪽 패널 (주문 내역)
        self.right_panel = OrderRightWidget()

        # 왼쪽 패널 (주문 조회) - ✅ 오른쪽 패널을 인자로 전달!
        self.left_widget = OrderLeftWidget(order_right_widget=self.right_panel)

        # ✅ 크기 정책 설정
        self.left_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ✅ 고정 크기 설정
        self.left_widget.setFixedWidth(350)  # 1 비율
        main_layout.addWidget(self.left_widget)
        main_layout.addWidget(self.right_panel)

        self.setLayout(main_layout)
    def do_search(self, keyword):
        pass
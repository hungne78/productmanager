from PyQt5.QtWidgets import QWidget, QHBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,QInputDialog, \
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel, QComboBox, QVBoxLayout, QGridLayout, QScrollArea, QDateEdit
import os
import sys
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QResizeEvent,QFontMetrics, QColor, QStandardItem
import requests
# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_orders, api_create_order, api_update_order, api_delete_order, get_auth_headers
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtGui import QTextDocument, QFont
from PyQt5.QtCore import QSizeF
import json
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
import requests
from collections import OrderedDict

BASE_URL = "http://127.0.0.1:8000"  # 실제 서버 URL
global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)

class OrderLeftWidget(QWidget):
    def __init__(self, parent=None, order_right_widget=None):
        super().__init__(parent)
        self.order_right_widget = order_right_widget  # ✅ 오른쪽 패널을 저장
        self.current_shipment_round = 0  # ✅ 현재 출고 단계 저장 (초기값 0)
        layout = QVBoxLayout()

        # ✅ 1. 날짜 선택을 가장 위로 이동
        self.order_date_label = QLabel("주문 날짜 선택")
        self.order_date_picker = QDateEdit()
        self.order_date_picker.setCalendarPopup(True)
        self.order_date_picker.setDate(QDate.currentDate())
        self.order_date_picker.setMinimumDate(QDate(2025, 4, 1))  # ✅ 필요한 경우 조정
        self.order_date_picker.setMaximumDate(QDate.currentDate())              # ✅ 오늘까지만 선택 가능
        self.selected_order_date = self.order_date_picker.date().toString("yyyy-MM-dd")  # ✅ 초기값 설정
        self.order_date_picker.dateChanged.connect(self.on_date_changed)  # ✅ 이벤트 연결
        self.order_date_picker.dateChanged.connect(self.on_order_date_changed)
        layout.addWidget(self.order_date_label)
        layout.addWidget(self.order_date_picker)

        # ✅ 2. 출고 단계 선택 드롭다운 (현재 출고 가능 단계만 활성화)
        self.shipment_round_dropdown = QComboBox()
        self.shipment_round_dropdown.addItems([f"{i}차 출고" for i in range(1, 11)])  # ✅ 1차 ~ 10차
        self.shipment_round_dropdown.setEnabled(True)  # ✅ 기본적으로 비활성화
        layout.addWidget(QLabel("출고 단계 선택"))
        layout.addWidget(self.shipment_round_dropdown)

        self.lock_button = QPushButton("🚫 주문 종료")
        self.lock_button.clicked.connect(self.lock_order)
        layout.addWidget(self.lock_button)

        self.unlock_button = QPushButton("✅ 주문 해제")
        self.unlock_button.clicked.connect(self.unlock_order)
        layout.addWidget(self.unlock_button)
        
        self.finalize_button = QPushButton("📦 출고 확정")
        self.finalize_button.clicked.connect(self.finalize_inventory)
        layout.addWidget(self.finalize_button)
                         
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

        # ✅ 카테고리 & 브랜드 정렬 구역 라벨
        layout.addWidget(QLabel("🗂️ 카테고리 & 브랜드 순서 정렬"))

        # ✅ 가로 정렬로 감쌀 박스
        sort_layout = QHBoxLayout()

        # ▶️ [1] 카테고리 정렬 영역
        category_group = QVBoxLayout()
        category_group.addWidget(QLabel("📂 카테고리 순서"))
        self.category_list = QListWidget()
        self.category_list.setDragDropMode(QListWidget.InternalMove)
        category_group.addWidget(self.category_list)

        self.save_category_order_button = QPushButton("💾 저장")
        self.save_category_order_button.clicked.connect(self.save_category_order)
        category_group.addWidget(self.save_category_order_button)

        # ▶️ [2] 브랜드 정렬 영역
        brand_group = QVBoxLayout()
        brand_group.addWidget(QLabel("🏷️ 브랜드 순서"))
        self.brand_list = QListWidget()
        self.brand_list.setDragDropMode(QListWidget.InternalMove)
        brand_group.addWidget(self.brand_list)

        self.save_brand_order_button = QPushButton("💾 저장")
        self.save_brand_order_button.clicked.connect(self.save_brand_order)
        brand_group.addWidget(self.save_brand_order_button)

        # ▶️ 두 영역을 sort_layout에 추가
        sort_layout.addLayout(category_group)
        sort_layout.addLayout(brand_group)

        # ▶️ 메인 레이아웃에 추가
        layout.addLayout(sort_layout)

        # ✅ 최초 실행 시 목록 불러오기
        self.load_category_list_from_server()
        self.load_brand_list_from_server()

        
        self.current_round_orders_button = QPushButton("이번차수 전체 주문조회<<<")
        self.current_round_orders_button.clicked.connect(self.fetch_orders_for_current_shipment)
        layout.addWidget(self.current_round_orders_button)

        # ✅ 4. "전체 주문 조회" 버튼 추가
        self.order_button = QPushButton("전체 주문 조회")
        self.order_button.clicked.connect(self.fetch_orders_for_all_employees)  # ✅ 전체 주문 조회
        layout.addWidget(self.order_button)
        # ✅ 초기 UI 로드 시 출고 확정 상태 확인
        self.check_finalized_status()
        self.setLayout(layout)
         # ✅ 현재 출고 단계 불러오기
        self.fetch_current_shipment_round()
    
    def fetch_orders_for_current_shipment(self):
        """
        현재(시스템에서 받아둔) 출고 차수의 주문을 전직원 대상으로 조회하여 합산 후 표시한다.
        """
        selected_date = self.order_date_picker.date().toString("yyyy-MM-dd")
        # fetch_current_shipment_round() 에서 받아둔 현재 출고 차수를 사용 (예: 0부터 시작)
        current_round = self.current_shipment_round

        url = f"{BASE_URL}/employees/"
        headers = {"Authorization": f"Bearer {global_token}"}
        aggregated_orders = {}

        try:
            # 1. 모든 직원 목록 조회
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                employees = resp.json()
            else:
                print(f"❌ 직원 목록 조회 실패: {resp.status_code}, 응답: {resp.text}")
                return

            # 2. 각 직원의 주문 조회 (현재 출고 차수만)
            for employee in employees:
                employee_id = employee["id"]
                order_url = (f"{BASE_URL}/orders/orders_with_items?employee_id={employee_id}"
                            f"&date={selected_date}&shipment_round={current_round}")
                order_resp = requests.get(order_url, headers=headers)

                if order_resp.status_code == 200:
                    orders = order_resp.json()
                    for order in orders:
                        # 만약 응답에 출고 차수 정보가 있고 다르면 무시
                        if order.get("shipment_round") != current_round:
                            continue
                        for item in order["items"]:
                            product_id = item["product_id"]
                            quantity = item["quantity"]

                            key = (product_id, current_round)
                            if key in aggregated_orders:
                                aggregated_orders[key]["quantity"] += quantity
                            else:
                                aggregated_orders[key] = {
                                    "product_id": product_id,
                                    "product_name": item["product_name"],
                                    "quantity": quantity
                                }
                else:
                    print(f"❌ 직원 {employee_id}의 주문 조회 실패: {order_resp.status_code}")

            # 3. 합산된 주문 데이터를 오른쪽 패널에 표시
            aggregated_order_list = list(aggregated_orders.values())
            print(f"📌 이번차수 최종 합산 주문 데이터: {aggregated_order_list}")
            self.display_orders([{"order_id": "all", "items": aggregated_order_list}])
        except Exception as e:
            print(f"❌ 오류 발생: {e}")


    
    def load_brand_list_from_server(self):
        try:
            resp = requests.get(f"{BASE_URL}/products/brands/order")  # ✅ 순서 포함된 엔드포인트로 변경
            resp.raise_for_status()
            brand_names = resp.json()

            self.brand_list.clear()
            for name in brand_names:
                self.brand_list.addItem(name)

            # print("✅ 브랜드 정렬 순서 불러오기 완료:", brand_names)
        except Exception as e:
            print(f"❌ 브랜드 목록 불러오기 실패: {e}")


    def save_brand_order(self):
        brand_order = [self.brand_list.item(i).text() for i in range(self.brand_list.count())]
        try:
            resp = requests.post(
                f"{BASE_URL}/products/brands/order",
                json=brand_order
            )
            resp.raise_for_status()
            print("✅ 브랜드 순서 저장 완료")
        except Exception as e:
            print(f"❌ 브랜드 순서 저장 실패: {e}")

    
    def save_category_order(self):
        order = [self.category_list.item(i).text() for i in range(self.category_list.count())]
        # print("✅ 저장된 카테고리 순서:", order)

        # 1️⃣ 로컬 저장
        with open("category_order.json", "w", encoding="utf-8") as f:
            json.dump(order, f, ensure_ascii=False, indent=2)

        # 2️⃣ 서버에 업로드
        url = f"{BASE_URL}/products/category_order"
        headers = {
            "Authorization": f"Bearer {global_token}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(url, headers=headers, json={"order": order})
            if response.status_code == 200:
                print("✅ 서버에 카테고리 순서 업로드 완료")
            else:
                print(f"❌ 서버 업로드 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ 서버 업로드 중 예외 발생: {e}")

        # 3️⃣ 우측 테이블 갱신
        if self.order_right_widget:
            self.order_right_widget.set_category_order(order)
            self.order_right_widget.populate_table()

    
    def load_category_order(self):
        import os
        if os.path.exists("category_order.json"):
            with open("category_order.json", "r", encoding="utf-8") as f:
                order = json.load(f)
                self.category_list.clear()
                for category in order:
                    self.category_list.addItem(QListWidgetItem(category))

            if self.order_right_widget:
                self.order_right_widget.set_category_order(order)

        
    def load_category_list_from_server(self):
        url = f"{BASE_URL}/products/categories"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                categories = response.json()
                if not os.path.exists("category_order.json"):
                    self.category_list.clear()
                    for category in categories:
                        self.category_list.addItem(QListWidgetItem(category))
                else:
                    self.load_category_order()
            else:
                print(f"❌ 카테고리 목록 불러오기 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ 카테고리 목록 요청 실패: {e}")


    
    def on_order_date_changed(self):
        """
        주문 날짜가 변경될 때 출고 단계를 새로 가져오고 드롭다운을 업데이트
        """
        self.fetch_current_shipment_round()  # ✅ 새 출고 단계 가져오기


    def update_shipment_dropdown(self):
        """
        모든 출고 차수를 활성화하고, 현재 출고 차수를 강조(예: 파란색/굵은 글씨)하여 표시합니다.
        """
        self.shipment_round_dropdown.clear()  # 기존 항목 초기화

        for i in range(10):  # 1차 ~ 10차까지 표시
            item_text = f"{i + 1}차 출고"
            item = QStandardItem(item_text)
            # 모든 항목 활성화
            item.setEnabled(True)
            # 현재 출고 차수는 강조(예: 파란색, 굵은 글씨)
            if i == self.current_shipment_round:
                item.setForeground(QColor(0, 0, 255))  # 파란색
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            else:
                item.setForeground(QColor(0, 0, 0))
            self.shipment_round_dropdown.model().appendRow(item)

        # 기본 선택은 현재 출고 차수로 설정
        self.shipment_round_dropdown.setCurrentIndex(self.current_shipment_round)
        self.shipment_round_dropdown.setEnabled(True)
        print(f"📌 [디버깅] 현재 출고 차수는 {self.current_shipment_round + 1}차로 표시됩니다.")



    def fetch_current_shipment_round(self):
        """
        서버에서 현재 출고 단계를 가져와서 드롭다운을 업데이트
        """
        selected_date = self.order_date_picker.date().toString("yyyy-MM-dd")
        url = f"{BASE_URL}/orders/current_shipment_round/{selected_date}"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.current_shipment_round = data.get("shipment_round", 0)  # ✅ 기본값 0

                # ✅ 출고 차수 드롭다운 업데이트 함수 호출
                self.update_shipment_dropdown()

                print(f"📌 [디버깅] {selected_date} 출고 차수: {self.current_shipment_round}")

            else:
                print(f"❌ 출고 단계 조회 실패: {response.text}")
        except Exception as e:
            print(f"❌ 출고 단계 조회 중 오류 발생: {e}")

    def check_finalized_status(self):
        """
        출고 확정 상태를 확인하여 버튼을 비활성화
        """
        url = f"{BASE_URL}/orders/lock_status/{self.selected_order_date}"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                lock_status = response.json()
                if lock_status["is_finalized"]:  # ✅ 출고 확정 여부 확인
                    self.finalize_button.setEnabled(False)  # ✅ 출고 확정 버튼 비활성화
                    self.finalize_button.setText("출고 완료됨 ✅")
            else:
                print(f"❌ 출고 확정 상태 확인 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ 서버 오류 발생: {e}")

    def finalize_inventory(self):
        """
        선택한 출고 단계를 서버로 전송하여 출고 확정 실행
        """
        selected_date = self.order_date_picker.date().toString("yyyy-MM-dd")
        selected_round = self.shipment_round_dropdown.currentIndex() + 1  # ✅ 콤보박스 인덱스 (0부터 시작하므로 +1)

        url = f"{BASE_URL}/inventory/finalize_inventory/{selected_date}?shipment_round={selected_round}"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                QMessageBox.information(self, "성공", f"{selected_round}차 출고가 확정되었습니다.")
                self.fetch_current_shipment_round()  # ✅ 출고 확정 후 드롭다운 업데이트
            else:
                if "주문이 없어서 출고차수가 변경되지 않았습니다" in response.text:
                    QMessageBox.information(self, "안내", "🚫 주문이 없어 출고차수가 변경되지 않았습니다.")
                else:
                    QMessageBox.critical(self, "실패", f"출고 확정 실패: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류 발생", f"서버 요청 오류: {e}")
            
    def on_date_changed(self):
        """
        날짜 선택 시 `self.selected_order_date`를 업데이트하고 오른쪽 패널에도 전달
        """
        self.selected_order_date = self.order_date_picker.date().toString("yyyy-MM-dd")
        print(f"✅ 선택된 주문 날짜: {self.selected_order_date}")

        # ✅ 오른쪽 패널이 존재하면 날짜 업데이트
        if self.order_right_widget:
            self.order_right_widget.set_selected_order_date(self.selected_order_date)

    def lock_order(self):
        """
        선택한 날짜의 주문을 차단
        """
        selected_date = self.order_date_picker.date().toString("yyyy-MM-dd")
        url = f"{BASE_URL}/orders/lock/{selected_date}"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                QMessageBox.information(self, "성공", f"{selected_date} 주문이 종료되었습니다.")
            else:
                QMessageBox.critical(self, "실패", f"주문 종료 실패: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류 발생", f"서버 요청 오류: {e}")

    def unlock_order(self):
        """
        선택한 날짜의 주문 차단을 해제
        """
        selected_date = self.order_date_picker.date().toString("yyyy-MM-dd")
        url = f"{BASE_URL}/orders/unlock/{selected_date}"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                QMessageBox.information(self, "성공", f"{selected_date} 주문 차단이 해제되었습니다.")
            else:
                QMessageBox.critical(self, "실패", f"주문 차단 해제 실패: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류 발생", f"서버 요청 오류: {e}")

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
        주문 데이터를 오른쪽 패널의 테이블에 표시 (출고 차수 적용)
        """
        print(f"📌 [display_orders] 호출됨, 받은 데이터: {orders}")  
        if self.order_right_widget:
            self.order_right_widget.update_orders(orders)  
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
        선택한 날짜와 직원 ID를 기반으로 주문 데이터 가져오기 (출고 차수 포함)
        """
        selected_date = self.order_date_picker.date().toString("yyyy-MM-dd")
        selected_round = self.shipment_round_dropdown.currentIndex()  # ✅ 선택된 출고 차수

        url = f"{BASE_URL}/orders/orders_with_items?employee_id={employee_id}&date={selected_date}&shipment_round={selected_round}"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                orders = resp.json()
                print(f"📌 직원 {employee_id}의 {selected_round}차 주문 조회 성공: {orders}")  
                self.display_orders(orders)
                self.update_employee_buttons(employee_id)  
            else:
                print(f"❌ 주문 조회 실패: {resp.status_code}, 응답: {resp.text}")
                QMessageBox.warning(self, "주문 조회 실패", "주문 데이터를 불러오지 못했습니다.")
                if self.order_right_widget:
                    self.order_right_widget.reset_orders_to_zero()  

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            QMessageBox.warning(self, "오류 발생", f"주문 조회 중 오류 발생: {e}")


    def update_employee_buttons(self, selected_employee_id):
        """
        선택한 직원 버튼 스타일 변경 (선택된 버튼 강조)
        """
        for btn in self.employee_buttons:
            if btn.property("employee_id") == selected_employee_id:
                btn.setStyleSheet("background-color: lightblue; font-weight: bold;")
            else:
                btn.setStyleSheet("")  # ✅ 다른 버튼들은 원래 스타일로 되돌림

    def reset_orders_to_zero(self):
        """
        주문이 없는 경우 모든 상품의 주문 수량을 0으로 초기화
        """
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, QTableWidget):
                for row in range(widget.rowCount()):
                    quantity_item = widget.item(row, 1)  # ✅ 수량 열(두 번째 열)
                    if quantity_item:
                        quantity_item.setText("0")
        print("🔄 주문이 없는 경우 모든 수량을 0으로 초기화 완료")

    def fetch_orders_for_all_employees(self):
        """
        모든 직원의 주문을 개별 조회 후, 상품별로 합산하여 표시 (출고 차수 포함)
        """
        selected_date = self.order_date_picker.date().toString("yyyy-MM-dd")
        selected_round = self.shipment_round_dropdown.currentIndex()  # ✅ 선택된 출고 차수

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
                order_url = f"{BASE_URL}/orders/orders_with_items?employee_id={employee_id}&date={selected_date}&shipment_round={selected_round}"
                order_resp = requests.get(order_url, headers=headers)

                if order_resp.status_code == 200:
                    orders = order_resp.json()
                    for order in orders:
                        if order["shipment_round"] != selected_round:  # ✅ 출고 차수가 다르면 무시
                            continue

                        for item in order["items"]:
                            product_id = item["product_id"]
                            quantity = item["quantity"]

                            if (product_id, selected_round) in aggregated_orders:
                                aggregated_orders[(product_id, selected_round)]["quantity"] += quantity
                            else:
                                aggregated_orders[(product_id, selected_round)] = {
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
        self.category_order = []

        self.selected_order_date = QDate.currentDate().toString("yyyy-MM-dd")  # ✅ 기본값: 오늘 날짜
        self.current_products = []  # ✅ 상품 목록 저장
        self.selected_order_id = None  # ✅ 선택한 주문 ID 저장
        self.current_items = []
        self.current_mode = "전체"
        # ✅ 주문 수정 버튼 추가
        self.update_button = QPushButton("✏️ 주문 수정")
        self.update_button.clicked.connect(self.fix_order)
        self.update_button.setEnabled(False)
        self.layout.addWidget(self.update_button)

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
        # ✅ 스크롤 영역 추가
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.container)


        self.layout.addWidget(self.scroll_area)
        self.total_items_label = QLabel("📦 총 주문 품목 수: 0")
        self.total_quantity_label = QLabel("💰 총 주문 수량: 0")
        self.layout.addWidget(self.total_items_label)
        self.layout.addWidget(self.total_quantity_label)
        # ✅ 인쇄 버튼 추가
        self.print_button = QPushButton("🖨️ 인쇄")
        self.print_button.clicked.connect(self.on_print_clicked)
        self.layout.addWidget(self.print_button)

        self.setLayout(self.layout)
        self.load_products()  # ✅ 서버에서 상품 목록 로드
    
    def set_category_order(self, order_list):
        self.category_order = order_list
    
    def update_mode(self, mode_str):
        self.current_mode = mode_str  # "전체" or 직원명

    def update_date(self, date_str):
        self.current_date = date_str

    def update_items(self, items):
        """
        items: [ { "product_name":..., "quantity":... }, ... ]
        """
        self.current_items = items
        QMessageBox.information(self, "주문 내역", f"주문 {len(items)}개 로드됨")

    def set_selected_order_date(self, date_str):
        self.current_date = date_str

    def on_print_clicked(self):
        # 1) 테이블에 표시된 순서 그대로 아이템 목록을 가져온다.
        items_in_table_order = self.gather_current_items_in_ui_order()

        # 2) “주문 날짜/모드”는 기존처럼 가져오거나, self.selected_order_date 등 사용
        order_date = self.selected_order_date
        mode = self.current_mode

        # 3) QPainter로 인쇄
        self.print_orders_painter(items_in_table_order, order_date, mode)

    def print_orders_painter(self, items, order_date, mode):
        from PyQt5.QtGui import QPainter, QFont
        from PyQt5.QtCore import QRectF, Qt
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

        printer = QPrinter(QPrinter.HighResolution)
        ...

        dlg = QPrintDialog(printer, self)
        if dlg.exec_() != QPrintDialog.Accepted:
            return

        margin_mm = 10
        page_width_mm = 210 - margin_mm * 2
        page_height_mm = 297 - margin_mm * 2

        total_columns = 16
        rows = 63
        pairs_count = total_columns // 2

        width_per_pair_mm = page_width_mm / pairs_count
        name_col_ratio = 0.6
        qty_col_ratio = 0.4
        cell_h_mm = page_height_mm / rows

        dpmm = printer.resolution() / 25.4
        name_col_w_px = (width_per_pair_mm * name_col_ratio) * dpmm
        qty_col_w_px  = (width_per_pair_mm * qty_col_ratio)  * dpmm
        cell_h_px     = cell_h_mm * dpmm
        margin_x_px   = margin_mm * dpmm
        margin_y_px   = margin_mm * dpmm

        painter = QPainter()
        if not painter.begin(printer):
            print("❌ QPainter 시작 실패")
            return

        # 제목
        font_title = QFont("Arial", 12)
        painter.setFont(font_title)
        painter.drawText(int(margin_x_px), int(margin_y_px - 3*dpmm),
                        f"주문 날짜: {order_date} / {mode}")

        # 표 폰트
        font_cell = QFont("Arial", 7)
        painter.setFont(font_cell)

        max_items = pairs_count * rows
        item_count = min(len(items), max_items)

        for i in range(item_count):
            col_pair = i // rows
            row_idx  = i % rows

            x_name = margin_x_px + col_pair*(name_col_w_px + qty_col_w_px)
            x_qty  = x_name + name_col_w_px
            y_row  = margin_y_px + row_idx*cell_h_px

            rect_name = QRectF(x_name, y_row, name_col_w_px, cell_h_px)
            rect_qty  = QRectF(x_qty,  y_row, qty_col_w_px, cell_h_px)

            data = items[i]
            product_name = data.get("product_name", "❌ 없음")
            quantity_val = data.get("quantity", None)
            is_cat       = data.get("is_category", False)

            if is_cat:
                # ▷ 카테고리 행: 2칸 합쳐서 중앙 정렬
                merged_rect = QRectF(x_name, y_row,
                                    name_col_w_px + qty_col_w_px,
                                    cell_h_px)
                painter.drawRect(merged_rect)
                painter.drawText(merged_rect, int(Qt.AlignCenter), product_name)

            else:
                # ▷ 일반 상품 행: 왼쪽(상품명) + 오른쪽(수량)
                painter.drawRect(rect_name)
                painter.drawRect(rect_qty)

                # 상품명 왼쪽 정렬
                painter.drawText(rect_name, int(Qt.AlignVCenter|Qt.AlignLeft), product_name)

                # 수량(없으면 0)
                qty_str = str(quantity_val if quantity_val is not None else 0)
                painter.drawText(rect_qty, int(Qt.AlignCenter), qty_str)

        # 남은 칸은 빈칸
        total_cells = pairs_count*rows
        for i in range(item_count, total_cells):
            col_pair = i // rows
            row_idx  = i % rows
            x_name = margin_x_px + col_pair*(name_col_w_px + qty_col_w_px)
            x_qty  = x_name + name_col_w_px
            y_row  = margin_y_px + row_idx*cell_h_px

            rect_name = QRectF(x_name, y_row, name_col_w_px, cell_h_px)
            rect_qty  = QRectF(x_qty,  y_row, qty_col_w_px, cell_h_px)
            painter.drawRect(rect_name)
            painter.drawRect(rect_qty)

        painter.end()
        print("✅ 인쇄 완료")



    def gather_current_items_in_ui_order(self):
        collected_items = []

        for table_index in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(table_index).widget()
            if not isinstance(widget, QTableWidget):
                continue

            for row in range(widget.rowCount()):
                product_name_item = widget.item(row, 0)  # 첫 칸
                quantity_item = widget.item(row, 1)     # 두 번째 칸(수량)

                if product_name_item is None:
                    continue

                product_name = product_name_item.text().strip()
                if not product_name:
                    continue

                # [A] 여기서 UserRole을 확인: 
                #     is_category = True/False
                role_data = product_name_item.data(Qt.UserRole)
                is_category = bool(role_data)  # True면 카테고리 행

                if is_category:
                    # 카테고리 행: 2칸 span되어 수량칸은 무의미
                    collected_items.append({
                        "product_name": product_name,
                        "quantity": None,
                        "is_category": True
                    })
                else:
                    # 일반 상품 행
                    qty_val = 0
                    if quantity_item:
                        qtext = quantity_item.text().strip()
                        if qtext:
                            try:
                                qty_val = int(qtext)
                            except:
                                qty_val = 0
                    collected_items.append({
                        "product_name": product_name,
                        "quantity": qty_val,
                        "is_category": False
                    })

        return collected_items



    def print_orders(self):
        """
        QPainter로 A4 한 장에 16칸×50행 표를 그려 출력.
        폰트가 커도 셀이 안 늘어나므로, 칸보다 크면 텍스트 잘릴 수 있음.
        """
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt5.QtGui import QPainter, QFont
        from PyQt5.QtCore import QRectF

        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        printer.setOrientation(QPrinter.Portrait)
        printer.setFullPage(True)
        printer.setResolution(300)  # 300 DPI (픽셀/인치)

        dlg = QPrintDialog(printer, self)
        if dlg.exec_() != QPrintDialog.Accepted:
            return

        # A4 = 210×297mm
        # 여백 10mm씩 설정 → 남는 폭=190mm, 높이=277mm
        margin_mm = 10
        page_width_mm = 210 - margin_mm*2  # 190mm
        page_height_mm = 297 - margin_mm*2 # 277mm

        # 16열 × 50행
        cols = 16
        rows = 50

        cell_w_mm = page_width_mm / cols   # 190/16 = 11.875mm
        cell_h_mm = page_height_mm / rows  # 277/50 = 5.54mm

        # mm → device coordinate 변환
        # (300 dpi) 1 inch = 25.4mm, 1mm ≈ 11.81 device units
        dpmm = printer.resolution() / 25.4
        cell_w_px = cell_w_mm * dpmm
        cell_h_px = cell_h_mm * dpmm

        painter = QPainter()
        painter.begin(printer)

        # Font 설정 (너무 크면 글자 잘림)
        font = QFont("Arial", 7)  # 8pt 정도
        painter.setFont(font)

        # 왼쪽/위쪽 여백
        margin_x_px = margin_mm * dpmm
        margin_y_px = margin_mm * dpmm

        # 테이블 그리기
        # y = margin_y_px
        for r in range(rows):
            # x = margin_x_px
            for c in range(cols):
                # 각 셀의 좌표(픽셀)
                x = margin_x_px + c * cell_w_px
                y = margin_y_px + r * cell_h_px

                # 사각형
                rect = QRectF(x, y, cell_w_px, cell_h_px)
                painter.drawRect(rect)

                # 예시 텍스트
                text = f"({r+1},{c+1})"

                # drawText(사각형, flag, text)
                # 너무 긴 텍스트면 잘릴 수 있음
                painter.drawText(rect, 
                                int(Qt.AlignCenter|Qt.TextWordWrap), 
                                text)
        
        painter.end()


    def reset_orders_to_zero(self):
        """
        주문이 없는 경우 모든 상품의 주문 수량을 0으로 초기화
        """
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, QTableWidget):
                for row in range(widget.rowCount()):
                    quantity_item = widget.item(row, 1)  # ✅ 수량 열(두 번째 열)
                    if quantity_item:
                        quantity_item.setText("0")
        print("🔄 주문이 없는 경우 모든 수량을 0으로 초기화 완료")
        
    def set_selected_order_date(self, order_date):
        """
        왼쪽 패널에서 선택한 날짜를 오른쪽 패널에 저장
        """
        self.selected_order_date = order_date
        print(f"✅ [OrderRightWidget] 선택된 주문 날짜 업데이트: {self.selected_order_date}")


    def fix_order(self):
        """
        기존 테이블에서 선택한 날짜 주문에서 '주문 수량(갯수)'만 수정하여 서버로 전송
        """
        if not self.selected_order_date:
            self.selected_order_date = QDate.currentDate().toString("yyyy-MM-dd")  # ✅ 날짜가 None이면 오늘 날짜로 설정
            print(f"✅ [자동 설정] 선택된 주문 날짜: {self.selected_order_date}")

        print(f"📝 [DEBUG] 주문 수정 요청 진행")
        print(f"📝 선택된 상품 ID: {getattr(self, 'selected_order_id', None)}")
        print(f"📝 선택된 상품명: {getattr(self, 'selected_product_name', None)}")
        print(f"📝 선택된 주문 날짜: {getattr(self, 'selected_order_date', None)}")

        # ✅ 필수값이 없는 경우 오류 메시지 출력
        if not all([
            getattr(self, 'selected_order_id', None),
            getattr(self, 'selected_product_name', None),
            getattr(self, 'selected_order_date', None)
        ]):
            print("⚠️ [DEBUG] 필수값 누락 → 주문 수정 불가")
            QMessageBox.warning(self, "오류", "수정할 주문을 선택하세요.")
            return

        print(f"📝 주문 수량 수정 진행: 상품 ID={self.selected_order_id}, 상품명={self.selected_product_name}, 날짜={self.selected_order_date}")

        selected_order_row = None
        selected_table = None  # ✅ 현재 선택된 테이블 저장

        # ✅ 현재 grid_layout 내의 테이블을 순회하여 선택된 주문을 찾기
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, QTableWidget):
                for row in range(widget.rowCount()):
                    product_name_item = widget.item(row, 0)  # ✅ 첫 번째 열(상품명)
                    if product_name_item:
                        product_name_text = product_name_item.text().strip().lower()  # ✅ 공백 제거 및 소문자로 변환
                        selected_product_name_text = self.selected_product_name.strip().lower()

                        if product_name_text == selected_product_name_text:
                            selected_order_row = row
                            selected_table = widget  # ✅ 현재 사용 중인 테이블 저장
                            break

        if selected_order_row is None or selected_table is None:
            QMessageBox.warning(self, "오류", "선택된 주문을 찾을 수 없습니다.")
            return

        # ✅ 기존 값 가져오기 (주문 수량)
        quantity_item = selected_table.item(selected_order_row, 1)  # ✅ "갯수" 열(두 번째 열)
        existing_quantity = int(quantity_item.text()) if quantity_item else 0

        # ✅ 팝업 창을 띄워 수정할 주문 수량 입력 받기
        new_quantity, ok = QInputDialog.getInt(self, "주문 수량 수정", "새 주문 수량 입력:", existing_quantity)

        if not ok:
            return  # ✅ 사용자가 입력을 취소하면 종료

        # ✅ FastAPI의 `product_id` + `order_date`를 사용하여 요청 보내기 (is_admin=True 추가)
        url = f"{BASE_URL}/orders/update_quantity/{self.selected_order_id}/?order_date={self.selected_order_date}&is_admin=True"
        headers = {"Authorization": f"Bearer {global_token}", "Content-Type": "application/json"}
        data = {
            "quantity": new_quantity  # ✅ 주문 수량(갯수)만 변경
        }

        try:
            response = requests.put(url, json=data, headers=headers)
            if response.status_code == 200:
                QMessageBox.information(self, "성공", "주문 수량이 수정되었습니다.")
                quantity_item.setText(str(new_quantity))  # ✅ 테이블에서 주문 수량 업데이트
            else:
                QMessageBox.critical(self, "실패", f"주문 수량 수정 실패: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류 발생", f"서버 요청 오류: {e}")




            
    def select_order_for_edit(self, row, column):
        """
        기존 테이블에서 선택한 상품의 주문 수량을 수정할 수 있도록 설정
        """
        sender_table = self.sender()  # ✅ 클릭된 `QTableWidget` 가져오기
        if not sender_table:
            return

        product_name_item = sender_table.item(row, 0)  # ✅ 첫 번째 열(품명)
        quantity_item = sender_table.item(row, 1)  # ✅ 두 번째 열(갯수)

        # ✅ 품명 또는 수량을 클릭했을 때 수정 기능 실행
        if column == 0 or column == 1:
            if product_name_item:
                self.selected_product_name = product_name_item.text().strip()
                print(f"📝 선택된 상품: {self.selected_product_name}")

                # ✅ 기존 주문 데이터에서 해당 상품 ID 찾기
                self.selected_order_id = None
                for order in self.current_products:
                    if order["product_name"] == self.selected_product_name:
                        try:
                            self.selected_order_id = int(order["id"])  # ✅ 주문 ID 변환
                            print(f"✅ 주문 선택됨: ID={self.selected_order_id}")
                            self.update_button.setEnabled(True)  # ✅ 수정 버튼 활성화
                        except ValueError:
                            print(f"❌ 주문 ID 변환 실패: {order['id']}")
                            self.selected_order_id = None
                        break

                if self.selected_order_id is None:
                    print("❌ 선택한 상품에 대한 주문 ID를 찾을 수 없습니다.")
                    QMessageBox.warning(self, "오류", "선택한 상품에 대한 주문이 없습니다.")



    def populate_table(self):
        """
        서버에서 정렬된 상품 목록을 그대로 표시 (카테고리 → 브랜드 → 품명 순서 유지)
        """
        # 기존 위젯 제거
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        available_height = self.height() - self.header_layout.sizeHint().height() - 80
        row_height = 30
        max_rows_per_section = max(5, available_height // row_height)

        row = 0
        col = 0
        table = None
        row_index = 0
        current_category = None
        current_brand = None

        # ✅ 정렬 없이 그대로 사용
        products_to_display = self.current_products

        for product in products_to_display:
            category = product.get("category", "")
            brand = product.get("brand_name", "")
            product_name = product.get("product_name", "")

            if row_index == 0 or table is None:
                table = QTableWidget()
                table.setColumnCount(2)
                table.setHorizontalHeaderLabels(["품명", "갯수"])
                header = table.horizontalHeader()
                header.setSectionResizeMode(0, QHeaderView.Stretch)
                header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
                table.setFont(QFont("Arial", 9))
                table.verticalHeader().setVisible(False)
                table.setRowCount(0)
                table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                table.setMinimumWidth(300)
                table.cellClicked.connect(self.select_order_for_edit)

            # ✅ 카테고리 제목 추가
            if current_category != category:
                table.insertRow(table.rowCount())
                category_item = QTableWidgetItem(category)
                category_item.setFont(QFont("Arial", 9, QFont.Bold))
                category_item.setTextAlignment(Qt.AlignCenter)
                category_item.setData(Qt.UserRole, True)
                table.setSpan(table.rowCount() - 1, 0, 1, 2)
                table.setItem(table.rowCount() - 1, 0, category_item)
                current_category = category
                current_brand = None  # 브랜드 초기화

            # ✅ 브랜드 구분용 빈 줄 추가 가능 (옵션)
            if current_brand != brand:
                current_brand = brand
                # 원하면 브랜드 타이틀 줄도 추가 가능

            table.insertRow(table.rowCount())
            table.setItem(table.rowCount() - 1, 0, self.create_resized_text(product_name, table))
            table.setItem(table.rowCount() - 1, 1, QTableWidgetItem(""))
            name_item = self.create_resized_text(product_name, table)
            # 카테고리가 아닌 일반 상품이므로, UserRole=False (또는 설정 안 함)
            name_item.setData(Qt.UserRole, False)
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
        주문 데이터를 받아서 기존 테이블의 두 번째 열(수량)에 반영 (출고 차수 적용)
        그리고 self.current_items 에 주문 데이터를 저장하여 프린트 시 품목명이 나오도록 함
        """
        print("\n🔹 [update_orders] 호출됨")
        print(f"🔹 받은 주문 데이터: {orders}")

        order_quantity_map = {item["product_id"]: item["quantity"] for order in orders for item in order["items"]}
        print(f"📌 주문 ID → 수량 매핑 결과: {order_quantity_map}")

        # ✅ 현재 로드된 상품 목록 출력
        print(f"📌 현재 로드된 상품 목록 (self.current_products):")
        for p in self.current_products:
            print(f"   - ID: {p['id']}, 이름: {p['product_name']}")

        # ✅ self.current_items 초기화 후 주문 데이터를 저장
        self.current_items = []  # <<<<< ✅ 여기가 핵심

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

                        matching_product = next((p for p in self.current_products if p["product_name"] == product_name), None)

                        if matching_product:
                            product_id = matching_product["id"]
                            print(f"   ✅ 상품 매칭됨 → ID: {product_id}, 이름: {product_name}")

                            if product_id in order_quantity_map:
                                quantity = order_quantity_map[product_id]
                                quantity_item.setText(str(quantity))
                                print(f"   📝 수량 업데이트: {quantity}")

                                # ✅ 주문 목록을 self.current_items 에 추가
                                self.current_items.append({
                                    "product_name": product_name,
                                    "quantity": quantity
                                })
                            else:
                                quantity_item.setText("")  # 주문이 없으면 빈 값 유지
                                print(f"   ❌ 주문 없음 → 수량 비움")
                        else:
                            print(f"   ❌ {product_name}에 해당하는 상품을 찾을 수 없음 (self.current_products에 없음)")

                    else:
                        print(f"   ❗ row={row}에서 product_name_item 또는 quantity_item이 없음")

        # ✅ self.current_items에 저장된 데이터 확인
        print(f"\n✅ 현재 주문 목록 저장됨 (self.current_items): {self.current_items}")


    def fetch_orders_for_whole_day(self):
        """
        선택된 날짜의 전체 주문을 가져와 표시 (출고 차수 관계 없음)
        """
        selected_date = self.order_date_picker.date().toString("yyyy-MM-dd")

        url = f"{BASE_URL}/orders/orders_with_items?date={selected_date}&all_shipment_rounds=True"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                orders = response.json()
                print(f"📌 [전체 주문 조회] {selected_date}: {orders}")
                self.display_orders(orders)
            else:
                print(f"❌ 전체 주문 조회 실패: {response.status_code}, 응답: {response.text}")
        except Exception as e:
            print(f"❌ 오류 발생: {e}")


    def refresh_orders(self):
        """
        새로고침 버튼 클릭 시 주문 목록 갱신
        """
        self.orders_table.clearContents()
        self.orders_table.setRowCount(0)

        
    

    def load_products(self):
        try:
            url = f"{BASE_URL}/products/grouped"
            response = requests.get(url)
            response.raise_for_status()

            grouped_raw = response.json()

            # ✅ OrderedDict로 순서 유지
            grouped = OrderedDict()
            flat_product_list = []

            for category in grouped_raw:
                brand_group = grouped_raw[category]
                ordered_brand_group = OrderedDict()
                for brand_name in brand_group:
                    products = brand_group[brand_name]
                    ordered_brand_group[brand_name] = products

                    # ✅ 상품 평탄화
                    for p in products:
                        p["category"] = category
                        p["brand_name"] = brand_name
                        flat_product_list.append(p)

                grouped[category] = ordered_brand_group

            # ✅ 디버깅 출력
            print("✅ 서버에서 받은 정렬 결과:")
            for cat, brands in grouped.items():
                print(f"📦 {cat} → {list(brands.keys())}")

            # 저장
            self.current_products = flat_product_list  # ✅ 테이블에 쓸 리스트 저장
            self.grouped_products = grouped            # (선택) 원형도 보관

        except Exception as e:
            print(f"❌ 상품 불러오기 실패: {e}")
    
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
        self.left_panel = OrderLeftWidget(order_right_widget=self.right_panel)

        # ✅ 크기 정책 설정
        self.left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ✅ 고정 크기 설정
        self.left_panel.setFixedWidth(350)  # 1 비율
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)

        self.setLayout(main_layout)
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
    def do_search(self, keyword):
        pass
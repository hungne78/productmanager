from PyQt5.QtWidgets import QWidget, QHBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel, QDialog, QVBoxLayout, QListWidget, QComboBox, QGroupBox,QPlainTextEdit,QFileDialog
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
import json
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import QProgressDialog

global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)

class ProductDialog(QDialog):
    def __init__(self, title, product=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(500, 600)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # ✅ 브랜드 ID
        self.brand_name_combo = QComboBox()
        self.refresh_brand_names()  # 서버에서 브랜드명 리스트 불러오기
        form_layout.addRow("브랜드명:", self.brand_name_combo)

        # ✅ 상품명
        self.name_edit = QLineEdit()
        form_layout.addRow("상품명:", self.name_edit)

        # ✅ 여러 바코드 입력 (QPlainTextEdit)
        # 기존: self.barcode_edit = QLineEdit()
        # 바꿈: 여러 줄로 바코드를 입력할 수 있게
        self.barcodes_edit = QPlainTextEdit()
        self.barcodes_edit.setPlaceholderText("바코드를 여러 줄로 입력하세요.\n예:\n12345\n67890\n...")
        form_layout.addRow("바코드 목록:", self.barcodes_edit)

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
        self.price_type_edit.addItems(["일반가", "고정가"]) 
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
            brand_name = product.get("brand_name", "")
            index = self.brand_name_combo.findText(brand_name)
            if index >= 0:
                self.brand_name_combo.setCurrentIndex(index)
            self.name_edit.setText(product.get("product_name", ""))
            # 바코드는 여러 개일 수 있으므로, 줄바꿈으로 join
            # product["barcodes"] = ["12345","67890"] 라고 가정
            barcodes_list = product.get("barcodes", [])
            barcodes_text = "\n".join(barcodes_list)
            self.barcodes_edit.setPlainText(barcodes_text)

            self.price_edit.setText(str(product.get("default_price", "0")))
            self.incentive_edit.setText(str(product.get("incentive", "0")))
            self.stock_edit.setText(str(product.get("stock", "0")))
            self.box_quantity_edit.setText(str(product.get("box_quantity", "1")))
            self.active_edit.setCurrentIndex(0 if product.get("is_active", 1) == 1 else 1)
            self.category_edit.setText(product.get("category", ""))
            self.price_type_edit.setCurrentIndex(1 if product.get("is_fixed_price", False) else 0)

    def refresh_brand_names(self):
        try:
            resp = requests.get(
                "http://127.0.0.1:8000/brands/",
                headers={"Authorization": f"Bearer {global_token}"}
            )
            if resp.status_code == 200:
                brand_list = resp.json()
                self.brand_name_combo.clear()
                if not brand_list:
                    QMessageBox.warning(self, "경고", "등록된 브랜드가 없습니다.")
                    return
                for brand in brand_list:
                    self.brand_name_combo.addItem(brand["name"])
        except Exception as e:
            print("❌ 브랜드 목록 불러오기 실패:", e)

    def get_product_data(self):
        """
        다이얼로그에서 입력한 데이터를 dict로 만들어 반환
        """
        # brand_id_text = self.brand_id_edit.text().strip()
        # brand_id = int(brand_id_text) if brand_id_text.isdigit() else 0

        barcodes_text = self.barcodes_edit.toPlainText().strip()
        # 여러 줄을 리스트로 분리
        # 공백 줄은 제거하도록 filter 처리
        barcode_lines = [line.strip() for line in barcodes_text.splitlines() if line.strip()]

        data = {
            "brand_name": self.brand_name_combo.currentText().strip(),
            "product_name": self.name_edit.text().strip(),
            "barcodes": barcode_lines,  # ← 여러 개 바코드를 리스트로
            "default_price": float(self.price_edit.text().strip() or 0),
            "stock": int(self.stock_edit.text().strip() or 0),
            "is_active": 1 if "1" in self.active_edit.currentText() else 0,
            "incentive": float(self.incentive_edit.text().strip() or 0),
            "box_quantity": int(self.box_quantity_edit.text().strip() or 1),
            "category": self.category_edit.text().strip(),
            "is_fixed_price": True if self.price_type_edit.currentIndex() == 1 else False
        }
        return data

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
        self.btn_import_excel = QPushButton("엑셀 업로드")
        self.layout().itemAt(1).layout().addWidget(self.btn_import_excel)

        # 버튼 클릭 이벤트 연결
        self.btn_import_excel.clicked.connect(self.import_from_excel)
        # ✅ 버튼 클릭 이벤트 연결
        self.btn_new.clicked.connect(self.create_product)
        self.btn_edit.clicked.connect(self.update_product)
        self.btn_delete.clicked.connect(self.delete_product)
        self.btn_add_brand = QPushButton("브랜드 등록")
        self.layout().itemAt(1).layout().addWidget(self.btn_add_brand)
        self.btn_add_brand.clicked.connect(self.add_brand_dialog)
        self.current_product_id = None

    def add_brand_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("브랜드 등록")
        dialog.setFixedSize(300, 150)
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        brand_name_edit = QLineEdit()
        form.addRow("브랜드명:", brand_name_edit)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("등록")
        btn_cancel = QPushButton("취소")
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        def on_register():
            name = brand_name_edit.text().strip()
            if not name:
                QMessageBox.warning(dialog, "경고", "브랜드명을 입력하세요.")
                return
            try:
                resp = requests.post(
                    "http://127.0.0.1:8000/brands/",
                    headers={"Authorization": f"Bearer {global_token}"},
                    json={"name": name}
                )
                if resp.status_code == 201:
                    QMessageBox.information(dialog, "성공", "브랜드가 등록되었습니다.")
                    dialog.accept()
                else:
                    # QMessageBox.critical(dialog, "실패", f"등록 실패: {resp.status_code}\n{resp.text}")
                    pass
            except Exception as e:
                QMessageBox.critical(dialog, "에러", str(e))

        btn_ok.clicked.connect(on_register)
        btn_cancel.clicked.connect(dialog.reject)
        dialog.exec_()

    def import_from_excel(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Excel Files (*.xlsx *.xls)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            if not file_path:
                return

            try:
                df = pd.read_excel(file_path)
            except Exception as e:
                QMessageBox.critical(self, "에러", f"엑셀 파일을 읽는 중 오류가 발생했습니다.\n{str(e)}")
                return

            total_rows = len(df)
            if total_rows == 0:
                QMessageBox.information(self, "정보", "엑셀에 등록할 상품이 없습니다.")
                return

            # ✅ 진행바
            progress = QProgressDialog("상품을 업로드 중입니다...", "취소", 0, total_rows, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)

            created_count = 0
            error_count = 0

            for idx, (_, row) in enumerate(df.iterrows()):
                if progress.wasCanceled():
                    QMessageBox.information(self, "중단", "업로드가 사용자에 의해 중단되었습니다.")
                    return

                try:
                    # ✅ 필수값 추출 및 유효성 검사
                    brand_name = str(row.get("brand_name", "")).strip()
                    product_name = str(row.get("상품명", "")).strip()

                    if not brand_name or not product_name:
                        print(f"❌ {idx+1}행: brand_name 또는 상품명이 비어 있어 건너뜀")
                        error_count += 1
                        continue

                    # ✅ 바코드 처리 (여러 줄 또는 JSON 배열 가능)
                    raw_barcode = row.get("바코드", "")
                    barcodes = []
                    if isinstance(raw_barcode, str):
                        raw_barcode = raw_barcode.strip()
                        if raw_barcode.startswith("["):
                            try:
                                barcodes = [b.strip() for b in json.loads(raw_barcode) if b.strip()]
                            except:
                                barcodes = [raw_barcode] if raw_barcode else []
                        elif "\n" in raw_barcode:
                            barcodes = [line.strip() for line in raw_barcode.splitlines() if line.strip()]
                        elif "," in raw_barcode:
                            barcodes = [b.strip() for b in raw_barcode.split(",") if b.strip()]
                        else:
                            if raw_barcode:
                                barcodes = [raw_barcode]
                    elif pd.notna(raw_barcode):
                        barcodes = [str(raw_barcode).strip()]

                    # ✅ 나머지 필드
                    default_price = float(row.get("기본가격", 0))
                    incentive = float(row.get("인센티브", 0))
                    stock = int(row.get("재고수량", 0))
                    box_qty = int(row.get("박스당수량", 1))
                    category = str(row.get("카테고리", "")).strip()
                    is_active = 1 if str(row.get("활성화여부", "1")).strip() == "1" else 0
                    is_fixed_price = str(row.get("가격유형", "")).strip() == "고정가"

                    data = {
                        "brand_name": brand_name,
                        "product_name": product_name,
                        "barcodes": barcodes,
                        "default_price": default_price,
                        "incentive": incentive,
                        "stock": stock,
                        "box_quantity": box_qty,
                        "category": category,
                        "is_active": is_active,
                        "is_fixed_price": is_fixed_price
                    }

                    resp = api_create_product(global_token, data)
                    if resp and resp.status_code in (200, 201):
                        created_count += 1
                    else:
                        print(f"❌ {idx+1}행 업로드 실패: {resp.status_code} {resp.text}")
                        error_count += 1
                except Exception as e:
                    print(f"❌ {idx+1}행 처리 중 예외 발생:", e)
                    error_count += 1

                progress.setValue(idx + 1)

            progress.close()
            QMessageBox.information(
                self,
                "엑셀 업로드 결과",
                f"총 {total_rows}건 중 {created_count}건 등록 성공, {error_count}건 실패"
            )


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
        self.set_value(0, product.get("brand_name", ""))
        self.set_value(1, product.get("product_name", ""))
        barcodes = product.get("barcodes", [])
        first_barcode = barcodes[0] if isinstance(barcodes, list) and barcodes else ""
        self.set_value(2, first_barcode)
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
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        dialog = ProductDialog("신규 상품 등록")
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_product_data()  # ← 여기서 barcodes 리스트도 함께 옴
            resp = api_create_product(global_token, data)
            if resp and resp.status_code in (200, 201):
                QMessageBox.information(self, "성공", "상품 등록 완료!")
            else:
                QMessageBox.critical(self, "실패", f"상품 등록 실패: {resp.status_code}\n{resp.text}")

        
    def update_product(self):
        """
        현재 테이블에 표시된 상품 하나를 수정
        """
        global global_token

        # ✅ 현재 표시된 상품의 ID가 있는지 확인
        if not getattr(self, "current_product_id", None):
            QMessageBox.warning(self, "주의", "표시된 상품이 없습니다.")
            return

        product_id = self.current_product_id

        # ✅ 테이블에 표시된 정보를 기반으로 기존 값 구성
        current_product = {
            "brand_name": self.get_value(0),  # 브랜드 이름
            "product_name": self.get_value(1),
            "barcodes": [self.get_value(2)] if self.get_value(2) else [],
            "default_price": float(self.get_value(3) or 0),
            "incentive": float(self.get_value(4) or 0),
            "stock": int(self.get_value(5) or 0),
            "box_quantity": int(self.get_value(6) or 1),
            "category": self.get_value(7) or "",
            "is_active": 1 if self.get_value(8) == "활성" else 0,
            "is_fixed_price": True if self.get_value(9) == "고정가" else False
        }

        dialog = ProductDialog("상품 수정", product=current_product)
        if dialog.exec_() == QDialog.Accepted:
            try:
                brand_name = dialog.brand_name_combo.currentText().strip()
                product_name = dialog.name_edit.text().strip()
                barcodes_raw = dialog.barcodes_edit.toPlainText().strip()
                barcodes = [line.strip() for line in barcodes_raw.splitlines() if line.strip()]

                data = {
                    "brand_name": brand_name,
                    "product_name": product_name,
                    "barcodes": barcodes,
                    "default_price": float(dialog.price_edit.text().strip() or 0),
                    "stock": int(dialog.stock_edit.text().strip() or 0),
                    "incentive": float(dialog.incentive_edit.text().strip() or 0),
                    "box_quantity": int(dialog.box_quantity_edit.text().strip() or 1),
                    "category": dialog.category_edit.text().strip(),
                    "is_active": 1 if "1" in dialog.active_edit.currentText() else 0,
                    "is_fixed_price": dialog.price_type_edit.currentIndex() == 1
                }

                resp = api_update_product_by_id(global_token, product_id, data)
                if resp and resp.status_code == 200:
                    QMessageBox.information(self, "성공", "상품 수정 완료!")
                    self.refresh_product_list()
                else:
                    QMessageBox.critical(self, "실패", f"상품 수정 실패: {resp.status_code}\n{resp.text}")

            except Exception as e:
                QMessageBox.critical(self, "에러", f"수정 중 오류 발생: {e}")


    def refresh_product_list(self):
        """
        서버에서 상품 목록을 다시 불러오고,
        테이블(또는 해당 UI)을 다시 표시한다.
        """
        # 1) api_fetch_products() 같은 걸 호출해서 서버에서 전체 상품 목록 가져오기
        # 2) 현재 선택된 상품 ID, 검색 결과, 테이블 업데이트 등
        pass

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

    
    def do_custom_action(self):
        """ '모든 검색' 버튼 클릭 시 실행: 전체 상품 목록 보여줌 """
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        try:
            # 전체 상품 불러오기
            resp = api_fetch_products(global_token)
            if not isinstance(resp, dict):
                QMessageBox.critical(self, "실패", "상품 목록 불러오기 실패!")
                return

            # 카테고리별로 묶여 있으므로 풀어서 리스트로 만들기
            all_products = []
            for category, items in resp.items():
                for p in items:
                    p["category"] = category
                    all_products.append(p)

            if not all_products:
                QMessageBox.information(self, "정보", "등록된 상품이 없습니다.")
                return

            # 다이얼로그에서 선택
            dialog = ProductSelectionDialog(all_products, parent=self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_product:
                self.left_panel.display_product(dialog.selected_product)

        except Exception as e:
            QMessageBox.critical(self, "에러", f"전체 상품 불러오기 실패:\n{e}")


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


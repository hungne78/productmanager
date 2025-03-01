from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QLabel, QComboBox, QFileDialog, QLineEdit, QGroupBox
import requests
import pandas as pd
from PyQt5.QtCore import Qt, QSize
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import get_auth_headers
from PyQt5.QtWidgets import QSizePolicy

BASE_URL = "http://127.0.0.1:8000"  # 실제 서버 URL
global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)
import pandas as pd
from datetime import datetime


class InvoicesLeftPanel(QWidget):
    """
    왼쪽 패널 - 연도 & 월 선택 + 유형 선택 + 등록/수정/삭제 버튼
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # ✅ [1] 연도 & 월 선택 (그룹박스로 감싸기)
        date_group = QGroupBox("📅 기간 선택")
        date_layout = QHBoxLayout()
        self.year_selector = QComboBox()
        self.month_selector = QComboBox()

        # 📌 크기 조정
        self.year_selector.setMinimumSize(QSize(80, 30))
        self.month_selector.setMinimumSize(QSize(80, 30))

        # 📅 현재 연도 & 월 설정
        current_year = datetime.today().year
        current_month = datetime.today().month
        for y in range(current_year - 5, current_year + 6):
            self.year_selector.addItem(str(y))
        for m in range(1, 13):
            self.month_selector.addItem(str(m).zfill(2))

        self.year_selector.setCurrentText(str(current_year))
        self.month_selector.setCurrentText(str(current_month).zfill(2))

        # 📅 UI 배치
        date_layout.addWidget(QLabel("연도:"))
        date_layout.addWidget(self.year_selector)
        date_layout.addWidget(QLabel("월:"))
        date_layout.addWidget(self.month_selector)
        date_group.setLayout(date_layout)
        main_layout.addWidget(date_group)

        # ✅ [2] 세금계산서 유형 선택 (그룹박스로 감싸기)
        type_group = QGroupBox("📑 세금계산서 유형")
        type_layout = QVBoxLayout()
        self.invoice_type_selector = QComboBox()
        self.invoice_type_selector.addItem("01 (일반)")
        self.invoice_type_selector.addItem("02 (영세율)")
        self.invoice_type_selector.setMinimumSize(QSize(140, 30))

        type_layout.addWidget(self.invoice_type_selector)
        type_group.setLayout(type_layout)
        main_layout.addWidget(type_group)

        # ✅ [3] 거래처 검색 필터
        search_group = QGroupBox("🔍 거래처 검색")
        search_layout = QVBoxLayout()
        self.client_search = QLineEdit()
        self.client_search.setPlaceholderText("거래처명 입력...")
        self.client_search.setMinimumSize(QSize(200, 30))
        self.client_search.textChanged.connect(self.filter_clients)

        search_layout.addWidget(self.client_search)
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)

        # ✅ [4] 총 공급가액 & 총 세액 (가운데 정렬)
        total_group = QGroupBox("💰 총 금액")
        total_layout = QVBoxLayout()
        self.total_sales_label = QLabel("총 공급가액: ₩0")
        self.total_tax_label = QLabel("총 세액: ₩0")

        # 📌 가운데 정렬
        self.total_sales_label.setAlignment(Qt.AlignCenter)
        self.total_tax_label.setAlignment(Qt.AlignCenter)

        total_layout.addWidget(self.total_sales_label)
        total_layout.addWidget(self.total_tax_label)
        total_group.setLayout(total_layout)
        main_layout.addWidget(total_group)

        # ✅ [5] 버튼 (등록/수정/삭제) 세로 정렬
        btn_group = QGroupBox("🛠️ 관리")
        btn_layout = QVBoxLayout()
        self.add_button = QPushButton("➕ 등록")
        self.edit_button = QPushButton("✏️ 수정")
        self.delete_button = QPushButton("🗑 삭제")

        # 📌 버튼 크기 조정
        self.add_button.setMinimumSize(QSize(120, 40))
        self.edit_button.setMinimumSize(QSize(120, 40))
        self.delete_button.setMinimumSize(QSize(120, 40))

        btn_layout.addWidget(self.add_button)
        btn_layout.addWidget(self.edit_button)
        btn_layout.addWidget(self.delete_button)
        btn_group.setLayout(btn_layout)
        main_layout.addWidget(btn_group)

        # ✅ [6] 📊 조회 버튼 (가로로 넓게 배치)
        self.search_button = QPushButton("📊 세금계산서 조회")
        self.search_button.setMinimumSize(QSize(250, 40))
        self.search_button.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(self.search_button)

        # ✅ [7] 📂 파일 불러오기 버튼 (하단)
        self.import_button = QPushButton("📂 파일 불러오기")
        self.import_button.setMinimumSize(QSize(250, 40))
        self.import_button.clicked.connect(self.import_excel)
        main_layout.addWidget(self.import_button)

        # 📌 레이아웃 설정
        self.search_button.clicked.connect(self.fetch_invoices)
        self.setLayout(main_layout)

    def fetch_invoices(self):
        """
        세금계산서 조회
        """
        if self.parent_widget:
            selected_year = self.year_selector.currentText()
            selected_month = self.month_selector.currentText()
            self.parent_widget.load_invoices(selected_year, selected_month)

    def filter_clients(self):
        """
        거래처명을 입력하면 해당 거래처만 필터링하여 조회
        """
        if self.parent_widget:
            search_text = self.client_search.text()
            self.parent_widget.filter_invoices(search_text)

    def update_totals(self, total_sales, total_tax):
        """
        총 공급가액 & 총 세액 표시 업데이트
        """
        self.total_sales_label.setText(f"💰 총 공급가액: ₩{total_sales:,}")
        self.total_tax_label.setText(f"💵 총 세액: ₩{total_tax:,}")

    def import_excel(self):
        """
        엑셀 파일 불러오기
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "엑셀 파일 불러오기", "", "Excel Files (*.xls *.xlsx)")
        if not file_path:
            return

        try:
            df = pd.read_excel(file_path, sheet_name="Sheet1", skiprows=3)  # 헤더 제외하고 데이터 로드
            invoice_data = df.to_dict(orient="records")
            self.parent_widget.load_imported_invoices(invoice_data)
            print(f"✅ 엑셀 파일 로드 성공: {file_path}")
        except Exception as e:
            print(f"❌ 엑셀 파일 로드 실패: {e}")

class InvoicesRightPanel(QWidget):
    """
    오른쪽 패널 - 거래처별 월 매출 리스트 + 엑셀 저장
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(15)
        self.invoice_table.setHorizontalHeaderLabels([
            "전자(세금)계산서 종류", "작성일자", "공급자 등록번호", "공급자 상호", "공급자 성명",
            "공급받는자 등록번호", "공급받는자 상호", "공급받는자 성명",
            "공급가액 합계", "세액 합계", "일자1", "공급가액1", "세액1", "영수(01)", "청구(02)"
        ])
        self.invoice_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("📑 거래처별 월 매출 목록"))
        layout.addWidget(self.invoice_table)

        # ✅ 엑셀 저장 버튼
        self.export_button = QPushButton("📄 엑셀 저장")
        self.export_button.clicked.connect(self.export_to_excel)
        layout.addWidget(self.export_button)

        self.setLayout(layout)

    def update_invoice_data(self, invoice_data):
        """
        거래처별 월 매출 리스트 업데이트
        """
        self.invoice_table.setRowCount(0)
        for invoice in invoice_data:
            row = self.invoice_table.rowCount()
            self.invoice_table.insertRow(row)
            
            # ✅ 기본 값 설정
            self.invoice_table.setItem(row, 0, QTableWidgetItem("01"))  # 전자세금계산서 종류 (01: 일반)
            self.invoice_table.setItem(row, 1, QTableWidgetItem(datetime.today().strftime("%Y-%m-%d")))  # 작성일자
            self.invoice_table.setItem(row, 2, QTableWidgetItem(invoice["supplier_id"]))  # 공급자 등록번호
            self.invoice_table.setItem(row, 3, QTableWidgetItem(invoice["supplier_name"]))  # 공급자 상호
            self.invoice_table.setItem(row, 4, QTableWidgetItem(invoice["supplier_ceo"]))  # 공급자 성명
            self.invoice_table.setItem(row, 5, QTableWidgetItem(invoice["client_id"]))  # 공급받는자 등록번호
            self.invoice_table.setItem(row, 6, QTableWidgetItem(invoice["client_name"]))  # 공급받는자 상호
            self.invoice_table.setItem(row, 7, QTableWidgetItem(invoice["client_ceo"]))  # 공급받는자 성명
            self.invoice_table.setItem(row, 8, QTableWidgetItem(f"₩{invoice['total_sales']:,}"))  # 공급가액 합계
            self.invoice_table.setItem(row, 9, QTableWidgetItem(f"₩{invoice['tax_amount']:,}"))  # 세액 합계
            self.invoice_table.setItem(row, 10, QTableWidgetItem("01"))  # 일자1 (기본값)
            self.invoice_table.setItem(row, 11, QTableWidgetItem(f"₩{invoice['total_sales']:,}"))  # 공급가액1
            self.invoice_table.setItem(row, 12, QTableWidgetItem(f"₩{invoice['tax_amount']:,}"))  # 세액1
            self.invoice_table.setItem(row, 13, QTableWidgetItem("01"))  # 영수(01)
            self.invoice_table.setItem(row, 14, QTableWidgetItem("02"))  # 청구(02)

    def export_to_excel(self):
        """
        세금계산서를 엑셀 파일로 저장
        """
        file_path, _ = QFileDialog.getSaveFileName(self, "엑셀 파일 저장", "", "Excel Files (*.xls *.xlsx)")
        if not file_path:
            return

        row_count = self.invoice_table.rowCount()
        col_count = self.invoice_table.columnCount()

        # ✅ 엑셀 데이터 저장 준비
        data = []
        for row in range(row_count):
            row_data = [self.invoice_table.item(row, col).text() for col in range(col_count)]
            data.append(row_data)

        df = pd.DataFrame(data, columns=[self.invoice_table.horizontalHeaderItem(i).text() for i in range(col_count)])



        # ✅ 100건 이하 / 100건 초과 구분
        template_file = "/mnt/data/세금계산서등록양식(일반).xls" if row_count <= 100 else "/mnt/data/세금계산서등록양식(일반)_대량.xls"

        try:
            writer = pd.ExcelWriter(template_file, engine="openpyxl")
            df.to_excel(writer, sheet_name="Sheet1", startrow=3, index=False, header=False)
            writer.close()
            df.to_excel(file_path, index=False)
            print(f"✅ 엑셀 저장 완료: {file_path}")
        except Exception as e:
            print(f"❌ 엑셀 저장 실패: {e}")

class InvoicesTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        self.left_panel = InvoicesLeftPanel(self)
        self.right_panel = InvoicesRightPanel()
        # ✅ 크기 정책 설정
        self.left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ✅ 고정 크기 설정
        self.left_panel.setFixedWidth(350)  # 1 비율
        layout.addWidget(self.left_panel)
        layout.addWidget(self.right_panel)
        self.setLayout(layout)

    def load_invoices(self, year, month):
        """
        거래처별 월 매출 데이터 로드
        """
        global global_token
        url = f"http://127.0.0.1:8000/sales/clients/{year}/{month}"
        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            invoice_data = resp.json()
            self.right_panel.update_invoice_data(invoice_data)
        except Exception as e:
            print(f"❌ 거래처 매출 조회 실패: {e}")

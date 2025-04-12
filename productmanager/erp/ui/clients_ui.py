from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,  QGridLayout, QFrame,\
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel, QDialog, QVBoxLayout, QListWidget, QGroupBox, QInputDialog, QDateEdit, QComboBox
import sys
import os
from PyQt5.QtGui import QColor
# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_clients, api_create_client, api_update_client, api_delete_client, api_fetch_client_names,\
    api_assign_employee_client, api_fetch_employee_clients_all, get_auth_headers, api_fetch_lent_freezers, api_fetch_employees, api_unassign_employee_client
from baselefttabwidget import BaseLeftTableWidget
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QSizePolicy
import requests
from PyQt5.QtGui import QFont
from datetime import datetime
from config import BASE_URL
from PyQt5.QtWidgets import QFileDialog
import pandas as pd
import traceback
global_token = get_auth_headers

class CustomCalendarCell(QFrame):
    def __init__(self, date: QDate, sales_amount: int = 0, parent=None):
        super().__init__(parent)
        self.date = date
        self.sales_amount = sales_amount
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        self.date_label = QLabel(str(self.date.day()))
        self.date_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.date_label.setFont(QFont("Malgun Gothic", 10, QFont.Bold))

        self.sales_label = QLabel(f"{self.sales_amount:,}원" if self.sales_amount else "")
        self.sales_label.setAlignment(Qt.AlignCenter)
        self.sales_label.setFont(QFont("Malgun Gothic", 9))

        layout.addWidget(self.date_label)
        layout.addStretch()
        layout.addWidget(self.sales_label)
        self.setLayout(layout)

        bg = "#ffffff"
        if self.date.dayOfWeek() == 7:
            bg = "#ffeaea"  # 일요일
        elif self.date.dayOfWeek() == 6:
            bg = "#eaf1ff"  # 토요일

        self.setStyleSheet(f"""
            QFrame {{
                border: 1px solid #d0d7e2;
                border-radius: 6px;
                background-color: {bg};
            }}
            QLabel {{
                color: #1E3A8A;
            }}
        """)

class CustomCalendarWidget(QWidget):
    def __init__(self, year: int, month: int, sales_data: dict[int, int], parent=None):
        super().__init__(parent)
        self.year = year
        self.month = month
        self.sales_data = sales_data
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title = QLabel(f"{self.year}년 {self.month}월")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Malgun Gothic", 12, QFont.Bold))
        self.layout.addWidget(self.title)

        self.grid = QGridLayout()
        self.layout.addLayout(self.grid)

        # 요일 헤더
        weekdays = ["월", "화", "수", "목", "금", "토", "일"]
        for i, name in enumerate(weekdays):
            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            if name in ["토", "일"]:
                label.setStyleSheet("color: red;" if name == "일" else "color: blue;")
            self.grid.addWidget(label, 0, i)

        self.build_calendar()

    def build_calendar(self):
        # 이전 위젯 제거
        for i in reversed(range(self.grid.count())):
            if i >= 7:  # 요일 라벨 제외
                widget = self.grid.itemAt(i).widget()
                self.grid.removeWidget(widget)
                widget.deleteLater()

        first_day = QDate(self.year, self.month, 1)
        start_col = first_day.dayOfWeek() - 1  # Monday = 0
        days_in_month = first_day.daysInMonth()

        row = 1
        col = start_col
        for day in range(1, days_in_month + 1):
            date = QDate(self.year, self.month, day)
            amount = self.sales_data.get(day, 0)
            cell = CustomCalendarCell(date, amount)
            self.grid.addWidget(cell, row, col)

            col += 1
            if col > 6:
                col = 0
                row += 1

    def update_sales(self, sales_dict: dict[int, int]):
        """
        일별 매출을 받아서 달력 셀에 업데이트
        sales_dict 예시: {1: 10000, 2: 5000, 15: 120000}
        """
        for i in reversed(range(self.layout().count())):
            item = self.layout().itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        first_day = QDate(self.year, self.month, 1)
        start_col = first_day.dayOfWeek() - 1  # Monday=0
        days_in_month = first_day.daysInMonth()

        # 요일 라벨 (월~일)
        weekdays = ["월", "화", "수", "목", "금", "토", "일"]
        for col in range(7):
            label = QLabel(weekdays[col])
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-weight: bold; color: #2F3A66;")
            self.layout().addWidget(label, 0, col)

        row = 1
        col = start_col
        for day in range(1, days_in_month + 1):
            current_date = QDate(self.year, self.month, day)
            sales = sales_dict.get(day, 0)
            cell = CustomCalendarCell(current_date, sales)

            # 토/일 색상 지정
            if current_date.dayOfWeek() == 7:  # 일요일
                cell.setStyleSheet("background-color: #ffeef0; border: 1px solid #ccc; border-radius: 6px;")
            elif current_date.dayOfWeek() == 6:  # 토요일
                cell.setStyleSheet("background-color: #e7f1ff; border: 1px solid #ccc; border-radius: 6px;")

            self.layout().addWidget(cell, row, col)

            col += 1
            if col > 6:
                col = 0
                row += 1


class LentEditorDialog(QDialog):
    def __init__(self, client_id, parent=None):
        super().__init__(parent)

        self.setWindowTitle("대여 냉동고 등록/수정")
        self.resize(800, 800)
        self.client_id = client_id
        self.selected_lent_id = None  # ✅ 현재 수정 대상 냉동고 ID

        layout = QVBoxLayout()

        # 🔹 냉동고 목록 테이블
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "브랜드", "사이즈", "시리얼", "년식"])
        self.table.setColumnHidden(0, True) 
        self.table.setMinimumHeight(180)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemClicked.connect(self.fill_form_from_table)

        layout.addWidget(QLabel("📦 현재 등록된 냉동고 목록"))
        layout.addWidget(self.table)

        # 🔹 입력 폼
        self.brand_edit = QLineEdit()
        self.size_edit = QLineEdit()
        self.serial_edit = QLineEdit()
        self.year_edit = QLineEdit()

        form = QFormLayout()
        form.addRow("브랜드", self.brand_edit)
        form.addRow("사이즈", self.size_edit)
        form.addRow("시리얼번호", self.serial_edit)
        form.addRow("년식", self.year_edit)
        layout.addLayout(form)

        # 🔹 버튼 영역
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("저장")
        cancel_btn = QPushButton("취소")
        self.recall_btn = QPushButton("♻️ 회수")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.recall_btn)
        layout.addLayout(btn_layout)

        save_btn.clicked.connect(self.save_data)
        cancel_btn.clicked.connect(self.reject)
        self.recall_btn.clicked.connect(self.recall_freezer)
        self.setLayout(layout)
        self.load_existing_data()

    def recall_freezer(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "선택 오류", "냉동고를 선택하세요.")
            return

        id_item = self.table.item(row, 0)
        if not id_item:
            QMessageBox.critical(self, "ID 오류", "ID가 없습니다.")
            return

        id_text = id_item.text().strip()
        if not id_text.isdigit():
            QMessageBox.critical(self, "ID 오류", "ID가 숫자가 아닙니다.")
            return

        freezer_id = int(id_text)


        confirm = QMessageBox.question(
            self, "회수 확인", "선택한 냉동고를 회수(회사로 반환)하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            try:
                payload = {
                    "brand": self.table.item(row, 1).text(),
                    "size": self.table.item(row, 2).text(),
                    "serial_number": self.table.item(row, 3).text(),
                    "year": int(self.table.item(row, 4).text()),
                    "client_id": 0  # ✅ 회수 처리 핵심
                }
                url = f"{BASE_URL}/lent/id/{freezer_id}"
                resp = requests.put(url, json=payload)
                if resp.status_code == 200:
                    QMessageBox.information(self, "회수 완료", "냉동고가 회사로 회수되었습니다.")
                    self.load_existing_data()
                else:
                    QMessageBox.warning(self, "회수 실패", resp.text)
            except Exception as e:
                QMessageBox.critical(self, "오류", str(e))


    def load_existing_data(self):
        try:
            response = api_fetch_lent_freezers(global_token, self.client_id)
            if response and isinstance(response, list):
                self.table.setRowCount(len(response))
                for row, freezer in enumerate(response):
                    self.table.setItem(row, 0, QTableWidgetItem(str(freezer["id"])))
                    self.table.setItem(row, 1, QTableWidgetItem(freezer.get("brand", "")))
                    self.table.setItem(row, 2, QTableWidgetItem(freezer.get("size", "")))
                    self.table.setItem(row, 3, QTableWidgetItem(freezer.get("serial_number", "")))
                    self.table.setItem(row, 4, QTableWidgetItem(str(freezer.get("year", ""))))

            else:
                self.table.setRowCount(0)
        except Exception as e:
            print(f"❌ 냉동고 정보 로딩 실패: {e}")

    def fill_form_from_table(self, item):
        row = item.row()
        self.selected_lent_id = self.table.item(row, 0).data(Qt.UserRole) or self.table.item(row, 0).text()

        # 인덱스 순서 주의! 1~4열에서 가져와야 함
        self.brand_edit.setText(self.table.item(row, 1).text())
        self.size_edit.setText(self.table.item(row, 2).text())
        self.serial_edit.setText(self.table.item(row, 3).text())
        self.year_edit.setText(self.table.item(row, 4).text())


    def save_data(self):
        data = {
            "client_id": int(self.client_id),
            "brand": self.brand_edit.text(),
            "size": self.size_edit.text(),
            "serial_number": self.serial_edit.text(),
            "year": int(self.year_edit.text()),
        }

        headers = {"Authorization": f"Bearer {global_token}"}

        try:
            if self.selected_lent_id:  # ✅ 수정
                url = f"{BASE_URL}/lent/id/{self.selected_lent_id}"
                response = requests.put(url, headers=headers, json=data)
            else:  # ✅ 신규 등록
                url = f"{BASE_URL}/lent/{self.client_id}"
                response = requests.post(url, headers=headers, json=data)

            if response.status_code in (200, 201):
                QMessageBox.information(self, "성공", "냉동고 정보가 저장되었습니다.")
                self.selected_lent_id = None  # ✅ 입력 폼 리셋
                self.brand_edit.clear()
                self.size_edit.clear()
                self.serial_edit.clear()
                self.year_edit.clear()
                self.load_existing_data()  # ✅ 목록 새로고침
            else:
                QMessageBox.critical(self, "오류", f"저장 실패: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "에러", f"오류 발생: {e}")

            
class ClientDialog(QDialog):
    def __init__(self, title, client=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(500, 600)

        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.representative_edit = QLineEdit() 
        self.address_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.outstanding_edit = QLineEdit("0")
        self.regular_price__edit = QLineEdit("35")
        self.fixed_price_edit = QLineEdit("70")
        self.business_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("입력 안하면 변경 없음")
        self.password_edit.setEchoMode(QLineEdit.Password)

        form_layout.addRow("거래처명:", self.name_edit)
        form_layout.addRow("대표자명:", self.representative_edit)
        form_layout.addRow("주소:", self.address_edit)
        form_layout.addRow("전화번호:", self.phone_edit)
        form_layout.addRow("미수금:", self.outstanding_edit)
        form_layout.addRow("일반가단단가:", self.regular_price__edit)
        form_layout.addRow("고정가단단가:", self.fixed_price_edit)
        form_layout.addRow("사업자번호:", self.business_edit)
        form_layout.addRow("이메일:", self.email_edit)
        form_layout.addRow("비밀번호:", self.password_edit)

        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("확인")
        self.cancel_button = QPushButton("취소")
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        if client:
            self.name_edit.setText(client.get("client_name", ""))
            self.representative_edit.setText(client.get("representative_name", ""))  # ✅ 빠진 필드 추가
            self.address_edit.setText(client.get("address", ""))
            self.phone_edit.setText(client.get("phone", ""))
            self.outstanding_edit.setText(str(client.get("outstanding_amount", "0")))

            self.regular_price__edit.setText(str(client.get("regular_price", "35")))  # ✅ 키명 수정
            self.fixed_price_edit.setText(str(client.get("fixed_price", "70")))      # ✅ 키명 수정

            self.business_edit.setText(client.get("business_number", ""))
            self.email_edit.setText(client.get("email", ""))

            self.password_edit.setText("")  # 항상 비워둠 (입력 시에만 변경)

            print("🧪 클라이언트 dict 구조 확인:")
            for k, v in client.items():
                print(f"   {k}: {v}")
class ClientSelectionDialog(QDialog):
    def __init__(self, clients, parent=None):
        super().__init__(parent)
        self.setWindowTitle("거래처 목록")
        self.resize(300, 400)
        self.clients = clients  # ✅ 전체 dict 리스트 저장
        self.selected_client = None

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()

        for client in clients:
            self.list_widget.addItem(client["client_name"])  # 이름만 표시

        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("선택")
        cancel_btn = QPushButton("취소")
        ok_btn.clicked.connect(self.on_ok)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def on_ok(self):
        selected = self.list_widget.currentItem()
        if selected:
            name = selected.text()
            self.selected_client = next((c for c in self.clients if c["client_name"] == name), None)
            self.accept()
        else:
            QMessageBox.warning(self, "알림", "거래처를 선택해주세요.")


            
class ClientLeftPanel(BaseLeftTableWidget):
    """ 거래처 상세 정보 및 담당 직원 배정 기능 추가 """

    def __init__(self, parent=None):
        # 이제 8행: 거래처ID, 거래처명, 주소, 전화번호, 미수금, 일반가단가, 고정가단가, 사업자번호, 메일주소
        labels = [
            "거래처ID",    # 0
            "거래처명",
            "대표자명",    # 1
            "주소",        # 2
            "전화번호",    # 3
            "미수금",      # 4
            "일반가단가", 
            "고정가단가",
            "사업자번호",  # 6
            "메일주소",     # 7
            "비밀번호",
        ]
        
        super().__init__(row_count=len(labels), labels=labels, parent=parent)
        
       # ✅ 현재 레이아웃 가져오기
        main_layout = self.layout()
        if main_layout is None:
            main_layout = QVBoxLayout()
            self.setLayout(main_layout)

        # 🔹 버튼을 그리드로 깔끔하게 정리
        btn_grid = QGridLayout()
        btn_grid.setSpacing(6)

        # 1) 기존 부모 클래스의 버튼들
        self.btn_new.setFixedHeight(32)
        self.btn_edit.setFixedHeight(32)
        btn_grid.addWidget(self.btn_new, 0, 0)
        btn_grid.addWidget(self.btn_edit, 0, 1)

        # 2) 자식 클래스에서 추가한 버튼들
        self.btn_delete = QPushButton("삭제")
        self.btn_assign = QPushButton("담당 직원 배정")
        self.btn_unassign = QPushButton("담당 직원 해제")
        self.btn_lent = QPushButton("대여 냉동고")
        for btn in [self.btn_delete, self.btn_assign, self.btn_unassign, self.btn_lent]:
            btn.setFixedHeight(32)
            btn.setMinimumWidth(100)
        btn_grid.addWidget(self.btn_delete,   1, 0)
        btn_grid.addWidget(self.btn_assign,   1, 1)
        btn_grid.addWidget(self.btn_unassign, 2, 0)
        btn_grid.addWidget(self.btn_lent,     2, 1)

        # 3) 🔽 "서버 → 엑셀 내보내기" + "엑셀 → 서버 등록" 버튼도 같은 그리드에 추가
        self.btn_export_excel = QPushButton("서버 거래처 → 엑셀")
        self.btn_export_excel.clicked.connect(self.export_excel_clients)
        self.btn_import_excel = QPushButton("엑셀 → 서버 등록")
        self.btn_import_excel.clicked.connect(self.import_excel_clients)

        # 버튼 크기 통일
        for btn in [self.btn_export_excel, self.btn_import_excel]:
            btn.setFixedHeight(32)
            btn.setMinimumWidth(160)

        btn_grid.addWidget(self.btn_export_excel, 3, 0)
        btn_grid.addWidget(self.btn_import_excel, 3, 1)
        font = QFont("맑은 고딕", 7)  # 폰트 이름 + 크기

        for btn in [self.btn_export_excel, self.btn_import_excel, self.btn_new, self.btn_edit,
                    self.btn_delete, self.btn_assign, self.btn_unassign, self.btn_lent]:
            btn.setFont(font)
        # 🔹 구성된 그리드 레이아웃을 메인 레이아웃에 추가
        main_layout.addLayout(btn_grid)

        # 🔹 담당 직원 목록 라벨 및 테이블
        main_layout.addWidget(QLabel("담당 직원 목록"))
        self.assigned_employees_table = QTableWidget()
        self.assigned_employees_table.setColumnCount(1)
        self.assigned_employees_table.setHorizontalHeaderLabels(["담당 직원"])
        self.assigned_employees_table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.assigned_employees_table)

        # 예시: 테이블에서 직원 더블클릭 시 어떤 동작
        self.assigned_employees_table.itemDoubleClicked.connect(self.on_employee_double_clicked)

        # 🔹 행사 등록 박스 (예시)
        promo_box = QGroupBox("📣 행사 등록")
        promo_layout = QVBoxLayout()

        # 행사 시작/종료일
        row1 = QHBoxLayout()
        self.promo_start = QDateEdit()
        self.promo_start.setCalendarPopup(True)
        self.promo_start.setDate(QDate.currentDate())
        self.promo_end = QDateEdit()
        self.promo_end.setCalendarPopup(True)
        self.promo_end.setDate(QDate.currentDate().addDays(7))

        # 🔹 줄1: 시작일 ~ 종료일
        # 🔹 줄1: 시작일 ~ 종료일
        row1 = QHBoxLayout()
        self.promo_start = QDateEdit()
        self.promo_start.setCalendarPopup(True)
        self.promo_start.setDate(QDate.currentDate())
        self.promo_end = QDateEdit()
        self.promo_end.setCalendarPopup(True)
        self.promo_end.setDate(QDate.currentDate().addDays(7))
        row1.addWidget(QLabel("시작일:"))
        row1.addWidget(self.promo_start)
        row1.addWidget(QLabel("종료일:"))
        row1.addWidget(self.promo_end)

        # 🔹 줄2: 카테고리 ~ 단가
        row2 = QHBoxLayout()
        self.promo_category = QComboBox()
        self.load_category_options()  # 여기서 404 날 수 있으니 try/except로 감싸도 됨
        self.promo_price = QLineEdit()
        self.promo_price.setPlaceholderText("단가 (숫자)")
        row2.addWidget(QLabel("분류:"))
        row2.addWidget(self.promo_category)
        row2.addWidget(QLabel("단가:"))
        row2.addWidget(self.promo_price)

        # 🔹 줄3: 적용 버튼 (먼저 선언해야 에러 안 나!)
        row3 = QHBoxLayout()
        apply_btn = QPushButton("적용")
        apply_btn.clicked.connect(self.apply_promotion)
        row3.addStretch()
        row3.addWidget(apply_btn)

        # 전체 추가
        promo_layout.addLayout(row1)
        promo_layout.addLayout(row2)
        promo_layout.addLayout(row3)

        # ── 행사 테이블
        # ── 행사 테이블
        self.promo_table = QTableWidget(0, 4)
        self.promo_table.setHorizontalHeaderLabels(["분류", "단가", "시작", "종료"])
        self.promo_table.horizontalHeader().setStretchLastSection(True)
        self.promo_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        promo_layout.addWidget(self.promo_table)
        promo_box.setLayout(promo_layout)
        main_layout.addWidget(promo_box)
        # ✅ 버튼 이벤트 연결
        self.btn_lent.clicked.connect(self.open_lent_editor_dialog)
        self.btn_new.clicked.connect(self.create_client)
        self.btn_edit.clicked.connect(self.update_client)
        self.btn_delete.clicked.connect(self.delete_client)
        self.btn_assign.clicked.connect(self.assign_employee)
        
        self.btn_unassign.clicked.connect(self.unassign_employee)
    
    def export_excel_clients(self):
        """
        서버에 저장된 거래처들을 조회해 엑셀로 저장
        """
        try:
            # 1. 서버로부터 거래처 목록 가져오기
            clients = api_fetch_clients(get_auth_headers)  # 실제로는 페이지네이션 등 처리 가능
            if not clients:
                QMessageBox.information(self, "알림", "서버에 거래처가 없습니다.")
                return

            # 2. pandas DataFrame으로 변환
            df = pd.DataFrame(clients)
            if df.empty:
                QMessageBox.information(self, "알림", "서버에 거래처가 없습니다.")
                return

            # 3. 사용자에게 저장 경로를 물어봄
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "엑셀로 저장",
                "",
                "Excel Files (*.xlsx *.xls)"
            )
            if not file_path:
                return  # 취소 시

            # 4. DataFrame을 엑셀로 저장
            df.to_excel(file_path, index=False, sheet_name="Clients")
            QMessageBox.information(self, "완료", f"거래처 목록을 엑셀로 저장했습니다:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 내보내기 실패: {e}")
            
    def import_excel_clients(self):
        """
        엑셀 파일에서 거래처 데이터를 읽어 한 번에 등록하는 로직
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "엑셀 파일 불러오기", 
            "", 
            "Excel Files (*.xls *.xlsx)"
        )
        if not file_path:
            return  # 파일 선택이 취소된 경우

        try:
            df = pd.read_excel(file_path)
            # df.columns → 예: ['거래처명','대표자명','주소','전화번호','미수금','일반가','고정가','사업자번호','이메일','비밀번호']

            total_count = 0
            success_count = 0

            for idx, row in df.iterrows():
                # 필요한 컬럼만 추출, NaN 방어코드
                client_name = str(row.get('거래처명','')).strip()
                rep_name    = str(row.get('대표자명','')).strip()
                address     = str(row.get('주소','')).strip()
                phone       = str(row.get('전화번호','')).strip()
                outstanding = float(row.get('미수금', 0) or 0)
                regular_p   = float(row.get('일반가', 35) or 35)
                fixed_p     = float(row.get('고정가', 70) or 70)
                business    = str(row.get('사업자번호','')).strip()
                email       = str(row.get('이메일','')).strip()
                password    = str(row.get('비밀번호','')).strip()  # 비밀번호가 꼭 필요한 경우

                # 필수 값이 부족하면 건너뛰기
                if not client_name:
                    print(f"[{idx}행] 거래처명 없음 → 스킵")
                    continue

                # API에 보낼 payload 구성
                payload = {
                    "client_name": client_name,
                    "representative_name": rep_name,
                    "address": address,
                    "phone": phone,
                    "outstanding_amount": outstanding,
                    "regular_price": regular_p,
                    "fixed_price": fixed_p,
                    "business_number": business,
                    "email": email
                }
                # 비밀번호 입력이 있다면 서버 쪽에 맞춰 전달
                if password:
                    payload["password"] = password

                # 요청 전송
                resp = api_create_client(get_auth_headers, payload)
                total_count += 1
                if resp and hasattr(resp, "status_code") and resp.status_code in (200,201):
                    success_count += 1
                else:
                    print(f"[{idx}행] 등록 실패: {resp.text if resp else 'No response'}")

            QMessageBox.information(
                self,
                "엑셀 등록 완료",
                f"총 {total_count}건 중 {success_count}건 등록 성공!"
            )
            # 등록 후 테이블 새로고침
            self.load_data_from_server()  # 예: self.parentWidget().reload_clients() 식으로 갱신

        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 불러오기 실패: {e}\n{traceback.format_exc()}")

    def on_employee_double_clicked(self, item):
        """
        담당 직원 테이블에서 직원 이름 또는 ID 더블클릭 시 → 직원 탭 전환 요청
        """
        row = item.row()
        if row < 0:
            return

        # 예시: 첫 번째 컬럼이 직원 이름일 경우
        employee_name_item = self.assigned_employees_table.item(row, 0)
        if not employee_name_item:
            return

        employee_name = employee_name_item.text().strip()

        print(f"✅ 직원 더블클릭: {employee_name}")

        # MainApp 찾아서 직원 탭 전환 요청
        main_window = self.find_main_window()
        if main_window:
            main_window.show_employee_tab(employee_name)  # 아래에서 정의할 함수

    def find_main_window(self):
        from PyQt5.QtWidgets import QMainWindow
        parent = self.parent()
        while parent:
            if isinstance(parent, QMainWindow):
                return parent
            parent = parent.parent()
        return None


    def fetch_client_detail(self, client_id: int) -> dict:
        """
        서버로부터 client_id를 이용해 상세 정보를 가져오는 함수(예시)
        """
        import requests
        url = f"{BASE_URL}/clients/{client_id}"
        headers = {"Authorization": f"Bearer {global_token}"}
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()  # { "id":..., "client_name":..., ... }
        return {}
    
    def apply_promotion(self):
        client_id = self.get_value(0).strip()
        if not client_id or not client_id.isdigit():
            QMessageBox.warning(self, "입력 오류", "먼저 거래처를 선택하세요.")
            return

        category = self.promo_category.currentText()
        try:
            price = float(self.promo_price.text())
        except:
            QMessageBox.warning(self, "입력 오류", "올바른 숫자 단가를 입력하세요.")
            return

        # 🔍 단가 유형은 서버에서 카테고리마다 고정이므로 여기선 서버가 처리한다고 가정
        payload = {
            "client_id": int(client_id),
            "category_name": category,
            "price_type": "normal" if category == "바" else "fixed",  # 💡 규칙 기반
            "override_price": price,
            "start_date": self.promo_start.date().toString("yyyy-MM-dd"),
            "end_date": self.promo_end.date().toString("yyyy-MM-dd")
        }

        try:
            url = f"{BASE_URL}/category_price_overrides/"
            resp = requests.post(url, json=payload)
            if resp.status_code == 200:
                QMessageBox.information(self, "성공", "행사 단가가 등록되었습니다.")
                self.load_promotions_for_client(client_id)
            else:
                QMessageBox.warning(self, "실패", f"등록 실패: {resp.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))

    def load_promotions_for_client(self, client_id):
        """ 서버에서 유효한 행사만 불러와서 테이블 표시 """
        try:
            today = QDate.currentDate().toString("yyyy-MM-dd")
            url = f"{BASE_URL}/category_price_overrides/"
            resp = requests.get(url)
            if resp.status_code != 200:
                return

            data = resp.json()
            filtered = [
                p for p in data
                if str(p["client_id"]) == str(client_id)
                and p["start_date"] <= today <= p["end_date"]
            ]

            self.promo_table.setRowCount(len(filtered))
            for row, item in enumerate(filtered):
                start_str = datetime.strptime(item["start_date"], "%Y-%m-%d").strftime("%m/%d")
                end_str = datetime.strptime(item["end_date"], "%Y-%m-%d").strftime("%m/%d")

                self.promo_table.setItem(row, 0, QTableWidgetItem(item["category_name"]))
                self.promo_table.setItem(row, 1, QTableWidgetItem(str(item["override_price"])))
                self.promo_table.setItem(row, 2, QTableWidgetItem(start_str))
                self.promo_table.setItem(row, 3, QTableWidgetItem(end_str))
        except Exception as e:
            print("❌ 행사 목록 불러오기 실패:", e)


    def open_lent_editor_dialog(self):
        client_id = self.get_value(0).strip()
        if not client_id:
            QMessageBox.warning(self, "경고", "거래처를 먼저 선택하세요.")
            return

        dialog = LentEditorDialog(client_id, self)
        if dialog.exec_() == QDialog.Accepted:
            # 저장 완료 후 새로고침 가능
            print("✅ 냉동고 정보 저장 완료")
    
    def unassign_employee(self):
        """ 팝업 창에서 직원 ID를 입력받아 거래처에서 해제하는 기능 """
        global global_token
        client_id = self.get_value(0).strip()

        if not client_id:
            QMessageBox.warning(self, "경고", "담당 직원을 해제할 거래처를 선택하세요.")
            return

        # ✅ 직원 ID 입력 팝업 창
        emp_id, ok = QInputDialog.getInt(self, "담당 직원 해제", "직원 ID를 입력하세요:")
        if not ok:
            return

        # ✅ API 호출하여 직원-거래처 관계 삭제
        response = api_unassign_employee_client(global_token, client_id, emp_id)

        if response and response.status_code == 200:
            QMessageBox.information(self, "성공", f"직원 ID {emp_id}이(가) 거래처에서 해제되었습니다.")
            self.load_assigned_employees(client_id)  # ✅ 해제 후 테이블 업데이트
        else:
            error_msg = response.text if response and hasattr(response, "text") else "알 수 없는 오류 발생"
            QMessageBox.critical(self, "실패", f"담당 직원 해제 실패: {error_msg}")


    def load_category_options(self):
        import os, json

        if os.path.exists("category_order.json"):
            with open("category_order.json", "r", encoding="utf-8") as f:
                order = json.load(f)
                self.promo_category.clear()
                self.promo_category.addItems(order)



   
    def load_assigned_employees(self, client_id):
        """ 현재 거래처의 담당 직원 목록을 가져와 테이블에 표시 """
        global global_token

        print(f"🚀 담당 직원 목록 로드 요청: 거래처 ID {client_id}")

        # ✅ 직원 목록 가져오기
        employees = api_fetch_employees(global_token)
        employee_dict = {e["id"]: e["name"] for e in employees}  # ✅ 직원 ID → 직원 이름 매핑

        # ✅ 직원-거래처 관계 데이터 가져오기
        employee_clients = api_fetch_employee_clients_all(global_token)
        assigned_employees = [e for e in employee_clients if str(e.get("client_id")) == str(client_id)]

        if not assigned_employees:
            print(f"⚠️ 거래처 ID {client_id}에 배정된 직원이 없습니다.")
        else:
            print(f"✅ 거래처 ID {client_id}에 배정된 직원 수: {len(assigned_employees)}")

        self.assigned_employees_table.setRowCount(0)
        for emp in assigned_employees:
            row = self.assigned_employees_table.rowCount()
            self.assigned_employees_table.insertRow(row)

            # ✅ 직원 이름 찾기 (없으면 "알 수 없음" 출력)
            employee_name = employee_dict.get(emp["employee_id"], "알 수 없음")
            self.assigned_employees_table.setItem(row, 0, QTableWidgetItem(employee_name))

    
    def get_employee_name_by_id(self, employee_id):
        """ 직원 ID를 기반으로 직원 이름을 가져오는 함수 """
        global global_token

        # ✅ 직원 ID를 이용해 검색
        employees = api_fetch_employees(global_token, name_keyword="")

        for employee in employees:
            if employee.get("id") == employee_id:
                return employee.get("name", "알 수 없음")

        return "알 수 없음"

    def assign_employee(self):
        """ 직원 ID를 입력받아 거래처와 연결하는 기능 """
        global global_token
        client_id = self.get_value(0).strip()  # ✅ 현재 선택된 거래처 ID 가져오기

        if not client_id:
            QMessageBox.warning(self, "경고", "담당 직원을 배정할 거래처를 선택하세요.")
            return

        # ✅ 직원 ID 입력 팝업 창
        emp_id, ok = QInputDialog.getInt(self, "담당 직원 배정", "직원 ID를 입력하세요:")
        if not ok:
            return

        # ✅ 직원 목록 가져오기
        employees = api_fetch_employees(global_token)
        employee_dict = {e["id"]: e["name"] for e in employees}  # ✅ 직원 ID → 직원 이름 매핑

        # ✅ API 호출하여 직원-거래처 연결
        response = api_assign_employee_client(global_token, client_id, emp_id)
        
        if response and response.status_code == 200:
            emp_name = employee_dict.get(emp_id, "알 수 없음")  # ✅ 직원 이름 찾기
            client_name = self.get_value(1).strip()
            QMessageBox.information(self, "성공", f'"{client_name}"이(가) "{emp_name}" 직원에게 배정되었습니다.')
            self.load_assigned_employees(client_id)  # ✅ 배정 후 테이블 업데이트
        else:
            QMessageBox.critical(self, "실패", "담당 직원 배정에 실패했습니다.")



    def show_lent_freezers(self):
        """
        대여 냉동고 버튼 클릭 시 팝업 창을 띄우는 함수
        """
        global global_token
        client_id = self.get_value(0).strip()  # 거래처 ID 가져오기
        if not client_id:
            QMessageBox.warning(self, "경고", "조회할 거래처 ID가 없습니다.")
            return

        # 대여 냉동고 정보 가져오기
        lent_data = api_fetch_lent_freezers(global_token, client_id)

        if not lent_data:
            QMessageBox.information(self, "정보", "이 거래처에는 대여 냉동고가 없습니다.")
            return

        # 팝업 창 띄우기
        dialog = LentEditorDialog(lent_data, self)
        dialog.exec_()
           
    def display_client(self, client):
        """
        검색된 거래처 정보를 왼쪽 패널에 표시하는 함수
        """
        if not hasattr(self, "table_info") or self.table_info is None:
            print("Error: table_info is None or deleted")
            return

        if not client:
            # 검색 결과가 없으면 모든 칸 초기화
            for r in range(self.row_count):
                self.set_value(r, "")
            return

        # client가 dict 형태라고 가정 (키: id, client_name, address, phone, outstanding_amount, unit_price, business_number, email)
        self.set_value(0, str(client.get("id", "")))
        self.set_value(1, client.get("client_name", ""))
        self.set_value(2, client.get("representative_name", ""))
        self.set_value(3, client.get("address", ""))
        self.set_value(4, client.get("phone", ""))
        self.set_value(5, str(client.get("outstanding_amount", "")))
        self.set_value(6, str(client.get("regular_price", "")))
        self.set_value(7, str(client.get("fixed_price", "")))
        self.set_value(8, client.get("business_number", ""))
        self.set_value(9, client.get("email", ""))
        password_status = "🔒 설정됨" if client.get("password_hash") else "❌ 미설정"
        self.set_value(10, password_status)
        # ✅ 거래처 ID가 있을 경우 담당 직원 목록을 불러옴
        client_id = client.get("id")
        if client_id:
            print(f"🚀 거래처 ID {client_id}의 담당 직원 목록을 불러옵니다.")
            self.load_promotions_for_client(client_id)
            self.load_assigned_employees(client_id)
        else:
            print("⚠️ 거래처 ID가 없습니다. 담당 직원 목록을 불러오지 않습니다.")
        
    def create_client(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        dialog = ClientDialog("신규 거래처 등록")
        if dialog.exec_() == QDialog.Accepted:
            data = {
                "client_name": dialog.name_edit.text(),
                "representative_name": dialog.representative_edit.text(),
                "address": dialog.address_edit.text(),
                "phone": dialog.phone_edit.text(),
                "outstanding_amount": float(dialog.outstanding_edit.text() or 0),
                "regular_price": float(dialog.regular_price__edit.text() or 0),
                "fixed_price": float(dialog.fixed_price_edit.text() or 0),
                "business_number": dialog.business_edit.text(),
                "email": dialog.email_edit.text(),
                "password": "1234",
            }
            resp = api_create_client(global_token, data)
            if resp and resp.status_code in (200, 201):
                QMessageBox.information(self, "성공", "거래처 등록 완료!")
            else:
                QMessageBox.critical(self, "실패", f"거래처 등록 실패: {resp.status_code}\n{resp.text}")

    def update_client(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        client_id = self.get_value(0).strip()
        if not client_id:
            QMessageBox.warning(self, "주의", "수정할 거래처 ID가 없습니다.")
            return

        current_client = {
            "client_name": self.get_value(1),
            "representative_name": self.get_value(2),  # ✅ 추가
            "address": self.get_value(3),
            "phone": self.get_value(4),
            "outstanding_amount": self.get_value(5),
            "regular_price": self.get_value(6),
            "fixed_price": self.get_value(7),
            "business_number": self.get_value(8),
            "email": self.get_value(9),
        }

        
        dialog = ClientDialog("거래처 수정", client=current_client)
        if dialog.exec_() == QDialog.Accepted:
            data = {
                "client_name": dialog.name_edit.text(),
                "representative_name": dialog.representative_edit.text(),
                "address": dialog.address_edit.text(),
                "phone": dialog.phone_edit.text(),
                "outstanding_amount": float(dialog.outstanding_edit.text() or 0),
                "regular_price": float(dialog.regular_price__edit.text() or 35),
                "fixed_price": float(dialog.fixed_price_edit.text() or 70),
                "business_number": dialog.business_edit.text(),
                "email": dialog.email_edit.text(),
            }
            password = dialog.password_edit.text().strip()
            if password:
                data["password"] = password

            resp = api_update_client(global_token, client_id, data)
            if resp and resp.status_code == 200:
                QMessageBox.information(self, "성공", "거래처 수정 완료!")
            else:
                QMessageBox.critical(self, "실패", f"거래처 수정 실패: {resp.status_code}\n{resp.text}")

    def delete_client(self):
        """ 선택된 거래처를 삭제하는 함수 """
        global global_token
        client_id = self.get_value(0).strip()
        
        if not client_id:
            QMessageBox.warning(self, "경고", "삭제할 거래처를 선택하세요.")
            return

        reply = QMessageBox.question(
            self,
            "거래처 삭제 확인",
            f"정말 거래처 ID {client_id}를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            resp = api_delete_client(global_token, client_id)
            
            if resp and hasattr(resp, "status_code") and resp.status_code == 200:
                QMessageBox.information(self, "성공", "거래처가 삭제되었습니다.")
                for r in range(self.row_count):
                    self.set_value(r, "")
            else:
                error_msg = resp.text if resp and hasattr(resp, "text") else "알 수 없는 오류 발생"
                QMessageBox.critical(self, "실패", f"거래처 삭제 실패: {error_msg}")

class ClientRightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # 상단 3개 (Box1, Box2, Box3)
        top_row = QHBoxLayout()

        # 1) 월별 매출
        self.box1 = QGroupBox("월별 매출")
        self.tbl_box1 = QTableWidget(12, 1)
        self.tbl_box1.setVerticalHeaderLabels([f"{i+1}월" for i in range(12)])
        self.tbl_box1.setHorizontalHeaderLabels(["매출"])
        self.tbl_box1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box1.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout1 = QVBoxLayout()
        layout1.addWidget(self.tbl_box1)
        self.box1.setLayout(layout1)
        top_row.addWidget(self.box1, 2)

        # 2) 월별 방문
        self.box2 = QGroupBox("월별 방문 횟수")
        self.tbl_box2 = QTableWidget(12, 1)
        self.tbl_box2.setVerticalHeaderLabels([f"{i+1}월" for i in range(12)])
        self.tbl_box2.setHorizontalHeaderLabels(["방문"])
        self.tbl_box2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box2.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout2 = QVBoxLayout()
        layout2.addWidget(self.tbl_box2)
        self.box2.setLayout(layout2)
        top_row.addWidget(self.box2, 2)

        # 3) 커스텀 달력 (일별 매출)
        self.box3 = QGroupBox("일별 매출 (달력)")
        self.box3_layout = QVBoxLayout()
        self.box3.setLayout(self.box3_layout)
        from datetime import date
        today = date.today()
        self.custom_calendar = CustomCalendarWidget(today.year, today.month, {})
        self.box3_layout.addWidget(self.custom_calendar)
        top_row.addWidget(self.box3, 7)

        # 상단 3개 → 전체 레이아웃에 추가
        main_layout.addLayout(top_row, 2)

        # 하단 - Box4: 분류별 당일 판매
        self.box4 = QGroupBox("당일 분류별 판매")
        layout4 = QVBoxLayout()
        self.tbl_box4_main = QTableWidget(50, 5)
        self.tbl_box4_main.setHorizontalHeaderLabels(["분류", "총매출", "수량", "직원", "기타"])
        self.tbl_box4_main.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box4_main.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout4.addWidget(self.tbl_box4_main)

        self.tbl_box4_footer = QTableWidget(1, 5)
        self.tbl_box4_footer.setFixedHeight(35)
        self.tbl_box4_footer.verticalHeader().setVisible(False)
        self.tbl_box4_footer.horizontalHeader().setVisible(False)
        self.tbl_box4_footer.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout4.addWidget(self.tbl_box4_footer)
        self.box4.setLayout(layout4)

        main_layout.addWidget(self.box4, 1)
        self.setLayout(main_layout)

    def update_sales_calendar(self, year: int, month: int, daily_sales: list[int]):
        sales_map = {i + 1: amt for i, amt in enumerate(daily_sales) if amt > 0}

        self.box3_layout.removeWidget(self.custom_calendar)
        self.custom_calendar.deleteLater()

        self.custom_calendar = CustomCalendarWidget(year, month, sales_map)
        self.box3_layout.addWidget(self.custom_calendar)

    def update_data_for_client(self, client_id: int):
        """
        실제로 client_id를 받아서 서버에서
        - /sales/monthly_sales_client/{client_id}/{year}
        - /sales/monthly_visits_client/{client_id}/{year}
        - /sales/daily_sales_client/{client_id}/{year}/{month}
        - /sales/today_categories_client/{client_id}
        를 호출해 테이블에 채워넣음
        """
        global global_token
        if not global_token:
            print("⚠️ 토큰이 없어 서버 호출이 불가합니다.")
            return

        # 오늘 날짜
        now = datetime.now()
        year = now.year
        month = now.month

        headers = {"Authorization": f"Bearer {global_token}"}
        base_url = BASE_URL  # 서버 주소 (환경에 맞춰 수정)

        # 1) 해당 거래처의 월별 매출
        url_monthly = f"{base_url}/sales/monthly_sales_client/{client_id}/{year}"
        try:
            resp = requests.get(url_monthly, headers=headers)
            resp.raise_for_status()
            monthly_sales = resp.json()  # 예: 길이 12짜리 리스트
        except Exception as e:
            print(f"❌ 월별 매출 조회 실패: {e}")
            monthly_sales = [0]*12

        # 테이블( box1 )에 채워넣기
        for c in range(12):
            self.tbl_box1.setItem(0, c, QTableWidgetItem(str(monthly_sales[c])))

        # 2) 해당 거래처의 월별 방문 횟수
        url_visits = f"{base_url}/client_visits/monthly_visits_client/{client_id}/{year}"
        try:
            resp = requests.get(url_visits, headers=headers)
            resp.raise_for_status()
            monthly_visits = resp.json()  # 예: 길이 12
        except Exception as e:
            print(f"❌ 월별 방문 조회 실패: {e}")
            monthly_visits = []
        # ✅ 리스트 길이가 12가 아닐 경우 기본값(0)으로 채우기
        
        if len(monthly_visits) < 12:
            monthly_visits += [0] * (12 - len(monthly_visits))
        for c in range(12):
            self.tbl_box2.setItem(0, c, QTableWidgetItem(str(monthly_visits[c])))

        # 3) 이번달 일별 매출
        try:
            resp = requests.get(f"{BASE_URL}/sales/daily_sales_client/{client_id}/{year}/{month}", headers=headers)
            resp.raise_for_status()
            daily_sales = resp.json()
        except:
            daily_sales = [0] * 31

        self.update_sales_calendar(year, month, daily_sales)

        # 4) 당일 분류별 판매
        url_today = f"{base_url}/sales/today_categories_client/{client_id}"
        try:
            resp = requests.get(url_today, headers=headers)
            resp.raise_for_status()
            category_data = resp.json()  # [{category, total_amount, total_qty, employee_name}, ...]
        except Exception as e:
            print(f"❌ 당일 분류별 판매조회 실패: {e}")
            category_data = []

        # 테이블 초기화(기존 row 50개라고 했으니, 우선 0행부터 다시 세팅)
        # ✅ 기본 행 개수 설정 (예: 50행 유지)
        default_row_count = max(50, len(category_data) + 1)  # 최소 50개 유지
        self.tbl_box4_main.setRowCount(default_row_count)

        # ✅ API 응답 확인
        print(f"📌 category_data: {category_data}")

        # ✅ 데이터가 없으면 테이블 초기화 (합계만 남김)
        if not category_data:
            print("⚠️ API에서 받은 데이터가 없습니다! 테이블을 초기화합니다.")
            self.tbl_box4_main.setRowCount(default_row_count)  # 기본 행 개수 유지
            for row in range(default_row_count):
                self.tbl_box4_main.setItem(row, 0, QTableWidgetItem(""))
                self.tbl_box4_main.setItem(row, 1, QTableWidgetItem(""))
                self.tbl_box4_main.setItem(row, 2, QTableWidgetItem(""))
                self.tbl_box4_main.setItem(row, 3, QTableWidgetItem(""))
                self.tbl_box4_main.setItem(row, 4, QTableWidgetItem(""))

            # ✅ 마지막 합계 행 추가
            self.tbl_box4_main.setItem(default_row_count - 1, 0, QTableWidgetItem("합계"))
            self.tbl_box4_main.setItem(default_row_count - 1, 1, QTableWidgetItem("0 원"))
            self.tbl_box4_main.setItem(default_row_count - 1, 2, QTableWidgetItem("0 개"))
            self.tbl_box4_main.setItem(default_row_count - 1, 3, QTableWidgetItem(""))
            self.tbl_box4_main.setItem(default_row_count - 1, 4, QTableWidgetItem(""))
            return

        # ✅ 데이터가 있을 경우 기존 테이블에 업데이트 (행 개수 유지)
        total_amt = 0
        total_qty = 0

        for row_idx in range(default_row_count - 1):
            if row_idx < len(category_data):
                item = category_data[row_idx]
                cat = item.get("category", "기타")  # ✅ None 방지
                amt = float(item.get("total_amount", 0))  # ✅ None 방지 후 변환
                qty = int(item.get("total_qty", 0))  # ✅ None 방지 후 변환
                emp = item.get("employee_name", "")  # ✅ None 방지

                self.tbl_box4_main.setItem(row_idx, 0, QTableWidgetItem(cat))  # 분류
                self.tbl_box4_main.setItem(row_idx, 1, QTableWidgetItem(f"{amt:,} 원"))  # ✅ 천 단위 콤마 추가
                self.tbl_box4_main.setItem(row_idx, 2, QTableWidgetItem(f"{qty:,} 개"))  # ✅ 천 단위 콤마 추가
                self.tbl_box4_main.setItem(row_idx, 3, QTableWidgetItem(emp))  # 직원
                self.tbl_box4_main.setItem(row_idx, 4, QTableWidgetItem(""))  # 기타

                total_amt += amt
                total_qty += qty
            else:
                # ✅ 남은 행은 빈 값으로 초기화
                self.tbl_box4_main.setItem(row_idx, 0, QTableWidgetItem(""))
                self.tbl_box4_main.setItem(row_idx, 1, QTableWidgetItem(""))
                self.tbl_box4_main.setItem(row_idx, 2, QTableWidgetItem(""))
                self.tbl_box4_main.setItem(row_idx, 3, QTableWidgetItem(""))
                self.tbl_box4_main.setItem(row_idx, 4, QTableWidgetItem(""))

        # ✅ 마지막 행(합계) 업데이트 (테이블 크기 유지)
        sum_row = default_row_count - 1
        self.tbl_box4_main.setItem(sum_row, 0, QTableWidgetItem("합계"))
        self.tbl_box4_main.setItem(sum_row, 1, QTableWidgetItem(f"{total_amt:,} 원"))  # ✅ 천 단위 콤마 추가
        self.tbl_box4_main.setItem(sum_row, 2, QTableWidgetItem(f"{total_qty:,} 개"))  # ✅ 천 단위 콤마 추가
        self.tbl_box4_main.setItem(sum_row, 3, QTableWidgetItem(""))
        self.tbl_box4_main.setItem(sum_row, 4, QTableWidgetItem(""))

        # ✅ 푸터 테이블도 동일하게 업데이트
        self.tbl_box4_footer.setItem(0, 0, QTableWidgetItem("합계"))
        self.tbl_box4_footer.setItem(0, 1, QTableWidgetItem(f"{total_amt:,} 원"))
        self.tbl_box4_footer.setItem(0, 2, QTableWidgetItem(f"{total_qty:,} 개"))
        self.tbl_box4_footer.setItem(0, 3, QTableWidgetItem(""))
        self.tbl_box4_footer.setItem(0, 4, QTableWidgetItem(""))

        print(f"✅ 테이블 업데이트 완료! 총 판매금액: {total_amt:,} 원, 총 판매수량: {total_qty:,} 개")


class ClientsTab(QWidget):
    """ 거래처 관리 메인 탭 """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        self.left_panel = ClientLeftPanel()
        self.right_panel = ClientRightPanel()

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
    border: 1px solid #CBD5E0;
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
    border: 1px solid #D2D6DC;
    border-radius: 8px;
    gridline-color: #E2E2E2;
    font-size: 13px;
    color: #333333;
    alternate-background-color: #fafafa;
    selection-background-color: #c8dafc;
}
QHeaderView::section {
    background-color: #EEF1F5;
    color: #333333;
    font-weight: 600;
    padding: 6px;
    border: none;
    border-radius: 0;
    border-bottom: 1px solid #ddd;
}
""")
        
    
    def display_client_by_id(self, client_id: int):
        """
        직원창에서 넘어온 client_id를 받아, 서버에서 해당 거래처 정보를 로딩 후
        왼쪽 패널 or 테이블에 표시해주는 함수
        """
        from services.api_services import api_fetch_client_by_id  # 예시
        client_data = api_fetch_client_by_id(global_token, client_id)
        if not client_data:
            print(f"❌ 거래처 ID={client_id} 정보를 가져오지 못했습니다.")
            return
        
        # 예: 왼쪽 테이블/폼에 표시
        # display_client 함수가 있다면 재사용
        self.left_panel.display_client(client_data)
        self.right_panel.update_data_for_client(client_id)

    def do_custom_action(self):
        """ '기능 버튼' 클릭 시 실행되는 동작 (모든 거래처 보기) """
        self.show_all_clients()

    def show_all_clients(self):
        """ 모든 거래처 목록을 가져와서 팝업 창에 표시 """
        global global_token

        # ✅ 전체 거래처 데이터 가져오기
        resp = api_fetch_clients(global_token)
        if not resp or resp.status_code != 200:
            QMessageBox.critical(self, "실패", "거래처 목록 불러오기 실패!")
            return

        clients = resp.json()  # ✅ 전체 거래처 정보 가져오기
        client_names = [c["client_name"] for c in clients]  # ✅ 거래처 이름 리스트 생성

        print(f"📌 UI에서 받은 거래처 데이터: {clients}")  # ✅ 전체 거래처 정보 디버깅
        print(f"📌 ClientSelectionDialog 받은 거래처 이름 목록: {client_names}")  # ✅ 거래처 이름 디버깅

        if not client_names:
            QMessageBox.information(self, "거래처 목록", "등록된 거래처가 없습니다.")
            return

        # ✅ 거래처 선택 팝업 띄우기
        dialog = ClientSelectionDialog(clients, parent=self)

        if dialog.exec_() == QDialog.Accepted and dialog.selected_client:
            selected_client = dialog.selected_client
            print(f"✅ 선택한 거래처 정보: {selected_client}")  # ✅ 선택한 거래처 정보 출력

            self.left_panel.display_client(selected_client)  # ✅ 왼쪽 패널 업데이트
            self.right_panel.update_data_for_client(selected_client["id"])  # ✅ 오른쪽 패널 업데이트

            if selected_client:
                print(f"✅ 선택한 거래처 정보: {selected_client}")  # ✅ 선택한 거래처 정보 출력
                self.left_panel.display_client(selected_client)  # ✅ 왼쪽 패널 업데이트
                self.right_panel.update_data_for_client(selected_client["id"])  # ✅ 오른쪽 패널 업데이트
            else:
                print(f"🚨 거래처를 찾을 수 없음!")




        

    def do_search(self, keyword):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        resp = api_fetch_clients(global_token)
        if not resp or resp.status_code != 200:
            QMessageBox.critical(self, "실패", "거래처 목록 불러오기 실패!")
            return

        clients = resp.json()

        # 검색어 포함된 거래처 찾기 (대소문자 구분 없이 검색)
        filtered_clients = [c for c in clients if keyword.lower() in c["client_name"].lower()]

        if not filtered_clients:
            self.left_panel.display_client(None)
            QMessageBox.information(self, "검색 결과", "검색 결과가 없습니다.")
            return

        if len(filtered_clients) == 1:
            # 검색 결과가 1개면 바로 선택
            self.left_panel.display_client(filtered_clients[0])
        else:
            # 검색 결과가 여러 개면 팝업창 띄우기
            dialog = ClientSelectionDialog(filtered_clients, parent=self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_client:
                selected_client = dialog.selected_client
                self.left_panel.display_client(selected_client)
                self.right_panel.update_data_for_client(selected_client["id"])

        if len(filtered_clients) == 1:
            selected_client = filtered_clients[0]
            self.left_panel.display_client(selected_client)

            # 🟢 오른쪽 패널 업데이트
            cid = selected_client["id"]
            self.right_panel.update_data_for_client(cid)

        else:
            # 여러 건이면 팝업창
            dialog = ClientSelectionDialog(filtered_clients, parent=self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_client:
                selected_client = dialog.selected_client
                self.left_panel.display_client(selected_client)
                self.right_panel.update_data_for_client(selected_client["id"])


                # 동일하게 오른쪽 패널도 갱신
                cid = dialog.selected_client["id"]
                self.right_panel.update_data_for_client(cid)
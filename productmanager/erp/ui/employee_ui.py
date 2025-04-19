from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,QScrollArea,  QGridLayout, QFrame,QCalendarWidget,\
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel, QInputDialog,QVBoxLayout, QListWidget, QDialog, QGroupBox, QDateEdit, QPushButton
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import requests
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from datetime import datetime
import json
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtGui import QFont
from config import BASE_URL
# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가

from services.api_services import api_fetch_employees_, api_create_employee, api_update_employee, api_delete_employee, \
    api_fetch_vehicle, get_auth_headers, api_create_vehicle, api_fetch_employee_vehicle_info
from baselefttabwidget import BaseLeftTableWidget

global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)


from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QHBoxLayout, QDateEdit, QComboBox, QMessageBox
)
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QDate, QRegExp

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QHBoxLayout, QDateEdit, QComboBox, QMessageBox
)
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QDate, QRegExp


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

    def set_sales_data(self, sales_dict: dict[str, int]):
        """
        sales_dict 예: {"2025-04-03": 12000, ...}
        """
        self.sales_data.clear()
        for date_str, value in sales_dict.items():
            try:
                qdate = QDate.fromString(date_str, "yyyy-MM-dd")
                if qdate.year() == self.year and qdate.month() == self.month:
                    self.sales_data[qdate.day()] = value
            except:
                continue
        self.build_calendar()


class EmployeeDialog(QDialog):
    def __init__(self, title, employee=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(500, 600)

        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()

        # ✅ 전화번호 입력란: 숫자만 입력 허용 (10~11자리)
        self.phone_edit = QLineEdit()
        phone_validator = QRegExpValidator(QRegExp(r"^01[0-9]\d{7,8}$"))  # 01012345678 형식 허용
        self.phone_edit.setValidator(phone_validator)

        # ✅ 직책 선택을 위한 드롭다운(QComboBox)
        self.role_edit = QComboBox()
        self.role_edit.addItems(["영업사원", "관리자"])  # ✅ 사용자 선택은 한국어, 서버 전송은 sales/admin

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.birthday_edit = QDateEdit()
        self.birthday_edit.setCalendarPopup(True)
        self.birthday_edit.setDisplayFormat("yyyy-MM-dd")

        self.address_edit = QLineEdit()
        
        form_layout.addRow("이름:", self.name_edit)
        form_layout.addRow("전화번호:", self.phone_edit)
        form_layout.addRow("직책:", self.role_edit)  # ✅ 드롭다운 메뉴 적용
        form_layout.addRow("생일:", self.birthday_edit)
        form_layout.addRow("주소:", self.address_edit)
        form_layout.addRow("비밀번호:", self.password_edit)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("확인")
        self.cancel_button = QPushButton("취소")
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

        # ✅ 버튼 이벤트 연결
        self.ok_button.clicked.connect(self.validate_and_accept)
        self.cancel_button.clicked.connect(self.reject)
        
        # ✅ 수정 시 기존 정보 미리 채우기 (비밀번호 제외)
        if employee:
            self.name_edit.setText(employee.get("name", ""))
            self.phone_edit.setText(self.clean_phone_number(employee.get("phone", "")))
            self.role_edit.setCurrentText(self.role_to_display(employee.get("role", "sales")))  # ✅ 기존 역할 변환
            if employee.get("birthday"):
                date_obj = QDate.fromString(employee.get("birthday"), "yyyy-MM-dd")
                self.birthday_edit.setDate(date_obj)
            self.address_edit.setText(employee.get("address", ""))

    def validate_and_accept(self):
        """ ✅ 입력값 검증 후 다이얼로그 닫기 """
        phone_text = self.clean_phone_number(self.phone_edit.text())

        if not phone_text:
            QMessageBox.warning(self, "입력 오류", "전화번호를 입력하세요.")
            return

        if not phone_text.isdigit() or len(phone_text) not in (10, 11):
            QMessageBox.warning(self, "입력 오류", "전화번호 형식이 올바르지 않습니다.\n예: 01012345678 (숫자만 입력)")
            return

        self.phone_edit.setText(phone_text)  # ✅ '-' 제거된 형식으로 저장
        self.accept()

    def clean_phone_number(self, phone):
        """ ✅ 전화번호에서 '-' 제거 후 반환 """
        return phone.replace("-", "")

    def role_to_display(self, role):
        """ ✅ 서버에서 가져온 role을 UI용 한국어로 변환 """
        return "관리자" if role == "admin" else "영업사원"

    def role_to_server(self):
        """ ✅ UI에서 선택한 role을 서버 전송용 영문으로 변환 """
        return "admin" if self.role_edit.currentText() == "관리자" else "sales"



class EmployeeSelectionDialog(QDialog):
    def __init__(self, employees, parent=None):
        super().__init__(parent)
        self.setWindowTitle("검색 결과")
        self.resize(300, 400)
        self.employees = employees  # 직원 목록 (dict 리스트)
        self.selected_employee = None

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        # "ID - 이름" 형식으로 항목 추가
        for emp in employees:
            display_text = f"{emp.get('id')} - {emp.get('name')}"
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
            self.selected_employee = self.employees[index]
            self.accept()
        else:
            QMessageBox.warning(self, "선택", "직원을 선택해주세요.")

class VehicleDialog(QDialog):
    """ 차량 등록 팝업 창 """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("차량 정보 등록/수정")
        self.setFixedSize(300, 250)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # 입력 필드 생성
        self.emp_id_edit = QLineEdit()
        self.monthly_fuel_edit = QLineEdit()
        self.current_mileage_edit = QLineEdit()
        self.oil_change_date_edit = QDateEdit()
        self.oil_change_date_edit.setCalendarPopup(True)
        self.oil_change_date_edit.setDate(QDate.currentDate())

        # 폼 레이아웃에 추가
        form_layout.addRow("직원 ID:", self.emp_id_edit)
        form_layout.addRow("월 주유비:", self.monthly_fuel_edit)
        form_layout.addRow("현재 주행거리:", self.current_mileage_edit)
        form_layout.addRow("엔진오일 교체일:", self.oil_change_date_edit)

        layout.addLayout(form_layout)

        # 버튼 추가
        self.btn_confirm = QPushButton("확인")
        self.btn_cancel = QPushButton("취소")

        layout.addWidget(self.btn_confirm)
        layout.addWidget(self.btn_cancel)

        self.btn_confirm.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        self.setLayout(layout)

    def get_vehicle_data(self):
        """ 입력된 차량 정보를 반환 """
        try:
            return {
                "employee_id": int(self.emp_id_edit.text().strip()),
                "monthly_fuel_cost": float(self.monthly_fuel_edit.text().strip()),
                "current_mileage": int(self.current_mileage_edit.text().strip()),
                "last_engine_oil_change": self.oil_change_date_edit.date().toString("yyyy-MM-dd")
            }
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "올바른 숫자 값을 입력하세요.")
            return None
        
class EmployeeLeftWidget(BaseLeftTableWidget):
    def __init__(self, parent=None):
        """
        7행(직원ID, 이름, 전화번호, 직책, 차량_주유비, 주행거리, 엔진오일교체일)을
        테이블 형태로 배치하는 UI.
        """
        labels = [
            "직원ID", "이름", "전화번호", "직책", "생일", "주소",
            "차량_주유비", "현재_주행거리", "엔진오일교체일"
        ]
        super().__init__(row_count=len(labels), labels=labels, parent=parent)
        # -------------------------------------------
        # 1) "담당 거래처 / 이번달 매출" 테이블 추가
        # -------------------------------------------
        # 📌 1) 테이블 설정
        self.client_sales_table = QTableWidget()
        self.client_sales_table.setColumnCount(4)
        self.client_sales_table.setHorizontalHeaderLabels(["거래처명", "이번달 매출", "미수금", "id"])
        self.client_sales_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.client_sales_table.verticalHeader().setVisible(False)

        self.client_sales_table.itemDoubleClicked.connect(self.on_client_sales_double_clicked)

        # 열 크기 조절
        header = self.client_sales_table.horizontalHeader()

        # 첫 번째 열 (client_id) - 최소 크기 설정
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # client_id는 자동 크기

        # 두 번째, 세 번째, 네 번째 열 - 내용에 맞게 크기 조정
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 거래처명
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 이번달 매출
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 미수금

        # 네 번째 열에 대해서는 Stretch를 사용해서 테이블 내 공간을 나눠줍니다.
        header.setSectionResizeMode(3, QHeaderView.Stretch) 

        # 📌 2) 스크롤 영역으로 감싸기
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.client_sales_table)
        scroll_area.setFixedHeight(350)

        # 📌 3) 합계 라벨 추가
        self.client_sales_total_label = QLabel("합계: 0 원")
        self.client_sales_total_label.setAlignment(Qt.AlignRight)
        self.client_sales_total_label.setFont(QFont("Arial", 10, QFont.Bold))

        # 📌 4) 레이아웃에 추가
        self.client_sales_label = QLabel("담당 거래처 + 이번달 매출")
        self.layout().addWidget(self.client_sales_label)
        self.layout().addWidget(scroll_area)
        self.layout().addWidget(self.client_sales_total_label)
        # 테이블 하단에 여유 공간 확보 (예: stretch)
        # spacer = QWidget()
        # spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.layout().addWidget(spacer)
        
        # 상위 BaseLeftTableWidget에서 table_info + "신규등록/수정" 버튼 생성
        self.btn_new.clicked.connect(self.create_employee)
        self.btn_edit.clicked.connect(self.update_employee)
        self.btn_delete = QPushButton("삭제")
        self.btn_vehicle = QPushButton("차량등록")

        
        # BaseLeftTableWidget의 레이아웃(버튼이 들어있는 레이아웃)에 추가합니다.
        # (BaseLeftTableWidget의 init_ui()에서 마지막에 addLayout(btn_layout)을 호출함)
        self.layout().itemAt(1).layout().addWidget(self.btn_delete)
        self.btn_delete.clicked.connect(self.delete_employee)
        self.layout().itemAt(1).layout().addWidget(self.btn_vehicle)
        self.btn_vehicle.clicked.connect(self.create_vehicle)
        
    def on_client_sales_double_clicked(self, item):
        """
        담당 거래처 테이블의 셀을 더블클릭하면 실행되는 슬롯 함수
        - 더블클릭된 거래처(순번, 거래처명 등) 행 정보를 가져와서 거래처 ID를 파악
        """
        row = item.row()
        if row < 0:
            return

        # 첫 번째 열에 client_id가 들어 있다고 가정하고 이를 가져옵니다.
        client_id_item = self.client_sales_table.item(row, 3)  # 첫 번째 열
        if not client_id_item:
            return

        client_id_str = client_id_item.text().strip()  # 텍스트로 읽어오기
        if not client_id_str.isdigit():
            print("⚠️ 잘못된 거래처 ID:", client_id_str)
            return

        client_id = int(client_id_str)  # client_id를 정수로 변환
        print(f"✅ 더블클릭으로 거래처 ID={client_id} 확인")

        # MainWindow에서 거래처 탭으로 이동하도록 요청
        main_window = self.find_main_window()  # 상위 MainWindow를 찾기 위한 메서드
        if main_window:
            main_window.show_client_tab(client_id)  # 거래처 화면으로 이동하는 메서드 호출


    def find_main_window(self):
        """
        부모 위젯들을 거슬러 올라가면서 MainWindow(혹은 최상위 Window)를 찾는 헬퍼 함수
        """
        from PyQt5.QtWidgets import QMainWindow
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, QMainWindow):
                return parent
            parent = parent.parent()
        return None
    
    def create_vehicle(self):
        """ 차량 등록 팝업 창 열기 및 등록 처리 """
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        dialog = VehicleDialog(self)
        if dialog.exec_():  # 사용자가 "확인"을 눌렀을 때만 실행
            data = dialog.get_vehicle_data()
            if not data:
                return

            try:
                resp = api_create_vehicle(global_token, data)
                if resp is None:  # ✅ 응답이 None이면 오류 처리
                    QMessageBox.critical(self, "오류", "서버에서 응답이 없습니다. 다시 시도해 주세요.")
                    return

                resp.raise_for_status()
                QMessageBox.information(self, "성공", "차량 정보가 등록/수정되었습니다.")
                self.fetch_vehicle()  # 차량 정보 갱신
            except requests.exceptions.HTTPError as http_err:
                QMessageBox.critical(self, "HTTP 오류", f"HTTP 오류 발생: {http_err}")
            except requests.exceptions.RequestException as req_err:
                QMessageBox.critical(self, "네트워크 오류", f"네트워크 오류 발생: {req_err}")
            except Exception as ex:
                QMessageBox.critical(self, "오류", f"예외 발생: {str(ex)}")


    def fetch_vehicle(self):
        """ 현재 선택된 직원의 차량 정보를 조회하고 기존 테이블에 추가 """
        global global_token

        emp_id = self.get_value(0).strip()  # ✅ 직원ID 가져오기
        if not emp_id:
            QMessageBox.warning(self, "경고", "조회할 직원이 선택되지 않았습니다.")
            return

        try:
            print(f"✅ 차량 정보 조회 요청: 직원 ID = {emp_id}")
            resp = api_fetch_vehicle(global_token, emp_id)  # ✅ 직원 ID 전달

            if resp is None:
                QMessageBox.critical(self, "오류", "서버 응답이 없습니다.")
                return

            if isinstance(resp, str):  # ✅ 응답이 문자열이면 JSON 변환 시도
                print(f"🚀 응답이 문자열입니다. JSON 변환 시도: {resp}")
                resp = json.loads(resp)

            if not isinstance(resp, dict):  # ✅ 응답이 딕셔너리인지 확인
                QMessageBox.critical(self, "오류", "서버 응답 형식이 잘못되었습니다.")
                return

            # ✅ 기존 직원 테이블에 차량 정보 추가
            self.set_value(6, str(resp.get("monthly_fuel_cost", "")))
            self.set_value(7, str(resp.get("current_mileage", "")))
            self.set_value(8, resp.get("last_engine_oil_change", ""))

        except Exception as ex:
            QMessageBox.critical(self, "오류", f"예외 발생: {str(ex)}")


                        
    def display_employee(self, employee):
        """
        검색된 직원 정보(또는 None)를 받아,
        테이블의 각 행(0~8)에 값을 채워넣음.
        """
        if not hasattr(self, "table_info") or self.table_info is None:
            print("Error: table_info is None or deleted")
            return

        if not employee:
            for r in range(self.row_count):
                self.set_value(r, "")
            return

        emp_id = str(employee.get("id", ""))
        self.set_value(0, emp_id)
        self.set_value(1, employee.get("name", ""))
        self.set_value(2, employee.get("phone", ""))
        self.set_value(3, self.role_to_display(employee.get("role", "")))  # ✅ 직책 변환
        self.set_value(4, employee.get("birthday", ""))
        self.set_value(5, employee.get("address", ""))

        veh = api_fetch_employee_vehicle_info(employee["id"])
        if veh:
            self.set_value(6, str(veh.get("monthly_fuel_cost", "")))
            self.set_value(7, str(veh.get("current_mileage", "")))
            self.set_value(8, str(veh.get("last_engine_oil_change", "")))
        else:
            self.set_value(6, "")
            self.set_value(7, "")
            self.set_value(8, "")

        if not employee:
            for r in range(self.row_count):
                self.set_value(r, "")
            # 하단 테이블도 비우기
            self.client_sales_table.setRowCount(0)
            return

        emp_id = str(employee.get("id", ""))
        self.set_value(0, emp_id)
        ...
        # 차량 정보 표시 ...

        # 새로 추가: 담당 거래처 + 매출 테이블 갱신
        self.update_client_sales(emp_id)

    def update_client_sales(self, emp_id):
        from datetime import datetime
        now = datetime.now()
        year = now.year
        month = now.month

        url = f"{BASE_URL}/sales/"
        headers = {"Authorization": f"Bearer {global_token}"}
        params = {"employee_id": emp_id, "year": year, "month": month}

        try:
            resp = requests.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print("❌ 직원 거래처 매출 조회 실패:", e)
            return

        per_client = data.get("per_client", {})
        client_names = data.get("client_names", {})
        outstanding_map = data.get("outstanding_map", {})  # 추가된 미수금 map

        self.client_sales_table.clearContents()

        # 열 수: 거래처명, 이번달 매출, 미수금, client_id (숨겨진 열로 추가)
        self.client_sales_table.setColumnCount(4)  
        self.client_sales_table.setHorizontalHeaderLabels(["거래처명", "이번달 매출", "미수금", "id"])

        self.client_sales_table.setRowCount(len(per_client))

        # 열 크기 조절
        header = self.client_sales_table.horizontalHeader()

        # 첫 번째 열 (client_id) - 최소 크기 설정
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # client_id는 자동 크기

        # 두 번째, 세 번째, 네 번째 열 - 내용에 맞게 크기 조정
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 거래처명
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 이번달 매출
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 미수금

        # 네 번째 열에 대해서는 Stretch를 사용해서 테이블 내 공간을 나눠줍니다.
        header.setSectionResizeMode(3, QHeaderView.Stretch) 

        total_sum = 0
        for row_idx, (client_id, monthly_sales) in enumerate(per_client.items()):
            name = client_names.get(str(client_id), f"거래처 {client_id}")
            this_month_sales = monthly_sales[month - 1]  # 이번 달 매출
            outstanding_val = outstanding_map.get(str(client_id), 0.0)

            # 거래처명
            item_name = QTableWidgetItem(name)
            item_name.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.client_sales_table.setItem(row_idx, 0, item_name)

            # 이번달 매출
            item_sales = QTableWidgetItem(f"{this_month_sales:,.0f} 원")
            item_sales.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.client_sales_table.setItem(row_idx, 1, item_sales)

            # 미수금
            item_outs = QTableWidgetItem(f"{outstanding_val:,.0f} 원")
            item_outs.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.client_sales_table.setItem(row_idx, 2, item_outs)

            # client_id (숨겨진 열에 설정)
            item_client_id = QTableWidgetItem(str(client_id))
            item_client_id.setTextAlignment(Qt.AlignCenter)
            item_client_id.setFlags(item_client_id.flags() & ~Qt.ItemIsEditable)  # 읽기 전용으로 설정
            self.client_sales_table.setItem(row_idx, 3, item_client_id)

            total_sum += this_month_sales

        # 합계 라벨 표시
        self.client_sales_total_label.setText(f"합계: {total_sum:,.0f} 원")
        self.client_sales_total_label.setAlignment(Qt.AlignRight)





    def format_phone_number(self, phone):
        """ ✅ 전화번호를 '010-1234-5678' 형식으로 변환 """
        phone = self.clean_phone_number(phone)  # ✅ 하이픈 제거 후 숫자만 남김
        if len(phone) == 10:
            return f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
        elif len(phone) == 11:
            return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
        return phone  # 변환 실패 시 원본 반환


    def clean_phone_number(self, phone):
        """ ✅ 전화번호에서 '-' 제거 후 숫자만 반환 """
        return "".join(filter(str.isdigit, phone))  # 숫자만 남기기

    def create_employee(self):
        """
        '신규등록' 버튼 클릭 시 팝업 다이얼로그를 띄워서 새 직원 정보를 입력받고,
        서버에 등록.
        """
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        dialog = EmployeeDialog("신규 직원 등록")
        if dialog.exec_() == QDialog.Accepted:
            data = {
                "password": dialog.password_edit.text() or "1234",
                "name": dialog.name_edit.text(),
                "phone": self.clean_phone_number(dialog.phone_edit.text()),
                "role": dialog.role_to_server(),
                "birthday": dialog.birthday_edit.date().toString("yyyy-MM-dd"),
                "address": dialog.address_edit.text()
            }
            resp = api_create_employee(global_token, data)
            if resp and resp.status_code in (200, 201):
                QMessageBox.information(self, "성공", "직원 등록 완료!")
            else:
                status = resp.status_code if resp else "None"
                text = resp.text if resp else "No response"
                QMessageBox.critical(self, "실패", f"직원 등록 실패: {status}\n{text}")

    def update_employee(self):
        """
        '수정' 버튼 클릭 시 팝업 다이얼로그를 띄워서 현재 직원 정보를 수정하고,
        서버에 업데이트.
        """
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인이 필요합니다.")
            return

        emp_id = self.get_value(0).strip()
        if not emp_id:
            QMessageBox.warning(self, "주의", "수정할 직원 ID가 없습니다.")
            return

        # 현재 테이블에 표시된 정보를 미리 불러옴
        current_employee = {
            "name": self.get_value(1),
            "phone": self.get_value(2),
            "role": self.role_to_display(self.get_value(3)),  # ✅ 직책 변환 (UI에서 "관리자"/"영업사원"으로 표시)
            "birthday": self.get_value(4),
            "address": self.get_value(5)
        }
        dialog = EmployeeDialog("직원 수정", employee=current_employee)
        if dialog.exec_() == QDialog.Accepted:
            data = {
                "password": dialog.password_edit.text() or "1234",
                "name": dialog.name_edit.text(),
                "phone": self.clean_phone_number(dialog.phone_edit.text()), 
                "role": dialog.role_to_server(),  # ✅ 서버 전송 시 변환 ("관리자" → "admin", "영업사원" → "sales")
                "birthday": dialog.birthday_edit.date().toString("yyyy-MM-dd"),
                "address": dialog.address_edit.text()
            }
            resp = api_update_employee(global_token, emp_id, data)
            if resp and resp.status_code == 200:
                QMessageBox.information(self, "성공", "직원 수정 완료!")
            else:
                status = resp.status_code if resp else "None"
                text = resp.text if resp else "No response"
                QMessageBox.critical(self, "실패", f"직원 수정 실패: {status}\n{text}")

    def role_to_display(self, role):
        """ ✅ 서버에서 가져온 role을 UI용 한국어로 변환 """
        return "관리자" if role == "admin" else "영업사원"

    def role_to_server(self):
        """ ✅ UI에서 선택한 role을 서버 전송용 영문으로 변환 """
        return "admin" if self.role_edit.currentText() == "관리자" else "sales"

    def delete_employee(self):
        global global_token
        emp_id = self.get_value(0).strip()
        if not emp_id:
            QMessageBox.warning(self, "주의", "삭제할 직원 ID가 없습니다.")
            return

        reply = QMessageBox.question(
            self,
            "직원 삭제 확인",
            f"정말 직원 ID {emp_id}를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            resp = api_delete_employee(global_token, emp_id)
            if resp and resp.status_code == 200:
                QMessageBox.information(self, "성공", "직원 삭제 완료!")
                # 삭제 후, 테이블을 초기화
                for r in range(self.row_count):
                    self.set_value(r, "")
            else:
                status = resp.status_code if resp else "None"
                text = resp.text if resp else "No response"
                QMessageBox.critical(self, "실패", f"직원 삭제 실패: {status}\n{text}")


class EmployeeRightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_tab = parent  # 부모 탭을 저장
        self.year = datetime.now().year  # 기본값으로 현재 연도 설정
        self.month = datetime.now().month  # 기본값으로 현재 월 설정
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # 🔷 월별 매출 박스
        self.box1 = QGroupBox("월별 매출")
        self.tbl_box1 = QTableWidget(12, 1)
        self.tbl_box1.setVerticalHeaderLabels([f"{i+1}월" for i in range(12)])
        self.tbl_box1.setHorizontalHeaderLabels(["매출"])
        self.tbl_box1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box1.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        box1_layout = QVBoxLayout()
        box1_layout.addWidget(self.tbl_box1)
        self.box1.setLayout(box1_layout)

        # 🔷 월별 방문 박스
        self.box2 = QGroupBox("월별 방문 횟수")
        self.tbl_box2 = QTableWidget(12, 1)
        self.tbl_box2.setVerticalHeaderLabels([f"{i+1}월" for i in range(12)])
        self.tbl_box2.setHorizontalHeaderLabels(["방문"])
        self.tbl_box2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box2.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        box2_layout = QVBoxLayout()
        box2_layout.addWidget(self.tbl_box2)
        self.box2.setLayout(box2_layout)

        # 🔷 달력 박스
        self.box3 = QGroupBox("일별 매출 (달력)")
        self.box3_layout = QVBoxLayout()

        from datetime import date
        today = date.today()
        self.year, self.month = today.year, today.month

        # 🔹 달력 타이틀 라벨
        self.lbl_calendar_title = QLabel()
        self.lbl_calendar_title.setAlignment(Qt.AlignCenter)
        self.lbl_calendar_title.setFont(QFont("Malgun Gothic", 13, QFont.Bold))
        self.update_calendar_title()

        # 🔹 이전/다음 버튼
        self.prev_button = QPushButton("◀")
        self.next_button = QPushButton("▶")
        self.prev_button.setFixedSize(60, 32)
        self.next_button.setFixedSize(60, 32)
        self.prev_button.clicked.connect(self.show_previous_month)
        self.next_button.clicked.connect(self.show_next_month)

        # 🔹 버튼과 타이틀을 나란히
        title_row = QHBoxLayout()
        title_row.addWidget(self.prev_button)
        title_row.addStretch()
        title_row.addWidget(self.lbl_calendar_title)
        title_row.addStretch()
        title_row.addWidget(self.next_button)

        # 🔹 달력 위젯
        self.custom_calendar = CustomCalendarWidget(self.year, self.month, {})
        self.custom_calendar.setFixedHeight(360)

        # 🔹 box3 조립
        
        self.box3_layout.addWidget(self.custom_calendar)
        self.box3.setLayout(self.box3_layout)

        # 🔷 상단 3박스 정렬 (2:2:7 비율)
        top_row = QHBoxLayout()
        top_row.addWidget(self.box1, 2)
        top_row.addWidget(self.box2, 2)
        top_row.addWidget(self.box3, 7)

        # 🔷 상단 컨테이너
        top_container = QWidget()
        top_container_layout = QVBoxLayout()
        top_container_layout.addLayout(title_row)
        top_container_layout.addLayout(top_row)
        top_container.setLayout(top_container_layout)
        top_container.setMaximumHeight(600)  # 크기 흔들림 방지

        # 🔷 하단 거래처 정보
        self.box4 = QGroupBox("당일 방문 거래처 정보")
        layout4 = QVBoxLayout()

        self.tbl_box4_main = QTableWidget(50, 5)
        self.tbl_box4_main.setHorizontalHeaderLabels(["거래처", "오늘 매출", "미수금", "방문시간", "기타"])
        self.tbl_box4_main.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box4_main.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout4.addWidget(self.tbl_box4_main)

        self.tbl_box4_footer = QTableWidget(1, 5)
        self.tbl_box4_footer.verticalHeader().setVisible(False)
        self.tbl_box4_footer.horizontalHeader().setVisible(False)
        self.tbl_box4_footer.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box4_footer.setFixedHeight(35)
        self.tbl_box4_footer.setItem(0, 0, QTableWidgetItem("합계"))
        self.tbl_box4_main.horizontalScrollBar().valueChanged.connect(
            self.tbl_box4_footer.horizontalScrollBar().setValue
        )
        layout4.addWidget(self.tbl_box4_footer)
        self.box4.setLayout(layout4)

        # 🔷 전체 레이아웃 조립
        main_layout.addWidget(top_container, 2)
        main_layout.addWidget(self.box4, 1)
        self.setLayout(main_layout)

    def update_calendar_title(self):
        self.lbl_calendar_title.setText(f"{self.year}년 {self.month}월")

    def update_calendar_title_1(self, year, month):
        self.lbl_calendar_title.setText(f"{year}년 {month}월") 
           
    def update_all(self):
        """ 모든 박스(매출, 방문, 달력)를 한 번에 업데이트 """
        self.update_monthly_sales()
        self.update_monthly_visits()
        
        self.update_calendar()

    def update_monthly_sales(self):
        """ 월별 매출 업데이트 """
        print(f"✅ 월별 매출 업데이트: {self.year}년 {self.month}월")

    def update_monthly_visits(self):
        """ 월별 방문 횟수 업데이트 """
        print(f"✅ 월별 방문 횟수 업데이트: {self.year}년 {self.month}월")

    def update_calendar(self):
        """ 일별 매출 (달력) 업데이트 """
        print(f"✅ 달력 업데이트: {self.year}년 {self.month}월")
        self.parent_tab.do_update_data_from_db(self.year, self.month)

    def show_previous_month(self):
        """ 이전 달로 이동 """
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self.update_all()
        self.update_calendar_title()

    def show_next_month(self):
        """ 다음 달로 이동 """
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.update_all()
        self.update_calendar_title()
    def update_calendar_sales(self, year: int, month: int, sales_list: list[int]):
        sales_map = {day + 1: amt for day, amt in enumerate(sales_list) if amt > 0}

        # 이전 달력 제거
        self.box3_layout.removeWidget(self.custom_calendar)
        self.custom_calendar.deleteLater()

        # 새 달력 추가
        self.custom_calendar = CustomCalendarWidget(year, month, sales_map)
        self.box3_layout.addWidget(self.custom_calendar)
        
    
        
    def on_date_selected(self, date: QDate):
        print("선택된 날짜:", date.toString("yyyy-MM-dd"))

    def update_data_from_db(self, employee_id: int, year: int, month: int):
        if not global_token:
            return

        headers = {"Authorization": f"Bearer {global_token}"}

        # 월별 매출
        try:
            resp = requests.get(f"{BASE_URL}/sales/monthly_sales_pc/{employee_id}/{year}", headers=headers)
            monthly_sales = resp.json()
           
        except:
            monthly_sales = {}

        if not isinstance(monthly_sales, dict):
            print("⚠️ dict 아님! 서버 응답 확인 필요")
            monthly_sales = {i + 1: 0 for i in range(12)}

        for i in range(12):
            key = str(i + 1)  # 문자열 키로!
            value = monthly_sales.get(key, 0)
            self.tbl_box1.setItem(i, 0, QTableWidgetItem(f"{value:,}"))



       # 월별 방문
        try:
            resp = requests.get(f"{BASE_URL}/client_visits/monthly_visits/{employee_id}/{year}", headers=headers)
            monthly_visits = resp.json()
        except:
            monthly_visits = []

        # 안전성 체크
        if not isinstance(monthly_visits, list) or len(monthly_visits) < 12:
            monthly_visits = [0] * 12  # 부족하거나 이상하면 초기화

        for i in range(12):
            self.tbl_box2.setItem(i, 0, QTableWidgetItem(str(monthly_visits[i])))

        # 일별 매출
        try:
            resp = requests.get(f"{BASE_URL}/sales/daily_sales_pc/{employee_id}/{year}/{month}", headers=headers)
            daily_sales = resp.json()
        except:
            daily_sales = []

        # 안전성 체크
        if not isinstance(daily_sales, list) or len(daily_sales) < 31:
            daily_sales = [0] * 31  # 보통 31일 기준으로 넉넉하게

        # 달력에 표시할 매출 맵
        sales_dict = {}
        for i, val in enumerate(daily_sales):
            if val > 0:
                date_key = f"{year}-{month:02d}-{i+1:02d}"
                sales_dict[date_key] = val

        self.custom_calendar.set_sales_data(sales_dict)



        # ✅ 당일 방문 거래처
        try:
            resp = requests.get(f"{BASE_URL}/client_visits/today_visits_details?employee_id={employee_id}", headers=headers)
            visits_data = resp.json()
        except:
            visits_data = []

        # ✅ 응답이 리스트 형태가 아니면 빈 리스트로 보정
        if not isinstance(visits_data, list):
            visits_data = []

        # ✅ 캘린더도 갱신
        self.update_calendar_sales(year, month, daily_sales)

        # ✅ 방문 거래처 테이블 초기화
        self.tbl_box4_main.setRowCount(max(50, len(visits_data) + 1))

        # ✅ 합계 계산
        total_today_sales = 0
        total_outstanding = 0

        for row in range(50):
            if row < len(visits_data):
                v = visits_data[row] or {}  # 요소 자체가 None인 경우도 방지
                name = v.get("client_name", "")
                today_sales = v.get("today_sales", 0)
                outstanding = v.get("outstanding_amount", 0)
                visit_time = v.get("visit_datetime", "")
                visit_count = v.get("visit_count", 1)

                total_today_sales += today_sales
                total_outstanding += outstanding

                self.tbl_box4_main.setItem(row, 0, QTableWidgetItem(name))
                self.tbl_box4_main.setItem(row, 1, QTableWidgetItem(f"{today_sales:,} 원"))
                self.tbl_box4_main.setItem(row, 2, QTableWidgetItem(f"{outstanding:,} 원"))
                self.tbl_box4_main.setItem(row, 3, QTableWidgetItem(visit_time))
                self.tbl_box4_main.setItem(row, 4, QTableWidgetItem(str(visit_count)))
            else:
                for col in range(5):
                    self.tbl_box4_main.setItem(row, col, QTableWidgetItem(""))

        # ✅ 합계 라인 (맨 마지막 줄)
        self.tbl_box4_main.setItem(49, 0, QTableWidgetItem("합계"))
        self.tbl_box4_main.setItem(49, 1, QTableWidgetItem(f"{total_today_sales:,} 원"))
        self.tbl_box4_main.setItem(49, 2, QTableWidgetItem(f"{total_outstanding:,} 원"))



class EmployeesTab(QWidget):
    """ 직원 관리 메인 탭 """

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.employee_id = None  # 직원 ID 초기화
    def init_ui(self):
        main_layout = QHBoxLayout()
        
        self.setFont(QFont("Malgun Gothic", 15))  # 혹은 Windows/기본폰
        self.left_panel = EmployeeLeftWidget()
        self.right_panel = EmployeeRightPanel(parent=self)

        self.left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ✅ 고정 크기 설정
        self.left_panel.setFixedWidth(350)  # 1 비율
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)

        self.setLayout(main_layout)
                # 📌 ERP 스타일 QSS 테마 적용
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

    def display_employee_by_name(self, name: str):
        """
        직원 이름으로 검색 후:
        1. 왼쪽 패널에 표시
        2. 오른쪽 패널(캘린더, 방문횟수, 매출 등)도 업데이트
        """
        from services.api_services import api_fetch_employees
        

        all_emps = api_fetch_employees(global_token)

        match = next((emp for emp in all_emps if emp.get("name") == name), None)

        if not match:
            QMessageBox.warning(self, "검색 실패", f"'{name}' 직원 정보를 찾을 수 없습니다.")
            return

        print(f"✅ 직원 정보 로딩: {match}")
        self.left_panel.display_employee(match)

        # ✅ 오른쪽 패널도 업데이트
        employee_id = match.get("id")
        
        if employee_id:
            self.employee_id = employee_id  # 선택된 직원 ID 저장
            self.update_employee_ui(employee_id)
            
        

    def do_update_data_from_db(self, year, month):
        print(f"{self.employee_id}")
        self.right_panel.update_data_from_db(self.employee_id, year, month)

    def update_employee_ui(self, employee_id: int):
        """ 매출 발생 후 직원 데이터 업데이트 """
        now = datetime.now()
        year = now.year
        month = now.month
        self.employee_id = employee_id
        self.right_panel.update_data_from_db(employee_id, year, month)    

    def do_custom_action(self):
        """ '기능 버튼' 클릭 시 실행되는 동작 (모든 직원 보기) """
        self.show_all_employees()

    def show_all_employees(self):
        """ 모든 직원 목록을 가져와서 팝업 창에 표시 """
        global global_token
        employees = api_fetch_employees_(global_token, "")  # ✅ 빈 문자열로 모든 직원 가져오기

        if not isinstance(employees, list) or len(employees) == 0:
            QMessageBox.information(self, "직원 목록", "등록된 직원이 없습니다.")
            return

        # ✅ 직원 선택 팝업 띄우기
        dialog = EmployeeSelectionDialog(employees, parent=self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_employee:
            selected_emp = dialog.selected_employee
            self.employee_id = selected_emp["id"]
            self.left_panel.display_employee(selected_emp)
            self.left_panel.fetch_vehicle()  # ✅ 선택된 직원의 차량 정보 조회

            # ✅ 오른쪽 패널 업데이트 (현재 연도/월 기준)
            now = datetime.now()
            self.right_panel.update_data_from_db(selected_emp["id"], now.year, now.month)
            self.right_panel.update_calendar_title_1(now.year,now.month)

    def do_search(self, keyword):
        global global_token
        employees = api_fetch_employees_(global_token, keyword)
        
        # 만약 API가 단일 dict로 줄 수도 있고, list로 줄 수도 있으니 처리
        if isinstance(employees, dict):
            employees = [employees]

        if not isinstance(employees, list) or len(employees) == 0:
            self.left_panel.display_employee(None)
            QMessageBox.information(self, "검색 결과", "검색 결과가 없습니다.")
            return

        # 부분일치 필터
        filtered_employees = [
            emp for emp in employees
            if keyword.lower() in emp.get("name", "").lower()
        ]

        if not filtered_employees:
            self.left_panel.display_employee(None)
            QMessageBox.information(self, "검색 결과", "검색 결과가 없습니다.")
        elif len(filtered_employees) == 1:
            selected_emp = filtered_employees[0]
            self.left_panel.display_employee(selected_emp)
            # ✅ 선택된 직원의 차량 정보 조회
            self.left_panel.fetch_vehicle()    
            # 🟢 오른쪽 패널 업데이트 (연도/월은 현재 시점 사용)
            now = datetime.now()
            self.right_panel.update_data_from_db(selected_emp["id"], now.year, now.month)

        else:
            # 여러 건이면 선택창
            dialog = EmployeeSelectionDialog(filtered_employees, parent=self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_employee:
                selected_emp = dialog.selected_employee
                self.left_panel.display_employee(selected_emp)
                # ✅ 선택된 직원의 차량 정보 조회
                self.left_panel.fetch_vehicle()     
                # 🟢 동일하게 오른쪽 패널 업데이트
                now = datetime.now()
                self.right_panel.update_data_from_db(selected_emp["id"], now.year, now.month)
        self.employee_id = selected_emp["id"]
        self.right_panel.update_calendar_title_1(now.year,now.month)

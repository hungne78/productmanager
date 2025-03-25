from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel, QInputDialog,QVBoxLayout, QListWidget, QDialog, QGroupBox, QDateEdit, QPushButton
import sys
import os
import requests
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from datetime import datetime
import json
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtGui import QFont
# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from services.api_services import api_fetch_employees_, api_create_employee, api_update_employee, api_delete_employee, \
    api_fetch_vehicle, get_auth_headers, api_create_vehicle, api_fetch_employee_vehicle_info
from baselefttabwidget import BaseLeftTableWidget

global_token = get_auth_headers  # 로그인 토큰 (Bearer 인증)
BASE_URL = "http://127.0.0.1:8000"  # 실제 서버 URL

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

    """
    - QVBoxLayout으로 4개 QGroupBox (세로)
    - 1) 월별 매출, 2) 월별 방문, 3) 이번달 일별 매출(2줄), 4) 당일 방문정보
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        # 1) box1
        self.box1 = QGroupBox("월별 매출")
        self.tbl_box1 = QTableWidget(2, 12)  # 2행 12열
        # box1 (월별 매출)에서,
        # - 열 헤더가 "1월"~"12월"
        # - row=0 (첫 행)에 매출값을 쓰고 싶다.
        self.tbl_box1.setRowCount(1)          # 1행
        self.tbl_box1.setColumnCount(12)      # 12열
        self.tbl_box1.setHorizontalHeaderLabels([
            "1월","2월","3월","4월","5월","6월",
            "7월","8월","9월","10월","11월","12월"
        ])


        self.tbl_box1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box1.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tbl_box1.setHorizontalHeaderLabels([""]*12)
        box1_layout = QVBoxLayout()
        box1_layout.addWidget(self.tbl_box1)
        self.box1.setLayout(box1_layout)
        main_layout.addWidget(self.box1)

        # 2) box2
        self.box2 = QGroupBox("월별 방문횟수")
        self.tbl_box2 = QTableWidget(2, 12)
        # box1 (월별 매출)에서,
        # - 열 헤더가 "1월"~"12월"
        # - row=0 (첫 행)에 매출값을 쓰고 싶다.
        self.tbl_box2.setRowCount(1)          # 1행
        self.tbl_box2.setColumnCount(12)      # 12열
        self.tbl_box2.setHorizontalHeaderLabels([
            "1월","2월","3월","4월","5월","6월",
            "7월","8월","9월","10월","11월","12월"
        ])

       
        self.tbl_box2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box2.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        box2_layout = QVBoxLayout()
        box2_layout.addWidget(self.tbl_box2)
        self.box2.setLayout(box2_layout)
        main_layout.addWidget(self.box2)

       
        self.box3 = QGroupBox("일별 매출")
        v = QVBoxLayout()


        self.tbl_box3_top = QTableWidget(2, 15)  # 1~15일
        self.tbl_box3_top.setRowCount(1)          # 1행
        self.tbl_box3_top.setColumnCount(15)      # 12열
        self.tbl_box3_top.setHorizontalHeaderLabels([
            "1일","2일","3일","4일","5일","6일",
            "7일","8일","9일","10일","11일","12일","13일","14일","15일"
        ])

        self.tbl_box3_top.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box3_top.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tbl_box3_top.setHorizontalHeaderLabels([""]*15)

        self.tbl_box3_bottom = QTableWidget(2, 16)  # 16~31일
        self.tbl_box3_bottom.setRowCount(1)          # 1행
        self.tbl_box3_bottom.setColumnCount(16)      # 12열
        self.tbl_box3_bottom.setHorizontalHeaderLabels([
            "16일","17일","18일","19일","20일","21일",
            "22일","23일","24일","25일","26일","27일","28일","29일","30일","31일"
        ])
        self.tbl_box3_bottom.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box3_bottom.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tbl_box3_bottom.setHorizontalHeaderLabels([""]*16)

        v.addWidget(self.tbl_box3_top)
        v.addWidget(self.tbl_box3_bottom)
        self.box3.setLayout(v)
        main_layout.addWidget(self.box3)

        # 4) box4
        self.box4 = QGroupBox("당일 방문 거래처 정보")
        box4_layout = QVBoxLayout()
        self.tbl_box4_main = QTableWidget(10, 5)
        self.tbl_box4_main.setRowCount(50)  # 원하는 만큼
        self.tbl_box4_main.setColumnCount(5)
        self.tbl_box4_main.setHorizontalHeaderLabels(["거래처","오늘 매출","미수금","방문시간","기타"])
        self.tbl_box4_main.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box4_main.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        box4_layout.addWidget(self.tbl_box4_main)
        
        self.tbl_box4_footer = QTableWidget()
        self.tbl_box4_footer.setRowCount(1)
        self.tbl_box4_footer.setColumnCount(5)
        # 헤더 감추기 (가로/세로 둘 다)
        self.tbl_box4_footer.horizontalHeader().setVisible(False)
        # self.tbl_box4_footer.verticalHeader().setVisible(False)
        self.tbl_box4_footer.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # 가로 스크롤은 필요하지만, 세로 스크롤은 필요없음
        self.tbl_box4_footer.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 푸터 테이블 높이 제한 (1행이므로 크게 필요없음)
        self.tbl_box4_footer.setFixedHeight(35)  # 원하는 높이로 조절. 예: 35px
        # 또는 self.tbl_box4_footer.setRowHeight(0, 30) 등으로 높이를 조절 가능

        # 헤더도 보이게 할 수 있지만, 합계 행만 있으므로 세로헤더는 안 보이게
        self.tbl_box4_footer.verticalHeader().setVisible(False)
        box4_layout.addWidget(self.tbl_box4_footer)
        # 메인테이블 스크롤 동기화
        self.tbl_box4_main.horizontalScrollBar().valueChanged.connect(
            self.tbl_box4_footer.horizontalScrollBar().setValue
        )
        item = QTableWidgetItem("합계")
        # item.setBackground(QColor("#333333"))
        # item.setForeground(QColor("white"))
        self.tbl_box4_footer.setItem(0, 0, item)
        # box4_layout = QVBoxLayout()
        # box4_layout.addWidget(self.tbl_box4)
        self.box4.setLayout(box4_layout)
        main_layout.addWidget(self.box4)

        main_layout.setStretchFactor(self.box1, 1)
        main_layout.setStretchFactor(self.box2, 1)
        main_layout.setStretchFactor(self.box3, 3)
        main_layout.setStretchFactor(self.box4, 10)
        
        self.setLayout(main_layout)

    def update_data_from_db(self, employee_id: int, year: int, month: int):
        """
        실제 DB에서 월별 매출, 월별 방문, 일별 매출, 일별 방문 기록을 가져와서
        각각 box1, box2, box3, box4 테이블에 채워넣는다.
        """
        global global_token
        if not global_token:
            # 로그인 토큰 없으면 그냥 종료(실제 앱에선 안내창 띄우면 됨)
            return

        headers = {"Authorization": f"Bearer {global_token}"}

        # 1) 월별 매출
        url_monthly_sales = f"{BASE_URL}/sales/monthly_sales_pc/{employee_id}/{year}"
        try:
            resp = requests.get(url_monthly_sales, headers=headers)
            resp.raise_for_status()
            monthly_sales = resp.json()  # 길이 12의 리스트
        except:
            monthly_sales = [0]*12
        for c in range(12):
            # monthly_sales[c] 값 → row=0, col=c 셀에 표시
            self.tbl_box1.setItem(0, c, QTableWidgetItem(str(monthly_sales[c])))
        # 2) 월별 방문
        url_monthly_visits = f"{BASE_URL}/client_visits/monthly_visits/{employee_id}/{year}"
        try:
            resp = requests.get(url_monthly_visits, headers=headers)
            resp.raise_for_status()
            monthly_visits = resp.json()  # 길이 12의 리스트
        except:
            monthly_visits = [0]*12
        # [BOX2] 월별 방문 테이블 채우기
        # self.tbl_box2 역시 1행 12열
        for c in range(12):
            self.tbl_box2.setItem(0, c, QTableWidgetItem(str(monthly_visits[c])))


        # 3) 일별 매출 (해당 월)
        url_daily_sales = f"{BASE_URL}/sales/daily_sales_pc/{employee_id}/{year}/{month}"
        try:
            resp = requests.get(url_daily_sales, headers=headers)
            resp.raise_for_status()
            daily_sales = resp.json()  # 길이 31(최대)의 리스트
        except:
            daily_sales = [0]*31

       
        for day_index in range(15):  # 0~14
            val = daily_sales[day_index]   # day_index=0 → 1일, 1 → 2일 ...
            self.tbl_box3_top.setItem(0, day_index, QTableWidgetItem(str(val)))

       
        for day_index in range(15, 31):  # 15~30
            val = daily_sales[day_index]
            # 아래 테이블에서는 col=day_index-15
            self.tbl_box3_bottom.setItem(0, day_index - 15, QTableWidgetItem(str(val)))
        # -----------------------------
        # (4) 당일 방문 + 미수금 + 오늘 매출 (box4)
        # -----------------------------
        
        url_today_visits = f"{BASE_URL}/client_visits/today_visits_details?employee_id={employee_id}"

        try:
            resp = requests.get(url_today_visits, headers=headers)
            resp.raise_for_status()
            visits_data = resp.json()
            print(f"📌 오늘 방문 데이터: {visits_data}")  # ✅ API 응답 확인 로그 추가
        except Exception as e:
            print("🚨 오늘 방문 데이터 조회 오류:", e)
            visits_data = []

        # ✅ 기본 행 개수를 유지 (예: 50개)
        default_row_count = max(50, len(visits_data) + 1)
        self.tbl_box4_main.setRowCount(default_row_count)

        # ✅ 총 매출 및 미수금 계산
        total_today_sales = sum(item.get("today_sales", 0) for item in visits_data)
        total_outstanding = sum(item.get("outstanding_amount", 0) for item in visits_data)

        # 🔹 **기존 테이블 유지하며, 방문 데이터만 갱신**
        for row_index in range(default_row_count - 1):
            if row_index < len(visits_data):
                info = visits_data[row_index]
                client_name = str(info.get("client_name", "N/A"))
                today_sales = str(f"{info.get('today_sales', 0):,} 원")  # ✅ 천 단위 콤마 추가
                outstanding = str(f"{info.get('outstanding_amount', 0):,} 원")
                visit_time = str(info.get("visit_datetime", ""))
                visit_count = str(info.get("visit_count", 1))  # ✅ 방문 횟수 추가

                self.tbl_box4_main.setItem(row_index, 0, QTableWidgetItem(client_name))
                self.tbl_box4_main.setItem(row_index, 1, QTableWidgetItem(today_sales))
                self.tbl_box4_main.setItem(row_index, 2, QTableWidgetItem(outstanding))
                self.tbl_box4_main.setItem(row_index, 3, QTableWidgetItem(visit_time))
                self.tbl_box4_main.setItem(row_index, 4, QTableWidgetItem(visit_count))  # ✅ 방문 횟수 추가
            else:
                # ✅ 데이터가 없는 행은 빈 값으로 유지
                self.tbl_box4_main.setItem(row_index, 0, QTableWidgetItem(""))
                self.tbl_box4_main.setItem(row_index, 1, QTableWidgetItem(""))
                self.tbl_box4_main.setItem(row_index, 2, QTableWidgetItem(""))
                self.tbl_box4_main.setItem(row_index, 3, QTableWidgetItem(""))
                self.tbl_box4_main.setItem(row_index, 4, QTableWidgetItem(""))

        # 🔹 **합계 행 업데이트 (항상 마지막 행)**
        last_row_index = default_row_count - 1
        self.tbl_box4_main.setItem(last_row_index, 0, QTableWidgetItem("합계"))
        self.tbl_box4_main.setItem(last_row_index, 1, QTableWidgetItem(f"{total_today_sales:,} 원"))
        self.tbl_box4_main.setItem(last_row_index, 2, QTableWidgetItem(f"{total_outstanding:,} 원"))
        self.tbl_box4_main.setItem(last_row_index, 3, QTableWidgetItem(""))  # 방문시간 칸 비움
        self.tbl_box4_main.setItem(last_row_index, 4, QTableWidgetItem(""))  # 방문 횟수 칸 비움
        

class EmployeesTab(QWidget):
    """ 직원 관리 메인 탭 """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        
        self.setFont(QFont("Malgun Gothic", 15))  # 혹은 Windows/기본폰
        self.left_panel = EmployeeLeftWidget()
        self.right_panel = EmployeeRightPanel()

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


    def update_employee_ui(self, employee_id: int):
        """ 매출 발생 후 직원 데이터 업데이트 """
        now = datetime.now()
        year = now.year
        month = now.month
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
            self.left_panel.display_employee(selected_emp)
            self.left_panel.fetch_vehicle()  # ✅ 선택된 직원의 차량 정보 조회

            # ✅ 오른쪽 패널 업데이트 (현재 연도/월 기준)
            now = datetime.now()
            self.right_panel.update_data_from_db(selected_emp["id"], now.year, now.month)


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


    
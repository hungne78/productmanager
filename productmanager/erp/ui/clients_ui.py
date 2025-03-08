from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel, QDialog, QVBoxLayout, QListWidget, QGroupBox, QInputDialog
import sys
import os
from PyQt5.QtGui import QColor
# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_clients, api_create_client, api_update_client, api_delete_client, \
    api_assign_employee_client, api_fetch_employee_clients_all, get_auth_headers, api_fetch_lent_freezers, api_fetch_employees, api_unassign_employee_client
from baselefttabwidget import BaseLeftTableWidget
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy
import requests
from datetime import datetime
global_token = get_auth_headers

class LentDialog(QDialog):
    def __init__(self, lent_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("대여 냉동고 목록")
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["상표", "시리얼 번호", "년식"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.table)

        self.populate_table(lent_data)

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def populate_table(self, lent_data):
        self.table.setRowCount(len(lent_data))
        for i, record in enumerate(lent_data):
            self.table.setItem(i, 0, QTableWidgetItem(record.get("brand", "")))
            self.table.setItem(i, 1, QTableWidgetItem(record.get("serial_number", "")))
            self.table.setItem(i, 2, QTableWidgetItem(str(record.get("year", ""))))
            
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
        
        form_layout.addRow("거래처명:", self.name_edit)
        form_layout.addRow("대표자명:", self.representative_edit)
        form_layout.addRow("주소:", self.address_edit)
        form_layout.addRow("전화번호:", self.phone_edit)
        form_layout.addRow("미수금:", self.outstanding_edit)
        form_layout.addRow("일반가단단가:", self.regular_price__edit)
        form_layout.addRow("고정가단단가:", self.fixed_price_edit)
        form_layout.addRow("사업자번호:", self.business_edit)
        form_layout.addRow("이메일:", self.email_edit)

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
            self.address_edit.setText(client.get("address", ""))
            self.phone_edit.setText(client.get("phone", ""))
            self.outstanding_edit.setText(str(client.get("outstanding_amount", "0")))

            self.regular_price__edit.setText(str(client.get("unit_price", "0")))
            self.fixed_price_edit.setText(str(client.get("unit_price", "0")))

            self.business_edit.setText(client.get("business_number", ""))
            self.email_edit.setText(client.get("email", ""))
            
class ClientSelectionDialog(QDialog):
    def __init__(self, clients, parent=None):
        super().__init__(parent)
        self.setWindowTitle("검색 결과")
        self.resize(300, 400)
        self.clients = clients  # 거래처 목록 (dict 리스트)
        self.selected_client = None

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        
        # "ID - 거래처명" 형식으로 항목 추가
        for client in clients:
            display_text = f"{client.get('id')} - {client.get('client_name')}"
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
            self.selected_client = self.clients[index]
            self.accept()
        else:
            QMessageBox.warning(self, "선택", "거래처를 선택해주세요.")
            
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
            "메일주소"     # 7
        ]
        
        super().__init__(row_count=len(labels), labels=labels, parent=parent)
        
        # ✅ 현재 레이아웃을 가져옴 (None 방지)
        main_layout = self.layout()
        if main_layout is None:
            main_layout = QVBoxLayout()
            self.setLayout(main_layout)
            
        # ✅ 담당 직원 목록을 보여줄 테이블 추가
        self.assigned_employees_table = QTableWidget()
        self.assigned_employees_table.setColumnCount(1)
        self.assigned_employees_table.setHorizontalHeaderLabels(["담당 직원"])
        self.assigned_employees_table.horizontalHeader().setStretchLastSection(True)

        # ✅ "대여 냉동고" 버튼을 개별 레이아웃으로 추가
        btn_layout_top = QHBoxLayout()
        self.btn_lent = QPushButton("대여 냉동고")
        btn_layout_top.addWidget(self.btn_lent)

        # ✅ 기존 버튼 줄에 "삭제" 버튼 추가
        btn_layout_bottom = QHBoxLayout()
        self.btn_delete = QPushButton("삭제")
        self.btn_assign = QPushButton("담당 직원 배정")  # ✅ 담당 직원 배정 버튼 추가
        btn_layout_bottom.addWidget(self.btn_delete)
        btn_layout_bottom.addWidget(self.btn_assign)
        
        # ✅ 부모 클래스의 버튼 레이아웃이 있는지 확인하고 가져오기
        if main_layout.count() > 1 and main_layout.itemAt(1) is not None:
            btn_layout_bottom = main_layout.itemAt(1).layout()
        else:
            btn_layout_bottom = QHBoxLayout()
            main_layout.addLayout(btn_layout_bottom)

        # ✅ 기존 버튼 줄에 "삭제" 버튼 추가
        self.btn_delete = QPushButton("삭제")
         # ✅ "담당 직원 배정 해제" 버튼 추가
        self.btn_unassign = QPushButton("담당 직원 해제")
        btn_layout_bottom.addWidget(self.btn_delete)
        btn_layout_bottom.addWidget(self.btn_assign)
        # ✅ 버튼 레이아웃에 추가
        btn_layout_bottom.addWidget(self.btn_unassign)      
       
        # ✅ "대여 냉동고" 버튼을 최상단에 추가
        main_layout.insertLayout(0, btn_layout_top)

        # ✅ 담당 직원 목록 추가
        main_layout.addWidget(QLabel("담당 직원 목록"))
        main_layout.addWidget(self.assigned_employees_table)

        # ✅ 버튼 레이아웃 추가
        main_layout.addLayout(btn_layout_bottom)
        
        # ✅ 버튼 이벤트 연결
        self.btn_lent.clicked.connect(self.show_lent_freezers)
        self.btn_new.clicked.connect(self.create_client)
        self.btn_edit.clicked.connect(self.update_client)
        self.btn_delete.clicked.connect(self.delete_client)
        self.btn_assign.clicked.connect(self.assign_employee)
        
        self.btn_unassign.clicked.connect(self.unassign_employee)
        
        
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
        dialog = LentDialog(lent_data, self)
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
        # ✅ 거래처 ID가 있을 경우 담당 직원 목록을 불러옴
        client_id = client.get("id")
        if client_id:
            print(f"🚀 거래처 ID {client_id}의 담당 직원 목록을 불러옵니다.")
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
            "address": self.get_value(2),
            "phone": self.get_value(3),
            "outstanding_amount": self.get_value(4),
            "regular_price": self.get_value(5),
            "fixed_price": self.get_value(6),
            "business_number": self.get_value(7),
            "email": self.get_value(8),
        }
        
        dialog = ClientDialog("거래처 수정", client=current_client)
        if dialog.exec_() == QDialog.Accepted:
            data = {
                "client_name": dialog.name_edit.text(),
                "address": dialog.address_edit.text(),
                "phone": dialog.phone_edit.text(),
                "outstanding_amount": float(dialog.outstanding_edit.text() or 0),
                "regular_price": float(dialog.regular_price__edit.text() or 35),
                "fixed_price": float(dialog.fixed_price_edit.text() or 70),
                "business_number": dialog.business_edit.text(),
                "email": dialog.email_edit.text(),
            }
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
        # 1) box1
        self.box1 = QGroupBox("해당거래처 월별 매출")
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

        # 그다음에 update_data_example 등에서 데이터 넣기:
        # sales_data = [100,200,300,400,500,600,700,800,900,1000,1100,1200]
        # for c in range(12):
        #     # row=0, col=c 위치에 매출값 쓰기
        #     self.tbl_box1.setItem(0, c, QTableWidgetItem(str(sales_data[c])))

        self.tbl_box1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box1.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tbl_box1.setHorizontalHeaderLabels([""]*12)
        box1_layout = QVBoxLayout()
        box1_layout.addWidget(self.tbl_box1)
        self.box1.setLayout(box1_layout)
        main_layout.addWidget(self.box1)

        # 2) box2
        self.box2 = QGroupBox("해당거래처 영업사원 방문횟수")
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

        # 그다음에 update_data_example 등에서 데이터 넣기:
        # sales_data = [100,200,300,400,500,600,700,800,900,1000,1100,1200]
        # for c in range(12):
        #     # row=0, col=c 위치에 매출값 쓰기
        #     self.tbl_box2.setItem(0, c, QTableWidgetItem(str(sales_data[c])))
        self.tbl_box2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_box2.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        box2_layout = QVBoxLayout()
        box2_layout.addWidget(self.tbl_box2)
        self.box2.setLayout(box2_layout)
        main_layout.addWidget(self.box2)

        # 3) box3: 이번달 일별 매출 (2줄)
        #    - 첫 번째 테이블: 1~15일
        #    - 두 번째 테이블: 16~31일
        self.box3 = QGroupBox("이번달 일별 매출")
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
        self.box4 = QGroupBox("당일 분류별 판매내용용")
        box4_layout = QVBoxLayout()
        self.tbl_box4_main = QTableWidget(10, 5)
        self.tbl_box4_main.setRowCount(50)  # 원하는 만큼
        self.tbl_box4_main.setColumnCount(5)
        self.tbl_box4_main.setHorizontalHeaderLabels(["분류","판매금액","수량","직원","기타"])
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
        item.setBackground(QColor("#333333"))
        item.setForeground(QColor("white"))
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
        base_url = "http://127.0.0.1:8000"  # 서버 주소 (환경에 맞춰 수정)

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
        url_daily = f"{base_url}/sales/daily_sales_client/{client_id}/{year}/{month}"
        try:
            resp = requests.get(url_daily, headers=headers)
            resp.raise_for_status()
            daily_sales = resp.json()  # 최대 길이 31
        except Exception as e:
            print(f"❌ 일별 매출 조회 실패: {e}")
            daily_sales = [0]*31

        # 상단(1~15일)
        for i in range(15):
            self.tbl_box3_top.setItem(0, i, QTableWidgetItem(str(daily_sales[i])))

        # 하단(16~31일)
        for i in range(15, 31):
            col_index = i - 15
            self.tbl_box3_bottom.setItem(0, col_index, QTableWidgetItem(str(daily_sales[i])))

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
                self.left_panel.display_client(dialog.selected_client)
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
                self.left_panel.display_client(dialog.selected_client)

                # 동일하게 오른쪽 패널도 갱신
                cid = dialog.selected_client["id"]
                self.right_panel.update_data_for_client(cid)
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QMessageBox, QFormLayout, QLineEdit, QLabel
import sys
import os

# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_clients, api_create_client, api_update_client, api_delete_client, \
    api_assign_employee_client, api_fetch_employee_clients_all


class ClientLeftPanel(QWidget):
    """ 거래처 상세 정보 및 담당 직원 배정 기능 추가 """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.id_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.outstanding_edit = QLineEdit()
        
        # 담당 직원 목록을 보여줄 테이블
        self.assigned_employees_table = QTableWidget()
        self.assigned_employees_table.setColumnCount(1)
        self.assigned_employees_table.setHorizontalHeaderLabels(["담당 직원"])
        self.assigned_employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        form_layout.addRow("ID:", self.id_edit)
        form_layout.addRow("거래처명:", self.name_edit)
        form_layout.addRow("주소:", self.address_edit)
        form_layout.addRow("전화번호:", self.phone_edit)
        form_layout.addRow("미수금:", self.outstanding_edit)
        form_layout.addRow("담당 직원:", self.assigned_employees_table)

        self.id_edit.setReadOnly(True)  # ID는 수정 불가

        layout.addLayout(form_layout)

        self.btn_add = QPushButton("신규 등록")
        self.btn_edit = QPushButton("수정")
        self.btn_delete = QPushButton("삭제")
        self.btn_assign = QPushButton("담당 직원 배정")

        layout.addWidget(self.btn_add)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_delete)
        layout.addWidget(self.btn_assign)

        self.btn_add.clicked.connect(self.add_client)
        self.btn_edit.clicked.connect(self.edit_client)
        self.btn_delete.clicked.connect(self.delete_client)
        self.btn_assign.clicked.connect(self.assign_employee)

        self.setLayout(layout)

    def display_client(self, client):
        """ 검색된 거래처 정보를 왼쪽 패널에 표시 """
        self.id_edit.setText(str(client.get("id", "")))
        self.name_edit.setText(client.get("client_name", ""))
        self.address_edit.setText(client.get("address", ""))
        self.phone_edit.setText(client.get("phone", ""))
        self.outstanding_edit.setText(str(client.get("outstanding_amount", 0)))

        # 현재 거래처의 담당 직원 목록 업데이트
        self.load_assigned_employees(client.get("id"))

    def load_assigned_employees(self, client_id):
        """ 현재 거래처의 담당 직원 목록을 가져와 테이블에 표시 """
        employees = api_fetch_employee_clients_all()
        assigned_employees = [e for e in employees if e["client_id"] == client_id]

        self.assigned_employees_table.setRowCount(0)
        for emp in assigned_employees:
            row = self.assigned_employees_table.rowCount()
            self.assigned_employees_table.insertRow(row)
            self.assigned_employees_table.setItem(row, 0, QTableWidgetItem(emp.get("employee_name", "N/A")))

    def assign_employee(self):
        """ 직원 ID를 입력받아 거래처와 연결 """
        client_id = self.id_edit.text().strip()
        if not client_id:
            QMessageBox.warning(self, "경고", "담당 직원을 배정할 거래처를 선택하세요.")
            return

        emp_id, ok = QInputDialog.getInt(self, "담당 직원 배정", "직원 ID를 입력하세요:")
        if not ok:
            return

        response = api_assign_employee_client(client_id, emp_id)
        if response and response.status_code == 200:
            # 담당 직원 정보 업데이트
            emp_name = response.json().get("employee_name", "N/A")
            client_name = self.name_edit.text().strip()
            QMessageBox.information(self, "성공", f'"{client_name}"이(가) "{emp_name}"으로 배정되었습니다.')
            self.load_assigned_employees(client_id)

    def add_client(self):
        name = self.name_edit.text().strip()
        address = self.address_edit.text().strip()
        phone = self.phone_edit.text().strip()
        outstanding = self.outstanding_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "경고", "거래처명을 입력하세요.")
            return

        data = {"client_name": name, "address": address, "phone": phone, "outstanding_amount": float(outstanding or 0)}
        response = api_create_client(data)
        if response and response.status_code in [200, 201]:
            QMessageBox.information(self, "성공", "거래처가 추가되었습니다.")

    def edit_client(self):
        client_id = self.id_edit.text().strip()
        name = self.name_edit.text().strip()
        address = self.address_edit.text().strip()
        phone = self.phone_edit.text().strip()
        outstanding = self.outstanding_edit.text().strip()

        if not client_id:
            QMessageBox.warning(self, "경고", "수정할 거래처를 선택하세요.")
            return

        data = {"client_name": name, "address": address, "phone": phone, "outstanding_amount": float(outstanding or 0)}
        response = api_update_client(client_id, data)
        if response and response.status_code == 200:
            QMessageBox.information(self, "성공", "거래처 정보가 수정되었습니다.")

    def delete_client(self):
        client_id = self.id_edit.text().strip()
        if not client_id:
            QMessageBox.warning(self, "경고", "삭제할 거래처를 선택하세요.")
            return

        confirm = QMessageBox.question(self, "삭제 확인", f"정말 거래처 ID {client_id}를 삭제하시겠습니까?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            response = api_delete_client(client_id)
            if response and response.status_code == 200:
                QMessageBox.information(self, "성공", "거래처가 삭제되었습니다.")


class ClientRightPanel(QWidget):
    """ 거래처의 매출 및 방문 정보 (오른쪽 패널) """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(2)
        self.sales_table.setHorizontalHeaderLabels(["월", "매출"])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.visit_table = QTableWidget()
        self.visit_table.setColumnCount(2)
        self.visit_table.setHorizontalHeaderLabels(["월", "방문 횟수"])
        self.visit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(QLabel("월별 매출"))
        layout.addWidget(self.sales_table)
        layout.addWidget(QLabel("월별 방문 횟수"))
        layout.addWidget(self.visit_table)

        self.setLayout(layout)

    def update_sales_data(self, sales_data):
        """ 거래처별 월별 매출 데이터 표시 """
        self.sales_table.setRowCount(0)
        for month, amount in sales_data.items():
            row = self.sales_table.rowCount()
            self.sales_table.insertRow(row)
            self.sales_table.setItem(row, 0, QTableWidgetItem(month))
            self.sales_table.setItem(row, 1, QTableWidgetItem(str(amount)))

    def update_visit_data(self, visit_data):
        """ 거래처별 월별 방문 횟수 표시 """
        self.visit_table.setRowCount(0)
        for month, visits in visit_data.items():
            row = self.visit_table.rowCount()
            self.visit_table.insertRow(row)
            self.visit_table.setItem(row, 0, QTableWidgetItem(month))
            self.visit_table.setItem(row, 1, QTableWidgetItem(str(visits)))


class ClientsTab(QWidget):
    """ 거래처 관리 메인 탭 """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.left_panel = ClientLeftPanel()
        self.right_panel = ClientRightPanel()

        main_layout.addWidget(self.left_panel, 2)  # 거래처 정보 (좌)
        main_layout.addWidget(self.right_panel, 3)  # 매출 및 방문 (우)

        self.setLayout(main_layout)

        self.load_clients()

    def load_clients(self):
        """ 거래처 목록을 가져와 테이블에 로드 """
        clients = api_fetch_clients()
        if clients:
            first_client = clients[0]
            self.left_panel.display_client(first_client)

            # 테스트용 데이터
            sample_sales_data = {"1월": 6000, "2월": 7500, "3월": 9200}
            sample_visit_data = {"1월": 8, "2월": 12, "3월": 18}
            self.right_panel.update_sales_data(sample_sales_data)
            self.right_panel.update_visit_data(sample_visit_data)

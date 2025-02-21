#!/usr/bin/env python
import sys
import json
import requests
from datetime import datetime, date
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QMessageBox, QDateEdit, QComboBox, QSpinBox, QGroupBox, QHeaderView, QInputDialog
)
from PyQt5.QtCore import Qt, QDate

# ----------------------------
# Global Variables and API Base
# ----------------------------
BASE_URL = "http://127.0.0.1:8000"
global_token = None

# ----------------------------
# API Service Functions
# ----------------------------
def api_login(employee_id, password):
    url = f"{BASE_URL}/login"
    data = {"id": employee_id, "password": password}
    headers = {"Content-Type": "application/json"}
    return requests.post(url, json=data, headers=headers)

def api_fetch_orders(token):
    # 서버에 전체 주문 데이터를 가져오는 엔드포인트 (/orders)
    url = f"{BASE_URL}/orders"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers)

# ----------------------------
# Login Dialog
# ----------------------------
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("로그인")
        self.setFixedSize(300, 150)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("사원 ID (예: 1)")
        form_layout.addRow("사원 ID:", self.id_edit)
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("비밀번호")
        self.password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("비밀번호:", self.password_edit)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.login_btn = QPushButton("로그인")
        self.login_btn.clicked.connect(self.attempt_login)
        btn_layout.addWidget(self.login_btn)
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def attempt_login(self):
        id_text = self.id_edit.text().strip()
        password = self.password_edit.text().strip()
        if not id_text or not password:
            QMessageBox.warning(self, "경고", "사원 ID와 비밀번호를 입력하세요.")
            return
        try:
            employee_id = int(id_text)
        except ValueError:
            QMessageBox.warning(self, "경고", "사원 ID는 정수로 입력하세요.")
            return
        # 관리 프로그램은 여러 직원의 데이터를 봐야 하므로 제한 없이 모든 직원 데이터를 허용할 수 있음.
        # (예시에서는 테스트 목적으로 ID 1만 허용하도록 제한했다면, 여기서는 제한을 풀거나 관리권한을 가진 계정으로 로그인하게 할 수 있습니다.)
        # 아래는 제한 없이 진행하는 예시:
        try:
            response = api_login(employee_id, password)
            if response.status_code == 200:
                data = response.json()
                if "token" not in data:
                    QMessageBox.critical(self, "오류", "로그인 응답에 token이 없습니다.")
                    return
                global global_token
                global_token = data["token"]
                QMessageBox.information(self, "성공", "로그인 성공!")
                self.accept()
            else:
                QMessageBox.critical(self, "로그인 실패", f"로그인 실패: {response.status_code}\n{response.text}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"로그인 중 오류 발생: {e}")

# ----------------------------
# Orders Management Tab
# ----------------------------
class OrdersManagementTab(QWidget):
    """
    이 탭은 전체 주문 데이터를 불러와서,
    - 선택한 날짜의 주문들로 당일 매출을 계산하고,
    - 특정 직원별 주문 내역과 매출도 집계하여 보여줍니다.
    집계는 클라이언트 측(Python)에서 수행합니다.
    """
    def __init__(self, token, parent=None):
        super().__init__(parent)
        self.token = token
        self.all_orders = []  # 전체 주문 데이터를 저장
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # 주문 데이터 새로고침 버튼
        refresh_btn = QPushButton("전체 주문 데이터 새로고침")
        refresh_btn.clicked.connect(self.fetch_all_orders)
        main_layout.addWidget(refresh_btn)

        # 날짜 선택 및 당일 매출 계산
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("날짜 선택:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_edit)
        calc_btn = QPushButton("당일 매출 계산")
        calc_btn.clicked.connect(self.calculate_daily_sales)
        date_layout.addWidget(calc_btn)
        main_layout.addLayout(date_layout)

        self.daily_sales_label = QLabel("당일 매출: 0 원")
        self.daily_sales_label.setAlignment(Qt.AlignCenter)
        self.daily_sales_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(self.daily_sales_label)

        # 직원 필터를 위한 콤보박스 (전체 직원 + 개별 직원)
        emp_layout = QHBoxLayout()
        emp_layout.addWidget(QLabel("직원 ID (전체는 비워둠):"))
        self.emp_filter_edit = QLineEdit()
        emp_layout.addWidget(self.emp_filter_edit)
        filter_btn = QPushButton("직원별 매출 계산")
        filter_btn.clicked.connect(self.calculate_employee_sales)
        emp_layout.addWidget(filter_btn)
        main_layout.addLayout(emp_layout)

        self.emp_sales_label = QLabel("선택한 직원 매출: 0 원")
        self.emp_sales_label.setAlignment(Qt.AlignCenter)
        self.emp_sales_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(self.emp_sales_label)

        # 주문 내역 테이블
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Client ID", "Employee ID", "주문일자", "총액", "상태"])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.orders_table)

        self.setLayout(main_layout)

    def fetch_all_orders(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.get(f"{BASE_URL}/orders", headers=headers)
            response.raise_for_status()
            self.all_orders = response.json()  # 전체 주문 리스트
            QMessageBox.information(self, "성공", "전체 주문 데이터를 새로고침했습니다.")
            self.populate_orders_table(self.all_orders)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"주문 데이터 가져오기 오류: {e}")

    def populate_orders_table(self, orders):
        self.orders_table.setRowCount(0)
        for order in orders:
            row = self.orders_table.rowCount()
            self.orders_table.insertRow(row)
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(order.get("id"))))
            self.orders_table.setItem(row, 1, QTableWidgetItem(str(order.get("client_id"))))
            self.orders_table.setItem(row, 2, QTableWidgetItem(str(order.get("employee_id"))))
            self.orders_table.setItem(row, 3, QTableWidgetItem(order.get("order_date", "")))
            self.orders_table.setItem(row, 4, QTableWidgetItem(str(order.get("total_amount"))))
            self.orders_table.setItem(row, 5, QTableWidgetItem(order.get("status", "")))

    def calculate_daily_sales(self):
        selected_date = self.date_edit.date().toString("yyyy-MM-dd")
        # 필터: 주문의 order_date가 선택한 날짜와 일치하는 주문만 추출
        daily_orders = [order for order in self.all_orders if order.get("order_date", "").startswith(selected_date)]
        total_sales = sum(float(order.get("total_amount") or 0) for order in daily_orders)
        self.daily_sales_label.setText(f"당일 매출: {total_sales} 원")

    def calculate_employee_sales(self):
        emp_filter = self.emp_filter_edit.text().strip()
        if not emp_filter:
            QMessageBox.warning(self, "경고", "직원 ID를 입력하세요 (전체 매출을 보려면 공백으로 두세요).")
            return
        try:
            emp_id = int(emp_filter)
        except ValueError:
            QMessageBox.warning(self, "경고", "직원 ID는 정수로 입력하세요.")
            return
        # 선택한 직원의 주문만 필터링
        emp_orders = [order for order in self.all_orders if order.get("employee_id") == emp_id]
        total_sales = sum(float(order.get("total_amount") or 0) for order in emp_orders)
        self.emp_sales_label.setText(f"직원 {emp_id} 매출: {total_sales} 원")

# ----------------------------
# Salary Calculation Tab (월별 월급 계산)
# ----------------------------
class SalaryCalculationTab(QWidget):
    """
    선택한 월에 대해 각 직원의 주문(발주) 데이터를 기반으로,
    월매출과 월별 인센티브의 합을 계산하여, 
    각 직원의 월급(월매출×커미션율 + 인센티브 합)을 계산합니다.
    직원별 커미션율은 Employee 데이터에 저장되어 있다고 가정합니다.
    """
    def __init__(self, token, parent=None):
        super().__init__(parent)
        self.token = token
        self.all_orders = []  # 전체 주문 데이터를 저장 (월별 필터링에 사용)
        self.all_employees = []  # 전체 직원 데이터를 저장
        self.init_ui()
        self.fetch_all_orders()
        self.fetch_all_employees()

    def init_ui(self):
        main_layout = QVBoxLayout()
        # 월 선택을 위한 QDateEdit (월만 선택)
        month_layout = QHBoxLayout()
        month_layout.addWidget(QLabel("월 선택 (YYYY-MM):"))
        self.month_edit = QDateEdit()
        self.month_edit.setCalendarPopup(True)
        self.month_edit.setDisplayFormat("yyyy-MM")
        self.month_edit.setDate(QDate.currentDate())
        month_layout.addWidget(self.month_edit)
        calc_btn = QPushButton("월급 계산")
        calc_btn.clicked.connect(self.calculate_salary)
        month_layout.addWidget(calc_btn)
        main_layout.addLayout(month_layout)

        # 결과를 보여줄 테이블: 직원 ID, 이름, 월매출, 월별 인센티브, 커미션율, 계산된 월급
        self.salary_table = QTableWidget()
        self.salary_table.setColumnCount(6)
        self.salary_table.setHorizontalHeaderLabels(["직원 ID", "이름", "월매출", "월별 인센티브", "커미션율(%)", "월급"])
        self.salary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.salary_table)

        self.setLayout(main_layout)

    def fetch_all_orders(self):
        try:
            response = api_fetch_orders(self.token)
            response.raise_for_status()
            self.all_orders = response.json()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"전체 주문 데이터 조회 오류: {e}")

    def fetch_all_employees(self):
        try:
            response = api_fetch_employees(self.token)
            response.raise_for_status()
            self.all_employees = response.json()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"직원 데이터 조회 오류: {e}")

    def calculate_salary(self):
        # 선택한 월 가져오기: "YYYY-MM"
        selected_month = self.month_edit.date().toString("yyyy-MM")
        # 직원별로 월별 매출과 인센티브 합계를 집계
        results = []  # 각 결과: (emp_id, name, monthly_sales, monthly_incentives, commission_rate, salary)
        for emp in self.all_employees:
            emp_id = emp.get("id")
            name = emp.get("name")
            commission_rate = float(emp.get("commission_rate") or 0)
            # 해당 직원의 해당 월 주문 필터링
            emp_orders = [order for order in self.all_orders if order.get("employee_id") == emp_id and order.get("order_date", "").startswith(selected_month)]
            monthly_sales = sum(float(order.get("total_amount") or 0) for order in emp_orders)
            monthly_incentives = 0
            for order in emp_orders:
                items = order.get("order_items", [])
                for item in items:
                    monthly_incentives += float(item.get("incentive") or 0)
            salary = (monthly_sales * (commission_rate / 100)) + monthly_incentives
            results.append((emp_id, name, monthly_sales, monthly_incentives, commission_rate, salary))
        # 결과를 테이블에 표시
        self.salary_table.setRowCount(0)
        for res in results:
            row = self.salary_table.rowCount()
            self.salary_table.insertRow(row)
            self.salary_table.setItem(row, 0, QTableWidgetItem(str(res[0])))
            self.salary_table.setItem(row, 1, QTableWidgetItem(str(res[1])))
            self.salary_table.setItem(row, 2, QTableWidgetItem(str(res[2])))
            self.salary_table.setItem(row, 3, QTableWidgetItem(str(res[3])))
            self.salary_table.setItem(row, 4, QTableWidgetItem(str(res[4])))
            self.salary_table.setItem(row, 5, QTableWidgetItem(str(res[5])))


# --- Employee Vehicle Tab ---
class EmployeeVehicleTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # 조회 부분: 직원 ID 입력 후 조회 버튼
        search_group = QGroupBox("직원 차량 관리 조회")
        search_layout = QFormLayout()
        self.emp_id_search_edit = QLineEdit()
        search_layout.addRow("Employee ID:", self.emp_id_search_edit)
        self.search_btn = QPushButton("조회")
        self.search_btn.clicked.connect(self.fetch_vehicle)
        search_layout.addRow(self.search_btn)
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)
        
        # 정보 입력 및 수정 부분
        info_group = QGroupBox("직원 차량 관리 정보")
        info_layout = QFormLayout()
        self.emp_id_edit = QLineEdit()
        info_layout.addRow("Employee ID:", self.emp_id_edit)
        self.monthly_fuel_edit = QLineEdit()
        info_layout.addRow("1달 주유비:", self.monthly_fuel_edit)
        self.current_mileage_edit = QLineEdit()
        info_layout.addRow("현재 주행거리:", self.current_mileage_edit)
        self.oil_change_date_edit = QDateEdit()
        self.oil_change_date_edit.setCalendarPopup(True)
        self.oil_change_date_edit.setDate(QDate.currentDate())
        info_layout.addRow("엔진오일 교체일:", self.oil_change_date_edit)
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # 버튼: 생성, 수정, 삭제
        btn_layout = QHBoxLayout()
        self.create_vehicle_btn = QPushButton("생성")
        self.create_vehicle_btn.clicked.connect(self.create_vehicle)
        btn_layout.addWidget(self.create_vehicle_btn)
        self.update_vehicle_btn = QPushButton("수정")
        self.update_vehicle_btn.clicked.connect(self.update_vehicle)
        btn_layout.addWidget(self.update_vehicle_btn)
        self.delete_vehicle_btn = QPushButton("삭제")
        self.delete_vehicle_btn.clicked.connect(self.delete_vehicle)
        btn_layout.addWidget(self.delete_vehicle_btn)
        main_layout.addLayout(btn_layout)
        
        # 조회 결과 테이블
        self.vehicle_table = QTableWidget()
        self.vehicle_table.setColumnCount(5)
        self.vehicle_table.setHorizontalHeaderLabels(["ID", "Employee ID", "1달 주유비", "주행거리", "엔진오일 교체일"])
        self.vehicle_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.vehicle_table)
        
        self.setLayout(main_layout)

    def create_vehicle(self):
        global global_token
        if not global_token:
            QMessageBox.warning(self, "경고", "로그인 토큰이 없습니다.")
            return
        try:
            data = {
                "employee_id": int(self.emp_id_edit.text()),
                "monthly_fuel_cost": float(self.monthly_fuel_edit.text() or 0),
                "current_mileage": int(self.current_mileage_edit.text() or 0),
                "last_engine_oil_change": self.oil_change_date_edit.date().toString("yyyy-MM-dd")
            }
            response = requests.post(f"{BASE_URL}/employee_vehicles", json=data,
                                     headers={"Authorization": f"Bearer {global_token}", "Content-Type": "application/json"})
            response.raise_for_status()
            QMessageBox.information(self, "성공", "차량 관리 정보 생성 완료!")
            self.fetch_vehicle()  # 새로고침
        except Exception as e:
            QMessageBox.critical(self, "오류", f"차량 관리 정보 생성 오류: {e}")

    def fetch_vehicle(self):
        global global_token
        emp_id = self.emp_id_search_edit.text().strip()
        if not emp_id:
            QMessageBox.warning(self, "경고", "조회할 직원 ID를 입력하세요.")
            return
        try:
            # 전체 차량 관리 기록 중, 해당 직원의 정보 조회
            response = requests.get(f"{BASE_URL}/employee_vehicles", headers={"Authorization": f"Bearer {global_token}"})
            response.raise_for_status()
            vehicles = response.json()
            # 필터링: 해당 직원 ID에 해당하는 데이터만
            filtered = [v for v in vehicles if v.get("employee_id") == int(emp_id)]
            self.vehicle_table.setRowCount(0)
            for v in filtered:
                row = self.vehicle_table.rowCount()
                self.vehicle_table.insertRow(row)
                self.vehicle_table.setItem(row, 0, QTableWidgetItem(str(v.get("id"))))
                self.vehicle_table.setItem(row, 1, QTableWidgetItem(str(v.get("employee_id"))))
                self.vehicle_table.setItem(row, 2, QTableWidgetItem(str(v.get("monthly_fuel_cost"))))
                self.vehicle_table.setItem(row, 3, QTableWidgetItem(str(v.get("current_mileage"))))
                self.vehicle_table.setItem(row, 4, QTableWidgetItem(v.get("last_engine_oil_change") or ""))
        except Exception as e:
            QMessageBox.critical(self, "오류", f"차량 관리 정보 조회 오류: {e}")

    def update_vehicle(self):
        global global_token
        vehicle_id, ok = QInputDialog.getInt(self, "차량 정보 수정", "수정할 차량 관리 정보 ID:")
        if not ok:
            return
        try:
            data = {
                "employee_id": int(self.emp_id_edit.text()),
                "monthly_fuel_cost": float(self.monthly_fuel_edit.text() or 0),
                "current_mileage": int(self.current_mileage_edit.text() or 0),
                "last_engine_oil_change": self.oil_change_date_edit.date().toString("yyyy-MM-dd")
            }
            response = requests.put(f"{BASE_URL}/employee_vehicles/{vehicle_id}", json=data,
                                    headers={"Authorization": f"Bearer {global_token}", "Content-Type": "application/json"})
            response.raise_for_status()
            QMessageBox.information(self, "성공", "차량 관리 정보 수정 완료!")
            self.fetch_vehicle()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"차량 관리 정보 수정 오류: {e}")

    def delete_vehicle(self):
        global global_token
        vehicle_id, ok = QInputDialog.getInt(self, "차량 정보 삭제", "삭제할 차량 관리 정보 ID:")
        if not ok:
            return
        try:
            response = requests.delete(f"{BASE_URL}/employee_vehicles/{vehicle_id}",
                                       headers={"Authorization": f"Bearer {global_token}"})
            response.raise_for_status()
            QMessageBox.information(self, "성공", "차량 관리 정보 삭제 완료!")
            self.fetch_vehicle()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"차량 관리 정보 삭제 오류: {e}")


# ----------------------------
# Main Window
# ----------------------------
class MainApp(QMainWindow):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.setWindowTitle("매출 관리 시스템")
        self.setGeometry(100, 100, 1200, 800)
        self.init_ui()

    def init_ui(self):
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # 관리용 탭: 여러 탭 추가 (여기서는 주문 및 매출 관리 탭을 중심으로 구성)
        self.orders_mgmt_tab = OrdersManagementTab(self.token)
        self.salary_calc_tab = SalaryCalculationTab(self.token)
        # 추가적으로 직원별 매출, 전체 매출 등 다른 탭을 만들 수 있음
        # 예를 들어, DashboardTab (전체 매출 집계) 등을 추가할 수 있음
        # self.dashboard_tab = DashboardTab(self.token)
        # self.daily_orders_tab = DailyOrdersTab(self.token)
        # self.daily_sales_tab = DailySalesTab(self.token)
        # self.monthly_sales_tab = MonthlySalesTab(self.token)
        # self.yearly_sales_tab = YearlySalesTab(self.token)
        self.vehicle_tab = EmployeeVehicleTab()
        # self.tab_widget.addTab(self.dashboard_tab, "대시보드")
        self.tab_widget.addTab(self.orders_mgmt_tab, "주문/매출 관리")
        # self.tab_widget.addTab(self.daily_sales_tab, "일매출")
        # self.tab_widget.addTab(self.monthly_sales_tab, "월매출")
        # self.tab_widget.addTab(self.yearly_sales_tab, "년매출")
        self.tab_widget.addTab(self.vehicle_tab, "차량 관리")
        self.tab_widget.addTab(self.salary_calc_tab, "월급 계산")
        self.tab_widget.addTab(self.orders_mgmt_tab, "주문/매출 관리")
        # 다른 탭 추가 가능: 예) 직원별 매출, 전체 매출 등

# ----------------------------
# Main Function
# ----------------------------
def main():
    app = QApplication(sys.argv)
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.Accepted:
        main_window = MainApp(global_token)
        main_window.show()
        sys.exit(app.exec())
    else:
        sys.exit()

if __name__ == "__main__":
    main()

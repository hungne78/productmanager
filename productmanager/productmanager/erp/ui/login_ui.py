from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QHBoxLayout
import sys
import os

# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.api_services import api_login_employee
from ui.main_ui import MainApp

class LoginWindow(QWidget):
    """ 로그인 창 """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("🔑 성심유통 관리자 로그인")
        self.resize(450, 200)
        self.setStyleSheet("""
            QWidget {
                background-color: #F5F5F5;
            }
            QLabel {
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                font-size: 14px;
                border: 1px solid #B0BEC5;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #2E86C1;
                color: white;
                font-size: 14px;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1F618D;
            }
        """)

        layout = QVBoxLayout()

        # 직원 ID 입력
        self.id_label = QLabel("👤 직원 ID:")
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("직원 ID 입력 (숫자)")
        self.id_input.returnPressed.connect(self.handle_login)  # ✅ 엔터키 지원

        # 비밀번호 입력
        self.password_label = QLabel("🔒 비밀번호:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("비밀번호 입력")
        self.password_input.returnPressed.connect(self.handle_login)  # ✅ 엔터키 지원

        # 로그인 버튼
        self.login_button = QPushButton("로그인")
        self.login_button.clicked.connect(self.handle_login)

        # 버튼 정렬
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.login_button)

        # 위젯 추가
        layout.addWidget(self.id_label)
        layout.addWidget(self.id_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def handle_login(self):
        emp_id = self.id_input.text().strip()
        password = self.password_input.text().strip()

        if not emp_id or not password:
            QMessageBox.warning(self, "⚠️ 경고", "직원 ID와 비밀번호를 입력하세요.")
            return

        try:
            emp_id = int(emp_id)  # 직원 ID는 숫자로 변환
        except ValueError:
            QMessageBox.warning(self, "⚠️ 경고", "올바른 직원 ID를 입력하세요.")
            return

        response = api_login_employee(emp_id, password)

        if response and "token" in response:
            QMessageBox.information(self, "✅ 성공", f"{response['name']}님, 환영합니다!")
            self.open_main_app()
        else:
            QMessageBox.warning(self, "🚫 로그인 실패", "직원 ID 또는 비밀번호가 올바르지 않습니다.")

    def open_main_app(self):
        """ 로그인 성공 후 메인 화면 실행 """
        self.close()  # 로그인 창 닫기
        self.main_app = MainApp()  # 메인 앱 실행
        self.main_app.show()

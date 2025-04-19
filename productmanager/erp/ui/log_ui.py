from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QFileDialog, QApplication
from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QTextCursor
import os
import sys
from PyQt5.QtCore import QObject, pyqtSignal
MAX_LOG_LINES = 500  # 💡 로그 최대 줄 수
class EmittingStream(QObject):
    text_written = pyqtSignal(str)

    def write(self, text):
        self.text_written.emit(str(text))

    def flush(self):
        pass  # 필요한 경우 구현
class LogTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("로그 탭")
        self.init_ui()

        self.log_file_path = "client_app_log.txt"  # 기본 로그 파일 경로
        # ✅ 표준 출력 연결
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        self.stdout_stream = EmittingStream()
        self.stdout_stream.text_written.connect(self.append_raw)
        sys.stdout = self.stdout_stream
        sys.stderr = self.stdout_stream

    def init_ui(self):
        layout = QVBoxLayout()

        # ✅ 로그 출력 영역
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #f0f0f0; font-family: Consolas;")
        layout.addWidget(self.log_output)

        # ✅ 버튼들
        btn_layout = QHBoxLayout()
        self.copy_btn = QPushButton("복사")
        self.save_btn = QPushButton("파일로 저장")
        self.clear_btn = QPushButton("지우기")
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # ✅ 버튼 동작 연결
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.save_btn.clicked.connect(self.save_to_file)
        self.clear_btn.clicked.connect(self.clear_log)

    def append_raw(self, text: str):
        self.log_output.moveCursor(QTextCursor.End)
        self.log_output.insertPlainText(text)

        # ✅ 로그 줄 수 초과 시 삭제
        current_text = self.log_output.toPlainText()
        lines = current_text.split("\n")
        if len(lines) > MAX_LOG_LINES:
            trimmed = "\n".join(lines[-MAX_LOG_LINES:])
            self.log_output.setPlainText(trimmed)
            self.log_output.moveCursor(QTextCursor.End)


    def append_log(self, message: str, level="INFO"):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        line = f"[{timestamp}] [{level}] {message}"
        self.log_output.append(line)
        self.log_output.moveCursor(QTextCursor.End)

        # ✅ 로그 파일에도 저장
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            self.log_output.append(f"[ERROR] 로그 파일 저장 실패: {e}")

        # ✅ 로그 줄 수 초과 시 삭제
        current_text = self.log_output.toPlainText()
        lines = current_text.split("\n")
        if len(lines) > MAX_LOG_LINES:
            trimmed = "\n".join(lines[-MAX_LOG_LINES:])
            self.log_output.setPlainText(trimmed)
            self.log_output.moveCursor(QTextCursor.End)
            
    def copy_to_clipboard(self):
        clipboard = self.clipboard() if hasattr(self, 'clipboard') else QApplication.clipboard()
        clipboard.setText(self.log_output.toPlainText())

    def save_to_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "로그 저장", "log.txt", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.log_output.toPlainText())
                self.append_log(f"로그를 '{file_path}'에 저장했습니다.", level="INFO")
            except Exception as e:
                self.append_log(f"파일 저장 실패: {e}", level="ERROR")

    def clear_log(self):
        self.log_output.clear()
        self.append_log("로그 화면 초기화됨", level="INFO")

import sys
import traceback
import atexit
from PyQt5.QtWidgets import QApplication
from ui.main_ui import MainApp
from ui.login_ui import LoginWindow

# 🔥 예외 발생 시 로그로 남기기
def global_exception_handler(exctype, value, tb):
    error_text = "".join(traceback.format_exception(exctype, value, tb))
    print(f"❌ 예외 발생:\n{error_text}")
    try:
        with open("fatal_log.txt", "a", encoding="utf-8") as f:
            f.write(f"\n=== Unhandled Exception ===\n{error_text}\n")
    except:
        pass
    sys.exit(1)

# 📌 종료 직전 자동 로그 저장
def save_log_on_exit():
    try:
        if hasattr(app, "main_window") and hasattr(app.main_window, "log_tab"):
            log_text = app.main_window.log_tab.log_output.toPlainText()
            with open("final_log.txt", "w", encoding="utf-8") as f:
                f.write(log_text)
            print("✅ 종료 시 로그 저장 완료")
    except Exception as e:
        print(f"⚠️ 로그 저장 실패: {e}")

# 전역 예외 및 종료 후처리 등록
sys.excepthook = global_exception_handler
atexit.register(save_log_on_exit)

# 로그인 성공 시 실행될 콜백 함수 정의
def on_login_success():
    main_window = MainApp()
    app.main_window = main_window         # ✅ 로그 저장을 위해 참조 연결
    main_window.show()

def main():
    global app
    app = QApplication(sys.argv)

    login_window = LoginWindow()
    login_window.login_success_callback = on_login_success  # ✅ 로그인 성공 시 콜백 등록
    login_window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

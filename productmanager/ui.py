import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QTabWidget
from PyQt5.QtCore import Qt

def get_flat_stylesheet():
    """
    화이트+파스텔 톤의 가벼운 UI 느낌을 위한 QSS 예시
    """
    return """
    QMainWindow {
        background-color: #FAFAFA;
    }
    QToolBar {
        background-color: #FFFFFF;
        border-bottom: 1px solid #E0E0E0;
    }
    QToolBar QToolButton {
        color: #333333;
        font-size: 14px;
    }
    QWidget {
        background-color: #FAFAFA;
        color: #222222;
        font-family: 'Apple SD Gothic Neo', '맑은 고딕', sans-serif;
    }
    QLineEdit {
        border: 1px solid #CCCCCC;
        padding: 5px;
        border-radius: 5px;
        background-color: #FFFFFF;
    }
    QPushButton {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #CCCCCC;
        border-radius: 5px;
        padding: 6px 12px;
    }
    QPushButton:hover {
        background-color: #F5F5F5;
        border: 1px solid #BBBBBB;
    }
    QLabel {
        color: #333333;
        font-size: 14px;
    }
    QTabWidget::pane {
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        margin-top: -1px;
    }
    QTabWidget::tab-bar {
        left: 5px;
    }
    QTabBar::tab {
        background: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 8px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    QTabBar::tab:selected, QTabBar::tab:hover {
        background: #F5F5F5;
        border-bottom: 1px solid #F5F5F5;
    }
    """

class FlatMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("플랫 디자인 예시")
        self.resize(1200, 800)
        self.setStyleSheet(get_flat_stylesheet())

        # 탭 UI를 예시로
        self.tabs = QTabWidget()
        self.tabs.addTab(self.make_tab_widget("직원관리"), "직원관리")
        self.tabs.addTab(self.make_tab_widget("거래처관리"), "거래처관리")
        self.tabs.addTab(self.make_tab_widget("제품관리"), "제품관리")

        self.setCentralWidget(self.tabs)

    def make_tab_widget(self, title):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"{title} 탭 화면"))
        layout.addWidget(QPushButton("버튼 예시"))
        widget.setLayout(layout)
        return widget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlatMainWindow()
    window.show()
    sys.exit(app.exec_())

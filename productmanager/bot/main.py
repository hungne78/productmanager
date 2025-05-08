# main.py (루트에 위치)
from ilmarebot.ui.main_window import ChatBotUI
from PyQt5 import QtWidgets
import sys

app = QtWidgets.QApplication(sys.argv)
win = ChatBotUI()
win.show()
sys.exit(app.exec_())

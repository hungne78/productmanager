from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
     QHeaderView
    
)
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtGui import QPen
from PyQt5.QtCore import Qt

class ThickLineDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        painter.save()
        pen = QPen(Qt.gray, 2)  # ✅ 원하는 색과 두께로 선 설정 (여기선 2px 회색)
        painter.setPen(pen)
        painter.drawRect(option.rect)  # ✅ 셀 테두리 그리기
        painter.restore()

class BaseLeftTableWidget(QWidget):
    def __init__(self, row_count, labels, parent=None):
        super().__init__(parent)
        self.row_count = row_count
        self.labels = labels  # ["ID","Name", ...]

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # ✅ `QTableWidget` 추가
        self.table_info = QTableWidget(self.row_count, 2)
        
        self.table_info.setHorizontalHeaderLabels(["항목", "값"])
        self.table_info.verticalHeader().setVisible(False)
        self.table_info.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_info.setEditTriggers(QTableWidget.DoubleClicked)  # 더블클릭 편집 가능
        
        if not hasattr(self, "table_info") or self.table_info is None:
            print("Error: table_info is None or deleted")
            return
        for r in range(self.row_count):
            # 항목명 셀
            item_label = QTableWidgetItem(self.labels[r])
            item_label.setFlags(Qt.ItemIsEnabled)  # 편집불가
            self.table_info.setItem(r, 0, item_label)
            # 값은 비워둠 (나중에 setItem(r,1,...) 혹은 setText)
            self.table_info.setItem(r, 1, QTableWidgetItem(""))
        self.table_info.setItemDelegate(ThickLineDelegate(self.table_info))
        main_layout.addWidget(self.table_info)

        # 버튼 (신규등록, 수정)
        btn_layout = QVBoxLayout()
        self.btn_new = QPushButton("신규등록")
        self.btn_edit = QPushButton("수정")
        

        btn_layout.addWidget(self.btn_new)
        btn_layout.addWidget(self.btn_edit)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def get_value(self, row):
        """row 행의 '값' 칸 텍스트"""
        if not hasattr(self, "table_info") or self.table_info is None:
            print("Error: table_info is None or deleted")
            return ""
        item = self.table_info.item(row, 1)
        return item.text().strip() if item and item.text() else "" 
        

    def set_value(self, row, text):
        """row 행의 '값' 칸을 설정"""
        if not hasattr(self, "table_info") or self.table_info is None:
            print("Error: table_info is None or deleted")
            return
        self.table_info.setItem(row, 1, QTableWidgetItem(text))

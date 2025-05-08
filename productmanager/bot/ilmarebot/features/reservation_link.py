
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QDateEdit

from PyQt5.QtCore import QDate
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp
from PyQt5 import QtWidgets,  QtGui
from ilmarebot.features.tide_sms import send_message_via_sens

from datetime import datetime
import sys


class MultiNumberInputDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("예약링크 보내기")
        self.setGeometry(100, 100, 500, 500)
        
        layout = QVBoxLayout()
        labels = ["전화번호 입력", "입실 날짜", "퇴실 날짜", "방호수"]
        self.num_inputs = []
        self.date_inputs = []

        # 첫 번째 입력란 (숫자 입력)
        label = QLabel(labels[0])
        layout.addWidget(label)
        # 전화번호 입력 필드 (0으로 시작 가능)
        self.phone_input = QLineEdit("010")
        self.phone_input.setPlaceholderText("예: 01012345678")
        self.phone_input.setStyleSheet("font-size: 25px; padding: 5px;")
        
        # 숫자만 입력 가능하도록 설정 (정규식 사용)
        phone_validator = QRegExpValidator(QRegExp("0[0-9]{9,10}"))  # 최소 10~11자리 숫자 입력
        self.phone_input.setValidator(phone_validator)

        layout.addWidget(self.phone_input)

        # 두 번째와 세 번째 입력란 (달력 - QDateEdit 사용)
        for i in range(1,3):  # 두 번째와 세 번째만 날짜 입력 필드로 설정
            date_label = QLabel(labels[i])
            date_label.setStyleSheet("font-size: 20px; font-weight: bold;")
            layout.addWidget(date_label)
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)  # 달력 팝업 활성화
            if i == 1:
                date_edit.setDate(QDate.currentDate())  # ✅ 첫 번째(출생 날짜) 기본값: 오늘 날짜
            else:
                date_edit.setDate(QDate.currentDate().addDays(1))  # ✅ 두 번째(예약 날짜)
            date_edit.setStyleSheet("font-size: 25px; padding: 5px;")
            
            layout.addWidget(date_edit)
            self.date_inputs.append(date_edit)
        
        # 네 번째 입력란 (드롭다운)
        label = QLabel(labels[-1])
        label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.dropdown = QComboBox()
        self.dropdown.addItems(["201호", "202호", "501호", "502호", "503호", "601호", "602호", "603호", "사랑채", "C02호", "C03호", "C04호", "C05호", "별채"])
        self.dropdown.setStyleSheet("font-size: 25px; padding: 5px;") 
        layout.addWidget(label)
        layout.addWidget(self.dropdown)

        self.ok_button = QPushButton("확인")
        self.ok_button.clicked.connect(self.get_inputs)
        self.ok_button.setStyleSheet("font-size: 25px; padding: 10px; background-color: #0073e6; color: white; border-radius: 5px;")
        layout.addWidget(self.ok_button)
        # 결과 레이블
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("font-size: 25px; color: blue;")
        layout.addWidget(self.result_label)
        self.setLayout(layout)

    def get_inputs(self):
        results = []
       
        # 숫자 입력 가져오기
        try:
            phone_number = self.phone_input.text()  # 문자열로 가져오기
            if len(phone_number) < 10:
                self.result_label.setText("전화번호를 올바르게 입력하세요!")
            else:
                self.result_label.setText(f"입력한 전화번호: {phone_number}")
                print(f"전화번호: {phone_number}")  # 콘솔 출력

            results.append(phone_number)
        except ValueError:
            results.append(None)  # 숫자가 아닌 경우 None 저장

        # 날짜 입력 가져오기
        for date_edit in self.date_inputs:
            results.append(date_edit.date().toString("yyyyMMdd"))  
              
        # 드롭다운에서 선택한 값 가져오기
        selected_room = self.dropdown.currentText()
        results.append(selected_room)
        room_mapping = {
            "201호": "5601454",
            "202호": "5601478",
            "501호": "5601501",
            "502호": "5601520",
            "503호": "5601527",
            "601호": "5601533",
            "602호": "5601537",
            "603호": "5601542",
            "사랑채": "5601549",
            "C02호": "5870382",
            "C03호": "5807525",
            "C04호": "5807529",
            "C05호": "5807541",
            "별채": "6369700"
        }

        selected_room = self.dropdown.currentText()  # 선택된 드롭다운 값 가져오기
        room_no = room_mapping.get(selected_room, "201")  # 값이 없으면 기본값 반환
        formatted_start_date = datetime.strptime(results[1], "%Y%m%d").strftime("%Y년 %m월 %d일")
        formatted_end_date = datetime.strptime(results[2], "%Y%m%d").strftime("%Y년 %m월 %d일")
        rink = f"https://m.place.naver.com/accommodation/20530084/room/{room_no}?entry=pll&businessCategory=pension&level=top&guest=2&checkin={results[1]}&checkout={results[2]}&reviewItem={room_no}"
        message = f'''입실: {formatted_start_date}
퇴실: {formatted_end_date}
객실 : {selected_room}
예약 링크 : {rink}'''
        print("입력한 값:", results)
        self.accept()  # 다이얼로그 닫기
        send_message_via_sens(phone_number, message)
        QtWidgets.QMessageBox.information(self, "일마레 알림", "예약링크 보내기 성공")






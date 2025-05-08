# 기존 ChatBotUI 코드를 유지하고 단계적으로 분리하세요.
from datetime import datetime
import threading
from selenium.webdriver.chrome.service import Service
from PyQt5 import QtWidgets,  QtGui
import sys
import json
import os
from PyQt5 import QtCore 
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
import fitz  # PyMuPDF (기존 PDF 내용을 유지하는 라이브러리)
import requests
import shutil
from PyQt5.QtCore import QTimer, QTime
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtWidgets import QInputDialog, QListWidget
import shutil
from ilmarebot.features.ddnayo_scraper import ddnayo_whole_res
from ilmarebot.features.instagram_commenter import instagram_process
from ilmarebot.features.talk_chatbot import start_full_process
from ilmarebot.features.review_bot import start_review_process
from ilmarebot.features.tide_sms import send_to_one_tide, tide_message
from ilmarebot.features.reservation_link import MultiNumberInputDialog
from ilmarebot.features import talk_chatbot
from ilmarebot.features import ddnayo_scraper
from ilmarebot.features import review_bot
from translate import Translator
from ilmarebot.common.path import JSON_FOLDER, LOGIN_INFO, PROMPT_FILE, EXTRA_PROMPT_FILE, CHECKBOX_STATE_FILE, ROOMS_FILE, UPDATE_SERVER_URL, LOCAL_VERSION_FILE, CURRENT_VERSION, UNANSWERED_QUESTIONS_FILE, PDF_SETTINGS_FILE, SETTINGS_FILE




# 네이버톡 챗봇 UI 클래스(pyqt5)
class ChatBotUI(QtWidgets.QMainWindow):
    instance = None
    
    def __init__(self):
        super(ChatBotUI, self).__init__()
        
        self.setWindowTitle("MyShop 네이버톡톡 챗봇 and 리뷰댓글봇 v1.0.1")
        self.setGeometry(100, 100, 800, 1200)
        self.setWindowIcon(QIcon('naver.ico'))  # 아이콘 파일 경로 지정
        self.running = True
        self.threads = []  # 실행 중인 스레드를 관리하기 위한 리스트
        
        # 🟢 트레이 아이콘 추가
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("naver.ico"))  # 아이콘 파일 (변경 가능)
        self.tray_icon.setToolTip("네이버톡톡 챗봇 실행 중")  # 툴팁 설정

        # 트레이 메뉴
        self.tray_menu = QMenu()
        show_action = QAction("보이기", self)
        exit_action = QAction("종료", self)

        show_action.triggered.connect(self.show_window)  # 창 보이기
        exit_action.triggered.connect(self.exit_app)  # 앱 종료

        self.tray_menu.addAction(show_action)
        self.tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(self.tray_menu)  # 메뉴 연결

        # 창 닫을 때 트레이로 최소화
        self.tray_icon.activated.connect(self.tray_icon_clicked)

        # 트레이 아이콘 표시
        self.tray_icon.show()

        # 메뉴바 추가
        menubar = self.menuBar()
        file_menu = menubar.addMenu('파일')

        self.rooms = self.load_rooms()

        open_file_action = QtWidgets.QAction('PDF 파일 열기', self)
        open_file_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_file_action)

        # '버전' 및 '업데이트' 메뉴 추가
        update_menu = menubar.addMenu('업데이트')

        version_action = QtWidgets.QAction('버전', self)
        version_action.triggered.connect(self.show_version)
        update_menu.addAction(version_action)

        update_action = QtWidgets.QAction('업데이트', self)
        update_action.triggered.connect(self.check_for_updates)
        update_menu.addAction(update_action)

        # 메인 레이아웃
        main_layout = QtWidgets.QVBoxLayout()
       
        # 중앙 위젯과 레이아웃 설정
        main_layout = QtWidgets.QVBoxLayout()
        self.pdf_status_label = QtWidgets.QLabel("불러온 파일: 없음")
        self.pdf_status_label.setStyleSheet("font-size: 16px; color: blue; border: 1px solid #ccc; padding: 5px;")
        main_layout.addWidget(self.pdf_status_label)

        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # PDF 폴더 경로 설정
        PDF_FOLDER = os.path.join(os.getcwd(), 'json')
        # 폴더가 없으면 생성
        if not os.path.exists(PDF_FOLDER):
            os.makedirs(PDF_FOLDER)
        self.selected_pdf_path = None
        self.system_message = ""
        self.load_saved_pdf()  # 이전에 저장된 PDF 불러오기

        # 네이버톡 챗창 레이블
        chat_label = QtWidgets.QLabel("네이버톡 챗창")
        chat_label.setStyleSheet("font-size: 27px; font-weight: bold; color: #0073e6;")
        main_layout.addWidget(chat_label)

        # 채팅 상태 창
        self.chat_status = QtWidgets.QTextEdit()
        self.chat_status.setReadOnly(True)
        self.chat_status.setStyleSheet("background-color: #ffffff; border: 1px solid #ccc; font-size: 22px;")
        main_layout.addWidget(self.chat_status)

        # 스크롤 자동 이동 추가
        self.chat_status.textChanged.connect(lambda: self.chat_status.verticalScrollBar().setValue(self.chat_status.verticalScrollBar().maximum()))
        

        # 시스템 메세지 레이블
        system_label = QtWidgets.QLabel("시스템 메세지")
        system_label.setStyleSheet("font-size: 27px; font-weight: bold; color: #0073e6;")
        main_layout.addWidget(system_label)

        # 시스템 상태 창
        self.system_status = QtWidgets.QTextEdit()
        self.system_status.setReadOnly(True)
        self.system_status.setStyleSheet("background-color: #ffffff; border: 1px solid #ccc; font-size: 22px;")
        main_layout.addWidget(self.system_status)
        
        # 스크롤 자동 이동 추가
        self.system_status.textChanged.connect(lambda: self.system_status.verticalScrollBar().setValue(self.system_status.verticalScrollBar().maximum()))
        
        # 자동 로그인 체크박스 추가
        self.auto_login_checkbox = QtWidgets.QCheckBox("자동 로그인")
        self.auto_login_checkbox.setStyleSheet("font-size: 16px;")
        main_layout.addWidget(self.auto_login_checkbox)

        # 체크박스 추가
        self.remember_checkbox = QtWidgets.QCheckBox("로그인 정보 기억하기")
        self.remember_checkbox.setStyleSheet("font-size: 16px;")
        main_layout.addWidget(self.remember_checkbox)

        # 체크박스 상태 불러오기
        self.load_checkbox_state()
        
        # 버튼 레이아웃 추가
        top_button_layout = QtWidgets.QHBoxLayout()
        bottom_button_layout = QtWidgets.QHBoxLayout()
        

        # 네이버톡 입력 필드 (한 줄에 배치)
        naver_layout = QtWidgets.QHBoxLayout()

        self.naver_id_label = QtWidgets.QLabel("네이버 ID:")
        naver_layout.addWidget(self.naver_id_label)
        self.naver_id_input = QtWidgets.QLineEdit()
        naver_layout.addWidget(self.naver_id_input)

        self.naver_pw_label = QtWidgets.QLabel("네이버 PW:")
        naver_layout.addWidget(self.naver_pw_label)
        self.naver_pw_input = QtWidgets.QLineEdit()
        self.naver_pw_input.setEchoMode(QtWidgets.QLineEdit.Password)
        naver_layout.addWidget(self.naver_pw_input)
        
        main_layout.addLayout(naver_layout)

        naverno_layout = QtWidgets.QHBoxLayout()

        self.naver_number_label = QtWidgets.QLabel("네이버 No:")
        naverno_layout.addWidget(self.naver_number_label)
        self.naver_number_input = QtWidgets.QLineEdit()
        self.naver_number_input.setValidator(QtGui.QIntValidator())  # 숫자만 입력 가능
        naverno_layout.addWidget(self.naver_number_input)
        
        self.naver_number_label2 = QtWidgets.QLabel("네이버 No2:")
        naverno_layout.addWidget(self.naver_number_label2)
        self.naver_number_input2 = QtWidgets.QLineEdit()
        self.naver_number_input2.setValidator(QtGui.QIntValidator())  # 숫자만 입력 가능
        naverno_layout.addWidget(self.naver_number_input2)

        main_layout.addLayout(naverno_layout)
        # 리뷰 입력 필드 (한 줄에 배치)
        review_layout = QtWidgets.QHBoxLayout()

        self.naver_number_label = QtWidgets.QLabel("리  뷰  No:")
        review_layout.addWidget(self.naver_number_label)
        self.review_input = QtWidgets.QLineEdit()
        self.review_input.setValidator(QtGui.QIntValidator())  # 숫자만 입력 가능
        review_layout.addWidget(self.review_input)
        
        self.naver_number_label2 = QtWidgets.QLabel("리  뷰 No2:")
        review_layout.addWidget(self.naver_number_label2)
        self.review_input2 = QtWidgets.QLineEdit()
        self.review_input2.setValidator(QtGui.QIntValidator())  # 숫자만 입력 가능
        review_layout.addWidget(self.review_input2)

        main_layout.addLayout(review_layout)
        
        # 떠나요 입력 필드 (한 줄에 배치)
        ddnayo_layout = QtWidgets.QHBoxLayout()

        self.ddnayo_id_label = QtWidgets.QLabel("떠나요 ID:")
        ddnayo_layout.addWidget(self.ddnayo_id_label)
        self.ddnayo_id_input = QtWidgets.QLineEdit()
        ddnayo_layout.addWidget(self.ddnayo_id_input)

        self.ddnayo_pw_label = QtWidgets.QLabel("떠나요 PW:")
        ddnayo_layout.addWidget(self.ddnayo_pw_label)
        self.ddnayo_id_input2 = QtWidgets.QLineEdit()
        self.ddnayo_id_input2.setEchoMode(QtWidgets.QLineEdit.Password)
        ddnayo_layout.addWidget(self.ddnayo_id_input2)
        main_layout.addLayout(ddnayo_layout)

        ddnayo_layout2 = QtWidgets.QHBoxLayout()
        self.ddnayo_number_label = QtWidgets.QLabel("떠나요 No:")
        ddnayo_layout2.addWidget(self.ddnayo_number_label)
        self.ddnayo_number_input2 = QtWidgets.QLineEdit()
        self.ddnayo_number_input2.setValidator(QtGui.QIntValidator())  # 숫자만 입력 가능
        ddnayo_layout2.addWidget(self.ddnayo_number_input2)
        
        # ✅ 버튼 레이아웃 추가 (한 줄에 두 개)
        button_layout = QtWidgets.QHBoxLayout()

        # ✅ 미응답 질문 확인 버튼
        self.show_unanswered_btn = QtWidgets.QPushButton("미응답 질문 확인")
        self.show_unanswered_btn.setStyleSheet("background-color: #ffcc00; color: black; font-size: 16px;")
        self.show_unanswered_btn.clicked.connect(self.show_unanswered_questions)

        # ✅ 질문에 답변 입력 버튼
        self.answer_question_btn = QtWidgets.QPushButton("질문에 답변 입력")
        self.answer_question_btn.setStyleSheet("background-color: #28a745; color: white; font-size: 16px;")
        self.answer_question_btn.clicked.connect(self.show_answer_input)

        # 방 관리 버튼 추가
        self.manage_rooms_button = QtWidgets.QPushButton("방 관리")
        self.manage_rooms_button.setStyleSheet("background-color: #17a2b8; color: white; font-size: 16px; font-weight: bold; padding: 10px;")
        self.manage_rooms_button.clicked.connect(self.show_room_management)
       

        self.res_message_button = QtWidgets.QPushButton("예약링크 보내기")
        self.res_message_button.setStyleSheet("background-color: #0073e6; color: white; font-size: 16px; font-weight: bold; padding: 10px;")
        self.res_message_button.clicked.connect(self.reservation_message)
       

        # ✅ 버튼을 가로로 추가
        button_layout.addWidget(self.show_unanswered_btn)
        button_layout.addWidget(self.answer_question_btn)
        button_layout.addWidget(self.manage_rooms_button)
        button_layout.addWidget(self.res_message_button)
        # ✅ 메인 레이아웃에 버튼 레이아웃 추가
        main_layout.addLayout(button_layout)


        # 네이버톡 시작 버튼
        start_btn = QtWidgets.QPushButton("네이버톡 시작")
        start_btn.setStyleSheet("background-color: #0073e6; color: white; font-size: 23px; font-weight: bold; padding: 10px;")
        start_btn.clicked.connect(self.call_external_function)
        top_button_layout.addWidget(start_btn)
        self.start_btn = start_btn  # 버튼 저장

        # 네이버톡 프롬프트 버튼
        extra_btn = QtWidgets.QPushButton("네이버톡 프롬프트")
        extra_btn.setStyleSheet("background-color: #6c757d; color: white; font-size: 23px; font-weight: bold; padding: 10px;")
        extra_btn.clicked.connect(self.call_extra_function)
        top_button_layout.addWidget(extra_btn) 
        self.extra_btn = extra_btn  # 버튼 저장

        # 리뷰 댓글 시작 버튼 추가
        review_btn = QtWidgets.QPushButton("리뷰 댓글 시작")
        review_btn.setStyleSheet("background-color: #28a745; color: white; font-size: 23px; font-weight: bold; padding: 10px;")
        review_btn.clicked.connect(self.call_review_function)
        bottom_button_layout.addWidget(review_btn)
        self.review_btn = review_btn  # 버튼 저장

        # 리뷰 프롬프트 시작 버튼 추가
        prompt_btn = QtWidgets.QPushButton("리뷰 댓글 프롬프트")
        prompt_btn.setStyleSheet("background-color: #ffc107; color: white; font-size: 23px; font-weight: bold; padding: 10px;")
        prompt_btn.clicked.connect(self.call_prompt_function)
        bottom_button_layout.addWidget(prompt_btn)
        self.prompt_btn = prompt_btn  # 버튼 저장

        
        instagram_layout = QtWidgets.QHBoxLayout()
        
        self.instagram_input = QtWidgets.QLineEdit()
        self.instagram_input.setPlaceholderText("인스타그램 게시글 주소")
        instagram_layout.addWidget(self.instagram_input)

        self.instagram_start_input = QtWidgets.QLineEdit()
        self.instagram_start_input.setPlaceholderText("댓글시작아이디")
        
        instagram_layout.addWidget(self.instagram_start_input)

        self.instagram_end_input = QtWidgets.QLineEdit()
        self.instagram_end_input.setPlaceholderText("댓글끝번호")
        instagram_layout.addWidget(self.instagram_end_input)

        instagram_reply_button = QtWidgets.QPushButton("인스타답변 자동댓글")
        instagram_reply_button.setStyleSheet("background-color: #8224e3; color: white; font-size: 16px; font-weight: bold; padding: 10px;")
        instagram_reply_button.clicked.connect(self.instagram_reply)
        instagram_layout.addWidget(instagram_reply_button)
        self.instagram_reply_button = instagram_reply_button
       
        self.instagram_input.setFixedSize(300,50)
        self.instagram_start_input.setFixedHeight(50)
        self.instagram_end_input.setFixedHeight(50)
        instagram_reply_button.setFixedSize(200, 50)
       

        main_layout.addLayout(instagram_layout)

        # 두 번째 줄(물때 안내)
        tide_layout = QtWidgets.QHBoxLayout()

        self.tide_input = QtWidgets.QLineEdit()
        self.tide_input.setPlaceholderText("보내실 전화번호를 입력하세요.")
        tide_layout.addWidget(self.tide_input)

        # 추가 버튼 하나 더 (예: '추가 물때 버튼')
        extra_tide_button = QtWidgets.QPushButton("입력번호로 물때 보내기")
        extra_tide_button.setStyleSheet("background-color: #1e73be; color: white; font-size: 16px; font-weight: bold; padding: 10px;")
        extra_tide_button.clicked.connect(self.send_to_one)  
        tide_layout.addWidget(extra_tide_button)

        tide_information_button = QtWidgets.QPushButton("당일물때 전체보내기")
        tide_information_button.setStyleSheet("background-color: #dd9933; color: white; font-size: 16px; font-weight: bold; padding: 10px;")
        tide_information_button.clicked.connect(self.tide_information)
        tide_layout.addWidget(tide_information_button)
        self.tide_information_button = tide_information_button  # 버튼 저장
        

        self.tide_input.setFixedHeight(30)
        tide_information_button.setFixedSize(200, 50)
        extra_tide_button.setFixedSize(200, 50)
        main_layout.addLayout(tide_layout)

        
        self.log_path = "tide_process_log.txt"

        # 타이머 설정 (매 1분마다 check_time 실행)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tide_check_time)
        self.timer.start(60_000)  # 60,000ms = 1분

        # 타이머 설정 (1시간 마다 떠나요 웹스크래핑 실행)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.extra_function)
        self.timer.start(7200000)  # 1시간 = 3600000ms

        main_layout.addLayout(top_button_layout)
        main_layout.addLayout(bottom_button_layout)
        
        
        # 중앙 위젯 설정
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # 프롬프트 입력창 설정
        self.prompt_window = QtWidgets.QDialog(self)
        self.prompt_window.setWindowTitle("리뷰 프롬프트 입력창")
        self.prompt_window.setGeometry(self.geometry().right(), 100, 800, 800)  # 위치와 크기 설정

         # QTextEdit를 새 창에 추가
        self.prompt_text_edit = QtWidgets.QTextEdit(self.prompt_window)
        self.prompt_text_edit.setGeometry(10, 10, 780, 680)
        self.prompt_text_edit.setStyleSheet("background-color: #f8f9fa; border: 1px solid #ccc; font-size: 20px;")
        self.prompt_text_edit.setReadOnly(False)
        # 라디오 버튼 추가
        self.radio_button_group = QtWidgets.QButtonGroup(self.prompt_window)

        # 라디오 버튼 1
        self.radio_button_1 = QtWidgets.QRadioButton("네이버예약 가능업소", self.prompt_window)
        self.radio_button_1.setChecked(True)  # 기본적으로 첫 번째 라디오 버튼 선택
        self.radio_button_group.addButton(self.radio_button_1)

        # 라디오 버튼 2
        self.radio_button_2 = QtWidgets.QRadioButton("네이버예약 불가능업소", self.prompt_window)
        self.radio_button_group.addButton(self.radio_button_2)

        # 라디오 버튼들을 수평 레이아웃에 추가
        radio_button_layout = QtWidgets.QHBoxLayout()
        radio_button_layout.addWidget(self.radio_button_1)
        radio_button_layout.addWidget(self.radio_button_2)

        # 라디오 버튼 레이아웃을 메인 레이아웃에 추가
        main_layout.addLayout(radio_button_layout)

        # 레이아웃 생성
        button_layout = QtWidgets.QHBoxLayout()

        # 저장 버튼 추가
        save_button = QtWidgets.QPushButton("저장", self.prompt_window)
        save_button.setStyleSheet("background-color: #28a745; color: white; font-size: 16px; padding: 1px; border-radius: 5px;")
        save_button.clicked.connect(self.save_prompt_content)
        button_layout.addWidget(save_button)

        # 취소 버튼 추가
        cancel_button = QtWidgets.QPushButton("취소", self.prompt_window)
        cancel_button.setStyleSheet("background-color: #dc3545; color: white; font-size: 16px; padding: 1px; border-radius: 5px;")
        cancel_button.clicked.connect(self.cancel_prompt_content)
        button_layout.addWidget(cancel_button)

        # 버튼들이 가운데 정렬
        button_layout.setAlignment(QtCore.Qt.AlignCenter)

        # 버튼들의 크기 설정: 각 버튼을 창의 절반 크기로 설정
        save_button.setFixedSize(self.prompt_window.width() // 2 - 20, 50)  # 버튼 크기 늘림
        cancel_button.setFixedSize(self.prompt_window.width() // 2 - 20, 50)  # 버튼 크기 늘림

        # 레이아웃을 창에 추가
        layout_widget = QtWidgets.QWidget(self.prompt_window)
        layout_widget.setLayout(button_layout)
        layout_widget.setGeometry(0, 700, 800, 100)  # 버튼 위치와 크기 설정
        
        self.load_login_info()
        self.load_checkbox_state()
        # __init__ 안에 체크박스 이벤트 연결
        self.auto_login_checkbox.stateChanged.connect(self.save_checkbox_state)
        self.remember_checkbox.stateChanged.connect(self.save_checkbox_state)

        # 라디오 버튼 선택 상태 불러오기
        self.load_radio_button_state()

    def show_answer_input(self):
        """미응답 질문 중 하나를 선택하고 답변을 입력하는 창"""
        if not os.path.exists(UNANSWERED_QUESTIONS_FILE):
            QtWidgets.QMessageBox.warning(self, "오류", "저장된 미응답 질문이 없습니다.")
            return

        with open(UNANSWERED_QUESTIONS_FILE, "r", encoding="utf-8") as f:
            questions = json.load(f)

        if not questions:
            QtWidgets.QMessageBox.information(self, "알림", "기록할 미응답 질문이 없습니다.")
            return

        # 질문 선택
        question, ok = QInputDialog.getItem(self, "질문 선택", "답변할 질문을 선택하세요:", questions, 0, False)
        if not ok:
            return

        # 답변 입력
        answer, ok = QInputDialog.getText(self, "답변 입력", f"'{question}'에 대한 답변을 입력하세요:")
        if not ok or not answer.strip():
            return

        # 저장할 PDF 파일 선택 (기존 파일 or 새 파일)
        if self.selected_pdf_path:
            pdf_path = self.selected_pdf_path  # 기존에 불러온 PDF에 저장
        else:
            pdf_path, _ = QFileDialog.getSaveFileName(self, "PDF 파일 선택", "", "PDF Files (*.pdf);;All Files (*)")
            if not pdf_path:
                return

        # PDF 파일이 열려 있는 경우 처리 (복사본 만들고 저장)
        temp_pdf_path = pdf_path + "_temp.pdf"
        shutil.copy(pdf_path, temp_pdf_path)  # 기존 파일을 백업

        # PDF에 추가 저장
        self.append_to_pdf(temp_pdf_path, answer)

        # 원래 파일을 교체
        shutil.move(temp_pdf_path, pdf_path)

        # JSON에서 해당 질문 삭제
        questions.remove(question)
        with open(UNANSWERED_QUESTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=4)

        QtWidgets.QMessageBox.information(self, "완료", "답변이 PDF에 저장되었습니다.")

    def translate_to_english(self, text):
        """한글을 영어로 번역 (translate 라이브러리 사용)"""
        translator = Translator(to_lang="en", from_lang="ko")
        translation = translator.translate(text)
        return translation

    def append_to_pdf(self, pdf_path, answer):
        """기존 PDF의 마지막 페이지에 한글 답변을 입력하고, 번역된 영어 텍스트를 추가 (PyMuPDF + FPDF 조합)"""
        try:
            temp_pdf_path = pdf_path + "_temp.pdf"  # 임시 파일 생성

            # ✅ 기존 PDF 열기
            if os.path.exists(pdf_path):
                doc = fitz.open(pdf_path)  # 기존 PDF 열기
            else:
                doc = fitz.open()  # 새 PDF 생성
                doc.new_page()  # 첫 번째 페이지 생성

            # ✅ 마지막 페이지 선택
            last_page = doc[-1]

            # ✅ 기존 페이지의 마지막 텍스트 위치 찾기
            last_y = 50  # 기본 Y 위치
            text_blocks = last_page.get_text("blocks")  # 페이지에서 텍스트 블록 가져오기

            if text_blocks:
                last_y = max(block[3] for block in text_blocks) + 15  # 마지막 텍스트 위치 + 여백 추가

            # ✅ 페이지 높이를 초과하면 새 페이지 생성
            if last_y > last_page.rect.height - 50:
                last_page = doc.new_page()
                last_y = 50  # 새로운 페이지에서 시작 위치 초기화

            # ✅ 기존 페이지 하단에 번역된 텍스트 추가 (PyMuPDF는 한글을 지원하지 않음)
            last_page.insert_text((50, last_y), self.translate_to_english(answer), fontsize=12, fontname="helv")  # 기본 폰트 사용

            # ✅ 수정된 PDF 저장 (기존 PDF 유지)
            doc.save(temp_pdf_path)
            doc.close()

            # ✅ 기존 파일 삭제 후 임시 파일을 원본으로 변경
            os.remove(pdf_path)
            shutil.move(temp_pdf_path, pdf_path)

            QtWidgets.QMessageBox.information(self, "완료", f"번역된 텍스트가 PDF의 마지막 페이지에 추가되었습니다: {pdf_path}")

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "오류", f"PDF 저장 중 오류 발생: {str(e)}")

    def clear_unanswered_questions(self):
        """미응답 질문 목록을 초기화"""
        if os.path.exists(UNANSWERED_QUESTIONS_FILE):
            os.remove(UNANSWERED_QUESTIONS_FILE)  # JSON 파일 삭제

        self.question_list.clear()
        QtWidgets.QMessageBox.information(self, "완료", "미응답 질문 목록이 초기화되었습니다.")

    def show_unanswered_questions(self):
        """저장된 미응답 질문을 UI에 표시"""
        if not os.path.exists(UNANSWERED_QUESTIONS_FILE):
            QtWidgets.QMessageBox.warning(self, "오류", "저장된 미응답 질문이 없습니다.")
            return

        with open(UNANSWERED_QUESTIONS_FILE, "r", encoding="utf-8") as f:
            questions = json.load(f)

        if not questions:
            QtWidgets.QMessageBox.information(self, "알림", "기록할 미응답 질문이 없습니다.")
            return

        # 다이얼로그 생성
        dialog = QDialog(self)
        dialog.setWindowTitle("미응답 질문 목록")
        dialog.setGeometry(300, 300, 500, 400)

        layout = QVBoxLayout()

        # 질문 목록 리스트
        self.question_list = QListWidget()
        self.question_list.addItems(questions)
        layout.addWidget(self.question_list)

        # 모든 질문 삭제 버튼
        clear_button = QPushButton("모든 질문 삭제")
        clear_button.setStyleSheet("background-color: #ff0000; color: white; font-size: 16px;")
        clear_button.clicked.connect(self.clear_unanswered_questions)
        layout.addWidget(clear_button)

        dialog.setLayout(layout)
        self.unanswered_dialog = dialog
        self.unanswered_dialog.show()

    # 🟢 창 보이기 (트레이 아이콘에서 선택 시 실행)
    def show_window(self):
        self.showNormal()
        self.activateWindow()

    # 🟢 트레이 아이콘 클릭 시 동작
    def tray_icon_clicked(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    # 🟢 창 닫기 이벤트 (트레이로 최소화)
    
    # 🟢 종료 버튼 클릭 시 실행
    def exit_app(self):
        self.tray_icon.hide()
        sys.exit()

    def send_to_one(self):

        thread = threading.Thread(target=send_to_one_tide, args=(self,), daemon=True)
        thread.start()

    def check_if_pressed_today(self):
        """
        오늘 날짜(YYYY-MM-DD)를 포함하는 기록이 있는지 로그 파일을 뒤져 확인.
        있으면 True, 없으면 False
        """
        today_str = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", encoding="utf-8") as f:
                pass  # 내용 없이 새 파일만 생성
            return False
        
        with open(self.log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # 뒤에서부터 찾아도 되고, 순서대로 찾아도 됨
            for line in reversed(lines):
                if f"[{today_str} " in line:
                    return True
        return False
    
    def add_log(self, message):
        """
        예시로 오늘 날짜와 함께 로그를 추가하는 메서드
        """
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

    def tide_check_time(self):
        """매분마다 시간 확인하여 9시에 버튼 자동 클릭, 10시에 로그 확인 후 미기록 시 경고"""
        current_time = QTime.currentTime().toString("HH:mm")
        
        # 매일 9시 정각에 버튼 자동 클릭
        if current_time == "09:00":
            self.tide_information_button.click()
            self.add_log("물때 시간표 보내기 완료")
        
        # 10시에 로그 확인 후 만약 오늘 날짜 기록이 없다면 경고 메시지
        elif current_time == "10:00":
            if not self.check_if_pressed_today():
                self.show_warning()

    def show_warning(self):
        """오늘 날짜 기록이 없을 때 경고 메시지 박스 표시"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("경고")
        msg.setText("오늘 9시에 물때시간표를 고객님들께 보내지 못했습니다.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def tide_information(self):
        """아침 9시마다 당일 예약 손님들에게 물때 시간표 자동 보내기 기능"""
        # 인스타그램 답변 자동 댓글 기능 추가
        thread = threading.Thread(target=tide_message , args=(self,), daemon=True )
        thread.start()

    def instagram_reply(self, event):
        """인스타그램 답변 자동 댓글 기능"""
        # 인스타그램 답변 자동 댓글 기능 추가
        thread = threading.Thread(target=instagram_process, args=(self,), daemon=True )
        thread.start()

    def load_rooms(self):
        """Load rooms from the JSON file."""
        if not os.path.exists(ROOMS_FILE):
            default_rooms = ["A201", "A202", "B501", "B502", "B503", "B601", "B602", "B603", "사랑채", "C02", "C03", "C04", "C05", "별채"]
            self.save_rooms(default_rooms)
            return default_rooms

        with open(ROOMS_FILE, "r", encoding="utf-8") as file:
            return json.load(file).get("rooms", [])

    def save_rooms(self, rooms):
        """Save rooms to the JSON file."""
        with open(ROOMS_FILE, "w", encoding="utf-8") as file:
            json.dump({"rooms": rooms}, file, ensure_ascii=False, indent=4)

    def show_room_management(self):
        """Show a dialog for managing rooms."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("객실 관리")
        dialog.setGeometry(200, 200, 400, 300)

        layout = QtWidgets.QVBoxLayout()

        # 방 목록 표시
        room_list_widget = QtWidgets.QListWidget()
        room_list_widget.addItems(self.rooms)
        layout.addWidget(room_list_widget)

        # 방 추가 입력 필드
        room_input = QtWidgets.QLineEdit()
        room_input.setPlaceholderText("추가할 방 번호를 입력하세요")
        layout.addWidget(room_input)

        # 버튼 레이아웃
        button_layout = QtWidgets.QHBoxLayout()

        # 방 추가 버튼
        add_button = QtWidgets.QPushButton("추가")
        add_button.clicked.connect(lambda: self.add_room(room_input, room_list_widget))
        button_layout.addWidget(add_button)

        # 방 삭제 버튼
        remove_button = QtWidgets.QPushButton("삭제")
        remove_button.clicked.connect(lambda: self.remove_room(room_list_widget))
        button_layout.addWidget(remove_button)

        # 저장 버튼
        save_button = QtWidgets.QPushButton("저장")
        save_button.clicked.connect(lambda: self.save_rooms_dialog(dialog, room_list_widget))
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.exec_()

    def add_room(self, room_input, room_list_widget):
        """Add a room to the list."""
        new_room = room_input.text().strip()
        if not new_room:
            QtWidgets.QMessageBox.warning(self, "입력 오류", "방 번호를 입력하세요.")
            return
        if new_room in self.rooms:
            QtWidgets.QMessageBox.warning(self, "중복 오류", "이미 존재하는 방 번호입니다.")
            return

        self.rooms.append(new_room)
        room_list_widget.addItem(new_room)
        room_input.clear()

    def remove_room(self, room_list_widget):
        """Remove the selected room from the list."""
        selected_items = room_list_widget.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "선택 오류", "삭제할 방 번호를 선택하세요.")
            return

        for item in selected_items:
            self.rooms.remove(item.text())
            room_list_widget.takeItem(room_list_widget.row(item))

    def save_rooms_dialog(self, dialog, room_list_widget):
        """Save rooms and close the dialog."""
        self.rooms = [room_list_widget.item(i).text() for i in range(room_list_widget.count())]
        self.save_rooms(self.rooms)
        QtWidgets.QMessageBox.information(self, "저장 완료", "방 목록이 저장되었습니다.")
        dialog.close()

    def load_checkbox_state_remember(self):
        login_info_path = os.path.join(JSON_FOLDER, "login_info.json")
        if os.path.exists(login_info_path):
            with open(login_info_path, "r") as f:
                login_info = json.load(f)
                self.remember_checkbox.setChecked(True)  # 기억하기 체크박스 체크
                self.load_login_info()  # 저장된 로그인 정보 불러오기
        else:
            self.remember_checkbox.setChecked(False)  # 체크박스 초기화

    def remember_checkbox_state_changed(self):
        login_info_path = os.path.join(JSON_FOLDER, "login_info.json")
        if self.remember_checkbox.isChecked():
            self.save_login_info()  # 로그인 정보 저장
        else:
            if os.path.exists(login_info_path):
                os.remove(login_info_path)  # 로그인 정보 파일 삭제


    def save_login_info(self):
        """로그인 정보를 저장."""
        if self.remember_checkbox.isChecked():
            login_data = {
                "naver_id": self.naver_id_input.text(),
                "naver_pw": self.naver_pw_input.text(),
                "naver_no1": self.naver_number_input.text(),
                "naver_no2": self.naver_number_input2.text(),
                "review_no1": self.review_input.text(),
                "review_no2": self.review_input2.text(),
                "ddnayo_id": self.ddnayo_id_input.text(),
                "ddnayo_pw": self.ddnayo_id_input2.text(),
                "ddnayo_no": self.ddnayo_number_input2.text(),
            }
            login_info_path = os.path.join(JSON_FOLDER, "login_info.json")
            with open(login_info_path, "w", encoding="utf-8") as file:
                json.dump(login_data, file)

    def load_login_info(self):
        """로그인 정보를 로드."""
        login_info_path = os.path.join(JSON_FOLDER, "login_info.json")
        if os.path.exists(login_info_path):
            with open(login_info_path, "r", encoding="utf-8") as file:
                login_data = json.load(file)
                self.naver_id_input.setText(login_data.get("naver_id", ""))
                self.naver_pw_input.setText(login_data.get("naver_pw", ""))
                self.naver_number_input.setText(login_data.get("naver_no1", ""))
                self.naver_number_input2.setText(login_data.get("naver_no2", ""))
                self.review_input.setText(login_data.get("review_no1", ""))
                self.review_input2.setText(login_data.get("review_no2", ""))
                self.ddnayo_id_input.setText(login_data.get("ddnayo_id", ""))
                self.ddnayo_id_input2.setText(login_data.get("ddnayo_pw", ""))
                self.ddnayo_number_input2.setText(login_data.get("ddnayo_no", ""))
   
           
    def extra_function(self):
        
        thread = threading.Thread(target=ddnayo_whole_res, args=(self,), daemon=True )
        thread.start()
        

    def show_version(self):
        QMessageBox.information(self, "버전 정보", f"현재 버전: {CURRENT_VERSION}")

    def check_for_updates(self):
        try:
            # 로컬 업데이트 정보를 먼저 확인
            if os.path.exists(LOCAL_VERSION_FILE):
                with open(LOCAL_VERSION_FILE, "r") as f:
                    local_version_info = json.load(f)
                    local_version = local_version_info.get("version", CURRENT_VERSION)
            else:
                local_version = CURRENT_VERSION  # 로컬 버전 정보가 없으면 기본 버전 사용

            response = requests.get(UPDATE_SERVER_URL)
            if response.status_code == 200:
                remote_version_info = response.json()
                remote_version = remote_version_info["version"]
                download_url = remote_version_info["download_url"]

                local_version = CURRENT_VERSION

                if self.is_new_version_available(local_version, remote_version):
                    reply = QMessageBox.question(
                        self,
                        "업데이트 확인",
                        f"새로운 버전 {remote_version}이(가) 이용 가능합니다. 업데이트하시겠습니까?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.download_update(download_url)
                else:
                    QMessageBox.information(self, "업데이트 확인", "최신 버전이 설치되어 있습니다.")
        except Exception as e:
            QMessageBox.warning(self, "업데이트 오류", f"업데이트 확인 중 오류 발생: {str(e)}")


    def is_new_version_available(self, local_version, remote_version):
        return tuple(map(int, remote_version.split("."))) > tuple(map(int, local_version.split(".")))

    def download_update(self, download_url):
        try:
            response = requests.get(download_url, stream=True)
            with open("update_setup.exe", 'wb') as file:
                shutil.copyfileobj(response.raw, file)
            QMessageBox.information(self, "업데이트 완료", "업데이트 파일이 다운로드되었습니다. 설치 후 프로그램을 다시 실행하세요.")
        except Exception as e:
            QMessageBox.critical(self, "업데이트 오류", f"업데이트 다운로드 중 오류 발생: {str(e)}")


    def open_file_dialog(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "PDF 파일 선택", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if file_path:
            self.selected_pdf_path = file_path
            self.load_pdf_content()
            self.save_pdf_path()  # 선택한 PDF 파일 경로 저장

    def load_pdf_content(self):
        if not self.selected_pdf_path:
            QtWidgets.QMessageBox.warning(self, "경고", "파일이 선택되지 않았습니다.")
            return

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(self.selected_pdf_path)
            context = ""
            for page in doc:
                text = page.get_text()
                context += text
            with open(EXTRA_PROMPT_FILE, 'r', encoding='utf-8') as file:
                content = file.read()
            self.system_message = f"{content}" + context
            self.pdf_status_label.setText(f"불러온 파일: {self.selected_pdf_path}")
            QtWidgets.QMessageBox.information(self, "성공", "PDF 파일을 성공적으로 불러왔습니다.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"파일 로드 중 오류 발생: {str(e)}")

    def save_pdf_path(self):
        with open(PDF_SETTINGS_FILE, 'w') as file:
            json.dump({"pdf_path": self.selected_pdf_path}, file)

    def load_saved_pdf(self):
        if os.path.exists(PDF_SETTINGS_FILE):
            with open(PDF_SETTINGS_FILE, 'r') as file:
                data = json.load(file)
                if "pdf_path" in data:
                    self.selected_pdf_path = data["pdf_path"]
                    self.load_pdf_content()

    def call_extra_function(self):
        # 엑스트라 버튼을 눌렀을 때 실행되는 함수
        try:
            # 엑스트라용 프롬프트 창 띄우기
            self.extra_prompt_window = QtWidgets.QDialog(self)
            self.extra_prompt_window.setWindowTitle("엑스트라 프롬프트 입력창")
            self.extra_prompt_window.setGeometry(self.geometry().right(), 100, 800, 800)

            # 레이아웃 생성 (기본 레이아웃)
            main_layout = QtWidgets.QVBoxLayout()

            # 텍스트 편집기 추가
            self.extra_prompt_text_edit = QtWidgets.QTextEdit(self.extra_prompt_window)
            self.extra_prompt_text_edit.setGeometry(10, 10, 780, 680)
            self.extra_prompt_text_edit.setStyleSheet("background-color: #f8f9fa; border: 1px solid #ccc; font-size: 20px;")
            self.extra_prompt_text_edit.setReadOnly(False)
            main_layout.addWidget(self.extra_prompt_text_edit)

            # 버튼 레이아웃 생성
            extra_button_layout = QtWidgets.QHBoxLayout()

            # 저장 버튼 추가
            save_button = QtWidgets.QPushButton("저장", self.extra_prompt_window)
            save_button.setStyleSheet("background-color: #28a745; color: white; font-size: 16px; padding: 1px; border-radius: 5px;")
            save_button.clicked.connect(self.save_extra_prompt_content)
            extra_button_layout.addWidget(save_button)

            # 취소 버튼 추가
            cancel_button = QtWidgets.QPushButton("취소", self.extra_prompt_window)
            cancel_button.setStyleSheet("background-color: #dc3545; color: white; font-size: 16px; padding: 1px; border-radius: 5px;")
            cancel_button.clicked.connect(self.cancel_extra_prompt_content)
            extra_button_layout.addWidget(cancel_button)

            # 버튼들이 가운데 정렬
            extra_button_layout.setAlignment(QtCore.Qt.AlignCenter)

            # 버튼들의 크기 설정: 각 버튼을 창의 절반 크기로 설정
            save_button.setFixedSize(self.extra_prompt_window.width() // 2 - 20, 50)  # 버튼 크기 늘림
            cancel_button.setFixedSize(self.extra_prompt_window.width() // 2 - 20, 50)  # 버튼 크기 늘림

            # 레이아웃을 창에 추가
            extra_layout_widget = QtWidgets.QWidget(self.extra_prompt_window)
            extra_layout_widget.setLayout(extra_button_layout)
            extra_layout_widget.setGeometry(0, 700, 800, 100)  # 버튼 위치와 크기 설정

            # 라디오 버튼을 설정한 레이아웃을 창에 추가
            extra_layout_widget = QtWidgets.QWidget(self.extra_prompt_window)
            extra_layout_widget.setLayout(main_layout)
            extra_layout_widget.setGeometry(0, 0, 800, 600)  # 텍스트 편집기와 라디오 버튼을 포함한 레이아웃 설정

            # 엑스트라 프롬프트 창에서 파일 내용 불러오기
            self.load_extra_prompt_content()

            self.extra_prompt_window.show()
            self.chat_status.append("엑스트라 프롬프트창에 내용을 작성해주세요!" + "\n")
            selected_option = self.get_selected_radio_button()
            self.chat_status.append(f"선택된 옵션: {selected_option}")
        

        except Exception as e:
            self.chat_status.append(f"Error: {str(e)}")

    def reservation_message(self):
        dialog = MultiNumberInputDialog()
        if dialog.exec_():  # 다이얼로그 실행
            pass

    
    def get_selected_radio_button(self):
        # 선택된 라디오 버튼을 확인
        selected_button = self.radio_button_group.checkedButton()
    
        if selected_button:
            # 선택된 라디오 버튼의 텍스트를 가져옴
            selected_text = selected_button.text()
            return selected_text
        else:
            # 선택된 라디오 버튼이 없을 경우
            return None
        
    def save_extra_prompt_content(self):
        # 엑스트라 프롬프트 창에서 내용을 저장
        extra_prompt_content = self.extra_prompt_text_edit.toPlainText()
        with open(EXTRA_PROMPT_FILE, 'w', encoding='utf-8') as file:
            file.write(extra_prompt_content)
        self.chat_status.append(f"네이버톡 프롬프트 내용 저장됨: {extra_prompt_content}\n")
        self.extra_prompt_window.accept()

    def load_extra_prompt_content(self):
        # 엑스트라 프롬프트 내용 불러오기
        if os.path.exists(EXTRA_PROMPT_FILE):
            with open(EXTRA_PROMPT_FILE, 'r', encoding='utf-8') as file:
                content = file.read()
                self.extra_prompt_text_edit.setText(content)

    def cancel_extra_prompt_content(self):
        # 엑스트라 프롬프트 창에서 취소 버튼을 눌렀을 때
        self.extra_prompt_text_edit.clear()  # 입력창의 내용을 지움
        self.extra_prompt_window.reject()  # 창을 닫음

    def save_prompt_content(self):
        prompt_content = self.prompt_text_edit.toPlainText()
        with open(PROMPT_FILE, 'w', encoding='utf-8') as file:
            file.write(prompt_content)
        self.chat_status.append(f"입력한 내용 저장됨: {prompt_content}\n")
        self.prompt_window.accept()

    def load_prompt_content(self):
        if os.path.exists(PROMPT_FILE):
            with open(PROMPT_FILE, 'r',  encoding='utf-8') as file:
                content = file.read()
                self.prompt_text_edit.setText(content)

    def cancel_prompt_content(self):
        # 취소 버튼을 눌렀을 때 호출되는 함수
        self.prompt_text_edit.clear()  # 입력창의 내용을 지움
        self.prompt_window.reject()  # 창을 닫음

    def append_chat_status(self, message, color="black"):
        cursor = self.chat_status.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        fmt = QtGui.QTextCharFormat()

        # 외부에서 색상을 직접 지정하도록 추가
        if message.startswith("[ChatBot]"):
            fmt.setForeground(QtGui.QColor("blue"))
            fmt.setFontWeight(QtGui.QFont.Bold)
        elif message.startswith("[U S E R]"):
            fmt.setForeground(QtGui.QColor("red"))
            fmt.setFontWeight(QtGui.QFont.Bold)
        else:
            fmt.setForeground(QtGui.QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(message + "\n")

    def call_external_function(self):
        # 외부 함수 호출
        try:
            start_full_process(self)
            self.start_btn.setEnabled(False)
            self.chat_status.append("MyShop 채팅 시작!"+"\n")
        except Exception as e:
            self.chat_status.append(f"Error: {str(e)}")

    def call_review_function(self):
        # 리뷰 기능 호출
        try:
            threading.Thread(target=start_review_process, args=(self,)).start()
            self.review_btn.setEnabled(False)
            self.chat_status.append("리뷰 프로세스 시작!"+"\n")
        except Exception as e:
            self.chat_status.append(f"Error: {str(e)}")

    def call_prompt_function(self):
        # 프롬프트 버튼을 눌렀을 때 실행되는 함수
        try:
            # 프롬프트 창 띄우기
            self.prompt_window.show()

            # 라디오 버튼에서 선택된 내용 가져오기
            selected_option = self.get_selected_radio_button()
            self.chat_status.append(f"선택된 옵션: {selected_option}")

        except Exception as e:
            self.chat_status.append(f"Error: {str(e)}")
       

    def get_credentials(self):
        # 자동 로그인 체크 확인
        self.load_login_info()
        naver_id = self.naver_id_input.text()
        naver_pw = self.naver_pw_input.text()
        naver_no1 = self.naver_number_input.text()
        naver_no2 = self.naver_number_input2.text()
        rv_no1 = self.review_input.text()
        rv_no2 = self.review_input2.text()
        dn_id = self.ddnayo_id_input.text()
        dn_pw = self.ddnayo_id_input2.text()
        dn_no = self.ddnayo_number_input2.text()

        return naver_id, naver_pw, naver_no1, naver_no2, rv_no1, rv_no2, dn_id, dn_pw, dn_no 
    
    def save_checkbox_state(self):
        """체크박스 상태를 저장."""
        state_data = {
            "remember": self.remember_checkbox.isChecked(),
            "auto_login": self.auto_login_checkbox.isChecked()
        }
        with open(CHECKBOX_STATE_FILE, 'w', encoding='utf-8') as file:
            json.dump(state_data, file)

    def load_checkbox_state(self):
        """체크박스 상태를 로드."""
        if os.path.exists(CHECKBOX_STATE_FILE):
            with open(CHECKBOX_STATE_FILE, 'r', encoding='utf-8') as file:
                state = json.load(file)
                self.remember_checkbox.setChecked(state.get("remember", False))
                self.auto_login_checkbox.setChecked(state.get("auto_login", False))
        else:
            # 파일이 없으면 기본값 설정
            self.remember_checkbox.setChecked(False)
            self.auto_login_checkbox.setChecked(False)

    def load_radio_button_state(self):
        # 저장된 라디오 버튼 상태 불러오기
        settings = QSettings(SETTINGS_FILE, QSettings.IniFormat)
        last_selected_option = settings.value("last_selected_option", "네이버예약 가능업소")  # 기본값은 "네이버예약 가능업소"

        # 라디오 버튼을 마지막에 선택된 값으로 설정
        if last_selected_option == "네이버예약 가능업소":
            self.radio_button_1.setChecked(True)
        elif last_selected_option == "네이버예약 불가능업소":
            self.radio_button_2.setChecked(True)

    def save_radio_button_state(self):
        # 라디오 버튼의 선택 상태를 저장
        selected_option = self.get_selected_radio_button()
        if selected_option:
            settings = QSettings(SETTINGS_FILE, QSettings.IniFormat)
            settings.setValue("last_selected_option", selected_option)

    def closeEvent(self, event):
        """창 닫을 때 동작: '아니오' 선택 시 트레이로 최소화"""
        
        self.save_login_info()
        reply = QtWidgets.QMessageBox.question(
            self,
            'Exit Application',
            'Are you sure you want to exit?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        self.save_radio_button_state()

        if reply == QtWidgets.QMessageBox.Yes:
            try:
                self.running = False
                talk_chatbot.driver.quit()
                review_bot.review_driver.quit()
                ddnayo_scraper.scraping_driver.quit()
                
                for thread in self.threads:
                    thread.join()  # 모든 스레드가 종료될 때까지 대기

                self.tray_icon.hide()  # 트레이 아이콘도 숨김
                super().closeEvent(event)  # 기본 동작 수행

            except AttributeError:
                pass
            event.accept()

        elif reply == QtWidgets.QMessageBox.No:
            # "아니오" 선택 시 창을 최소화하고 트레이로 이동
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "네이버톡톡 챗봇",
                "프로그램이 트레이에서 실행 중입니다.",
                QSystemTrayIcon.Information,
                2000
            )
        
        else:
            # "취소" 선택 시 아무 동작 없이 창 유지
            event.ignore()



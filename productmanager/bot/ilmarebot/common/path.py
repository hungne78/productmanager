import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

JSON_FOLDER = os.path.join(BASE_DIR, "json")

# Ensure the folder exists
if not os.path.exists(JSON_FOLDER):
    os.makedirs(JSON_FOLDER)

# CREDENTIALS_FILE = os.path.join(JSON_FOLDER, "credentials.json")
# REVIEW_CREDENTIALS_FILE = os.path.join(JSON_FOLDER, "review_credentials.json")
LOGIN_INFO = os.path.join(JSON_FOLDER, "login_info.json") # 로그인 정보 저장 파일
PROMPT_FILE = os.path.join(JSON_FOLDER, "prompt_content.txt") # 네이버톡 프롬프트 파일
EXTRA_PROMPT_FILE = os.path.join(JSON_FOLDER, "extra_prompt_content.txt") #네이버 리뷰 댓글 프롬프트 파일
SETTINGS_FILE = "settings.ini"  # 설정 파일 경로
PDF_SETTINGS_FILE = os.path.join(JSON_FOLDER, "pdf_settings.json")  # PDF 상태 저장 파일
CHECKBOX_STATE_FILE = os.path.join(JSON_FOLDER, "checkbox_state.json") # 체크박스 상태 저장 파일
UPDATE_SERVER_URL = "https://hungne78.synology.me/version.json" # 업데이트 서버 URL
LOCAL_VERSION_FILE = os.path.join(JSON_FOLDER, "local_version.json") # 로컬 버전 파일
ROOMS_FILE = os.path.join(JSON_FOLDER, "rooms.json")
CURRENT_VERSION = "1.0.1"  # 현재 버전 정보
log_path = "tide_process_log.txt"

UNANSWERED_QUESTIONS_FILE = os.path.join(JSON_FOLDER, "unanswered_questions.json")
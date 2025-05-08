from PyQt5 import QtWidgets
from PyQt5.QtCore import QEvent
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, UnexpectedAlertPresentException
from selenium.webdriver.common.keys import Keys
from ilmarebot.common.path import EXTRA_PROMPT_FILE
from selenium import webdriver
import threading
import time
import re


from ilmarebot.common.utils import remove_emoji, remove_non_bmp
from ilmarebot.ui.chatbot import ChatBot
pre_href=""
driver = None #네이버톡 드라이버
running_flag = True  # 루프 실행 여부 제어 플래그

consultation_running = False  # 상담 실행 여부

def login_to_site(driver,ui,user_id,user_pw):  #네이버 로그인 함수수
    username = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'id')))
    pw = driver.find_element(By.NAME, 'pw')
    driver.execute_script("arguments[0].value = arguments[1]", username, user_id)
    time.sleep(2)
    driver.execute_script("arguments[0].value = arguments[1]", pw, user_pw)
    time.sleep(2)
    
    driver.find_element(By.CLASS_NAME, "btn_login").click()
    ui.system_status.append("[INFO] Login attempt completed.")
    time.sleep(5)

def initialize_driver():
    """네이버톡 드리이버."""
    global driver

    chrome_options = webdriver.ChromeOptions()
    
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

def start_consultation(ui): #네이버톡 상담 시작 함수
    
    global consultation_running
    
    consultation_running = True
    
    ui.system_status.append("[INFO] Starting consultation...")
   
    if ui.system_message:
        system_message = ui.system_message
    else:
        with open(EXTRA_PROMPT_FILE, 'r', encoding='utf-8') as file:
            content = file.read() 
        # system_message = f"{content}"

    chatbot_mini = ChatBot("gpt-4o-mini-2024-07-18", system_message)
    chatbot_full = ChatBot("gpt-4o", system_message)
    # instance.system_status.append(system_message)

    def is_date_related_query(user_input):   #날짜 관련 쿼리인지 확인하는 함수(중요한 문맥일경우 GTP-4O를 시용하기 위해)
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',   # Matches formats like 12/31/2024
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',     # Matches formats like 2024-12-31
            r'\b\d{1,2}월\s?\d{1,2}일\b',      # Matches formats like 12월 31일
            r'\b(오늘|내일|어제|요일)\b',       # Matches words like today, tomorrow, yesterday, day of the week
            r'\b(몇\s?일|며칠|날짜|요일)\b',    # Matches phrases like "what date", "which day"
            r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b', # Matches formats like 25.01.28 or 25.1.2028
            r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',   # Matches formats like 25-01-28 or 25-1-2028
            r'\b\d{1,2}\s\w+\s\d{4}\b',       # Matches formats like 25 January 2028
            r'\b\w+\s\d{1,2},\s\d{4}\b',       # Matches formats like January 25, 2028
            r'\b(비용|금액|추가|기준인원|추가인원|예약)\b'           # Matches words like "비용", "금액", "추가"
        ]
        for pattern in date_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return True
        return False
    

    iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "iframe"))
    )
    driver.switch_to.frame(iframe)
    
     
    def consultation_loop(is_running, driver, instance):
        global pre_href
        global last_click_time

        last_click_time = time.time()

        ### (수정됨) AI가 응답을 보낸 뒤, 다음 'user'(실제 사용자) 메시지에서 이미지를 감지할지 여부
        check_next_user_image = False

        try:
            while is_running():
                user = ""
                current_time = time.time()
                try:
                    if not driver.session_id:
                        ui.system_status.append("Driver session is no longer valid. Exiting loop.")
                        break

                    wait = WebDriverWait(driver, 10)
                    chat_result_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "chat_result")))

                    # --- 4시간마다 재실행 로직 ---
                    if current_time - last_click_time >= 14400:
                        try:
                            if instance and instance.start_btn:
                                instance.running = False
                                instance.save_login_info()
                                driver.quit()
                                instance.start_btn.setEnabled(True)
                                instance.start_btn.click()
                                ui.system_status.append("Naver Restart.")
                                last_click_time = current_time
                                return
                        except Exception as e:
                            ui.system_status.append(f"Error clicking Start button: {e}")
                            return

                    while True:
                        try:
                            wait1 = WebDriverWait(chat_result_div, 10)
                            ul_element = wait1.until(
                                EC.presence_of_element_located((By.CLASS_NAME, "list_chat_result.scroll_vertical"))
                            )
                            break
                        except StaleElementReferenceException:
                            continue

                    li_elements = ul_element.find_elements(By.CSS_SELECTOR, "li.item_chat_result")
                    ui.system_status.append(f"Found {len(li_elements)} list items.")

                    if len(li_elements):
                        for li_item in li_elements:
                            try:
                                anchor = WebDriverWait(li_item, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, "inner"))
                                )
                                href = anchor.get_attribute("href")
                                if href:
                                    ui.system_status.append(f"Clicking link: {href}")
                                    if pre_href == href:
                                        pass
                                    else:
                                        user_input = ""

                                    pre_href = href
                                    driver.get(href)
                                    time.sleep(2)

                            except UnexpectedAlertPresentException:
                                alert = driver.switch_to.alert
                                alert.accept()
                                continue
                            except Exception as e:
                                ui.system_status.append(f"Error processing list item: {e}")

                            time.sleep(1)

                            content_div = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '#content.column_top.chat_detail'))
                            )
                            message_section = content_div.find_element(By.CLASS_NAME, "message_section._chatWindow")
                            chat_reverse = message_section.find_element(By.CLASS_NAME, "chat_reverse")
                            group_message_balloon = chat_reverse.find_element(By.CLASS_NAME, "group_message_balloon")

                            li_all = group_message_balloon.find_elements(
                                By.CSS_SELECTOR, '[class^="new_message_balloon_area"]'
                            )

                            li_all = WebDriverWait(driver, 10).until(
                                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li'))
                            )

                            # (중요) partner = AI, user = 실제 유저
                            # Step 1: 최근 AI 메시지(= data-sender="partner") 찾기
                            last_ai_li = None
                            for li_elem in li_all:
                                if li_elem.get_attribute("data-sender") == "partner":  # AI
                                    last_ai_li = li_elem

                            # Step 2: AI가 메시지를 보냈다면, 그 이후(= partner 다음)에 있는 user 메시지를 추출
                            if last_ai_li:
                                found_partner = False
                                for li_elem in li_all:
                                    if li_elem == last_ai_li:
                                        found_partner = True
                                    elif found_partner and li_elem.get_attribute("data-sender") == "partner":
                                        # AI가 또 나왔으면 무시(원하면 break or 계속)
                                        # 여기선 그냥 continue
                                        continue
                                    elif found_partner and li_elem.get_attribute("data-sender") == "user":
                                        try:
                                            # user(실제 유저)가 보낸 텍스트 추출
                                            balloon_user = li_elem.find_element(By.CLASS_NAME, "message_balloon.card_message.type_text")
                                            p_elems = balloon_user.find_elements(By.TAG_NAME, "p")

                                            for p in p_elems:
                                                ui.system_status.append(f"[UserMsg] {p.text}")
                                                user += remove_non_bmp(remove_emoji(p.text))

                                        except Exception as e:
                                            ui.system_status.append("Image Error: 이미지 이해못함.")

                                user_input = user
                                ui.append_chat_status("[User]" + user)

                                # 이제 AI가 새 답변 만듦 (AI = partner)
                                if is_date_related_query(user_input):
                                    response = chatbot_full.get_response(user_input)
                                else:
                                    response = chatbot_mini.get_response(user_input)

                                # AI 답장 전송
                                try:
                                    textarea = WebDriverWait(driver, 10).until(
                                        EC.visibility_of_element_located((By.CLASS_NAME, 'chat_write_from'))
                                    )
                                    sanitized = remove_non_bmp(remove_emoji(response))
                                    message_parts = sanitized.split('\n')
                                    textarea.clear()

                                    for part in message_parts:
                                        textarea.send_keys(part)
                                        textarea.send_keys(Keys.SHIFT, Keys.ENTER)

                                except Exception as e:
                                    ui.system_status.append(f"An error occurred: {e}")

                                try:
                                    button = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.CLASS_NAME, 'chat_write_btn'))
                                    )
                                    button.click()
                                except Exception as e:
                                    ui.system_status.append(f"An error occurred: {e}")

                                ui.append_chat_status("[AI]" + (response if response else "응답을 생성할 수 없습니다."))

                                # (수정됨) AI가 답변(=partner 메시지)했으니,
                                # 그 다음에 올 user 메시지(=실제 유저)에서 이미지를 감지하도록 플래그 세팅
                                check_next_user_image = True

                                # 기존 상담 완료 버튼 로직 (원본 코드 유지)
                                try:
                                    done_button = driver.find_element(By.XPATH, '//*[@id="content"]/div/div[1]/div/div[3]/button')
                                    done_button.click()
                                    driver.execute_script("window.location.reload();")
                                except Exception as e:
                                    ui.system_status.append(f"An error occurred: {e}")

                                # 이제 이후 루프(또는 지금 로직이 한 번 끝난 뒤)에서
                                # check_next_user_image를 확인해 user 메시지가 이미지면 처리

                            # (수정됨) 만약 check_next_user_image가 True라면,
                            # 지금 새로 들어온 user 메시지(=data-sender="user")를 확인해 이미지가 있는지 검사
                            
                            if check_next_user_image:
                                time.sleep(1)
                                message_section = driver.find_element(By.CLASS_NAME, "message_section._chatWindow")
                                chat_reverse = message_section.find_element(By.CLASS_NAME, "chat_reverse")
                                group_message_balloon = chat_reverse.find_element(By.CLASS_NAME, "group_message_balloon")

                                user_lis = group_message_balloon.find_elements(
                                    By.CSS_SELECTOR, '[class^="new_message_balloon_area"][data-sender="user"]'
                                )
                                li_all = group_message_balloon.find_elements(By.CSS_SELECTOR, 'li')

                                # 1) '마지막 파트너(=AI) 메시지'의 인덱스를 찾는다.
                                last_partner_index = -1
                                for i, li_elem in enumerate(li_all):
                                    if li_elem.get_attribute("data-sender") == "partner":
                                        last_partner_index = i
                                
                                image_found = False
                                # 2) 그 인덱스보다 '뒤'에 있는 li만 확인한다 → li_all[last_partner_index+1:]
                                for li_elem in li_all[last_partner_index+1:]:
                                    if li_elem.get_attribute("data-sender") == "user":
                                        # 이건 새로운 user 메시지
                                        imgs = li_elem.find_elements(By.TAG_NAME, "img")
                                        if imgs:
                                            # 이미지 감지!

                                            ui.system_status.append("📷 사용자(user) 메시지에 이미지 감지!")
                                            image_found = True
                                            break
                                    

                                if image_found:
                                    try:
                                        consultation_done_button = driver.find_element(
                                            By.XPATH, '//*[@id="content"]/div/div[1]/div/div[3]/button'
                                        )
                                        consultation_done_button.click()
                                        driver.execute_script("window.location.reload();")
                                        ui.system_status.append("✅상담 완료 버튼 클릭 완료!")
                                    except Exception as e:
                                        ui.system_status.append(f"Error clicking 상담 완료 버튼: {e}")

                                # 검사 끝났으면 플래그 off
                                check_next_user_image = False

                except TimeoutException:
                    pass
                except KeyboardInterrupt:
                    ui.system_status.append("Stopping the script.")
                    instance.running = False
                    driver.quit()

        finally:
            if driver:
                instance.running = False
                driver.quit()
                QtWidgets.QApplication.instance().postEvent(
                    ui.start_btn, QEvent(QEvent.EnabledChange)
                )
                ui.start_btn.setEnabled(True)
                ui.system_status.append("Driver closed safely.")



    # 스레드 시작
    thread = threading.Thread(target=consultation_loop, args=(lambda: running_flag, driver,  ui), daemon=True)
    thread.start()


# 네이버 톡 시작 프로세스
def start_full_process(ui):
    
    ui.system_status.append("[INFO] Starting the full process...")

    # get_credentials 함수 호출
    credentials = ui.get_credentials()
    if credentials is None:  # 입력 취소 또는 오류 처리
        ui.system_status.append("[ERROR] Credentials not provided.")
        return

    naver_id, naver_pw, naver_no1, naver_no2, rv_no1, rv_no2, dn_id, dn_pw, dn_no  = credentials  
    ui.system_status.append(f"[INFO] ID: {naver_id}, Password: {'*' * len(naver_pw)}")    

    ui.system_status.append("[INFO] Starting the full process...")

    def run_script():   #네이버 로그인
        try:
            
            initialize_driver()
            
            ui.system_status.append("[INFO] Chrome WebDriver initialized.")
            driver.get('https://naver.com')
            WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            ui.system_status.append("[INFO] Naver homepage loaded.")

            # Login process
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@class='MyView-module__link_login___HpHMW']")))
            login_button.click()
            ui.system_status.append("[INFO] Login button clicked.")

            login_to_site(driver,ui,naver_id,naver_pw)

            # 네이버톡 이동
            url2 = f"https://partner.talk.naver.com/web/accounts/{naver_no1}/chat"
            driver.get(url2)
            cookies = driver.get_cookies()

            #쿠키 저장 되는지 안되는지 모르겠음
            for cookie in cookies:
                driver.add_cookie(cookie)

            WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            ui.system_status.append("[INFO] Reservation management page loaded.")
            start_consultation(ui)

        except Exception as e:
            ui.system_status.append(f"[ERROR] {e}")

    threading.Thread(target=run_script).start()

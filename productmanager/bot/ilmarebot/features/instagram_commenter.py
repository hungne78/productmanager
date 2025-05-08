from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
import time
import random
import os

from ilmarebot.ui.review_chatbot import Review_ChatBot
from ilmarebot.common.utils import remove_emoji, remove_non_bmp

MAX_COMMENTS_PER_HOUR = 7  # ✅ 한 시간당 최대 7개 댓글만 허용
comment_count = 0
start_time = time.time()

def get_user_id_file(ui):
    """현재 Instagram 게시글 ID에 따른 사용자 기록 파일 경로 반환"""
    post_id = ui.instagram_input.text().strip()  # ✅ 현재 게시글 ID 가져오기
    return f"commented_users_{post_id}.txt"

def load_commented_users(ui):
    """현재 게시글 ID에 따른 기존에 댓글을 단 사용자 목록을 파일에서 불러옴"""
    user_id_file = get_user_id_file(ui)
    if not os.path.exists(user_id_file):
        return set()  # 파일이 없으면 빈 집합 반환
    with open(user_id_file, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f.readlines())

def save_commented_user(user_id, ui):
    """새로운 사용자 ID를 현재 게시글 파일에 추가"""
    user_id_file = get_user_id_file(ui)
    with open(user_id_file, "a", encoding="utf-8") as f:
        f.write(user_id + "\n")

def force_scroll_multiple(ui, times: int = 1):
    """ 특정 div 영역에서 휠 스크롤 실행 (동적 요소 변경 방지) """
    try:
        # ✅ 스크롤 대상 div가 변경되었는지 확인하고 다시 가져오기
        try:
            scroll_container = WebDriverWait(instagram_driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                    "div.x5yr21d.xw2csxc.x1odjw0f.x1n2onr6"))
            )
        except (StaleElementReferenceException, NoSuchElementException):
            ui.system_status.append("⚠ 스크롤 대상 div가 변경됨. 다시 찾는 중...")
            time.sleep(2)  # ✅ 약간의 대기 후 다시 찾기
            scroll_container = WebDriverWait(instagram_driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                    "div.x5yr21d.xw2csxc.x1odjw0f.x1n2onr6"))
            )

        prev_height = instagram_driver.execute_script("return arguments[0].scrollHeight", scroll_container)

        # ✅ `times` 만큼 반복하여 여러 번 스크롤
        for _ in range(2):
            # ✅ JavaScript를 사용하여 강제 스크롤 (기본 휠 이벤트가 작동하지 않을 경우 대비)
            instagram_driver.execute_script("arguments[0].scrollBy(0, 500);", scroll_container)
            time.sleep(3)  # ✅ 짧은 대기 시간 설정 (빠른 연속 스크롤)

            # ✅ 키보드 스크롤 추가 (`Keys.PAGE_DOWN`)
            instagram_driver.find_element(By.CSS_SELECTOR, 
                    "div.x5yr21d.xw2csxc.x1odjw0f.x1n2onr6").send_keys(Keys.PAGE_DOWN)
            time.sleep(3)

            # ✅ ActionChains 휠 스크롤 적용 (백업용)
            actions = ActionChains(instagram_driver)
            actions.move_to_element(scroll_container).scroll_by_amount(0, 500).perform()
            time.sleep(3)

        # ✅ 새로운 높이 확인
        new_height = instagram_driver.execute_script("return arguments[0].scrollHeight", scroll_container)

        if new_height > prev_height:
            ui.system_status.append(f"✅ {times}번 연속 스크롤 성공: 새로운 댓글이 로드됨.")
            return True  # ✅ 스크롤 성공 후 댓글 로드됨

        ui.system_status.append("⚠ 스크롤 후에도 새로운 댓글이 없음. 종료 시도 중...")
        return False  # ✅ 스크롤해도 새로운 댓글이 없으면 종료

    except Exception as e:
        ui.system_status.append(f"⚠ 스크롤 실행 중 오류 발생: {e}")
        return False
def human_typing(textarea_element, text, ui):
    """ 사람처럼 보이는 타이핑을 구현 (속도 랜덤화) """
    try:
        textarea_element.clear()  # ✅ 기존 입력값 제거
        time.sleep(random.uniform(0.5, 1.2))  # ✅ 첫 입력 전 랜덤 딜레이

        for char in text:
            textarea_element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))  # ✅ 랜덤 타이핑 속도 적용

            # ✅ 가끔 Backspace를 입력하여 사람이 입력하는 것처럼 보이게 함
            if random.random() < 0.1:  # 10% 확률로 백스페이스 입력
                textarea_element.send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.1, 0.3))
                textarea_element.send_keys(char)  # 다시 입력

        time.sleep(random.uniform(1.0, 2.0))  # ✅ 입력 후 랜덤 딜레이

    except Exception as e:
        ui.system_status.append(f"⚠ 타이핑 중 오류 발생: {e}")

# def wait_for_comment_box():
#     """ 댓글 입력창이 활성화될 때까지 기다리는 함수 """
#     try:
#         # ✅ 로딩 아이콘(`svg`)이 있으면 기다림
#         WebDriverWait(instagram_driver, 5).until_not(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='읽어들이는 중...']"))
#         )
#         ui.system_status.append("✅ 로딩 아이콘 사라짐. 댓글 입력 가능.")

#         # ✅ 댓글 입력창이 활성화될 때까지 대기
#         textarea_element = WebDriverWait(instagram_driver, 10).until(
#             EC.element_to_be_clickable((By.CSS_SELECTOR, 'textarea.x1i0vuye.xvbhtw8'))
#         )

#         # ✅ 스크롤 후 클릭하여 활성화
#         instagram_driver.execute_script("arguments[0].scrollIntoView();", textarea_element)
#         time.sleep(1)  # ✅ 스크롤 후 대기
#         textarea_element.click()  # ✅ 클릭하여 활성화

#         return textarea_element  # ✅ 활성화된 입력창 반환

#     except TimeoutException:
#         ui.system_status.append("⚠ 댓글 입력창이 활성화되지 않음.")
#         return None
#     except ElementClickInterceptedException:
#         ui.system_status.append("⚠ 다른 요소가 클릭을 가로막음. 다시 시도 중...")
#         return None

def submit_comment(res, ui):
    """ 게시 버튼 클릭 후 댓글 등록 완료 확인 및 최대 댓글 제한 적용 """
    global comment_count, start_time

    try:
        # ✅ 최대 댓글 제한 확인
        elapsed_time = time.time() - start_time  # 경과 시간 계산
        

        # ✅ `게시` 버튼 찾기 및 클릭
        post_button = WebDriverWait(instagram_driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, '//div[contains(@class, "x1i0vuye") and @role="button" and text()="게시"]'))
        )
        post_button.click()
        time.sleep(2)  # ✅ 버튼 클릭 후 대기

        # ✅ 댓글이 정상적으로 등록되었는지 확인
        WebDriverWait(instagram_driver, 15).until_not(
            EC.text_to_be_present_in_element_value((By.CSS_SELECTOR, 'textarea.x1i0vuye.xvbhtw8'), res)
        )

        ui.system_status.append("✅ 댓글 게시 완료!")
        comment_count += 1  # ✅ 댓글 카운트 증가

        # ✅ 댓글 등록 후 랜덤 대기 시간 적용 (봇 감지 우회)
        time.sleep(random.uniform(10, 30))  # ✅ 10~30초 랜덤 대기
        if comment_count >= MAX_COMMENTS_PER_HOUR:
            ui.system_status.append("⚠ 최대 댓글 개수 초과. 1시간 대기 후 다시 시도.")
            instagram_driver.quit()

            time.sleep(3600)  # ✅ 1시간 대기 후 다시 시작
            
            comment_count = 0  # ✅ 카운트 초기화
            start_time = time.time()  # ✅ 시작 시간 초기화

    except TimeoutException:
        ui.system_status.append("⚠ 게시 버튼 클릭 후 댓글이 등록되지 않음.")
        comment_count += 1  # ✅ 댓글 카운트 증가
    except Exception as e:
        ui.system_status.append(f"⚠ 댓글 게시 중 오류 발생: {e}")
        comment_count += 1  # ✅ 댓글 카운트 증가
import os

def get_last_commented_user():
    """현재 게시글의 마지막으로 댓글을 단 사용자 ID 가져오기"""
    user_id_file = get_user_id_file()
    if os.path.exists(user_id_file):
        with open(user_id_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                return lines[-1].strip()  # ✅ 마지막 사용자 ID 반환
    return None  # ✅ 파일이 없거나 비어 있으면 None 반환

def instagram_process(ui):
    
    system_message = "당신은 이 글의 주체이며, 메인글을 쓴 사람이다. 당신의 글에 답글을 쓴 사람들에게 유쾌하고 재미있게 답변한다."
    review_reply_chatbot = Review_ChatBot("gpt-4o", system_message)

    ui.system_status.append("[INFO] Instagram 페이지 시작...")

    # WebDriver 초기화
    initialize_instagram_driver()

    # 계정 정보 불러오기
    credentials = ui.get_credentials()
    naver_id, naver_pw, naver_no1, naver_no2, rv_no1, rv_no2, dn_id, dn_pw, dn_no = credentials  
    ui.system_status.append(f"[INFO] 로그인 ID: {naver_id}, 비밀번호: {'*' * len(naver_pw)}")

    # Instagram 로그인
    ui.system_status.append("[INFO] Instagram 로그인 중...")
    instagram_driver.get("https://www.instagram.com/")
    WebDriverWait(instagram_driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')

    # 로그인 필드 찾기
    username = WebDriverWait(instagram_driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
    password = instagram_driver.find_element(By.NAME, 'password')

    # 계정 정보 입력
    username.send_keys("jebuilmare")
    time.sleep(1)
    password.send_keys("b22387200@7")
    time.sleep(1)
    password.send_keys(Keys.RETURN)
    time.sleep(10)  # 로그인 대기
    print(ui.instagram_input.text())
    ui.system_status.append("[INFO] Instagram 게시물 이동 중...")
    instagram_driver.get(f"https://www.instagram.com/p/{ui.instagram_input.text()}/?img_index=1")
    time.sleep(5)
    span_element = WebDriverWait(instagram_driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "x193iq5w.xeuugli.x1fj9vlw.x13faqbe.x1vvkbs.xt0psk2.x1i0vuye.xvs91rp.xo1l8bm.x5n08af.x10wh9bi.x1wdrske.x8viiok.x18hxmgj"))
    )
    # 댓글 스크롤 컨테이너 찾기
    ui.chat_status.append(f"{span_element.text}")
    scroll_container = WebDriverWait(instagram_driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.x5yr21d.xw2csxc.x1odjw0f.x1n2onr6"))
    )
    container = instagram_driver.find_element(By.CSS_SELECTOR, ".x78zum5.xdt5ytf.x1iyjqo2")
    processed_spans = set()  # 이미 처리한 댓글을 저장하는 집합
    found_start_id = False  # start_id가 발견되었는지 여부
    comments_made = 0  # 작성한 댓글 수
    prev_processed_count = 0  # ✅ 이전에 처리한 `span` 개수 저장

    # UI 입력에서 값 가져오기
    start_id = ui.instagram_start_input.text().strip()  # 댓글 시작 기준 ID
    end_count = int(ui.instagram_end_input.text().strip())  # 최대 댓글 작성 개수
    spans = container.find_elements(
                    By.CSS_SELECTOR,
                    "span.x1lliihq.x1plvlek.xryxfnj.x1n2onr6.x1ji0vk5.x18bv5gf.x193iq5w.xeuugli"
                    ".x1fj9vlw.x13faqbe.x1vvkbs.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty."
                    "x1943h6x.x1i0vuye.xvs91rp.xo1l8bm.x5n08af.x10wh9bi.x1wdrske.x8viiok.x18hxmgj"
                    )
    do_reply_spans = [span for span in spans if "답글" not in span.text]
    
    id_spans = WebDriverWait(instagram_driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.x1lliihq.x193iq5w.x6ikm8r.x10wlt62.xlyipyv.xuxw1ft"))
    )
    reply_spans = [span for span in id_spans if span.text == "답글 달기"]

    new_spans = [span for span in reply_spans if span not in processed_spans]  # 새로 발견된 span만 처리
    scroll_attempts = 0
    commented_users = load_commented_users(ui)
    consecutive_empty_for_loops = 0
    MAX_EMPTY_FOR_LOOPS = 3  # ✅ 최대 3번 연속으로 실행되지 않으면 종료
    while True:
        for_executed = False  # ✅ `for` 루프 실행 여부 추적
        start_index = prev_processed_count
        for i in range(start_index, len(new_spans)):  # ✅ 기존 처리한 span 제외하고 처리 시작
            
            try:
                for_executed = True  # ✅ `for` 루프가 실행되었음을 기록
                consecutive_empty_for_loops = 0  # ✅ 정상 실행되었으므로 카운터 초기화
               
                span = new_spans[i]
                span.click()
                if span.text == "jebuilmare":
                    instagram_driver.quit()
                    time.sleep(10)
                    ui.instagram_reply_button.click()
                    
                time.sleep(1)  # UI 업데이트 대기
                
                user_id = do_reply_spans[2 * (len(processed_spans) + 1) - 1].text

                # ✅ 현재 게시글에 대해 이미 댓글을 단 사용자라면 건너뛰기
                if user_id in commented_users:
                    ui.system_status.append(f"⚠ {user_id} 이미 현재 게시글에 댓글을 작성한 사용자. 건너뜀.")
                    processed_spans.add(span)
                    continue
                else:
                    commented_users.add(span.text)  # ✅ 새로운 사용자 기록
                      # ✅ 파일에도 저장

                    # ✅ 댓글 입력창 찾기
                    textarea_element = WebDriverWait(instagram_driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea.x1i0vuye.xvbhtw8'))
                    )

                    # ✅ 현재 자동 입력된 @ID 가져오기
                    current_text = textarea_element.get_attribute("value").strip()

                    # ✅ start_id가 나오기 전까지 대기
                    # if not found_start_id:
                    #     if start_id in current_text:
                    #         found_start_id = True  # ID가 감지되면 댓글 작성 시작
                    #         ui.system_status.append(f"✅ 시작 ID({start_id}) 발견! 댓글 작성 시작.")
                    #         time.sleep(1)
                    #     else:
                    #         ui.system_status.append(f"⏳ ID({start_id}) 발견 전까지 대기 중...")
                    #         processed_spans.add(span)
                            
                    #         continue  # start_id가 나오지 않았다면 댓글 작성 안 함

                    # ✅ 댓글 개수 초과 시 종료
                    if comments_made >= end_count:
                        ui.system_status.append(f"✅ 설정된 {end_count}개의 댓글을 모두 작성 완료. 종료.")
                        instagram_driver.quit()
                        return

                    # ✅ 댓글과 답글을 미리 매칭하여 유지
                    response = review_reply_chatbot.get_review_comment(span_element.text, do_reply_spans[2 * (len(processed_spans) + 1)].text)

                    ui.chat_status.append(f"{do_reply_spans[2 * (len(processed_spans) + 1) - 1].text} : ")
                    ui.chat_status.append(f"{do_reply_spans[2 * (len(processed_spans) + 1)].text}\n")
                    ui.chat_status.append(f"[Chatbot]: {response}\n")

                    # ✅ 댓글 입력창 활성화 대기
                    # textarea_element = wait_for_comment_box()
                    # if textarea_element:
                        # ✅ 기존 입력값 확인하여 중복 입력 방지
                    existing_text = textarea_element.get_attribute("value").strip()
                    if existing_text == response:
                        ui.system_status.append("⚠ 이미 입력된 댓글과 동일함. 입력 생략.")
                    else:
                        human_typing(textarea_element, remove_emoji(remove_non_bmp(response)), ui)  # ✅ 자연스러운 타이핑 실행
                        time.sleep(1)

                        submit_comment(response, ui) 
                        save_commented_user(user_id, ui)

                    # ✅ 댓글 개수 증가
                    comments_made += 1

                    # ✅ 처리한 span 저장
                    processed_spans.add(span)

            except TimeoutException:
                ui.system_status.append("⚠ 댓글 작성 중 타임아웃 발생. 다음 댓글로 넘어감.")
                continue
            except NoSuchElementException:
                ui.system_status.append("⚠ 일부 요소가 누락됨. 댓글 생략 후 진행.")
                time.sleep(4)
                continue
            except StaleElementReferenceException:
                ui.system_status.append("⚠ 요소가 사라짐. 새로고침 후 재시도.")
                continue
        
        if not for_executed:
            consecutive_empty_for_loops += 1  # ✅ 연속 실행되지 않은 횟수 증가
            ui.system_status.append("[INFO] No new comments loaded, scrolling down to load more comments...")

            # ✅ `for` 루프가 3번 연속 실행되지 않으면 프로그램 종료
            if consecutive_empty_for_loops >= MAX_EMPTY_FOR_LOOPS:
                ui.system_status.append("⚠ 연속 3번 이상 `for` 루프 실행되지 않음. 프로그램 종료.")
                instagram_driver.quit()
                ui.instagram_start_input = get_last_commented_user()
                ui.instagram_reply_button()
                break  # ✅ 프로그램 종료

        else:
            consecutive_empty_for_loops = 0  # ✅ `for` 루프가 정상 실행되었으므로 카운터 초기화        

        prev_processed_count = len(new_spans)
        ui.system_status.append("[INFO] Scrolling down to load more comments...")

        # ✅ 다시 댓글 리스트 업데이트
        spans = container.find_elements(
            By.CSS_SELECTOR,
            "span.x1lliihq.x1plvlek.xryxfnj.x1n2onr6.x1ji0vk5.x18bv5gf.x193iq5w.xeuugli"
            ".x1fj9vlw.x13faqbe.x1vvkbs.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty."
            "x1943h6x.x1i0vuye.xvs91rp.xo1l8bm.x5n08af.x10wh9bi.x1wdrske.x8viiok.x18hxmgj"
        )
        do_reply_spans = [span for span in spans if "답글" not in span.text]
        id_spans = WebDriverWait(instagram_driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.x1lliihq.x193iq5w.x6ikm8r.x10wlt62.xlyipyv.xuxw1ft"))
        )

        reply_spans = [span for span in id_spans if span.text == "답글 달기"]

        # ✅ `new_spans` 업데이트 후 새로운 댓글 감지
        new_spans = [span for span in reply_spans if span not in processed_spans]

        # ✅ 새로운 댓글이 없으면 종료
        if not new_spans:
            ui.system_status.append("[INFO] No more new comments found. Exiting.")
            
            if not force_scroll_multiple(ui, times=1):  # ✅ `times` 값을 조절하여 스크롤 강도 조절 가능
                ui.system_status.append("⚠ 더 이상 댓글이 로드되지 않음. 종료합니다.")
                instagram_driver.quit()
                break  # ✅ 스크롤 실패 시 종료

            scroll_attempts += 1  # ✅ 스크롤 실행 횟수 증가
            continue  # ✅ 새로운 댓글을 찾기 위해 다시 반복

        # ✅ 새로운 댓글이 감지되었으면 스크롤 횟수 초기화
        scroll_attempts = 0


def initialize_instagram_driver():
    """인스타그램 드라이버."""
    global instagram_driver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    # chrome_options.add_argument("--headless")
    instagram_driver = webdriver.Chrome(options=chrome_options)

def instagram_process():
    """인스타그램 자동 댓글 — 기존 instagram_process 코드 붙여넣기"""
    pass

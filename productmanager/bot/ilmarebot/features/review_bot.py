
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

from ilmarebot.common.path import PROMPT_FILE
from ilmarebot.ui.review_chatbot import Review_ChatBot
from ilmarebot.common.utils import remove_emoji


review_driver = None #리뷰 드라이버

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

def initialize_review_driver():
    """리뷰 드라이버."""
    
    global review_driver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--headless")
    review_driver = webdriver.Chrome(options=chrome_options)


def start_review_process(ui):  #네이버 리뷰 댓글 프로세스
    try:
        with open(PROMPT_FILE, 'r', encoding='utf-8') as file: 
            content = file.read()  

        system_message = content
        
        review_chatbot = Review_ChatBot("gpt-4o", system_message)
     

        credentials = ui.get_credentials()
        if credentials is None:  # 입력 취소 또는 오류 처리
            ui.ststem_status.append("[ERROR] Credentials not provided.")
            return

        naver_id, naver_pw, naver_no1, naver_no2, rv_no1, rv_no2, dn_id, dn_pw, dn_no = credentials  
        ui.ststem_status.append(f"[INFO] ID: {naver_id}, Password: {'*' * len(naver_pw)}")   
        
        initialize_review_driver()

        review_driver.get('https://naver.com')
        WebDriverWait(review_driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        ui.ststem_status.append("[INFO] Naver homepage loaded.")

        # Login process
        login_button = WebDriverWait(review_driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@class='MyView-module__link_login___HpHMW']")))
        login_button.click()
        ui.ststem_status.append("[INFO] Login button clicked.")

        login_to_site(review_driver,ui,naver_id,naver_pw)

        ui.append_chat_status(f"선택된 옵션: {ui.get_selected_radio_button()}")

        should_quit = False
        time.sleep(5)
        while True:
            # 하위 button 태그 클릭
            if ui.get_selected_radio_button() == "네이버예약 가능업소":         #예약가능업소는 숫자가 두개이므로 두개의 숫자를 받아온다.           
                url3 = f"https://new.smartplace.naver.com/bizes/place/{rv_no1}/reviews?bookingBusinessId={rv_no2}&menu=visitor"
                review_driver.get(url3)
            
                time.sleep(4) 
                review_driver.get(f"https://new.smartplace.naver.com/bizes/place/{rv_no1}/reviews?bookingBusinessId={rv_no2}&hasReply=false&menu=visitor")
                time.sleep(3)

            else:
                review_driver.get(f"https://new.smartplace.naver.com/bizes/place/{rv_no1}/reviews?menu=visitor") #예약가능업소가 아닐경우
                time.sleep(3)
            
            
            review_driver.execute_script("document.body.style.zoom = '50%'") #페이지 줌아웃(버튼이 안보일경우 대비)
            
            time.sleep(3)

            # '미등록' 값을 가진 button 태그 클릭
            div_element = WebDriverWait(review_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.ButtonSelector_root__h7HaW.ButtonSelector_calendar__ablcH'))
            )

            button = div_element.find_element(By.TAG_NAME, 'button')
            WebDriverWait(review_driver, 10).until(EC.element_to_be_clickable(button)).click()
            ui.ststem_status.append("버튼 클릭 완료")

            # '한달' 값을 가진 li 태그 클릭
            review_li_elements = WebDriverWait(review_driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'li'))
            )
            for li in review_li_elements:
                if li.text.strip() == "한달":
                    li.click()
                    break

            time.sleep(3) 
            
            soup = BeautifulSoup(review_driver.page_source, 'html.parser')
            
            # li 태그 찾기 (class="pui__X35jYm Review_pui_review__zhZdn")
            li_elements = soup.find_all('li', class_='pui__X35jYm Review_pui_review__zhZdn')
            if li_elements:
                for li in li_elements:
                    try:
                        # class="pui__vn15t2"인 div 태그를 찾아 a 태그 텍스트 출력
                        div_vn15t2 = li.find('div', class_='pui__vn15t2')
                        if div_vn15t2:
                            a_tag = div_vn15t2.find('a')
                            if a_tag:
                                ui.chat_status.append(f"[ 리 뷰 ]:  {remove_emoji(a_tag.get_text())}")
                        else:
                            review_driver.quit()
                        # class="Review_btn_group__mDkTf"인 div 태그 아래 버튼 찾기
                        btn_group = li.find('div', class_='Review_btn_group__mDkTf')
                        if btn_group:
                            buttons = btn_group.find_all('button')
                            for button in buttons:
                                if button:
                                    ui.ststem_status.append(f"버튼 클릭: {button.text}")
                                    # 버튼 클릭
                                    review_driver.find_element(By.XPATH, f"//button[text()='{button.text}']").click()
                                    time.sleep(2)  # 페이지 로딩 대기

                                    # 1. class="Review_textarea_wrap__4H0_k"인 div 태그 찾기
                                    textarea_wrap = review_driver.find_element(By.CLASS_NAME, 'Review_textarea_wrap__4H0_k')

                                    # 2. 그 아래에 있는 textarea 태그를 찾고 클릭하기
                                    textarea = textarea_wrap.find_element(By.TAG_NAME, 'textarea')
                                    response = review_chatbot.get_response(a_tag.get_text())
                                    ui.chat_status.append(response)

                                    # 3. 각 버튼에 맞는 텍스트 입력
                                    textarea.click()  # 클릭하여 포커스를 맞춤
                                    textarea.clear()  # 기존 텍스트를 지운 후 새로 입력
                                    textarea.send_keys("AI 자동답변] :" + remove_emoji(response))  # 첫 번째 버튼은 'aaaa 1', 두 번째 버튼은 'aaaa 2'
                                    time.sleep(2)

                                    # 4. "enter" 버튼 클릭
                                    button_enter = review_driver.find_element(By.CSS_SELECTOR, ".Review_btn__Lu4nI.Review_btn_enter__az8i7.Review_active__1tJOt")

                                    # 버튼이 존재하면 클릭
                                    button_enter.click()
                                    ui.ststem_status.append("리뷰 버튼 클릭 완료")

                                    review_chatbot.reset()
                                    # 클릭 후 잠시 대기 (필요시 로딩을 기다리기 위해)
                                    time.sleep(5)  
                        #         else:
                        #             should_quit = True  # 종료 조건 추가
                                    
                    
                        # else:
                        #      should_quit = True  # 종료 조건 추가    
                    except Exception as e:
                        ui.system_status.append(f"Error processing li: {e}")
            else:
                ui.chat_status.append("[INFO] 리뷰 완료")
                should_quit = True  # 종료 조건 추가
                break
                
        if should_quit:
            review_driver.quit()
            
            ui.review_btn.setEnabled(True)
            ui.system_status.append("브라우저가 종료되었습니다.")
            should_quit = False

    except Exception as e:
            ui.system_status.append(f"[ERROR] {e}")





# employee_map_ui.py
import sys
import os
import io
import requests
import folium
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from datetime import datetime
import pytz
KST = pytz.timezone("Asia/Seoul")  # ✅ KST 타임존 정의
BASE_URL = "http://127.0.0.1:8000"  # FastAPI 서버 주소
GOOGLE_MAPS_API_KEY = "AIzaSyD0d6_wU5vPID4djhY3qZKp0e0XSJITg_w"  # Google Maps API 키 (여기에 본인의 API 키 입력)

class EmployeeMapTab(QWidget):
    """
    직원 '이름'으로 검색하여,
    날짜 관계없이 모든 방문 기록을 지도에 표시하고,
    팝업(풍선창)에 [거래처명, 방문시간, 당일 매출]을 보여주는 예시 탭.
    단, 마커 위치는 거래처의 주소를 기반으로 변환한 실제 좌표를 사용합니다.
    """
    def __init__(self, base_url: str = None):
        """
        base_url: 예) "http://127.0.0.1:8000" 처럼 FastAPI 서버의 루트 주소.
        """
        super().__init__()
        if base_url is None:
            base_url = BASE_URL
        self.base_url = base_url
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # (1) 상단 검색창/버튼 (직원이름)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("직원이름을 입력하세요 (예: 홍길동)")
        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self.do_search)

        layout.addWidget(self.search_edit)
        layout.addWidget(self.search_button)

        # (2) 웹뷰 - Folium 지도를 표시
        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)

        self.setLayout(layout)

        # 처음에는 기본 서울 지도
        self.load_default_map()

    def load_default_map(self):
        """
        프로그램 시작 시 지도에 아무 데이터도 없을 때
        서울 중심을 보여주도록 초기화.
        """
        map_obj = folium.Map(location=[37.5665, 126.9780], zoom_start=11)  # 서울 시청
        self.display_map(map_obj)

    def do_search(self):
        """
        (검색 버튼 콜백)
        1) 사용자가 입력한 직원이름을 받아온다.
        2) 백엔드 GET /employee_map/all_visits?employee_name=... 호출하여
           날짜에 상관없이 모든 방문 기록을 조회.
        3) 결과를 folium 지도에 표시.
        """
        name = self.search_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "경고", "직원이름을 입력하세요.")
            return

        try:
            # 변경: daily_visits -> all_visits
            url = f"{self.base_url}/employee_map/all_visits"
            params = {"employee_name": name}

            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 404:
                QMessageBox.warning(self, "오류", f"직원 '{name}'을 찾을 수 없습니다.")
                return

            if resp.status_code != 200:
                QMessageBox.critical(self, "오류", f"서버 에러: {resp.text}")
                return

            data = resp.json()  # list of dict (방문 기록)
            if not data:
                QMessageBox.information(self, "알림", f"직원 '{name}'의 방문 기록이 없습니다.")
                self.load_default_map()
                return

            self.update_map(data)

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "에러", f"서버 요청 실패: {e}")

    def geocode_address(self, address):
        """
        주소를 Google Maps Geocoding API를 사용하여 위도와 경도로 변환합니다.
        """
        try:
            url = f"https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": address,
                "key": GOOGLE_MAPS_API_KEY
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            results = response.json().get("results", [])

            if not results:
                return None, None  # 주소 변환 실패 시 None 반환

            location = results[0]["geometry"]["location"]
            return location["lat"], location["lng"]

        except requests.exceptions.RequestException as e:
            print(f"지오코딩 실패: {e}")
            return None, None

    def update_map(self, visits_data):
        """
        visits_data 예시:
        [
          {
            "visit_id": 10,
            "visit_datetime": "2025-03-05 10:20:30",
            "client_id": 3,
            "client_name": "ABC상사",
            "address": "서울시 강남구 ...",
            "outstanding_amount": 20000.0,
            "today_sales": 50000.0
          },
          ...
        ]
        """
        """ 방문 데이터를 folium 지도에 표시 """
        first_address = visits_data[0]["address"]
        first_lat, first_lng = self.geocode_address(first_address)

        if first_lat is None or first_lng is None:
            first_lat, first_lng = 37.5665, 126.9780  # 서울 기본값

        map_obj = folium.Map(location=[first_lat, first_lng], zoom_start=12)

        for item in visits_data:
            address = item["address"]
            lat, lng = self.geocode_address(address)

            if lat is None or lng is None:
                continue  

            c_name = item["client_name"]
            v_time = item["visit_datetime"]
            sales = item["today_sales"]
            visit_count = item.get("visit_count", 1)  # ✅ 방문 횟수 추가

            popup_html = f"""
            <b>거래처명:</b> {c_name}<br>
            <b>방문시간:</b> {v_time}<br>
            <b>방문횟수:</b> {visit_count}<br>
            <b>당일매출:</b> {int(sales)}원
            """

            folium.Marker(
                location=[lat, lng],
                popup=popup_html,
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(map_obj)

        self.display_map(map_obj)
        
    def display_map(self, map_obj: folium.Map):
        """
        Folium Map 객체를 HTML로 변환하여 QWebEngineView에 로드.
        """
        data = io.BytesIO()
        map_obj.save(data, close_file=False)
        self.map_view.setHtml(data.getvalue().decode())

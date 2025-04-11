# employee_map_ui.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import io
import requests
import folium
import pytz
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QMessageBox, QListWidget, QListWidgetItem
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from datetime import datetime
from config import BASE_URL
# 타임존 및 기본 설정
KST = pytz.timezone("Asia/Seoul")

GOOGLE_MAPS_API_KEY = "AIzaSyD0d6_wU5vPID4djhY3qZKp0e0XSJITg_w"  # 유효한 API 키로 교체

class EmployeeMapTab(QWidget):
    """
    좌우 분할 UI:
      - left_panel: 직원 검색 영역 (검색 필드, 검색 버튼, 직원 목록)
      - right_panel: 지도 영역 (Folium 지도 표시)
    Main UI에서는 각각 .left_panel, .right_panel 속성을 통해 접근합니다.
    """
    def __init__(self, base_url: str = None):
        super().__init__()
        if base_url is None:
            base_url = BASE_URL
        self.base_url = base_url
        self.init_ui()

    def init_ui(self):
        # 전체를 좌우로 배치하는 레이아웃 생성
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        self.setLayout(main_layout)

        # --- 왼쪽 패널: 직원 검색 및 선택 영역 ---
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)

        # 검색 필드와 버튼
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("직원이름을 입력하세요 (예: 홍길동)")
        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self.do_search)
        left_layout.addWidget(self.search_edit)
        left_layout.addWidget(self.search_button)

        # 직원 목록 (검색 결과)
        self.employee_list = QListWidget()
        self.employee_list.itemClicked.connect(self.on_employee_selected)
        left_layout.addWidget(self.employee_list)

        main_layout.addWidget(self.left_panel, 1)  # 왼쪽 패널 (비율 1)

        # --- 오른쪽 패널: 지도 영역 ---
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)

        self.map_view = QWebEngineView()
        right_layout.addWidget(self.map_view)

        main_layout.addWidget(self.right_panel, 3)  # 오른쪽 패널 (비율 3)

        # 초기 지도 로드
        self.load_default_map()

    def load_default_map(self):
        """프로그램 시작 시 서울 기본 지도를 로드합니다."""
        map_obj = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
        self.display_map(map_obj)

    def do_search(self):
        """
        직원 이름으로 방문 기록을 조회하여 지도 업데이트.
        API 호출 후 결과가 여러 직원이면 왼쪽 목록에 이름을 채워 넣습니다.
        """
        name = self.search_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "경고", "직원이름을 입력하세요.")
            return

        try:
            url = f"{self.base_url}/employee_map/daily_visits"
            params = {"employee_name": name}
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 404:
                QMessageBox.warning(self, "오류", f"직원 '{name}'을 찾을 수 없습니다.")
                return
            if resp.status_code != 200:
                QMessageBox.critical(self, "오류", f"서버 에러: {resp.text}")
                return

            data = resp.json()  # 방문 기록 리스트
            if not data:
                QMessageBox.information(self, "알림", f"직원 '{name}'의 방문 기록이 없습니다.")
                self.load_default_map()
                return

            # 여러 직원 이름이 포함될 경우, 왼쪽 목록에 추가
            self.employee_list.clear()
            employee_names = set(record["employee_name"] for record in data)
            for ename in employee_names:
                item = QListWidgetItem(ename)
                self.employee_list.addItem(item)
            # 단일 직원이면 바로 지도 업데이트
            if len(employee_names) == 1:
                self.update_map(data)
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "에러", f"서버 요청 실패: {e}")

    def on_employee_selected(self, item):
        """
        왼쪽 목록에서 직원 선택 시 해당 직원 이름을 검색 필드에 채우고,
        다시 검색하여 지도를 업데이트합니다.
        """
        selected_name = item.text()
        self.search_edit.setText(selected_name)
        self.do_search()

    def geocode_address(self, address):
        """주소를 위도, 경도로 변환 (Google Geocoding API 사용)"""
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {"address": address, "key": GOOGLE_MAPS_API_KEY}
            response = requests.get(url, params=params)
            response.raise_for_status()
            results = response.json().get("results", [])
            if not results:
                return None, None
            location = results[0]["geometry"]["location"]
            return location["lat"], location["lng"]
        except requests.exceptions.RequestException as e:
            print(f"지오코딩 실패: {e}")
            return None, None

    def update_map(self, visits_data):
        """
        방문 기록 데이터(리스트)를 바탕으로 Folium 지도에 마커를 추가하고 업데이트합니다.
        """
        if not visits_data:
            self.load_default_map()
            return

        first_address = visits_data[0]["address"]
        first_lat, first_lng = self.geocode_address(first_address)
        if first_lat is None or first_lng is None:
            first_lat, first_lng = 37.5665, 126.9780

        map_obj = folium.Map(location=[first_lat, first_lng], zoom_start=12)
        for item in visits_data:
            address = item["address"]
            lat, lng = self.geocode_address(address)
            if lat is None or lng is None:
                continue
            c_name = item["client_name"]
            v_time = item["visit_datetime"]
            sales = item["today_sales"]
            visit_count = item.get("visit_count", 1)
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
        """Folium Map 객체를 HTML로 변환하여 QWebEngineView에 로드합니다."""
        data = io.BytesIO()
        map_obj.save(data, close_file=False)
        self.map_view.setHtml(data.getvalue().decode())


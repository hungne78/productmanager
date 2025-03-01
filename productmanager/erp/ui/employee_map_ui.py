from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
import folium
import io
import sys
import os

# 현재 파일의 상위 폴더(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api_services import api_fetch_employee_visits, api_fetch_client_coordinates, get_auth_headers


class EmployeeMapTab(QWidget):
    """ 직원 방문 거래처를 지도에 표시하는 탭 """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 직원 검색 입력창
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("직원 ID 입력")
        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self.search_employee)

        layout.addWidget(self.search_edit)
        layout.addWidget(self.search_button)

        # 지도 뷰어
        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)

        self.setLayout(layout)
        self.load_default_map()

    def load_default_map(self):
        """ 기본 지도 설정 (서울·경기권 중심) """
        map_object = folium.Map(location=[37.5665, 126.9780], zoom_start=12)  # 서울 시청 기준
        self.display_map(map_object)

    def search_employee(self):
        """ 직원 ID로 방문한 거래처 조회 후 지도 업데이트 """
        employee_id = self.search_edit.text().strip()
        if not employee_id.isdigit():
            QMessageBox.warning(self, "경고", "올바른 직원 ID를 입력하세요.")
            return

        employee_id = int(employee_id)
        visits = api_fetch_employee_visits(employee_id)

        if not visits:
            QMessageBox.information(self, "정보", f"직원 ID {employee_id}의 방문 거래처가 없습니다.")
            return

        client_locations = []
        for visit in visits:
            client_id = visit["client_id"]
            coords = api_fetch_client_coordinates(client_id)
            if coords:
                client_locations.append((coords[0], coords[1], coords[2], visit["visit_datetime"], visit["today_sales"]))

        if client_locations:
            self.update_map(client_locations)
        else:
            QMessageBox.information(self, "정보", f"직원 ID {employee_id}의 방문 거래처 위치를 찾을 수 없습니다.")

    def update_map(self, client_locations):
        """ 방문한 거래처들의 위치를 지도에 표시 """
        if not client_locations:
            return

        # 기본 지도 설정 (첫 번째 거래처 위치를 기준으로)
        lat, lon = client_locations[0][:2]
        map_object = folium.Map(location=[lat, lon], zoom_start=12)

        for lat, lon, name, visit_time, today_sales in client_locations:
            popup_content = f"""
            <b>거래처명:</b> {name}<br>
            <b>방문 시간:</b> {visit_time}<br>
            <b>당일 매출:</b> {today_sales}원
            """
            folium.Marker([lat, lon], popup=popup_content, icon=folium.Icon(color="blue")).add_to(map_object)

        self.display_map(map_object)

    def display_map(self, map_object):
        """ 지도 HTML 변환 후 표시 """
        map_html = io.BytesIO()
        map_object.save(map_html, close_file=False)
        self.map_view.setHtml(map_html.getvalue().decode())

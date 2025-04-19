import sys, os, json, colorsys, requests
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QTimer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import BASE_URL

KAKAO_JS_KEY = "c56b498bb536bd492cd6a5a0bb85062c"
DEFAULT_CENTER_LAT = 37.5665  # 서울시청
DEFAULT_CENTER_LON = 126.9780

class EmployeeMapTab(QWidget):
    def __init__(self):
        super().__init__()
        self.employees = []  # 전체 직원 목록
        self.color_map = {}
        self._build_ui()
        self.load_default_map()
        QTimer.singleShot(200, self._load_all_employees)

    def _build_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        # 왼쪽: 버튼 패널
        self.left_panel = QVBoxLayout()
        self.left_panel.setAlignment(Qt.AlignTop)
        left_widget = QWidget()
        left_widget.setLayout(self.left_panel)
        left_widget.setFixedWidth(160)
        layout.addWidget(left_widget)

        self.map = QWebEngineView()
        layout.addWidget(self.map)

    def _load_all_employees(self):
        try:
            resp = requests.get(f"{BASE_URL}/employees/", timeout=5)
            resp.raise_for_status()
            self.employees = resp.json()
            if not self.employees:
                QMessageBox.information(self, "직원 없음", "등록된 직원이 없습니다.")
                return
            self.color_map = self._make_color_table(self.employees)
            self._build_employee_buttons()
        except Exception as e:
            QMessageBox.critical(self, "에러", f"직원 목록 불러오기 실패:\n{e}")

    def _build_employee_buttons(self):
        # 기존 버튼 제거
        while self.left_panel.count():
            item = self.left_panel.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 새로고침 버튼
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self._load_all_employees)
        self.left_panel.addWidget(refresh_btn)

        self.left_panel.addSpacing(10)

        # 직원 버튼
        for emp in sorted(self.employees, key=lambda x: x["name"]):
            emp_id = emp["id"]
            emp_name = emp["name"]
            color = self.color_map.get(emp_id, "#888")
            btn = QPushButton(emp_name)
            btn.setStyleSheet(f"background-color: {color}; color: white;")
            btn.clicked.connect(lambda _, name=emp_name: self._load_employee_visits(name))
            self.left_panel.addWidget(btn)

        self.left_panel.addStretch()

    def _load_employee_visits(self, emp_name):
        try:
            url = f"{BASE_URL}/employee_map/daily_visits"
            params = {"employee_name": emp_name}
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                QMessageBox.information(self, "방문 없음", f"{emp_name}의 방문 기록이 없습니다.")
                self.load_default_map()
                return
            self._render_map(data, self.color_map)
        except Exception as e:
            QMessageBox.critical(self, "에러", f"방문 기록 요청 실패:\n{e}")

    def load_default_map(self):
        html = self._generate_map_html(DEFAULT_CENTER_LAT, DEFAULT_CENTER_LON, [])
        self.map.setHtml(html)

    def _render_map(self, dataset: list[dict], color_map: dict):
        if not dataset:
            self.load_default_map()
            return

        center_lat = dataset[0].get("lat", DEFAULT_CENTER_LAT)
        center_lon = dataset[0].get("lon", DEFAULT_CENTER_LON)

        markers = []
        for d in dataset:
            lat, lon = d.get("lat"), d.get("lon")
            if lat is None or lon is None:
                continue
            emp_id = d.get("employee_id")
            color = color_map.get(emp_id, "#007BFF")
            label = f"{d['client_name']}<br>방문: {d['visit_datetime']}<br>매출: {int(d['today_sales'])}원"
            markers.append({
                "lat": lat,
                "lon": lon,
                "color": color,
                "label": label
            })

        html = self._generate_map_html(center_lat, center_lon, markers)
        self.map.setHtml(html)

    def _make_color_table(self, employees):
        hue_step = 1.0 / max(len(employees), 1)
        colors = {}
        for idx, emp in enumerate(sorted(employees, key=lambda x: x["id"])):
            h = (idx * hue_step) % 1.0
            r, g, b = colorsys.hls_to_rgb(h, 0.5, 0.65)
            colors[emp["id"]] = "#{:02X}{:02X}{:02X}".format(int(r * 255), int(g * 255), int(b * 255))
        return colors

    def _generate_map_html(self, center_lat, center_lon, markers):
        markers_json = json.dumps(markers, ensure_ascii=False)
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>직원 방문 지도</title>
            <style>html, body, #map {{width:100%;height:100%;margin:0;padding:0;}}</style>
            <script type="text/javascript" src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}"></script>
        </head>
        <body>
        <div id="map"></div>
        <script>
            var mapContainer = document.getElementById('map');
            var mapOption = {{
                center: new kakao.maps.LatLng({center_lat}, {center_lon}),
                level: 9
            }};
            var map = new kakao.maps.Map(mapContainer, mapOption);
            var markers = {markers_json};

            markers.forEach(function(item) {{
                var marker = new kakao.maps.Marker({{
                    position: new kakao.maps.LatLng(item.lat, item.lon),
                    map: map
                }});
                var label = new kakao.maps.CustomOverlay({{
                    position: new kakao.maps.LatLng(item.lat, item.lon),
                    content: '<div style="padding:4px;background:' + item.color + ';color:white;border-radius:4px;font-size:12px;">' + item.label + '</div>',
                    yAnchor: 1
                }});
                label.setMap(map);
            }});
        </script>
        </body>
        </html>
        """

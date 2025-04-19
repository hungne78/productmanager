# ui/client_map_widget.py

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl
import tempfile, json, colorsys, requests
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import BASE_URL

KAKAO_JS_KEY = "c56b498bb536bd492cd6a5a0bb85062c"
DEFAULT_CENTER_LAT = 37.5662952
DEFAULT_CENTER_LON = 126.9779451


class ClientMapWidget(QWidget):
    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.token = token
        self.raw = []
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self.left_panel = QVBoxLayout()
        self.left_panel.setAlignment(Qt.AlignTop)
        left_widget = QWidget()
        left_widget.setLayout(self.left_panel)
        left_widget.setFixedWidth(160)
        layout.addWidget(left_widget)

        self.web = QWebEngineView()
        layout.addWidget(self.web)

    def _load_data(self):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            resp = requests.get(f"{BASE_URL}/clients/map/clients", headers=headers, timeout=10)
            resp.raise_for_status()
            self.raw = resp.json()
            self._build_employee_buttons()
            self.color_map = self._make_color_table(self.raw)
            self._render_map(self.raw, self.color_map)
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "로드 실패", f"거래처 데이터를 불러오는 중 오류 발생:\n{e}")
            print("❌ 지도 데이터 오류:", e)

    def _build_employee_buttons(self):
        while self.left_panel.count():
            item = self.left_panel.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.raw:
            return

        employees = {(d["employee_id"], d["employee_name"]) for d in self.raw}
        color_map = self._make_color_table(self.raw)
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self._load_data)
        self.left_panel.addWidget(refresh_btn)
        all_btn = QPushButton("전체 보기")
        all_btn.clicked.connect(lambda: self._render_map(self.raw, self.color_map))  # ✅ 인자 2개 전달

        self.left_panel.addWidget(all_btn)

        for emp_id, emp_name in sorted(employees):
            btn = QPushButton(emp_name)
            btn.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    padding-left: 10px;
                    background-color: {color_map.get(emp_id, "#ddd")};
                    color: white;
                    border-radius: 6px;
                    margin-bottom: 4px;
                }}
            """)
            btn.clicked.connect(lambda _, eid=emp_id: self._render_map(
                [c for c in self.raw if c["employee_id"] == eid], self.color_map
            ))

            self.left_panel.addWidget(btn)

        self.left_panel.addStretch()
    
    def _render_map(self, dataset: list[dict], color_map: dict):
        if not dataset:
            self.web.setHtml("<h3 style='color:red'>표시할 거래처가 없습니다.</h3>")
            return

        center_lat = DEFAULT_CENTER_LAT
        center_lon = DEFAULT_CENTER_LON

        color_map = self._make_color_table(dataset)
        markers = []
        for d in dataset:
            if not isinstance(d, dict):
                continue
            lat, lon = d.get("lat"), d.get("lon")
            if lat is None or lon is None:
                continue
            color = color_map.get(d["employee_id"], "#007BFF")
            markers.append({
                "lat": lat,
                "lon": lon,
                "color": color,
                "label": f"{d['client_name']}<br>담당: {d['employee_name']}"
            })
        markers.append({
            "lat": 37.630063,
            "lon": 127.194985,
            "color": "#FFD700",
            "label": "성심유통"
        })
        html = self._generate_kakao_map_html(center_lat, center_lon, markers)
        
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        with open(tmp.name, "w", encoding="utf-8") as f:
            f.write(html)
        self.web.load(QUrl.fromLocalFile(tmp.name))
        
    def _make_color_table(self, data):
        uniq_emp = sorted({d["employee_id"] for d in data})
        hue_step = 1.0 / max(len(uniq_emp), 1)
        colors = {}
        for idx, emp in enumerate(uniq_emp):
            h = (idx * hue_step) % 1.0
            r, g, b = colorsys.hls_to_rgb(h, 0.5, 0.65)
            colors[emp] = "#{:02X}{:02X}{:02X}".format(
                int(r * 255), int(g * 255), int(b * 255))
        return colors

    def _generate_kakao_map_html(self, center_lat, center_lon, markers):
        markers_json = json.dumps(markers, ensure_ascii=False)
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>거래처 지도</title>
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

        var content = '<div style="padding:6px 10px;border-radius:5px;border:1px solid #888;background:' + item.color + ';color:white;">'
                    + item.label + '</div>';

        var infowindow = new kakao.maps.InfoWindow({{
            content: content
        }});
        kakao.maps.event.addListener(marker, 'click', function() {{
            infowindow.open(map, marker);
        }});

        var label = new kakao.maps.CustomOverlay({{
            position: new kakao.maps.LatLng(item.lat, item.lon),
            content: '<div style="padding:2px 6px;background:' + item.color + ';color:white;font-size:13px;border-radius:4px;font-weight:bold;">' + item.label + '</div>',
            yAnchor: 1
        }});
        label.setMap(map);
    }});
</script>
</body>
</html>
"""

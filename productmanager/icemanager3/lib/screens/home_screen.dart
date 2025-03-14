import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../auth_provider.dart';
import '../services/api_service.dart';
import '../product_provider.dart';
import '../screens/sales_screen.dart';
import '../screens/order_screen.dart';
import '../screens/clients_screen.dart';
import '../screens/VehicleStock_Screen.dart';
import '../screens/vehicle_management_screen.dart';
import '../screens/sales_summary_screen.dart';
import 'product_screen.dart';
import 'order_history_screen.dart';
import 'package:url_launcher/url_launcher.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'dart:typed_data';
import 'package:charset_converter/charset_converter.dart';
import 'dart:io';
import '../screens/settings_screen.dart';
import '../screens/printer.dart';

// 최신 발표 시각 찾기 (06시, 18시 중 가장 최근 값)
class WeatherService {
  static const String _apiKey = "_oHcvFMzSx6B3LxTMzseUg"; // 🔹 기상청 API 키
  static const String _shortLandUrl = "https://apihub.kma.go.kr/api/typ01/url/fct_afs_dl.php"; // 🔹 단기 육상 예보
  static const String _shortTempUrl = "https://apihub.kma.go.kr/api/typ01/url/fct_afs_dl2.php"; // 🔹 단기 기온 예보
  static const String _midTempUrl = "https://apihub.kma.go.kr/api/typ01/url/fct_afs_wc.php"; // 🔹 중기 기온 예보
  static const String _midLandUrl = "https://apihub.kma.go.kr/api/typ01/url/fct_afs_wl.php"; // 🔹 중기 육상 예보
  static const String _shortRegId = "11B10101"; // ✅ 단기 지역 코드
  static const String _midRegId = "11B00000"; // ✅ 중기 지역 코드

  // 🔹 오늘 날짜 (단기 예보용)
  static String _getToday() {
    return DateFormat('yyyyMMdd').format(DateTime.now());
  }

  // 🔹 단기 예보 (오늘~3일)
  static String _getShortTermTmef() {
    return DateFormat('yyyyMMdd').format(DateTime.now().add(Duration(days: 3)));
  }

  // 🔹 중기 예보 (4~7일)
  static String _getMidTermTmef1() {
    return DateFormat('yyyyMMdd').format(DateTime.now().add(Duration(days: 4)));
  }

  static String _getMidTermTmef2() {
    return DateFormat('yyyyMMdd').format(DateTime.now().add(Duration(days: 7)));
  }

  // 🔹 최신 발표 시각 (06시, 18시 중 최근 값)
  static String _getLatestForecastTime() {
    DateTime now = DateTime.now();
    if (now.hour < 6) {
      now = now.subtract(Duration(days: 1));
      return DateFormat('yyyyMMdd18').format(now);
    } else if (now.hour < 18) {
      return DateFormat('yyyyMMdd06').format(now);
    } else {
      return DateFormat('yyyyMMdd18').format(now);
    }
  }
  // 🔹 최신 발표 시각 찾기 (하루 8회, 3시간 간격 발표)
  static String _getLatestForecastTime_short() {
    DateTime now = DateTime.now();

    // 기상청 발표 시각 목록
    List<int> forecastHours = [2, 5, 8, 11, 14, 17, 20, 23];

    // 현재 시간보다 작은(과거) 중 가장 최근 시각 찾기
    int latestHour = forecastHours.lastWhere((h) => h <= now.hour, orElse: () => forecastHours.last);

    // 만약 지금 시간이 01시라면, 전날 23시 발표 시각 사용
    DateTime forecastDate = now.hour >= latestHour ? now : now.subtract(Duration(days: 1));

    // 최종 발표 시각 (yyyyMMddHH 형식)
    return DateFormat('yyyyMMdd').format(forecastDate) + latestHour.toString().padLeft(2, '0');
  }
  // 🔹 최신 발표 시각 범위 찾기 (하루 8회, 3시간 간격 발표)
  static List<String> _getLatestForecastTimeRange() {
    DateTime now = DateTime.now();

    // 기상청 발표 시각 목록 (하루 8회, 3시간 간격)
    List<int> forecastHours = [2, 5, 8, 11, 14, 17, 20, 23];

    // 현재 시간보다 작은(과거) 중 가장 최근 발표 시각 찾기
    int latestHour = forecastHours.lastWhere((h) => h <= now.hour, orElse: () => forecastHours.last);

    // 현재 시간이 발표 직후(데이터가 없을 가능성이 높음)라면 이전 발표 시각 사용
    if (now.hour == latestHour && now.minute < 50) {  // 50분 이전이면 데이터가 없을 가능성 있음
      int index = forecastHours.indexOf(latestHour);
      if (index > 0) {
        latestHour = forecastHours[index - 1]; // 한 단계 이전 발표 시각 사용
      }
    }

    // 만약 현재 시간이 02시 이전이라면, 전날 23시 데이터를 사용
    DateTime forecastDate = now;
    if (now.hour < forecastHours.first) {
      forecastDate = now.subtract(Duration(days: 1));
      latestHour = forecastHours.last; // 전날 마지막 발표 시각 사용
    }

    // 최종 발표 시각 (yyyyMMddHH 형식)
    String tmfc = DateFormat('yyyyMMdd').format(forecastDate) + latestHour.toString().padLeft(2, '0');

    return [tmfc, tmfc]; // 단기 예보는 같은 값으로 설정
  }



  // 🔹 데이터 가져오기
  static Future<List<Map<String, dynamic>>> fetchWeatherData() async {
    final String today = _getToday();
    final String shortTermTmef = _getLatestForecastTime_short();
    final String midTermTmef1 = _getMidTermTmef1();
    final String midTermTmef2 = _getMidTermTmef2();
    final String latestForecastTime = _getLatestForecastTime();
    final List<String> latestForecastTimeRange = _getLatestForecastTimeRange();
    // 🔹 단기 예보 (오늘~3일)
    final Uri shortLandUri = Uri.parse(
        "$_shortLandUrl?reg=$_shortRegId&tmfc1=${latestForecastTimeRange[0]}&tmfc2=${latestForecastTimeRange[1]}&disp=1&authKey=$_apiKey");

    final Uri shortTempUri = Uri.parse(
        "$_shortTempUrl?reg=$_shortRegId&tmfc1=${latestForecastTimeRange[0]}&tmfc2=${latestForecastTimeRange[1]}&disp=1&authKey=$_apiKey");

    // 🔹 중기 예보 (4~7일)
    final Uri midTempUri = Uri.parse(
        "$_midTempUrl?reg=$_shortRegId&tmfc1=$latestForecastTime&tmfc2=$latestForecastTime&tmef1=$midTermTmef1&tmef2=$midTermTmef2&disp=1&authKey=$_apiKey");

    final Uri midLandUri = Uri.parse(
        "$_midLandUrl?reg=$_midRegId&tmfc1=$latestForecastTime&tmfc2=$latestForecastTime&tmef1=$midTermTmef1&tmef2=$midTermTmef2&disp=1&authKey=$_apiKey");

    print("🔗 요청 URL (단기 육상): $shortLandUri");
    print("🔗 요청 URL (단기 기온): $shortTempUri");
    print("🔗 요청 URL (중기 기온): $midTempUri");
    print("🔗 요청 URL (중기 육상): $midLandUri");

    try {
      final responseShortLand = await http.get(shortLandUri);
      final responseShortTemp = await http.get(shortTempUri);
      final responseMidTemp = await http.get(midTempUri);
      final responseMidLand = await http.get(midLandUri);

      if (responseShortLand.statusCode != 200 ||
          responseShortTemp.statusCode != 200 ||
          responseMidTemp.statusCode != 200 ||
          responseMidLand.statusCode != 200) {
        throw Exception("❌ 날씨 데이터 요청 실패");
      }

      final List<Map<String, dynamic>> parsedShortLand = _parseWeatherData(responseShortLand.body, "short_land");
      final List<Map<String, dynamic>> parsedShortTemp = _parseWeatherData(responseShortTemp.body, "short_temp");
      final List<Map<String, dynamic>> parsedMidTemp = _parseWeatherData(responseMidTemp.body, "mid_temp");
      final List<Map<String, dynamic>> parsedMidLand = _parseWeatherData(responseMidLand.body, "mid_land");

      final mergedData = _mergeWeatherData(parsedShortLand, parsedShortTemp, parsedMidTemp, parsedMidLand);

      return mergedData;
    } catch (e) {
      print("❌ API 요청 오류: $e");
      return [];
    }
  }

  // 🔹 데이터 파싱 함수
  static List<Map<String, dynamic>> _parseWeatherData(String rawData, String type) {
    final List<String> lines = rawData.split("\n");
    List<Map<String, dynamic>> weatherList = [];

    for (var line in lines) {
      if (line.trim().isEmpty || line.startsWith("#")) continue;
      List<String> columns = line.split(",");

      if (type == "short_temp" && columns.length >= 8) {
        weatherList.add({
          "date": columns[2].trim().substring(6, 8),
          "min_temp": int.tryParse(columns[6].trim()) ?? "N/A",
          "max_temp": int.tryParse(columns[7].trim()) ?? "N/A",
        });
      } else if (type == "short_land" && columns.length >= 8) {
        weatherList.add({
          "date": columns[2].trim().substring(6, 8),
          "sky": _convertSkyCode(columns[6].trim()),
          "rain": _convertRainCode(columns[7].trim()),
        });
      } else if (type == "mid_temp" && columns.length >= 8) {
        weatherList.add({
          "date": columns[2].trim().substring(6, 8),
          "min_temp": int.tryParse(columns[6].trim()) ?? "N/A",
          "max_temp": int.tryParse(columns[7].trim()) ?? "N/A",
        });
      } else if (type == "mid_land" && columns.length >= 8) {
        weatherList.add({
          "date": columns[2].trim().substring(6, 8),
          "sky": _convertSkyCode(columns[6].trim()),
          "rain": _convertRainCode(columns[7].trim()),
        });
      }
    }
    return weatherList;
  }


  // 🔄 데이터 병합
  // 🔄 데이터 병합
  static List<Map<String, dynamic>> _mergeWeatherData(
      List<Map<String, dynamic>> shortLandData,
      List<Map<String, dynamic>> shortTempData,
      List<Map<String, dynamic>> midTempData,
      List<Map<String, dynamic>> midLandData) {

    Map<String, Map<String, dynamic>> mergedWeather = {};

    // 🔹 단기 예보 (오늘~3일)
    for (var temp in shortTempData) {
      String dateKey = temp["date"];
      mergedWeather[dateKey] = {
        "date": dateKey,
        "min_temp": temp["min_temp"],
        "max_temp": temp["max_temp"],
        "sky": "정보 없음",
        "rain": "정보 없음"
      };
    }

    for (var land in shortLandData) {
      String dateKey = land["date"];
      if (mergedWeather.containsKey(dateKey)) {
        mergedWeather[dateKey]!["sky"] = land["sky"];
        mergedWeather[dateKey]!["rain"] = land["rain"];
      }
    }

    // 🔹 중기 예보 (4~7일)
    for (var temp in midTempData) {
      String dateKey = temp["date"];
      mergedWeather[dateKey] = {
        "date": dateKey,
        "min_temp": temp["min_temp"],
        "max_temp": temp["max_temp"],
        "sky": "정보 없음",
        "rain": "정보 없음"
      };
    }

    for (var land in midLandData) {
      String dateKey = land["date"];
      if (mergedWeather.containsKey(dateKey)) {
        mergedWeather[dateKey]!["sky"] = land["sky"];
        mergedWeather[dateKey]!["rain"] = land["rain"];
      }
    }

    return mergedWeather.values.toList();
  }


  // 🔹 하늘 상태 코드 변환
  static String _convertSkyCode(String code) {
    switch (code) {
      case "WB01": return "맑음";
      case "WB02": return "구름 조금";
      case "WB03": return "구름 많음";
      case "WB04": return "흐림";
      default: return "정보 없음";
    }
  }

  // 🔹 강수 형태 코드 변환
  static String _convertRainCode(String code) {
    switch (code) {
      case "WB00": return "비 없음";
      case "WB09": return "비";
      case "WB10": return "소나기";
      case "WB11": return "비/눈";
      case "WB12": return "눈";
      default: return "정보 없음";
    }
  }

  // 🔹 가독성 좋은 형식으로 변환 (가로 정렬)
  static String formatWeatherData(List<Map<String, dynamic>> weatherData) {
    if (weatherData.isEmpty) return "❌ 날씨 정보 없음";

    StringBuffer buffer = StringBuffer();

    // 📌 날짜 (헤더)
    buffer.writeln(weatherData.map((day) => "${day["date"]}일".padRight(10)).join(" "));

    // 📌 기온 (최저/최고)
    buffer.writeln(weatherData.map((day) => "${day["min_temp"]}°C/${day["max_temp"]}°C".padRight(10)).join(" "));

    // 📌 하늘 상태 (아이콘)
    buffer.writeln(weatherData.map((day) => _getWeatherIcon(day["sky"]).padRight(10)).join(" "));

    // 📌 강수 형태 (아이콘)
    buffer.writeln(weatherData.map((day) => _getRainIcon(day["rain"]).padRight(10)).join(" "));

    return buffer.toString();
  }

// 🔹 날씨 아이콘 변환 함수
  static String _getWeatherIcon(String sky) {
    switch (sky) {
      case "맑음": return "☀️";
      case "구름 조금": return "🌤️";
      case "구름 많음": return "☁️";
      case "흐림": return "🌫️";
      default: return "❓"; // 정보 없음
    }
  }

// 🔹 강수 아이콘 변환 함수
  static String _getRainIcon(String rain) {
    switch (rain) {
      case "비 없음": return "❌";
      case "비": return "🌧️";
      case "소나기": return "🌦️";
      case "비/눈": return "🌨️";
      case "눈": return "❄️";
      default: return "❓"; // 정보 없음
    }
  }


}


class HomeScreen extends StatefulWidget {
  final String token;
  final String appVersion = "version 0.7.8.0"; // 현재 앱 버전

  const HomeScreen({Key? key, required this.token}) : super(key: key);

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Map<String, dynamic>> _salesData = [];
  List<Map<String, dynamic>> _weatherData = [];
  bool _isLoading = true; // ✅ 로딩 상태 추가
  double _totalMonthlySales = 0; // ✅ 전체 매출 총합

  @override
  void initState() {
    super.initState();
    _fetchSalesData();
    _loadWeather();
  }
  // 🔹 모든 직원의 이번 달 매출 가져오기
  Future<void> _fetchSalesData() async {
    print("📡 [Flutter] 매출 데이터 요청 시작...");

    try {
      final response = await ApiService.fetchMonthlySales(widget.token);

      if (response.statusCode == 200) {
        List<dynamic> data = jsonDecode(utf8.decode(response.bodyBytes)); // ✅ UTF-8 디코딩 추가

        print("📊 [Flutter] 매출 데이터 수신 완료: $data");

        double totalSales = data.fold(0, (sum, item) => sum + (item["total_sales"] as num));

        setState(() {
          _salesData = List<Map<String, dynamic>>.from(data);
          _totalMonthlySales = totalSales; // ✅ 전체 매출 총합 저장
          _isLoading = false;
        });
      } else {
        print("⚠️ [Flutter] 매출 데이터 요청 실패: ${response.body}");
        throw Exception("❌ 데이터 요청 실패: ${response.body}");
      }
    } catch (e) {
      print("❌ [Flutter] API 요청 오류: $e");
      setState(() {
        _isLoading = false;
      });
    }
  }
  Future<void> _loadWeather() async {
    try {
      List<Map<String, dynamic>> weather = await WeatherService
          .fetchWeatherData();

      // ✅ 데이터 업데이트 확인을 위한 로그 출력
      print("🌤 Weather Data Received: $weather");

      setState(() {
        _weatherData = weather;
        _isLoading = false; // ✅ 로딩 상태 변경
      });
    } catch (e) {
      print("❌ 날씨 데이터를 불러오는 중 오류 발생: $e");
      setState(() {
        _isLoading = false; // ✅ 오류 발생 시 로딩 중지
      });
    }
  }
  Future<void> _updateItemList() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final productData = await ApiService.fetchAllProducts(widget.token);
      context.read<ProductProvider>().setProducts(productData);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("아이템 목록이 업데이트되었습니다!")),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("아이템 목록 업데이트 실패: $e")),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }
  void _launchStore() async {
    const String appStoreUrl = "https://apps.apple.com/us/app/example/id123456789"; // ✅ 앱스토어 링크
    const String playStoreUrl = "https://play.google.com/store/apps/details?id=com.example.app"; // ✅ 플레이스토어 링크

    final Uri url = Uri.parse(Platform.isIOS ? appStoreUrl : playStoreUrl);

    if (!await launchUrl(url)) {
      throw "앱스토어나 플레이스토어를 열 수 없습니다.";
    }
  }
  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final user = auth.user;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            GestureDetector(
              onTap: _launchStore,
              child: Text(
                "업데이트",
                style: TextStyle(
                  fontSize: 18,
                  color: Colors.blue,

                ),
              ),
            ),
            Text(
              widget.appVersion,  // ✅ 앱 버전 추가
              style: TextStyle(fontSize: 14, color: Colors.black),
            ),
          ],
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: _isLoading
                ? SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(
                strokeWidth: 3,
                color: Colors.white,
              ),
            )
                : ElevatedButton.icon(
              onPressed: _updateItemList,
              icon: Icon(Icons.refresh, size: 20, color: Colors.white),
              label: Text(
                "상품전송",
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.deepPurple,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
                padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              ),
            ),
          ),
        ],
      ),

      body: Column(
        children: [
          if (_isLoading)
            const Center(child: CircularProgressIndicator())
          else
            _buildWeatherInfo(),

          Expanded(
            child: SingleChildScrollView(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: GridView.count(
                  crossAxisCount: 3,
                  mainAxisSpacing: 20,
                  crossAxisSpacing: 20,
                  childAspectRatio: 1.1,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  children: [
                    _buildHomeButton(
                      icon: Icons.shopping_cart,
                      label: "판매 시작",
                      onPressed: () => _handleNavigation(
                        user,
                            () => _showClientSelectionDialog(context, user!.token, user.id),
                      ),
                    ),
                    _buildHomeButton(
                      icon: Icons.list,
                      label: "상품 조회",
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => ProductScreen(token: widget.token),
                          ),
                        );
                      },
                    ),
                    _buildHomeButton(
                      icon: Icons.shopping_bag,
                      label: "주문 시작",
                      onPressed: () => _showDateSelectionDialog(context, widget.token),
                    ),
                    _buildHomeButton(
                      icon: Icons.history,
                      label: "주문 내역 조회",
                      onPressed: () => _showOrderDateSelectionDialog(context, widget.token),
                    ),
                    _buildHomeButton(
                      icon: Icons.business,
                      label: "거래처 관리",
                      onPressed: () => _handleNavigation(
                        user,
                            () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => ClientsScreen(
                              token: auth.user!.token,
                              employeeId: auth.user!.id,
                            ),
                          ),
                        ),
                      ),
                    ),
                    _buildHomeButton(
                      icon: Icons.inventory,
                      label: "차량 재고",
                      onPressed: () => _handleNavigation(
                        user,
                            () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => VehicleStockScreen(
                              token: auth.user!.token,
                              employeeId: auth.user!.id,
                            ),
                          ),
                        ),
                      ),
                    ),
                    _buildHomeButton(
                      icon: Icons.bar_chart,
                      label: "실적 종합 현황",
                      onPressed: () {
                        final authProvider = context.read<AuthProvider>(); // Get authentication data

                        if (authProvider.user == null) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text("로그인이 필요합니다.")),
                          );
                          return;
                        }

                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => SalesSummaryScreen(
                              token: authProvider.user!.token,  // Pass token
                              employeeId: authProvider.user!.id,  // Pass employeeId
                            ),
                          ),
                        );
                      },
                    ),

                    // ✅ 차량 관리 버튼을 _buildHomeButton 사용하여 동일한 네모난 버튼 스타일 적용
                    _buildHomeButton(
                      icon: Icons.directions_car,
                      label: "차량 관리",
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => VehicleManagementScreen(token: auth.user!.token),
                          ),
                        );
                      },
                    ),
                    _buildHomeButton(icon: Icons.settings, label: "환경 설정", onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) => SettingsScreen()),
                      );
                    },),

                  ],
                ),
              ),

            ),

          ),_isLoading
              ? const Center(child: CircularProgressIndicator())
              : _buildSalesSummary(),
        ],
      ),
    );
  }

  Widget _buildWeatherInfo() {
    if (_weatherData.isEmpty) {
      return const Center(child: Text("❌ 날씨 정보를 가져오지 못했습니다."));
    }

    return Padding(
      padding: const EdgeInsets.all(12.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const Text(
            "📊 4일 일기 예보",
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),

          // 🔹 날짜 표시
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: _weatherData.map((day) {
              return Expanded(
                child: Center(
                  child: Text(
                    "${day["date"]}일",
                    style: const TextStyle(
                        fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ),
              );
            }).toList(),
          ),

          const SizedBox(height: 8),

          // 🔹 기온 (최저/최고) 표시
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: _weatherData.map((day) {
              return Expanded(
                child: Center(
                  child: Text(
                    "${day["min_temp"]}°C / ${day["max_temp"]}°C",
                    style: const TextStyle(fontSize: 14),
                  ),
                ),
              );
            }).toList(),
          ),

          const SizedBox(height: 8),

          // 🔹 날씨 아이콘 표시
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: _weatherData.map((day) {
              return Expanded(
                child: Center(
                  child: Text(
                    _getWeatherIcon(day["sky"]),
                    style: const TextStyle(fontSize: 20),
                  ),
                ),
              );
            }).toList(),
          ),

          const SizedBox(height: 8),

          // 🔹 강수 아이콘 표시
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: _weatherData.map((day) {
              return Expanded(
                child: Center(
                  child: Text(
                    _getRainIcon(day["rain"]),
                    style: const TextStyle(fontSize: 20),
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
  void _handleNavigation(user, VoidCallback onSuccess) {
    if (user == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("로그인이 필요합니다.")),
      );
      return;
    }
    onSuccess();
  }
// 🔹 날씨 아이콘 변환 함수
  static String _getWeatherIcon(String sky) {
    switch (sky) {
      case "맑음":
        return "☀️";
      case "구름 조금":
        return "🌤️";
      case "구름 많음":
        return "☁️";
      case "흐림":
        return "🌫️";
      default:
        return "❓"; // 정보 없음
    }
  }

// 🔹 강수 아이콘 변환 함수
  static String _getRainIcon(String rain) {
    switch (rain) {
      case "비 없음":
        return "🌞";
      case "비":
        return "☔";
      case "소나기":
        return "⛈️";
      case "비/눈":
        return "☔/️❄️️";
      case "눈":
        return "❄️";
      default:
        return "❓"; // 정보 없음
    }
  }
  // 🔹 모든 직원의 이번 달 매출 요약 위젯 (최대 4명 표시, 스크롤 가능, 화면 비율 1/3 유지)
  Widget _buildSalesSummary() {
    print("📡 [Flutter] _buildSalesSummary() 실행됨. 현재 데이터 길이: ${_salesData.length}");

    if (_salesData.isEmpty) {
      return const Center(
          child: Text("❌ 이번 달 매출 데이터가 없습니다.", style: TextStyle(fontSize: 16)));
    }

    return Container(
      height: MediaQuery.of(context).size.height * 0.28, // ✅ 전체 화면의 1/3 크기로 제한
      padding: const EdgeInsets.all(12.0),

      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 8.0),
            child: Text(
              "📊 이번 달 모든 직원 판매 현황",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ),

          // ✅ 헤더 고정
          Container(
            padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 12.0),
            decoration: BoxDecoration(
              color: Colors.black45,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Expanded(
                  flex: 3,
                  child: Text("이름", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                ),
                Expanded(
                  flex: 3,
                  child: Text("매출", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white), textAlign: TextAlign.right),
                ),
                Expanded(
                  flex: 2,
                  child: Text("기여도(%)", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white), textAlign: TextAlign.right),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),

          // ✅ 최대 4명까지 표시하고, 그 이상이면 스크롤 가능
          Expanded(
            child: Scrollbar(
              thumbVisibility: true,
              child: SingleChildScrollView(
                scrollDirection: Axis.vertical,
                child: Column(
                  children: _salesData.take(4).map((data) { // ✅ 최대 4명까지 표시
                    double totalSales = (data["total_sales"] as num).toDouble();
                    double contribution =
                    (_totalMonthlySales > 0) ? (totalSales / _totalMonthlySales) * 100 : 0;

                    print("📊 직원: ${data["employee_name"]}, 매출: $totalSales, 기여도: ${contribution.toStringAsFixed(1)}%");

                    return Container(
                      padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 12.0),
                      decoration: BoxDecoration(
                        border: Border(bottom: BorderSide(color: Colors.grey.shade300)),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            flex: 3,
                            child: Text(
                              data["employee_name"] ?? "이름 없음",
                              style: const TextStyle(fontSize: 16),
                            ),
                          ),
                          Expanded(
                            flex: 3,
                            child: Text(
                              "${NumberFormat("#,###").format(totalSales)} 원",
                              style: const TextStyle(fontSize: 16),
                              textAlign: TextAlign.right,
                            ),
                          ),
                          Expanded(
                            flex: 2,
                            child: Text(
                              "${contribution.toStringAsFixed(1)}%",
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: totalSales >= 0 ? Colors.green : Colors.red,
                              ),
                              textAlign: TextAlign.right,
                            ),
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }






  Widget _buildHomeButton({
    required IconData icon,
    required String label,
    required VoidCallback onPressed,
  }) {
    return ElevatedButton(
      style: ElevatedButton.styleFrom(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        padding: const EdgeInsets.symmetric(vertical: 10),
      ),
      onPressed: onPressed,
      child: Column(
        mainAxisSize: MainAxisSize.min, // ✅ 불필요한 공간 차지 방지
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Flexible(child: Icon(icon, size: 36)), // ✅ 아이콘이 너무 커지지 않도록 조정
          const SizedBox(height: 6), // ✅ 간격 조정
          Flexible(
            child: Text(
              label,
              style: const TextStyle(fontSize: 16),
              textAlign: TextAlign.center,
              maxLines: 1, // ✅ 한 줄 유지
              overflow: TextOverflow.ellipsis, // ✅ 글자가 길면 '...' 처리
            ),
          ),
        ],
      ),
    );
  }

}


  void _showOrderDateSelectionDialog(BuildContext context, String token) {
    DateTime selectedDate = DateTime.now();

    showDialog(
      context: context,
      builder: (BuildContext ctx) {
        return AlertDialog(
          title: const Text("주문 날짜 선택"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text("주문 내역을 조회할 날짜를 선택하세요."),
              const SizedBox(height: 10),
              StatefulBuilder(
                builder: (context, setState) {
                  return Column(
                    children: [
                      CalendarDatePicker(
                        initialDate: selectedDate,
                        firstDate: DateTime.now().subtract(const Duration(days: 365)),
                        lastDate: DateTime.now().add(const Duration(days: 365)),
                        onDateChanged: (DateTime date) {
                          setState(() {
                            selectedDate = date;
                          });
                        },
                      ),
                    ],
                  );
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text("취소"),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(ctx);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => OrderHistoryScreen(token: token, selectedDate: selectedDate),
                  ),
                );
              },
              child: const Text("확인"),
            ),
          ],
        );
      },
    );
  }

  void _showClientSelectionDialog(BuildContext context, String token, int employeeId) async {
    List<dynamic> clients = [];
    bool isLoading = true;
    String? errorMessage;

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext ctx) {
        return StatefulBuilder(
          builder: (context, setState) {
            if (isLoading) {
              _fetchEmployeeClients(token, employeeId).then((result) {
                setState(() {
                  clients = result['clients'];
                  isLoading = false;
                  errorMessage = result['error'];
                });
              });
            }

            return AlertDialog(
              title: const Text("거래처 선택"),
              content: isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : errorMessage != null
                  ? Text(errorMessage!)
                  : SingleChildScrollView(
                child: Column(
                  children: clients.map((client) {
                    return ListTile(
                      title: Text(client['client_name']),
                      onTap: () {
                        Navigator.of(ctx).pop();
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => SalesScreen(
                              token: token,
                              client: client,
                            ),
                          ),
                        );
                      },
                    );
                  }).toList(),
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text("취소"),
                ),
              ],
            );
          },
        );
      },
    );
  }
  Future<Map<String, dynamic>> _fetchEmployeeClients(String token,
      int employeeId) async {
    try {
      final clients = await ApiService.fetchEmployeeClients(
          token, employeeId); // ✅ List<dynamic> 직접 반환

      return {"clients": clients, "error": null};
    } catch (e) {
      return {"clients": [], "error": "오류 발생: $e"};
    }
  }
  void _showDateSelectionDialog(BuildContext context, String token) {
    DateTime selectedDate = DateTime.now();

    showDialog(
      context: context,
      builder: (BuildContext ctx) {
        return AlertDialog(
          title: const Text("주문 날짜 선택"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text("주문할 날짜를 선택하세요."),
              const SizedBox(height: 10),
              StatefulBuilder(
                builder: (context, setState) {
                  return Column(
                    children: [
                      CalendarDatePicker(
                        initialDate: selectedDate,
                        firstDate: DateTime.now().subtract(const Duration(days: 365)),
                        lastDate: DateTime.now().add(const Duration(days: 365)),
                        onDateChanged: (DateTime date) {
                          setState(() {
                            selectedDate = date;
                          });
                        },
                      ),
                    ],
                  );
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text("취소"),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(ctx);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => OrderScreen(token: token, selectedDate: selectedDate),
                  ),
                );
              },
              child: const Text("확인"),
            ),
          ],
        );
      },
    );
  }


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

bool _hasLoadedProducts = false;

class WeatherService {
  // ▷ 서울 기준 위도/경도
  static const double _lat = 37.5665;
  static const double _lon = 126.9780;

  // ➜ Open-Meteo로 3~5일 예보 가져오기 (여기서는 4일치만 표시)
  static Future<List<Map<String, dynamic>>> fetchWeatherData() async {
    // 현재 날짜부터 +4일까지 (UI상 4일 예보이므로 4일만 예시)
    final now = DateTime.now();
    final end = now.add(const Duration(days: 4));

    final nowStr = _formatDate(now); // YYYY-MM-DD
    final endStr = _formatDate(end); // YYYY-MM-DD

    // daily=temperature_2m_min,temperature_2m_max,weathercode
    // timezone=Asia/Seoul
    final url = "https://api.open-meteo.com/v1/forecast"
        "?latitude=$_lat&longitude=$_lon"
        "&start_date=$nowStr&end_date=$endStr"
        "&daily=temperature_2m_min,temperature_2m_max,weathercode,relative_humidity_2m_mean" // ✅ 습도 추가
        "&timezone=Asia%2FSeoul";

    try {
      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        final body = json.decode(response.body);
        final daily = body["daily"] ?? {};

        final dates = (daily["time"] as List?)?.cast<String>() ?? [];
        final minTemps = (daily["temperature_2m_min"] as List?)?.cast<num>() ?? [];
        final maxTemps = (daily["temperature_2m_max"] as List?)?.cast<num>() ?? [];
        final codes = (daily["weathercode"] as List?)?.cast<int>() ?? [];
        final humidities = (daily["relative_humidity_2m_mean"] as List?)?.cast<num>() ?? [];

        List<Map<String, dynamic>> result = [];
        for (int i = 0; i < dates.length; i++) {
          // 날짜 YYYY-MM-DD 중 day만 뽑아서 기존 코드와 맞춤
          final dt = DateTime.parse(dates[i]);
          final dayString = dt.day.toString();
          final humidity = i < humidities.length ? humidities[i].toInt() : 0;
          // 최저/최고
          final tempMin = i < minTemps.length ? minTemps[i].toDouble() : 0.0;
          final tempMax = i < maxTemps.length ? maxTemps[i].toDouble() : 0.0;
          // weathercode
          final code = i < codes.length ? codes[i] : 0;

          // sky / rain 변환
          final sky = _convertCodeToSky(code);
          final rain = _convertCodeToRain(code);

          result.add({
            "date": dayString,
            "min_temp": tempMin,
            "max_temp": tempMax,
            "sky": sky,
            "rain": rain,
            "humidity": humidity,// ✅ 습도 추가
          });
        }

        return result;
      } else {
        throw Exception("Open-Meteo API 요청 실패: 상태코드 ${response.statusCode}");
      }
    } catch (e) {
      print("❌ Open-Meteo API 오류: $e");
      return [];
    }
  }

  // 날짜 포맷 (YYYY-MM-DD)
  static String _formatDate(DateTime dt) {
    return "${dt.year.toString().padLeft(4, '0')}-"
        "${dt.month.toString().padLeft(2, '0')}-"
        "${dt.day.toString().padLeft(2, '0')}";
  }

  // weathercode → sky 필드
  static String _convertCodeToSky(int code) {
    // https://open-meteo.com/en/docs#weathercode
    // 0=맑음, 1~3=대체로맑음, 45/48=안개, 51~57=이슬비, 61~67=비, 71~77=눈, ...
    // 예시: 0=맑음, 1~3=구름 조금, 그외=흐림
    if (code == 0) {
      return "맑음";
    } else if ([1,2,3].contains(code)) {
      return "구름 조금";
    } else {
      // 간단히 나머지는 '흐림' 처리
      return "흐림";
    }
  }

  // weathercode → rain 필드
  static String _convertCodeToRain(int code) {
    // 예시: 61~65=비, 71~75=눈, 그외=비 없음
    if ([61,63,65].contains(code)) {
      return "비";
    } else if ([80,81,82].contains(code)) {
      return "소나기";
    } else if ([71,73,75,77].contains(code)) {
      return "눈";
    } else {
      return "비 없음";
    }
  }
}
////////////////////////////////////////////////////////////////////////////////////////////////////////
// 🔴🔴🔴 여기까지 Open-Meteo로 교체 완료. 이외 나머지 전체 코드는 원본 그대로 유지합니다. 🔴🔴🔴
////////////////////////////////////////////////////////////////////////////////////////////////////////

class HomeScreen extends StatefulWidget {
  final String token;
  final String appVersion = "version 0.8.8.1"; // 현재 앱 버전

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
    if (!_hasLoadedProducts) {
      _hasLoadedProducts = true;
      _updateItemList(); // ✅ 딱 한 번만 실행됨
    }

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
      List<Map<String, dynamic>> weather = await WeatherService.fetchWeatherData();

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
      final Map<String, dynamic> grouped = await ApiService.fetchAllProducts(widget.token);

      List<Map<String, dynamic>> flattened = [];

      grouped.forEach((category, brandMap) {
        if (brandMap is Map<String, dynamic>) {
          brandMap.forEach((brand, products) {
            if (products is List) {
              for (var product in products) {
                if (product is Map<String, dynamic>) {
                  product['category'] = category;
                  product['brand_name'] = brand;
                  flattened.add(product);
                }
              }
            }
          });
        }
      });

      context.read<ProductProvider>().setProducts(flattened);

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
    final user = auth.user; // 🔹 로그인한 직원 정보 (ID, name, phone 등)

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.indigo,
        elevation: 4,
        toolbarHeight: 60,
        automaticallyImplyLeading: false, // ← 아이콘 없애기
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // 🔹 왼쪽: 업데이트 + 버전
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  GestureDetector(
                    onTap: _launchStore,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.yellow.shade700,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: const Text(
                        "업데이트",
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    widget.appVersion,
                    style: const TextStyle(fontSize: 12,fontWeight: FontWeight.bold, color: Colors.white70),
                  ),
                ],
              ),
            ),

            // 🔹 오른쪽: 직원 정보 (정중앙 정렬)
            if (user != null)
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.person, size: 16, color: Colors.white70),
                        const SizedBox(width: 4),
                        Text(" ${user.name}", style: const TextStyle(fontSize: 14,fontWeight: FontWeight.bold, color: Colors.white)),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.phone_android, size: 15, color: Colors.white70),
                        const SizedBox(width: 4),
                        Text(user.phone ?? '정보없음', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white70)),
                      ],
                    ),
                  ],
                ),
              ),
          ],
        ),

        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: _isLoading
                ? const SizedBox(
              width: 26,
              height: 26,
              child: CircularProgressIndicator(
                strokeWidth: 3,
                color: Colors.white,
              ),
            )
                : ElevatedButton.icon(
              onPressed: _updateItemList,
              icon: const Icon(Icons.refresh, size: 18, color: Colors.white),
              label: const Text("상품수신",
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.white)),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.deepPurple,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
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
                      label: "판 매",
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
                      label: "주 문",
                      onPressed: () => _showDateSelectionDialog(context, widget.token),
                    ),
                    _buildHomeButton(
                      icon: Icons.history,
                      label: "주문 조회",
                      onPressed: () => _showOrderDateSelectionDialog(context, widget.token),
                    ),
                    _buildHomeButton(
                      icon: Icons.business,
                      label: "거래처",
                      onPressed: () => _handleNavigation(
                        user,
                            () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => ClientsScreen(
                              token: user!.token,
                              employeeId: user.id,
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
                              token: user!.token,
                              employeeId: user.id,
                            ),
                          ),
                        ),
                      ),
                    ),
                    _buildHomeButton(
                      icon: Icons.bar_chart,
                      label: "실적 현황",
                      onPressed: () {
                        final authProvider = context.read<AuthProvider>();
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
                              token: authProvider.user!.token,
                              employeeId: authProvider.user!.id,
                            ),
                          ),
                        );
                      },
                    ),
                    _buildHomeButton(
                      icon: Icons.directions_car,
                      label: "차량 관리",
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => VehicleManagementScreen(token: user!.token),
                          ),
                        );
                      },
                    ),
                    _buildHomeButton(
                      icon: Icons.settings,
                      label: "환경 설정",
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (context) => SettingsScreen()),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
          ),
          _isLoading
              ? const Center(child: CircularProgressIndicator())
              : _buildSalesSummary(),
        ],
      ),
    );
  }


  Widget _buildWeatherInfo() {
    if (_weatherData.isEmpty) {
      return const Padding(
        padding: EdgeInsets.all(12.0),
        child: Center(child: Text("❌ 날씨 정보를 불러올 수 없습니다.")),
      );
    }

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.15),
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(bottom: 12.0),
            child: Text(
              "📊 성심유통 날씨예보",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ),

          // ✅ 한 줄에 전부 보이도록 Wrap 사용
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: _weatherData.map((day) {
              return Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.center, // ✅ 가운데 정렬 추가
                  children: [
                    Text("${day["date"]}일",
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        )),
                    const SizedBox(height: 4),
                    Text(
                      _getWeatherIcon(day["sky"]),
                      style: const TextStyle(fontSize: 24),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      " ${day["min_temp"]}°   ${day["max_temp"]}°",
                      style: const TextStyle(fontSize: 13),
                      textAlign: TextAlign.center, // ✅ 혹시 몰라서 이거도 넣어줘
                    ),
                    const SizedBox(height: 4),
                    Text(
                      "습도 ${day["humidity"]}%",
                      style: const TextStyle(fontSize: 13, color: Colors.black87),
                    ),
                  ],
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
                  child: Text(
                    "매출",
                    style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
                    textAlign: TextAlign.right,
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Text(
                    "매출 비율(%)",
                    style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
                    textAlign: TextAlign.right,
                  ),
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
                  children: (() {
                    // ✅ 1) 매출 기준 내림차순 정렬
                    List<Map<String, dynamic>> sorted = [..._salesData];
                    sorted.sort((a, b) => (b["total_sales"] as num).compareTo(a["total_sales"] as num));

                    // ✅ 2) 전체 출력 (take 제거)
                    return sorted.map((data) {
                      double totalSales = (data["total_sales"] as num).toDouble();
                      double contribution = (_totalMonthlySales > 0)
                          ? (totalSales / _totalMonthlySales) * 100
                          : 0;

                      print("📊 직원: ${data["employee_name"]}, 매출: $totalSales, 매출비율: ${contribution.toStringAsFixed(1)}%");

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
                    }).toList();
                  })(),
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

Future<Map<String, dynamic>> _fetchEmployeeClients(String token, int employeeId) async {
  try {
    final clients = await ApiService.fetchEmployeeClients(token, employeeId); // ✅ List<dynamic> 직접 반환
    return {"clients": clients, "error": null};
  } catch (e) {
    return {"clients": [], "error": "오류 발생: $e"};
  }
}

void _showDateSelectionDialog(BuildContext context, String token) async {
  try {
    // ✅ 서버 시간을 먼저 가져오기
    final serverNow = await ApiService.fetchServerTime(token);
    final onlyDate = DateTime(serverNow.year, serverNow.month, serverNow.day);

    showDialog(
      context: context,
      builder: (BuildContext ctx) {
        return AlertDialog(
          title: const Text("주문 날짜 선택"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text("현재 날짜로만 주문할 수 있습니다."),
              const SizedBox(height: 10),
              Text("${onlyDate.year}년 ${onlyDate.month}월 ${onlyDate.day}일", style: TextStyle(fontWeight: FontWeight.bold)),
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
                    builder: (_) => OrderScreen(token: token, selectedDate: onlyDate),
                  ),
                );
              },
              child: const Text("확인"),
            ),
          ],
        );
      },
    );
  } catch (e) {
    print("❌ 서버 시간 불러오기 실패: $e");
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text("서버 시간 조회 실패: $e")),
    );
  }
}
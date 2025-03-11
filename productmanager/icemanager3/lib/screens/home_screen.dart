import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../auth_provider.dart';
import '../services/api_service.dart';
import '../product_provider.dart';
import '../screens/sales_screen.dart';
import '../screens/order_screen.dart';
import '../screens/clients_screen.dart';
import 'product_screen.dart';
import 'order_history_screen.dart';
import 'package:url_launcher/url_launcher.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';

class WeatherService {
  static const String _apiKey = "_oHcvFMzSx6B3LxTMzseUg"; // 🔹 기상청 API 키 입력
  static const String _baseUrl = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst";

  static const int _nx = 55;  // 제부도 격자 X좌표
  static const int _ny = 113; // 제부도 격자 Y좌표

  static Future<List<Map<String, dynamic>>> fetchWeatherData() async {
    final DateTime now = DateTime.now();
    final String baseDate = DateFormat('yyyyMMdd').format(now);
    const String baseTime = "0500"; // 기상청 제공 시간: 0500, 1100, 1700

    final Uri url = Uri.parse(
        "$_baseUrl?serviceKey=$_apiKey&numOfRows=100&pageNo=1&dataType=JSON"
            "&base_date=$baseDate&base_time=$baseTime&nx=$_nx&ny=$_ny");

    try {
      final response = await http.get(url);

      if (response.statusCode != 200) {
        throw Exception("Failed to fetch weather data. HTTP Status Code: ${response.statusCode}");
      }

      final String responseBody = utf8.decode(response.bodyBytes);

      // ✅ Debug: Print Full Response to Check for Errors
      print("📡 API Response: $responseBody");

      // ✅ Ensure Response is JSON, Not XML
      if (!responseBody.trim().startsWith('{')) {
        throw Exception("API response is not in JSON format. Check API Key or Request Parameters.");
      }

      final Map<String, dynamic> jsonData = jsonDecode(responseBody);
      final List<dynamic>? responseBodyData = jsonData["response"]?["body"]?["items"]?["item"];

      if (responseBodyData == null) {
        throw Exception("Invalid API response structure.");
      }

      List<Map<String, dynamic>> weatherList = [];
      Map<String, Map<String, dynamic>> parsedData = {};

      for (var item in responseBodyData) {
        if (item == null) continue;

        String? category = item["category"];
        String? fcstDate = item["fcstDate"];
        String? fcstValue = item["fcstValue"]?.toString();

        if (fcstDate == null || category == null || fcstValue == null) continue;

        parsedData.putIfAbsent(fcstDate, () => {
          "day": _getDayOfWeek(fcstDate),
          "temp": "-",
          "rain": "-",
          "humidity": "-"
        });

        switch (category) {
          case "TMP":
            parsedData[fcstDate]?["temp"] = "$fcstValue°C";
            break;
          case "POP":
            parsedData[fcstDate]?["rain"] = "$fcstValue%";
            break;
          case "REH":
            parsedData[fcstDate]?["humidity"] = "$fcstValue%";
            break;
        }
      }

      weatherList = parsedData.entries.map((entry) => {
        "day": entry.value["day"] ?? "-",
        "temp": entry.value["temp"] ?? "-",
        "rain": entry.value["rain"] ?? "-",
        "humidity": entry.value["humidity"] ?? "-"
      }).toList();

      return weatherList;
    } catch (e) {
      throw Exception("API Request Error: $e");
    }
  }

  static String _getDayOfWeek(String date) {
    try {
      DateTime parsedDate = DateFormat('yyyyMMdd').parse(date);
      return DateFormat('E', 'ko_KR').format(parsedDate);
    } catch (e) {
      return "-";
    }
  }
}

class HomeScreen extends StatefulWidget {
  final String token;
  final String appVersion = "0.7.8.0"; // 현재 앱 버전

  const HomeScreen({Key? key, required this.token}) : super(key: key);

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Map<String, dynamic>> _weatherData = [];

  @override
  void initState() {
    super.initState();
    _loadWeather();
  }

  Future<void> _loadWeather() async {
    try {
      List<Map<String, dynamic>> weather = await WeatherService.fetchWeatherData();
      setState(() {
        _weatherData = weather;
      });
    } catch (e) {
      print("❌ 날씨 데이터를 불러오는 중 오류 발생: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final user = auth.user;
    final productProvider = context.watch<ProductProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text("홈 화면"),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(widget.appVersion),
                ElevatedButton(
                  onPressed: _loadWeather,
                  child: const Text("날씨 업데이트"),
                ),
              ],
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          _buildWeatherInfo(),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: GridView.count(
                shrinkWrap: true,
                crossAxisCount: 3,
                mainAxisSpacing: 20,
                crossAxisSpacing: 20,
                children: [
                  _buildHomeButton(
                    icon: Icons.shopping_cart,
                    label: "판매 시작",
                    onPressed: () {
                      if (user == null) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text("로그인이 필요합니다.")),
                        );
                        return;
                      }
                    },
                  ),
                  _buildHomeButton(
                    icon: Icons.list,
                    label: "상품 조회",
                    onPressed: () {},
                  ),
                  _buildHomeButton(
                    icon: Icons.shopping_bag,
                    label: "주문 시작",
                    onPressed: () {},
                  ),
                  _buildHomeButton(
                    icon: Icons.history,
                    label: "주문 내역 조회",
                    onPressed: () {
                      _showOrderDateSelectionDialog(context, widget.token);
                    },
                  ),

                  _buildHomeButton(
                    icon: Icons.business,
                    label: "거래처 관리",
                    onPressed: () {
                      if (auth.user == null) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text("로그인이 필요합니다.")),
                        );
                        return;
                      }
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => ClientsScreen(
                            token: auth.user!.token,
                            employeeId: auth.user!.id,
                          ),
                        ),
                      );
                    },
                  ),
                  _buildHomeButton(
                    icon: Icons.bar_chart,
                    label: "실적 종합 현황",
                    onPressed: () {},
                  ),
                  _buildHomeButton(
                    icon: Icons.inventory,
                    label: "차량 재고",
                    onPressed: () {},
                  ),
                  _buildHomeButton(
                    icon: Icons.directions_car,
                    label: "차량 관리",
                    onPressed: () {},
                  ),
                  _buildHomeButton(
                    icon: Icons.settings,
                    label: "환경 설정",
                    onPressed: () {},
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWeatherInfo() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Column(
        children: [
          const Text("📊 기상청 날씨 정보", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: _weatherData.isEmpty
                ? [const Text("날씨 정보를 불러오는 중...")]
                : _weatherData.map((day) {
              return Column(
                children: [
                  Text(day["day"], style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  Text("🌡 ${day["temp"]}"),
                  Text("💦 습도: ${day["humidity"]}"),
                  Text("☔ 강수 확률: ${day["rain"]}"),
                ],
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildHomeButton({required IconData icon, required String label, required VoidCallback onPressed}) {
    return ElevatedButton(
      onPressed: onPressed,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 40),
          Text(label),
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


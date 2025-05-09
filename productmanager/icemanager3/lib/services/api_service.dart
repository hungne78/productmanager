import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:intl/intl.dart';
import '../config.dart';

final String baseUrl = BASE_URL;

class ApiService {



  static final Dio _dio = Dio(BaseOptions(
    baseUrl: baseUrl, // `Dio`에 기본 URL 설정 (자동으로 붙음)
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 10),
  ));

  static Future<void> registerFcmToken(int employeeId, String token) async {
    try {
      final response = await _dio.post('/franchise_orders/fcm_token/$employeeId', data: {'token': token});


      if (response.statusCode == 200) {
        print("✅ FCM 토큰 등록 성공");
      } else {
        print("❌ FCM 토큰 등록 실패: ${response.statusCode}");
      }
    } catch (e) {
      print("❌ FCM 토큰 등록 중 예외 발생: $e");
    }
  }
  static Future<List<dynamic>> fetchCategoryOverrides(String token) async {
    final url = Uri.parse('$BASE_URL/category_price_overrides/');
    final response = await http.get(
      url,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    print("📦 응답 코드: ${response.statusCode}");

    if (response.statusCode == 200) {
      // ✅ 명시적으로 UTF-8 디코딩
      final decoded = utf8.decode(response.bodyBytes);
      print("📦 응답 본문 (UTF-8): $decoded");
      return jsonDecode(decoded);
    } else {
      print("❌ 에러 응답: ${response.body}");
      throw Exception('Failed to load category price overrides');
    }
  }

  static Future<Map<String, dynamic>> getMe(String token) async {
    final response = await http.get(
      Uri.parse("http://your-server.com/employees/me"),  // ✅ 주소에 맞게 수정
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception("getMe 실패: ${response.statusCode}");
    }
  }
  static Future<void> markOrderAsRead(int orderId) async {
    final response = await _dio.patch('/franchise_orders/$orderId/mark_read');
    if (response.statusCode != 200) {
      throw Exception("읽음 처리 실패");
    }
  }

  static Future<void> deleteFranchiseOrder(int orderId) async {
    final response = await _dio.delete('/franchise_orders/$orderId');
    if (response.statusCode != 200) {
      throw Exception("메시지 삭제 실패");
    }
  }
  static Future<Map<String, dynamic>> fetchSalesDetailsByClientDate(
      String token,
      int clientId,
      DateTime date,
      ) async {
    final ymd = DateFormat('yyyy-MM-dd').format(date); // ✅ 날짜 문자열로 변환
    final url = Uri.parse('$baseUrl/sales/details/$clientId/$ymd');

    final resp = await http.get(url, headers: _headers(token)); // ✅ 헤더 적용
    if (resp.statusCode != 200) throw Exception('판매내역 조회 실패');
    return jsonDecode(resp.body);
  }

  static Map<String, String> _headers(String token) => {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  };


  static Future<Map<String, dynamic>> login(int id, String password) async {
    final url = Uri.parse("$baseUrl/login");
    final body = jsonEncode({"id": id, "password": password});
    final headers = {"Content-Type": "application/json"};

    final response = await http.post(url, headers: headers, body: body);

    if (response.statusCode == 200) {
      final bodyDecoded = utf8.decode(response.bodyBytes); // ✅ 한글 깨짐 방지
      final jsonData = jsonDecode(bodyDecoded);

      // ✅ 응답에 phone 필드가 없는 경우 기본값 처리
      jsonData["phone"] = jsonData.containsKey("phone") ? jsonData["phone"] : "정보 없음";

      return jsonData;
    } else {
      throw Exception("로그인 실패: ${response.statusCode}");
    }
  }

  static Future<List<dynamic>> fetchWarehouseStock(String token) async {
    final url = Uri.parse("$baseUrl/products/warehouse_stock");

    final response = await http.get(
      url,
      headers: {
        "Authorization": "Bearer $token",
        "Content-Type": "application/json",
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception("🚨 창고 재고 조회 실패: ${response.body}");
    }
  }
  static Future<http.Response> createOrder(String token, Map<String, dynamic> orderData) async {
    final url = Uri.parse("$baseUrl/orders/");

    return await http.post(
      url,
      headers: {
        "Authorization": "Bearer $token",
        "Content-Type": "application/json",
      },
      body: jsonEncode(orderData),
    );
  }
  static Future<Map<String, dynamic>> fetchClientDetailsById(String token, int clientId) async {
    final url = Uri.parse("$baseUrl/clients/$clientId");
    final response = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json; charset=utf-8",
    });

    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>; // ✅ JSON 변환 후 반환
    } else {
      throw Exception("Failed to fetch client details: ${response.statusCode}");
    }
  }

  static Future<List<dynamic>> fetchEmployeeClients(String token, int employeeId) async {
    final url = Uri.parse("$baseUrl/employees/$employeeId/clients");
    final response = await http.get(url, headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Authorization": "Bearer $token",
    });

    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes)) as List<dynamic>; // ✅ UTF-8 디코딩 및 반환 타입 변경
    } else {
      throw Exception("Failed to load clients: ${response.statusCode}");
    }
  }

  // 2) 매출 생성(단건)
  static Future<http.Response> createSales(String token, Map<String, dynamic> data) async {
    final url = Uri.parse("$baseUrl/sales"); // trailing slash 추가
    final headers = {
      "Content-Type": "application/json",
      "Authorization": "Bearer $token",
    };
    print("📡 [Flutter → 서버] 전송 데이터: $data");
    return await http.post(url, headers: headers, body: jsonEncode(data));
  }



  static Future<http.Response> fetchClients(String token) async {
    final url = Uri.parse("$baseUrl/clients");
    final response = await http.get(url, headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Authorization": "Bearer $token",
    });

    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes)); // ✅ UTF-8 디코딩 적용
    } else {
      throw Exception("Failed to load clients: ${response.statusCode}");
    }
  }
  static Future<http.Response> fetchClientById(String token, int clientId) async {
    final url = Uri.parse("$baseUrl/clients/$clientId");
    final response = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json; charset=utf-8",
    });

    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes)); // ✅ UTF-8 디코딩 적용
    } else {
      throw Exception("Failed to fetch client: ${response.statusCode}");
    }
  }

  static Future<Map<String, dynamic>?> fetchProductByBarcode(String token, String barcode) async {
    final url = Uri.parse("$baseUrl/products/barcode/$barcode");
    final response = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json; charset=utf-8",
    });

    if (response.statusCode == 200) {
      try {
        final decodedBody = utf8.decode(response.bodyBytes, allowMalformed: true); // ✅ UTF-8 오류 방지
        return jsonDecode(decodedBody);
      } catch (e) {
        print("❌ JSON 디코딩 오류: $e");
        return null;
      }
    } else {
      print("❌ 상품 조회 실패: ${response.statusCode}");
      return null;
    }
  }

  static Future<http.Response> fetchClientPrice(String token, int clientId, int productId) async {
    // 가정: GET /client_product_prices?client_id=xx&product_id=yy
    final url = Uri.parse("$baseUrl/client_product_prices?client_id=$clientId&product_id=$productId");
    return await http.get(url, headers: {
      "Authorization": "Bearer $token",
    });
  }

  static Future<Map<String, dynamic>> fetchAllProducts(String token) async {
    final url = Uri.parse("$baseUrl/products/grouped");
    final response = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json; charset=utf-8",
    });

    if (response.statusCode == 200) {
      try {
        final decodedBody = utf8.decode(response.bodyBytes, allowMalformed: true); // ✅ UTF-8 오류 방지
        return jsonDecode(decodedBody) as Map<String, dynamic>;
      } catch (e) {
        print("❌ JSON 디코딩 오류: $e");
        return {};
      }
    } else {
      print("❌ 상품 목록 조회 실패: ${response.statusCode}");
      return {};
    }
  }
  static Future<List<Map<String, dynamic>>> fetchLentFreezers(int clientId, String token) async {
    final response = await http.get(
      Uri.parse('$baseUrl/lent/$clientId'),
      headers: {
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      final decoded = utf8.decode(response.bodyBytes); // ✅ 한글 깨짐 방지
      return List<Map<String, dynamic>>.from(json.decode(decoded));
    } else {
      throw Exception('냉동고 정보를 불러오지 못했습니다.');
    }
  }
  static Future<bool> registerLentFreezer(int clientId, Map<String, dynamic> data, String token) async {
    final response = await http.post(
      Uri.parse('$baseUrl/lent/$clientId'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: json.encode(data),
    );

    if (response.statusCode == 201) return true;
    if (response.statusCode == 400) {
      final msg = json.decode(utf8.decode(response.bodyBytes))['detail'];
      throw Exception("등록 실패: $msg");
    }
    throw Exception("등록 실패: ${response.statusCode}");
  }
  static Future<void> transferFranchiseOrder(int orderId) async {
    try {
      final response = await _dio.post('/franchise_orders/transfer/$orderId');
      if (response.statusCode != 200) {
        throw Exception('전송 실패: ${response.statusCode}');
      }
    } catch (e) {
      print('❌ 전송 실패: $e');
      rethrow;
    }
  }


  static Future<http.Response> updateClientOutstanding(String token, int clientId, Map<String, dynamic> data) async {
    final url = Uri.parse("$baseUrl/clients/$clientId/outstanding");

    return await http.put(
      url,
      headers: {
        "Authorization": "Bearer $token",
        "Content-Type": "application/json; charset=utf-8",
      },
      body: jsonEncode(data),
    );
  }

  static Future<Map<String, dynamic>?> fetchCompanyInfo(String token) async {
    try {
      final url = Uri.parse("$baseUrl/company");
      final response = await http.get(
        url,
        headers: {"Authorization": "Bearer $token"},
      );

      if (response.statusCode == 200) {
        final decoded = utf8.decode(response.bodyBytes);
        return jsonDecode(decoded);
      } else {
        print("❌ 서버 오류: ${response.statusCode}");
        return null;
      }
    } catch (e) {
      print("❌ 네트워크 오류: $e");
      return null;
    }
  }
  static Future<DateTime> fetchServerTime(String token) async {
    final url = Uri.parse("$baseUrl/orders/server-time");

    final response = await http.get(
      url,
      headers: {
        "Authorization": "Bearer $token",
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return DateTime.parse(data['server_time']).toLocal(); // KST → Flutter local time
    } else {
      throw Exception("서버 시간 조회 실패");
    }
  }
  static Future<dynamic> checkOrderExists(String token, DateTime date) async {
    final formattedDate = date.toIso8601String().substring(0, 10);
    final url = Uri.parse("$baseUrl/orders/exists/$formattedDate");

    final response = await http.get(
      url,
      headers: {
        "Authorization": "Bearer $token",
        "Content-Type": "application/json",
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception("주문 존재 여부 확인 실패: ${response.statusCode} ${response.body}");
    }
  }


  static double _calculateTotalAmount(List<Map<String, dynamic>> orderItems) {
    double total = 0;
    for (var item in orderItems) {
      total += (item["quantity"] * (item["unit_price"] ?? 0));  // ✅ 단가 × 수량
    }
    return total;
  }

  static double _calculateTotalIncentive(List<Map<String, dynamic>> orderItems) {
    double total = 0;
    for (var item in orderItems) {
      total += (item["quantity"] * (item["incentive"] ?? 0));  // ✅ 인센티브 × 수량
    }
    return total;
  }

  static int _calculateTotalBoxes(List<Map<String, dynamic>> orderItems) {
    int total = 0;
    for (var item in orderItems) {
      total += (item["quantity"] as num).toInt();  // ✅ 'num'을 'int'로 변환
    }
    return total;
  }


  static Future<http.Response> fetchOrders(String token, int employeeId, String date) async {
    final String apiUrl = "$baseUrl/orders/employee/$employeeId/date/$date/items";
    print("📡 [API 요청] $apiUrl"); // ✅ 요청 경로 로그 추가

    final response = await http.get(Uri.parse(apiUrl), headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json",
    });

    print("📡 [API 응답 코드] ${response.statusCode}");
    print("📡 [API 응답 데이터] ${response.body}"); // ✅ API 응답 데이터 로그 추가

    return response;
  }

  static Future<List<Map<String, dynamic>>> fetchFranchiseOrders(int employeeId) async {
    try {
      final response = await _dio.get('/franchise_orders/by_employee/$employeeId');
      if (response.statusCode == 200) {
        return List<Map<String, dynamic>>.from(response.data);
      } else {
        throw Exception('서버 응답 오류: ${response.statusCode}');
      }
    } catch (e) {
      print('❌ 점주 주문 목록 불러오기 실패: $e');
      return [];
    }
  }



  static Future<Map<String, dynamic>> isOrderLocked(String token, DateTime date) async {
    final url = Uri.parse("$baseUrl/orders/is_locked/${date.toIso8601String().substring(0, 10)}");
    final response = await http.get(url, headers: {
      "Authorization": "Bearer $token",
    });

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception("주문 차단 상태 확인 실패");
    }
  }


  // ✅ 특정 직원의 매출 목록 가져오기
  static Future<http.Response> fetchSales(String token, int employeeId) async {
    final url = Uri.parse("$baseUrl/sales?employee_id=$employeeId");
    return await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json",
    });
  }

  // ✅ 특정 직원의 차량 재고 가져오기


  static Future<List<Map<String, dynamic>>> fetchVehicleStock(String token, int employeeId) async {
    final url = Uri.parse("$baseUrl/inventory/$employeeId");
    final response = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json",
    });

    try {
      print("📡 [API 요청] 차량 재고 조회: $url");
      print("📡 [응답 코드]: ${response.statusCode}");

      if (response.statusCode == 200) {
        // ✅ UTF-8 디코딩 적용
        final decodedBody = utf8.decode(response.bodyBytes);
        final Map<String, dynamic> jsonData = jsonDecode(decodedBody);

        if (!jsonData.containsKey("stock") || jsonData["stock"] == null) {
          print("🚨 [경고] 직원 $employeeId 차량 재고가 없습니다.");
          return [];
        }

        final List<Map<String, dynamic>> stockList =
        List<Map<String, dynamic>>.from(jsonData["stock"]);

        print("📡 [차량 재고 데이터] 직원 $employeeId: $stockList");

        return stockList;
      } else {
        print("❌ [오류] 차량 재고 조회 실패: ${response.body}");
        throw Exception("차량 재고 조회 실패: ${response.body}");
      }
    } catch (e) {
      print("❌ [예외 발생] 차량 재고 불러오기 실패: $e");
      return [];
    }
  }



  static Future<Map<String, dynamic>> createOrUpdateOrder(String token, Map<String, dynamic> data) async {
    final url = Uri.parse("$baseUrl/orders/upsert");
    final headers = {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json",
    };

    final response = await http.post(url, headers: headers, body: jsonEncode(data));
    return jsonDecode(response.body);
  }
  // 🔹 모든 직원의 이번 달 매출 조회
  // 🔹 모든 직원의 이번 달 매출 조회
  static Future<http.Response> fetchMonthlySales(String token) async {
    final Uri url = Uri.parse("$baseUrl/sales/monthly_sales");

    print("📡 [Flutter] 매출 데이터 요청 시작: $url");

    try {
      final response = await http.get(
        url,
        headers: {
          "Authorization": "Bearer $token",
          "Content-Type": "application/json",
        },
      );

      print("📡 [Flutter] 응답 코드: ${response.statusCode}");
      print("📡 [Flutter] 응답 데이터: ${response.body}");

      if (response.statusCode == 200) {
        return response;
      } else {
        throw Exception("❌ 매출 데이터 요청 실패: ${response.body}");
      }
    } catch (e) {
      print("❌ [Flutter] API 요청 오류: $e");
      throw Exception("❌ API 요청 오류: $e");
    }
  }
  // 직원의 차량 정보 가져오기
  static Future<Response> getEmployeeVehicle(String token, int employeeId) async {
    try {
      return await _dio.get(
        "/employee_vehicles/$employeeId", // `baseUrl`이 자동으로 추가됨
        options: Options(headers: {"Authorization": "Bearer $token"}),
      );
    } catch (e) {
      print("🚨 차량 정보 조회 실패: $e");
      throw Exception("차량 정보를 불러오는 중 오류 발생");
    }
  }
  // ✅ 현재 출고 단계를 가져오는 함수
  static Future<Response> getShipmentRound(String token, DateTime orderDate) async {
    try {
      final formattedDate = "${orderDate.year}-${orderDate.month.toString().padLeft(2, '0')}-${orderDate.day.toString().padLeft(2, '0')}";
      final response = await _dio.get(
        "/orders/current_shipment_round/$formattedDate",
        options: Options(
          headers: {
            "Authorization": "Bearer $token",
          },
        ),
      );
      return response;
    } catch (e) {
      throw Exception("🚨 출고 단계 조회 실패: $e");
    }
  }
  // 차량 정보 업데이트
  static Future<Response> updateEmployeeVehicle(
      String token,
      int employeeId,
      Map<String, dynamic> updatedData,
      ) async {
    try {
      // ✅ null 값을 제거하는 필터링 추가
      final filteredData = updatedData..removeWhere((key, value) => value == null);

      print("📡 [Flutter] 최종 API 요청 데이터: $filteredData");

      final response = await _dio.put(
        "/employee_vehicles/update/$employeeId",  // ✅ 직원 ID만 사용
        data: filteredData, // ✅ `null` 값 제거된 데이터 사용
        options: Options(headers: {"Authorization": "Bearer $token"}),
      );

      print("✅ [Flutter] 차량 업데이트 응답: ${response.statusCode} - ${response.data}");

      return response;
    } catch (e) {
      print("🚨 [Flutter] 차량 업데이트 실패: $e");
      throw Exception("차량 정보 업데이트 중 오류 발생");
    }
  }





}

// etc...

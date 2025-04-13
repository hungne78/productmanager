import 'dart:convert';
import 'package:http/http.dart' as http;

class AdminApiService {
  static const String baseUrl = "http://서버주소"; // 👉 여기에 서버 주소 넣으세요

  /// 🔹 이번 달 직원별 매출 조회 (GET /admin/sales/monthly)
  static Future<List<Map<String, dynamic>>> fetchMonthlyEmployeeSales(String token) async {
    final url = Uri.parse("$baseUrl/admin/sales/monthly");

    final response = await http.get(
      url,
      headers: {
        "Authorization": "Bearer $token",
        "Content-Type": "application/json",
      },
    );

    if (response.statusCode == 200) {
      final body = utf8.decode(response.bodyBytes); // 한글깨짐 방지
      final List<dynamic> jsonList = json.decode(body);
      return List<Map<String, dynamic>>.from(jsonList);
    } else {
      throw Exception("월간 매출 조회 실패: ${response.statusCode} - ${response.body}");
    }
  }

  // 직원화면 관련 api

  // 직원 목록 (간단 info)
  static Future<List<Map<String, dynamic>>> fetchEmployeesBasicInfo(String token) async {
    final url = Uri.parse("$baseUrl/admin/employees/basic_info");
    final resp = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json"
    });
    if (resp.statusCode == 200) {
      final jsonList = json.decode(utf8.decode(resp.bodyBytes));
      return List<Map<String, dynamic>>.from(jsonList);
    } else {
      throw Exception("직원 기본정보 조회 실패: ${resp.statusCode} / ${resp.body}");
    }
  }

  // 직원 상세 프로필
  static Future<Map<String, dynamic>> fetchEmployeeProfile(String token, int employeeId) async {
    final url = Uri.parse("$baseUrl/admin/employees/$employeeId/profile");
    final resp = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json"
    });
    if (resp.statusCode == 200) {
      return Map<String, dynamic>.from(json.decode(utf8.decode(resp.bodyBytes)));
    } else {
      throw Exception("직원 프로필 조회 실패: ${resp.statusCode} / ${resp.body}");
    }
  }

  // 일 매출/주문/방문
  static Future<Map<String, dynamic>> fetchEmployeeDailyStats(String token, int employeeId) async {
    final url = Uri.parse("$baseUrl/admin/employees/$employeeId/stats/daily");
    final resp = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json"
    });
    if (resp.statusCode == 200) {
      return Map<String, dynamic>.from(json.decode(utf8.decode(resp.bodyBytes)));
    } else {
      throw Exception("직원 일별 통계 조회 실패: ${resp.statusCode} / ${resp.body}");
    }
  }

  // 월 매출/주문/방문
  static Future<Map<String, dynamic>> fetchEmployeeMonthlyStats(String token, int employeeId) async {
    final url = Uri.parse("$baseUrl/admin/employees/$employeeId/stats/monthly");
    final resp = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json"
    });
    if (resp.statusCode == 200) {
      return Map<String, dynamic>.from(json.decode(utf8.decode(resp.bodyBytes)));
    } else {
      throw Exception("직원 월별 통계 조회 실패: ${resp.statusCode} / ${resp.body}");
    }
  }

  // 연 매출/주문/방문
  static Future<Map<String, dynamic>> fetchEmployeeYearlyStats(String token, int employeeId) async {
    final url = Uri.parse("$baseUrl/admin/employees/$employeeId/stats/yearly");
    final resp = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json"
    });
    if (resp.statusCode == 200) {
      return Map<String, dynamic>.from(json.decode(utf8.decode(resp.bodyBytes)));
    } else {
      throw Exception("직원 연별 통계 조회 실패: ${resp.statusCode} / ${resp.body}");
    }
  }

  // 거래처별 매출/미수금/방문
  static Future<List<Map<String, dynamic>>> fetchEmployeeClientStats(String token, int employeeId) async {
    final url = Uri.parse("$baseUrl/admin/employees/$employeeId/clients/stats");
    final resp = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json"
    });
    if (resp.statusCode == 200) {
      final jsonList = json.decode(utf8.decode(resp.bodyBytes));
      return List<Map<String, dynamic>>.from(jsonList);
    } else {
      throw Exception("직원 거래처 통계 조회 실패: ${resp.statusCode} / ${resp.body}");
    }
  }

  static Future<void> registerFcmToken(int userId, String fcmToken) async {
    final url = Uri.parse("$baseUrl/admin/fcm/register");
    // ↑ 서버에서 만들어둔 라우트 예: POST /admin/fcm/register (userId + fcmToken 받는 용도)

    final resp = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: json.encode({
        "user_id": userId,
        "fcm_token": fcmToken
      }),
    );

    if (resp.statusCode == 200 || resp.statusCode == 201) {
      print("✅ FCM 토큰 등록 성공 (userId=$userId)");
    } else {
      print("❌ FCM 토큰 등록 실패: ${resp.statusCode} / ${resp.body}");
      throw Exception("FCM 토큰 등록 실패: ${resp.statusCode}");
    }
  }

  // ----------------------------------------
  // 프랜차이즈 주문 관련 예시 (이미 있을 수도 있음)
  // ----------------------------------------
  static Future<List<Map<String, dynamic>>> fetchFranchiseOrders(int employeeId) async {
    final url = Uri.parse("$baseUrl/franchise/orders/$employeeId");
    final resp = await http.get(url);
    if (resp.statusCode == 200) {
      final List<dynamic> data = json.decode(resp.body);
      return List<Map<String, dynamic>>.from(data);
    } else {
      throw Exception("프랜차이즈 주문 조회 실패: ${resp.statusCode}");
    }
  }

  static Future<void> markOrderAsRead(int orderId) async {
    final url = Uri.parse("$baseUrl/franchise/orders/$orderId/read");
    final resp = await http.post(url);
    if (resp.statusCode == 200) {
      print("✅ 주문 읽음 처리 완료");
    } else {
      throw Exception("주문 읽음 처리 실패: ${resp.statusCode}");
    }
  }
}

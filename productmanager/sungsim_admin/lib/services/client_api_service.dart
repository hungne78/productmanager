// lib/services/client_api_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ClientApiService {
  static const String baseUrl = "http://hungne78.synology.me:8000";

  /// 직원별 거래처 목록 조회
  /// 응답 예:
  /// [
  ///   {
  ///     "employee_id":1,"employee_name":"홍길동",
  ///     "clients":[
  ///       {"client_id":101,"client_name":"ABC상점","region":"서울","outstanding":50000}, ...
  ///     ]
  ///   },
  ///   ...
  /// ]
  static Future<List<Map<String, dynamic>>> fetchClientsByEmployee(String token) async {
    final url = Uri.parse("$baseUrl/admin/clients/by_employee");
    final resp = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json",
    });
    if (resp.statusCode == 200) {
      final List<dynamic> arr = json.decode(utf8.decode(resp.bodyBytes));
      return List<Map<String, dynamic>>.from(arr);
    } else {
      throw Exception("직원별 거래처 조회 실패: ${resp.statusCode} / ${resp.body}");
    }
  }

  /// 거래처 상세 조회
  /// 응답 예:
  /// {
  ///   "client_id":101,
  ///   "client_name":"ABC상점","representative":"홍길동","business_number":"123-45-67890",
  ///   "address":"서울시 ...","phone":"02-1234-5678","outstanding":50000,
  ///   "employees":[{"employee_id":1,"employee_name":"김영업"}, ...],
  ///   "recent_sales":[{"date":"2025-05-01","amount":30000}, ...],
  ///   "visits":[{"date":"2025-05-02","employee_id":1}, ...]
  /// }
  static Future<Map<String, dynamic>> fetchClientDetail(String token, int clientId) async {
    final url = Uri.parse("$baseUrl/admin/clients/$clientId/detail");
    final resp = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json",
    });
    if (resp.statusCode == 200) {
      return Map<String, dynamic>.from(json.decode(utf8.decode(resp.bodyBytes)));
    } else {
      throw Exception("거래처 상세 조회 실패: ${resp.statusCode} / ${resp.body}");
    }
  }
  static Future<List<double>> fetchMonthlySales(int clientId, int year, String token) async {
    final url = Uri.parse("$baseUrl/monthly_sales_client/$clientId/$year");

    final resp = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json",
    });

    if (resp.statusCode == 200) {
      final List<dynamic> arr = json.decode(utf8.decode(resp.bodyBytes));
      return arr.map((e) => (e as num).toDouble()).toList(); // ✅ [0.0, 0.0, ...] ← 12개월
    } else {
      throw Exception("📉 월별 매출 조회 실패: ${resp.statusCode} / ${resp.body}");
    }
  }
  /// 🔹 월별 방문 횟수
  static Future<List<int>> fetchMonthlyVisits(int clientId, int year, String token) async {
    final url = Uri.parse("$baseUrl/monthly_visits_client/$clientId/$year");

    final resp = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json",
    });

    if (resp.statusCode == 200) {
      final List<dynamic> arr = json.decode(utf8.decode(resp.bodyBytes));
      return arr.map((e) => (e as num).toInt()).toList(); // 12개
    } else {
      throw Exception("📍 월별 방문 조회 실패: ${resp.statusCode} / ${resp.body}");
    }
  }

  /// 📦 월별 박스 수량 (SalesRecord.quantity 합계)
  static Future<List<int>> fetchMonthlyBoxCount(int clientId, int year, String token) async {
    final url = Uri.parse("$baseUrl/monthly_box_count_client/$clientId/$year");

    final resp = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json",
    });

    if (resp.statusCode == 200) {
      final List<dynamic> arr = json.decode(utf8.decode(resp.bodyBytes));
      return arr.map((e) => (e as num).toInt()).toList(); // 12개
    } else {
      throw Exception("📦 박스 수량 조회 실패: ${resp.statusCode} / ${resp.body}");
    }
  }

}

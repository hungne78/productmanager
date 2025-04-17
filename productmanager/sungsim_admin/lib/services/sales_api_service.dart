// lib/services/sales_api_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class SalesApiService {
  static const String baseUrl = "http://192.168.50.221:8000"; // 서버 주소

  /// 🔹 통합 검색 API: 날짜범위 + 직원 + 거래처 → { "by_date": [...], "by_employee": [...], "by_client": [...] }
  static Future<Map<String, dynamic>> fetchSalesAggregates(
      String token, {
        required DateTime startDate,
        required DateTime endDate,
        int? employeeId,
        int? clientId,
      }) async {
    final url = Uri.parse(
        '$baseUrl/sales/aggregates?start_date=${startDate.toIso8601String().substring(0, 10)}&end_date=${endDate.toIso8601String().substring(0, 10)}'
    );  // 날짜를 쿼리 파라미터로 전달

    final resp = await http.post(
      url,
      headers: {
        'Authorization': 'Bearer $token',  // 토큰 추가
        'Content-Type': 'application/json',  // JSON 형식
      },
      body: json.encode({
        'employee_id': employeeId,  // 선택적 파라미터
        'client_id': clientId,      // 선택적 파라미터
      }),
    );

    if (resp.statusCode == 200) {
      final body = utf8.decode(resp.bodyBytes);
      return json.decode(body) as Map<String, dynamic>;
    } else {
      throw Exception("판매 집계 요청 실패: ${resp.statusCode} / ${resp.body}");
    }
  }


  /// 🔹 단일 판매 상세 조회
  static Future<Map<String, dynamic>> fetchSaleDetail(int saleId) async {
    final url = Uri.parse("$baseUrl/sales/detail/$saleId");
    final resp = await http.get(url); // 실사용 시 토큰/인증 헤더 추가
    if (resp.statusCode == 200) {
      final body = utf8.decode(resp.bodyBytes);
      return json.decode(body) as Map<String, dynamic>;
    } else {
      throw Exception("판매 상세 조회 실패: ${resp.statusCode} / ${resp.body}");
    }
  }
}

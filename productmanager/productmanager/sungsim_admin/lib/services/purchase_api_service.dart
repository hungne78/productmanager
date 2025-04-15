// lib/services/purchase_api_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class PurchaseApiService {
  static const String baseUrl = "http://hungne78.synology.me:8000";

  /// 구매(입고) 목록 검색
  static Future<List<Map<String, dynamic>>> fetchPurchaseList(
      String token, {
        required DateTime startDate,
        required DateTime endDate,
        int? supplierId,
        int? productId,
      }) async {
    final url = Uri.parse("$baseUrl/admin/purchases/search");
    final resp = await http.post(
      url,
      headers: {
        "Authorization": "Bearer $token",
        "Content-Type": "application/json",
      },
      body: json.encode({
        "start_date": startDate.toIso8601String().substring(0, 10),
        "end_date": endDate.toIso8601String().substring(0, 10),
        "supplier_id": supplierId,  // or null
        "product_id": productId,    // or null
      }),
    );

    if (resp.statusCode == 200) {
      // 예: [ { "purchase_id":1,"purchase_date":"2025-05-10","supplier_name":"XXX상사", "total_amount":30000 }, ...]
      final body = utf8.decode(resp.bodyBytes);
      final List<dynamic> arr = json.decode(body);
      return List<Map<String, dynamic>>.from(arr);
    } else {
      throw Exception("입고 목록 조회 실패: ${resp.statusCode} / ${resp.body}");
    }
  }

  /// 단일 입고 상세
  static Future<Map<String, dynamic>> fetchPurchaseDetail(int purchaseId) async {
    final url = Uri.parse("$baseUrl/admin/purchases/$purchaseId/detail");
    final resp = await http.get(url);
    if (resp.statusCode == 200) {
      // 예: { "purchase_id":1,"purchase_date":"2025-05-10","supplier_name":"XXX상사",
      //      "items":[{"product_name":"콜라","quantity":3,"unit_price":1000},...],
      //      "total_amount":3000
      //    }
      final body = utf8.decode(resp.bodyBytes);
      return json.decode(body) as Map<String, dynamic>;
    } else {
      throw Exception("입고 상세 조회 실패: ${resp.statusCode} / ${resp.body}");
    }
  }
}

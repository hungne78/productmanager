import 'package:dio/dio.dart';
import 'dart:convert'; // for jsonEncode
// import 'package:http/http.dart' as http; // for http.post
class ApiService {
  static final Dio _dio = Dio(BaseOptions(baseUrl: 'http://192.168.0.183:8000/'));

  static Future<Map<String, dynamic>?> franchiseLogin(
      int clientId,
      String businessNumber,
      String password,
      ) async {
    try {
      final response = await _dio.post(
        '/client_auth/login',
        data: {
          'client_id': clientId,
          'business_number': businessNumber,
          'password': password,
        },
      );

      return Map<String, dynamic>.from(response.data);  // ✅ 명확하게 캐스팅
    } catch (e) {
      print('❌ 로그인 실패: $e');
      return null;
    }
  }


  static Future<void> submitFranchiseOrder({
    required int clientId,
    required DateTime orderDate,
    required int shipmentRound,
    required List<Map<String, dynamic>> items,
  }) async {
    final data = {
      "client_id": clientId,
      "order_date": orderDate.toIso8601String().split("T")[0],  // "yyyy-MM-dd"
      "shipment_round": shipmentRound,
      "items": items,
    };

    final response = await _dio.post("/franchise_orders/", data: data);

    if (response.statusCode != 200 && response.statusCode != 201) {
      throw Exception("서버 응답 오류: ${response.statusCode}");
    }
  }
  static Future<DateTime> fetchServerTime() async {
    final res = await _dio.get('/orders//server-time');
    return DateTime.parse(res.data['server_time']);
  }

  static Future<List<Map<String, dynamic>>> fetchProductList(int clientId) async {
    final res = await _dio.get('/products/public');
    print("🚀 상품 응답: ${res.data}");

    // 카테고리 딕셔너리를 모두 합쳐 하나의 리스트로 변환
    if (res.data is Map<String, dynamic>) {
      final Map<String, dynamic> categorized = res.data;
      List<Map<String, dynamic>> allProducts = [];

      for (var entry in categorized.entries) {
        if (entry.value is List) {
          allProducts.addAll(List<Map<String, dynamic>>.from(entry.value));
        }
      }

      return allProducts;
    } else {
      throw Exception("예상하지 못한 응답 형식입니다.");
    }
  }

}
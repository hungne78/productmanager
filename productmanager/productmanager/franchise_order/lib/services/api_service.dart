import 'package:dio/dio.dart';
import 'dart:collection';

class ApiService {
  static final Dio _dio = Dio(
    BaseOptions(baseUrl: 'http://192.168.0.183:8000/'),
  );

  /// ✅ 가맹점 로그인
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

      return Map<String, dynamic>.from(response.data);
    } catch (e) {
      print('❌ 로그인 실패: $e');
      return null;
    }
  }

  /// ✅ 가맹점 주문 전송
  static Future<void> submitFranchiseOrder({
    required int clientId,
    required DateTime orderDate,
    required int shipmentRound,
    required List<Map<String, dynamic>> items,
  }) async {
    final data = {
      "client_id": clientId,
      "order_date": orderDate.toIso8601String().split("T")[0], // yyyy-MM-dd
      "shipment_round": shipmentRound,
      "items": items,
    };

    final response = await _dio.post("/franchise_orders/", data: data);

    if (response.statusCode != 200 && response.statusCode != 201) {
      throw Exception("서버 응답 오류: ${response.statusCode}");
    }
  }

  /// ✅ 서버 시간 불러오기
  static Future<DateTime> fetchServerTime() async {
    final res = await _dio.get('/orders//server-time');
    return DateTime.parse(res.data['server_time']);
  }
  static Future<List<String>> fetchCategoryOrder() async {
    final res = await _dio.get('/orders/category');
    return List<String>.from(res.data);
  }

  static Future<List<String>> fetchBrandOrder() async {
    final res = await _dio.get('/orders/brand');
    return List<String>.from(res.data);
  }

  /// ✅ 상품 목록 (카테고리 → 브랜드 → 상품)
  static Future<LinkedHashMap<String, LinkedHashMap<String, List<Map<String, dynamic>>>>>
  fetchGroupedByCategoryAndBrand() async {
    final res = await _dio.get('/products/public');

    if (res.data is Map<String, dynamic>) {
      final outerMap = LinkedHashMap<String, LinkedHashMap<String, List<Map<String, dynamic>>>>();

      res.data.forEach((categoryKey, productList) {
        final brandMap = LinkedHashMap<String, List<Map<String, dynamic>>>();

        if (productList is List) {
          for (final item in productList) {
            final brand = item['brand_name'] ?? '기타';

            if (!brandMap.containsKey(brand)) {
              brandMap[brand] = [];
            }
            brandMap[brand]!.add(Map<String, dynamic>.from(item));
          }
        }

        outerMap[categoryKey] = brandMap;
      });

      return outerMap;
    } else {
      throw Exception("❌ 응답 형식이 이상합니다.");
    }
  }


  /// ✅ 상품 목록 (flat 리스트로 변환)
  static Future<List<Map<String, dynamic>>> fetchProductList(int clientId) async {
    final res = await _dio.get('/products/public');
    // print("🚀 상품 응답: ${res.data}");

    if (res.data is Map<String, dynamic>) {
      final Map<String, dynamic> categorized = res.data;
      List<Map<String, dynamic>> allProducts = [];

      for (var entry in categorized.entries) {
        final value = entry.value;
        if (value is Map<String, dynamic>) {
          for (var brandEntry in value.entries) {
            if (brandEntry.value is List) {
              allProducts.addAll(List<Map<String, dynamic>>.from(brandEntry.value));
            }
          }
        }
      }

      return allProducts;
    } else {
      throw Exception("예상하지 못한 응답 형식입니다.");
    }
  }
}

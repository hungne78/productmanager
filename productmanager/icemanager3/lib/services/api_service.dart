import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  static const String baseUrl = "http://192.168.50.221:8000"; //개인pc
  // static const String baseUrl = "http://192.168.0.183:8000";  //맥북
  static Future<http.Response> login(int id, String password) async {
    final url = Uri.parse("$baseUrl/login");
    final body = jsonEncode({"id": id, "password": password});
    final headers = {"Content-Type": "application/json"};
    return await http.post(url, headers: headers, body: body);
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

  static Future<List<dynamic>> fetchAllProducts(String token) async {
    final url = Uri.parse("$baseUrl/products/all");
    final response = await http.get(url, headers: {
      "Authorization": "Bearer $token",
      "Content-Type": "application/json; charset=utf-8",
    });

    if (response.statusCode == 200) {
      try {
        final decodedBody = utf8.decode(response.bodyBytes, allowMalformed: true); // ✅ UTF-8 오류 방지
        return jsonDecode(decodedBody) as List<dynamic>;
      } catch (e) {
        print("❌ JSON 디코딩 오류: $e");
        return [];
      }
    } else {
      print("❌ 상품 목록 조회 실패: ${response.statusCode}");
      return [];
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

// etc...
}
import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  static const String baseUrl = "http://192.168.50.221:8000";

  static Future<http.Response> login(int id, String password) async {
    final url = Uri.parse("$baseUrl/login");
    final body = jsonEncode({"id": id, "password": password});
    final headers = {"Content-Type": "application/json"};
    return await http.post(url, headers: headers, body: body);
  }

  static Future<http.Response> fetchEmployeeClients(String token, int employeeId) async {
    // 예: GET /employees/{employee_id}/clients
    final url = Uri.parse("$baseUrl/employees/$employeeId/clients");
    return await http.get(url, headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer $token",
    });
  }

  // 2) 매출 생성(단건)
  static Future<http.Response> createSales(String token, Map<String, dynamic> data) async {
    final url = Uri.parse("$baseUrl/sales"); // trailing slash 추가
    final headers = {
      "Content-Type": "application/json",
      "Authorization": "Bearer $token",
    };
    return await http.post(url, headers: headers, body: jsonEncode(data));
  }



  static Future<http.Response> fetchClients(String token) async {
    final url = Uri.parse("$baseUrl/clients");
    return await http.get(url, headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer $token",
    });
  }

  static Future<http.Response> fetchProductByBarcode(String token, String barcode) async {
    // 가정: 서버에 GET /products/barcode/{barcode} 엔드포인트가 있다고 가정
    final url = Uri.parse("$baseUrl/products/barcode/$barcode");
    return await http.get(url, headers: {
      "Authorization": "Bearer $token",
    });
  }

  static Future<http.Response> fetchClientPrice(String token, int clientId, int productId) async {
    // 가정: GET /client_product_prices?client_id=xx&product_id=yy
    final url = Uri.parse("$baseUrl/client_product_prices?client_id=$clientId&product_id=$productId");
    return await http.get(url, headers: {
      "Authorization": "Bearer $token",
    });
  }

  static Future<http.Response> fetchAllProducts(String token) async {
    final url = Uri.parse("$baseUrl/products/all");
    return await http.get(url, headers: {
      "Authorization": "Bearer $token",
    });
  }
  static Future<http.Response> updateClientOutstanding(String token, int clientId, Map<String, dynamic> data) async {
    final url = Uri.parse("$baseUrl/sales/outstanding/$clientId");  // ✅ URL 수정

    print("🔹 [PUT 요청] 미수금 업데이트 시작...");
    print("🔹 요청 URL: $url");
    print("🔹 요청 데이터: $data");
    print("🔹 요청 헤더: Bearer $token");

    return await http.put(
      url,
      headers: {
        "Authorization": "Bearer $token", // ✅ 인증 토큰 포함
        "Content-Type": "application/json",
      },
      body: jsonEncode(data),
    );
  }
// etc...
}
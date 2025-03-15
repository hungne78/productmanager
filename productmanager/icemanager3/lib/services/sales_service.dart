import 'dart:convert';
import 'package:http/http.dart' as http;

class SalesService {
  final String baseUrl;
  SalesService(this.baseUrl);

  // Fetch daily sales data for a specific employee
  Future<List<dynamic>> fetchDailySales(String token, int employeeId, String date) async {
    try {
      print("📡 Requesting daily sales for employee $employeeId: $baseUrl/sales/by_employee/$employeeId/$date");

      final response = await http.get(
        Uri.parse('$baseUrl/sales/by_employee/$employeeId/$date'),
        headers: {"Authorization": "Bearer $token"},
      );

      print("✅ Response Code: ${response.statusCode}");
      print("✅ Response Body: ${response.body}");

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception("Failed to load daily sales data: ${response.body}");
      }
    } catch (e) {
      print("❌ Error fetching daily sales: $e");
      throw Exception("Error fetching daily sales: $e");
    }
  }

  // Fetch monthly sales data for a specific employee
  Future<List<Map<String, dynamic>>> fetchMonthlySales(
      String token, int employeeId, int year, int month) async {
    try {
      print("📡 Requesting monthly sales: $baseUrl/sales/daily_sales/$employeeId/$year/$month");

      final response = await http.get(
        Uri.parse('$baseUrl/sales/daily_sales/$employeeId/$year/$month'),
        headers: {
          "Authorization": "Bearer $token",
          "Content-Type": "application/json; charset=UTF-8"  // ✅ Ensure UTF-8 decoding
        },
      );

      print("✅ Response Code: ${response.statusCode}");
      print("✅ Raw Response Body: ${response.body}");

      if (response.statusCode == 200) {
        var jsonData = utf8.decode(response.bodyBytes);  // ✅ Decode response to preserve Korean text
        var parsedData = jsonDecode(jsonData);

        if (parsedData is List) {
          return List<Map<String, dynamic>>.from(parsedData);
        } else {
          return [];
        }
      } else {
        throw Exception("Failed to load monthly sales data: ${response.body}");
      }
    } catch (e) {
      print("❌ Error fetching monthly sales: $e");
      throw Exception("Error fetching monthly sales: $e");
    }
  }



  // Fetch yearly sales data for a specific employee
  Future<List<Map<String, dynamic>>> fetchYearlySales(
      String token, int employeeId, int year) async {
    try {
      print("📡 Requesting yearly sales: $baseUrl/sales/monthly_sales/$employeeId/$year");

      final response = await http.get(
        Uri.parse('$baseUrl/sales/monthly_sales/$employeeId/$year'),
        headers: {"Authorization": "Bearer $token"},
      );

      print("✅ Response Code: ${response.statusCode}");
      print("✅ Raw Response Body: ${response.body}");

      if (response.statusCode == 200) {
        var jsonData = jsonDecode(utf8.decode(response.bodyBytes)); // ✅ Preserve Korean text
        print("🔍 Parsed JSON Data: $jsonData");  // ✅ Log parsed data

        if (jsonData is List && jsonData.isNotEmpty && jsonData[0] is Map<String, dynamic>) {
          return List<Map<String, dynamic>>.from(jsonData);
        } else {
          print("⚠️ API returned a list, but it's empty or contains unexpected data: $jsonData");
          return [];
        }
      } else {
        throw Exception("Failed to load yearly sales data: ${response.body}");
      }
    } catch (e) {
      print("❌ Error fetching yearly sales: $e");
      throw Exception("Error fetching yearly sales: $e");
    }
  }

  // ✅ 새로운 미수금 데이터를 가져오는 함수 추가
  Future<List<dynamic>> fetchOutstanding(String token, int employeeId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/sales/outstanding/$employeeId'),
      headers: {'Authorization': 'Bearer $token'},
    );

    if (response.statusCode == 200) {
      // ✅ UTF-8로 강제 디코딩
      String decodedBody = utf8.decode(response.bodyBytes);
      print("📌 Decoded API Response: $decodedBody");

      return jsonDecode(decodedBody);
    } else {
      throw Exception('Failed to fetch outstanding balance');
    }
  }
  Future<List<dynamic>> fetchSalesSummary(String token, int employeeId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/sales/summary/$employeeId'),
      headers: {'Authorization': 'Bearer $token'},
    );

    if (response.statusCode == 200) {
      String decodedBody = utf8.decode(response.bodyBytes); // ✅ UTF-8 디코딩
      print("📌 Decoded API Response: $decodedBody");
      return jsonDecode(decodedBody);
    } else {
      throw Exception('Failed to fetch sales summary');
    }
  }
  Future<List<dynamic>> fetchAllClients(String token, int employeeId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/clients/all/$employeeId'),
      headers: {'Authorization': 'Bearer $token'},
    );

    if (response.statusCode == 200) {
      String decodedBody = utf8.decode(response.bodyBytes); // ✅ UTF-8 디코딩
      return jsonDecode(decodedBody);
    } else {
      throw Exception('Failed to fetch clients');
    }
  }



}

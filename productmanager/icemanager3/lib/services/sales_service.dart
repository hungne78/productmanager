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
        headers: {"Authorization": "Bearer $token"},
      );

      print("✅ Response Code: ${response.statusCode}");
      print("✅ Response Body: ${response.body}");

      if (response.statusCode == 200) {
        var jsonData = jsonDecode(response.body);
        if (jsonData is List) {
          return List<Map<String, dynamic>>.from(jsonData);
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
      print("✅ Response Body: ${response.body}");

      if (response.statusCode == 200) {
        var jsonData = jsonDecode(response.body);
        if (jsonData is List) {
          return List<Map<String, dynamic>>.from(jsonData);
        } else {
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

}

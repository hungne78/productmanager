// lib/screens/sales/sales_main_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../providers/auth_provider.dart';
import '../../services/sales_api_service.dart';
import 'sales_detail_screen.dart';
import 'dart:convert';

class SalesMainScreen extends StatefulWidget {
  const SalesMainScreen({Key? key}) : super(key: key);

  @override
  _SalesMainScreenState createState() => _SalesMainScreenState();
}

class _SalesMainScreenState extends State<SalesMainScreen> {
  // 🔹 필터: 날짜범위, 직원ID, 거래처ID 등
  DateTime _startDate = DateTime.now().subtract(const Duration(days: 7));
  DateTime _endDate = DateTime.now();
  int? _selectedEmployeeId;
  int? _selectedClientId;

  bool _isLoading = false;
  String? _error;

  // 🔹 검색 결과 데이터
  List<Map<String, dynamic>> _byDate = [];     // [{ "date":"2025-05-10", "sum_sales":..., "items": [...], }, ...]
  List<Map<String, dynamic>> _byEmployee = []; // [{ "employee_id":..., "employee_name":..., "sum_sales":..., "items":[...]}, ...]
  List<Map<String, dynamic>> _byClient = [];   // [{ "client_id":..., "client_name":..., "sum_sales":..., "items":[...]}, ...]

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("판매 정보"),
      ),
      body: Column(
        children: [
          // 🔹 (A) 필터 영역
          _buildFilterBar(),

          // 🔹 (B) 검색 버튼
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: ElevatedButton.icon(
              onPressed: _search,
              icon: const Icon(Icons.search),
              label: const Text("검색"),
            ),
          ),

          // 🔹 (C) 결과 표시 (탭 or ExpansionTile)
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
                : SingleChildScrollView(
              padding: const EdgeInsets.all(8.0),
              child: Column(
                children: [
                  _buildExpansionSection("일자별", _byDate, "date"),
                  const SizedBox(height: 16),
                  _buildExpansionSection("직원별", _byEmployee, "employee_name"),
                  const SizedBox(height: 16),
                  _buildExpansionSection("거래처별", _byClient, "client_name"),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterBar() {
    final dateFormat = DateFormat("yyyy-MM-dd");

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            // (1) 시작일자
            TextButton.icon(
              icon: const Icon(Icons.calendar_today),
              label: Text(dateFormat.format(_startDate)),
              onPressed: () async {
                final picked = await showDatePicker(
                  context: context,
                  initialDate: _startDate,
                  firstDate: DateTime(2022),
                  lastDate: DateTime(2030),
                );
                if (picked != null) {
                  setState(() => _startDate = picked);
                }
              },
            ),
            const SizedBox(width: 8),

            // (2) 종료일자
            TextButton.icon(
              icon: const Icon(Icons.calendar_today),
              label: Text(dateFormat.format(_endDate)),
              onPressed: () async {
                final picked = await showDatePicker(
                  context: context,
                  initialDate: _endDate,
                  firstDate: DateTime(2022),
                  lastDate: DateTime(2030),
                );
                if (picked != null) {
                  setState(() => _endDate = picked);
                }
              },
            ),
            const SizedBox(width: 16),

            // (3) 직원 (간단히 텍스트필드 or Dropdown)
            // 실제로는 _fetchEmployeeList() 등을 해서 Dropdown 구성 가능
            // 여기서는 예시 간단화
            Text("직원ID:"),
            SizedBox(
              width: 80,
              child: TextField(
                onChanged: (val) => _selectedEmployeeId = int.tryParse(val),
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(hintText: "전체"),
              ),
            ),
            const SizedBox(width: 16),

            // (4) 거래처
            Text("거래처ID:"),
            SizedBox(
              width: 80,
              child: TextField(
                onChanged: (val) => _selectedClientId = int.tryParse(val),
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(hintText: "전체"),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _search() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    final auth = context.read<AuthProvider>();
    final token = auth.token;
    if (token == null) {
      setState(() {
        _isLoading = false;
        _error = "로그인이 필요합니다.";
      });
      return;
    }

    try {
      final data = await SalesApiService.fetchSalesAggregates(
        token,
        startDate: _startDate,
        endDate: _endDate,
        employeeId: _selectedEmployeeId,
        clientId: _selectedClientId,
      );

      // 응답의 'items' 필드가 String으로 오면 JSON으로 변환
      for (var group in data["by_date"] ?? []) {
        if (group["items"] is String) {
          try {
            // `items`가 String 형식으로 오면 JSON 배열로 변환
            group["items"] = json.decode('[' + group["items"] + ']') as List<dynamic>;
          } catch (e) {
            print("JSON 파싱 오류: $e");
          }
        }

      }

      setState(() {
        _byDate = List<Map<String, dynamic>>.from(data["by_date"] ?? []);
        _byEmployee = List<Map<String, dynamic>>.from(data["by_employee"] ?? []);
        _byClient = List<Map<String, dynamic>>.from(data["by_client"] ?? []);
      });
    } catch (e) {
      setState(() => _error = "검색 실패: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }


  Widget _buildExpansionSection(String title, List<Map<String, dynamic>> dataList, String labelKey) {
    if (dataList.isEmpty) {
      return Card(
        child: ListTile(title: Text("[$title] 데이터가 없습니다.")),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("[$title]", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 6),
        ...dataList.map((group) {
          final groupLabel = group[labelKey]?.toString() ?? "N/A";
          final sumSales = group["sum_sales"] ?? 0;
          final items = group["items"] as List<dynamic>? ?? [];

          return ExpansionTile(
            title: Text("$groupLabel (합계: $sumSales 원)"),
            children: items.isEmpty
                ? [const ListTile(title: Text("세부 판매 데이터 없음"))]
                : items.map((item) {
              // item 예시: { "sale_id": 10, "datetime":"2025-05-01 10:22", "employee_name":"홍길동", ... }
              final saleId = item["sale_id"];
              final dateTime = item["datetime"] ?? "N/A";
              final totalPrice = item["total_price"] ?? 0;
              return ListTile(
                title: Text("판매 #$saleId / $dateTime / $totalPrice 원"),
                onTap: () {
                  // 클릭 시 판매 상세 화면으로 이동
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => SalesDetailScreen(saleId: saleId),
                    ),
                  );
                },
              );
            }).toList(),
          );
        }).toList(),
      ],
    );
  }
}

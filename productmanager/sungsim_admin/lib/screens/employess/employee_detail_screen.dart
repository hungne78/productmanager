// lib/screens/employees/employee_detail_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../services/admin_api_service.dart';
import 'package:intl/intl.dart';

class EmployeeDetailScreen extends StatefulWidget {
  final int employeeId;
  const EmployeeDetailScreen({Key? key, required this.employeeId}) : super(key: key);

  @override
  _EmployeeDetailScreenState createState() => _EmployeeDetailScreenState();
}

class _EmployeeDetailScreenState extends State<EmployeeDetailScreen> {
  bool _isLoading = false;
  Map<String, dynamic>? _employeeBasic; // 직원 기본 프로필
  Map<String, dynamic>? _dailyStats;    // {"sales":..., "orders":..., "visits":...}
  Map<String, dynamic>? _monthlyStats;
  Map<String, dynamic>? _yearlyStats;
  List<Map<String, dynamic>> _clientStats = []; // 거래처별 매출/미수금/방문 등

  @override
  void initState() {
    super.initState();
    _fetchAllData();
  }

  Future<void> _fetchAllData() async {
    setState(() => _isLoading = true);

    final auth = context.read<AuthProvider>();
    final token = auth.token;
    if (token == null) {
      setState(() => _isLoading = false);
      return;
    }

    try {
      // 1) 직원 기본 프로필
      final basicInfo = await AdminApiService.fetchEmployeeProfile(token, widget.employeeId);
      // 응답: { "id":1, "name":"홍길동", "phone":"010-...", "role":"sales", ... }

      // 2) 일매출/주문/방문
      final daily = await AdminApiService.fetchEmployeeDailyStats(token, widget.employeeId);

      // 3) 월매출/주문/방문
      final monthly = await AdminApiService.fetchEmployeeMonthlyStats(token, widget.employeeId);

      // 4) 년매출/주문/방문
      final yearly = await AdminApiService.fetchEmployeeYearlyStats(token, widget.employeeId);

      // 5) 거래처별 매출/미수금/방문
      final clientStats = await AdminApiService.fetchEmployeeClientStats(token, widget.employeeId);
      // 예) [
      //   { "client_id":10, "client_name":"ABC유통", "daily_sales":200000, "monthly_sales":..., "yearly_sales":..., "outstanding":5000, "daily_visits":1, ... },
      //   ...
      // ]

      setState(() {
        _employeeBasic = basicInfo;
        _dailyStats = daily;
        _monthlyStats = monthly;
        _yearlyStats = yearly;
        _clientStats = List<Map<String, dynamic>>.from(clientStats);
      });
    } catch (e) {
      print("❌ 직원 상세정보 가져오기 실패: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("직원 상세 조회 실패: $e")),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final numberFormatter = NumberFormat("#,###");

    return Scaffold(
      appBar: AppBar(
        title: Text("직원 상세 (ID: ${widget.employeeId})"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _employeeBasic == null
          ? const Center(child: Text("직원 정보를 불러올 수 없습니다."))
          : SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Column(
            children: [
              // (A) 직원 기본 정보 카드
              _buildBasicProfileCard(),

              const SizedBox(height: 12),

              // (B) ExpansionTile들
              _buildStatsExpansion(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildBasicProfileCard() {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Row(
          children: [
            const Icon(Icons.person, size: 48),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _employeeBasic?["name"] ?? "이름 없음",
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  Text("전화: ${_employeeBasic?["phone"] ?? "정보 없음"}"),
                  Text("직급: ${_employeeBasic?["role"] ?? "sales"}"),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatsExpansion() {
    return Column(
      children: [
        // 1) 일매출/주문/방문
        ExpansionTile(
          title: const Text("📅 오늘 (일) 정보"),
          children: [
            if (_dailyStats == null)
              const ListTile(title: Text("정보 없음"))
            else
              Column(
                children: [
                  _buildStatRow("오늘 매출", _dailyStats!["sales"]),
                  _buildStatRow("오늘 주문", _dailyStats!["orders"]),
                  _buildStatRow("오늘 방문", _dailyStats!["visits"]),
                ],
              ),
          ],
        ),
        // 2) 월매출/주문/방문
        ExpansionTile(
          title: const Text("🗓 이번 달 (월) 정보"),
          children: [
            if (_monthlyStats == null)
              const ListTile(title: Text("정보 없음"))
            else
              Column(
                children: [
                  _buildStatRow("이달 매출", _monthlyStats!["sales"]),
                  _buildStatRow("이달 주문", _monthlyStats!["orders"]),
                  _buildStatRow("이달 방문", _monthlyStats!["visits"]),
                ],
              ),
          ],
        ),
        // 3) 연매출/주문/방문
        ExpansionTile(
          title: const Text("📆 올해 (년) 정보"),
          children: [
            if (_yearlyStats == null)
              const ListTile(title: Text("정보 없음"))
            else
              Column(
                children: [
                  _buildStatRow("연 매출", _yearlyStats!["sales"]),
                  _buildStatRow("연 주문", _yearlyStats!["orders"]),
                  _buildStatRow("연 방문", _yearlyStats!["visits"]),
                ],
              ),
          ],
        ),
        // 4) 거래처별
        ExpansionTile(
          title: const Text("🔎 거래처별 매출/미수금/방문"),
          children: [
            if (_clientStats.isEmpty)
              const ListTile(title: Text("등록된 거래처 정보가 없습니다."))
            else
              Column(
                children: _clientStats.map((c) {
                  // c: { "client_id":..., "client_name":..., "daily_sales":..., "outstanding":..., ...}
                  return ListTile(
                    title: Text("${c["client_name"]} (ID: ${c["client_id"]})"),
                    subtitle: Text(
                      "일매출: ${c["daily_sales"]} / 월매출: ${c["monthly_sales"]}\n"
                          "미수금: ${c["outstanding"]}\n"
                          "방문(월): ${c["monthly_visits"]}회",
                    ),
                  );
                }).toList(),
              ),
          ],
        ),
      ],
    );
  }

  Widget _buildStatRow(String label, dynamic value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 12),
      child: Row(
        children: [
          Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
          const Spacer(),
          Text(value == null ? "0" : value.toString()),
        ],
      ),
    );
  }
}
